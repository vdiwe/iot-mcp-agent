"""Abstract base class and shared data types for all LLM adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A single tool call requested by the LLM."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    """Normalised response from any LLM provider."""

    # None means the model made tool calls; str (possibly empty) means it finished.
    final_text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    # Provider-specific raw object — passed back to make_assistant_message().
    raw: Any = None


class LLMAdapter(ABC):
    """
    Common interface for all LLM provider backends.

    Each adapter translates the generic agentic loop into the idioms of its
    provider SDK, keeping BaseAgent free of any provider-specific logic.
    """

    @abstractmethod
    async def chat(self, messages: list[Any], tools: list[Any]) -> LLMResponse:
        """Send messages to the LLM and return a normalised response."""
        ...

    @abstractmethod
    def format_tools(self, mcp_tools: list) -> list[Any]:
        """Convert MCP tool definitions to the provider's tool format."""
        ...

    @abstractmethod
    def make_user_message(self, text: str) -> Any:
        """Wrap a plain text string as a user message for this provider."""
        ...

    @abstractmethod
    def make_assistant_message(self, raw: Any) -> Any:
        """Wrap the raw provider response as an assistant history entry."""
        ...

    @abstractmethod
    def make_tool_results_message(
        self,
        tool_calls: list[ToolCall],
        results: dict[str, str],
    ) -> list[Any]:
        """
        Return one or more message objects carrying tool results.

        Always returns a list so callers can use ``messages.extend()``.
        Anthropic/Gemini return a list of one; OpenAI returns one per call.
        """
        ...
