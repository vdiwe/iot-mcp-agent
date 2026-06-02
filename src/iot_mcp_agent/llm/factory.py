"""Factory that creates the right LLM adapter from Settings."""

from ..config import Settings
from .base import LLMAdapter


def create_llm_adapter(
    system_prompt: str,
    model: str | None = None,
    settings: Settings | None = None,
) -> LLMAdapter:
    """
    Instantiate the correct LLM adapter based on ``LLM_PROVIDER`` in settings.

    Args:
        system_prompt: System prompt passed to every LLM call.
        model: Override the model name; falls back to ``settings.llm_model``.
        settings: Loaded Settings instance; created from env if not supplied.

    Returns:
        A concrete :class:`LLMAdapter` instance.

    Raises:
        ValueError: If ``LLM_PROVIDER`` is not one of the supported providers.
        ImportError: If the required SDK for the chosen provider is not installed.
    """
    if settings is None:
        settings = Settings()

    resolved_model = model or settings.llm_model
    provider = settings.llm_provider.split("#", 1)[0].strip().lower()

    if provider == "anthropic":
        from .anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(
            api_key=settings.anthropic_api_key,
            model=resolved_model,
            system_prompt=system_prompt,
        )

    if provider == "openai":
        from .openai_adapter import OpenAIAdapter

        return OpenAIAdapter(
            api_key=settings.openai_api_key,
            model=resolved_model,
            system_prompt=system_prompt,
        )

    if provider == "gemini":
        from .gemini_adapter import GeminiAdapter

        return GeminiAdapter(
            api_key=settings.gemini_api_key,
            model=resolved_model,
            system_prompt=system_prompt,
        )

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. Supported values: 'anthropic', 'openai', 'gemini'."
    )
