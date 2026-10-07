"""Tests for determinism utilities: controlled clock and seed controller."""

from datetime import datetime, timedelta, timezone
import pytest
from ating_engine.clock.time_model import LogicalTime, TimeWindow
from ating_engine.determinism.clock import DeterministicClock
from ating_engine.determinism.seed import SeedController


def test_deterministic_clock_advancement():
    t0 = LogicalTime(timestamp=datetime(2026, 10, 6, 15, 0, 0, tzinfo=timezone.utc))
    clock = DeterministicClock(initial_time=t0)

    assert clock.now().to_iso8601() == "2026-10-06T15:00:00+00:00"

    # Advance 37 minutes (matching Section 6 example)
    t1 = clock.advance(timedelta(minutes=37))
    assert t1.to_iso8601() == "2026-10-06T15:37:00+00:00"
    assert clock.now() == t1

    # TimeWindow causality
    window = TimeWindow(start_time=t0, target_time=t1)
    window.validate_causality()
    assert window.duration_seconds == 37 * 60


def test_time_window_negative_duration_raises():
    t_start = LogicalTime(timestamp=datetime(2026, 10, 6, 16, 0, 0, tzinfo=timezone.utc))
    t_target = LogicalTime(timestamp=datetime(2026, 10, 6, 15, 0, 0, tzinfo=timezone.utc))

    window = TimeWindow(start_time=t_start, target_time=t_target)
    with pytest.raises(ValueError):
        window.validate_causality()


def test_seed_controller_reproducibility():
    sc1 = SeedController(master_seed=12345)
    seq1 = [sc1.next_float() for _ in range(5)]

    sc2 = SeedController(master_seed=12345)
    seq2 = [sc2.next_float() for _ in range(5)]

    assert seq1 == seq2

    # Child RNG derived with same subkey should produce identical sequence
    rng1 = sc1.get_child_rng("agent_decision")
    rng2 = sc2.get_child_rng("agent_decision")
    assert [rng1.randint(1, 100) for _ in range(5)] == [rng2.randint(1, 100) for _ in range(5)]
