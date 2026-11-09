from __future__ import annotations

import os
from pathlib import Path


def log_directory() -> Path:
    return Path(os.environ.get("SYSTEM_ASSISTANT_LOG_DIR", "~/.system-assistant/logs")).expanduser()


MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_FILE_BYTES = 1_000_000
COMMAND_TIMEOUT_SECONDS = 30

