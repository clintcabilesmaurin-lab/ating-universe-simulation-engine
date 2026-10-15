"""Tests for the first deterministic world-advancement operation."""

from datetime import datetime, timezone

import pytest

from ating_engine.contracts.agent import Agent, AgentIdentity, AgentState
from ating_engine.contracts.event import EventProvenance, EventStatus, EventType, SimulationEvent
from ating_engine.contracts.input import InputKind, InputProvenance, SimulationInput
from ating_engine.contracts.operation import (
    OperationRequestMetadata,
    OperationStatus,
    SimulationOperation,
)
from ating_engine.contracts.state import EnvironmentState, WorldIdentity, WorldState
from ating_engine.errors.base import (
    ConcurrencyConflictError,
    InternalEngineError,
    InvalidStateTransitionError,
    ValidationError,
)
from ating_engine.execution import AdvanceWorldResult, advance_world


BASE_TIME = "2026-10-06T15:00:00+00:00"
TARGET_TIME = "2026-10-06T15:37:00+00:00"


def make_state(
    *,
    world_id: str = "world-1",
    state_version: int = 7,
    logical_time: str = BASE_TIME,
) -> WorldState:
    return WorldState(
        world=WorldIdentity(world_id=world_id, name="Ating World"),
        state_version=state_version,
        logical_time=logical_time,
        agents={},
        active_events=[],
        environment=EnvironmentState(),
        metadata={},
    )


def make_operation(
    *,
    world_id: str = "world-1",
    previous_logical_time: str = BASE_TIME,
    target_logical_time: str = TARGET_TIME,
    previous_state_version: int = 7,
    status: OperationStatus = OperationStatus.PENDING,
    inputs: list[SimulationInput] | None = None,
) -> SimulationOperation:
    return SimulationOperation(
        operation_id="op-1",
        world_id=world_id,
        previous_logical_time=previous_logical_time,
        target_logical_time=target_logical_time,
        previous_state_version=previous_state_version,
        status=status,
        request=OperationRequestMetadata(inputs=inputs or []),
        created_at=BASE_TIME,
    )


def make_input() -> SimulationInput:
    return SimulationInput(
        input_id="input-1",
        world_id="world-1",
        kind=InputKind.USER_MESSAGE,
        content="Hello, world.",
        provenance=InputProvenance(
            sender_id="user-clint",
            received_at=BASE_TIME,
        ),
    )


def test_no_event_advance_moves_time_and_increments_state_version_once():
    state = make_state()
    operation = make_operation()

    result = advance_world(state, operation)

    assert isinstance(result, AdvanceWorldResult)
    assert result.next_state.logical_time == TARGET_TIME
    assert result.next_state.state_version == state.state_version + 1
    assert result.next_state.active_events == []
    assert result.processed_events == ()


def test_advance_does_not_mutate_input_state_or_operation():
    state = make_state()
    operation = make_operation()
    original_state = state.model_copy(deep=True)
    original_operation = operation.model_copy(deep=True)

    advance_world(state, operation)

    assert state == original_state
    assert operation == original_operation


def test_world_id_mismatch_is_rejected():
    state = make_state()

    with pytest.raises(InvalidStateTransitionError):
        advance_world(state, make_operation(world_id="world-other"))


def test_previous_logical_time_mismatch_is_rejected():
    state = make_state()

    with pytest.raises(InvalidStateTransitionError):
        advance_world(
            state,
            make_operation(
                previous_logical_time="2026-10-06T15:01:00+00:00",
                target_logical_time=TARGET_TIME,
            ),
        )


def test_state_version_mismatch_is_a_concurrency_conflict():
    state = make_state(state_version=7)

    with pytest.raises(ConcurrencyConflictError):
        advance_world(state, make_operation(previous_state_version=6))


def test_backward_time_is_rejected_as_an_invalid_transition():
    state = make_state()

    with pytest.raises(InvalidStateTransitionError):
        advance_world(
            state,
            make_operation(
                target_logical_time="2026-10-06T14:59:00+00:00",
            ),
        )


def test_non_empty_operation_inputs_are_rejected():
    state = make_state()

    with pytest.raises(ValidationError):
        advance_world(state, make_operation(inputs=[make_input()]))


def test_terminal_operation_status_is_rejected():
    state = make_state()

    with pytest.raises(InvalidStateTransitionError):
        advance_world(state, make_operation(status=OperationStatus.COMPLETED))


