"""Validation engine combining JSON Schema enforcement and Python domain invariants."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import jsonschema
from jsonschema import Draft202012Validator

from ating_engine.contracts.agent import Agent
from ating_engine.contracts.event import SimulationEvent
from ating_engine.contracts.input import SimulationInput
from ating_engine.contracts.operation import OperationStatus, SimulationOperation
from ating_engine.contracts.state import WorldState
from ating_engine.errors.base import ValidationError
from ating_engine.schemas.loader import build_schema_registry, load_schema


class SchemaValidator:
    """Validates raw dictionaries against versioned JSON schemas with cross-schema referencing."""

    def __init__(self, version: str = "v1") -> None:
        self.version = version
        self.registry = build_schema_registry(version)
        self._validators: Dict[str, Draft202012Validator] = {}

    def get_validator(self, schema_name: str) -> Draft202012Validator:
        """Get or initialize a cached Draft202012Validator for a schema."""
        norm_name = schema_name.replace(".schema", "")
        if norm_name not in self._validators:
            schema = load_schema(norm_name, self.version)
            self._validators[norm_name] = Draft202012Validator(
                schema=schema,
                registry=self.registry,
            )
        return self._validators[norm_name]

    def validate(self, data: Dict[str, Any], schema_name: str) -> None:
        """Validate raw dictionary against schema. Raises ValidationError on failure."""
        validator = self.get_validator(schema_name)
        errors: List[str] = []
        for error in validator.iter_errors(data):
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"[{path}] {error.message}")

        if errors:
            raise ValidationError(
                message=f"JSON schema validation failed for '{schema_name}': {'; '.join(errors[:5])}",
                details={"errors": errors, "schema": schema_name},
            )


# Default module-level schema validator instance
_default_schema_validator = SchemaValidator()


def validate_raw_json(data: Dict[str, Any], schema_name: str, version: str = "v1") -> None:
    """Validate raw JSON/dict against a versioned JSON schema."""
    if version == "v1":
        _default_schema_validator.validate(data, schema_name)
    else:
        SchemaValidator(version=version).validate(data, schema_name)


def validate_operation_invariants(operation: SimulationOperation) -> None:
    """Enforce Python-level business rules and causality invariants on a SimulationOperation."""
    try:
        t_prev = datetime.fromisoformat(operation.previous_logical_time)
        t_target = datetime.fromisoformat(operation.target_logical_time)
    except Exception as exc:
        raise ValidationError(
            f"Invalid ISO-8601 logical timestamps in operation {operation.operation_id}: {exc}",
            operation_id=operation.operation_id,
        ) from exc

    if t_target < t_prev:
        raise ValidationError(
            f"Causality violation: target logical time ({operation.target_logical_time}) "
            f"cannot precede previous logical time ({operation.previous_logical_time}).",
            details={
                "previous_logical_time": operation.previous_logical_time,
                "target_logical_time": operation.target_logical_time,
            },
            operation_id=operation.operation_id,
        )

    if operation.previous_state_version < 0:
        raise ValidationError(
            f"previous_state_version must be non-negative: {operation.previous_state_version}",
            operation_id=operation.operation_id,
        )

    if operation.status == OperationStatus.COMPLETED:
        if operation.result.target_state_version is None:
            raise ValidationError(
                "Completed operation must specify target_state_version in result.",
                operation_id=operation.operation_id,
            )
        if operation.result.target_state_version <= operation.previous_state_version:
            raise ValidationError(
                f"Completed operation target_state_version ({operation.result.target_state_version}) "
                f"must be strictly greater than previous_state_version ({operation.previous_state_version}).",
                operation_id=operation.operation_id,
            )

    if operation.status == OperationStatus.FAILED:
        if operation.result.error is None:
            raise ValidationError(
                "Failed operation must include structured error details in result.",
                operation_id=operation.operation_id,
            )


def validate_state_invariants(state: WorldState) -> None:
    """Enforce Python-level invariants on a WorldState."""
    if state.state_version < 0:
        raise ValidationError(f"State version cannot be negative: {state.state_version}")

    try:
        datetime.fromisoformat(state.logical_time)
    except Exception as exc:
        raise ValidationError(f"Invalid logical_time format: {exc}") from exc

    for agent_id, agent in state.agents.items():
        if agent.identity.agent_id != agent_id:
            raise ValidationError(
                f"Agent key mismatch: dict key '{agent_id}' does not match agent.identity.agent_id '{agent.identity.agent_id}'.",
                details={"key": agent_id, "agent_id": agent.identity.agent_id},
            )

    for event in state.active_events:
        if event.world_id != state.world.world_id:
            raise ValidationError(
                f"World ID mismatch: active event '{event.event_id}' belongs to world '{event.world_id}', "
                f"expected world '{state.world.world_id}'.",
                details={"event_id": event.event_id, "event_world": event.world_id, "world_id": state.world.world_id},
            )


def validate_event_invariants(event: SimulationEvent) -> None:
    """Enforce domain invariants on a SimulationEvent."""
    try:
        datetime.fromisoformat(event.occurrence_time)
        datetime.fromisoformat(event.provenance.created_at)
    except Exception as exc:
        raise ValidationError(f"Invalid event timestamp: {exc}") from exc


def validate_input_invariants(inp: SimulationInput) -> None:
    """Enforce domain invariants on a SimulationInput."""
    try:
        datetime.fromisoformat(inp.provenance.received_at)
    except Exception as exc:
        raise ValidationError(f"Invalid input received_at timestamp: {exc}") from exc

    if not inp.content.strip():
        raise ValidationError("Simulation input content cannot be empty or whitespace-only.")


def validate_agent_invariants(agent: Agent) -> None:
    """Enforce domain invariants on an Agent."""
    if not agent.identity.agent_id.strip():
        raise ValidationError("Agent agent_id cannot be blank.")
    if not agent.identity.name.strip():
        raise ValidationError("Agent name cannot be blank.")
    if agent.state.energy is not None and not (0.0 <= agent.state.energy <= 1.0):
        raise ValidationError(
            f"Agent energy must be between 0.0 and 1.0, got {agent.state.energy}",
            details={"energy": agent.state.energy},
        )
