from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Permission(str, Enum):
    READ = "read-only"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


class ToolResult(BaseModel):
    ok: bool
    summary: str
    data: Any = None
    error: str | None = None
    changed_system: bool = False


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    timestamp: str
    event: str
    details: dict[str, Any] = Field(default_factory=dict)

