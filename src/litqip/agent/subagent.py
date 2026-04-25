from __future__ import annotations

import json
import logging
from typing import Any

from litqip.constants import SUBAGENT_MAX_ROUNDS
from litqip.llm import ChatResponse, LLMClient
from litqip.tools import dispatch_tools

logger = logging.getLogger("litqip.agent.subagent")


def run_subagent(
    prompt: str,
    llm_client: LLMClient,
    tools: list[dict[str, Any]],
    tool_handlers: dict[str, Any],
) -> str:
    """Spawn a subagent to handle a focused task. Uses the same model as the main agent."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    resp: ChatResponse | None = None

    for _ in range(SUBAGENT_MAX_ROUNDS):
        resp = llm_client.chat(messages=messages, tools=tools)
        messages.append({"role": "assistant", "content": resp.text or None})

        if resp.stop_reason != "tool_use" or not resp.tool_calls:
            break

        # Append assistant tool_calls message (OpenAI format)
        tc_msg: dict[str, Any] = {"role": "assistant", "content": None}
        if resp.reasoning_content:
            tc_msg["reasoning_content"] = resp.reasoning_content
        tc_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.input)},
            }
            for tc in resp.tool_calls
        ]
        messages.append(tc_msg)

        results, _, _ = dispatch_tools(resp.tool_calls, tool_handlers)
        for r in results:
            messages.append({"role": "tool", "tool_call_id": r["tool_use_id"], "content": r["content"]})

    if resp:
        return resp.text or "(no summary)"
    return "(subagent failed)"
