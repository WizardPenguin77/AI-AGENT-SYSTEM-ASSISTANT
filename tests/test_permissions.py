import pytest

from system_assistant.execution.permissions import PermissionDenied, PermissionManager
from system_assistant.models import Action, Permission


def action(name="write_file", value="x"): return Action(tool_name=name, arguments={"value": value})

def test_read_needs_no_approval():
    assert PermissionManager().authorize(action("read"), Permission.READ) is None

def test_write_without_approval_is_denied():
    with pytest.raises(PermissionDenied): PermissionManager().authorize(action(), Permission.WRITE)

def test_decline_never_executes():
    with pytest.raises(PermissionDenied): PermissionManager(lambda *_: False).authorize(action(), Permission.WRITE)

def test_ambiguous_approval_is_denied():
    with pytest.raises(PermissionDenied): PermissionManager(lambda *_: "yes").authorize(action(), Permission.WRITE)

def test_approval_is_exact_and_single_use():
    manager = PermissionManager(lambda *_: True); original = action(); token = manager.authorize(original, Permission.WRITE)
    with pytest.raises(PermissionDenied): manager.consume(action(value="different"), Permission.WRITE, token)
    manager.consume(original, Permission.WRITE, token)
    with pytest.raises(PermissionDenied): manager.consume(original, Permission.WRITE, token)

def test_banned_destructive_action_is_denied():
    with pytest.raises(PermissionDenied): PermissionManager(lambda *_: True).authorize(Action(tool_name="run_command", arguments={"command": ["rm", "-rf", "/"]}), Permission.DESTRUCTIVE)