def test_equivalent_previous_time_instants_with_different_offsets_are_accepted():
    state = make_state(logical_time="2026-10-06T17:00:00+02:00")
    operation = make_operation(
        previous_logical_time="2026-10-06T15:00:00+00:00",
        target_logical_time="2026-10-06T18:00:00+02:00",
    )

    result = advance_world(state, operation)

    assert result.next_state.logical_time == "2026-10-06T16:00:00+00:00"
    assert result.next_state.state_version == 8


def test_equal_time_operation_is_valid_and_increments_version_once():
    state = make_state()
    operation = make_operation(
        previous_logical_time=BASE_TIME,
        target_logical_time=BASE_TIME,
    )

    result = advance_world(state, operation)

    assert result.next_state.logical_time == BASE_TIME
    assert result.next_state.state_version == 8
    assert result.processed_events == ()



def make_event(
    event_id: str,
    occurrence_time: str,
    *,
    status: EventStatus = EventStatus.PENDING,
    world_id: str = "world-1",
) -> SimulationEvent:
    return SimulationEvent(
        event_id=event_id,
        world_id=world_id,
        event_type=EventType.SYSTEM.value,
        occurrence_time=occurrence_time,
        status=status,
        provenance=EventProvenance(
            source_id="system",
            source_type="schedule",
            created_at=BASE_TIME,
        ),
    )


def recording_handler(state: WorldState, event: SimulationEvent) -> WorldState:
    updated = state.model_copy(deep=True)
    updated.metadata["handled_ids"] = [
        *updated.metadata.get("handled_ids", []),
        event.event_id,
    ]
    return updated


def test_due_events_process_chronologically_with_ties_and_inclusive_boundaries():
    state = make_state()
    state.active_events = [
        make_event("event-b", "2026-10-06T15:05:00+00:00"),
        make_event("event-late", "2026-10-06T15:40:00+00:00"),
        make_event("event-a", "2026-10-06T15:05:00+00:00"),
        make_event("event-target", TARGET_TIME),
        make_event("event-start", BASE_TIME),
        make_event("event-middle", "2026-10-06T15:03:00+00:00"),
        make_event(
            "event-cancelled",
            "2026-10-06T15:04:00+00:00",
            status=EventStatus.CANCELLED,
        ),
    ]
    original_state = state.model_copy(deep=True)

    result = advance_world(
        state,
        make_operation(),
        event_handlers={EventType.SYSTEM.value: recording_handler},
    )

    expected_ids = [
        "event-start",
        "event-middle",
        "event-a",
        "event-b",
        "event-target",
    ]
    assert [event.event_id for event in result.processed_events] == expected_ids
    assert all(event.status == EventStatus.PROCESSED for event in result.processed_events)
    assert result.next_state.metadata["handled_ids"] == expected_ids
    assert [event.event_id for event in result.next_state.active_events] == [
        "event-late",
        "event-cancelled",
    ]
    assert state == original_state


def test_same_time_event_order_is_independent_of_input_list_order():
    state_ab = make_state()
    state_ab.active_events = [
        make_event("event-b", "2026-10-06T15:05:00+00:00"),
        make_event("event-a", "2026-10-06T15:05:00+00:00"),
    ]
    state_ba = make_state()
    state_ba.active_events = list(reversed(state_ab.active_events))
    operation = make_operation()

    result_ab = advance_world(
        state_ab,
        operation,
        event_handlers={EventType.SYSTEM.value: recording_handler},
    )
    result_ba = advance_world(
        state_ba,
        operation,
        event_handlers={EventType.SYSTEM.value: recording_handler},
    )

    assert [event.event_id for event in result_ab.processed_events] == [
        "event-a",
        "event-b",
    ]
    assert [event.event_id for event in result_ba.processed_events] == [
        "event-a",
        "event-b",
    ]
    assert result_ab.next_state.metadata == result_ba.next_state.metadata


def test_duplicate_active_event_ids_are_rejected():
    state = make_state()
    state.active_events = [
        make_event("duplicate", "2026-10-06T15:05:00+00:00"),
        make_event("duplicate", "2026-10-06T15:06:00+00:00"),
    ]

    with pytest.raises(ValidationError, match="duplicate"):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: recording_handler},
        )


def test_stale_pending_event_before_current_state_time_is_rejected():
    state = make_state()
    state.active_events = [
        make_event("event-stale", "2026-10-06T14:59:00+00:00"),
    ]

    with pytest.raises(InvalidStateTransitionError, match="older|before|stale"):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: recording_handler},
        )


