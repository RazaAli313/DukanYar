"""Conversations router — TEXT-2 streaming, TEXT-3 persistence, TEXT-5 modes.

POST /conversations/{conversation_id}/messages  send a message, stream the reply
POST /conversations/sale/confirm                execute a proposed sale
GET  /conversations/history                     reload the thread

Auth: ``Authorization: Bearer <supabase access token>``; the shop is resolved
from the profile, never the body. The conversation is the shop's single thread;
the path id is ignored.

The shopkeeper picks the mode on the dashboard (``sale`` | ``udhaar`` |
``kharcha`` | ``ask``), so the assistant never classifies intent. For ``sale``
the model does a structured parse and the router emits an ``action`` card the
shopkeeper confirms; every other mode is a normal streamed reply.
"""

import asyncio
import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from openai import APIError, APITimeoutError
from pydantic import BaseModel, Field

from app.auth import CurrentUserDep
from app.config import settings
from app.db import get_supabase
from app.services import catalog, expenses, sale
from app.services import khata as khata_svc
from app.services import conversations as convo
from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter()

Mode = Literal["sale", "udhaar", "kharcha", "ask"]


class Turn(BaseModel):
    role: str
    content: str


class MessageRequest(BaseModel):
    text: str
    channel: Literal["text", "voice"] = "text"
    mode: Mode = "ask"
    transcription_confidence: float | None = None
    #: Deprecated — context comes from the DB now. Accepted so old clients don't 422.
    recent_turns: list[Turn] = Field(default_factory=list, deprecated=True)


class SaleLine(BaseModel):
    name: str
    quantity: int


class SaleConfirmRequest(BaseModel):
    items: list[SaleLine]
    stated_total: float
    payment: Literal["cash", "udhaar"] = "cash"
    khata_number: int | None = None


class ExpenseConfirmRequest(BaseModel):
    amount: float
    desc: str | None = None


class UdhaarConfirmRequest(BaseModel):
    amount: float
    kind: Literal["udhaar", "payment"] = "udhaar"
    khata_number: int | None = None
    customer_name: str | None = None
    #: Set when registering a brand-new credit customer in the same step.
    cnic: str | None = None
    new_customer: bool = False


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _money(n: float) -> str:
    return f"₨ {int(round(n)):,}"


def _sale_card(
    status: str, resolved: list[dict], stated_total: float, note: str | None = None
) -> dict:
    # Stated-total primacy (SALE-3): the shopkeeper's spoken amount is the truth,
    # so line items show the name + quantity only — never a per-item price.
    lines = []
    for r in resolved:
        product = r.get("product")
        if product:
            lines.append({"label": f"{product['name']} × {r['quantity']}", "value": ""})
        else:
            lines.append(
                {
                    "label": f"{r['name']} × {r['quantity']}",
                    "value": "nahi mila",
                    "flag": True,
                }
            )
    return {
        "kind": "sale",
        "status": status,
        "title": "Naya Sale",
        "lines": lines,
        "total": _money(stated_total),
        "note": note,
    }


