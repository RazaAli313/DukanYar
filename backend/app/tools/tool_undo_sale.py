"""undo_sale tool — TOOL-3, SALE-3.

Reverses a committed sale: restores stock and removes any linked ledger entry.
Available in "sale" mode so the shopkeeper can say "woh wali sale hatao".
"""

from __future__ import annotations

from typing import Any

from app.services import sale as sale_svc
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sale_id": {
            "type": "string",
            "description": "UUID of the sale to undo (from the confirmation card or prior turn).",
        },
    },
    "required": ["sale_id"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    sale_id: str = params.get("sale_id") or ""
    if not sale_id:
        return {"ok": False, "reply": "Sale ID nahi mila. Kaunsi sale wapas karni hai?"}

    removed = sale_svc.reverse_sale(shop_id=shop_id, sale_id=sale_id)
    if not removed:
        return {"ok": False, "reply": "Ye sale nahi mili ya pehle se hata di gayi thi."}

    return {
        "ok": True,
        "sale_id": sale_id,
        "reply": "Sale wapas ho gayi. Stock restore kar diya.",
    }


get_registry().register(ToolDefinition(
    name="undo_sale",
    description=(
        "Undo a previously recorded sale and restore stock. "
        "Use when the shopkeeper says 'undo', 'wapas karo', or 'galti ho gayi'."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    modes=["sale"],
    handler=_handler,
))
