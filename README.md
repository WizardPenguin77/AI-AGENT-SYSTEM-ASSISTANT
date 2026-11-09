# System Assistant

System Assistant is a terminal-based OpenAI agent for inspecting and managing a computer with a permission-first execution pipeline. It uses structured tool calls only; the model cannot execute Python or shell code directly.

## Safety model

Read-only inspection tools run without confirmation. Every write-capable or destructive tool requires an exact, one-time approval from the terminal interface. Unknown tools, malformed arguments, protected paths, overwrites, broad destructive targets, and shell expansion are rejected. The generic command tool uses `shell=False`, structured argument lists, timeouts, and a conservative read-only allowlist; scripts and unknown commands require approval.

The default model is `gpt-4o-mini`. Set `OPENAI_API_KEY` in the environment; it is never printed or logged. Audit logs are stored at `~/.system-assistant/logs/audit.jsonl` by default. The application creates that directory during startup. Set `SYSTEM_ASSISTANT_LOG_DIR` to choose another application-owned location.

## Setup and launch

```bash
python3 -m venv .venv
. .venv/bin/activate       # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -e '.[test]'
export OPENAI_API_KEY='...' # PowerShell: $env:OPENAI_API_KEY='...'
system-assistant
```

Use natural-language requests such as “check my disk usage”, “list Python files below this project”, or “create a new file at …”. The latter displays the exact action and waits for `yes`. `help`, `history`, `clear`, and `exit` are also supported.

## Tests

```bash
pytest
```

Tests use temporary directories and mocked permission boundaries; they do not modify the real filesystem. Windows support is prepared through structured `subprocess` invocation, while the current tests and fixed developer commands are cross-platform where possible.
