from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECRET_KEY = re.compile(r"(key|token|password|secret|authorization|credential)", re.I)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: "[REDACTED]" if SECRET_KEY.search(k) else redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    text = str(value)
    return "[REDACTED]" if SECRET_KEY.search(text) and len(text) < 300 else text


class AuditLogger:
    def __init__(self, directory: Path):
        self.path = directory.expanduser() / "audit.jsonl"
        self.initialized = False

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self.initialized = True

    def record(self, event: str, **details: Any) -> None:
        if not self.initialized:
            raise RuntimeError("Audit logging is not initialized")
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "details": redact(details)}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")

