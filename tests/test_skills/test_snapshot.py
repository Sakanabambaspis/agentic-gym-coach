"""snapshot unit tests — generation, upsert, e1RM cap, block_state, profile insight."""

from datetime import date, timedelta

import pytest

from models import ExerciseModel, Goal, GoalKind, MuscleGroup, SessionInput, UserProfile
from skills.init import get_duckdb
from skills.profile import set_profile
from skills.session_logger import log_session
from skills.snapshot import generate_phase_snapshot, _specialization_1rms, _fetch_all_sets


def _seed_recent(today, weights, reps=5):
    for i, w in enumerate(weights):
        log_session(SessionInput(
            date=today - timedelta(days=1),
            exercises=[
                ExerciseModel(name="Incline Bench Press", sets=len(weights),
                              reps=[reps] * len(weights), rpe=[9] * len(weights),
                              weight_kg=[w] * len(weights), form_quality=5),
            ],
        ))


def test_snapshot_generates_and_persists_row():
    today = date.today()
    _seed_recent(today, [40.0, 42.0, 45.0])
    snap = generate_phase_snapshot()
    assert snap.snapshot_date == today
    rows = get_duckdb().execute("SELECT count(*) FROM phase_snapshots WHERE snapshot_date = ?", [today]).fetchone()[0]
    assert rows == 1


def test_specialization_1rm_uses_low_rep_cap():
    today = date.today()
    _seed_recent(today, [40.0], reps=5)
    snap = generate_phase_snapshot()
    assert "Incline Bench Press" in snap.specialization_lifts
    # Epley 40*(1+5/30) ~ 46.7 — from the reps<=6 qualifying set
    assert snap.specialization_lifts["Incline Bench Press"] == pytest.approx(46.7, abs=0.5)
    # high-rep sets never inflate the estimate
    _seed_recent(today, [70.0], reps=12)
    snap2 = generate_phase_snapshot()
    assert snap2.specialization_lifts["Incline Bench Press"] == pytest.approx(46.7, abs=0.5)


def test_snapshot_is_upsert_idempotent():
    today = date.today()
    _seed_recent(today, [40.0])
    generate_phase_snapshot()
    generate_phase_snapshot()  # same day -> upsert, not duplicate
    n = get_duckdb().execute("SELECT count(*) FROM phase_snapshots WHERE snapshot_date = ?", [today]).fetchone()[0]
    assert n == 1


def test_empty_history_snapshot_no_crash():
    snap = generate_phase_snapshot()
    assert snap.specialization_lifts == {}
    assert snap.phase is None  # no prior snapshot, no sessions
    assert "no user profile" in snap.key_insight


def test_block_state_counts_since_last_deload():
    today = date.today()
    log_session(SessionInput(
        date=today - timedelta(days=14), phase="deload",
        exercises=[ExerciseModel(name="Crunch", sets=2, reps=[15, 15],
                                 rpe=[6, 6], weight_kg=[None, None])],
    ))
    snap = generate_phase_snapshot()
    assert snap.block_state["weeks_since_deload"] == pytest.approx(2.0, abs=0.1)
    assert snap.block_state["blocks_since_deload"] == 0


def test_block_state_none_without_deload_history():
    snap = generate_phase_snapshot()
    assert snap.block_state["weeks_since_deload"] is None


def test_insight_targets_come_from_profile():
    today = date.today()
    set_profile(UserProfile(goals=[
        Goal(kind=GoalKind.hypertrophy, target_muscles=[MuscleGroup.rear_delt]),
    ]))
    # log lots of one muscle, none of the target
    log_session(SessionInput(date=today - timedelta(days=1), exercises=[
        ExerciseModel(name="Cable Lateral Raise", sets=6, reps=[12] * 6,
                      rpe=[9] * 6, weight_kg=[10.0] * 6),
    ]))
    snap = generate_phase_snapshot()
    assert "rear_delt" in snap.key_insight
    assert "no work logged" in snap.key_insight


def test_consistency_recomputed_matches_within_5pct():
    today = date.today()
    _seed_recent(today, [40.0, 42.0, 45.0])
    snap = generate_phase_snapshot()
    # recompute independently
    df = _fetch_all_sets(today - timedelta(days=28), today)
    recomputed = _specialization_1rms(df)
    for ex, v in snap.specialization_lifts.items():
        assert abs(recomputed[ex] - v) / max(recomputed[ex], 1) < 0.05
