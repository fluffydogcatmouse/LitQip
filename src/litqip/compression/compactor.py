from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from litqip.constants import AUTO_COMPACT_CHARS, MICROCOMPACT_KEEP, TOKEN_THRESHOLD

logger = logging.getLogger("litqip.compression")


def _transcript_dir() -> Path:
    return Path.cwd() / ".transcripts"


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    """Rough token estimate via JSON serialization."""
    return len(json.dumps(messages, default=str)) // 4


def microcompact(messages: list[dict[str, Any]]) -> None:
    """
    Clear old tool results to save context, keeping the last 3.
    Operates in-place on the messages list.
    """
    indices: list[dict[str, Any]] = []
    for msg in messages:
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    indices.append(part)
    if len(indices) <= MICROCOMPACT_KEEP:
        return
    for part in indices[:-MICROCOMPACT_KEEP]:
        if isinstance(part.get("content"), str) and len(part["content"]) > 100:
            part["content"] = "[cleared]"
    logger.info("microcompact: cleared %d tool results", len(indices) - 3)


def auto_compact(
    messages: list[dict[str, Any]],
    llm_client: Any,
) -> list[dict[str, Any]]:
    """
    Archive messages to .transcripts/ and replace with a compressed summary.
    Returns a new messages list with the summary.
    """
    tdir = _transcript_dir()
    tdir.mkdir(exist_ok=True)
    path = tdir / f"transcript_{int(time.time())}.jsonl"
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    logger.info("archived transcript to %s", path.name)

    conv_text = json.dumps(messages, default=str)[-AUTO_COMPACT_CHARS:]
    resp = llm_client.chat(
        messages=[{"role": "user", "content": f"Summarize for continuity:\n{conv_text}"}],
    )
    summary = resp.text or "(no summary)"
    logger.info("auto_compact summary: %d chars", len(summary))
    return [
        {
            "role": "user",
            "content": f"[Compressed. Transcript: {path.name}]\n{summary}",
        }
    ]
