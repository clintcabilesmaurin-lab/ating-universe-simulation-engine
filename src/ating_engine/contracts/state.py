"""Minimal versioned state contract for the Ating Universe."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ating_engine.contracts.agent import Agent
from ating_engine.contracts.event import SimulationEvent


class WorldIdentity(BaseModel):
    """Identity boundary for a simulated world instance."""

    world_id: str = Field(description="Unique identifier for the world/session.")
    name: str = Field(description="Descriptive name of the simulated world.")
    timeline_id: str = Field(default="prime", description="Branch or timeline identifier.")


class EnvironmentState(BaseModel):
    """World-level environment attributes."""

    weather: Optional[str] = Field(default=None, description="Current ambient weather/conditions.")
    ambient_context: Optional[str] = Field(default=None, description="General narrative or environment summary.")
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible environment state variables.",
    )


class WorldState(BaseModel):
    """Minimal versioned state representation of the simulated universe.

    Guarantees:
    - State version is strictly non-negative and increments with every transition.
    - Logical time is continuous and tracked accurately.
    - Agents and active events are keyed and contained within domain boundaries.
    """

    world: WorldIdentity
    state_version: int = Field(
        ge=0,
        description="Monotonically increasing integer version for optimistic concurrency.",
    )
    logical_time: str = Field(
        description="ISO-8601 UTC timestamp of current continuous logical world time.",
    )
    agents: Dict[str, Agent] = Field(
        default_factory=dict,
        description="Dictionary mapping agent_id to Agent contract representations.",
    )
    active_events: List[SimulationEvent] = Field(
        default_factory=list,
        description="Active or pending simulation events in this state snapshot.",
    )
    environment: EnvironmentState = Field(
        default_factory=EnvironmentState,
        description="Global environment properties.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Audit and engine metadata.",
    )
