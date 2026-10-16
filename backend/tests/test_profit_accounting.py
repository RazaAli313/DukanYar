from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.services import dashboard
from app.tools import tool_add_product, tool_adjust_product, tool_record_sale


class _Query:
    def __init__(self, table: str, rows: dict[str, list[dict]]):
        self.table = table
        self.rows = rows

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: self

    def execute(self):
        return SimpleNamespace(data=self.rows[self.table])


class _Supabase:
    def __init__(self, rows: dict[str, list[dict]]):
        self.rows = rows

    def table(self, name: str):
        return _Query(name, self.rows)


def test_profit_uses_recorded_sale_total_and_snapshotted_cost(monkeypatch):
    rows = {
        "sales": [
            {
                "id": "sale-1",
                "total_amount": 450,
                "payment_type": "cash",
                "created_at": "2099-01-01T00:00:00",
            }
        ],
        "sold_items": [
            {
                "quantity": 2,
                "unit_cost": 100,
                "products": {"cost_price": 999},
            }
        ],
        "expenses": [],
        "ledger_entries": [],
        "products": [],
    }
    monkeypatch.setattr(dashboard, "get_supabase", lambda: _Supabase(rows))
    monkeypatch.setattr(dashboard, "_recent_entries", lambda **_kwargs: [])

    result = dashboard.today_snapshot(shop_id="shop-1")

    assert result["totals"]["profit"] == 250


def test_add_product_requires_cost_and_shows_it_for_confirmation():
    missing = asyncio.run(
        tool_add_product._handler(
            {"name": "Coke", "sale_price": 120, "stock": 10},
            {"shop_id": "shop-1"},
        )
    )
    card = tool_add_product._present(
        params={
            "name": "Coke",
            "sale_price": 120,
            "cost_price": 80,
            "stock": 10,
        },
        result={},
        tool_call_id="call-1",
        status="proposed",
    )

    assert missing["needs_clarification"] is True
    assert "cost price" in missing["reply"]
    assert {line["label"]: line["value"] for line in card["lines"]}[
        "Purchase cost"
    ] == "₨ 80"


def test_sale_waits_until_existing_product_has_a_cost(monkeypatch):
    monkeypatch.setattr(
        tool_record_sale.catalog,
        "resolve_product",
        lambda **_kwargs: {
            "id": "product-1",
            "name": "Coke",
            "sale_price": 120,
            "cost_price": 0,
        },
    )

    result = asyncio.run(
        tool_record_sale._handler(
            {"items": [{"name": "Coke", "quantity": 1}], "stated_total": 120},
            {"shop_id": "shop-1", "user_id": "user-1"},
        )
    )

    assert result["needs_clarification"] is True
    assert "purchase cost missing" in result["reply"]


def test_adjust_product_can_set_a_missing_cost(monkeypatch):
    monkeypatch.setattr(
        tool_adjust_product.catalog,
        "resolve_product",
        lambda **_kwargs: {
            "id": "product-1",
            "name": "Coke",
            "stock": 10,
            "sale_price": 120,
            "cost_price": 0,
        },
    )
    monkeypatch.setattr(
        tool_adjust_product.catalog,
        "update_product",
        lambda **kwargs: {**kwargs, "name": "Coke"},
    )

    result = asyncio.run(
        tool_adjust_product._handler(
            {"product_name": "Coke", "cost_price": 80},
            {"shop_id": "shop-1"},
        )
    )

    assert result["ok"] is True
    assert result["changes"] == {"cost_price": 80.0}
