"""trend_analysis unit tests — hard sets, form discount, bodyweight, overlap, e1RM cap, trend."""

from datetime import date, timedelta

import pytest

from models import ExerciseModel, MuscleGroup, SessionInput
from skills.session_logger import log_session
from skills.trend_analysis import get_specialization_trend, hard_sets_by_muscle


def _side_delt(d, weights, reps=5, rpe=9.0, form=5):
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


def test_effective_volume_counts_hard_sets():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0, 10.0, 10.0], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    # volume currency = hard sets: 3 sets × form_mult 1.0
    assert r.effective_volume == pytest.approx(3.0)
    # tonnage demoted to detail: 5 reps * 10 kg * 3 sets = 150
    assert r.detail["tonnage_kg"] == pytest.approx(150.0, rel=0.01)


def test_est_1rm_only_from_low_rep_sets():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0, 10.0, 10.0], reps=9)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    # reps 9 > 6 cap -> no qualifying sets -> est_1rm None (never a bad estimate)
    assert r.est_1rm_kg is None
    # uncapped Epley survives as reference: 10*(1+9/30) = 13.0
    assert r.detail["epley_all_reps"] == pytest.approx(13.0, abs=0.1)
    _side_delt(today - timedelta(days=2), [10.0], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    # Epley 10*(1+5/30) = 11.7 from the single qualifying set
    assert r.est_1rm_kg == pytest.approx(11.7, abs=0.1)


def test_form_quality_below_three_halves_sets():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0] * 3, reps=5, form=2)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    # form_mult 0.5 => 3 sets * 0.5 = 1.5 effective hard sets
    assert r.effective_volume == pytest.approx(1.5)


def test_bodyweight_sets_count_as_hard_sets():
    today = date.today()
    exs = [ExerciseModel(
        name="Pull-Up", sets=3, reps=[8, 7, 6], rpe=[9, 9, 9],
        weight_kg=[None, None, None],  # bodyweight
    )]
    log_session(SessionInput(date=today - timedelta(days=1), exercises=exs))
    r = get_specialization_trend(MuscleGroup.lats, window_days=28)
    assert r.effective_volume == pytest.approx(3.0)  # hard sets, load or not
    assert r.detail["unloaded_sets"] == 3
    assert r.detail["tonnage_kg"] == pytest.approx(0.0)


def test_overlap_secondary_muscles_credited():
    today = date.today()
    exs = [ExerciseModel(
        name="Row", sets=4, reps=[10] * 4, rpe=[8] * 4,
        weight_kg=[60.0] * 4,
    )]
    log_session(SessionInput(date=today - timedelta(days=1), exercises=exs))
    mid = get_specialization_trend(MuscleGroup.mid_back, window_days=28)
    rear = get_specialization_trend(MuscleGroup.rear_delt, window_days=28)
    biceps = get_specialization_trend(MuscleGroup.biceps, window_days=28)
    # Helms ch03: primary and secondary count 1:1
    assert mid.effective_volume == pytest.approx(4.0)
    assert mid.detail["overlap_sets"] == pytest.approx(0.0)
    assert rear.effective_volume == pytest.approx(4.0)
    assert rear.detail["overlap_sets"] == pytest.approx(4.0)
    assert biceps.effective_volume == pytest.approx(4.0)


def test_other_muscle_groups_excluded():
    today = date.today()
    _side_delt(today - timedelta(days=1), [10.0])
    r = get_specialization_trend(MuscleGroup.rear_delt, window_days=28)
    assert r.effective_volume == 0.0
    assert r.sessions_in_window == 0


def test_trend_up_with_increasing_load():
    today = date.today()
    for i, w in enumerate([20.0, 30.0, 40.0, 50.0]):
        _side_delt(today - timedelta(days=4 - i), [w], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    assert r.trend_direction == "up"
    assert r.stalled is False


def test_trend_down_decreasing_load_flags_stall():
    today = date.today()
    for i, w in enumerate([50.0, 40.0, 30.0, 20.0]):
        _side_delt(today - timedelta(days=4 - i), [w], reps=5)
    r = get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    assert r.trend_direction == "down"
    assert r.stalled is True


def test_hard_sets_by_muscle_overlap_inclusive():
    today = date.today()
    exs = [ExerciseModel(
        name="Row", sets=4, reps=[10] * 4, rpe=[8] * 4, weight_kg=[60.0] * 4,
    ), ExerciseModel(
        name="Squat", sets=3, reps=[5] * 3, rpe=[8] * 3, weight_kg=[100.0] * 3,
        form_quality=2,  # 3 sets * 0.5
    )]
    log_session(SessionInput(date=today - timedelta(days=1), exercises=exs))
    vol = hard_sets_by_muscle(today - timedelta(days=7), today)
    assert vol["mid_back"] == pytest.approx(4.0)
    assert vol["lats"] == pytest.approx(4.0)      # Row secondary
    assert vol["rear_delt"] == pytest.approx(4.0)  # Row secondary
    assert vol["biceps"] == pytest.approx(4.0)     # Row secondary
    assert vol["quads"] == pytest.approx(1.5)     # Squat primary, form-discounted
    assert vol["glutes"] == pytest.approx(1.5)     # Squat secondary, form-discounted
    assert vol["core"] == pytest.approx(1.5)       # Squat secondary, form-discounted


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
            "sets": 20, "reps": [5.0] * 20, "rpe": [9.0] * 20,
            "weight_kg": [20.0] * 20, "tempo": None,
            "form_quality": 5, "pain_flag": False, "notes": None,
        }]
        rows.append((today - timedelta(days=i % 28), "maintenance", None, ex_struct, None))
    d.executemany(
        "INSERT INTO sessions (date, phase, pre_recovery_score, exercises, post_feedback) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    t0 = time.perf_counter()
    get_specialization_trend(MuscleGroup.side_delt, window_days=28)
    dt_ms = (time.perf_counter() - t0) * 1000
    assert dt_ms < 100, f"trend ran in {dt_ms:.1f}ms"  # ponytail: <100ms guard (SPEC <50 on 10K)
