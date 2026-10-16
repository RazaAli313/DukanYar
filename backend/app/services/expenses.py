"""Expense data layer — EXP-1 / EXP-2 / EXP-3.

Routing-independent CRUD over ``public.expenses`` plus category resolution.
Nothing here knows *how* it is called (block UI, tool-call, plain endpoint) —
it just reads and writes rows.

The backend uses the Supabase **service_role** key, so RLS is bypassed. Every
function therefore takes ``shop_id`` and scopes its query explicitly — never
trust a caller-supplied row to already be shop-correct.
"""

from __future__ import annotations

import logging
from typing import Any

from app.db import get_supabase

logger = logging.getLogger(__name__)

# Columns returned to callers, with the category name embedded from the FK.
_SELECT = "id,amount,note,expense_date,created_at,category_id,expense_categories(name)"

_UNCATEGORIZED = "Uncategorized"

# Roman-Urdu / English keyword -> canonical category name. Matched as a
# substring of the hint, so "bijli ka bill" resolves to Utilities.
_CATEGORY_KEYWORDS: dict[str, str] = {
    # Utilities
    "bijli": "Utilities", "electricity": "Utilities", "gas": "Utilities",
    "paani": "Utilities", "water": "Utilities", "phone": "Utilities",
    "mobile": "Utilities", "internet": "Utilities", "wifi": "Utilities",
    "net ": "Utilities", "bill": "Utilities", "utility": "Utilities",
    # Rent
    "kiraya": "Rent", "kraya": "Rent", "rent": "Rent",
    # Supplies
    "shopper": "Supplies", "lifafa": "Supplies", "bag": "Supplies",
    "packing": "Supplies", "packaging": "Supplies", "dabba": "Supplies",
    "supplies": "Supplies", "saman": "Supplies", "stationery": "Supplies",
    # Salaries
    "tankhwah": "Salaries", "tankha": "Salaries", "salary": "Salaries",
    "naukar": "Salaries", "mazdoori": "Salaries", "worker": "Salaries",
    "staff": "Salaries", "mulazim": "Salaries",
    # Transport
    "transport": "Transport", "delivery": "Transport", "petrol": "Transport",
    "diesel": "Transport", "fuel": "Transport", "rickshaw": "Transport",
    "loading": "Transport", "truck": "Transport", "kraya gaari": "Transport",
    # Maintenance
    "marammat": "Maintenance", "repair": "Maintenance", "maintenance": "Maintenance",
    "painting": "Maintenance", "mistri": "Maintenance",
}


class ExpenseError(Exception):
    """Invalid expense input (e.g. a non-positive amount)."""


# ── categories ────────────────────────────────────────────────────────────────

def _category_index() -> dict[str, str]:
    """``name.lower()`` -> ``id`` for every row in ``expense_categories``."""
    rows = get_supabase().table("expense_categories").select("id,name").execute().data
    return {r["name"].lower(): r["id"] for r in rows}


def resolve_category(name: str | None) -> str | None:
    """Resolve a free-text category hint to an ``expense_categories.id``.

    Order: exact category-name match → keyword map (substring) → Uncategorized.
    Returns ``None`` only if the Uncategorized row is somehow missing.
    """
    index = _category_index()
    fallback = index.get(_UNCATEGORIZED.lower())

    if not name or not name.strip():
        return fallback

    key = name.strip().lower()

    if key in index:
        return index[key]

    for keyword, canonical in _CATEGORY_KEYWORDS.items():
        if keyword in key:
            hit = index.get(canonical.lower())
            if hit:
                return hit

    return fallback


# ── CRUD ──────────────────────────────────────────────────────────────────────

def _expand(row: dict[str, Any]) -> dict[str, Any]:
    """Flatten the embedded ``expense_categories`` object to a ``category`` string."""
    embedded = row.pop("expense_categories", None)
    name = embedded.get("name") if isinstance(embedded, dict) else None
    row["category"] = name or _UNCATEGORIZED
    return row


def create_expense(
    *,
    shop_id: str,
    amount: float,
    category: str | None = None,
    note: str | None = None,
    expense_date: str | None = None,  # ISO 'YYYY-MM-DD'; defaults to today in the DB
    created_by: str | None = None,
) -> dict[str, Any]:
    """Insert one expense and return it (with the resolved category name).

    Raises ``ExpenseError`` if ``amount`` is not a positive number.
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ExpenseError("amount must be a number") from None
    if amount <= 0:
        raise ExpenseError("amount must be greater than 0")

    row: dict[str, Any] = {
        "shop_id": shop_id,
        "amount": round(amount, 2),
        "category_id": resolve_category(category),
    }
    if note and note.strip():
        row["note"] = note.strip()
    if expense_date:
        row["expense_date"] = expense_date
    if created_by:
        row["created_by"] = created_by

    inserted = get_supabase().table("expenses").insert(row).execute().data
    if not inserted:
        raise ExpenseError("insert returned no row")

    created = get_expense(shop_id=shop_id, expense_id=inserted[0]["id"])
    if created is None:  # pragma: no cover — would mean the row vanished
        raise ExpenseError("could not read back the created expense")
    logger.info("expense created: shop=%s id=%s amount=%s", shop_id, created["id"], amount)
    return created


def get_expense(*, shop_id: str, expense_id: str) -> dict[str, Any] | None:
    rows = (
        get_supabase()
        .table("expenses")
        .select(_SELECT)
        .eq("id", expense_id)
        .eq("shop_id", shop_id)
        .limit(1)
        .execute()
        .data
    )
    return _expand(rows[0]) if rows else None


def list_expenses(*, shop_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Most recent first (by expense date, then insertion time)."""
    rows = (
        get_supabase()
        .table("expenses")
        .select(_SELECT)
        .eq("shop_id", shop_id)
        .order("expense_date", desc=True)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return [_expand(r) for r in rows]


def delete_expense(*, shop_id: str, expense_id: str) -> bool:
    """Delete one expense scoped to its shop. Returns True if a row was removed.

    This is the EXP-2 undo and the EXP-3 delete — same operation.
    """
    deleted = (
        get_supabase()
        .table("expenses")
        .delete()
        .eq("id", expense_id)
        .eq("shop_id", shop_id)
        .execute()
        .data
    )
    return bool(deleted)
