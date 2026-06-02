"""Google Gemini adapter (gemini-2.0-flash, gemini-2.5-pro, etc.)."""

import uuid
from typing import Any

from .base import LLMAdapter, LLMResponse, ToolCall


class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        try:
            from google import genai  # type: ignore[import-untyped,import-not-found]
            from google.genai import types  # type: ignore[import-untyped,import-not-found]
        except ImportError as exc:
            raise ImportError(
                "google-genai package is required for the Gemini provider. "
                "Install it with: pip install 'iot-mcp-agent[gemini]'"
            ) from exc

        clean_api_key = api_key.split("#", 1)[0].strip()
        if not clean_api_key:
            raise ValueError(
                "GEMINI_API_KEY is empty. Set a valid Google AI Studio API key in .env."
            )

        self.model = model
        self.system_prompt = system_prompt
        self._types = types
        # Force Google AI Studio (Gemini Developer API) mode.
        # This avoids accidental Vertex AI endpoint usage, which requires OAuth.
        self._client = genai.Client(api_key=clean_api_key, vertexai=False)

    async def chat(self, messages: list[Any], tools: list[Any]) -> LLMResponse:
        types = self._types

        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            tools=tools if tools else None,
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=messages,
                config=config,
            )
        except Exception as exc:
            text = str(exc)
            if "UNAUTHENTICATED" in text or "401" in text:
                raise RuntimeError(
                    "Gemini authentication failed. Set a valid GEMINI_API_KEY in .env "
                    "(from Google AI Studio) and ensure LLM_PROVIDER=gemini."
                ) from exc
            raise

        candidates = response.candidates or []
        first_candidate = candidates[0] if candidates else None
        content = first_candidate.content if first_candidate else None
        parts = content.parts if content and content.parts else []

        tool_calls: list[ToolCall] = []
        for part in parts:
            fc = part.function_call
            if fc:
                name = fc.name
                if not name:
                    continue
                args = fc.args or {}
                if not isinstance(args, dict):
                    args = dict(args)

                tool_calls.append(
                    ToolCall(
                        id=getattr(fc, "id", None) or str(uuid.uuid4()),
                        name=name,
                        input=args,
                    )
                )

        final_text: str | None = None
        if not tool_calls:
            final_text = response.text or ""

        return LLMResponse(
            final_text=final_text,
            tool_calls=tool_calls,
            raw=content,
        )

    def format_tools(self, mcp_tools: list) -> list[Any]:
        types = self._types
        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=t.name,
                        description=t.description,
                        parameters=t.inputSchema,
                    )
                    for t in mcp_tools
                ]
            )
        ]

    def make_user_message(self, text: str) -> Any:
        types = self._types
        return types.Content(role="user", parts=[types.Part.from_text(text=text)])

    def make_assistant_message(self, raw: Any) -> Any:
        types = self._types
        if raw is not None:
            # raw is usually a types.Content with role="model" from the Gemini response.
            return raw
        return types.Content(role="model", parts=[types.Part.from_text(text="")])

    def make_tool_results_message(
        self,
        tool_calls: list[ToolCall],
        results: dict[str, str],
    ) -> list[Any]:
        types = self._types
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=tc.name,
                        response={"result": results[tc.id]},
                    )
                    for tc in tool_calls
                ],
            )
        ]
