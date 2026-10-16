"""Shared primitives for tool-owned action cards (TOOL-4)."""

from __future__ import annotations

from typing import Any


def money(value: float) -> str:
    return f"₨ {int(round(value)):,}"


def card_base(
    *,
    tool_name: str,
    tool_call_id: str,
    status: str,
    result: dict[str, Any],
    undoable: bool,
) -> dict[str, Any]:
    return {
        "status": status,
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "undoable": undoable,
        "note": result.get("reply") if status == "failed" else None,
    }
