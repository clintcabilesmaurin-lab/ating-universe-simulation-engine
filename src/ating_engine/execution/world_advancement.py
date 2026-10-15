"""Pure logical-time advancement for the Ating Universe simulation."""

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass

from ating_engine.clock.time_model import LogicalTime
from ating_engine.contracts.agent import Agent, AgentIdentity, AgentState
from ating_engine.contracts.event import EventProvenance, EventStatus, SimulationEvent
from ating_engine.contracts.operation import OperationStatus, SimulationOperation
from ating_engine.contracts.state import EnvironmentState, WorldIdentity, WorldState
from ating_engine.errors.base import (
    ConcurrencyConflictError,
    EngineError,
    InternalEngineError,
    InvalidStateTransitionError,
    ValidationError,
)
from ating_engine.validation.validator import (
    validate_agent_invariants,
    validate_event_invariants,
    validate_operation_invariants,
    validate_raw_json,
    validate_state_invariants,
)


EventHandler = Callable[[WorldState, SimulationEvent], WorldState]


def _validate_raw_json_contract(
    data: dict,
    schema_name: str,
    operation_id: str,
) -> None:
    """Validate a serialized contract while retaining operation context."""
    try:
        validate_raw_json(data, schema_name)
    except ValidationError as exc:
        if exc.operation_id == operation_id:
            raise
        raise ValidationError(
            exc.message,
            details=exc.details,
            operation_id=operation_id,
        ) from exc


def _validate_state_domain_invariants(state: WorldState, operation_id: str) -> None:
    """Run domain invariants and attach the active operation to failures."""
    try:
        validate_state_invariants(state)
        for agent in state.agents.values():
            validate_agent_invariants(agent)
    except ValidationError as exc:
        if exc.operation_id == operation_id:
            raise
        raise ValidationError(
            exc.message,
            details=exc.details,
            operation_id=operation_id,
        ) from exc


def _normalize_and_validate_state(state: WorldState, operation_id: str) -> WorldState:
    """Return a canonical JSON-round-tripped state or a structured engine error."""
    try:
        if not isinstance(state, WorldState):
            raise ValidationError(
                "State must be a WorldState instance.",
                operation_id=operation_id,
            )
        if not isinstance(state.world, WorldIdentity) or not isinstance(
            state.environment, EnvironmentState
        ):
            raise ValidationError(
                "WorldState contains a malformed world or environment model.",
                operation_id=operation_id,
            )
        for agent_id, agent in state.agents.items():
            if not isinstance(agent, Agent) or not isinstance(
                agent.identity, AgentIdentity
            ) or not isinstance(agent.state, AgentState):
                raise ValidationError(
                    f"Agent {agent_id!r} is not a valid Agent model.",
                    operation_id=operation_id,
                    details={"agent_id": agent_id},
                )
        for event in state.active_events:
            if not isinstance(event, SimulationEvent) or not isinstance(
                event.provenance, EventProvenance
            ):
                raise ValidationError(
                    "WorldState contains a malformed active event.",
                    operation_id=operation_id,
                )

        serialized = state.model_dump(mode="json")
        # Re-parse after serialization: Pydantic models can be corrupted after
        # construction, and validation of the serialized contract alone won't catch it.
        normalized = WorldState.model_validate(serialized)
        normalized_json = normalized.model_dump(mode="json")
        _validate_raw_json_contract(normalized_json, "state", operation_id)
        _validate_state_domain_invariants(normalized, operation_id)
        return normalized
    except EngineError:
        raise
    except Exception as exc:
        raise ValidationError(
            f"Invalid state for operation {operation_id}: {exc}",
            operation_id=operation_id,
            details={"exception_type": type(exc).__name__},
        ) from exc


@dataclass(frozen=True)
class AdvanceWorldResult:
    """Result of one world-state transition and its processed events."""

    next_state: WorldState
    processed_events: tuple[SimulationEvent, ...]


