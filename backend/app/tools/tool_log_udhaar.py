"""log_udhaar tool — KHATA-2, TOOL-1.

Records credit given to a customer and logs it in the ledger.
commit_undo: commits immediately; reverse_ledger_entry undoes it.
Available in "udhaar" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import khata as khata_svc
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

    if not customer:
        who = f"Khata #{khata_number}" if khata_number else (customer_name or "Ye customer")
        return {"ok": False, "reply": f"{who} ka record nahi mila. Pehle register karein."}

    try:
        res = khata_svc.log_udhaar(
            shop_id=shop_id,
            customer_id=customer["id"],
            amount=float(amount),
            sale_id=params.get("sale_id"),
            created_by=user_id,
        )
    except khata_svc.KhataError as exc:
        return {"ok": False, "reply": str(exc)}

    who = customer.get("name") or f"Khata #{customer.get('khata_number')}"
    return {
        "ok": True,
        "entry_id": res["entry"]["id"],
        "khata_number": customer.get("khata_number"),
        "new_balance": res["balance"],
        "reply": f"{who} ko ₨ {int(float(amount))} udhaar likh diya. Naya balance ₨ {int(res['balance'])}.",
    }


get_registry().register(ToolDefinition(
    name="log_udhaar",
    description=(
        "Log credit given to a customer on their khata (ledger). "
        "Use when the shopkeeper says someone took goods on credit or owes money."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    modes=["udhaar"],
    handler=_handler,
))
