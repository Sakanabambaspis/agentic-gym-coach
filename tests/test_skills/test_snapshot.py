"""snapshot unit tests — generation, upsert, 5% consistency, empty history."""

from datetime import date

import pytest

from models import ExerciseModel, SessionInput
from skills.init import get_duckdb
from skills.session_logger import log_session
from skills.snapshot import generate_phase_snapshot, _specialization_1rms, _volume_by_muscle


def _seed_recent(today, weights):
    from datetime import timedelta
    for i, w in enumerate(weights):
        log_session(SessionInput(
            date=today - timedelta(days=1),
            exercises=[
                ExerciseModel(name="Incline Bench Press", sets=len(weights),
                              reps=[8] * len(weights), rpe=[9] * len(weights),
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


def test_specialization_1rm_in_snapshot():
    today = date.today()
    _seed_recent(today, [40.0])
    snap = generate_phase_snapshot()
    assert "Incline Bench Press" in snap.specialization_lifts
    # Epley 40*(1+8/30) ~ 50.7
    assert snap.specialization_lifts["Incline Bench Press"] == pytest.approx(50.7, abs=0.5)


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


def test_consistency_recomputed_matches_within_5pct():
    today = date.today()
    _seed_recent(today, [40.0, 42.0, 45.0])
    snap = generate_phase_snapshot()
    # recompute independently
    from datetime import timedelta
    from skills.snapshot import _fetch_all_sets
    df = _fetch_all_sets(today - timedelta(days=28), today)
    recomputed = _specialization_1rms(df)
    for ex, v in snap.specialization_lifts.items():
        assert abs(recomputed[ex] - v) / max(recomputed[ex], 1) < 0.05