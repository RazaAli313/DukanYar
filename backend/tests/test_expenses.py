"""Expense data-layer tests — EXP-1 / EXP-2 / EXP-3.

These hit the real Supabase project (no mocks). Each test runs against a
throwaway shop that is deleted afterwards; ON DELETE CASCADE removes any
expenses created under it, so the real shops stay clean.

Skips itself if SUPABASE_URL / SUPABASE_KEY are not configured.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.db import get_supabase
from app.services import expenses as E

pytestmark = pytest.mark.skipif(
    not (settings.supabase_url and settings.supabase_key),
    reason="SUPABASE_URL / SUPABASE_KEY not set",
)


@pytest.fixture
def shop_id():
    sb = get_supabase()
    row = sb.table("shops").insert({"name": "TEST — expenses pytest"}).execute().data[0]
    yield row["id"]
    sb.table("shops").delete().eq("id", row["id"]).execute()


@pytest.fixture
def other_shop_id():
    sb = get_supabase()
    row = sb.table("shops").insert({"name": "TEST — expenses pytest (other)"}).execute().data[0]
    yield row["id"]
    sb.table("shops").delete().eq("id", row["id"]).execute()


# ── EXP-1 AC3 / EXP-2 AC3 (validation) ───────────────────────────────────────

@pytest.mark.parametrize("bad_amount", [0, -1, -1000, "abc", None])
def test_amount_must_be_positive(shop_id, bad_amount):
    with pytest.raises(E.ExpenseError):
        E.create_expense(shop_id=shop_id, amount=bad_amount)


# ── EXP-2 AC1 (category inference) ───────────────────────────────────────────

def test_no_category_defaults_to_uncategorized(shop_id):
    exp = E.create_expense(shop_id=shop_id, amount=500)
    assert exp["category"] == "Uncategorized"


@pytest.mark.parametrize(
    ("hint", "expected"),
    [
        ("bijli ka bill", "Utilities"),
        ("gas", "Utilities"),
        ("kiraya", "Rent"),
        ("tankhwah", "Salaries"),
        ("petrol delivery", "Transport"),
        ("marammat", "Maintenance"),
        ("utilities", "Utilities"),          # exact name
        ("something random", "Uncategorized"),
    ],
)
def test_category_is_inferred(shop_id, hint, expected):
    exp = E.create_expense(shop_id=shop_id, amount=100, category=hint)
    assert exp["category"] == expected


# ── EXP-3 (list) ────────────────────────────────────────────────────────────

def test_list_is_most_recent_first_and_shop_scoped(shop_id, other_shop_id):
    E.create_expense(shop_id=shop_id, amount=10, expense_date="2026-01-01")
    E.create_expense(shop_id=shop_id, amount=20, expense_date="2026-06-01")
    E.create_expense(shop_id=other_shop_id, amount=999, expense_date="2026-12-31")

    rows = E.list_expenses(shop_id=shop_id)

    assert [float(r["amount"]) for r in rows] == [20.0, 10.0]
    assert all(float(r["amount"]) != 999.0 for r in rows)  # never another shop's


# ── EXP-2 AC2 / EXP-3 (delete = undo, shop-scoped) ──────────────────────────

def test_delete_is_shop_scoped(shop_id, other_shop_id):
    exp = E.create_expense(shop_id=shop_id, amount=750)

    # a different shop cannot delete it
    assert E.delete_expense(shop_id=other_shop_id, expense_id=exp["id"]) is False
    assert E.get_expense(shop_id=shop_id, expense_id=exp["id"]) is not None

    # its own shop can
    assert E.delete_expense(shop_id=shop_id, expense_id=exp["id"]) is True
    assert E.get_expense(shop_id=shop_id, expense_id=exp["id"]) is None
