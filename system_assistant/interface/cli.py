from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from system_assistant.agent.controller import AgentController
from system_assistant.execution.permissions import Permission
from system_assistant.models import Action


class CLI:
    def __init__(self, controller: AgentController, console: Console | None = None):
        self.controller, self.console = controller, console or Console()
        self.history: list[tuple[str, str]] = []

    def approve(self, action: Action, permission: Permission) -> bool:
        self.console.print(Panel(f"Tool: {action.tool_name}\nPermission: {permission.value}\nArguments: {action.arguments}\n\nThis may modify your computer." if permission != Permission.READ else str(action.arguments), title="PROPOSED ACTION"))
        return Prompt.ask("Approve this exact operation?", choices=["yes", "no"], default="no").lower() == "yes"

    def run(self) -> None:
        self.console.print(Panel("SYSTEM ASSISTANT\nPermission-first terminal AI", title="Welcome"))
        while True:
            try: request = Prompt.ask(">")
            except (EOFError, KeyboardInterrupt): break
            if request.lower() in {"exit", "quit"}: break
            if request.lower() == "help": self.console.print("Natural language requests, plus: history, status, clear, exit"); continue
            if request.lower() == "history":
                for user, answer in self.history: self.console.print(f"[cyan]You:[/] {user}\n[green]Assistant:[/] {answer}")
                continue
            if request.lower() == "clear": self.console.clear(); continue
            answer = self.controller.handle(request)
            self.history.append((request, answer))
            self.console.print(Panel(answer, title="Assistant"))

