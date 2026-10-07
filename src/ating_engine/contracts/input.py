"""External input and message contract boundaries.

Maintains strict separation between external input/commands (from Vercel/users)
and authoritative internal simulation state.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InputKind(str, Enum):
    """Classification of external inputs entering the engine boundary."""

    USER_MESSAGE = "USER_MESSAGE"
    COMMAND = "COMMAND"
    INJECTION = "INJECTION"
    SYSTEM_TRIGGER = "SYSTEM_TRIGGER"


class InputProvenance(BaseModel):
    """Metadata regarding origin of the input."""

    sender_id: str = Field(description="Identifier of sender or external user.")
    origin_platform: str = Field(
        default="vercel_web_app",
        description="Origin source (e.g. 'vercel_web_app', 'cli', 'test_runner').",
    )
    received_at: str = Field(description="Physical UTC timestamp when input was received by boundary.")


class SimulationInput(BaseModel):
    """Contract for external requests or messages directed into the simulation.

    External clients (Vercel, CLI) submit this contract. It does NOT mutate
    state directly; it enters the simulation engine to be processed within
    a SimulationOperation.
    """

    input_id: str = Field(description="Unique idempotency/input identifier.")
    world_id: str = Field(description="Target world or simulation timeline ID.")
    kind: InputKind = Field(description="Type of input.")
    content: str = Field(description="Textual payload or command statement.")
    target_agent_id: Optional[str] = Field(
        default=None,
        description="Optional recipient agent ID if direct message or action.",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured arguments or contextual parameters.",
    )
    provenance: InputProvenance
    metadata: Dict[str, Any] = Field(default_factory=dict)
