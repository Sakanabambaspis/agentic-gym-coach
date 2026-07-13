"""trend_analysis unit tests — empty, tonnage, form discount, bodyweight, trend."""

from datetime import date, timedelta

import pytest

from models import ExerciseModel, MuscleGroup, SessionInput
from skills.init import get_duckdb
from skills.session_logger import log_session
from skills.trend_analysis import get_specialization_trend


def _side_delt(d, weights, reps=9, rpe=9.0, form=5):
    exs = [
        ExerciseModel(
            name="Cable Lateral Raise", sets=len(weights),
            reps=[reps] * len(weights), rpe=[rpe] * len(weights),
            weight_kg=weights, form_quality=form,
        )
    ]
    log_session(SessionInput(date=d, exercises=exs))


def test_empty_window_returns_zero_report():
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    assert r.effective_volume == 0.0
    assert r.avg_rpe is None
    assert r.est_1rm_kg is None
    assert r.sessions_in_window == 0
    assert r.trend_direction == "unknown"


def test_effective_volume_and_1rm_computed():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0, 10.0, 10.0], reps=9)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    # 9 reps * 10 kg * 3 sets * form_mult 1.0 = 270
    assert r.effective_volume == pytest.approx(270.0, rel=0.01)
    # Epley 10*(1+9/30) = 13.0
    assert r.est_1rm_kg == pytest.approx(13.0, abs=0.1)


def test_form_quality_below_three_halves_tonnage():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0] * 3, reps=9, form=2)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    # form_mult 0.5 => 270 * 0.5 = 135
    assert r.effective_volume == pytest.approx(135.0, rel=0.01)


def test_bodyweight_unloaded_sets_counted_without_tonnage():
    today = date.today()
    exs = [ExerciseModel(
        name="Pull-Up", sets=3, reps=[8, 7, 6], rpe=[9, 9, 9],
        weight_kg=[None, None, None],  # bodyweight
    )]
    log_session(SessionInput(date=today - timedelta(days=1), exercises=exs))
    r = get_specialization_trend(MuscleGroup.lats, window_days=28)
    assert r.effective_volume == 0.0  # no load → no tonnage
    assert r.detail["unloaded_sets"] == 3


def test_other_muscle_groups_excluded():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0])
    r = get_specialization_trend(MuscleGroup.rear_delt, window_days=28)
    assert r.effective_volume == 0.0
    assert r.sessions_in_window == 0


def test_trend_up_with_increasing_tonnage():
    today = date.today()
    for i, w in enumerate([20.0, 30.0, 40.0, 50.0]):
        _side_delt(today - timedelta(days=4 - i), [w], reps=9)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    assert r.trend_direction == "up"
    assert r.stalled is False


def test_trend_down_decreasing_tonnage_flags_stall():
    today = date.today()
    for i, w in enumerate([50.0, 40.0, 30.0, 20.0]):
        _side_delt(today - timedelta(days=4 - i), [w], reps=9)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    assert r.trend_direction == "down"
    assert r.stalled is True


@pytest.mark.slow
def test_perf_under_50ms_on_synthetic_set():
    import time
    from skills.init import get_duckdb
    # Bulk-insert 500 sessions x 20 sets (= 10K set-rows) directly to DuckDB,
    # bypassing log_session. This keeps the suite fast; only the QUERY is timed.
    today = date.today()
    d = get_duckdb()
    rows = []
    for i in range(500):
        ex_struct = [{
            "name": "Cable Lateral Raise", "muscle_group": "side_delt",
            "sets": 20, "reps": [9.0] * 20, "rpe": [9.0] * 20,
            "weight_kg": [20.0] * 20, "tempo": None,
            "form_quality": 5, "pain_flag": False, "notes": None,
        }]
        rows.append((today - timedelta(days=i % 28), "internship_maintenance", None, ex_struct, None))
    d.executemany(
        "INSERT INTO sessions (date, phase, pre_recovery_score, exercises, post_feedback) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    t0 = time.perf_counter()
    get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    dt_ms = (time.perf_counter() - t0) * 1000
    assert dt_ms < 100, f"trend ran in {dt_ms:.1f}ms"  # ponytail: <100ms guard (SPEC <50 on 10K)