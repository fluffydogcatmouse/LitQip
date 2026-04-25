from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from litqip.agent.subagent import run_subagent
from litqip.compression import auto_compact, estimate_tokens, microcompact
from litqip.constants import TODO_NAG_ROUNDS, TOKEN_THRESHOLD
from litqip.llm import ChatResponse, LLMClient
from litqip.skills import skills
from litqip.tools import tools, dispatch_tools
from litqip.todo import todo

logger = logging.getLogger("litqip.agent.loop")

SYSTEM_PROMPT = """You are a coding agent. Use tools to solve tasks.
Prefer breaking work into clear steps. Use TodoWrite for short checklists.
Use the 'task' tool to delegate sub-agents for isolated exploration or work.
Use load_skill to load specialized knowledge.
Available skills: {skills_descriptions}

Project context files may be provided inline or listed as available on demand.
Use read_file to load additional files when relevant to the user's request."""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT.format(skills_descriptions=skills.descriptions())


def load_project_context() -> str:
    """Load AGENTS.md or CLAUDE.md from CWD as project context."""
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = Path.cwd() / name
        if path.exists():
            logger.info("loaded %s", name)
            return path.read_text().strip()
    return ""


def _register_agent_tools() -> None:
    """Register agent-level tool definitions into the global ToolRegistry.

    Idempotent — subsequent calls are no-ops for already-registered tools.
    """
    tools.extend("TodoWrite", {
        "name": "TodoWrite",
        "description": "Update task tracking list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                            "activeForm": {"type": "string"},
                        },
                        "required": ["content", "status", "activeForm"],
                    },
                },
            },
            "required": ["items"],
        },
    }, todo.update)
    tools.extend("load_skill", {
        "name": "load_skill",
        "description": "Load specialized knowledge by name.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    }, skills.load)
    tools.extend("compress", {
        "name": "compress",
        "description": "Manually compress conversation context.",
        "input_schema": {"type": "object", "properties": {}},
    }, lambda: "Compressing...")
    tools.extend("task", {
        "name": "task",
        "description": "Spawn a subagent for isolated exploration or work.",
        "input_schema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
        },
    }, lambda prompt: "Subagent task registered.")


# Register agent tools at import time.
_register_agent_tools()


class AgentLoop:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client
        self._rounds_without_todo = 0
        self._handlers: dict[str, Any] = dict(tools.handlers)
        # Replace the stub task handler with a per-instance version
        self._handlers["task"] = self._make_task_handler()

    def _make_task_handler(self):
        def _run_task(prompt: str) -> str:
            return run_subagent(
                prompt=prompt,
                llm_client=self._llm,
                tools=tools.tools,
                tool_handlers=self._handlers,
            )
        return _run_task

    def run(self, messages: list[dict[str, Any]]) -> ChatResponse:
        """
        Run one turn of the agent loop.
        messages: conversation history as list of dicts (modified in place).
        The first message should be the system prompt.
        Returns the final ChatResponse.
        """
        while True:
            # Compression pipeline
            microcompact(messages)
            if estimate_tokens(messages) > TOKEN_THRESHOLD:
                logger.info("auto-compact triggered (tokens > %d)", TOKEN_THRESHOLD)
                messages[:] = auto_compact(messages, self._llm)

            # LLM call
            response = self._llm.chat(messages=messages, tools=tools.tools)

            llm_is_done = response.stop_reason != "tool_use" or not response.tool_calls
            if llm_is_done:
                messages.append({"role": "assistant", "content": response.text})
                return response

            # Append assistant message with tool_calls (OpenAI format)
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response.text or None}
            if response.reasoning_content:
                assistant_msg["reasoning_content"] = response.reasoning_content
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.input)},
                }
                for tc in response.tool_calls
            ]
            messages.append(assistant_msg)

            # Tool dispatch
            results, used_todo, manual_compress = dispatch_tools(
                response.tool_calls, self._handlers
            )

            # Todo nag
            self._rounds_without_todo = 0 if used_todo else self._rounds_without_todo + 1
            if todo.has_open_items() and self._rounds_without_todo >= TODO_NAG_ROUNDS:
                results.append({"type": "tool_result", "tool_use_id": "nag", "content": "<reminder>Update your todos.</reminder>"})

            # Append tool results in OpenAI format
            for r in results:
                messages.append({"role": "tool", "tool_call_id": r["tool_use_id"], "content": r["content"]})

            # Manual compress: compact and return immediately
            if manual_compress:
                logger.info("manual compact triggered")
                messages[:] = auto_compact(messages, self._llm)
                return response
