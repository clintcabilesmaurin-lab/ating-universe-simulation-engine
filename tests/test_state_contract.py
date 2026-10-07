"""Tests for WorldState contract versioning and invariants."""

import pytest
from ating_engine.contracts.agent import Agent, AgentIdentity
from ating_engine.contracts.event import EventProvenance, SimulationEvent
from ating_engine.contracts.state import EnvironmentState, WorldIdentity, WorldState
from ating_engine.errors.base import ValidationError
from ating_engine.validation.validator import validate_state_invariants


def build_sample_world_state(
    world_id: str = "world-ating",
    state_version: int = 1,
    logical_time: str = "2026-10-06T15:00:00+00:00",
) -> WorldState:
    agent = Agent(
        identity=AgentIdentity(agent_id="agent-clint", name="Clint"),
    )
    event = SimulationEvent(
        event_id="evt-1",
        world_id=world_id,
        event_type="SYSTEM",
        occurrence_time=logical_time,
        provenance=EventProvenance(
            source_id="system",
            source_type="schedule",
            created_at="2026-10-06T15:00:00+00:00",
        ),
    )
    return WorldState(
        world=WorldIdentity(world_id=world_id, name="Ating Main"),
        state_version=state_version,
        logical_time=logical_time,
        agents={"agent-clint": agent},
        active_events=[event],
        environment=EnvironmentState(weather="clear", ambient_context="quiet evening"),
    )


def test_valid_world_state():
    state = build_sample_world_state()
    validate_state_invariants(state)
    assert state.state_version == 1
    assert "agent-clint" in state.agents
    assert len(state.active_events) == 1


def test_state_agent_key_mismatch_raises():
    state = build_sample_world_state()
    # Miskey the agent in the dictionary
    state.agents = {"mismatched-key": state.agents["agent-clint"]}
    with pytest.raises(ValidationError) as exc:
        validate_state_invariants(state)
    assert "Agent key mismatch" in str(exc.value)


def test_state_event_world_id_mismatch_raises():
    state = build_sample_world_state()
    # Modify event to belong to different world
    state.active_events[0].world_id = "foreign-world"
    with pytest.raises(ValidationError) as exc:
        validate_state_invariants(state)
    assert "World ID mismatch" in str(exc.value)


def test_negative_state_version_rejected_by_pydantic():
    with pytest.raises(Exception):
        build_sample_world_state(state_version=-5)
