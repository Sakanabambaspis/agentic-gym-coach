"""recovery unit tests — empty history, back-to-back, pain day, determinism."""

from datetime import date, timedelta

from skills.init import get_duckdb
from skills.recovery import compute_recovery_score

_D = date(2025, 1, 15)


def _log_on(d, ex_names=("Incline Bench Press",), rpe=9.0, sets=4, pain=False):
    from models import ExerciseModel, SessionInput
    from skills.session_logger import log_session

    exs = [
        ExerciseModel(
            name=n, sets=sets,
            reps=[8] * sets, rpe=[rpe] * sets,
            weight_kg=[40] * sets, pain_flag=pain,
        )
        for n in ex_names
    ]
    log_session(SessionInput(date=d, exercises=exs))


def test_empty_history_is_push_ready():
    r = compute_recovery_score(_D)
    assert r.score == 100
    assert r.adjustment == "push-ready"
    assert r.components["days_since_last_session"] is None


def test_backward_history():
    r = compute_recovery_score(_D)
    assert r.date == _D


def test_pain_event_lowers_score():
    _log_on(_D - timedelta(days=2), pain=True)
    r = compute_recovery_score(_D)
    assert r.components["pain_events_7d"] == 1
    assert r.score < 100


def test_back_to_back_training_penalty():
    _log_on(_D - timedelta(days=2))
    _log_on(_D - timedelta(days=1))
    r = compute_recovery_score(_D)
    assert r.score < 100
    assert r.adjustment != "push-ready"


def test_high_volume_lowers_score():
    # ~40 sets over the last week
    for i in range(5):
        _log_on(_D - timedelta(days=i + 1), sets=8)
    r = compute_recovery_score(_D)
    assert r.components["sets_7d"] >= 40
    assert r.score < 100


def test_well_rested_after_two_rest_days():
    _log_on(_D - timedelta(days=3))
    r = compute_recovery_score(_D)
    # 2 rest days before target → bonus; single light session not enough to heavily penalize
    assert r.components["trained_yesterday"] is False
    assert r.components["trained_day_before"] is False