def test_foreign_world_event_is_rejected():
    state = make_state()
    state.active_events = [
        make_event(
            "event-foreign",
            "2026-10-06T15:05:00+00:00",
            world_id="world-other",
        ),
    ]

    with pytest.raises(ValidationError, match="World ID mismatch"):
        advance_world(state, make_operation())


def test_invalid_active_event_timestamp_is_rejected_as_validation_error():
    state = make_state()
    state.active_events = [make_event("event-invalid-time", "not-a-timestamp")]

    with pytest.raises(ValidationError, match="timestamp"):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: recording_handler},
        )


def test_due_event_without_registered_handler_fails_closed():
    state = make_state()
    state.active_events = [
        make_event("event-unhandled", "2026-10-06T15:05:00+00:00"),
    ]
    original_state = state.model_copy(deep=True)

    with pytest.raises(InvalidStateTransitionError, match="handler"):
        advance_world(state, make_operation())

    assert state == original_state


def test_handler_cannot_change_engine_owned_state_envelope():
    state = make_state()
    state.active_events = [
        make_event("event-protected", "2026-10-06T15:05:00+00:00"),
    ]
    original_state = state.model_copy(deep=True)

    def illegal_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.state_version += 100
        return working_state

    with pytest.raises(InvalidStateTransitionError, match="engine-owned|envelope"):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: illegal_handler},
        )

    assert state == original_state


def make_state_with_agent(energy: float = 0.8) -> WorldState:
    state = make_state()
    state.agents["agent-1"] = Agent(
        identity=AgentIdentity(agent_id="agent-1", name="Agent One"),
        state=AgentState(energy=energy),
    )
    return state


def test_handler_can_update_agent_domain_state_without_mutating_original():
    state = make_state_with_agent(energy=0.8)
    state.active_events = [
        make_event("event-agent-update", "2026-10-06T15:05:00+00:00"),
    ]

    def update_energy(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.agents["agent-1"].state.energy = 0.6
        return working_state

    result = advance_world(
        state,
        make_operation(),
        event_handlers={EventType.SYSTEM.value: update_energy},
    )

    assert result.next_state.agents["agent-1"].state.energy == 0.6
    assert state.agents["agent-1"].state.energy == 0.8


def test_existing_engine_error_from_handler_is_preserved():
    state = make_state()
    state.active_events = [
        make_event("event-domain-error", "2026-10-06T15:05:00+00:00"),
    ]
    original_state = state.model_copy(deep=True)
    original_operation = make_operation()
    intentional_error = ValidationError("intentional handler validation error")

    def failing_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        raise intentional_error

    with pytest.raises(ValidationError) as caught:
        advance_world(
            state,
            original_operation,
            event_handlers={EventType.SYSTEM.value: failing_handler},
        )

    assert caught.value is intentional_error
    assert caught.value.operation_id == original_operation.operation_id
    assert state == original_state
    assert original_operation == make_operation()


def test_unexpected_handler_exception_is_wrapped_and_nested_input_is_unchanged():
    state = make_state_with_agent(energy=0.8)
    state.active_events = [
        make_event("event-crash", "2026-10-06T15:05:00+00:00"),
    ]
    original_state = state.model_copy(deep=True)
    operation = make_operation()
    original_operation = operation.model_copy(deep=True)

    def crashing_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.agents["agent-1"].state.energy = 0.1
        raise RuntimeError("synthetic handler crash")

    with pytest.raises(InternalEngineError, match="synthetic handler crash") as caught:
        advance_world(
            state,
            operation,
            event_handlers={EventType.SYSTEM.value: crashing_handler},
        )

    assert caught.value.operation_id == operation.operation_id
    assert state == original_state
    assert operation == original_operation
    assert state.agents["agent-1"].state.energy == 0.8


def test_handler_returning_non_world_state_is_rejected():
    state = make_state()
    state.active_events = [
        make_event("event-invalid-result", "2026-10-06T15:05:00+00:00"),
    ]
    original_state = state.model_copy(deep=True)

    def invalid_handler(working_state: WorldState, event: SimulationEvent):
        return {"not": "a WorldState"}

    with pytest.raises(ValidationError, match="must return a WorldState"):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: invalid_handler},
        )

    assert state == original_state


