"""Tests for Agent contract domain boundaries and references."""

import pytest
from ating_engine.contracts.agent import (
    Agent,
    AgentIdentity,
    AgentMemoryReference,
    AgentNeedsReference,
    AgentRelationshipsReference,
    AgentScheduleReference,
    AgentState,
    AgentStatus,
    AgentTraitsReference,
)
from ating_engine.errors.base import ValidationError
from ating_engine.validation.validator import validate_agent_invariants


def test_agent_contract_defaults():
    agent = Agent(
        identity=AgentIdentity(agent_id="clint-001", name="Clint"),
    )
    assert agent.status == AgentStatus.ACTIVE
    assert isinstance(agent.state, AgentState)
    assert isinstance(agent.schedule, AgentScheduleReference)
    assert isinstance(agent.traits, AgentTraitsReference)
    assert isinstance(agent.needs, AgentNeedsReference)
    assert isinstance(agent.relationships, AgentRelationshipsReference)
    assert isinstance(agent.memory, AgentMemoryReference)
    validate_agent_invariants(agent)


def test_agent_traits_and_memory_references():
    agent = Agent(
        identity=AgentIdentity(agent_id="maica-001", name="Maica", archetype="Researcher"),
        traits=AgentTraitsReference(
            trait_profile_id="tp-maica-v1",
            descriptors=["thoughtful", "perceptive"],
        ),
        memory=AgentMemoryReference(
            memory_cluster_id="cluster-dating-era",
            recent_memory_ids=["mem-1", "mem-2"],
            memory_count=2,
        ),
        state=AgentState(energy=0.9, mood="content", location="Library"),
    )
    validate_agent_invariants(agent)
    assert agent.traits.descriptors == ["thoughtful", "perceptive"]
    assert agent.memory.memory_count == 2


def test_agent_invalid_energy_level():
    agent = Agent(
        identity=AgentIdentity(agent_id="a-1", name="Test"),
        state=AgentState(energy=1.5),  # exceeds 1.0
    )
    with pytest.raises(ValidationError) as exc:
        validate_agent_invariants(agent)
    assert "Agent energy must be between 0.0 and 1.0" in str(exc.value)


def test_agent_empty_identity_name():
    agent = Agent(
        identity=AgentIdentity(agent_id="a-1", name="  "),
    )
    with pytest.raises(ValidationError) as exc:
        validate_agent_invariants(agent)
    assert "Agent name cannot be blank" in str(exc.value)
