"""Simulation Operation foundational contract.

Establishes the boundary for discrete execution units that advance the simulation,
supporting idempotency, optimistic concurrency, retries, auditability,
and reproducibility.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ating_engine.contracts.input import SimulationInput
from ating_engine.version import SCHEMA_VERSION, __version__


class OperationStatus(str, Enum):
    """Lifecycle status of a Simulation Operation."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class OperationRequestMetadata(BaseModel):
    """Metadata regarding the trigger and inputs for the operation."""

    idempotency_key: Optional[str] = Field(
        default=None,
        description="Caller-provided key for deduplication and idempotency.",
    )
    requested_by: str = Field(
        default="system",
        description="Source identity triggering this operation (e.g. 'web_app', 'cli', 'cron').",
    )
    inputs: List[SimulationInput] = Field(
        default_factory=list,
        description="Optional list of external inputs/messages processed in this operation.",
    )
    request_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supplementary execution flags or constraints.",
    )


class OperationResultMetadata(BaseModel):
    """Output summary and audit diagnostics for completed or failed operations."""

    target_state_version: Optional[int] = Field(
        default=None,
        description="Committed state version resulting from this operation.",
    )
    events_generated_count: int = Field(
        default=0,
        description="Number of newly generated events during step execution.",
    )
    events_processed_count: int = Field(
        default=0,
        description="Number of events resolved/processed during this operation.",
    )
    execution_duration_ms: Optional[float] = Field(
        default=None,
        description="Wall-clock execution duration in milliseconds.",
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured error details if operation status is FAILED.",
    )
    diagnostics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible performance or diagnostic indicators.",
    )


class SimulationOperation(BaseModel):
    """Foundational contract representing a discrete computational operation.

    Encapsulates all metadata required to advance the universe from
    `previous_logical_time` to `target_logical_time` under optimistic concurrency.
    """

    operation_id: str = Field(description="Globally unique UUID for the simulation operation.")
    world_id: str = Field(description="Target world or simulation timeline ID.")
    engine_version: str = Field(
        default=__version__,
        description="Engine software version executing the operation.",
    )
    schema_version: str = Field(
        default=SCHEMA_VERSION,
        description="Schema contract version.",
    )
    previous_logical_time: str = Field(
        description="ISO-8601 UTC timestamp of logical time prior to operation execution.",
    )
    target_logical_time: str = Field(
        description="ISO-8601 UTC timestamp of desired logical time after operation execution.",
    )
    previous_state_version: int = Field(
        ge=0,
        description="State version required prior to execution for optimistic concurrency.",
    )
    status: OperationStatus = Field(
        default=OperationStatus.PENDING,
        description="Current execution lifecycle status.",
    )
    request: OperationRequestMetadata = Field(
        default_factory=OperationRequestMetadata,
        description="Request parameters and external inputs.",
    )
    result: OperationResultMetadata = Field(
        default_factory=OperationResultMetadata,
        description="Resulting audit metrics and diagnostics.",
    )
    created_at: str = Field(
        description="Physical UTC timestamp when the operation record was instantiated.",
    )
    completed_at: Optional[str] = Field(
        default=None,
        description="Physical UTC timestamp when the operation concluded.",
    )
