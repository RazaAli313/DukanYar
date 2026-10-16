"""Ledger read model — the Khata screen's full transaction list (RPT-1 style).

Merges sales, udhaar/payment ledger entries and expenses into one shop-scoped,
newest-first list. Read-only. service_role + explicit shop_id scoping.
"""

from __future__ import annotations

from typing import Any, Literal

from app.db import get_supabase

Filter = Literal["all", "sale", "udhaar", "kharcha"]


def transactions(*, shop_id: str, filter: Filter = "all", limit: int = 100) -> list[dict[str, Any]]:
    sb = get_supabase()
    rows: list[dict[str, Any]] = []

    if filter in ("all", "sale"):
        for s in (
            sb.table("sales")
            .select("id,total_amount,payment_type,created_at")
            .eq("shop_id", shop_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        ):
            udhaar = s["payment_type"] in ("udhaar", "split")
            rows.append(
                {
                    "kind": "sale",
                    "detail": "Sale",
                    "qism": "Udhaar" if udhaar else "Cash",
                    "amount": float(s["total_amount"]),
                    "direction": "in",
                    "at": s["created_at"],
                }
            )

    if filter in ("all", "udhaar"):
        for le in (
            sb.table("ledger_entries")
            .select("amount,type,created_at,customers(name,khata_number)")
            .eq("shop_id", shop_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        ):
            cust = le.get("customers") or {}
            who = cust.get("name") or (
                f"Khata #{cust['khata_number']}" if cust.get("khata_number") else "Customer"
            )
            is_payment = le["type"] == "payment"
            rows.append(
                {
                    "kind": "payment" if is_payment else "udhaar",
                    "detail": f"{'Wapsi' if is_payment else 'Udhaar'} — {who}",
                    "qism": "Wasooli" if is_payment else "Udhaar",
                    "amount": float(le["amount"]),
                    "direction": "in" if is_payment else "out",
                    "at": le["created_at"],
                }
            )

    if filter in ("all", "kharcha"):
        for e in (
            sb.table("expenses")
            .select("amount,note,created_at,expense_categories(name)")
            .eq("shop_id", shop_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        ):
            cat = (e.get("expense_categories") or {}).get("name")
            rows.append(
                {
                    "kind": "expense",
                    "detail": e.get("note") or cat or "Kharcha",
                    "qism": "Kharcha",
                    "amount": float(e["amount"]),
                    "direction": "out",
                    "at": e["created_at"],
                }
            )

    rows.sort(key=lambda r: r["at"], reverse=True)
    return rows[:limit]
