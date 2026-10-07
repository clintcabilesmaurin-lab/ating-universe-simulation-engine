"""Continuous logical world time representation with discrete step boundaries."""

from datetime import datetime, timezone, timedelta
from typing import Any, Union
from pydantic import BaseModel, Field, field_validator


class LogicalTime(BaseModel):
    """Represents a discrete evaluation point along a continuous logical world timeline.

    In the Ating Universe:
    - Logical time is continuous (not bound to discrete 1-second ticks).
    - Engine evaluations occur discretely across time windows.
    - All logical timestamps must be timezone-aware UTC.
    """

    timestamp: datetime = Field(
        description="Timezone-aware UTC datetime of the logical world instant."
    )

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, val: datetime) -> datetime:
        """Enforce UTC timezone awareness."""
        if val.tzinfo is None:
            # Assume UTC if naive
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)

    @classmethod
    def from_iso8601(cls, value: str) -> "LogicalTime":
        """Parse an ISO-8601 string into LogicalTime."""
        dt = datetime.fromisoformat(value)
        return cls(timestamp=dt)

    def to_iso8601(self) -> str:
        """Format as ISO-8601 UTC string."""
        return self.timestamp.isoformat()

    def advance_by(self, delta: timedelta) -> "LogicalTime":
        """Advance time by a specified timedelta."""
        if delta < timedelta(0):
            raise ValueError("Logical time cannot advance into the past.")
        return LogicalTime(timestamp=self.timestamp + delta)

    def diff(self, other: "LogicalTime") -> timedelta:
        """Compute the duration between this logical time and another."""
        return self.timestamp - other.timestamp

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, LogicalTime):
            return self.timestamp < other.timestamp
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, LogicalTime):
            return self.timestamp <= other.timestamp
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, LogicalTime):
            return self.timestamp > other.timestamp
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, LogicalTime):
            return self.timestamp >= other.timestamp
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LogicalTime):
            return self.timestamp == other.timestamp
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.timestamp)

    def __str__(self) -> str:
        return self.to_iso8601()


class TimeWindow(BaseModel):
    """Specification of an operational time-advancement window [start, target]."""

    start_time: LogicalTime
    target_time: LogicalTime

    @property
    def duration(self) -> timedelta:
        """Duration of this simulation time window."""
        return self.target_time.diff(self.start_time)

    @property
    def duration_seconds(self) -> float:
        """Duration of this window in seconds."""
        return self.duration.total_seconds()

    def validate_causality(self) -> None:
        """Verify that target time does not precede start time."""
        if self.target_time < self.start_time:
            raise ValueError(
                f"Target time ({self.target_time}) cannot precede start time ({self.start_time})."
            )
