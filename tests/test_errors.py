"""Tests for domain error hierarchy, error codes, and serialization."""

import pytest
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


def test_base_engine_error_serialization():
    err = EngineError(
        message="Test engine error",
        code=ErrorCode.INTERNAL_ENGINE_ERROR,
        details={"hint": "check stack trace"},
        operation_id="op-123",
    )
    d = err.to_dict()
    assert d["error_code"] == "INTERNAL_ENGINE_ERROR"
    assert d["message"] == "Test engine error"
    assert d["details"] == {"hint": "check stack trace"}
    assert d["operation_id"] == "op-123"


def test_all_specialized_errors_inherit_from_engine_error():
    subclasses = [
        (ValidationError, ErrorCode.VALIDATION_FAILURE),
        (InvalidStateTransitionError, ErrorCode.INVALID_STATE_TRANSITION),
        (ConcurrencyConflictError, ErrorCode.CONCURRENCY_CONFLICT),
        (IdempotencyConflictError, ErrorCode.IDEMPOTENCY_CONFLICT),
        (UnavailableDependencyError, ErrorCode.UNAVAILABLE_DEPENDENCY),
        (AIProviderError, ErrorCode.AI_PROVIDER_FAILURE),
        (PersistenceError, ErrorCode.PERSISTENCE_FAILURE),
        (ConfigurationError, ErrorCode.CONFIGURATION_ERROR),
        (InternalEngineError, ErrorCode.INTERNAL_ENGINE_ERROR),
    ]

    for cls, expected_code in subclasses:
        instance = cls(message="Failure", operation_id="op-test")
        assert isinstance(instance, EngineError)
        assert instance.code == expected_code
        payload = instance.to_dict()
        assert payload["error_code"] == expected_code.value
        assert payload["operation_id"] == "op-test"
