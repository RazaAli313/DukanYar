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
