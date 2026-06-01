"""iot_mcp_agent/config.py — centralised settings via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "anthropic"  # anthropic | openai | gemini
    llm_model: str = "claude-sonnet-4-5"  # provider default; override via LLM_MODEL

    # IoT Platform
    platform: str = "simulate"
    c8y_base_url: str = ""
    c8y_tenant_id: str = ""
    c8y_username: str = ""
    c8y_password: str = ""

    # Agent behaviour
    agent_max_iterations: int = 20
    agent_check_interval_seconds: int = 60
    log_level: str = "INFO"
