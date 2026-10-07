"""Tests for configuration boundary, environment parsing, and validation."""

import pytest
from ating_engine.config.settings import (
    EnvironmentType,
    LogLevel,
    load_settings,
)
from ating_engine.errors.base import ConfigurationError


def test_default_settings():
    settings = load_settings(env={})
    assert settings.engine.environment == EnvironmentType.DEVELOPMENT
    assert settings.engine.log_level == LogLevel.INFO
    assert not settings.database.is_configured
    assert not settings.ai.is_configured


def test_custom_environment_settings():
    custom_env = {
        "ENGINE_ENV": "staging",
        "ENGINE_LOG_LEVEL": "DEBUG",
        "ENGINE_VERSION": "0.2.0-alpha",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_ANON_KEY": "anon-key-abc",
        "GEMINI_ENABLED": "true",
        "GEMINI_API_KEY": "test-key-xyz",
    }
    settings = load_settings(env=custom_env)
    assert settings.engine.environment == EnvironmentType.STAGING
    assert settings.engine.log_level == LogLevel.DEBUG
    assert settings.engine.engine_version == "0.2.0-alpha"
    assert settings.database.is_configured
    assert settings.ai.is_configured


def test_invalid_environment_raises_configuration_error():
    with pytest.raises(ConfigurationError) as exc:
        load_settings(env={"ENGINE_ENV": "invalid_galaxy_env"})
    assert "Invalid ENGINE_ENV" in str(exc.value)


def test_invalid_log_level_raises_configuration_error():
    with pytest.raises(ConfigurationError) as exc:
        load_settings(env={"ENGINE_LOG_LEVEL": "VERBOSE"})
    assert "Invalid ENGINE_LOG_LEVEL" in str(exc.value)