def test_handler_returning_invalid_agent_state_is_rejected():
    state = make_state_with_agent(energy=0.8)
    state.active_events = [
        make_event("event-invalid-agent", "2026-10-06T15:05:00+00:00"),
    ]
    original_state = state.model_copy(deep=True)

    def invalid_agent_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.agents["agent-1"].state.energy = 1.5
        return working_state

    with pytest.raises(ValidationError, match="energy"):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: invalid_agent_handler},
        )

    assert state == original_state


def test_repeating_same_operation_with_pure_handler_is_deterministic():
    state = make_state()
    state.active_events = [
        make_event("event-repeat-b", "2026-10-06T15:07:00+00:00"),
        make_event("event-repeat-a", "2026-10-06T15:07:00+00:00"),
    ]
    operation = make_operation()
    original_state = state.model_copy(deep=True)
    original_operation = operation.model_copy(deep=True)
    handlers = {EventType.SYSTEM.value: recording_handler}

    first_result = advance_world(state, operation, event_handlers=handlers)
    second_result = advance_world(state, operation, event_handlers=handlers)

    assert first_result.next_state == second_result.next_state
    assert first_result.processed_events == second_result.processed_events
    assert state == original_state
    assert operation == original_operation


def test_state_invariant_failure_includes_operation_id():
    state = make_state()
    state.agents["wrong-key"] = Agent(
        identity=AgentIdentity(agent_id="agent-1", name="Agent One"),
    )

    with pytest.raises(ValidationError, match="Agent key mismatch") as caught:
        advance_world(state, make_operation())

    assert caught.value.operation_id == "op-1"


def test_later_handlers_see_earlier_due_events_as_processed():
    state = make_state()
    state.active_events = [
        make_event("event-a", "2026-10-06T15:05:00+00:00"),
        make_event("event-b", "2026-10-06T15:07:00+00:00"),
    ]

    def inspect_queue(working_state: WorldState, event: SimulationEvent) -> WorldState:
        statuses = {
            queued.event_id: queued.status.value
            for queued in working_state.active_events
        }
        working_state.metadata.setdefault("observed_queue_statuses", {})[
            event.event_id
        ] = statuses
        return working_state

    result = advance_world(
        state,
        make_operation(),
        event_handlers={EventType.SYSTEM.value: inspect_queue},
    )

    assert result.next_state.metadata["observed_queue_statuses"]["event-a"][
        "event-a"
    ] == EventStatus.PENDING.value
    assert result.next_state.metadata["observed_queue_statuses"]["event-b"][
        "event-a"
    ] == EventStatus.PROCESSED.value
    assert [event.event_id for event in result.next_state.active_events] == []

@pytest.mark.parametrize("bad_value", [object()])
def test_non_json_serializable_handler_output_becomes_validation_error(bad_value):
    state = make_state()
    state.active_events = [make_event("event-bad-json", "2026-10-06T15:05:00+00:00")]
    operation = make_operation()

    def bad_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.metadata["bad_value"] = bad_value
        return working_state

    with pytest.raises(ValidationError) as caught:
        advance_world(state, operation, event_handlers={EventType.SYSTEM.value: bad_handler})

    assert caught.value.operation_id == operation.operation_id
    assert state.metadata == {}


def test_malformed_nested_agent_handler_output_becomes_validation_error():
    state = make_state_with_agent(energy=0.8)
    state.active_events = [make_event("event-bad-agent", "2026-10-06T15:05:00+00:00")]
    operation = make_operation()

    def bad_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.agents["agent-1"] = {"identity": "not-an-identity"}
        return working_state

    with pytest.raises(ValidationError) as caught:
        advance_world(state, operation, event_handlers={EventType.SYSTEM.value: bad_handler})

    assert caught.value.operation_id == operation.operation_id
    assert state.agents["agent-1"].state.energy == 0.8


def test_non_json_serializable_input_state_becomes_validation_error():
    state = make_state()
    state.metadata["bad_value"] = object()
    operation = make_operation()

    with pytest.raises(ValidationError) as caught:
        advance_world(state, operation)

    assert caught.value.operation_id == operation.operation_id
    assert state.state_version == 7


def test_handler_state_is_normalized_to_json_round_trip_representation():
    state = make_state()
    state.active_events = [make_event("event-normalize", "2026-10-06T15:05:00+00:00")]

    def normalize_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.metadata["pair"] = (1, 2)
        working_state.metadata["created"] = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return working_state

    result = advance_world(
        state, make_operation(), event_handlers={EventType.SYSTEM.value: normalize_handler}
    )

    assert result.next_state.metadata["pair"] == [1, 2]
    assert isinstance(result.next_state.metadata["created"], str)
    assert result.next_state.metadata["created"].startswith("2026-01-01T00:00:00")


