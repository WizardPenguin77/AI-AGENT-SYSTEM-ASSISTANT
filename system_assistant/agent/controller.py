from __future__ import annotations

import json

from system_assistant.execution.executor import Executor
from system_assistant.execution.interpreter import ActionError, ActionInterpreter
from system_assistant.execution.permissions import PermissionDenied, PermissionManager
from system_assistant.llm.client import LLMClient
from system_assistant.logging.audit import AuditLogger
from system_assistant.models import ToolResult
from system_assistant.tools.registry import ToolRegistry


class AgentController:
    def __init__(self, llm: LLMClient, registry: ToolRegistry, permissions: PermissionManager, audit: AuditLogger):
        self.llm, self.registry, self.permissions, self.audit = llm, registry, permissions, audit
        self.interpreter = ActionInterpreter(registry)
        self.executor = Executor(permissions)

    def handle(self, request: str) -> str:
        self.audit.record("user_request", request=request)
        try:
            message = self.llm.complete(request, self.registry.schemas())
            rounds = 0
            while getattr(message, "tool_calls", None) and rounds < 10:
                rounds += 1
                for call in message.tool_calls:
                    try:
                        args = json.loads(call.function.arguments or "{}")
                        action, tool = self.interpreter.interpret(call.function.name, args)
                        permission = tool.required_permission(action.arguments)
                        self.audit.record("proposed_action", tool=tool.name, arguments=action.arguments, permission=permission.value)
                        token = self.permissions.authorize(action, permission)
                        self.audit.record("approval", tool=tool.name, granted=True)
                        result = self.executor.execute(action, tool, token)
                    except (ActionError, PermissionDenied, json.JSONDecodeError) as exc:
                        self.audit.record("action_rejected", error=str(exc))
                        result = ToolResult(ok=False, summary="Action was not executed", error=str(exc))
                    self.audit.record("execution", result=result.model_dump())
                    self.llm.add_tool_result(call.id, result.model_dump())
                message = self.llm.complete("Continue based on the tool results. Do not repeat completed actions.", self.registry.schemas())
            return message.content or "I completed the available analysis."
        except Exception as exc:
            self.audit.record("agent_error", error=str(exc))
            return f"I could not complete that request: {exc}"