def _resolve_items(shop_id: str, items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        product = catalog.resolve_product(shop_id=shop_id, term=it.get("name", ""))
        out.append(
            {
                "name": it.get("name", ""),
                "quantity": int(it.get("quantity", 1)),
                "product": product,
            }
        )
    return out


def _udhaar_lookup(
    shop_id: str, khata: int | None, name: str | None, cnic: str | None
) -> str:
    """Resolve a customer and read back their balance. Read-only (KHATA-4)."""
    customer = None
    if khata:
        customer = khata_svc.find_customer(shop_id=shop_id, khata_number=khata)
    if customer is None and cnic:
        try:
            customer = khata_svc.find_customer(shop_id=shop_id, cnic=cnic)
        except khata_svc.KhataError:
            customer = None
    if customer is None and name:
        rows = (
            get_supabase()
            .table("customers")
            .select("id,khata_number,name")
            .eq("shop_id", shop_id)
            .ilike("name", f"%{name}%")
            .limit(1)
            .execute()
            .data
        )
        customer = rows[0] if rows else None

    if customer is None:
        which = f"Khata #{khata}" if khata else (name or "Ye customer")
        return f"{which} ka koi record nahi mila."

    balance = khata_svc.customer_balance(shop_id=shop_id, customer_id=customer["id"])
    who = customer.get("name") or f"Khata #{customer.get('khata_number')}"
    if balance > 0:
        return f"{who} (khata #{customer.get('khata_number')}) ke zimme {_money(balance)} udhaar hai."
    if balance < 0:
        return f"{who} ka {_money(-balance)} advance jama hai."
    return f"{who} (khata #{customer.get('khata_number')}) ka koi udhaar baqaya nahi."


async def _parse_record(
    mode: str, shop_id: str, turns: list[dict]
) -> tuple[dict | None, str]:
    """Parse a record-mode message -> (action card | None, reply text)."""
    if mode == "sale":
        p = await llm.extract_sale(turns)
        reply = str(p.get("reply") or "Theek hai?")
        if p.get("action") != "propose" or not p.get("items"):
            return None, reply
        resolved = _resolve_items(shop_id, p["items"])
        total = float(p.get("stated_total") or 0)
        card = _sale_card("proposed", resolved, total)
        is_udhaar = bool(p.get("khata_number")) or p.get("payment") == "udhaar"
        card["payment"] = "udhaar" if is_udhaar else "cash"
        card["khata_number"] = p.get("khata_number")
        card["_items"] = [{"name": r["name"], "quantity": r["quantity"]} for r in resolved]
        card["_stated_total"] = total
        return card, reply

    if mode == "kharcha":
        p = await llm.extract_expense(turns)
        reply = str(p.get("reply") or "Theek hai?")
        amount = p.get("amount")
        if p.get("action") != "propose" or not amount:
            return None, reply
        note = str(p.get("note") or "Kharcha")
        card = {
            "kind": "kharcha",
            "status": "proposed",
            "title": "Naya Kharcha",
            "lines": [{"label": note, "value": ""}],
            "total": _money(float(amount)),
            "note": None,
            "_amount": float(amount),
            "_desc": note,
        }
        return card, reply

    if mode == "udhaar":
        p = await llm.extract_udhaar(turns)
        reply = str(p.get("reply") or "Theek hai?")
        amount = p.get("amount")
        khata = p.get("khata_number")
        name = (p.get("customer_name") or "").strip() or None
        cnic_raw = (p.get("cnic") or "").strip() or None
        is_payment = p.get("kind") == "payment"

        # ── lookup: read-only balance / customer info (KHATA-4) ──────────────
        if p.get("action") == "lookup":
            return None, _udhaar_lookup(shop_id, khata, name, cnic_raw)

        if p.get("action") != "propose" or not amount or not (khata or name):
            return None, reply

        # Find an existing customer.
        existing = None
        if khata:
            existing = khata_svc.find_customer(shop_id=shop_id, khata_number=khata)
        elif cnic_raw:
            try:
                existing = khata_svc.find_customer(shop_id=shop_id, cnic=cnic_raw)
            except khata_svc.KhataError:
                existing = None
        if existing is None and name:
            rows = (
                get_supabase()
                .table("customers")
                .select("id,khata_number,name,cnic")
                .eq("shop_id", shop_id)
                .ilike("name", f"%{name}%")
                .limit(1)
                .execute()
                .data
            )
            existing = rows[0] if rows else None

        new_customer = False
        if existing:
            who = existing["name"] or f"Khata #{existing['khata_number']}"
        elif is_payment:
            # Cannot repay a khata that does not exist.
            return None, (
                f"{name} abhi registered nahi hain. Pehle unka udhaar likhein."
            )
        else:
            # New customer path — need name + a valid 13-digit CNIC.
            digits = "".join(ch for ch in (cnic_raw or "") if ch.isdigit())
            if len(digits) != 13:
                return None, (
                    f"{name} naya customer hai. Unki CNIC bhi batayein "
                    f"(13 digits, jaise 12345-1234567-1)."
                )
            new_customer = True
            who = f"{name} (naya khata)"

        card = {
            "kind": "udhaar",
            "status": "proposed",
            "title": "Udhaar wapsi" if is_payment else "Naya Udhaar",
            "lines": [{"label": who, "value": ""}],
            "total": _money(float(amount)),
            "note": (
                "Wapsi confirm karne se pehle check kar lein."
                if is_payment
                else ("Naya khata banega." if new_customer else None)
            ),
            "_amount": float(amount),
            "_kind": "payment" if is_payment else "udhaar",
            "_khata_number": existing["khata_number"] if existing else None,
            "_customer_name": name,
            "_cnic": cnic_raw if new_customer else None,
            "_new": new_customer,
        }
        return card, reply

    return None, "Theek hai?"


# ── send a message ───────────────────────────────────────────────────────────

@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, body: MessageRequest, user: CurrentUserDep):
    try:
        llm._get_client()  # noqa: SLF001 — pre-flight before any write
    except Exception as exc:
        logger.exception("LLM client init failed")
        raise HTTPException(status_code=502, detail=f"LLM config error: {exc}") from exc

    conversation = convo.get_or_create_conversation(shop_id=user.shop_id, user_id=user.user_id)
    conv_id = conversation["id"]
    prior = convo.recent_turns(conversation_id=conv_id, max_turns=settings.llm_max_context_turns)

    # Voice transcripts arrive in Urdu script; store and reason over Roman-Urdu
    # so the whole thread reads the way the shopkeeper types.
    user_text = body.text
    if body.channel == "voice":
        user_text = await llm.to_roman_urdu(body.text)

    convo.add_message(
        conversation_id=conv_id,
        sender=convo.SENDER_USER,
        content=user_text,
        channel=body.channel,
        transcription_confidence=(
            body.transcription_confidence if body.channel == "voice" else None
        ),
    )
    turns = prior + [{"role": "user", "content": user_text}]

    async def event_stream():
        chunks: list[str] = []

        def persist(text: str, status: str) -> None:
            if not text.strip():
                return
            try:
                convo.add_message(
                    conversation_id=conv_id,
                    sender=convo.SENDER_ASSISTANT,
                    content=text,
                    channel=body.channel,
                    status=status,
                )
            except Exception:
                logger.exception("failed to persist assistant reply")

        yield _sse("meta", {"conversation_id": conv_id, "user_text": user_text})

        # ── record modes: structured parse -> propose card / clarify ─────────
        if body.mode in ("sale", "kharcha", "udhaar"):
            try:
                card, reply = await _parse_record(body.mode, user.shop_id, turns)
            except (APIError, APITimeoutError) as exc:
                yield _sse("error", {"detail": f"LLM error: {exc}"})
                return
            for word in reply.split(" "):
                yield _sse("delta", {"text": word + " "})
            if card:
                yield _sse("action", card)
            persist(reply.strip(), convo.STATUS_COMPLETE)
            yield _sse("done", {"conversation_id": conv_id})
            return

        # ── every other mode: normal streamed reply ─────────────────────────
        try:
            async for delta in llm.stream_reply(turns, channel=body.channel, mode=body.mode):
                chunks.append(delta)
                yield _sse("delta", {"text": delta})
        except asyncio.CancelledError:
            await asyncio.shield(
                asyncio.to_thread(persist, "".join(chunks), convo.STATUS_FAILED)
            )
            raise
        except (APIError, APITimeoutError) as exc:
            persist("".join(chunks), convo.STATUS_FAILED)
            yield _sse("error", {"detail": f"LLM error: {exc}"})
            return
        except Exception as exc:
            logger.exception("Unexpected error mid-stream")
            persist("".join(chunks), convo.STATUS_FAILED)
            yield _sse("error", {"detail": f"Internal error: {exc}"})
            return

        persist("".join(chunks), convo.STATUS_COMPLETE)
        yield _sse("done", {"conversation_id": conv_id})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── confirm a proposed sale ──────────────────────────────────────────────────

