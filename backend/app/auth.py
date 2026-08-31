"""Auth dependency — STUB.

Sheheryar owns the real implementation (Supabase Auth + shops/users/roles).
Until then, every request resolves to a single fake shopkeeper so the TEXT/VOICE
feature can be built and run end to end. Swap the body of `get_current_user`,
keep the shape.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    shop_id: str
    role: str  # "shopkeeper" | "admin"


_FAKE_USER = CurrentUser(
    user_id="00000000-0000-0000-0000-000000000001",
    shop_id="00000000-0000-0000-0000-000000000001",
    role="shopkeeper",
)


def get_current_user() -> CurrentUser:
    return _FAKE_USER
