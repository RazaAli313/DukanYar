"""Conversations endpoint tests — TEXT-3.

The LLM is monkeypatched (no model calls, deterministic deltas) but the database
is real: these assert what actually lands in `messages`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth import CurrentUser, get_current_user
from app.main import app
from app.services import conversations as C
from app.services import llm
from tests.conftest import requires_supabase

pytestmark = requires_supabase


@pytest.fixture
def captured():
    """Collects the message list the router hands to the model."""
    return {}


@pytest.fixture
def fake_llm(monkeypatch, captured):
    """Replace the model with a scripted stream. Returns a configure callable."""

    def configure(deltas=("acha ", "ji"), fail_with=None):
        async def stream_reply(turns, channel="text", mode=None):
            captured["turns"] = list(turns)
            captured["channel"] = channel
            for d in deltas:
                yield d
            if fail_with is not None:
                raise fail_with

        monkeypatch.setattr(llm, "stream_reply", stream_reply)
        monkeypatch.setattr(llm, "_get_client", lambda: object())

    configure()  # sane default; tests may reconfigure
    return configure


@pytest.fixture
def client(shop_id, auth_user):
    """A TestClient authenticated as auth_user, without minting a real token."""
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=auth_user["id"], shop_id=shop_id, role="shopkeeper"
    )
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def _events(response):
    """Parse an SSE body into [(event_name, data_str), ...]."""
    out = []
    for block in response.text.split("\n\n"):
        name = data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if name:
            out.append((name, data))
    return out


def _post(client, text="aaj ka kharcha 500", **body):
    return client.post(
        "/conversations/ignored-by-server/messages", json={"text": text, **body}
    )


# ── persistence (AC: both messages are stored) ───────────────────────────────

def test_stores_user_message_and_assistant_reply(client, fake_llm, shop_id):
    res = _post(client)
    assert res.status_code == 200

    conv = C.find_conversation(shop_id=shop_id)
    rows = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])

    assert [(r["role"], r["content"]) for r in rows] == [
        ("user", "aaj ka kharcha 500"),
        ("assistant", "acha ji"),
    ]
    assert all(r["status"] == "complete" for r in rows)


def test_reuses_one_conversation_across_messages(client, fake_llm, shop_id):
    _post(client, "pehla")
    _post(client, "doosra")
    _post(client, "teesra")

    conv = C.find_conversation(shop_id=shop_id)
    rows = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])
    assert [r["content"] for r in rows if r["role"] == "user"] == [
        "pehla",
        "doosra",
        "teesra",
    ]


def test_emits_conversation_id_in_meta_and_done(client, fake_llm, shop_id):
    events = _events(_post(client))
    names = [n for n, _ in events]

    assert names[0] == "meta"  # early, so the UI can bind immediately
    assert names[-1] == "done"

    conv = C.find_conversation(shop_id=shop_id)
    by_name = dict(events)
    assert conv["id"] in by_name["meta"]
    assert conv["id"] in by_name["done"]


def test_deltas_are_streamed(client, fake_llm):
    names = [n for n, _ in _events(_post(client))]
    assert names.count("delta") == 2


# ── context window (AC: recent turns reach the model) ────────────────────────

def test_new_message_reaches_the_model_exactly_once(client, fake_llm, captured):
    _post(client, "sirf ek baar")

    contents = [t["content"] for t in captured["turns"]]
    assert contents.count("sirf ek baar") == 1
    assert contents[-1] == "sirf ek baar"


def test_prior_turns_are_replayed_as_context(client, fake_llm, captured):
    _post(client, "pehla sawal")
    _post(client, "doosra sawal")

    assert [t["content"] for t in captured["turns"]] == [
        "pehla sawal",
        "acha ji",
        "doosra sawal",
    ]


def test_context_is_capped_and_drops_oldest(client, fake_llm, captured, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "llm_max_context_turns", 2)
    for i in range(4):
        _post(client, f"q{i}")

    # 2 replayed turns + the live message
    assert len(captured["turns"]) == 3
    assert captured["turns"][-1]["content"] == "q3"


def test_channel_is_forwarded_to_the_model(client, fake_llm, captured):
    _post(client, "bol kar likha", channel="voice")
    assert captured["channel"] == "voice"


# ── voice metadata ───────────────────────────────────────────────────────────

def test_voice_message_persists_confidence(client, fake_llm, shop_id):
    _post(client, "do kilo chawal", channel="voice", transcription_confidence=0.91)

    conv = C.find_conversation(shop_id=shop_id)
    user_row = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])[0]
    assert user_row["channel"] == "voice"
    assert user_row["transcription_confidence"] == pytest.approx(0.91)


def test_typed_message_ignores_confidence(client, fake_llm, shop_id):
    _post(client, "typed", channel="text", transcription_confidence=0.5)

    conv = C.find_conversation(shop_id=shop_id)
    user_row = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])[0]
    assert user_row["transcription_confidence"] is None


# ── failure paths ────────────────────────────────────────────────────────────

def test_midstream_failure_persists_partial_reply_as_failed(client, fake_llm, shop_id):
    fake_llm(deltas=("adhoora",), fail_with=RuntimeError("boom"))

    events = _events(_post(client))
    assert "error" in [n for n, _ in events]

    conv = C.find_conversation(shop_id=shop_id)
    rows = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])
    assistant = [r for r in rows if r["role"] == "assistant"]
    assert len(assistant) == 1
    assert assistant[0]["content"] == "adhoora"
    assert assistant[0]["status"] == "failed"


def test_failed_reply_is_not_replayed_as_context(client, fake_llm, captured):
    fake_llm(deltas=("adhoora",), fail_with=RuntimeError("boom"))
    _post(client, "pehla")

    fake_llm(deltas=("theek hai",))
    _post(client, "doosra")

    assert [t["content"] for t in captured["turns"]] == ["pehla", "doosra"]


def test_empty_reply_writes_no_assistant_row(client, fake_llm, shop_id):
    fake_llm(deltas=())

    _post(client, "koi jawab nahi")
    conv = C.find_conversation(shop_id=shop_id)
    rows = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])
    assert [r["role"] for r in rows] == ["user"]


def test_llm_config_error_returns_502_and_writes_nothing(
    client, fake_llm, shop_id, monkeypatch
):
    def broken():
        raise RuntimeError("no api key")

    monkeypatch.setattr(llm, "_get_client", broken)

    res = _post(client, "ye save nahi hona chahiye")
    assert res.status_code == 502
    # No orphan user row: a retry must not duplicate the message.
    assert C.find_conversation(shop_id=shop_id) is None


# ── history endpoint ─────────────────────────────────────────────────────────

def test_history_is_empty_before_any_message(client):
    body = client.get("/conversations/history").json()
    assert body == {"conversation_id": None, "messages": []}


def test_history_returns_thread_oldest_first(client, fake_llm, shop_id):
    _post(client, "pehla")
    _post(client, "doosra")

    body = client.get("/conversations/history").json()
    assert body["conversation_id"] == C.find_conversation(shop_id=shop_id)["id"]
    assert [(m["role"], m["content"]) for m in body["messages"]] == [
        ("user", "pehla"),
        ("assistant", "acha ji"),
        ("user", "doosra"),
        ("assistant", "acha ji"),
    ]


def test_history_wire_format_field_names(client, fake_llm):
    _post(client)
    message = client.get("/conversations/history").json()["messages"][0]
    assert set(message) == {
        "id",
        "role",
        "content",
        "channel",
        "status",
        "transcription_confidence",
        "created_at",
    }


def test_history_limit_returns_the_most_recent(client, fake_llm):
    for i in range(4):
        _post(client, f"q{i}")

    messages = client.get("/conversations/history?limit=2").json()["messages"]
    assert [m["content"] for m in messages] == ["q3", "acha ji"]


def test_history_rejects_out_of_range_limit(client):
    assert client.get("/conversations/history?limit=0").status_code == 422
    assert client.get("/conversations/history?limit=101").status_code == 422


# ── auth is enforced (no dependency override) ────────────────────────────────

def test_endpoints_require_a_token():
    with TestClient(app) as anon:
        res = anon.post("/conversations/x/messages", json={"text": "hi"})
        assert res.status_code == 401
        assert anon.get("/conversations/history").status_code == 401
