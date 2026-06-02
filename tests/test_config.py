"""Tests for iot_mcp_agent.config module."""

import os
from unittest.mock import patch

import pytest

from iot_mcp_agent.config import Settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_settings_defaults(self, mock_env_vars):
        """Test that Settings loads with correct defaults."""
        settings = Settings()

        assert settings.llm_provider == "anthropic"
        assert settings.anthropic_api_key == "test-key-123"
        assert settings.platform == "simulate"
        assert settings.agent_max_iterations == 20
        assert settings.agent_check_interval_seconds == 60
        assert settings.log_level == "INFO"

    def test_settings_from_env(self, monkeypatch):
        """Test Settings initialization from environment variables."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        monkeypatch.setenv("PLATFORM", "cumulocity")
        monkeypatch.setenv("AGENT_MAX_ITERATIONS", "30")

        settings = Settings()

        assert settings.llm_provider == "openai"
        assert settings.openai_api_key == "sk-test-123"
        assert settings.platform == "cumulocity"
        assert settings.agent_max_iterations == 30

    def test_settings_gemini_provider(self, monkeypatch):
        """Test Gemini LLM provider configuration."""
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy-test-123")

        settings = Settings()

        assert settings.llm_provider == "gemini"
        assert settings.gemini_api_key == "AIzaSy-test-123"

    def test_settings_c8y_configuration(self, monkeypatch):
        """Test Cumulocity-specific configuration."""
        monkeypatch.setenv("C8Y_BASE_URL", "https://test.cumulocity.com")
        monkeypatch.setenv("C8Y_USERNAME", "user@example.com")
        monkeypatch.setenv("C8Y_PASSWORD", "password123")
        monkeypatch.setenv("C8Y_TENANT_ID", "t12345")

        settings = Settings()

        assert settings.c8y_base_url == "https://test.cumulocity.com"
        assert settings.c8y_username == "user@example.com"
        assert settings.c8y_password == "password123"
        assert settings.c8y_tenant_id == "t12345"

    def test_settings_log_level_validation(self, monkeypatch):
        """Test log level is properly configured."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.log_level == "DEBUG"

    def test_settings_default_llm_model(self, monkeypatch):
        """Test model is populated from defaults/.env."""
        settings = Settings()
        assert isinstance(settings.llm_model, str)
        assert settings.llm_model

    def test_settings_custom_llm_model(self, monkeypatch):
        """Test custom LLM model override."""
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        settings = Settings()

        assert settings.llm_model == "gpt-4o"
