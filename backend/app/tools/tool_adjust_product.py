"""adjust_product tool — CATLG-2, TOOL-1.

Adjusts a product's stock, sale price, or cost price by voice.
commit_undo: changes stock immediately; the change is visible on the
next inventory view but there is no automated undo (the shopkeeper
says the new number, so it's always intentional).
Available in "maal" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import catalog
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "product_name": {
            "type": "string",
            "description": "Spoken product name or alias to look up.",
        },
        "stock": {
            "type": ["integer", "null"],
            "description": "New absolute stock count (not a delta).",
            "minimum": 0,
        },
        "sale_price": {
            "type": ["number", "null"],
            "description": "New selling price per unit.",
            "exclusiveMinimum": 0,
        },
        "cost_price": {
            "type": ["number", "null"],
            "description": "New cost / purchase price per unit.",
            "minimum": 0,
        },
    },
    "required": ["product_name"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    term = (params.get("product_name") or "").strip()
    if not term:
        return {"ok": False, "reply": "Kaunsa item adjust karna hai?"}

    product = catalog.resolve_product(shop_id=shop_id, term=term)
    if not product:
        candidates = catalog.find_candidates(shop_id=shop_id, term=term)
        if candidates:
            names = ", ".join(c["name"] for c in candidates[:3])
            return {"ok": False, "reply": f"'{term}' nahi mila. Shayad: {names}?"}
        return {"ok": False, "reply": f"'{term}' catalog mein nahi hai."}

    updates: dict[str, Any] = {}
    stock = params.get("stock")
    sale_price = params.get("sale_price")
    cost_price = params.get("cost_price")

    if stock is not None:
        updates["stock"] = int(stock)
    if sale_price is not None:
        updates["sale_price"] = round(float(sale_price), 2)
    if cost_price is not None:
        updates["cost_price"] = round(float(cost_price), 2)

    if not updates:
        return {"ok": False, "reply": "Kya change karna hai? Stock, sale price, ya cost price?"}

    updated = catalog.update_product(shop_id=shop_id, product_id=product["id"], **updates)
    if not updated:
        return {"ok": False, "reply": "Update nahi ho saka. Dobara koshish karein."}

    changes = []
    if "stock" in updates:
        changes.append(f"stock {updates['stock']}")
    if "sale_price" in updates:
        changes.append(f"sale price ₨ {int(updates['sale_price'])}")
    if "cost_price" in updates:
        changes.append(f"cost price ₨ {int(updates['cost_price'])}")

    return {
        "ok": True,
        "product_id": product["id"],
        "product_name": product["name"],
        "changes": updates,
        "reply": f"{product['name']} ka {', '.join(changes)} update ho gaya.",
    }


get_registry().register(ToolDefinition(
    name="adjust_product",
    description=(
        "Adjust a product's stock count, sale price, or cost price by voice. "
        "Use when the shopkeeper says things like 'Coke ka stock 50 karo' or "
        "'chips ka daam 30 karo'."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    modes=["maal"],
    handler=_handler,
))
