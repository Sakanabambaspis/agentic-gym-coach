"""trend_analysis edge cases — null RPE, session-count gate, window extremes."""

from datetime import date, timedelta

import pytest

from models import ExerciseModel, MuscleGroup, SessionInput
from skills.session_logger import log_session
from skills.trend_analysis import get_specialization_trend, hard_sets_by_muscle

T = date(2030, 1, 10)


def _log(d: date, weights: list[float | None], reps: float = 5.0,
         rpes: list[float | None] | None = None, name: str = "Cable Lateral Raise"):
    n = len(weights)
    exs = [ExerciseModel(
        name=name, sets=n, reps=[reps] * n,
        rpe=(rpes if rpes is not None else [9.0] * n), weight_kg=weights,
    )]
    log_session(SessionInput(date=d, exercises=exs))


def test_hard_sets_empty_window_is_empty_dict():
    assert hard_sets_by_muscle(date(2030, 3, 1), date(2030, 3, 28)) == {}


def test_null_rpe_gives_null_avg_without_crashing():
    _log(T - timedelta(days=1), [10.0, 10.0], rpes=[None, 8.0])
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28, end_date=T)
    assert r.avg_rpe == pytest.approx(8.0)  # nulls excluded from mean
    assert r.effective_volume == pytest.approx(2.0)


def test_all_null_rpe_gives_null_avg():
    _log(T - timedelta(days=1), [10.0], rpes=[None])
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28, end_date=T)
    assert r.avg_rpe is None


def test_null_weight_excluded_from_est_1rm_but_counts_as_set():
    _log(T - timedelta(days=1), [None, 60.0], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28, end_date=T)
    assert r.effective_volume == pytest.approx(2.0)  # bodyweight set counts
    assert r.detail["unloaded_sets"] == 1
    # only the 60kg set qualifies: 60 * (1 + 5/30) = 70.0
    assert r.est_1rm_kg == pytest.approx(70.0, abs=0.1)


def test_trend_needs_four_sessions_for_direction():
    for i in range(3):
        _log(T - timedelta(days=3 - i), [50.0 - 10 * i], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28, end_date=T)
    assert r.sessions_in_window == 3
    assert r.trend_direction == "unknown"
    assert r.stalled is False


def test_stalled_requires_plateau_or_down():
    for i in range(4):
        _log(T - timedelta(days=4 - i), [40.0], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28, end_date=T)
    assert r.trend_direction == "plateau"
    assert r.stalled is True


def test_negative_window_returns_empty_report():
    # CHARACTERIZATION (adversarial F7): inverted window silently means "no data".
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=-28, end_date=T)
    assert r.effective_volume == 0.0
    assert r.sessions_in_window == 0


def test_form_discount_applies_to_tonnage_and_sets():
    _log(T - timedelta(days=1), [100.0, 100.0, 100.0], reps=5)
    # make one set low-quality by rewriting form via a second low-form exercise
    exs = [ExerciseModel(name="Squat", sets=2, reps=[5, 5], rpe=[8, 8],
                         weight_kg=[100.0, 100.0], form_quality=2)]
    log_session(SessionInput(date=T - timedelta(days=2), exercises=exs))
    vol = hard_sets_by_muscle(T - timedelta(days=7), T)
    assert vol["quads"] == pytest.approx(1.0)   # 2 sets x 0.5
    assert vol["side_delt"] == pytest.approx(3.0)
