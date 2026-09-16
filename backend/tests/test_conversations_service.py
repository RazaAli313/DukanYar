"""Conversation persistence tests — TEXT-3 service layer.

Real Supabase project, no mocks. Shops are throwaway and cascade to
conversations/messages on delete.
"""

from __future__ import annotations

import pytest

from app.services import conversations as C
from tests.conftest import requires_supabase

pytestmark = requires_supabase


@pytest.fixture
def conversation(shop_id, auth_user):
    return C.get_or_create_conversation(shop_id=shop_id, user_id=auth_user["id"])


def _say(conversation, role, text, **kw):
    return C.add_message(
        conversation_id=conversation["id"], sender=role, content=text, **kw
    )


# ── get_or_create (one thread per shop) ──────────────────────────────────────

def test_creates_conversation_scoped_to_shop(shop_id, auth_user):
    conv = C.get_or_create_conversation(shop_id=shop_id, user_id=auth_user["id"])
    assert conv["shop_id"] == shop_id
    assert conv["user_id"] == auth_user["id"]


def test_get_or_create_is_idempotent(shop_id, auth_user):
    first = C.get_or_create_conversation(shop_id=shop_id, user_id=auth_user["id"])
    second = C.get_or_create_conversation(shop_id=shop_id, user_id=auth_user["id"])
    assert first["id"] == second["id"]


def test_find_conversation_returns_none_before_first_message(shop_id):
    assert C.find_conversation(shop_id=shop_id) is None


def test_find_conversation_after_creation(shop_id, auth_user):
    created = C.get_or_create_conversation(shop_id=shop_id, user_id=auth_user["id"])
    assert C.find_conversation(shop_id=shop_id)["id"] == created["id"]


# ── add_message / list_messages ──────────────────────────────────────────────

def test_message_round_trip_maps_db_columns_to_api_shape(conversation):
    stored = _say(conversation, C.SENDER_USER, "aaj ka kharcha 500")
    assert stored["role"] == "user"
    assert stored["content"] == "aaj ka kharcha 500"
    assert stored["channel"] == "text"
    assert stored["status"] == "complete"
    assert stored["id"] and stored["created_at"]


def test_list_messages_is_oldest_first(shop_id, conversation):
    for i in range(5):
        _say(conversation, C.SENDER_USER, f"msg-{i}")

    rows = C.list_messages(shop_id=shop_id, conversation_id=conversation["id"])
    assert [r["content"] for r in rows] == [f"msg-{i}" for i in range(5)]


def test_list_messages_limit_returns_the_last_n_not_the_first(shop_id, conversation):
    for i in range(10):
        _say(conversation, C.SENDER_USER, f"msg-{i}")

    rows = C.list_messages(shop_id=shop_id, conversation_id=conversation["id"], limit=3)
    assert [r["content"] for r in rows] == ["msg-7", "msg-8", "msg-9"]


def test_history_limit_is_capped(shop_id, conversation):
    _say(conversation, C.SENDER_USER, "hi")
    rows = C.list_messages(
        shop_id=shop_id, conversation_id=conversation["id"], limit=10_000
    )
    assert len(rows) == 1  # capped, not rejected


def test_voice_message_persists_transcription_confidence(shop_id, conversation):
    _say(
        conversation,
        C.SENDER_USER,
        "do kilo chawal",
        channel=C.CHANNEL_VOICE,
        transcription_confidence=0.87,
    )
    row = C.list_messages(shop_id=shop_id, conversation_id=conversation["id"])[0]
    assert row["channel"] == "voice"
    assert row["transcription_confidence"] == pytest.approx(0.87)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sender": "bot"},
        {"sender": "system"},
        {"channel": "sms"},
        {"status": "half-done"},
    ],
)
def test_add_message_rejects_unknown_vocabulary(conversation, kwargs):
    payload = {"sender": C.SENDER_USER, "content": "x", **kwargs}
    with pytest.raises(C.ConversationError):
        C.add_message(conversation_id=conversation["id"], **payload)


# ── recent_turns (the rolling context window) ────────────────────────────────

def test_recent_turns_returns_openai_shape_oldest_first(conversation):
    _say(conversation, C.SENDER_USER, "salaam")
    _say(conversation, C.SENDER_ASSISTANT, "walaikum salaam")

    turns = C.recent_turns(conversation_id=conversation["id"], max_turns=8)
    assert turns == [
        {"role": "user", "content": "salaam"},
        {"role": "assistant", "content": "walaikum salaam"},
    ]


def test_recent_turns_drops_oldest_beyond_the_cap(conversation):
    for i in range(12):
        _say(conversation, C.SENDER_USER, f"turn-{i}")

    turns = C.recent_turns(conversation_id=conversation["id"], max_turns=4)
    assert [t["content"] for t in turns] == ["turn-8", "turn-9", "turn-10", "turn-11"]


def test_recent_turns_skips_failed_and_partial_replies(conversation):
    _say(conversation, C.SENDER_USER, "kept")
    _say(conversation, C.SENDER_ASSISTANT, "half-written", status=C.STATUS_FAILED)
    _say(conversation, C.SENDER_ASSISTANT, "kept too")

    turns = C.recent_turns(conversation_id=conversation["id"], max_turns=8)
    assert [t["content"] for t in turns] == ["kept", "kept too"]


def test_recent_turns_empty_for_new_conversation(conversation):
    assert C.recent_turns(conversation_id=conversation["id"], max_turns=8) == []


def test_recent_turns_zero_cap_returns_nothing(conversation):
    _say(conversation, C.SENDER_USER, "hi")
    assert C.recent_turns(conversation_id=conversation["id"], max_turns=0) == []


# ── shop isolation ───────────────────────────────────────────────────────────

def test_conversation_is_not_readable_from_another_shop(
    shop_id, other_shop_id, conversation
):
    _say(conversation, C.SENDER_USER, "shop A ka raaz")

    with pytest.raises(C.ConversationError):
        C.list_messages(shop_id=other_shop_id, conversation_id=conversation["id"])


def test_each_shop_gets_its_own_thread(shop_id, other_shop_id, auth_user):
    mine = C.get_or_create_conversation(shop_id=shop_id, user_id=auth_user["id"])
    theirs = C.get_or_create_conversation(
        shop_id=other_shop_id, user_id=auth_user["id"]
    )
    assert mine["id"] != theirs["id"]
