from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from system_assistant.models import Action, Permission


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"


@dataclass(frozen=True)
class ApprovalToken:
    fingerprint: str


class PermissionDenied(Exception):
    pass


def fingerprint(action: Action) -> str:
    encoded = json.dumps(action.model_dump(mode="json"), sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


class PermissionManager:
    """Central policy gate. Approval is exact-action, single-use, and never implicit."""

    def __init__(self, approver: Callable[[Action, Permission], bool] | None = None):
        self.approver = approver
        self._approved: set[str] = set()

    def authorize(self, action: Action, permission: Permission) -> ApprovalToken | None:
        if permission == Permission.READ:
            return None
        if permission == Permission.DESTRUCTIVE and self._is_banned(action):
            raise PermissionDenied("This destructive operation is denied by safety policy")
        if self.approver is None or self.approver(action, permission) is not True:
            raise PermissionDenied("Operation was not explicitly approved")
        token = ApprovalToken(fingerprint(action))
        self._approved.add(token.fingerprint)
        return token

    def consume(self, action: Action, permission: Permission, token: ApprovalToken | None) -> None:
        if permission == Permission.READ:
            return
        expected = fingerprint(action)
        if token is None or token.fingerprint != expected or expected not in self._approved:
            raise PermissionDenied("Missing, mismatched, or already-used approval")
        self._approved.remove(expected)

    @staticmethod
    def _is_banned(action: Action) -> bool:
        command = action.arguments.get("command", [])
        if isinstance(command, list):
            tokens = [str(item).lower() for item in command]
            normalized = " ".join(tokens)
            if "rm" in tokens and "-rf" in tokens and "/" in tokens:
                return True
            if "rmdir" in tokens and "/s" in tokens:
                return True
            return any(item in tokens for item in {"format", "diskpart", "shutdown", "reboot"})
        args = json.dumps(action.arguments).lower()
        return any(item in args for item in ("format", "diskpart", "shutdown", "reboot"))


def protected_path(path: str | Path) -> bool:
    resolved = Path(path).expanduser().resolve(strict=False)
    protected = [Path("/").resolve(), Path("/etc").resolve(), Path("/boot").resolve(), Path("/root").resolve()]
    if resolved in protected:
        return True
    return any(parent in resolved.parents for parent in protected[1:])

