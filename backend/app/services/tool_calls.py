"""Persistent tool execution records for TOOL-2/TOOL-3."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db import get_supabase


def create(
    *, message_id: str, tool_name: str, params: dict[str, Any], status: str = "pending"
) -> dict[str, Any]:
    rows = (
        get_supabase()
        .table("tool_calls")
        .insert(
            {
                "message_id": message_id,
                "tool_name": tool_name,
                "status": status,
                "params": params,
            }
        )
        .execute()
        .data
    )
    if not rows:
        raise RuntimeError("tool call insert returned no row")
    return rows[0]


def resolve(
    *, tool_call_id: str, status: str, response: dict[str, Any]
) -> dict[str, Any]:
    rows = (
        get_supabase()
        .table("tool_calls")
        .update(
            {
                "status": status,
                "response": response,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", tool_call_id)
        .execute()
        .data
    )
    if not rows:
        raise RuntimeError("tool call update returned no row")
    return rows[0]


def get_for_shop(*, tool_call_id: str, shop_id: str) -> dict[str, Any] | None:
    """Return a tool call only when its source message belongs to *shop_id*."""
    calls = (
        get_supabase()
        .table("tool_calls")
        .select("id,message_id,tool_name,status,params,response,created_at,resolved_at")
        .eq("id", tool_call_id)
        .limit(1)
        .execute()
        .data
    )
    if not calls:
        return None

    messages = (
        get_supabase()
        .table("messages")
        .select("conversation_id")
        .eq("id", calls[0]["message_id"])
        .limit(1)
        .execute()
        .data
    )
    if not messages:
        return None

    conversations = (
        get_supabase()
        .table("conversations")
        .select("id")
        .eq("id", messages[0]["conversation_id"])
        .eq("shop_id", shop_id)
        .limit(1)
        .execute()
        .data
    )
    if not conversations:
        return None

    return {**calls[0], "conversation_id": messages[0]["conversation_id"]}


def set_status(*, tool_call_id: str, status: str) -> dict[str, Any]:
    rows = (
        get_supabase()
        .table("tool_calls")
        .update(
            {
                "status": status,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", tool_call_id)
        .execute()
        .data
    )
    if not rows:
        raise RuntimeError("tool call status update returned no row")
    return rows[0]


def claim_approval(*, tool_call_id: str) -> bool:
    """Atomically move one approval from pending to executing.

    The status predicate makes repeated or concurrent confirmation requests
    idempotent at the write boundary: only one caller can run the tool handler.
    """
    rows = (
        get_supabase()
        .table("tool_calls")
        .update({"status": "pending"})
        .eq("id", tool_call_id)
        .eq("status", "pending_approval")
        .execute()
        .data
    )
    return bool(rows)


def recent_for_conversation(
    *, conversation_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    """Recent actionable tool calls for restoring cards after a refresh."""
    message_rows = (
        get_supabase()
        .table("messages")
        .select("id")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
    )
    message_ids = [row["id"] for row in message_rows]
    if not message_ids:
        return []
    return (
        get_supabase()
        .table("tool_calls")
        .select("id,tool_name,status,params,response,created_at")
        .in_("message_id", message_ids)
        .in_("status", ["pending_approval", "committed"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