def test_mixed_offset_events_are_selected_and_sorted_by_utc_instant():
    state = make_state()
    state.active_events = [
        make_event("event-offset", "2026-10-06T14:05:00-01:00"),
        make_event("event-z", "2026-10-06T15:04:00Z"),
    ]

    result = advance_world(
        state, make_operation(), event_handlers={EventType.SYSTEM.value: recording_handler}
    )

    assert [event.event_id for event in result.processed_events] == ["event-z", "event-offset"]


def test_naive_state_time_matches_aware_operation_time():
    state = make_state(logical_time="2026-10-06T15:00:00")
    operation = make_operation(previous_logical_time=BASE_TIME)

    result = advance_world(state, operation)

    assert result.next_state.logical_time == TARGET_TIME
    assert result.next_state.state_version == 8


def test_equal_time_operation_processes_event_at_that_instant():
    state = make_state()
    state.active_events = [make_event("event-now", BASE_TIME)]
    operation = make_operation(previous_logical_time=BASE_TIME, target_logical_time=BASE_TIME)

    result = advance_world(
        state, operation, event_handlers={EventType.SYSTEM.value: recording_handler}
    )

    assert [event.event_id for event in result.processed_events] == ["event-now"]
    assert result.next_state.active_events == []
    assert result.next_state.state_version == 8


@pytest.mark.parametrize("protected_field", ["world", "logical_time", "active_events", "state_version"])
def test_handler_cannot_change_any_engine_owned_envelope_field(protected_field):
    state = make_state()
    state.active_events = [make_event("event-envelope", "2026-10-06T15:05:00+00:00")]

    def illegal_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        if protected_field == "world":
            working_state.world.world_id = "world-other"
        elif protected_field == "logical_time":
            working_state.logical_time = "2026-10-06T15:06:00+00:00"
        elif protected_field == "active_events":
            working_state.active_events.append(make_event("event-injected", TARGET_TIME))
        else:
            working_state.state_version += 1
        return working_state

    with pytest.raises(InvalidStateTransitionError, match="engine-owned|envelope"):
        advance_world(
            state, make_operation(), event_handlers={EventType.SYSTEM.value: illegal_handler}
        )


def test_handler_receives_its_event_time_normalized_to_utc():
    state = make_state()
    state.active_events = [make_event("event-local-time", "2026-10-06T17:05:00+02:00")]
    observed = {}

    def inspect_time(working_state: WorldState, event: SimulationEvent) -> WorldState:
        observed[event.event_id] = working_state.logical_time
        return working_state

    advance_world(state, make_operation(), event_handlers={EventType.SYSTEM.value: inspect_time})

    assert observed["event-local-time"] == "2026-10-06T15:05:00+00:00"


def test_mutating_handler_event_does_not_mutate_input_or_processed_record():
    state = make_state()
    original_event = make_event("event-detached", "2026-10-06T15:05:00+00:00")
    original_event.payload = {"original": "value"}
    state.active_events = [original_event]

    def mutate_event(working_state: WorldState, event: SimulationEvent) -> WorldState:
        event.payload["original"] = "changed"
        event.occurrence_time = TARGET_TIME
        return working_state

    result = advance_world(
        state, make_operation(), event_handlers={EventType.SYSTEM.value: mutate_event}
    )

    assert state.active_events[0].payload == {"original": "value"}
    assert state.active_events[0].occurrence_time == "2026-10-06T15:05:00+00:00"
    assert result.processed_events[0].payload == {"original": "value"}
    assert result.processed_events[0].occurrence_time == "2026-10-06T15:05:00+00:00"


def test_failure_in_later_handler_leaves_original_state_and_operation_unchanged():
    state = make_state()
    state.active_events = [
        make_event("event-first", "2026-10-06T15:05:00+00:00"),
        make_event("event-second", "2026-10-06T15:07:00+00:00"),
    ]
    state.active_events[1].event_type = EventType.ENVIRONMENTAL.value
    operation = make_operation()
    original_state = state.model_copy(deep=True)
    original_operation = operation.model_copy(deep=True)

    def fail_second(working_state: WorldState, event: SimulationEvent) -> WorldState:
        if event.event_id == "event-second":
            raise RuntimeError("second handler failure")
        working_state.metadata["first_handled"] = True
        return working_state

    with pytest.raises(InternalEngineError):
        advance_world(
            state,
            operation,
            event_handlers={
                EventType.SYSTEM.value: fail_second,
                EventType.ENVIRONMENTAL.value: fail_second,
            },
        )

    assert state == original_state
    assert operation == original_operation


