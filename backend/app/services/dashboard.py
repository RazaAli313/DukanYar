"""Dashboard read model — the shopkeeper's "aaj" snapshot (RPT-2/3/4).

Reads the reporting views and recent activity, all scoped by shop_id. Backend
service_role key → no dependency on auth.jwt() app_metadata / current_shop_id().
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.db import get_supabase

_LOW_STOCK_THRESHOLD = 5


def today_snapshot(*, shop_id: str) -> dict[str, Any]:
    sb = get_supabase()
    today = date.today().isoformat()

    # ── today's sales ────────────────────────────────────────────────────────
    sales = (
        sb.table("sales")
        .select("id,total_amount,payment_type,created_at")
        .eq("shop_id", shop_id)
        .gte("created_at", f"{today}T00:00:00")
        .execute()
        .data
    )
    sale_ids = [s["id"] for s in sales]
    total_sale = round(sum(float(s["total_amount"]) for s in sales), 2)
    udhaar_today = round(
        sum(float(s["total_amount"]) for s in sales if s["payment_type"] in ("udhaar", "split")),
        2,
    )

    # Profit = Σ (sale_price - cost_price) × quantity for today's sold_items.
    # This is COGS-based, not a flat margin (RPT-2).
    profit = 0.0
    if sale_ids:
        sold_items = (
            sb.table("sold_items")
            .select("quantity,unit_price,products(cost_price)")
            .in_("sale_id", sale_ids)
            .execute()
            .data
        )
        for item in sold_items:
            cost = float((item.get("products") or {}).get("cost_price") or 0)
            price = float(item.get("unit_price") or 0)
            qty = int(item.get("quantity") or 0)
            profit += (price - cost) * qty
    profit = round(profit, 2)

    # ── today's expenses ─────────────────────────────────────────────────────
    expenses = (
        sb.table("expenses")
        .select("amount")
        .eq("shop_id", shop_id)
        .gte("expense_date", today)
        .execute()
        .data
    )
    total_kharcha = round(sum(float(e["amount"]) for e in expenses), 2)

    # ── outstanding udhaar across all customers ──────────────────────────────
    ledger = (
        sb.table("ledger_entries")
        .select("type,amount")
        .eq("shop_id", shop_id)
        .execute()
        .data
    )
    outstanding = round(
        sum(
            float(l["amount"]) if l["type"] == "udhaar" else -float(l["amount"])
            for l in ledger
        ),
        2,
    )

    # ── low stock ────────────────────────────────────────────────────────────
    low = (
        sb.table("products")
        .select("id,name,stock")
        .eq("shop_id", shop_id)
        .lte("stock", _LOW_STOCK_THRESHOLD)
        .order("stock")
        .execute()
        .data
    )

    return {
        "date": today,
        "totals": {
            "sale": total_sale,
            "profit": profit,
            "udhaar_today": udhaar_today,
            "kharcha": total_kharcha,
            "outstanding_udhaar": outstanding,
        },
        "low_stock": [
            {"id": p["id"], "name": p["name"], "stock": p["stock"]} for p in low
        ],
        "recent": _recent_entries(shop_id=shop_id),
    }


def _recent_entries(*, shop_id: str, limit: int = 8) -> list[dict[str, Any]]:
    """Sales, udhaar payments and expenses, merged newest-first."""
    sb = get_supabase()
    out: list[dict[str, Any]] = []

    sales = (
        sb.table("sales")
        .select("id,total_amount,payment_type,created_at,customer_id")
        .eq("shop_id", shop_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    for s in sales:
        out.append(
            {
                "kind": "sale",
                "label": "Sale",
                "amount": float(s["total_amount"]),
                "tag": "Udhaar" if s["payment_type"] in ("udhaar", "split") else "Cash",
                "at": s["created_at"],
            }
        )

    payments = (
        sb.table("ledger_entries")
        .select("amount,type,created_at")
        .eq("shop_id", shop_id)
        .eq("type", "payment")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    for p in payments:
        out.append(
            {
                "kind": "payment",
                "label": "Udhaar wapsi",
                "amount": float(p["amount"]),
                "tag": "Wasooli",
                "at": p["created_at"],
            }
        )

    expenses = (
        sb.table("expenses")
        .select("amount,note,created_at")
        .eq("shop_id", shop_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    for e in expenses:
        out.append(
            {
                "kind": "expense",
                "label": e.get("note") or "Kharcha",
                "amount": float(e["amount"]),
                "tag": "Kharcha",
                "at": e["created_at"],
            }
        )

    out.sort(key=lambda r: r["at"], reverse=True)
    return out[:limit]
