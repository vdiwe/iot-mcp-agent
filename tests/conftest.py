"""Pytest configuration and shared fixtures."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    monkeypatch.setenv("PLATFORM", "simulate")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    return MagicMock(
        content="Task completed successfully",
        stop_reason="end_turn",
        tool_calls=[],
    )


@pytest.fixture
def mock_tool_call():
    """Create a mock tool call."""
    return MagicMock(
        name="list_devices",
        arguments={"limit": 10},
    )


@pytest.fixture
def mock_async_context():
    """Create a mock async context manager."""
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=ctx)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx
