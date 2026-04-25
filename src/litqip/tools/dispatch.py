from __future__ import annotations

import logging
from typing import Any

from litqip.constants import MAX_OUTPUT_LENGTH

logger = logging.getLogger("litqip.tools.dispatch")


def dispatch_tools(
    tool_calls: list[Any],
    handlers: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool, bool]:
    """Execute tool calls and collect results.

    Returns (results, used_todo, manual_compress).

    Never raises — individual tool errors are captured as string results.
    """
    results: list[dict[str, Any]] = []
    used_todo = False
    manual_compress = False

    for tc in tool_calls:
        handler = handlers.get(tc.name)
        try:
            if tc.name == "compress":
                manual_compress = True
                output = "Compressing..."
            elif handler:
                output = handler(**tc.input)
            else:
                output = f"Error: Unknown tool: {tc.name}"
        except Exception as e:
            output = f"Error: {e}"

        output_str = str(output)[:MAX_OUTPUT_LENGTH]
        logger.info("tool %s: %s", tc.name, output_str[:120])
        results.append({"type": "tool_result", "tool_use_id": tc.id, "content": output_str})

        if tc.name == "TodoWrite":
            used_todo = True

    return results, used_todo, manual_compress
