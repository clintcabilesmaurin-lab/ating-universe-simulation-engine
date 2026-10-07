"""Tests for Event and Input contracts separating input from simulation state."""

import pytest
from ating_engine.contracts.event import (
    EventProvenance,
    EventStatus,
    EventType,
    SimulationEvent,
)
from ating_engine.contracts.input import (
    InputKind,
    InputProvenance,
    SimulationInput,
)
from ating_engine.errors.base import ValidationError
from ating_engine.validation.validator import (
    validate_event_invariants,
    validate_input_invariants,
)


def test_simulation_event_lifecycle():
    event = SimulationEvent(
        event_id="evt-100",
        world_id="world-ating",
        event_type=EventType.INTERACTION.value,
        occurrence_time="2026-10-06T15:30:00+00:00",
        status=EventStatus.PENDING,
        payload={"topic": "book_discussion"},
        provenance=EventProvenance(
            source_id="agent-clint",
            source_type="user_input",
            created_at="2026-10-06T15:29:50+00:00",
        ),
    )
    validate_event_invariants(event)
    assert event.status == EventStatus.PENDING
    assert event.payload["topic"] == "book_discussion"


def test_simulation_input_contract():
    inp = SimulationInput(
        input_id="in-500",
        world_id="world-ating",
        kind=InputKind.USER_MESSAGE,
        content="What are you currently reading?",
        target_agent_id="agent-maica",
        provenance=InputProvenance(
            sender_id="user-clint",
            origin_platform="vercel_web_app",
            received_at="2026-10-06T15:30:00+00:00",
        ),
    )
    validate_input_invariants(inp)
    assert inp.kind == InputKind.USER_MESSAGE
    assert inp.target_agent_id == "agent-maica"


def test_empty_input_content_rejected():
    inp = SimulationInput(
        input_id="in-501",
        world_id="world-ating",
        kind=InputKind.USER_MESSAGE,
        content="   ",
        provenance=InputProvenance(
            sender_id="user-clint",
            received_at="2026-10-06T15:30:00+00:00",
        ),
    )
    with pytest.raises(ValidationError) as exc:
        validate_input_invariants(inp)
    assert "cannot be empty" in str(exc.value)
