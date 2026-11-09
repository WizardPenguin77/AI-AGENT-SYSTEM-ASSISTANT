from __future__ import annotations

from system_assistant.models import Permission
from system_assistant.tools.registry import RegisteredTool, ToolRegistry
from system_assistant.tools.terminal import CommandArgs, run_command

def register(registry: ToolRegistry) -> None:
    for name, args, description, command in [("git_status", [], "Inspect Git status.", ["git", "status", "--short"]), ("git_history", [], "Inspect recent Git history.", ["git", "log", "--oneline", "-10"]), ("project_tests", [], "Run the project's tests; approval is required because test code may modify state.", ["pytest"])]:
        # Fixed command tools do not accept caller-provided shell text.
        def handler(_command=command): return run_command(_command)
        from pydantic import create_model
        registry.register(RegisteredTool(name, description, create_model(f"{name}Args"), Permission.WRITE if name == "project_tests" else Permission.READ, handler))

