"""Conversations endpoint tests — TEXT-3.

The LLM is monkeypatched (no model calls, deterministic deltas) but the database
is real: these assert what actually lands in `messages`.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

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
    """Replace the model with scripted orchestration replies."""

    def configure(
        deltas=("acha ", "ji"),
        fail_with=None,
        tool_messages=None,
        scope_allowed=True,
    ):
        scripted = list(tool_messages or [])

        async def is_shop_request(turns):
            captured["scope_turns"] = list(turns)
            return scope_allowed

        async def tool_call_reply(turns, tools, channel="text", mode=None):
            captured["turns"] = list(turns)
            captured["channel"] = channel
            captured.setdefault("tool_rounds", []).append(
                {"turns": list(turns), "tools": list(tools), "mode": mode}
            )
            if fail_with is not None:
                raise fail_with
            if scripted:
                return scripted.pop(0)
            return SimpleNamespace(content="".join(deltas), tool_calls=[])

        monkeypatch.setattr(llm, "is_shop_request", is_shop_request, raising=False)
        monkeypatch.setattr(llm, "tool_call_reply", tool_call_reply)
        monkeypatch.setattr(llm, "_get_client", lambda: object())

    configure()  # sane default; tests may reconfigure
    return configure


def _model_message(*, content="", calls=()):
    return SimpleNamespace(content=content, tool_calls=list(calls))


def _tool_call(name, arguments, call_id="call-1"):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


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


def test_out_of_scope_programming_request_is_refused_before_main_llm(
    client, fake_llm, captured
):
    fake_llm(
        scope_allowed=False,
        deltas=("Sure, here's a Python function: def add(a, b): return a + b",),
    )

    events = _events(_post(client, "write a python function to add 2 numbers", mode="ask"))
    reply = "".join(
        json.loads(data)["text"] for name, data in events if name == "delta"
    )

    assert "sirf aapki dukaan" in reply.lower()
    assert "python" not in reply.lower()
    assert captured.get("tool_rounds", []) == []


def test_llm_selected_expense_commits_with_audited_action(
    client, fake_llm, shop_id
):
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "log_expense",
                        {"amount": 3000, "note": "bijli ka bill"},
                    )
                ]
            ),
            _model_message(content="Bijli ka kharcha likh diya."),
        ]
    )

    events = _events(_post(client, "bijli ka bill 3000", mode="ask"))
    actions = [json.loads(data) for name, data in events if name == "action"]

    assert len(actions) == 1
    assert actions[0]["kind"] == "kharcha"
    assert actions[0]["status"] == "recorded"
    assert actions[0]["tool_call_id"]

    from app.db import get_supabase

    expenses = (
        get_supabase()
        .table("expenses")
        .select("amount,note")
        .eq("shop_id", shop_id)
        .execute()
        .data
    )
    assert [(float(row["amount"]), row["note"]) for row in expenses] == [
        (3000.0, "bijli ka bill")
    ]

    calls = (
        get_supabase()
        .table("tool_calls")
        .select("tool_name,status")
        .eq("id", actions[0]["tool_call_id"])
        .execute()
        .data
    )
    assert calls == [{"tool_name": "log_expense", "status": "committed"}]


def test_approval_tool_waits_for_generic_confirmation(
    client, fake_llm, shop_id
):
    from app.services import khata

    customer = khata.register_customer(
        shop_id=shop_id,
        name="Ali",
        cnic="35202-1234567-1",
    )
    khata.log_udhaar(shop_id=shop_id, customer_id=customer["id"], amount=500)

    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "record_payment",
                        {"amount": 200, "khata_number": customer["khata_number"]},
                    )
                ]
            )
        ]
    )

    events = _events(_post(client, "Ali ne 200 jama karaye", mode="ask"))
    actions = [json.loads(data) for name, data in events if name == "action"]

    assert len(actions) == 1
    assert actions[0]["status"] == "proposed"
    assert actions[0]["tool_name"] == "record_payment"
    assert khata.customer_balance(shop_id=shop_id, customer_id=customer["id"]) == 500

    confirmed = client.post(
        f"/conversations/actions/{actions[0]['tool_call_id']}/confirm"
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["card"]["status"] == "recorded"
    assert khata.customer_balance(shop_id=shop_id, customer_id=customer["id"]) == 300

    repeated = client.post(
        f"/conversations/actions/{actions[0]['tool_call_id']}/confirm"
    )
    assert repeated.status_code == 409
    assert khata.customer_balance(shop_id=shop_id, customer_id=customer["id"]) == 300


def test_screen_mode_is_only_a_hint_and_does_not_bypass_llm_tool_choice(
    client, fake_llm, shop_id
):
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "log_expense",
                        {"amount": 900, "note": "delivery petrol"},
                    )
                ]
            ),
            _model_message(content="Petrol ka kharcha likh diya."),
        ]
    )

    events = _events(_post(client, "petrol 900 likho", mode="sale"))
    actions = [json.loads(data) for name, data in events if name == "action"]

    assert actions[0]["kind"] == "kharcha"
    assert actions[0]["status"] == "recorded"


def test_orchestrator_supports_multiple_llm_tool_rounds(
    client, fake_llm, captured
):
    fake_llm(
        tool_messages=[
            _model_message(calls=[_tool_call("daily_summary", {}, "summary")]),
            _model_message(calls=[_tool_call("low_stock", {}, "stock")]),
            _model_message(content="Aaj ka hisaab aur low stock dono dekh liye."),
        ]
    )

    events = _events(_post(client, "aaj ka poora haal batao", mode="ask"))

    assert len(captured["tool_rounds"]) == 3
    assert [name for name, _ in events][-1] == "done"
    reply = "".join(
        json.loads(data)["text"] for name, data in events if name == "delta"
    )
    assert "Aaj ka hisaab aur low stock dono dekh liye." in reply


def test_committed_tool_action_can_be_undone_through_generic_endpoint(
    client, fake_llm, shop_id
):
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "log_expense",
                        {"amount": 1200, "note": "generator diesel"},
                    )
                ]
            ),
            _model_message(content="Diesel ka kharcha likh diya."),
        ]
    )
    events = _events(_post(client, "diesel 1200", mode="kharcha"))
    card = next(json.loads(data) for name, data in events if name == "action")

    undone = client.delete(f"/conversations/actions/{card['tool_call_id']}")

    assert undone.status_code == 200
    assert undone.json()["ok"] is True

    from app.db import get_supabase

    assert (
        get_supabase()
        .table("expenses")
        .select("id")
        .eq("shop_id", shop_id)
        .execute()
        .data
        == []
    )
    status = (
        get_supabase()
        .table("tool_calls")
        .select("status")
        .eq("id", card["tool_call_id"])
        .single()
        .execute()
        .data["status"]
    )
    assert status == "undone"


def test_history_restores_the_latest_action_card(client, fake_llm):
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "log_expense",
                        {"amount": 650, "note": "internet bill"},
                    )
                ]
            ),
            _model_message(content="Internet ka kharcha likh diya."),
        ]
    )
    _post(client, "internet 650", mode="kharcha")

    history = client.get("/conversations/history")

    assert history.status_code == 200
    assert history.json()["action"]["kind"] == "kharcha"
    assert history.json()["action"]["status"] == "recorded"
    assert history.json()["action"]["undoable"] is True


def test_pending_action_can_be_rejected_without_writing(
    client, fake_llm, shop_id
):
    from app.services import khata

    customer = khata.register_customer(
        shop_id=shop_id,
        name="Sara",
        cnic="35202-7654321-9",
    )
    khata.log_udhaar(shop_id=shop_id, customer_id=customer["id"], amount=700)
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "record_payment",
                        {"amount": 250, "khata_number": customer["khata_number"]},
                    )
                ]
            )
        ]
    )
    events = _events(_post(client, "Sara ne 250 diye", mode="udhaar"))
    card = next(json.loads(data) for name, data in events if name == "action")

    rejected = client.post(
        f"/conversations/actions/{card['tool_call_id']}/reject"
    )

    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert khata.customer_balance(shop_id=shop_id, customer_id=customer["id"]) == 700


def test_new_credit_customer_and_udhaar_complete_in_one_llm_selected_action(
    client, fake_llm, shop_id
):
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "log_udhaar",
                        {
                            "amount": 450,
                            "customer_name": "Akram",
                            "cnic": "42101-1234567-9",
                        },
                    )
                ]
            ),
            _model_message(content="Akram ka naya khata bana kar udhaar likh diya."),
        ]
    )

    events = _events(_post(client, "Akram 450 udhaar, CNIC 42101-1234567-9", mode="udhaar"))
    card = next(json.loads(data) for name, data in events if name == "action")

    from app.services import khata

    customers = khata.list_customers(shop_id=shop_id)
    assert card["status"] == "recorded"
    assert card["note"] == "Naya khata ban gaya."
    assert [(row["name"], row["balance"]) for row in customers] == [("Akram", 450)]

    undone = client.delete(f"/conversations/actions/{card['tool_call_id']}")
    assert undone.status_code == 200
    assert khata.list_customers(shop_id=shop_id) == []


def test_add_product_waits_for_approval_then_can_be_undone(
    client, fake_llm, shop_id
):
    from app.services import catalog

    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "add_product",
                        {
                            "name": "Nimko",
                            "sale_price": 80,
                            "cost_price": 55,
                            "stock": 12,
                        },
                    )
                ]
            )
        ]
    )

    events = _events(_post(client, "Nimko 80 rupay, 12 packet add karo", mode="maal"))
    card = next(json.loads(data) for name, data in events if name == "action")
    assert card["status"] == "proposed"
    assert catalog.resolve_product(shop_id=shop_id, term="Nimko") is None

    confirmed = client.post(
        f"/conversations/actions/{card['tool_call_id']}/confirm"
    )
    assert confirmed.status_code == 200
    recorded = confirmed.json()["card"]
    assert recorded["status"] == "recorded"
    assert recorded["undoable"] is True
    assert catalog.resolve_product(shop_id=shop_id, term="Nimko")["stock"] == 12

    undone = client.delete(f"/conversations/actions/{card['tool_call_id']}")
    assert undone.status_code == 200
    assert catalog.resolve_product(shop_id=shop_id, term="Nimko") is None


def test_llm_selected_sale_records_stock_and_exposes_generic_undo(
    client, fake_llm, shop_id
):
    from app.services import catalog

    product = catalog.add_product(
        shop_id=shop_id,
        name="Coke",
        sale_price=120,
        cost_price=90,
        stock=10,
    )
    fake_llm(
        tool_messages=[
            _model_message(
                calls=[
                    _tool_call(
                        "record_sale",
                        {
                            "items": [{"name": "Coke", "quantity": 2}],
                            "stated_total": 240,
                            "payment": "cash",
                        },
                    )
                ]
            ),
            _model_message(content="Sale record ho gayi."),
        ]
    )

    events = _events(_post(client, "2 coke 240", mode="sale"))
    card = next(json.loads(data) for name, data in events if name == "action")

    assert card["kind"] == "sale"
    assert card["status"] == "recorded"
    assert card["total"] == "₨ 240"
    assert catalog.resolve_product(shop_id=shop_id, term="Coke")["stock"] == 8

    assert client.delete(f"/conversations/actions/{card['tool_call_id']}").status_code == 200
    assert catalog.resolve_product(shop_id=shop_id, term=product["name"])["stock"] == 10


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

def test_orchestration_failure_does_not_persist_a_fake_assistant_reply(
    client, fake_llm, shop_id
):
    fake_llm(deltas=("adhoora",), fail_with=RuntimeError("boom"))

    events = _events(_post(client))
    assert "error" in [n for n, _ in events]

    conv = C.find_conversation(shop_id=shop_id)
    rows = C.list_messages(shop_id=shop_id, conversation_id=conv["id"])
    assert [r for r in rows if r["role"] == "assistant"] == []


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
    assert body == {"conversation_id": None, "messages": [], "action": None}


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
