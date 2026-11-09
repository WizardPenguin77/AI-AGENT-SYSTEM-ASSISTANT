from __future__ import annotations

from system_assistant.agent.controller import AgentController
from system_assistant.config import log_directory
from system_assistant.execution.permissions import PermissionManager
from system_assistant.interface.cli import CLI
from system_assistant.llm.client import LLMClient
from system_assistant.logging.audit import AuditLogger
from system_assistant.tools import development, filesystem, system, terminal
from system_assistant.tools.registry import ToolRegistry


def build_controller(approver=None) -> AgentController:
    registry = ToolRegistry()
    filesystem.register(registry); system.register(registry); terminal.register(registry); development.register(registry)
    audit = AuditLogger(log_directory()); audit.initialize()
    return AgentController(LLMClient(), registry, PermissionManager(approver), audit)


def main() -> None:
    cli = None
    controller = build_controller()
    cli = CLI(controller)
    controller.permissions.approver = cli.approve
    cli.run()


if __name__ == "__main__": main()

