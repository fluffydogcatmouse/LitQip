from __future__ import annotations

import logging
from pathlib import Path

from litqip.constants import MAX_OUTPUT_LENGTH

logger = logging.getLogger("litqip.tools.file")


def safe_path(p: str) -> Path:
    """Resolve path and verify it stays within the current working directory."""
    workdir = Path.cwd()
    path = (workdir / p).resolve()
    if not path.is_relative_to(workdir):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def read(path: str, limit: int | None = None) -> str:
    """Read file content. Never raises — errors are returned as strings."""
    try:
        fp = safe_path(path)
        lines = fp.read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        result = "\n".join(lines)
        logger.info("read: %s (%d chars)", path, len(result))
        return result[:MAX_OUTPUT_LENGTH]
    except Exception as e:
        logger.warning("read failed: %s: %s", path, e)
        return f"Error: {e}"


def write(path: str, content: str) -> str:
    """Write content to file. Never raises — errors are returned as strings."""
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        logger.info("write: %s (%d bytes)", path, len(content))
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        logger.warning("write failed: %s: %s", path, e)
        return f"Error: {e}"


def edit(path: str, old_text: str, new_text: str) -> str:
    """Replace text in file. Never raises — errors are returned as strings."""
    try:
        fp = safe_path(path)
        c = fp.read_text()
        if old_text not in c:
            logger.warning("edit: text not found in %s", path)
            return f"Error: Text not found in {path}"
        fp.write_text(c.replace(old_text, new_text, 1))
        logger.info("edit: %s", path)
        return f"Edited {path}"
    except Exception as e:
        logger.warning("edit failed: %s: %s", path, e)
        return f"Error: {e}"