def test_unhandled_later_event_prevents_all_handler_invocations():
    state = make_state()
    first = make_event("event-first", "2026-10-06T15:05:00+00:00")
    later = make_event("event-later", "2026-10-06T15:07:00+00:00")
    later.event_type = "UNREGISTERED_TYPE"
    state.active_events = [first, later]
    invoked = []

    def record_invocation(working_state: WorldState, event: SimulationEvent) -> WorldState:
        invoked.append(event.event_id)
        return working_state

    with pytest.raises(InvalidStateTransitionError, match="handler"):
        advance_world(
            state, make_operation(), event_handlers={EventType.SYSTEM.value: record_invocation}
        )

    assert invoked == []



def test_invalid_input_state_is_rejected_before_any_handler_is_invoked():
    state = make_state()
    state.active_events = [make_event("event-invalid-input", "2026-10-06T15:05:00+00:00")]
    state.metadata["bad_value"] = object()
    invoked = []

    def record_invocation(working_state: WorldState, event: SimulationEvent) -> WorldState:
        invoked.append(event.event_id)
        return working_state

    with pytest.raises(ValidationError):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: record_invocation},
        )

    assert invoked == []


@pytest.mark.parametrize(
    "bad_value",
    [
        float("nan"),
        {1: "non-string key"},
        b"bytes are not JSON values",
        {"nested_unordered_values": {"alpha", "beta", "gamma"}},
    ],
    ids=["non-finite-float", "non-string-key", "bytes", "set"],
)
def test_handler_output_with_noncanonical_json_values_is_rejected(bad_value):
    state = make_state()
    state.active_events = [make_event("event-invalid-json-value", "2026-10-06T15:05:00+00:00")]
    operation = make_operation()
    original_state = state.model_copy(deep=True)

    def bad_value_handler(working_state: WorldState, event: SimulationEvent) -> WorldState:
        working_state.metadata["bad_value"] = bad_value
        return working_state

    with pytest.raises(ValidationError) as caught:
        advance_world(
            state,
            operation,
            event_handlers={EventType.SYSTEM.value: bad_value_handler},
        )

    assert caught.value.operation_id == operation.operation_id
    assert state == original_state


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("energy", True),
        ("energy", "0.5"),
        ("state_version", 7.0),
    ],
    ids=["boolean-as-float", "string-as-float", "float-as-integer"],
)
def test_handler_output_with_coercible_typed_values_is_rejected(field_name, bad_value):
    state = make_state_with_agent(energy=0.8)
    state.active_events = [make_event("event-coercible-value", "2026-10-06T15:05:00+00:00")]
    operation = make_operation()
    original_state = state.model_copy(deep=True)

    def corrupt_typed_value(working_state: WorldState, event: SimulationEvent) -> WorldState:
        if field_name == "energy":
            working_state.agents["agent-1"].state.energy = bad_value
        else:
            working_state.state_version = bad_value
        return working_state

    with pytest.raises(ValidationError):
        advance_world(
            state,
            operation,
            event_handlers={EventType.SYSTEM.value: corrupt_typed_value},
        )

    assert state == original_state


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("state_version", "7"),
        ("state_version", 7.0),
        ("energy", True),
    ],
    ids=["string-as-integer", "float-as-integer", "boolean-as-float"],
)
def test_input_state_with_coercible_typed_values_is_rejected_before_dispatch(field_name, bad_value):
    state = make_state_with_agent(energy=0.8) if field_name == "energy" else make_state()
    state.active_events = [make_event("event-invalid-typed-input", "2026-10-06T15:05:00+00:00")]
    if field_name == "state_version":
        state.state_version = bad_value
    else:
        state.agents["agent-1"].state.energy = bad_value
    invoked = []

    def record_invocation(working_state: WorldState, event: SimulationEvent) -> WorldState:
        invoked.append(event.event_id)
        return working_state

    with pytest.raises(ValidationError):
        advance_world(
            state,
            make_operation(),
            event_handlers={EventType.SYSTEM.value: record_invocation},
        )

    assert invoked == []