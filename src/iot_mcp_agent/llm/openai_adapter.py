"""OpenAI adapter (GPT-4o, o1, etc.)."""

import json
from typing import Any

from .base import LLMAdapter, LLMResponse, ToolCall


class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "openai package is required for the OpenAI provider. "
                "Install it with: pip install 'iot-mcp-agent[openai]'"
            ) from exc

        self.model = model
        self.system_prompt = system_prompt
        self._client = AsyncOpenAI(api_key=api_key)  # type: ignore[name-defined]

    async def chat(self, messages: list[Any], tools: list[Any]) -> LLMResponse:
        from openai import NOT_GIVEN  # type: ignore[import-untyped,import-not-found]

        all_messages = [{"role": "system", "content": self.system_prompt}, *messages]
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=all_messages,  # type: ignore[arg-type]
            tools=tools if tools else NOT_GIVEN,  # type: ignore[arg-type]
        )

        msg = response.choices[0].message

        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        input=json.loads(tc.function.arguments),
                    )
                )

        final_text: str | None = msg.content if not tool_calls else None

        return LLMResponse(final_text=final_text, tool_calls=tool_calls, raw=msg)

    def format_tools(self, mcp_tools: list) -> list[Any]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema,
                },
            }
            for t in mcp_tools
        ]

    def make_user_message(self, text: str) -> Any:
        return {"role": "user", "content": text}

    def make_assistant_message(self, raw: Any) -> Any:
        msg: dict[str, Any] = {"role": "assistant", "content": raw.content or ""}
        if raw.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in raw.tool_calls
            ]
        return msg

    def make_tool_results_message(
        self,
        tool_calls: list[ToolCall],
        results: dict[str, str],
    ) -> list[Any]:
        # OpenAI requires one "tool" role message per tool call.
        return [
            {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": results[tc.id],
            }
            for tc in tool_calls
        ]
