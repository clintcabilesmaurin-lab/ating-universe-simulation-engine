"""Tests for extension points and architectural ports."""

from ating_engine.contracts.agent import Agent, AgentIdentity
from ating_engine.contracts.operation import (
    OperationRequestMetadata,
    OperationResultMetadata,
    OperationStatus,
    SimulationOperation,
)
from ating_engine.contracts.state import WorldIdentity, WorldState
from ating_engine.extensions.ai import MockAIProvider
from ating_engine.extensions.persistence import InMemoryEphemeralPersistence


def test_in_memory_persistence_adapter():
    repo = InMemoryEphemeralPersistence()
    state = WorldState(
        world=WorldIdentity(world_id="w-ephemeral", name="Ephemeral World"),
        state_version=1,
        logical_time="2026-10-06T15:00:00+00:00",
    )

    repo.save_state_snapshot(state)
    latest = repo.load_latest_state("w-ephemeral")
    assert latest is not None
    assert latest.state_version == 1

    op = SimulationOperation(
        operation_id="op-e-1",
        world_id="w-ephemeral",
        previous_logical_time="2026-10-06T15:00:00+00:00",
        target_logical_time="2026-10-06T15:30:00+00:00",
        previous_state_version=0,
        status=OperationStatus.COMPLETED,
        request=OperationRequestMetadata(),
        result=OperationResultMetadata(target_state_version=1),
        created_at="2026-10-06T15:30:01+00:00",
    )
    repo.record_operation(op)
    retrieved = repo.get_operation("op-e-1")
    assert retrieved is not None
    assert retrieved.operation_id == "op-e-1"


def test_mock_ai_provider():
    ai = MockAIProvider(fixed_dialogue="Checking in on the simulation.")
    agent_a = Agent(identity=AgentIdentity(agent_id="clint", name="Clint"))
    agent_b = Agent(identity=AgentIdentity(agent_id="maica", name="Maica"))

    reflection = ai.evaluate_agent_reflection(agent_a, context={})
    assert reflection["agent_id"] == "clint"
    assert "mood_shift" in reflection

    dialogue = ai.generate_dialogue_candidate(agent_a, agent_b, context={})
    assert dialogue == "[Clint -> Maica]: Checking in on the simulation."
