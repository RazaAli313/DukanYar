"""Auth dependency — resolves the caller from a Supabase access token (TEXT-3).

**Provisional.** The AUTH epic (Sheheryar) owns the final implementation; this is
the minimum needed to unblock TEXT-3 and deliberately keeps the ``CurrentUser``
shape the original stub advertised, so replacing the body here is a drop-in.

How it works: the frontend already holds a Supabase session, so it sends the
access token as ``Authorization: Bearer <jwt>``. We verify the token with
Supabase, then read ``shop_id`` / ``role_name`` from ``public.profiles``.

Note we do **not** rely on JWT claims for the shop. ``public.current_shop_id()``
reads ``app_metadata.shop_id``, which nothing currently populates — but that only
matters for RLS-bound clients. The backend uses the service_role key (see
``app.db``), bypasses RLS, and scopes every query by the ``shop_id`` resolved
here.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthError

from app.db import get_supabase


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    shop_id: str
    role: str  # "shopkeeper" | "admin"


def _bearer_token(authorization: str | None) -> str:
    """Pull the raw JWT out of an Authorization header, or 401."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Expected 'Authorization: Bearer <token>'")
    return token.strip()


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Verify the caller's Supabase token and resolve their shop.

    401 — no/!bearer/invalid token. 403 — authenticated but no profile row, or a
    profile with no shop assigned (signup did not complete).
    """
    token = _bearer_token(authorization)
    sb = get_supabase()

    try:
        response = sb.auth.get_user(token)
    except AuthError as exc:
        raise HTTPException(401, f"Invalid or expired token: {exc}") from exc
    if response is None or response.user is None:
        raise HTTPException(401, "Invalid or expired token")

    user_id = response.user.id

    try:
        rows = (
            sb.table("profiles")
            .select("shop_id,role_name")
            .eq("id", user_id)
            .limit(1)
            .execute()
            .data
        )
    except APIError as exc:  # pragma: no cover — network/permission failure
        raise HTTPException(503, f"Profile lookup failed: {exc.message}") from exc

    if not rows:
        raise HTTPException(403, "No profile for this user")
    if not rows[0].get("shop_id"):
        raise HTTPException(403, "No shop assigned to this user")

    return CurrentUser(
        user_id=user_id,
        shop_id=rows[0]["shop_id"],
        role=rows[0].get("role_name") or "shopkeeper",
    )


#: Annotated shorthand so routes read `user: CurrentUserDep`.
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