@router.post("/sale/confirm")
def confirm_sale(body: SaleConfirmRequest, user: CurrentUserDep) -> dict[str, Any]:
    resolved = _resolve_items(user.shop_id, [i.model_dump() for i in body.items])
    unresolved = [r["name"] for r in resolved if not r.get("product")]
    if unresolved:
        raise HTTPException(422, f"Ye items nahi mile: {', '.join(unresolved)}")

    customer_id = None
    payment = body.payment
    if body.khata_number is not None:
        cust = (
            get_supabase()
            .table("customers")
            .select("id")
            .eq("shop_id", user.shop_id)
            .eq("khata_number", body.khata_number)
            .limit(1)
            .execute()
            .data
        )
        if not cust:
            raise HTTPException(422, f"Khata #{body.khata_number} nahi mila")
        customer_id = cust[0]["id"]
        payment = "udhaar"

    line_items = [
        {
            "product_id": r["product"]["id"],
            "quantity": r["quantity"],
            "unit_price": float(r["product"]["sale_price"]),
        }
        for r in resolved
    ]

    try:
        result = sale.record_sale(
            shop_id=user.shop_id,
            items=line_items,
            total_amount=body.stated_total,
            payment_type=payment,
            customer_id=customer_id,
            created_by=user.user_id,
        )
    except sale.SaleError as exc:
        raise HTTPException(422, str(exc)) from exc

    warn = ""
    if result["stock_alerts"]:
        names = ", ".join(a["name"] for a in result["stock_alerts"])
        warn = f" Stock khatam ho raha hai: {names}."
    conv = convo.get_or_create_conversation(shop_id=user.shop_id, user_id=user.user_id)
    convo.add_message(
        conversation_id=conv["id"],
        sender=convo.SENDER_ASSISTANT,
        content=f"Sale record ho gayi — total {_money(result['total_amount'])}.{warn}",
    )

    return {
        "ok": True,
        "sale_id": result["sale_id"],
        "card": _sale_card(
            "recorded", resolved, result["total_amount"], note=warn.strip() or None
        ),
        "stock_alerts": result["stock_alerts"],
    }


