import logging
import os
import sys

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".litqip" / ".env", override=True)

from litqip.repl import REPL


def main():
    log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(name)s >> %(message)s",
    )
    repl = REPL()
    try:
        repl.run()
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
