"""Simulation event contract and interface boundaries."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    """Lifecycle status of a simulation event."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class EventType(str, Enum):
    """Standardized event category types."""

    SYSTEM = "SYSTEM"
    AGENT_ACTION = "AGENT_ACTION"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    INTERACTION = "INTERACTION"
    EXTERNAL_INPUT = "EXTERNAL_INPUT"


class EventProvenance(BaseModel):
    """Provenance tracking for event origination and auditability."""

    source_id: str = Field(description="Identity of the initiator (e.g. agent_id, input_id, or 'system').")
    source_type: str = Field(description="Type of source: 'user_input', 'schedule', 'rule', or 'external'.")
    correlation_id: Optional[str] = Field(default=None, description="Correlation key linking related causality chains.")
    created_at: str = Field(description="Physical UTC timestamp when this event record was generated.")


class SimulationEvent(BaseModel):
    """Minimal event representation for the Ating Universe Simulation Engine."""

    event_id: str = Field(description="Unique event identifier (UUID).")
    world_id: str = Field(description="Identity of the world/timeline this event affects.")
    event_type: str = Field(description="Event classification identifier.")
    occurrence_time: str = Field(description="ISO-8601 logical world time of scheduled or actual occurrence.")
    status: EventStatus = Field(default=EventStatus.PENDING)
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary domain event data.")
    provenance: EventProvenance
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata.")
