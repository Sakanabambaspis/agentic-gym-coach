"""session_logger unit tests — ingest + anomaly detection + canonicalization."""

from datetime import date

import pytest
from pydantic import ValidationError

from models import ExerciseModel, LogConfirmation, MuscleGroup, SessionInput
from skills.init import get_duckdb
from skills.session_logger import log_session


def _ex(name, reps, rpe, **kw):
    return ExerciseModel(name=name, sets=len(reps), reps=reps, rpe=rpe, **kw)


def test_log_session_writes_and_returns_confirmation():
    inp = SessionInput(
        date=date(2025, 1, 12),
        exercises=[_ex("Incline Bench Press", [9, 7], [9, 9])],
    )
    conf = log_session(inp)
    assert isinstance(conf, LogConfirmation)
    assert conf.date == date(2025, 1, 12)
    count = get_duckdb().execute("SELECT count(*) FROM sessions").fetchone()[0]
    assert count == 1


def test_muscle_group_auto_filled_and_canonical_name_stored():
    inp = SessionInput(
        date=date(2025, 1, 19),
        exercises=[_ex("Incline Press", [11, 9], [9, 9])],  # alias -> canonical
    )
    log_session(inp)
    row = get_duckdb().execute(
        "SELECT exercises[1].name, exercises[1].muscle_group FROM sessions"
    ).fetchone()
    assert row[0] == "Incline Bench Press"  # canonical
    assert row[1] == MuscleGroup.upper_chest.value


def test_anomaly_flags_for_pain_low_form_and_unmapped():
    inp = SessionInput(
        date=date(2025, 1, 1),
        exercises=[
            _ex("Skull Crusher", [6, 4], [10, 10], pain_flag=True),
            _ex("Incline Bench Press", [9, 7], [9, 9], form_quality=2),
            _ex("Mystery Fly", [8, 6], [9, 9]),  # unknown -> needs_review
        ],
    )
    conf = log_session(inp)
    codes = sorted(f.code for f in conf.anomaly_flags)
    assert codes == ["form_quality_low", "needs_review", "pain_flag"]


def test_phase_defaults_to_maintenance_when_unspecified():
    inp = SessionInput(date=date(2025, 1, 1), exercises=[_ex("Squat", [8], [8])])
    log_session(inp)
    phase = get_duckdb().execute("SELECT phase FROM sessions").fetchone()[0]
    assert phase == "maintenance"


def test_phase_from_input_is_respected():
    inp = SessionInput(
        date=date(2025, 1, 1),
        phase="deload",
        exercises=[_ex("Squat", [8], [8])],
    )
    log_session(inp)
    phase = get_duckdb().execute("SELECT phase FROM sessions").fetchone()[0]
    assert phase == "deload"


def test_empty_exercises_logs_rest_day():
    inp = SessionInput(date=date(2025, 1, 2), exercises=[])
    conf = log_session(inp)
    assert conf.anomaly_flags == []
    assert get_duckdb().execute("SELECT count(*) FROM sessions").fetchone()[0] == 1


def test_null_rpe_entries_accepted():
    inp = SessionInput(
        date=date(2025, 3, 18),
        exercises=[_ex("Squat", [8, 8], [None, None])],  # RPE unrecorded
    )
    log_session(inp)
    rpe = get_duckdb().execute(
        "SELECT exercises[1].rpe FROM sessions"
    ).fetchone()[0]
    assert rpe == [None, None]


def test_pydantic_rejects_malformed_before_write():
    # form_quality out of 1-5 range -> ValidationError, never reaches DuckDB
    with pytest.raises(ValidationError):
        ExerciseModel(name="Squat", sets=1, reps=[8], rpe=[9], form_quality=8)
    # negative reps rejected
    with pytest.raises(ValidationError):
        ExerciseModel(name="Squat", sets=1, reps=[-5], rpe=[9])
    # zero sets rejected (ge=1)
    with pytest.raises(ValidationError):
        ExerciseModel(name="Squat", sets=0, reps=[], rpe=[])