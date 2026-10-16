from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.services import llm


class _Completions:
    def __init__(self, verdict: str):
        self.verdict = verdict
        self.request: dict | None = None

    async def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.verdict))]
        )


@pytest.mark.parametrize(
    ("verdict", "allowed"),
    [("ALLOW", True), ("BLOCK", False), ("maybe", False), ("", False)],
)
def test_scope_classifier_fails_closed(monkeypatch, verdict, allowed):
    completions = _Completions(verdict)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr(llm, "_get_client", lambda: client)

    result = asyncio.run(
        llm.is_shop_request(
            [{"role": "user", "content": "write a python function"}]
        )
    )

    assert result is allowed
    assert completions.request["temperature"] == 0
    assert "programming" in completions.request["messages"][0]["content"]
