from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from litqip.constants import BASH_TIMEOUT, MAX_OUTPUT_LENGTH

logger = logging.getLogger("litqip.tools.bash")

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "sudo",
    "shutdown",
    "reboot",
    "> /dev/",
    "| /dev/",
]


def run_bash(command: str) -> str:
    """Execute a bash command with auditing."""
    logger.info("bash audit: %s", command)

    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            logger.warning("dangerous command blocked: %s", command)
            return f"Error: Dangerous command blocked: {command}"

    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=BASH_TIMEOUT,
        )
        out = (r.stdout + r.stderr).strip()
        result = out[:MAX_OUTPUT_LENGTH] if out else "(no output)"
        logger.info("bash completed: exit=%d, output_len=%d", r.returncode, len(result))
        return result
    except subprocess.TimeoutExpired:
        logger.warning("bash timeout: %s", command)
        return f"Error: Timeout ({BASH_TIMEOUT}s)"
    except Exception as e:
        logger.error("bash error: %s: %s", command, e)
        return f"Error: {e}"
