from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from litqip.constants import LLM_TIMEOUT
from litqip.llm.types import BaseAdapter, ChatResponse, ModelConfig, ToolCall

logger = logging.getLogger("litqip.llm")


class OpenAIAdapter(BaseAdapter):
    """Generic adapter for any OpenAI-compatible chat API."""

    def __init__(self, config: ModelConfig, extra_payload: dict[str, Any] | None = None) -> None:
        self.config = config
        self.extra_payload = extra_payload or {}

    def _build_payload(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            **self.extra_payload,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ]
        return payload

    def _send_request(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(follow_redirects=False) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "litqip/0.1.0",
                },
                json=payload,
                timeout=LLM_TIMEOUT,
            )
            logger.debug("response status=%s content_type=%s length=%d", response.status_code, response.headers.get("content-type"), len(response.content))
            try:
                response.raise_for_status()
                return response.json()  # type: ignore[return-value]
            except Exception:
                logger.error("API error: url=%s status=%s body=%s", url, response.status_code, response.text[:1000])
                raise

    def _parse_response(self, data: dict[str, Any]) -> ChatResponse:
        choice = data["choices"][0]
        raw_message = choice["message"]

        content_blocks: list[dict[str, Any]] = []
        if raw_message.get("content") or raw_message.get("reasoning_content"):
            content_blocks.append({"type": "text", "text": raw_message.get("content") or raw_message.get("reasoning_content") or ""})

        tool_calls: list[ToolCall] | None = None
        if "tool_calls" in raw_message:
            tool_calls = []
            for tc in raw_message["tool_calls"]:
                content_blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"]})
                tool_calls.append(
                    ToolCall(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        input=json.loads(tc["function"]["arguments"]),
                    )
                )

        text = raw_message.get("content") or raw_message.get("reasoning_content") or ""
        finish_reason = choice.get("finish_reason") or "stop"
        stop_reason = "tool_use" if finish_reason == "tool_calls" else finish_reason

        return ChatResponse(
            content=content_blocks,
            text=text,
            stop_reason=stop_reason,
            tool_calls=tool_calls,
            reasoning_content=raw_message.get("reasoning_content"),
        )

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> ChatResponse:
        payload = self._build_payload(messages, tools)
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        logger.debug("LLM request url=%s payload=%s", url, payload)
        data = self._send_request(url, payload)
        logger.debug("LLM response: %s", data)
        return self._parse_response(data)


# Backward-compatible alias
OpenRouterAdapter = OpenAIAdapter


class DeepSeekAdapter(OpenAIAdapter):
    """Adapter for DeepSeek's official API with thinking mode support."""

    def __init__(self, config: ModelConfig) -> None:
        thinking = os.environ.get("DEEPSEEK_THINKING", "").lower() in ("true", "1", "yes")
        extra: dict[str, Any] = {}
        if thinking:
            extra["thinking"] = {"type": "enabled"}
        super().__init__(config, extra_payload=extra)
