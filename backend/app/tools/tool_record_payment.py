"""record_payment tool — KHATA-3, TOOL-3 (approval_required).

Records a customer repayment. Risk tier is approval_required because it
moves money-in: the shopkeeper's explicit confirmation is required before
this writes. The orchestration layer gates execution behind the approval
flow and only calls this handler AFTER approval is confirmed.
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
            "description": "Amount being repaid (must be positive).",
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
    },
    "required": ["amount"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    user_id: str = ctx["user_id"]

    amount = params.get("amount")
    if not amount:
        return {"ok": False, "reply": "Amount batayein — kitna wapas aaya?"}

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
        return {"ok": False, "reply": f"{who} ka record nahi mila."}

    try:
        res = khata_svc.record_payment(
            shop_id=shop_id,
            customer_id=customer["id"],
            amount=float(amount),
            created_by=user_id,
        )
    except khata_svc.KhataError as exc:
        return {"ok": False, "reply": str(exc)}

    who = customer.get("name") or f"Khata #{customer.get('khata_number')}"
    balance = res["balance"]
    balance_str = (
        f"Naya balance ₨ {int(balance)} baqaya hai."
        if balance > 0
        else ("Hisaab barabar!" if balance == 0 else f"₨ {int(-balance)} advance jama hai.")
    )
    return {
        "ok": True,
        "entry_id": res["entry"]["id"],
        "khata_number": customer.get("khata_number"),
        "new_balance": balance,
        "reply": f"{who} ki ₨ {int(float(amount))} wapsi likh di. {balance_str}",
    }


get_registry().register(ToolDefinition(
    name="record_payment",
    description=(
        "Record a customer repayment (udhaar wapsi). "
        "This is approval_required — always show the parsed action to the shopkeeper "
        "and wait for 'haan' / 'confirm' before executing."
    ),
    parameters=_PARAMETERS,
    risk_tier="approval_required",
    modes=["udhaar"],
    handler=_handler,
))
