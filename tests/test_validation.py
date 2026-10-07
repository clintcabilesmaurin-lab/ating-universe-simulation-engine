"""Tests for raw JSON schema validation and rejection of invalid data."""

import pytest
from ating_engine.errors.base import ValidationError
from ating_engine.validation.validator import SchemaValidator, validate_raw_json


@pytest.fixture
def validator():
    return SchemaValidator(version="v1")


def test_valid_agent_raw_json(validator):
    raw_agent = {
        "identity": {
            "agent_id": "agent-001",
            "name": "Clint",
            "archetype": "Architect",
        },
        "status": "ACTIVE",
        "state": {
            "location": "Workshop",
            "mood": "focused",
            "energy": 0.85,
        },
    }
    # Should not raise
    validator.validate(raw_agent, "agent")


def test_invalid_agent_missing_required_identity(validator):
    raw_agent = {
        "status": "ACTIVE",
    }
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(raw_agent, "agent")
    assert "identity" in str(exc_info.value)


def test_invalid_agent_wrong_type(validator):
    raw_agent = {
        "identity": {
            "agent_id": 12345,  # should be string
            "name": "Clint",
        }
    }
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(raw_agent, "agent")
    assert "validation failed" in str(exc_info.value).lower()


def test_invalid_agent_disallowed_status_enum(validator):
    raw_agent = {
        "identity": {"agent_id": "a-1", "name": "Test"},
        "status": "SUPER_ACTIVE",  # not in enum
    }
    with pytest.raises(ValidationError):
        validator.validate(raw_agent, "agent")


def test_valid_operation_raw_json(validator):
    raw_op = {
        "operation_id": "op-100",
        "world_id": "world-prime",
        "engine_version": "0.1.0",
        "schema_version": "1.0.0",
        "previous_logical_time": "2026-10-06T12:00:00Z",
        "target_logical_time": "2026-10-06T12:30:00Z",
        "previous_state_version": 4,
        "status": "PENDING",
        "created_at": "2026-10-06T12:00:01Z",
    }
    validator.validate(raw_op, "operation")


def test_invalid_operation_negative_previous_state_version(validator):
    raw_op = {
        "operation_id": "op-100",
        "world_id": "world-prime",
        "engine_version": "0.1.0",
        "schema_version": "1.0.0",
        "previous_logical_time": "2026-10-06T12:00:00Z",
        "target_logical_time": "2026-10-06T12:30:00Z",
        "previous_state_version": -1,  # negative invalid
        "created_at": "2026-10-06T12:00:01Z",
    }
    with pytest.raises(ValidationError):
        validator.validate(raw_op, "operation")


def test_valid_state_with_nested_agent_references(validator):
    raw_state = {
        "world": {
            "world_id": "w-1",
            "name": "Main Simulation",
            "timeline_id": "prime",
        },
        "state_version": 1,
        "logical_time": "2026-10-06T12:00:00Z",
        "agents": {
            "ag-1": {
                "identity": {"agent_id": "ag-1", "name": "Maica"},
                "status": "ACTIVE",
            }
        },
        "active_events": [],
    }
    validate_raw_json(raw_state, "state")
