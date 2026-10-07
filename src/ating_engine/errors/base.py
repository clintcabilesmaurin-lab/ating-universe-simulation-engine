"""Domain error model for the Ating Universe Simulation Engine."""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """Categorized engine error codes."""

    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    UNAVAILABLE_DEPENDENCY = "UNAVAILABLE_DEPENDENCY"
    AI_PROVIDER_FAILURE = "AI_PROVIDER_FAILURE"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_ENGINE_ERROR = "INTERNAL_ENGINE_ERROR"


class EngineError(Exception):
    """Base exception for all simulation engine errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ENGINE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.operation_id = operation_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to a structured representation for logging and contract responses."""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
            "operation_id": self.operation_id,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(code={self.code.value!r}, "
            f"message={self.message!r}, details={self.details!r}, "
            f"operation_id={self.operation_id!r})"
        )


class ValidationError(EngineError):
    """Raised when data or contracts fail schema or domain validation."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_FAILURE,
            details=details,
            operation_id=operation_id,
        )


class InvalidStateTransitionError(EngineError):
    """Raised when a state transition violates causal or domain invariants."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_STATE_TRANSITION,
            details=details,
            operation_id=operation_id,
        )


class ConcurrencyConflictError(EngineError):
    """Raised when an optimistic concurrency check fails (e.g. state version mismatch)."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.CONCURRENCY_CONFLICT,
            details=details,
            operation_id=operation_id,
        )


class IdempotencyConflictError(EngineError):
    """Raised when an operation with an identical key is submitted with differing parameters."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.IDEMPOTENCY_CONFLICT,
            details=details,
            operation_id=operation_id,
        )


class UnavailableDependencyError(EngineError):
    """Raised when an external or optional subsystem is unavailable."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.UNAVAILABLE_DEPENDENCY,
            details=details,
            operation_id=operation_id,
        )


class AIProviderError(EngineError):
    """Raised when an optional AI provider encounters an error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.AI_PROVIDER_FAILURE,
            details=details,
            operation_id=operation_id,
        )


class PersistenceError(EngineError):
    """Raised when a persistent storage operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.PERSISTENCE_FAILURE,
            details=details,
            operation_id=operation_id,
        )


class ConfigurationError(EngineError):
    """Raised when engine or environment configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            operation_id=operation_id,
        )


class InternalEngineError(EngineError):
    """Raised for unexpected internal engine failures."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_ENGINE_ERROR,
            details=details,
            operation_id=operation_id,
        )
