"""add_product tool — CATLG-1, TOOL-3 (approval_required).

Adds a new product to the shop catalog. approval_required because it
is a write to the catalog that the shopkeeper should confirm before it
persists — they typically dictate name, price, and starting stock.
Available in "maal" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import catalog
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Product name as the shopkeeper said it.",
        },
        "sale_price": {
            "type": "number",
            "description": "Selling price per unit.",
            "exclusiveMinimum": 0,
        },
        "cost_price": {
            "type": ["number", "null"],
            "description": "Purchase / cost price per unit (optional).",
            "minimum": 0,
        },
        "stock": {
            "type": ["integer", "null"],
            "description": "Starting stock count (default 0).",
            "minimum": 0,
        },
        "unit": {
            "type": ["string", "null"],
            "description": "Unit of measure, e.g. 'bottle', 'kg', 'packet' (optional).",
        },
    },
    "required": ["name", "sale_price"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    name = (params.get("name") or "").strip()
    if not name:
        return {"ok": False, "reply": "Product ka naam batayein."}

    sale_price = params.get("sale_price")
    if not sale_price:
        return {"ok": False, "reply": f"{name} ka sale price kya hai?"}

    # Check for an existing product with the same name to avoid accidental duplicates.
    existing = catalog.resolve_product(shop_id=shop_id, term=name)
    if existing and existing["name"].lower() == name.lower():
        return {
            "ok": False,
            "reply": (
                f"'{name}' pehle se catalog mein hai (stock {existing['stock']}, "
                f"₨ {int(float(existing['sale_price']))}). Adjust karna ho to adjust_product use karein."
            ),
        }

    try:
        product = catalog.add_product(
            shop_id=shop_id,
            name=name,
            sale_price=float(sale_price),
            cost_price=float(params.get("cost_price") or 0),
            stock=int(params.get("stock") or 0),
            unit=params.get("unit"),
        )
    except Exception as exc:
        return {"ok": False, "reply": f"Product add nahi ho saka: {exc}"}

    return {
        "ok": True,
        "product_id": product["id"],
        "product_name": product["name"],
        "sale_price": float(product["sale_price"]),
        "stock": product["stock"],
        "reply": (
            f"{product['name']} catalog mein add ho gaya — "
            f"₨ {int(float(product['sale_price']))}, stock {product['stock']}."
        ),
    }


get_registry().register(ToolDefinition(
    name="add_product",
    description=(
        "Add a new product to the shop catalog. "
        "approval_required — show the parsed product details and wait for the "
        "shopkeeper to say 'haan' before writing. "
        "Use when the shopkeeper dictates a new item's name and price."
    ),
    parameters=_PARAMETERS,
    risk_tier="approval_required",
    modes=["maal"],
    handler=_handler,
))
