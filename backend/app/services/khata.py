"""Khata (udhaar / credit ledger) data layer — KHATA-1..4.

Routing-independent: nothing here knows whether it was reached from a block UI,
a tool call, or a plain endpoint.

Customers exist **only** for credit (udhaar). A cash sale records no customer and
never touches this module (see SALE-3). Identity = name + a per-shop running
``khata_number`` (assigned by a DB trigger), with CNIC as the fallback anchor.

Balance model — a customer's outstanding udhaar is
``SUM(amount WHERE type='udhaar') - SUM(amount WHERE type='payment')`` over
``ledger_entries``. Partial repayment needs no special case: owe 400, pay 300 →
balance 100. Overpayment is allowed and yields a negative balance (the shop owes
the customer).

The backend uses the Supabase **service_role** key, so RLS is bypassed — every
function takes ``shop_id`` and scopes its own query.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from postgrest.exceptions import APIError

from app.db import get_supabase

logger = logging.getLogger(__name__)

_CUSTOMER_COLS = "id,shop_id,khata_number,name,cnic,created_at"
_LEDGER_COLS = "id,shop_id,customer_id,sale_id,type,amount,created_at"
_UNIQUE_VIOLATION = "23505"


class KhataError(Exception):
    """Invalid khata input (bad CNIC, non-positive amount, missing selector)."""


class DuplicateCustomerError(KhataError):
    """A customer with this CNIC is already registered in this shop."""

    def __init__(self, customer: dict[str, Any]):
        self.customer = customer
        super().__init__(
            f"CNIC pehle se registered hai — khata #{customer['khata_number']} "
            f"({customer['name']})"
        )


# ── CNIC ─────────────────────────────────────────────────────────────────────

def normalize_cnic(cnic: str | None) -> str:
    """Strip formatting and validate a Pakistani CNIC to 13 digits."""
    digits = re.sub(r"\D", "", cnic or "")
    if len(digits) != 13:
        raise KhataError("CNIC 13 digits ka hona chahiye (jaise 12345-1234567-1)")
    return digits


# ── customers (KHATA-1, KHATA-4) ─────────────────────────────────────────────

def register_customer(
    *,
    shop_id: str,
    name: str,
    cnic: str,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Register a credit customer. The DB trigger assigns ``khata_number``.

    Raises ``KhataError`` for a blank name or bad CNIC, and
    ``DuplicateCustomerError`` (carrying the existing row) if the CNIC is already
    registered in this shop.
    """
    name = (name or "").strip()
    if not name:
        raise KhataError("customer ka naam chahiye")
    cnic_digits = normalize_cnic(cnic)

    row: dict[str, Any] = {"shop_id": shop_id, "name": name, "cnic": cnic_digits}
    if created_by:
        row["created_by"] = created_by

    # Retry once on a khata_number collision (the trigger's MAX()+1 is not
    # concurrency-safe; a CNIC collision is a real duplicate and is re-raised).
    for attempt in range(2):
        try:
            created = get_supabase().table("customers").insert(row).execute().data
            break
        except APIError as exc:
            if exc.code != _UNIQUE_VIOLATION:
                raise
            detail = f"{exc.message} {exc.details}".lower()
            if "cnic" in detail:
                existing = find_customer(shop_id=shop_id, cnic=cnic_digits)
                if existing:
                    raise DuplicateCustomerError(existing) from exc
                raise
            if attempt == 0:  # khata_number race — try again
                logger.warning("khata_number collision, retrying insert")
                continue
            raise
    else:  # pragma: no cover
        raise KhataError("khata number assign nahi ho saka, dubara koshish karein")

    if not created:
        raise KhataError("insert returned no row")
    logger.info(
        "customer registered: shop=%s khata=%s", shop_id, created[0]["khata_number"]
    )
    return _customer_row(created[0])


def _customer_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in ("id", "shop_id", "khata_number", "name", "cnic", "created_at") if k in row}


