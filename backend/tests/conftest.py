"""Shared fixtures — real Supabase project, no mocks (see test_khata.py).

Every fixture creates throwaway rows and removes them afterwards. Shops cascade
to conversations/messages/customers/ledger, but **auth users do not cascade from
anything**, so they are deleted explicitly.
"""

from __future__ import annotations

import uuid

import pytest

from app.config import settings
from app.db import get_supabase

HAS_SUPABASE = bool(settings.supabase_url and settings.supabase_key)

requires_supabase = pytest.mark.skipif(
    not HAS_SUPABASE, reason="SUPABASE_URL / SUPABASE_KEY not set"
)

TEST_PASSWORD = "dukanyar-test-passw0rd!"


@pytest.fixture
def shop_id():
    """A throwaway shop. Cascades to conversations/messages on delete."""
    sb = get_supabase()
    row = sb.table("shops").insert({"name": "TEST — text3 pytest"}).execute().data[0]
    try:
        yield row["id"]
    finally:
        sb.table("shops").delete().eq("id", row["id"]).execute()


@pytest.fixture
def other_shop_id():
    """A second shop, for cross-tenant isolation checks."""
    sb = get_supabase()
    row = (
        sb.table("shops")
        .insert({"name": "TEST — text3 pytest (other)"})
        .execute()
        .data[0]
    )
    try:
        yield row["id"]
    finally:
        sb.table("shops").delete().eq("id", row["id"]).execute()


@pytest.fixture
def auth_user(shop_id):
    """A real auth user with a profile in *shop_id*.

    Yields ``{"id", "email", "password", "shop_id"}``. The profile row goes away
    with the shop (ON DELETE CASCADE on profiles.id would need the auth user, so
    we delete the user last).
    """
    sb = get_supabase()
    email = f"text3-{uuid.uuid4().hex[:12]}@dukanyar.test"

    created = sb.auth.admin.create_user(
        {"email": email, "password": TEST_PASSWORD, "email_confirm": True}
    )
    user_id = created.user.id

    try:
        sb.table("profiles").insert(
            {
                "id": user_id,
                "shop_id": shop_id,
                "email": email,
                "role_name": "shopkeeper",
            }
        ).execute()
        yield {
            "id": user_id,
            "email": email,
            "password": TEST_PASSWORD,
            "shop_id": shop_id,
        }
    finally:
        # Deleting the auth user cascades to public.profiles (FK on profiles.id).
        sb.auth.admin.delete_user(user_id)


@pytest.fixture
def access_token(auth_user):
    """A real, freshly minted access token for *auth_user*."""
    sb = get_supabase()
    session = sb.auth.sign_in_with_password(
        {"email": auth_user["email"], "password": auth_user["password"]}
    )
    token = session.session.access_token
    try:
        yield token
    finally:
        # Leave no session behind on the shared service client.
        try:
            sb.auth.sign_out()
        except Exception:  # pragma: no cover — best effort
            pass
