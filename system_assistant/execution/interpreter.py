from __future__ import annotations

from pydantic import ValidationError

from system_assistant.models import Action, Permission
from system_assistant.tools.registry import ToolRegistry, RegisteredTool


class ActionError(ValueError):
    pass


class ActionInterpreter:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def interpret(self, tool_name: str, arguments: dict) -> tuple[Action, RegisteredTool]:
        tool = self.registry.get(tool_name)
        if tool is None:
            raise ActionError(f"Unknown tool: {tool_name}")
        unknown = set(arguments) - set(tool.arguments_model.model_fields)
        if unknown:
            raise ActionError(f"Unexpected arguments for {tool_name}: {sorted(unknown)}")
        try:
            validated = tool.arguments_model.model_validate(arguments)
        except ValidationError as exc:
            raise ActionError(f"Invalid arguments for {tool_name}: {exc}") from exc
        action = Action(tool_name=tool_name, arguments=validated.model_dump(mode="json"))
        return action, tool

