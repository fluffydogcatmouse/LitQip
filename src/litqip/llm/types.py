from __future__ import annotations

import os
from typing import Any, Literal, Protocol, Union


class Message:
    role: Literal["system", "user", "assistant"]
    content: Union[str, list[dict[str, Any]]]

    def __init__(
        self,
        role: Literal["system", "user", "assistant"],
        content: Union[str, list[dict[str, Any]]],
    ) -> None:
        self.role = role
        self.content = content

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        return cls(role=data["role"], content=data["content"])


class ToolResult:
    tool_use_id: str
    content: str

    def __init__(self, tool_use_id: str, content: str) -> None:
        self.tool_use_id = tool_use_id
        self.content = content

    def to_dict(self) -> dict[str, str]:
        return {"type": "tool_result", "tool_use_id": self.tool_use_id, "content": self.content}


class ChatResponse:
    """
    content: raw block list from API (text blocks + tool_use blocks).
    text: extracted text content for display.
    stop_reason: 'stop' or 'tool_use'.
    tool_calls: list of ToolCall if any.
    reasoning_content: raw reasoning_content from DeepSeek thinking mode (must be passed back).
    """
    content: list[dict[str, Any]]  # raw blocks
    text: str                       # for display
    stop_reason: str
    tool_calls: list[ToolCall] | None
    reasoning_content: str | None

    def __init__(
        self,
        content: list[dict[str, Any]],
        text: str,
        stop_reason: str,
        tool_calls: list[ToolCall] | None = None,
        reasoning_content: str | None = None,
    ) -> None:
        self.content = content
        self.text = text
        self.stop_reason = stop_reason
        self.tool_calls = tool_calls
        self.reasoning_content = reasoning_content


class ToolCall:
    id: str
    name: str
    input: dict[str, Any]

    def __init__(self, id: str, name: str, input: dict[str, Any]) -> None:
        self.id = id
        self.name = name
        self.input = input


class ModelConfig:
    api_key: str
    base_url: str
    model_name: str

    def __init__(self, api_key: str, base_url: str, model_name: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    @classmethod
    def from_openrouter(cls) -> ModelConfig:
        return cls(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=os.environ["OPENROUTER_BASE_URL"],
            model_name=os.environ["OPENROUTER_MODEL"],
        )


class BaseAdapter(Protocol):
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> ChatResponse:
        ...
