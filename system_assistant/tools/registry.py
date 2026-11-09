from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Type

from pydantic import BaseModel

from system_assistant.models import Permission, ToolResult


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    arguments_model: Type[BaseModel]
    permission: Permission
    handler: Callable[..., ToolResult]
    permission_for: Callable[[dict[str, Any]], Permission] | None = None

    def required_permission(self, arguments: dict[str, Any]) -> Permission:
        return self.permission_for(arguments) if self.permission_for else self.permission

    def openai_schema(self) -> dict[str, Any]:
        schema = self.arguments_model.model_json_schema()
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": schema}}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: RegisteredTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.openai_schema() for tool in self._tools.values()]

    def all(self) -> list[RegisteredTool]:
        return list(self._tools.values())

