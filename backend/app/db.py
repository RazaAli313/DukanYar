"""Supabase client for the backend.

The backend uses the **service_role** key, so it bypasses RLS — every query
MUST filter by the caller's shop_id explicitly (see app.auth.get_current_user).
"""

from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache
def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_KEY not set in backend/.env "
            "(use the project URL + service_role key)."
        )
    return create_client(settings.supabase_url, settings.supabase_key)