def advance_world(
    previous_state: WorldState,
    operation: SimulationOperation,
    *,
    event_handlers: Mapping[str, EventHandler] | None = None,
) -> AdvanceWorldResult:
    """Advance one world snapshot across a bounded logical-time window.

    Execution is synchronous, deterministic, and offline. Registered event
    handlers are explicit dependencies, and all returned state is validated.
    """
    operation_id = operation.operation_id

    previous_state = _normalize_and_validate_state(previous_state, operation_id)
    try:
        operation_json = operation.model_dump(mode="json")
    except Exception as exc:
        raise ValidationError(
            f"Invalid operation for operation {operation_id}: {exc}",
            operation_id=operation_id,
            details={"exception_type": type(exc).__name__},
        ) from exc
    _validate_raw_json_contract(operation_json, "operation", operation_id)

    if operation.status not in (OperationStatus.PENDING, OperationStatus.RUNNING):
        raise InvalidStateTransitionError(
            f"Operation status {operation.status.value!r} is terminal and cannot be executed.",
            operation_id=operation_id,
            details={"status": operation.status.value},
        )

    if operation.request.inputs:
        raise ValidationError(
            "SimulationOperation.request.inputs are not supported by this execution phase.",
            operation_id=operation_id,
            details={"input_count": len(operation.request.inputs)},
        )

    try:
        state_time = LogicalTime.from_iso8601(previous_state.logical_time)
        operation_start = LogicalTime.from_iso8601(operation.previous_logical_time)
        target_time = LogicalTime.from_iso8601(operation.target_logical_time)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(
            f"Invalid logical timestamp for operation {operation_id}: {exc}",
            operation_id=operation_id,
        ) from exc

    if operation.world_id != previous_state.world.world_id:
        raise InvalidStateTransitionError(
            "Operation world_id does not match the supplied WorldState.",
            operation_id=operation_id,
            details={
                "operation_world_id": operation.world_id,
                "state_world_id": previous_state.world.world_id,
            },
        )

    if operation_start != state_time:
        raise InvalidStateTransitionError(
            "Operation previous_logical_time does not match the supplied WorldState logical_time.",
            operation_id=operation_id,
            details={
                "operation_previous_logical_time": operation.previous_logical_time,
                "state_logical_time": previous_state.logical_time,
            },
        )

    if operation.previous_state_version != previous_state.state_version:
        raise ConcurrencyConflictError(
            "Operation previous_state_version does not match the supplied WorldState.",
            operation_id=operation_id,
            details={
                "operation_previous_state_version": operation.previous_state_version,
                "state_version": previous_state.state_version,
            },
        )

    if target_time < operation_start:
        raise InvalidStateTransitionError(
            "Target logical time cannot precede previous logical time.",
            operation_id=operation_id,
            details={
                "previous_logical_time": operation.previous_logical_time,
                "target_logical_time": operation.target_logical_time,
            },
        )

    validate_operation_invariants(operation)
    _validate_state_domain_invariants(previous_state, operation_id)

    event_times: dict[str, LogicalTime] = {}
    seen_event_ids: set[str] = set()
    for event in previous_state.active_events:
        if not event.event_id.strip():
            raise ValidationError(
                "Active event_id cannot be blank.",
                operation_id=operation_id,
            )
        if event.event_id in seen_event_ids:
            raise ValidationError(
                f"Duplicate active event_id {event.event_id!r}.",
                operation_id=operation_id,
                details={"event_id": event.event_id},
            )
        seen_event_ids.add(event.event_id)

        try:
            validate_event_invariants(event)
            event_time = LogicalTime.from_iso8601(event.occurrence_time)
        except (ValidationError, TypeError, ValueError, OverflowError) as exc:
            raise ValidationError(
                f"Invalid active event {event.event_id!r} for operation {operation_id}: {exc}",
                operation_id=operation_id,
                details={"event_id": event.event_id},
            ) from exc

        event_times[event.event_id] = event_time
        if event.status == EventStatus.PENDING and event_time < state_time:
            raise InvalidStateTransitionError(
                f"Pending event {event.event_id!r} is stale and predates the current world time.",
                operation_id=operation_id,
                details={
                    "event_id": event.event_id,
                    "occurrence_time": event.occurrence_time,
                    "state_logical_time": previous_state.logical_time,
                },
            )

    due_events = sorted(
        (
            event
            for event in previous_state.active_events
            if event.status == EventStatus.PENDING
            and operation_start.timestamp <= event_times[event.event_id].timestamp
            <= target_time.timestamp
        ),
        key=lambda event: (event_times[event.event_id].timestamp, event.event_id),
    )

    handlers = event_handlers or {}
    for event in due_events:
        if not callable(handlers.get(event.event_type)):
            raise InvalidStateTransitionError(
                f"No registered handler for due event type {event.event_type!r}.",
                operation_id=operation_id,
                details={"event_id": event.event_id, "event_type": event.event_type},
            )

    working_state = deepcopy(previous_state)
    processed_events: list[SimulationEvent] = []
    processed_event_ids: set[str] = set()

    for event in due_events:
        event_time = event_times[event.event_id]
        handler_input = deepcopy(working_state)
        handler_input.logical_time = event_time.to_iso8601()
        protected_snapshot = deepcopy(handler_input)
        handler_event = deepcopy(event)

        handler = handlers[event.event_type]
        try:
            handler_result = handler(handler_input, handler_event)
        except EngineError as exc:
            if exc.operation_id is None:
                exc.operation_id = operation_id
            raise
        except Exception as exc:
            raise InternalEngineError(
                f"Unexpected error in handler for event {event.event_id!r}: {exc}",
                operation_id=operation_id,
                details={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "exception_type": type(exc).__name__,
                },
            ) from exc

        if not isinstance(handler_result, WorldState):
            raise ValidationError(
                f"Handler for event {event.event_id!r} must return a WorldState.",
                operation_id=operation_id,
                details={"event_id": event.event_id},
            )

        changed_envelope_fields: list[str] = []
        if handler_result.world != protected_snapshot.world:
            changed_envelope_fields.append("world")
        if handler_result.state_version != protected_snapshot.state_version:
            changed_envelope_fields.append("state_version")
        if handler_result.logical_time != protected_snapshot.logical_time:
            changed_envelope_fields.append("logical_time")
        if handler_result.active_events != protected_snapshot.active_events:
            changed_envelope_fields.append("active_events")
        if changed_envelope_fields:
            raise InvalidStateTransitionError(
                "Event handler attempted to modify engine-owned state envelope fields.",
                operation_id=operation_id,
                details={"event_id": event.event_id, "changed_fields": changed_envelope_fields},
            )

        handler_result = _normalize_and_validate_state(handler_result, operation_id)

        working_state = deepcopy(handler_result)
        # Reflect the successful dispatch in the working queue before a later
        # event handler observes this state snapshot.
        for queued_event in working_state.active_events:
            if queued_event.event_id == event.event_id:
                queued_event.status = EventStatus.PROCESSED
                break

        processed_event = deepcopy(event)
        processed_event.status = EventStatus.PROCESSED
        processed_events.append(processed_event)
        processed_event_ids.add(event.event_id)

    next_state = deepcopy(working_state)
    next_state.logical_time = target_time.to_iso8601()
    next_state.state_version = previous_state.state_version + 1
    next_state.active_events = [
        event
        for event in next_state.active_events
        if event.event_id not in processed_event_ids
    ]
    next_state = _normalize_and_validate_state(next_state, operation_id)

    return AdvanceWorldResult(
        next_state=next_state,
        processed_events=tuple(processed_events),
    )
