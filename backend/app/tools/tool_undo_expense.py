"""undo_expense tool — EXP-2, TOOL-3 (commit_undo).

Deletes a committed expense row. Available in "kharcha" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import expenses as exp_svc
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "expense_id": {
            "type": "string",
            "description": "UUID of the expense to undo (from the confirmation card).",
        },
    },
    "required": ["expense_id"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    expense_id: str = params.get("expense_id") or ""
    if not expense_id:
        return {"ok": False, "reply": "Expense ID nahi mila."}

    removed = exp_svc.delete_expense(shop_id=shop_id, expense_id=expense_id)
    if not removed:
        return {"ok": False, "reply": "Ye kharcha nahi mila ya pehle se hata diya gaya tha."}

    return {"ok": True, "expense_id": expense_id, "reply": "Kharcha wapas ho gaya."}


get_registry().register(ToolDefinition(
    name="undo_expense",
    description="Undo / delete a previously logged expense. Use when the shopkeeper says 'undo' after logging a kharcha.",
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    modes=["kharcha"],
    handler=_handler,
))
