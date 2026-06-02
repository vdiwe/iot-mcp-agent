"""Tests for iot_mcp_agent.llm.factory module."""

import importlib.util

import pytest

from iot_mcp_agent.config import Settings
from iot_mcp_agent.llm.factory import create_llm_adapter


class TestLLMFactory:
    """Test suite for LLM adapter factory."""

    def test_create_anthropic_adapter(self):
        settings = Settings(
            llm_provider="anthropic",
            anthropic_api_key="test-key",
            llm_model="claude-sonnet-4-5",
        )
        adapter = create_llm_adapter(system_prompt="You are a test agent", settings=settings)
        assert adapter is not None
        assert hasattr(adapter, "chat")

    def test_create_openai_adapter_when_installed(self):
        if importlib.util.find_spec("openai") is None:
            pytest.skip("openai extra is not installed")

        settings = Settings(
            llm_provider="openai",
            openai_api_key="test-key",
            llm_model="gpt-4o",
        )
        adapter = create_llm_adapter(system_prompt="You are a test agent", settings=settings)
        assert adapter is not None
        assert hasattr(adapter, "chat")

    def test_create_gemini_adapter_when_installed(self):
        if importlib.util.find_spec("google.genai") is None:
            pytest.skip("gemini extra is not installed")

        settings = Settings(
            llm_provider="gemini",
            gemini_api_key="test-key",
            llm_model="gemini-2.5-flash",
        )
        adapter = create_llm_adapter(system_prompt="You are a test agent", settings=settings)
        assert adapter is not None
        assert hasattr(adapter, "chat")

    def test_invalid_provider_raises_error(self):
        settings = Settings(llm_provider="invalid_provider")
        with pytest.raises(ValueError):
            create_llm_adapter(system_prompt="You are a test agent", settings=settings)

    def test_model_override_takes_precedence(self):
        settings = Settings(
            llm_provider="anthropic",
            anthropic_api_key="test-key",
            llm_model="default-model",
        )
        adapter = create_llm_adapter(
            system_prompt="You are a test agent",
            model="override-model",
            settings=settings,
        )
        assert adapter.model == "override-model"
