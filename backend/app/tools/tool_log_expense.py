"""log_expense tool — EXP-2, TOOL-3 (commit_undo).

Logs money the shop spent. Commits immediately; undo removes the row.
Available in "kharcha" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import expenses as exp_svc
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "amount": {
            "type": "number",
            "description": "Amount spent (must be positive).",
            "exclusiveMinimum": 0,
        },
        "note": {
            "type": "string",
            "description": "Short description of what the expense was for.",
        },
    },
    "required": ["amount"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    user_id: str = ctx["user_id"]

    amount = params.get("amount")
    if not amount:
        return {"ok": False, "reply": "Amount batayein — kitne ka kharcha tha?"}

    note: str | None = params.get("note") or None

    try:
        row = exp_svc.create_expense(
            shop_id=shop_id,
            amount=float(amount),
            note=note,
            created_by=user_id,
        )
    except exp_svc.ExpenseError as exc:
        return {"ok": False, "reply": str(exc)}

    cat = (row.get("expense_categories") or {}).get("name") or row.get("category") or "Kharcha"
    return {
        "ok": True,
        "expense_id": row["id"],
        "amount": float(row["amount"]),
        "category": cat,
        "reply": f"Kharcha likh diya — {note or cat} ₨ {int(float(row['amount']))}.",
    }


get_registry().register(ToolDefinition(
    name="log_expense",
    description=(
        "Log a shop expense (money going out). "
        "Use when the shopkeeper says things like 'bijli ka bill 3000' or 'kiraya 15000 diya'."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    modes=["kharcha"],
    handler=_handler,
))
