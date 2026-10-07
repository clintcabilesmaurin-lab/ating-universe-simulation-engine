"""Runtime configuration boundaries for the Ating Universe Simulation Engine."""

import os
from enum import Enum
from typing import Any, Dict, Mapping, Optional
from pydantic import BaseModel, Field

from ating_engine.errors.base import ConfigurationError
from ating_engine.version import __version__


class EnvironmentType(str, Enum):
    """Execution environment types."""

    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Allowed logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EngineRuntimeSettings(BaseModel):
    """Core simulation engine runtime parameters."""

    environment: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    engine_version: str = Field(default=__version__)


class DatabaseConfig(BaseModel):
    """Configuration boundary for durable persistence (e.g. Supabase).

    All values are optional in Phase 1; the engine runs autonomously without persistence.
    """

    supabase_url: Optional[str] = Field(default=None)
    supabase_anon_key: Optional[str] = Field(default=None)
    supabase_service_role_key: Optional[str] = Field(default=None)

    @property
    def is_configured(self) -> bool:
        """Check whether minimum persistence credentials exist."""
        return bool(self.supabase_url and (self.supabase_anon_key or self.supabase_service_role_key))


class AIConfig(BaseModel):
    """Configuration boundary for optional AI language/reasoning providers (e.g. Gemini).

    The engine runs without any AI provider configured in Phase 1.
    """

    gemini_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default="gemini-2.5-pro")
    enabled: bool = Field(default=False)

    @property
    def is_configured(self) -> bool:
        """Check whether AI integration is enabled and configured."""
        return bool(self.enabled and self.gemini_api_key)


class Settings(BaseModel):
    """Root configuration object containing all engine subsystem settings."""

    engine: EngineRuntimeSettings = Field(default_factory=EngineRuntimeSettings)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """Load and validate configuration from environment variables or custom mapping.

    Secrets must only be provided through environment variables.
    """
    source = os.environ if env is None else env

    try:
        env_raw = source.get("ENGINE_ENV", EnvironmentType.DEVELOPMENT.value).lower()
        try:
            environment = EnvironmentType(env_raw)
        except ValueError as err:
            raise ConfigurationError(
                f"Invalid ENGINE_ENV '{env_raw}'. Must be one of {[e.value for e in EnvironmentType]}.",
                details={"value": env_raw},
            ) from err

        log_level_raw = source.get("ENGINE_LOG_LEVEL", LogLevel.INFO.value).upper()
        try:
            log_level = LogLevel(log_level_raw)
        except ValueError as err:
            raise ConfigurationError(
                f"Invalid ENGINE_LOG_LEVEL '{log_level_raw}'. Must be one of {[l.value for l in LogLevel]}.",
                details={"value": log_level_raw},
            ) from err

        engine_version = source.get("ENGINE_VERSION", __version__)

        engine_settings = EngineRuntimeSettings(
            environment=environment,
            log_level=log_level,
            engine_version=engine_version,
        )

        db_config = DatabaseConfig(
            supabase_url=source.get("SUPABASE_URL"),
            supabase_anon_key=source.get("SUPABASE_ANON_KEY"),
            supabase_service_role_key=source.get("SUPABASE_SERVICE_ROLE_KEY"),
        )

        ai_enabled = source.get("GEMINI_ENABLED", "false").lower() in ("true", "1", "yes")
        ai_config = AIConfig(
            gemini_api_key=source.get("GEMINI_API_KEY"),
            gemini_model=source.get("GEMINI_MODEL", "gemini-2.5-pro"),
            enabled=ai_enabled,
        )

        return Settings(
            engine=engine_settings,
            database=db_config,
            ai=ai_config,
        )
    except ConfigurationError:
        raise
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to load engine configuration: {exc}",
            details={"error": str(exc)},
        ) from exc
