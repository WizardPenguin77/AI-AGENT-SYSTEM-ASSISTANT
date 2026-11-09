from __future__ import annotations

import os
import platform

import psutil
from pydantic import BaseModel

from system_assistant.models import Permission, ToolResult
from system_assistant.tools.registry import RegisteredTool, ToolRegistry


class EmptyArgs(BaseModel): pass

def system_info() -> ToolResult:
    return ToolResult(ok=True, summary="System information collected", data={"os": platform.platform(), "python": platform.python_version(), "machine": platform.machine()})
def resources() -> ToolResult:
    disk = psutil.disk_usage(os.getcwd())
    return ToolResult(ok=True, summary="Resource usage collected", data={"cpu_percent": psutil.cpu_percent(interval=0.2), "memory": psutil.virtual_memory()._asdict(), "disk": disk._asdict()})
def processes() -> ToolResult:
    return ToolResult(ok=True, summary="Running processes collected", data=[{"pid": p.info["pid"], "name": p.info["name"], "status": p.info["status"]} for p in psutil.process_iter(["pid", "name", "status"])])
def environment_names() -> ToolResult:
    return ToolResult(ok=True, summary="Environment variable names collected", data=sorted(os.environ))

def register(registry: ToolRegistry) -> None:
    for name, desc, handler in [("system_info", "Inspect operating system information.", system_info), ("resource_usage", "Inspect CPU, memory, and disk usage.", resources), ("list_processes", "List running processes without control actions.", processes), ("environment_variable_names", "List environment variable names only; never values.", environment_names)]:
        registry.register(RegisteredTool(name, desc, EmptyArgs, Permission.READ, handler))

