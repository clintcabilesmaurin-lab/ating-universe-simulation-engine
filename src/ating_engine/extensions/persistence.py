"""Extension points and architectural ports for durable persistence (Supabase).

These interfaces define the boundary between the in-memory Python simulation authority
and external persistent stores without binding the engine to any specific database driver.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ating_engine.contracts.operation import SimulationOperation
from ating_engine.contracts.state import WorldState


class StatePersistencePort(ABC):
    """Abstract persistence port for reading and writing WorldState snapshots."""

    @abstractmethod
    def save_state_snapshot(self, state: WorldState) -> None:
        """Persist a new versioned world state snapshot."""
        pass

    @abstractmethod
    def load_latest_state(self, world_id: str) -> Optional[WorldState]:
        """Fetch the most recent committed state snapshot for a world."""
        pass

    @abstractmethod
    def load_state_version(self, world_id: str, version: int) -> Optional[WorldState]:
        """Fetch a specific historical state snapshot for a world."""
        pass


class OperationAuditPort(ABC):
    """Abstract persistence port for recording simulation operations and audit logs."""

    @abstractmethod
    def record_operation(self, operation: SimulationOperation) -> None:
        """Persist an audit log of a SimulationOperation."""
        pass

    @abstractmethod
    def get_operation(self, operation_id: str) -> Optional[SimulationOperation]:
        """Retrieve an operation by unique operation ID."""
        pass


class InMemoryEphemeralPersistence(StatePersistencePort, OperationAuditPort):
    """Ephemeral, in-memory reference implementation for tests and offline execution.

    Explicitly NOT a production database.
    """

    def __init__(self) -> None:
        self._states: Dict[str, Dict[int, WorldState]] = {}
        self._operations: Dict[str, SimulationOperation] = {}

    def save_state_snapshot(self, state: WorldState) -> None:
        world_states = self._states.setdefault(state.world.world_id, {})
        world_states[state.state_version] = state

    def load_latest_state(self, world_id: str) -> Optional[WorldState]:
        world_states = self._states.get(world_id)
        if not world_states:
            return None
        latest_ver = max(world_states.keys())
        return world_states[latest_ver]

    def load_state_version(self, world_id: str, version: int) -> Optional[WorldState]:
        world_states = self._states.get(world_id, {})
        return world_states.get(version)

    def record_operation(self, operation: SimulationOperation) -> None:
        self._operations[operation.operation_id] = operation

    def get_operation(self, operation_id: str) -> Optional[SimulationOperation]:
        return self._operations.get(operation_id)