@router.post("/expense/confirm")
def confirm_expense(body: ExpenseConfirmRequest, user: CurrentUserDep) -> dict[str, Any]:
    try:
        row = expenses.create_expense(
            shop_id=user.shop_id,
            amount=body.amount,
            note=body.desc,
            created_by=user.user_id,
        )
    except expenses.ExpenseError as exc:
        raise HTTPException(422, str(exc)) from exc

    conv = convo.get_or_create_conversation(shop_id=user.shop_id, user_id=user.user_id)
    convo.add_message(
        conversation_id=conv["id"],
        sender=convo.SENDER_ASSISTANT,
        content=f"Kharcha likh diya — {_money(float(row['amount']))}.",
    )
    cat = (row.get("expense_categories") or {}).get("name")
    return {
        "ok": True,
        "expense_id": row["id"],
        "card": {
            "kind": "kharcha",
            "status": "recorded",
            "title": "Kharcha",
            "lines": [{"label": body.desc or cat or "Kharcha", "value": ""}],
            "total": _money(float(row["amount"])),
            "note": None,
        },
    }


@router.post("/udhaar/confirm")
def confirm_udhaar(body: UdhaarConfirmRequest, user: CurrentUserDep) -> dict[str, Any]:
    customer = None
    newly_registered = False

    if body.new_customer and body.customer_name and body.cnic:
        # Register the credit customer, then log against the fresh khata number.
        try:
            customer = khata_svc.register_customer(
                shop_id=user.shop_id,
                name=body.customer_name.strip(),
                cnic=body.cnic,
            )
            newly_registered = True
        except khata_svc.DuplicateCustomerError as exc:
            customer = exc.customer  # already exists — reuse it
        except khata_svc.KhataError as exc:
            raise HTTPException(422, str(exc)) from exc
    elif body.khata_number is not None:
        customer = khata_svc.find_customer(shop_id=user.shop_id, khata_number=body.khata_number)
    elif body.customer_name:
        rows = (
            get_supabase()
            .table("customers")
            .select("id,khata_number,name")
            .eq("shop_id", user.shop_id)
            .ilike("name", f"%{body.customer_name.strip()}%")
            .limit(1)
            .execute()
            .data
        )
        customer = rows[0] if rows else None

    if not customer:
        raise HTTPException(422, "Ye customer / khata nahi mila. Pehle register karein.")

    try:
        if body.kind == "payment":
            res = khata_svc.record_payment(
                shop_id=user.shop_id,
                customer_id=customer["id"],
                amount=body.amount,
                created_by=user.user_id,
            )
        else:
            res = khata_svc.log_udhaar(
                shop_id=user.shop_id,
                customer_id=customer["id"],
                amount=body.amount,
                created_by=user.user_id,
            )
    except khata_svc.KhataError as exc:
        raise HTTPException(422, str(exc)) from exc

    khata_no = customer.get("khata_number")
    who = customer.get("name") or f"Khata #{khata_no}"
    verb = "wapsi" if body.kind == "payment" else "udhaar"
    reg_note = (
        f"{who} ka naya khata ban gaya — number {khata_no}. Ye number yaad rakhein."
        if newly_registered
        else None
    )
    conv = convo.get_or_create_conversation(shop_id=user.shop_id, user_id=user.user_id)
    convo.add_message(
        conversation_id=conv["id"],
        sender=convo.SENDER_ASSISTANT,
        content=(
            (f"{reg_note} " if reg_note else "")
            + f"{who} ki {verb} {_money(body.amount)} likh di. "
            + f"Naya balance {_money(res['balance'])}."
        ),
    )
    return {
        "ok": True,
        "balance": res["balance"],
        "khata_number": khata_no,
        "card": {
            "kind": "udhaar",
            "status": "recorded",
            "title": "Udhaar wapsi" if body.kind == "payment" else "Udhaar",
            "lines": [
                {"label": who, "value": f"Khata #{khata_no}"},
                {"label": "Naya balance", "value": _money(res["balance"])},
            ],
            "total": _money(body.amount),
            "note": reg_note,
        },
    }


# ── history ──────────────────────────────────────────────────────────────────

@router.get("/history")
def get_history(
    user: CurrentUserDep,
    limit: int = Query(convo.DEFAULT_HISTORY_LIMIT, ge=1, le=convo.MAX_HISTORY_LIMIT),
):
    conversation = convo.find_conversation(shop_id=user.shop_id)
    if conversation is None:
        return {"conversation_id": None, "messages": []}
    return {
        "conversation_id": conversation["id"],
        "messages": convo.list_messages(
            shop_id=user.shop_id, conversation_id=conversation["id"], limit=limit
        ),
    }
