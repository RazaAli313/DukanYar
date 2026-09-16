"""udhaar_summary tool — RPT-3, TOOL-1.

Returns the list of credit customers and their outstanding balances for the
"ask" mode. Read-only.
Available in "ask" and "udhaar" modes.
"""

from __future__ import annotations

from typing import Any

from app.services import khata as khata_svc
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "khata_number": {
            "type": ["integer", "null"],
            "description": "If provided, return only this customer's balance.",
        },
        "customer_name": {
            "type": ["string", "null"],
            "description": "Partial name search — returns matching customer(s).",
        },
    },
    "required": [],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    khata_number = params.get("khata_number")
    customer_name = (params.get("customer_name") or "").strip() or None

    def _pk(n: float) -> str:
        return f"₨ {int(round(n)):,}"

    # Single customer lookup
    if khata_number or customer_name:
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
            who = f"Khata #{khata_number}" if khata_number else customer_name
            return {"ok": False, "reply": f"{who} ka koi record nahi mila."}

        balance = khata_svc.customer_balance(shop_id=shop_id, customer_id=customer["id"])
        who = customer.get("name") or f"Khata #{customer.get('khata_number')}"
        if balance > 0:
            reply = f"{who} (khata #{customer.get('khata_number')}) ke zimme {_pk(balance)} udhaar hai."
        elif balance < 0:
            reply = f"{who} ka {_pk(-balance)} advance jama hai."
        else:
            reply = f"{who} ka koi udhaar baqaya nahi."

        return {
            "ok": True,
            "customers": [{"name": who, "khata_number": customer.get("khata_number"), "balance": balance}],
            "reply": reply,
        }

    # All customers summary
    customers = khata_svc.list_customers(shop_id=shop_id, limit=50)
    total_outstanding = sum(c["balance"] for c in customers if c["balance"] > 0)
    debtors = [c for c in customers if c["balance"] > 0]

    if not customers:
        return {"ok": True, "customers": [], "reply": "Koi credit customer nahi hai abhi."}

    top = debtors[:3]
    top_str = "; ".join(
        f"{c.get('name') or 'Khata #' + str(c['khata_number'])} {_pk(c['balance'])}"
        for c in top
    )
    reply = f"Total baqaya udhaar {_pk(total_outstanding)}, {len(debtors)} customers mein."
    if top_str:
        reply += f" Sab se zyada: {top_str}."

    return {
        "ok": True,
        "customers": [
            {
                "name": c.get("name"),
                "khata_number": c.get("khata_number"),
                "balance": c["balance"],
            }
            for c in customers
        ],
        "total_outstanding": total_outstanding,
        "reply": reply,
    }


get_registry().register(ToolDefinition(
    name="udhaar_summary",
    description=(
        "Return outstanding udhaar balances for one customer (by name or khata number) "
        "or all customers. Use when the shopkeeper asks 'khata kya hai', 'Akram ka "
        "udhaar', 'sab ka baqaya batao', etc."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",  # read-only; tier is just for classification
    modes=["ask", "udhaar"],
    handler=_handler,
))
