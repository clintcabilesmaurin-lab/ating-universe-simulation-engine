"""Tests for SimulationOperation contract and invariant enforcement."""

import pytest
from ating_engine.contracts.operation import (
    OperationRequestMetadata,
    OperationResultMetadata,
    OperationStatus,
    SimulationOperation,
)
from ating_engine.errors.base import ValidationError
from ating_engine.validation.validator import validate_operation_invariants


def create_sample_operation(
    status: OperationStatus = OperationStatus.PENDING,
    prev_time: str = "2026-10-06T15:00:00+00:00",
    target_time: str = "2026-10-06T15:37:00+00:00",
    prev_version: int = 10,
    target_version: int = 11,
    idempotency_key: str = "idem-key-123",
) -> SimulationOperation:
    result = OperationResultMetadata()
    if status == OperationStatus.COMPLETED:
        result.target_state_version = target_version
        result.events_processed_count = 2
    elif status == OperationStatus.FAILED:
        result.error = {"code": "SIM_ERROR", "detail": "Simulation step failed"}

    return SimulationOperation(
        operation_id="op-test-1",
        world_id="world-ating-prime",
        previous_logical_time=prev_time,
        target_logical_time=target_time,
        previous_state_version=prev_version,
        status=status,
        request=OperationRequestMetadata(
            idempotency_key=idempotency_key,
            requested_by="web_app",
        ),
        result=result,
        created_at="2026-10-06T15:37:01+00:00",
    )


def test_valid_operation():
    op = create_sample_operation(status=OperationStatus.PENDING)
    validate_operation_invariants(op)
    assert op.operation_id == "op-test-1"
    assert op.request.idempotency_key == "idem-key-123"


def test_valid_completed_operation():
    op = create_sample_operation(status=OperationStatus.COMPLETED, prev_version=5, target_version=6)
    validate_operation_invariants(op)
    assert op.result.target_state_version == 6


def test_operation_causality_violation_raises():
    op = create_sample_operation(
        prev_time="2026-10-06T16:00:00+00:00",
        target_time="2026-10-06T15:00:00+00:00",  # backwards time
    )
    with pytest.raises(ValidationError) as exc:
        validate_operation_invariants(op)
    assert "Causality violation" in str(exc.value)


def test_completed_operation_without_target_state_version_raises():
    op = create_sample_operation(status=OperationStatus.COMPLETED)
    op.result.target_state_version = None
    with pytest.raises(ValidationError) as exc:
        validate_operation_invariants(op)
    assert "must specify target_state_version" in str(exc.value)


def test_completed_operation_non_incrementing_state_version_raises():
    op = create_sample_operation(
        status=OperationStatus.COMPLETED,
        prev_version=10,
        target_version=10,  # not strictly greater
    )
    with pytest.raises(ValidationError) as exc:
        validate_operation_invariants(op)
    assert "must be strictly greater" in str(exc.value)


def test_failed_operation_without_error_details_raises():
    op = create_sample_operation(status=OperationStatus.FAILED)
    op.result.error = None
    with pytest.raises(ValidationError) as exc:
        validate_operation_invariants(op)
    assert "must include structured error details" in str(exc.value)
