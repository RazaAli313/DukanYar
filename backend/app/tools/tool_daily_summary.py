"""daily_summary tool — RPT-2, TOOL-1.

Returns today's sales, profit, and expense totals for use in the "ask" mode
so the shopkeeper can say "aaj ka hisaab batao" and get a spoken summary.
Read-only — no writes.
Available in "ask" mode (also available with no mode restriction).
"""

from __future__ import annotations

from typing import Any

from app.services import dashboard as dash
from app.tools.registry import ToolDefinition, get_registry

_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "required": [],
}


async def _handler(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    shop_id: str = ctx["shop_id"]
    snap = dash.today_snapshot(shop_id=shop_id)
    t = snap["totals"]

    def _pk(n: float) -> str:
        return f"₨ {int(round(n)):,}"

    return {
        "ok": True,
        "date": snap["date"],
        "totals": t,
        "low_stock_count": len(snap.get("low_stock", [])),
        "reply": (
            f"Aaj ki sale {_pk(t['sale'])}, "
            f"profit {_pk(t['profit'])}, "
            f"kharcha {_pk(t['kharcha'])}. "
            f"Baqaya udhaar {_pk(t['outstanding_udhaar'])}."
        ),
    }


get_registry().register(ToolDefinition(
    name="daily_summary",
    description=(
        "Return today's sales, profit, expenses, and outstanding udhaar totals. "
        "Use when the shopkeeper asks 'aaj ka hisaab', 'aaj kitni sale hui', "
        "'profit kitna hua', etc."
    ),
    parameters=_PARAMETERS,
    risk_tier="commit_undo",  # read-only; no undo needed — tier is just for classification
    modes=["ask"],
    handler=_handler,
))
