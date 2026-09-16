"""Tool registry — TOOL-1.

Each tool lives in its own module under app/tools/ and calls
``registry.register(definition)`` at import time. The registry is
populated once (on the first call to ``get_registry()``) by importing
every sibling module, so adding a new tool is a matter of dropping a
new file here with no central-list edits.

Duplicate names raise ``ToolRegistryError`` at startup, giving a clear
signal rather than a silent shadow.
"""

from app.tools.registry import ToolRegistry, get_registry

__all__ = ["ToolRegistry", "get_registry"]
