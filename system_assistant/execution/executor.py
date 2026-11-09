from __future__ import annotations

from system_assistant.execution.permissions import ApprovalToken, PermissionManager
from system_assistant.models import ToolResult
from system_assistant.tools.registry import RegisteredTool


class Executor:
    def __init__(self, permissions: PermissionManager):
        self.permissions = permissions

    def execute(self, action, tool: RegisteredTool, token: ApprovalToken | None = None) -> ToolResult:
        self.permissions.consume(action, tool.required_permission(action.arguments), token)
        try:
            return tool.handler(**action.arguments)
        except Exception as exc:  # tool failures become structured results, never false success
            return ToolResult(ok=False, summary=f"{type(exc).__name__}: {exc}", error=str(exc))

