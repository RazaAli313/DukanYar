"""Khata data-layer tests — KHATA-1..4.

Hit the real Supabase project (no mocks). Each test runs against throwaway
shop(s) deleted afterwards; ON DELETE CASCADE removes customers + ledger rows.

Skips itself if SUPABASE_URL / SUPABASE_KEY are not configured.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.db import get_supabase
from app.services import khata as K

pytestmark = pytest.mark.skipif(
    not (settings.supabase_url and settings.supabase_key),
    reason="SUPABASE_URL / SUPABASE_KEY not set",
)

CNIC_A = "12345-1234567-1"
CNIC_B = "42101-7654321-9"


@pytest.fixture
def shop_id():
    sb = get_supabase()
    row = sb.table("shops").insert({"name": "TEST — khata pytest"}).execute().data[0]
    yield row["id"]
    sb.table("shops").delete().eq("id", row["id"]).execute()


@pytest.fixture
def other_shop_id():
    sb = get_supabase()
    row = sb.table("shops").insert({"name": "TEST — khata pytest (other)"}).execute().data[0]
    yield row["id"]
    sb.table("shops").delete().eq("id", row["id"]).execute()


# ── CNIC normalization (KHATA-1) ────────────────────────────────────────────

@pytest.mark.parametrize("raw", ["12345-1234567-1", "1234512345671", " 12345 1234567 1 "])
def test_normalize_cnic_accepts_13_digits(raw):
    assert K.normalize_cnic(raw) == "1234512345671"


@pytest.mark.parametrize("raw", ["123", "", None, "123456789012345"])
def test_normalize_cnic_rejects_wrong_length(raw):
    with pytest.raises(K.KhataError):
        K.normalize_cnic(raw)


# ── registration (KHATA-1) ─────────────────────────────────────────────────

def test_register_assigns_sequential_khata_number_per_shop(shop_id, other_shop_id):
    a = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    b = K.register_customer(shop_id=shop_id, name="Ahmed", cnic=CNIC_B)
    # a different shop restarts at 1
    c = K.register_customer(shop_id=other_shop_id, name="Bilal", cnic=CNIC_A)

    assert a["khata_number"] == 1
    assert b["khata_number"] == 2
    assert c["khata_number"] == 1
    assert a["cnic"] == "1234512345671"  # stored normalized


def test_register_requires_name(shop_id):
    with pytest.raises(K.KhataError):
        K.register_customer(shop_id=shop_id, name="  ", cnic=CNIC_A)


def test_duplicate_cnic_raises_with_existing_customer(shop_id):
    first = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    with pytest.raises(K.DuplicateCustomerError) as ei:
        K.register_customer(shop_id=shop_id, name="Ali Khan", cnic=CNIC_A)
    assert ei.value.customer["id"] == first["id"]


def test_same_cnic_allowed_in_different_shops(shop_id, other_shop_id):
    K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    other = K.register_customer(shop_id=other_shop_id, name="Ali", cnic=CNIC_A)
    assert other["khata_number"] == 1


# ── lookup (KHATA-4) ───────────────────────────────────────────────────────

def test_find_by_khata_number_and_cnic_fallback(shop_id):
    made = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    assert K.find_customer(shop_id=shop_id, khata_number=1)["id"] == made["id"]
    assert K.find_customer(shop_id=shop_id, cnic="12345-1234567-1")["id"] == made["id"]
    assert K.find_customer(shop_id=shop_id, khata_number=999) is None
    with pytest.raises(K.KhataError):
        K.find_customer(shop_id=shop_id)


def test_lookup_is_shop_scoped(shop_id, other_shop_id):
    K.register_customer(shop_id=other_shop_id, name="Ali", cnic=CNIC_A)
    assert K.find_customer(shop_id=shop_id, khata_number=1) is None


# ── ledger: udhaar, partial payment, undo (KHATA-2, KHATA-3) ────────────────

def test_udhaar_then_partial_payment_leaves_remainder(shop_id):
    cust = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    cid = cust["id"]

    assert K.customer_balance(shop_id=shop_id, customer_id=cid) == 0.0

    r1 = K.log_udhaar(shop_id=shop_id, customer_id=cid, amount=400)
    assert r1["balance"] == 400.0

    r2 = K.record_payment(shop_id=shop_id, customer_id=cid, amount=300)
    assert r2["balance"] == 100.0  # 400 owed, 300 paid -> 100 pending


def test_undo_udhaar_restores_prior_balance(shop_id):
    cust = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    cid = cust["id"]

    K.log_udhaar(shop_id=shop_id, customer_id=cid, amount=100)
    entry = K.log_udhaar(shop_id=shop_id, customer_id=cid, amount=450)["entry"]
    assert K.customer_balance(shop_id=shop_id, customer_id=cid) == 550.0

    assert K.reverse_ledger_entry(shop_id=shop_id, entry_id=entry["id"]) is True
    assert K.customer_balance(shop_id=shop_id, customer_id=cid) == 100.0


@pytest.mark.parametrize("bad", [0, -50, "x"])
def test_ledger_rejects_non_positive_amount(shop_id, bad):
    cust = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    with pytest.raises(K.KhataError):
        K.log_udhaar(shop_id=shop_id, customer_id=cust["id"], amount=bad)


def test_cannot_log_against_another_shops_customer(shop_id, other_shop_id):
    theirs = K.register_customer(shop_id=other_shop_id, name="Ali", cnic=CNIC_A)
    with pytest.raises(K.KhataError):
        K.log_udhaar(shop_id=shop_id, customer_id=theirs["id"], amount=100)
    # nothing was written under the wrong shop
    assert K.customer_balance(shop_id=other_shop_id, customer_id=theirs["id"]) == 0.0


def test_undo_is_shop_scoped(shop_id, other_shop_id):
    cust = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    entry = K.log_udhaar(shop_id=shop_id, customer_id=cust["id"], amount=200)["entry"]
    assert K.reverse_ledger_entry(shop_id=other_shop_id, entry_id=entry["id"]) is False
    assert K.customer_balance(shop_id=shop_id, customer_id=cust["id"]) == 200.0


# ── list_customers ─────────────────────────────────────────────────────────

def test_list_customers_with_balances_newest_first(shop_id):
    a = K.register_customer(shop_id=shop_id, name="Ali", cnic=CNIC_A)
    K.register_customer(shop_id=shop_id, name="Ahmed", cnic=CNIC_B)
    K.log_udhaar(shop_id=shop_id, customer_id=a["id"], amount=250)

    rows = K.list_customers(shop_id=shop_id)
    assert [r["khata_number"] for r in rows] == [2, 1]
    assert {r["name"]: r["balance"] for r in rows} == {"Ahmed": 0.0, "Ali": 250.0}
