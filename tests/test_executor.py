import pytest

from system_assistant.execution.executor import Executor
from system_assistant.execution.permissions import PermissionDenied, PermissionManager
from system_assistant.models import Action, Permission, ToolResult
from system_assistant.tools.registry import RegisteredTool
from pydantic import BaseModel

class Args(BaseModel): pass
def mutate(): return ToolResult(ok=True, summary="changed", changed_system=True)

def test_executor_requires_permission():
    tool = RegisteredTool("mutate", "", Args, Permission.WRITE, mutate)
    with pytest.raises(PermissionDenied): Executor(PermissionManager()).execute(Action(tool_name="mutate"), tool)

def test_executor_consumes_exact_approval():
    tool = RegisteredTool("mutate", "", Args, Permission.WRITE, mutate)
    manager = PermissionManager(lambda *_: True)
    action = Action(tool_name="mutate")
    token = manager.authorize(action, Permission.WRITE)
    assert Executor(manager).execute(action, tool, token).changed_system

