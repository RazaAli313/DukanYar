"""Sale recording — SALE-3 / SALE-4.

A sale is cash unless a customer (khata) is attached, then it is udhaar. The
shopkeeper's stated total is authoritative — it is stored as-is regardless of
what the line-item prices sum to.

Stock: a DB trigger (``handle_sold_item_stock`` on ``sold_items`` INSERT)
already decrements ``products.stock`` and writes a ``stock_movements`` row.
This module MUST NOT touch stock itself — it only inserts ``sales`` and
``sold_items`` and then reads back the resulting stock to flag shortfalls.

Backend uses the service_role key; every query is scoped by ``shop_id``.
"""

from __future__ import annotations

from typing import Any, Literal

from app.db import get_supabase


class SaleError(Exception):
    """Invalid sale input."""


PaymentType = Literal["cash", "udhaar", "split"]


def record_sale(
    *,
    shop_id: str,
    items: list[dict[str, Any]],
    total_amount: float,
    payment_type: PaymentType = "cash",
    customer_id: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Record a sale. *items* = [{product_id, quantity, unit_price}].

    Returns ``{sale_id, total_amount, payment_type, stock_alerts: [...]}``.
    ``stock_alerts`` lists products left at or below zero after the sale.
    """
    try:
        total_amount = round(float(total_amount), 2)
    except (TypeError, ValueError):
        raise SaleError("total ek number hona chahiye") from None
    if total_amount < 0:
        raise SaleError("total manfi nahi ho sakta")
    if not items:
        raise SaleError("kam se kam ek item chahiye")

    for it in items:
        if int(it.get("quantity", 0)) <= 0:
            raise SaleError("har item ki quantity 0 se zyada honi chahiye")

    if payment_type in ("udhaar", "split") and not customer_id:
        raise SaleError("udhaar sale ke liye customer (khata) chahiye")

    sb = get_supabase()

    sale_row: dict[str, Any] = {
        "shop_id": shop_id,
        "payment_type": payment_type,
        "total_amount": total_amount,
    }
    if customer_id:
        sale_row["customer_id"] = customer_id
    if created_by:
        sale_row["created_by"] = created_by

    sale = sb.table("sales").insert(sale_row).execute().data
    if not sale:
        raise SaleError("sale insert returned no row")
    sale_id = sale[0]["id"]

    # The trigger fires per row and handles stock + movements.
    sb.table("sold_items").insert(
        [
            {
                "sale_id": sale_id,
                "product_id": it["product_id"],
                "quantity": int(it["quantity"]),
                "unit_price": round(float(it["unit_price"]), 2),
            }
            for it in items
        ]
    ).execute()

    # Read stock back to flag shortfalls (SALE-4).
    product_ids = list({it["product_id"] for it in items})
    after = (
        sb.table("products")
        .select("id,name,stock")
        .in_("id", product_ids)
        .execute()
        .data
    )
    stock_alerts = [
        {"product_id": p["id"], "name": p["name"], "stock": p["stock"]}
        for p in after
        if p["stock"] is not None and p["stock"] <= 0
    ]

    # Udhaar sale → ledger entry so the khata balance moves (SALE-3 / KHATA-2).
    if payment_type in ("udhaar", "split") and customer_id:
        sb.table("ledger_entries").insert(
            {
                "shop_id": shop_id,
                "customer_id": customer_id,
                "sale_id": sale_id,
                "type": "udhaar",
                "amount": total_amount,
                **({"created_by": created_by} if created_by else {}),
            }
        ).execute()

    return {
        "sale_id": sale_id,
        "total_amount": total_amount,
        "payment_type": payment_type,
        "stock_alerts": stock_alerts,
    }


def reverse_sale(*, shop_id: str, sale_id: str) -> bool:
    """Undo a sale. Deleting the sale cascades sold_items; a separate trigger
    is not present for restock-on-delete, so we restore stock explicitly."""
    sb = get_supabase()
    owned = (
        sb.table("sales").select("id").eq("id", sale_id).eq("shop_id", shop_id).execute().data
    )
    if not owned:
        return False

    lines = (
        sb.table("sold_items").select("product_id,quantity").eq("sale_id", sale_id).execute().data
    )
    for ln in lines:
        cur = (
            sb.table("products").select("stock").eq("id", ln["product_id"]).single().execute().data
        )
        sb.table("products").update({"stock": (cur["stock"] or 0) + ln["quantity"]}).eq(
            "id", ln["product_id"]
        ).execute()

    sb.table("sales").delete().eq("id", sale_id).eq("shop_id", shop_id).execute()
    return True
