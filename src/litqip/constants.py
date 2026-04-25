"""litqip shared constants."""

from pathlib import Path

from pyfiglet import Figlet

_BANNER_RAW = Figlet(font="banner3").renderText("LitQip").rstrip()
BANNER = "\x1b[36m" + _BANNER_RAW.replace("#", "\u2588") + "\x1b[0m"

# --- Paths ---

#: Project-wide data directory in the current working directory.
LITQIP_DIR = Path.cwd() / ".litqip"

# --- Limits ---

#: Maximum length of tool output strings (chars).
MAX_OUTPUT_LENGTH = 50_000

#: Maximum number of Todo items.
MAX_TODO_ITEMS = 20

#: Maximum subagent tool-call rounds.
SUBAGENT_MAX_ROUNDS = 30

#: Keep the last N tool results during microcompact.
MICROCOMPACT_KEEP = 3

#: Number of rounds without TodoWrite before nagging.
TODO_NAG_ROUNDS = 3

# --- Timeouts (seconds) ---

#: Bash command timeout.
BASH_TIMEOUT = 120

#: LLM HTTP request timeout.
LLM_TIMEOUT = 120.0

# --- Compression ---

#: Token estimate threshold that triggers auto-compact.
TOKEN_THRESHOLD = 100_000

#: Number of trailing characters from JSON to feed to the summarizer.
AUTO_COMPACT_CHARS = 80_000
