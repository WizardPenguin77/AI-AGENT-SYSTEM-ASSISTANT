import pytest
from pydantic import BaseModel

from system_assistant.execution.interpreter import ActionError, ActionInterpreter
from system_assistant.models import Permission, ToolResult
from system_assistant.tools.registry import RegisteredTool, ToolRegistry

class Args(BaseModel): value: int
def handler(value): return ToolResult(ok=True, summary=str(value))

def registry():
    r = ToolRegistry(); r.register(RegisteredTool("test", "test", Args, Permission.READ, handler)); return r

def test_validates_and_interprets():
    action, tool = ActionInterpreter(registry()).interpret("test", {"value": 3})
    assert action.arguments == {"value": 3} and tool.name == "test"

def test_unknown_tool_rejected():
    with pytest.raises(ActionError): ActionInterpreter(registry()).interpret("missing", {})

def test_extra_arguments_rejected():
    with pytest.raises(ActionError): ActionInterpreter(registry()).interpret("test", {"value": 3, "extra": 1})

