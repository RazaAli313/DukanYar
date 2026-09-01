"""Database access — STUB.

Sheheryar owns the real Supabase client + `conversations` / `messages` tables
and their migrations. This placeholder exists only so feature code has something
to import. Replace `get_supabase()` with the real client; keep the name.
"""

from app.config import settings


def get_supabase():
    raise NotImplementedError(
        "Supabase client not wired yet — Sheheryar's scaffold/auth work. "
        f"(supabase_url set: {bool(settings.supabase_url)})"
    )
