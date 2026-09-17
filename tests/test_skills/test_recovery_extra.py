"""Recovery boundary tests — exact scores at every documented band edge.

Bands (skills/recovery.py): <60 deload, <80 autoregulate, <100 may train,
==100 push-ready. Each case crafts sessions so the composite lands exactly on
the boundary; all dates are fixed (no date.today()) for determinism.
"""

from datetime import date, timedelta

import pytest

from models import ExerciseModel, SessionInput
from skills.recovery import compute_recovery_score
from skills.session_logger import log_session

T = date(2030, 1, 10)  # target date


def _session(d: date, exercises: list[ExerciseModel]) -> None:
    log_session(SessionInput(date=d, exercises=exercises))


def _ex(name: str, sets: int, pain: bool = False) -> ExerciseModel:
    return ExerciseModel(
        name=name, sets=sets, reps=[5.0] * sets, rpe=[8.0] * sets,
        weight_kg=[60.0] * sets, pain_flag=pain,
    )


def test_score_100_empty_db_is_push_ready():
    r = compute_recovery_score(T)
    assert r.score == 100  # 100 + 10 well-rested, clamped
    assert r.adjustment == "push-ready"
    assert r.components["sets_7d"] == 0
    assert r.components["days_since_last_session"] is None


def test_score_99_single_session_three_days_back():
    # 100 + 10 (well-rested: nothing on t-1/t-2) - 11 (22 sets / 2) = 99
    _session(T - timedelta(days=3), [_ex("Squat", 11), _ex("Leg Press", 11)])
    r = compute_recovery_score(T)
    assert r.score == 99
    assert r.adjustment == "may train"  # 99 < 100, not push-ready


def test_score_80_is_may_train_not_autoregulate():
    # back-to-back (t-1 empty row + t-2 session): -15; 10 sets: -5 -> 80
    _session(T - timedelta(days=1), [])
    _session(T - timedelta(days=2), [_ex("Squat", 10)])
    r = compute_recovery_score(T)
    assert r.score == 80
    assert r.adjustment == "may train"


def test_score_79_is_autoregulate():
    # -15 (back-to-back) - 6 (12 sets / 2) = 79
    _session(T - timedelta(days=1), [])
    _session(T - timedelta(days=2), [_ex("Squat", 6), _ex("Leg Press", 6)])
    r = compute_recovery_score(T)
    assert r.score == 79
    assert r.adjustment == "autoregulate; cap top-set RPE"


def test_score_60_is_autoregulate_not_deload():
    # pain 1 (-20) + back-to-back (-15) + 10 sets (-5) = 60
    _session(T - timedelta(days=1), [])
    _session(T - timedelta(days=2), [_ex("Skull Crusher", 3, pain=True),
                                     _ex("Tricep Pushdown", 7)])
    r = compute_recovery_score(T)
    assert r.score == 60
    assert r.adjustment == "autoregulate; cap top-set RPE"
    assert r.components["pain_events_7d"] == 1


def test_score_59_is_deload():
    # pain 1 (-20) + back-to-back (-15) + 12 sets (-6) = 59
    _session(T - timedelta(days=1), [])
    _session(T - timedelta(days=2), [_ex("Skull Crusher", 3, pain=True),
                                     _ex("Tricep Pushdown", 9)])
    r = compute_recovery_score(T)
    assert r.score == 59
    assert r.adjustment == "deload recommended; reduce intensity"


def test_pain_outside_7d_window_does_not_count():
    _session(T - timedelta(days=8), [_ex("Skull Crusher", 3, pain=True)])
    r = compute_recovery_score(T)
    assert r.components["pain_events_7d"] == 0


def test_back_to_back_penalty_only_when_both_days_trained():
    # only t-1 trained (empty row), t-2 empty: -10, not -15
    _session(T - timedelta(days=1), [])
    r = compute_recovery_score(T)
    assert r.score == 90
    assert r.components["trained_yesterday"] is True
    assert r.components["trained_day_before"] is False


def test_sets_penalty_capped_at_20():
    # 100 - 15 (b2b) - 20 (cap) = 65; 100 sets would over-penalize uncapped
    _session(T - timedelta(days=1), [])
    _session(T - timedelta(days=2), [_ex("Squat", 50), _ex("Leg Press", 50)])
    r = compute_recovery_score(T)
    assert r.score == 65
