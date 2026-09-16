"""Conversation persistence & context — TEXT-3.

Routing-independent: nothing here knows whether it was reached from the chat UI,
the voice pillar, or a plain endpoint.

**One thread per shop.** A shopkeeper thinks "meri dukaan ki baat-cheet", not
"conversation #5", so there is exactly one ``conversations`` row per shop,
lazily created on the first message and never closed. There is no session or
thread concept and nothing is ever archived.

**Storage vs context are separate concerns.** Every message is kept forever
(INSERT only, no pruning) — rows are ~1KB and the audit trail is what makes
"did I really record that expense?" answerable. What is *capped* is how much of
that history each model call replays: see :func:`recent_turns`. Token cost and
latency come from the prompt, not from the table.

Voice collapses to text on the way in: the transcript lands in ``messages.message``
with ``channel='voice'``; audio is never stored.

The backend uses the Supabase **service_role** key, so RLS is bypassed — every
function takes ``shop_id`` and scopes its own query.
"""

from __future__ import annotations

import logging
from typing import Any

from app.db import get_supabase

logger = logging.getLogger(__name__)

# `sender` and `channel` are plain TEXT columns with no CHECK constraint, so the
# allowed values are this module's convention. `sender` doubles as the OpenAI
# role, which is why it is "user"/"assistant" rather than "shopkeeper"/"bot".
SENDER_USER = "user"
SENDER_ASSISTANT = "assistant"
_SENDERS = (SENDER_USER, SENDER_ASSISTANT)

CHANNEL_TEXT = "text"
CHANNEL_VOICE = "voice"
_CHANNELS = (CHANNEL_TEXT, CHANNEL_VOICE)

# message_status enum, per the FND migration.
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"
_STATUSES = ("pending", "streaming", STATUS_COMPLETE, STATUS_FAILED)

_CONVERSATION_COLS = "id,shop_id,user_id,created_at"
_MESSAGE_COLS = (
    "id,conversation_id,sender,channel,message,status,transcription_confidence,created_at"
)

DEFAULT_HISTORY_LIMIT = 30
MAX_HISTORY_LIMIT = 100


class ConversationError(Exception):
    """Invalid conversation input, or a conversation outside the caller's shop."""


# ── conversations ────────────────────────────────────────────────────────────

def get_or_create_conversation(*, shop_id: str, user_id: str) -> dict[str, Any]:
    """Return this shop's single conversation, creating it on first use.

    *user_id* is recorded as the creator only; every user in the shop shares the
    thread. Ordering by ``created_at`` keeps the choice deterministic if a race
    ever produced two rows (see the TEXT-3 unique-index migration).
    """
    sb = get_supabase()
    existing = (
        sb.table("conversations")
        .select(_CONVERSATION_COLS)
        .eq("shop_id", shop_id)
        .order("created_at")
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return existing[0]

    created = (
        sb.table("conversations")
        .insert({"shop_id": shop_id, "user_id": user_id})
        .execute()
        .data
    )
    if not created:
        raise ConversationError("conversation insert returned no row")

    logger.info("conversation created: shop=%s", shop_id)
    return {k: created[0][k] for k in _CONVERSATION_COLS.split(",") if k in created[0]}


def find_conversation(*, shop_id: str) -> dict[str, Any] | None:
    """This shop's conversation, or None if they have never sent a message."""
    rows = (
        get_supabase()
        .table("conversations")
        .select(_CONVERSATION_COLS)
        .eq("shop_id", shop_id)
        .order("created_at")
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


def _assert_conversation_in_shop(shop_id: str, conversation_id: str) -> None:
    """Guard: the conversation must belong to this shop before we read/write it."""
    rows = (
        get_supabase()
        .table("conversations")
        .select("id")
        .eq("id", conversation_id)
        .eq("shop_id", shop_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise ConversationError("is shop ki aisi koi conversation nahi")


# ── messages ─────────────────────────────────────────────────────────────────

def _message_row(row: dict[str, Any]) -> dict[str, Any]:
    """DB shape -> API shape: `sender`/`message` become `role`/`content`."""
    return {
        "id": row["id"],
        "role": row["sender"],
        "content": row["message"],
        "channel": row.get("channel"),
        "status": row.get("status"),
        "transcription_confidence": row.get("transcription_confidence"),
        "created_at": row.get("created_at"),
    }


def add_message(
    *,
    conversation_id: str,
    sender: str,
    content: str,
    channel: str = CHANNEL_TEXT,
    status: str = STATUS_COMPLETE,
    transcription_confidence: float | None = None,
) -> dict[str, Any]:
    """Append one message. Returns the stored row in API shape."""
    if sender not in _SENDERS:
        raise ConversationError(f"sender must be one of {_SENDERS}")
    if channel not in _CHANNELS:
        raise ConversationError(f"channel must be one of {_CHANNELS}")
    if status not in _STATUSES:
        raise ConversationError(f"status must be one of {_STATUSES}")
    if content is None:
        raise ConversationError("content is required")

    row: dict[str, Any] = {
        "conversation_id": conversation_id,
        "sender": sender,
        "channel": channel,
        "message": content,
        "status": status,
    }
    if transcription_confidence is not None:
        row["transcription_confidence"] = float(transcription_confidence)

    inserted = get_supabase().table("messages").insert(row).execute().data
    if not inserted:
        raise ConversationError("message insert returned no row")
    return _message_row(inserted[0])


def list_messages(
    *,
    shop_id: str,
    conversation_id: str,
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    """The **last** *limit* messages, oldest-first (chat reading order).

    Fetched newest-first then reversed — a plain oldest-first query with a limit
    would return the *first* N messages of the thread, not the most recent ones.
    """
    _assert_conversation_in_shop(shop_id, conversation_id)
    limit = max(1, min(int(limit), MAX_HISTORY_LIMIT))

    rows = (
        get_supabase()
        .table("messages")
        .select(_MESSAGE_COLS)
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return [_message_row(r) for r in reversed(rows)]


def recent_turns(*, conversation_id: str, max_turns: int) -> list[dict[str, str]]:
    """The last *max_turns* completed messages as OpenAI-style turns.

    This is the rolling context window: applied at read time, never by deleting
    rows. Only ``complete`` messages are replayed — a failed or half-streamed
    reply is not something the model should treat as its own prior turn.
    """
    if max_turns <= 0:
        return []

    rows = (
        get_supabase()
        .table("messages")
        .select("sender,message,created_at")
        .eq("conversation_id", conversation_id)
        .eq("status", STATUS_COMPLETE)
        .order("created_at", desc=True)
        .limit(int(max_turns))
        .execute()
        .data
    )
    return [
        {"role": r["sender"], "content": r["message"]} for r in reversed(rows)
    ]
