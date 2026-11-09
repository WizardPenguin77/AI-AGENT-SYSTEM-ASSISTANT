from __future__ import annotations

import json
import os
import time
from typing import Any

from openai import OpenAI

from system_assistant.config import MODEL
from system_assistant.llm.prompts import SYSTEM_PROMPT


class LLMClient:
    def __init__(self, model: str = MODEL, client: Any | None = None):
        if not os.environ.get("OPENAI_API_KEY") and client is None: raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = client or OpenAI(timeout=60, max_retries=0)
        self.model = model
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def complete(self, user_text: str, tools: list[dict]) -> Any:
        self.messages.append({"role": "user", "content": user_text})
        last_error = None
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(model=self.model, messages=self.messages, tools=tools, tool_choice="auto")
                message = response.choices[0].message
                self.messages.append(message.model_dump(exclude_none=True))
                return message
            except Exception as exc:
                last_error = exc
                if attempt < 2: time.sleep(2 ** attempt)
        raise RuntimeError(f"OpenAI request failed after retries: {last_error}") from last_error

    def add_tool_result(self, call_id: str, result: Any) -> None:
        self.messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result, default=str)[:100_000]})

