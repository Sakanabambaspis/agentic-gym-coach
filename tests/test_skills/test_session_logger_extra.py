"""session_logger edge cases — empty arrays, null RPE, pain paths, phase resolution."""

from datetime import date, timedelta

from models import ExerciseModel, SessionInput
from skills.init import get_duckdb
from skills.session_logger import log_session

T = date(2030, 1, 10)


def _stored_phase() -> str | None:
    return get_duckdb().execute(
        "SELECT phase FROM sessions ORDER BY date DESC LIMIT 1").fetchone()[0]


def test_empty_exercises_array_logs_cleanly():
    conf = log_session(SessionInput(date=T, exercises=[]))
    assert conf.anomaly_flags == []
    assert _stored_phase() == "maintenance"  # default phase on empty DB
    n = get_duckdb().execute("SELECT count(*) FROM sessions").fetchone()[0]
    assert n == 1


def test_null_rpe_entries_are_kept_and_averaged_downstream():
    exs = [ExerciseModel(name="Cable Lateral Raise", sets=3,
                         reps=[10, 10, 10], rpe=[None, 8.0, None],
                         weight_kg=[10.0, 10.0, 10.0])]
    conf = log_session(SessionInput(date=T, exercises=exs))
    assert conf.anomaly_flags == []
    row = get_duckdb().execute(
        "SELECT exercises[1].rpe FROM sessions").fetchone()[0]
    assert list(row) == [None, 8.0, None]


def test_pain_flag_sets_anomaly_and_survives_to_db():
    exs = [ExerciseModel(name="Skull Crusher", sets=2, reps=[10, 9],
                         rpe=[8, 8], weight_kg=[20.0, 20.0], pain_flag=True)]
    conf = log_session(SessionInput(date=T, exercises=exs))
    codes = [f.code for f in conf.anomaly_flags]
    assert "pain_flag" in codes
    stored = get_duckdb().execute(
        "SELECT exercises[1].pain_flag FROM sessions").fetchone()[0]
    assert stored is True


def test_low_form_quality_halves_flag_not_value():
    exs = [ExerciseModel(name="Squat", sets=2, reps=[5, 5], rpe=[8, 8],
                         weight_kg=[100.0, 100.0], form_quality=2)]
    conf = log_session(SessionInput(date=T, exercises=exs))
    assert [f.code for f in conf.anomaly_flags] == ["form_quality_low"]
    # stored value is the raw 2; discounting happens in analytics, not storage
    stored = get_duckdb().execute(
        "SELECT exercises[1].form_quality FROM sessions").fetchone()[0]
    assert stored == 2


def test_unmapped_and_sqlish_names_flagged_needs_review():
    exs = [ExerciseModel(name="Robert'); DROP TABLE sessions;--", sets=1,
                         reps=[5], rpe=[8], weight_kg=[60.0])]
    conf = log_session(SessionInput(date=T, exercises=exs))
    assert [f.code for f in conf.anomaly_flags] == ["needs_review"]
    n = get_duckdb().execute("SELECT count(*) FROM sessions").fetchone()[0]
    assert n == 1  # DB intact


def test_alias_maps_to_canonical_name_and_group():
    exs = [ExerciseModel(name="Overhead Press", sets=1, reps=[5], rpe=[8],
                         weight_kg=[40.0])]
    log_session(SessionInput(date=T, exercises=exs))
    name, mg = get_duckdb().execute(
        "SELECT exercises[1].name, exercises[1].muscle_group FROM sessions"
    ).fetchone()
    assert name == "Shoulder Press"
    assert str(mg) == "side_delt"


def test_pre_recovery_score_bounds():
    for bad in (-1, 101):
        try:
            log_session(SessionInput(date=T, pre_recovery_score=bad, exercises=[]))
            raised = False
        except Exception:
            raised = True
        assert raised, f"pre_recovery_score={bad} should be rejected"


def test_explicit_phase_beats_fallback_chain():
    log_session(SessionInput(date=T, phase="cut", exercises=[]))
    assert _stored_phase() == "cut"


def test_two_same_day_sessions_are_two_rows():
    log_session(SessionInput(date=T, exercises=[]))
    log_session(SessionInput(date=T, exercises=[]))
    n = get_duckdb().execute(
        "SELECT count(*) FROM sessions WHERE date = ?", [T]).fetchone()[0]
    assert n == 2
