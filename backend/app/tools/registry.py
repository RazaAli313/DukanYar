"""Runtime tool registry — TOOL-1.

Tools self-register by calling ``registry.register(definition)`` at module
load time. ``get_registry()`` bootstraps the registry on first call by
importing every sibling module (files named ``tool_*.py`` under this
package), so the orchestration loop never needs to name individual tools.

Risk tiers (TOOL-3):
  - "read_only"         — reads shop data without mutating it.
  - "commit_undo"       — writes immediately; a quick undo is shown.
  - "approval_required" — shows the parsed action and waits for explicit
                          shopkeeper approval before any write.

Each ToolDefinition is a plain dataclass so the orchestration loop can
serialise the ``parameters`` schema directly into the model call.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Literal

logger = logging.getLogger(__name__)

RiskTier = Literal["read_only", "commit_undo", "approval_required"]
ToolHandler = Callable[..., Coroutine[Any, Any, dict[str, Any]]]
ToolPresenter = Callable[..., dict[str, Any] | None]
ToolUndo = Callable[..., bool]


@dataclass
class ToolDefinition:
    """Everything the orchestration loop needs to know about a tool."""

    name: str
    description: str
    # JSON Schema object (will be forwarded to the model as-is).
    parameters: dict[str, Any]
    risk_tier: RiskTier
    # Async callable: (parsed_params, execution_context) -> result_dict
    handler: ToolHandler
    # Optional UI and reversal behavior live beside the tool, so adding a tool
    # never requires a central router switch statement.
    presenter: ToolPresenter | None = None
    undo: ToolUndo | None = None


class ToolRegistryError(Exception):
    """Raised when the registry is misconfigured (e.g. duplicate name)."""


class ToolRegistry:
    """Singleton registry populated at startup by importing sibling modules."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ``ToolRegistryError`` on duplicate names."""
        if definition.name in self._tools:
            raise ToolRegistryError(
                f"Duplicate tool name '{definition.name}'. Each tool must have "
                "a unique name. Check your tool modules for conflicts."
            )
        if definition.risk_tier == "commit_undo" and (
            definition.presenter is None or definition.undo is None
        ):
            raise ToolRegistryError(
                f"Commit-with-undo tool '{definition.name}' must declare both "
                "presenter and undo behavior."
            )
        if definition.risk_tier == "approval_required" and definition.presenter is None:
            raise ToolRegistryError(
                f"Approval-required tool '{definition.name}' must declare a presenter."
            )
        self._tools[definition.name] = definition
        logger.info("Tool registered: %s (tier=%s)", definition.name, definition.risk_tier)

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def all(self) -> list[ToolDefinition]:
        """Return every tool; UI modes never restrict model choice."""
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        """OpenAI-style tool schemas for use in a model call."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.all()
        ]

    def names(self) -> list[str]:
        return list(self._tools.keys())


# ── singleton ─────────────────────────────────────────────────────────────────

_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Return the populated singleton, bootstrapping it on first call."""
    global _registry
    if _registry is not None:
        return _registry

    _registry = ToolRegistry()
    _bootstrap(_registry)
    return _registry


def _bootstrap(registry: ToolRegistry) -> None:
    """Import every ``tool_*.py`` sibling module so they self-register."""
    import app.tools as _pkg

    package_path = _pkg.__path__
    package_name = _pkg.__name__

    loaded: list[str] = []
    for _finder, module_name, _is_pkg in pkgutil.iter_modules(package_path):
        if not module_name.startswith("tool_"):
            continue
        full_name = f"{package_name}.{module_name}"
        try:
            importlib.import_module(full_name)
            loaded.append(full_name)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load tool module %s: %s", full_name, exc)
            raise

    logger.info(
        "Tool registry bootstrapped: %d tool(s) from %d module(s) — %s",
        len(registry.names()),
        len(loaded),
        registry.names(),
    )
