from __future__ import annotations

import subprocess

from pydantic import BaseModel, Field

from system_assistant.config import COMMAND_TIMEOUT_SECONDS
from system_assistant.models import Permission, ToolResult
from system_assistant.tools.registry import RegisteredTool, ToolRegistry


class CommandArgs(BaseModel):
    command: list[str] = Field(min_length=1, max_length=20)
    cwd: str | None = None
    timeout: int = Field(default=COMMAND_TIMEOUT_SECONDS, ge=1, le=120)


def _command_permission(args: dict) -> Permission:
    # Conservative allowlist: inspection commands only. Everything else is write-capable.
    allowed = {"pwd", "ls", "dir", "whoami", "hostname", "ver", "where", "which", "git", "python", "python3"}
    command = args.get("command", [])
    dangerous = {"rm", "rmdir", "del", "erase", "format", "shutdown", "reboot", "kill", "taskkill", "chmod", "chown"}
    if any(part.lower() in dangerous for part in command): return Permission.DESTRUCTIVE
    if not command or command[0].lower() not in allowed: return Permission.WRITE
    if command[0].lower() == "git" and len(command) > 1 and command[1] not in {"status", "branch", "log", "diff", "remote"}: return Permission.WRITE
    if command[0].lower() in {"python", "python3"}:
        safe_python_flags = {"--version", "-V", "--help", "-h"}
        return Permission.READ if len(command) == 2 and command[1] in safe_python_flags else Permission.WRITE
    return Permission.READ

def run_command(command: list[str], cwd: str | None = None, timeout: int = COMMAND_TIMEOUT_SECONDS) -> ToolResult:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, shell=False, check=False)
    return ToolResult(ok=completed.returncode == 0, summary=f"Command exited with code {completed.returncode}", data={"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode}, error=None if completed.returncode == 0 else completed.stderr)

def register(registry: ToolRegistry) -> None:
    # Permission is conservatively WRITE for the generic command endpoint; the controller may downgrade only known-safe commands.
    registry.register(RegisteredTool("run_command", "Run one structured command without shell expansion. Unsafe or modifying commands require approval.", CommandArgs, Permission.WRITE, run_command, _command_permission))

