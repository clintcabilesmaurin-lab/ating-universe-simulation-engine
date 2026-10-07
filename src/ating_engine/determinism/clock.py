"""Deterministic clock provider for controlled simulation testing."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from ating_engine.clock.time_model import LogicalTime


class DeterministicClock:
    """Clock implementation whose logical time only changes via explicit advancement.

    Used in deterministic unit tests and reproducible scenario simulations.
    """

    def __init__(self, initial_time: Optional[LogicalTime] = None) -> None:
        if initial_time is None:
            self._current = LogicalTime(timestamp=datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc))
        else:
            self._current = initial_time

    def now(self) -> LogicalTime:
        """Return the current frozen/controlled logical time."""
        return self._current

    def set_time(self, new_time: LogicalTime) -> None:
        """Manually override current logical time."""
        self._current = new_time

    def advance(self, delta: timedelta) -> LogicalTime:
        """Advance logical time forward by a controlled timedelta."""
        self._current = self._current.advance_by(delta)
        return self._current
