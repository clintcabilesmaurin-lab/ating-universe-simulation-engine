"""Domain error exports for ating_engine."""

from ating_engine.errors.base import (
    AIProviderError,
    ConcurrencyConflictError,
    ConfigurationError,
    EngineError,
    ErrorCode,
    IdempotencyConflictError,
    InternalEngineError,
    InvalidStateTransitionError,
    PersistenceError,
    UnavailableDependencyError,
    ValidationError,
)

__all__ = [
    "AIProviderError",
    "ConcurrencyConflictError",
    "ConfigurationError",
    "EngineError",
    "ErrorCode",
    "IdempotencyConflictError",
    "InternalEngineError",
    "InvalidStateTransitionError",
    "PersistenceError",
    "UnavailableDependencyError",
    "ValidationError",
]
