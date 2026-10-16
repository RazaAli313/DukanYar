"""Auth dependency tests — real Supabase tokens, no mocks.

Covers the TEXT-3 prerequisite: a Supabase access token resolves to the right
shop via public.profiles.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth import CurrentUser, get_current_user
from tests.conftest import requires_supabase

pytestmark = requires_supabase


# ── header parsing (no network) ──────────────────────────────────────────────

@pytest.mark.parametrize(
    "header",
    [None, "", "token-without-scheme", "Basic abc123", "Bearer", "Bearer   "],
)
def test_rejects_malformed_authorization_header(header):
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization=header)
    assert exc.value.status_code == 401


def test_rejects_garbage_token():
    with pytest.raises(HTTPException) as exc:
        get_current_user(authorization="Bearer not-a-real-jwt")
    assert exc.value.status_code == 401


# ── happy path ───────────────────────────────────────────────────────────────

def test_resolves_user_and_shop_from_real_token(access_token, auth_user):
    user = get_current_user(authorization=f"Bearer {access_token}")

    assert isinstance(user, CurrentUser)
    assert user.user_id == auth_user["id"]
    assert user.shop_id == auth_user["shop_id"]
    assert user.role == "shopkeeper"


def test_scheme_is_case_insensitive(access_token, auth_user):
    user = get_current_user(authorization=f"bearer {access_token}")
    assert user.shop_id == auth_user["shop_id"]


# ── authenticated but not onboarded ──────────────────────────────────────────

def test_403_when_user_has_no_profile(shop_id):
    """A user whose profile row is missing entirely cannot be scoped."""
    import uuid

    from app.db import get_supabase

    sb = get_supabase()
    email = f"text3-noprofile-{uuid.uuid4().hex[:10]}@dukanyar.test"
    created = sb.auth.admin.create_user(
        {"email": email, "password": "dukanyar-test-passw0rd!", "email_confirm": True}
    )
    try:
        # The handle_new_user trigger auto-creates a profile — delete it so this
        # user genuinely has none.
        sb.table("profiles").delete().eq("id", created.user.id).execute()
        session = sb.auth.sign_in_with_password(
            {"email": email, "password": "dukanyar-test-passw0rd!"}
        )
        with pytest.raises(HTTPException) as exc:
            get_current_user(authorization=f"Bearer {session.session.access_token}")
        assert exc.value.status_code == 403
    finally:
        try:
            sb.auth.sign_out()
        except Exception:
            pass
        try:
            sb.auth.admin.delete_user(created.user.id)
        except Exception:
            pass


def test_403_when_profile_has_no_shop():
    """Profile exists but shop_id is NULL — signup half-finished."""
    import uuid

    from app.db import get_supabase

    sb = get_supabase()
    email = f"text3-noshop-{uuid.uuid4().hex[:10]}@dukanyar.test"
    created = sb.auth.admin.create_user(
        {"email": email, "password": "dukanyar-test-passw0rd!", "email_confirm": True}
    )
    try:
        # Trigger already made the profile with shop_id NULL — no insert needed.
        session = sb.auth.sign_in_with_password(
            {"email": email, "password": "dukanyar-test-passw0rd!"}
        )
        with pytest.raises(HTTPException) as exc:
            get_current_user(authorization=f"Bearer {session.session.access_token}")
        assert exc.value.status_code == 403
    finally:
        try:
            sb.auth.sign_out()
        except Exception:
            pass
        try:
            sb.auth.admin.delete_user(created.user.id)
        except Exception:
            pass
