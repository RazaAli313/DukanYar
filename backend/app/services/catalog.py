"""Catalog resolution — SALE-2 (minimal).

Match a spoken/typed item name to a shop's product, via the product name or a
registered alias. Roman-Urdu and Urdu-script aliases both work. Read-only.

Backend uses the service_role key (RLS bypassed) — every query is scoped by
``shop_id`` explicitly.
"""

from __future__ import annotations

import re
from typing import Any

from app.db import get_supabase

_PROD_COLS = "id,name,sale_price,cost_price,stock"


def _norm(term: str) -> str:
    return re.sub(r"\s+", " ", (term or "").strip().lower())


def resolve_product(*, shop_id: str, term: str) -> dict[str, Any] | None:
    """Best single match for *term* in this shop, or None.

    Order of preference: exact name, exact alias, name contains, alias contains.
    """
    t = _norm(term)
    if not t:
        return None
    sb = get_supabase()

    products = (
        sb.table("products")
        .select(f"{_PROD_COLS},product_aliases(alias)")
        .eq("shop_id", shop_id)
        .execute()
        .data
    )

    exact_name = exact_alias = part_name = part_alias = None
    for p in products:
        name = _norm(p["name"])
        aliases = [_norm(a["alias"]) for a in (p.get("product_aliases") or []) if a.get("alias")]
        row = {k: p[k] for k in _PROD_COLS.split(",")}
        if name == t:
            exact_name = row
        elif t in aliases:
            exact_alias = exact_alias or row
        elif t in name or name in t:
            part_name = part_name or row
        elif any(t in a or a in t for a in aliases):
            part_alias = part_alias or row

    return exact_name or exact_alias or part_name or part_alias


def find_candidates(*, shop_id: str, term: str, limit: int = 5) -> list[dict[str, Any]]:
    """Return up to *limit* products that partially match *term*.

    Used by record_sale for SALE-2 disambiguation: when resolve_product returns
    None, we surface near-matches so the model can ask the shopkeeper to clarify.
    """
    t = _norm(term)
    if not t:
        return []

    sb = get_supabase()
    products = (
        sb.table("products")
        .select(f"{_PROD_COLS},product_aliases(alias)")
        .eq("shop_id", shop_id)
        .execute()
        .data
    )

    matches: list[dict[str, Any]] = []
    for p in products:
        name = _norm(p["name"])
        aliases = [_norm(a["alias"]) for a in (p.get("product_aliases") or []) if a.get("alias")]
        row = {k: p[k] for k in _PROD_COLS.split(",")}
        # Include any row where name or alias is a partial match
        if (
            t in name
            or name in t
            or any(t in a or a in t for a in aliases)
        ):
            matches.append(row)
        if len(matches) >= limit:
            break

    return matches


def update_product(*, shop_id: str, product_id: str, **fields: Any) -> dict[str, Any] | None:
    """Patch a product row and return the updated record.

    Only provided *fields* are updated (e.g. stock, sale_price, cost_price).
    Returns None if the product was not found in this shop.
    """
    sb = get_supabase()
    result = (
        sb.table("products")
        .update(fields)
        .eq("id", product_id)
        .eq("shop_id", shop_id)
        .execute()
        .data
    )
    if not result:
        return None
    return {k: result[0][k] for k in _PROD_COLS.split(",") if k in result[0]}


def add_product(
    *,
    shop_id: str,
    name: str,
    sale_price: float,
    cost_price: float = 0.0,
    stock: int = 0,
    unit: str | None = None,
) -> dict[str, Any]:
    """Insert a new product and return the created row."""
    sb = get_supabase()
    row: dict[str, Any] = {
        "shop_id": shop_id,
        "name": name.strip(),
        "sale_price": round(sale_price, 2),
        "cost_price": round(cost_price, 2),
        "stock": stock,
    }
    if unit:
        row["unit"] = unit.strip()
    result = sb.table("products").insert(row).execute().data
    if not result:
        raise ValueError("Product insert returned no row.")
    return {k: result[0][k] for k in _PROD_COLS.split(",") if k in result[0]}


def list_products(*, shop_id: str) -> list[dict[str, Any]]:
    return (
        get_supabase()
        .table("products")
        .select(_PROD_COLS)
        .eq("shop_id", shop_id)
        .order("name")
        .execute()
        .data
    )
