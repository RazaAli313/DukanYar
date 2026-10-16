"""add_product tool — CATLG-1, TOOL-3 (approval_required).

Adds a new product to the shop catalog. approval_required because it
is a write to the catalog that the shopkeeper should confirm before it
persists — they typically dictate name, price, and starting stock.
Available in "maal" mode.
"""

from __future__ import annotations

from typing import Any

from app.services import catalog
from app.tools.cards import card_base, money
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
            "type": "number",
            "description": "Required acquisition / purchase cost for one unit.",
            "exclusiveMinimum": 0,
        },
        "stock": {
            "type": ["integer", "null"],
            "description": "Starting stock count (default 0).",
            "minimum": 0,
        },
    },
    "required": ["name", "sale_price", "cost_price"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    name = (params.get("name") or "").strip()
    if not name:
        return {"ok": False, "reply": "Product ka naam batayein."}

    sale_price = params.get("sale_price")
    if not sale_price:
        return {
            "ok": False,
            "needs_clarification": True,
            "reply": f"{name} ka sale price kya hai?",
        }

    cost_price = params.get("cost_price")
    if cost_price is None or float(cost_price) <= 0:
        return {
            "ok": False,
            "needs_clarification": True,
            "reply": f"{name} ka ek unit khareedne ka cost price kya hai?",
        }

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
            cost_price=float(cost_price),
            stock=int(params.get("stock") or 0),
        )
    except Exception as exc:
        return {"ok": False, "reply": f"Product add nahi ho saka: {exc}"}

    return {
        "ok": True,
        "product_id": product["id"],
        "product_name": product["name"],
        "sale_price": float(product["sale_price"]),
        "cost_price": float(product["cost_price"]),
        "stock": product["stock"],
        "reply": (
            f"{product['name']} catalog mein add ho gaya — "
            f"sale ₨ {int(float(product['sale_price']))}, "
            f"cost ₨ {int(float(product['cost_price']))}, stock {product['stock']}."
        ),
    }


def _present(
    *, params: dict[str, Any], result: dict[str, Any], tool_call_id: str, status: str
) -> dict[str, Any]:
    card = {
        **card_base(
            tool_name="add_product",
            tool_call_id=tool_call_id,
            status=status,
            result=result,
            undoable=status == "recorded",
        ),
        "kind": "maal",
        "title": "Naya Product",
        "lines": [
            {"label": params.get("name") or "Product", "value": ""},
            {"label": "Selling price", "value": money(float(params.get("sale_price") or 0))},
            {"label": "Purchase cost", "value": money(float(params.get("cost_price") or 0))},
            {"label": "Starting stock", "value": str(params.get("stock") or 0)},
        ],
        "total": money(float(params.get("sale_price") or 0)),
    }
    if status == "proposed":
        card["note"] = "Product add karne se pehle details check kar lein."
    return card


def _undo(*, result: dict[str, Any], ctx: dict[str, Any]) -> bool:
    product_id = result.get("product_id")
    return bool(
        product_id
        and catalog.delete_product(
            shop_id=ctx["shop_id"], product_id=product_id
        )
    )


get_registry().register(ToolDefinition(
    name="add_product",
    description=(
        "Add a new product to the shop catalog. "
        "approval_required — show the parsed product details and wait for the "
        "shopkeeper to say 'haan' before writing. "
        "Never add a product until the shopkeeper provides and confirms its "
        "name, selling price, acquisition cost per unit, and starting stock."
    ),
    parameters=_PARAMETERS,
    risk_tier="approval_required",
    handler=_handler,
    presenter=_present,
    undo=_undo,
))
