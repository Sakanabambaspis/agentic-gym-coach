"""phase — the single current-phase resolver (audit T3: was 3 divergent copies)."""

from datetime import date

from models import ExerciseModel, PhaseType, SessionInput
from skills.init import get_duckdb
from skills.phase import current_phase, phase_for_logging
from skills.session_logger import log_session

D = date(2030, 3, 1)


def _log(d: date, phase: PhaseType | None = None) -> None:
    ex = ExerciseModel(name="Squat", sets=1, reps=[5], rpe=[8], weight_kg=[100.0])
    log_session(SessionInput(date=d, exercises=[ex], phase=phase))


def test_no_data_returns_none():
    assert current_phase() is None


def test_modal_session_phase_is_fallback():
    _log(D, PhaseType.cut)
    _log(D, PhaseType.cut)
    _log(D, PhaseType.accumulation)
    assert current_phase() is PhaseType.cut


def test_latest_snapshot_wins_over_modal_sessions():
    _log(D, PhaseType.cut)
    get_duckdb().execute(
        "INSERT INTO phase_snapshots (snapshot_date, phase) VALUES (?, ?)",
        [date(2030, 3, 2), "accumulation"],
    )
    assert current_phase() is PhaseType.accumulation


def test_phase_for_logging_defaults_to_maintenance():
    assert phase_for_logging() is PhaseType.maintenance


def test_phase_for_logging_explicit_wins():
    assert phase_for_logging(PhaseType.deload) is PhaseType.deload


def test_phase_for_logging_uses_current_phase():
    _log(D, PhaseType.cut)
    assert phase_for_logging() is PhaseType.cut
