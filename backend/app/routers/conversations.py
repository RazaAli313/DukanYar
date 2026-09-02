"""Conversations router — TEXT-2 streaming reply, TEXT-3 persistence.

POST /conversations/{conversation_id}/messages   send a message, stream the reply
GET  /conversations/history                      reload the thread

Both require ``Authorization: Bearer <supabase access token>``; the caller's shop
is resolved from their profile (see app.auth), never from the request body.

The shop's single conversation is resolved server-side, so the ``conversation_id``
in the POST path is accepted but ignored -- a client cannot address another
shop's thread, or invent one.

Ordering inside the POST handler is deliberate:
  1. pre-flight the LLM client, *before* any write, so a config failure cannot
     leave an orphan user message that a retry would then duplicate;
  2. read the context window *before* persisting the new message, so the current
     text is not both replayed as history and appended as the live turn;
  3. persist the assistant reply only after the stream closes, and only if it
     produced text.
"""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from openai import APIError, APITimeoutError
from pydantic import BaseModel, Field
from typing import Literal

from app.auth import CurrentUserDep
from app.config import settings
from app.services import conversations as convo
from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / response models ────────────────────────────────────────────────

class Turn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class MessageRequest(BaseModel):
    text: str
    channel: Literal["text", "voice"] = "text"
    #: Speechmatics/Groq confidence for a transcribed turn (VOICE-2). Stored on
    #: voice messages only; meaningless for typed ones.
    transcription_confidence: float | None = None
    #: Deprecated. Context now comes from the database, which is the only source
    #: that survives a refresh. Accepted so older clients do not 422; ignored.
    recent_turns: list[Turn] = Field(default_factory=list, deprecated=True)


# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse_event(event: str, data: dict) -> str:
    """Format a single named SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: MessageRequest,
    user: CurrentUserDep,
):
    """Persist the user's message, stream the reply, then persist the reply.

    Pre-stream errors -> HTTP 502 JSON. Mid-stream errors -> named `error`
    event, then the stream closes.
    """
    # 1. Pre-flight: fail before writing anything if the LLM is misconfigured.
    try:
        llm._get_client()  # noqa: SLF001 — intentional pre-flight check
    except Exception as exc:
        logger.exception("LLM client init failed")
        raise HTTPException(status_code=502, detail=f"LLM config error: {exc}") from exc

    conversation = convo.get_or_create_conversation(
        shop_id=user.shop_id, user_id=user.user_id
    )
    conv_id = conversation["id"]

    # 2. Context window BEFORE the new message is stored, so it is not replayed
    #    as history and appended as the live turn.
    prior = convo.recent_turns(
        conversation_id=conv_id, max_turns=settings.llm_max_context_turns
    )

    convo.add_message(
        conversation_id=conv_id,
        sender=convo.SENDER_USER,
        content=body.text,
        channel=body.channel,
        transcription_confidence=(
            body.transcription_confidence if body.channel == "voice" else None
        ),
    )

    messages = prior + [{"role": "user", "content": body.text}]

    async def event_stream():
        chunks: list[str] = []

        def persist_reply(status: str) -> None:
            """Best-effort write of whatever the model produced."""
            reply = "".join(chunks)
            if not reply.strip():
                return  # nothing was generated — an empty bubble helps nobody
            try:
                convo.add_message(
                    conversation_id=conv_id,
                    sender=convo.SENDER_ASSISTANT,
                    content=reply,
                    channel=body.channel,
                    status=status,
                )
            except Exception:  # pragma: no cover — never break the stream on this
                logger.exception("failed to persist assistant reply")

        yield _sse_event("meta", {"conversation_id": conv_id})
        try:
            async for delta in llm.stream_reply(messages, body.channel):
                chunks.append(delta)
                yield _sse_event("delta", {"text": delta})
        except asyncio.CancelledError:
            # Client disconnected. CancelledError is a BaseException, so it does
            # not reach the handlers below; shield the write from the same
            # cancellation that is unwinding us.
            logger.info("client disconnected mid-stream, conv=%s", conv_id)
            await asyncio.shield(asyncio.to_thread(persist_reply, convo.STATUS_FAILED))
            raise
        except (APIError, APITimeoutError) as exc:
            logger.warning("LLM error mid-stream: %s", exc)
            persist_reply(convo.STATUS_FAILED)
            yield _sse_event("error", {"detail": f"LLM error: {exc}"})
            return
        except Exception as exc:
            logger.exception("Unexpected error mid-stream")
            persist_reply(convo.STATUS_FAILED)
            yield _sse_event("error", {"detail": f"Internal error: {exc}"})
            return

        persist_reply(convo.STATUS_COMPLETE)
        yield _sse_event("done", {"conversation_id": conv_id})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering if present
        },
    )


@router.get("/history")
def get_history(
    user: CurrentUserDep,
    limit: int = Query(convo.DEFAULT_HISTORY_LIMIT, ge=1, le=convo.MAX_HISTORY_LIMIT),
):
    """The shop's thread, oldest-first — what the UI renders on load.

    A shop that has never sent a message has no thread yet; this returns an empty
    one rather than creating a row on a read.
    """
    conversation = convo.find_conversation(shop_id=user.shop_id)
    if conversation is None:
        return {"conversation_id": None, "messages": []}

    return {
        "conversation_id": conversation["id"],
        "messages": convo.list_messages(
            shop_id=user.shop_id,
            conversation_id=conversation["id"],
            limit=limit,
        ),
    }
