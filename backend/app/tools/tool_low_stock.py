"""low_stock tool — RPT-4, TOOL-1.

Returns items that are running low (stock ≤ threshold). Read-only.
Available in "ask" mode.
"""

from __future__ import annotations

from typing import Any

from app.db import get_supabase
from app.tools.registry import ToolDefinition, get_registry

_DEFAULT_THRESHOLD = 5

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "threshold": {
            "type": ["integer", "null"],
            "description": f"Stock count at or below which an item is 'low'. Default {_DEFAULT_THRESHOLD}.",
            "minimum": 0,
        },
    },
    "required": [],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    threshold = int(params.get("threshold") or _DEFAULT_THRESHOLD)

    rows = (
        get_supabase()
        .table("products")
        .select("id,name,stock")
        .eq("shop_id", shop_id)
        .lte("stock", threshold)
        .order("stock")
        .execute()
        .data
    )

    if not rows:
        return {
            "ok": True,
            "items": [],
            "reply": f"Sab items ka stock theek hai (threshold {threshold}).",
        }

    names = ", ".join(
        f"{r['name']} ({r['stock']} baqaya)" for r in rows[:5]
    )
    more = f" aur {len(rows) - 5} aur" if len(rows) > 5 else ""
    return {
        "ok": True,
        "items": [{"id": r["id"], "name": r["name"], "stock": r["stock"]} for r in rows],
        "reply": f"Khatam hone wala maal: {names}{more}. Mungwa lein!",
    }


get_registry().register(ToolDefinition(
    name="low_stock",
    description=(
        "Return products whose stock is at or below a threshold (default 5). "
        "Use when the shopkeeper asks 'kya khatam ho raha hai', 'stock check karo', "
        "'kya mangwana chahiye', etc."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",  # read-only; tier is for classification only
    modes=["ask"],
    handler=_handler,
))
