from __future__ import annotations

import logging
from typing import Any, Callable

from litqip.tools import bash, file

logger = logging.getLogger("litqip.tools.registry")


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., str]] = {}
        self._definitions: list[dict[str, Any]] = []
        self._register_all()

    def _register_all(self) -> None:
        self._handlers = {
            "bash": bash.run_bash,
            "read_file": file.read,
            "write_file": file.write,
            "edit_file": file.edit,
        }
        self._definitions = [
            {
                "name": "bash",
                "description": "Run a shell command.",
                "input_schema": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
            {
                "name": "read_file",
                "description": "Read file contents.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}},
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write content to a file.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
            },
            {
                "name": "edit_file",
                "description": "Replace exact text in a file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"},
                    },
                    "required": ["path", "old_text", "new_text"],
                },
            },
        ]

    def dispatch(self, name: str, kwargs: dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return f"Error: Unknown tool: {name}"
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("tool %s raised: %s", name, e)
            return f"Error: {e}"

    def extend(self, name: str, definition: dict[str, Any], handler: Callable[..., str]) -> None:
        """Register additional tools beyond the base set. No-op if already registered."""
        if name in self._handlers:
            return
        self._handlers[name] = handler
        self._definitions.append(definition)

    @property
    def tools(self) -> list[dict[str, Any]]:
        return self._definitions

    @property
    def handlers(self) -> dict[str, Callable[..., str]]:
        return self._handlers


tools = ToolRegistry()
