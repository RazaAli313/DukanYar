"""record_sale tool — SALE-3, SALE-4, TOOL-1.

Self-registers with the runtime registry at import time.
Available in "sale" mode only (the shopkeeper picked the mode on the
dashboard, so the orchestrator never runs this tool in ask/kharcha/udhaar).
"""

from __future__ import annotations

from typing import Any

from app.services import catalog, sale as sale_svc
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "description": "Line items the shopkeeper mentioned.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Spoken product name or alias"},
                    "quantity": {"type": "integer", "minimum": 1},
                },
                "required": ["name", "quantity"],
            },
        },
        "stated_total": {
            "type": "number",
            "description": "Total amount the shopkeeper stated (source of truth).",
            "minimum": 0,
        },
        "payment": {
            "type": "string",
            "enum": ["cash", "udhaar"],
            "description": "cash unless a khata number was mentioned.",
        },
        "khata_number": {
            "type": ["integer", "null"],
            "description": "Customer khata number for udhaar sales.",
        },
    },
    "required": ["items", "stated_total"],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    user_id: str = ctx["user_id"]

    raw_items: list[dict[str, Any]] = params.get("items") or []
    resolved = []
    unresolved: list[str] = []
    ambiguous: list[str] = []

    for it in raw_items:
        name = it.get("name", "")
        qty = int(it.get("quantity") or 1)
        product = catalog.resolve_product(shop_id=shop_id, term=name)
        if product:
            resolved.append({
                "product_id": product["id"],
                "name": product["name"],
                "quantity": qty,
                "unit_price": float(product["sale_price"]),
            })
        else:
            # Try to find near-matches for disambiguation
            candidates = catalog.find_candidates(shop_id=shop_id, term=name)
            if len(candidates) > 1:
                ambiguous.append(f"{name} (shayad: {', '.join(c['name'] for c in candidates[:3])})")
            else:
                unresolved.append(name)

    if ambiguous:
        return {
            "ok": False,
            "needs_clarification": True,
            "reply": f"Ye items bilkul clear nahi hain — kaunse wale chahiye? {'; '.join(ambiguous)}",
        }
    if unresolved:
        return {
            "ok": False,
            "needs_clarification": True,
            "reply": f"Ye items catalog mein nahi mile: {', '.join(unresolved)}. Naam check kar ke dobara boliye.",
        }
    if not resolved:
        return {"ok": False, "reply": "Koi item nahi mila."}

    stated_total = float(params.get("stated_total") or 0)
    payment = params.get("payment") or "cash"
    khata_number = params.get("khata_number")

    customer_id: str | None = None
    if khata_number:
        from app.services import khata as khata_svc
        cust = khata_svc.find_customer(shop_id=shop_id, khata_number=int(khata_number))
        if not cust:
            return {"ok": False, "reply": f"Khata #{khata_number} nahi mila."}
        customer_id = cust["id"]
        payment = "udhaar"

    try:
        result = sale_svc.record_sale(
            shop_id=shop_id,
            items=resolved,
            total_amount=stated_total,
            payment_type=payment,
            customer_id=customer_id,
            created_by=user_id,
        )
    except sale_svc.SaleError as exc:
        return {"ok": False, "reply": str(exc)}

    alerts = result["stock_alerts"]
    warn = f" Chetavni: {', '.join(a['name'] for a in alerts)} khatam ho rahi hai." if alerts else ""
    return {
        "ok": True,
        "sale_id": result["sale_id"],
        "total_amount": result["total_amount"],
        "payment_type": result["payment_type"],
        "stock_alerts": alerts,
        "reply": f"Sale record ho gayi — total ₨ {int(result['total_amount'])}.{warn}",
    }


get_registry().register(ToolDefinition(
    name="record_sale",
    description=(
        "Record a sale with items, quantities and the shopkeeper's stated total. "
        "The stated total is always the source of truth. "
        "Set payment='udhaar' and khata_number only when the shopkeeper names a khata."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",
    modes=["sale"],
    handler=_handler,
))
