"""Anthropic Claude adapter."""

from typing import Any

import anthropic

from .base import LLMAdapter, LLMResponse, ToolCall


class AnthropicAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def chat(self, messages: list[Any], tools: list[Any]) -> LLMResponse:
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            tools=tools,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )

        tool_calls = [
            ToolCall(id=b.id, name=b.name, input=b.input)  # type: ignore[union-attr]
            for b in response.content
            if b.type == "tool_use"
        ]

        final_text: str | None = None
        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""  # type: ignore[union-attr]
            )

        return LLMResponse(final_text=final_text, tool_calls=tool_calls, raw=response)

    def format_tools(self, mcp_tools: list) -> list[Any]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in mcp_tools
        ]

    def make_user_message(self, text: str) -> Any:
        return {"role": "user", "content": text}

    def make_assistant_message(self, raw: Any) -> Any:
        return {"role": "assistant", "content": raw.content}

    def make_tool_results_message(
        self,
        tool_calls: list[ToolCall],
        results: dict[str, str],
    ) -> list[Any]:
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": results[tc.id],
                    }
                    for tc in tool_calls
                ],
            }
        ]
