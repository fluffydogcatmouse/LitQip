from __future__ import annotations

import logging
import os
from typing import Any

from litqip.llm.adapters import DeepSeekAdapter, OpenAIAdapter
from litqip.llm.types import BaseAdapter, ChatResponse, ModelConfig

logger = logging.getLogger("litqip.llm")


def _detect_provider() -> str:
    return os.environ.get("PROVIDER", "openrouter").lower()


class LLMClient:
    def __init__(self, adapter: BaseAdapter) -> None:
        self._adapter = adapter

    @classmethod
    def from_env(cls) -> LLMClient:
        provider = _detect_provider()

        if provider == "deepseek":
            config = ModelConfig(
                api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com",
                model_name=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            )
            adapter: BaseAdapter = DeepSeekAdapter(config)
        else:
            adapter = OpenAIAdapter(ModelConfig.from_openrouter())

        logger.info("using provider=%s model=%s", provider, adapter.config.model_name)  # type: ignore[union-attr]
        return cls(adapter)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResponse:
        logger.info("LLM chat with %d messages, %d tools", len(messages), len(tools) if tools else 0)
        return self._adapter.chat(messages, tools)
