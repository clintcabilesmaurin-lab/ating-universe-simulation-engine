"""Agent domain contract and interface boundaries for the Ating Universe."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Lifecycle status of a simulation agent."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DORMANT = "DORMANT"
    ARCHIVED = "ARCHIVED"


class AgentIdentity(BaseModel):
    """Immutable identity boundary for an agent."""

    agent_id: str = Field(description="Unique identifier for the agent (e.g. uuid or slug).")
    name: str = Field(description="Display or narrative name of the agent.")
    archetype: Optional[str] = Field(default=None, description="Optional archetype reference.")


class AgentScheduleReference(BaseModel):
    """Reference boundary for future schedule/routine resolution."""

    schedule_id: Optional[str] = Field(default=None, description="External schedule identifier.")
    current_activity: Optional[str] = Field(default=None, description="Current planned activity.")
    activity_started_at: Optional[str] = Field(default=None, description="ISO-8601 start timestamp.")
    activity_ends_at: Optional[str] = Field(default=None, description="ISO-8601 expected end timestamp.")


class AgentTraitsReference(BaseModel):
    """Reference boundary for personality and behavioral traits (Phase 3/4 integration)."""

    trait_profile_id: Optional[str] = Field(default=None, description="Identifier for trait profile.")
    version: Optional[str] = Field(default=None, description="Version of the trait profile.")
    descriptors: List[str] = Field(default_factory=list, description="Descriptive trait tags.")


class AgentNeedsReference(BaseModel):
    """Reference boundary for internal motivation and psychological/physiological needs."""

    metrics: Dict[str, float] = Field(default_factory=dict, description="Named need levels.")
    last_evaluated_at: Optional[str] = Field(default=None, description="ISO-8601 last evaluation time.")


class AgentRelationshipsReference(BaseModel):
    """Reference boundary for social graph ties to other agents."""

    ties: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of target agent IDs to relational metadata.",
    )


class AgentMemoryReference(BaseModel):
    """Reference boundary for memory system integration (future Phase 3 NotebookLM / vector store)."""

    memory_cluster_id: Optional[str] = Field(default=None, description="Cluster or namespace ID.")
    recent_memory_ids: List[str] = Field(default_factory=list, description="IDs of active/recent memories.")
    memory_count: int = Field(default=0, description="Total committed memories referenced.")


class AgentState(BaseModel):
    """Transient state attributes of an agent at a given logical time."""

    location: Optional[str] = Field(default=None, description="World location/room.")
    mood: Optional[str] = Field(default=None, description="Current emotional valence.")
    energy: Optional[float] = Field(default=None, description="Normalized energy level [0.0 - 1.0].")
    custom_attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible agent-specific attributes.",
    )


class Agent(BaseModel):
    """Comprehensive Agent Contract representing an entity within the simulation."""

    identity: AgentIdentity
    status: AgentStatus = Field(default=AgentStatus.ACTIVE)
    state: AgentState = Field(default_factory=AgentState)
    schedule: AgentScheduleReference = Field(default_factory=AgentScheduleReference)
    traits: AgentTraitsReference = Field(default_factory=AgentTraitsReference)
    needs: AgentNeedsReference = Field(default_factory=AgentNeedsReference)
    relationships: AgentRelationshipsReference = Field(default_factory=AgentRelationshipsReference)
    memory: AgentMemoryReference = Field(default_factory=AgentMemoryReference)
    metadata: Dict[str, Any] = Field(default_factory=dict)