def find_customer(
    *,
    shop_id: str,
    khata_number: int | None = None,
    cnic: str | None = None,
) -> dict[str, Any] | None:
    """Look up a customer by khata number, else by CNIC. Returns None if absent."""
    q = get_supabase().table("customers").select(_CUSTOMER_COLS).eq("shop_id", shop_id)
    if khata_number is not None:
        q = q.eq("khata_number", int(khata_number))
    elif cnic:
        q = q.eq("cnic", normalize_cnic(cnic))
    else:
        raise KhataError("khata number ya CNIC chahiye")

    rows = q.limit(1).execute().data
    return _customer_row(rows[0]) if rows else None


def _assert_customer_in_shop(shop_id: str, customer_id: str) -> None:
    """Guard: the customer must belong to this shop before we write its ledger."""
    rows = (
        get_supabase()
        .table("customers")
        .select("id")
        .eq("id", customer_id)
        .eq("shop_id", shop_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise KhataError("is shop ka aisa koi customer nahi")


# ── balance (KHATA-4) ───────────────────────────────────────────────────────

def customer_balance(*, shop_id: str, customer_id: str) -> float:
    """Outstanding udhaar = Σ udhaar − Σ payment. Read-only."""
    rows = (
        get_supabase()
        .table("ledger_entries")
        .select("type,amount")
        .eq("shop_id", shop_id)
        .eq("customer_id", customer_id)
        .execute()
        .data
    )
    total = 0.0
    for r in rows:
        amt = float(r["amount"])
        total += amt if r["type"] == "udhaar" else -amt
    return round(total, 2)


def list_customers(*, shop_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """All credit customers for a shop with their current balance, newest first."""
    customers = (
        get_supabase()
        .table("customers")
        .select(_CUSTOMER_COLS)
        .eq("shop_id", shop_id)
        .order("khata_number", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    out = []
    for c in customers:
        row = _customer_row(c)
        row["balance"] = customer_balance(shop_id=shop_id, customer_id=c["id"])
        out.append(row)
    return out


# ── ledger (KHATA-2, KHATA-3) ───────────────────────────────────────────────

def _new_ledger_entry(
    *,
    shop_id: str,
    customer_id: str,
    entry_type: str,
    amount: float,
    sale_id: str | None,
    created_by: str | None,
) -> dict[str, Any]:
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise KhataError("amount must be a number") from None
    if amount <= 0:
        raise KhataError("amount must be greater than 0")

    _assert_customer_in_shop(shop_id, customer_id)

    row: dict[str, Any] = {
        "shop_id": shop_id,
        "customer_id": customer_id,
        "type": entry_type,
        "amount": round(amount, 2),
    }
    if sale_id:
        row["sale_id"] = sale_id
    if created_by:
        row["created_by"] = created_by

    inserted = get_supabase().table("ledger_entries").insert(row).execute().data
    if not inserted:
        raise KhataError("insert returned no row")
    entry = {k: inserted[0][k] for k in _LEDGER_COLS.split(",") if k in inserted[0]}
    return {
        "entry": entry,
        "balance": customer_balance(shop_id=shop_id, customer_id=customer_id),
    }


def log_udhaar(
    *,
    shop_id: str,
    customer_id: str,
    amount: float,
    sale_id: str | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Give goods on credit — raises the customer's balance. Commit-with-undo.

    Returns ``{"entry": <ledger row>, "balance": <new balance>}``.
    """
    return _new_ledger_entry(
        shop_id=shop_id, customer_id=customer_id, entry_type="udhaar",
        amount=amount, sale_id=sale_id, created_by=created_by,
    )


def record_payment(
    *,
    shop_id: str,
    customer_id: str,
    amount: float,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Record a repayment — lowers the balance. Money-in.

    This is the *post-approval* action; the approval gate itself (KHATA-3 /
    TOOL-3) lives in the orchestration layer, not here.
    """
    return _new_ledger_entry(
        shop_id=shop_id, customer_id=customer_id, entry_type="payment",
        amount=amount, sale_id=None, created_by=created_by,
    )


def reverse_ledger_entry(*, shop_id: str, entry_id: str) -> bool:
    """Undo a ledger entry (the KHATA-2 undo). Shop-scoped. True if removed."""
    deleted = (
        get_supabase()
        .table("ledger_entries")
        .delete()
        .eq("id", entry_id)
        .eq("shop_id", shop_id)
        .execute()
        .data
    )
    return bool(deleted)
