"""log_udhaar tool — KHATA-2, TOOL-1.

Records credit given to a customer and logs it in the ledger.
commit_undo: commits immediately; reverse_ledger_entry undoes it.
Available in "udhaar" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import khata as khata_svc
from app.tools.cards import card_base, money
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "amount": {
            "type": "number",
            "description": "Amount of credit given (must be positive).",
            "exclusiveMinimum": 0,
        },
        "khata_number": {
            "type": ["integer", "null"],
            "description": "Customer's khata number.",
        },
        "customer_name": {
            "type": ["string", "null"],
            "description": "Customer name to search if khata_number is unknown.",
        },
        "cnic": {
            "type": ["string", "null"],
            "description": (
                "13-digit CNIC. Required with customer_name only when the customer "
                "is new; the tool registers the khata before logging udhaar."
            ),
        },
        "sale_id": {
            "type": ["string", "null"],
            "description": "Link to an existing sale UUID (optional).",
        },
    },
    "required": ["amount"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    user_id: str = ctx["user_id"]

    amount = params.get("amount")
    if not amount:
        return {"ok": False, "reply": "Amount batayein — kitna udhaar diya?"}

    khata_number = params.get("khata_number")
    customer_name = (params.get("customer_name") or "").strip() or None

    customer = None
    if khata_number:
        customer = khata_svc.find_customer(shop_id=shop_id, khata_number=int(khata_number))
    elif customer_name:
        from app.db import get_supabase
        rows = (
            get_supabase()
            .table("customers")
            .select("id,khata_number,name")
            .eq("shop_id", shop_id)
            .ilike("name", f"%{customer_name}%")
            .limit(1)
            .execute()
            .data
        )
        customer = rows[0] if rows else None

    customer_created = False
    if not customer and customer_name and params.get("cnic"):
        try:
            customer = khata_svc.register_customer(
                shop_id=shop_id,
                name=customer_name,
                cnic=str(params["cnic"]),
            )
            customer_created = True
        except khata_svc.DuplicateCustomerError as exc:
            customer = exc.customer
        except khata_svc.KhataError as exc:
            return {"ok": False, "reply": str(exc)}

    if not customer:
        who = f"Khata #{khata_number}" if khata_number else (customer_name or "Ye customer")
        suffix = " Naam ke saath 13-digit CNIC bhi batayein." if customer_name else ""
        return {
            "ok": False,
            "reply": f"{who} ka record nahi mila.{suffix or ' Pehle register karein.'}",
        }

    try:
        res = khata_svc.log_udhaar(
            shop_id=shop_id,
            customer_id=customer["id"],
            amount=float(amount),
            sale_id=params.get("sale_id"),
            created_by=user_id,
        )
    except khata_svc.KhataError as exc:
        if customer_created:
            khata_svc.delete_customer(
                shop_id=shop_id, customer_id=customer["id"]
            )
        return {"ok": False, "reply": str(exc)}

    who = customer.get("name") or f"Khata #{customer.get('khata_number')}"
    return {
        "ok": True,
        "entry_id": res["entry"]["id"],
        "customer_id": customer["id"],
        "customer_name": who,
        "customer_created": customer_created,
        "khata_number": customer.get("khata_number"),
        "new_balance": res["balance"],
        "reply": f"{who} ko ₨ {int(float(amount))} udhaar likh diya. Naya balance ₨ {int(res['balance'])}.",
    }


def _present(
    *, params: dict[str, Any], result: dict[str, Any], tool_call_id: str, status: str
) -> dict[str, Any]:
    who = (
        f"Khata #{params['khata_number']}"
        if params.get("khata_number")
        else params.get("customer_name") or "Customer"
    )
    card = {
        **card_base(
            tool_name="log_udhaar",
            tool_call_id=tool_call_id,
            status=status,
            result=result,
            undoable=status == "recorded",
        ),
        "kind": "udhaar",
        "title": "Naya Udhaar",
        "lines": [{"label": who, "value": ""}],
        "total": money(float(params.get("amount") or 0)),
    }
    if result.get("customer_created") and status == "recorded":
        card["note"] = "Naya khata ban gaya."
    return card


def _undo(*, result: dict[str, Any], ctx: dict[str, Any]) -> bool:
    entry_id = result.get("entry_id")
    if not entry_id or not khata_svc.reverse_ledger_entry(
        shop_id=ctx["shop_id"], entry_id=entry_id
    ):
        return False
    if result.get("customer_created") and result.get("customer_id"):
        return khata_svc.delete_customer(
            shop_id=ctx["shop_id"], customer_id=result["customer_id"]
        )
    return True


get_registry().register(ToolDefinition(
    name="log_udhaar",
    description=(
        "Log credit given to a customer on their khata (ledger). "
        "Use when the shopkeeper says someone took goods on credit or owes money."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    handler=_handler,
    presenter=_present,
    undo=_undo,
))
