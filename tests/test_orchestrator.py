"""orchestrator unit tests — Tier 1 load size, flow, decision_log writes."""

from datetime import date, timedelta

from models import ExerciseModel, SessionInput
from skills.init import get_duckdb
from skills.session_logger import log_session
import orchestrator


def test_initialize_session_loads_tier1_under_token_limit():
    wm = orchestrator.initialize_session(today=date(2025, 7, 8))
    assert wm.date == date(2025, 7, 8)
    assert wm.recovery is not None
    assert wm.active_injuries == []  # none seeded
    assert wm.autoregulation_required in (True, False)
    assert wm.estimate_tokens() < 3000


def test_finalize_session_persists_and_clears_wm():
    wm = orchestrator.initialize_session(today=date(2025, 7, 8))
    assert orchestrator.get_working_memory() is wm
    inp = SessionInput(date=date(2025, 7, 8), exercises=[
        ExerciseModel(name="Incline Bench Press", sets=2, reps=[8, 7],
                      rpe=[9, 9], weight_kg=[40, 40], pain_flag=True),
    ])
    conf = orchestrator.finalize_session(inp)
    assert conf.date == date(2025, 7, 8)
    assert orchestrator.get_working_memory() is None  # cleared
    # pain anomaly -> logged to decision_log
    n = get_duckdb().execute("SELECT count(*) FROM decision_log WHERE event_type='anomaly'").fetchone()[0]
    assert n >= 1


def test_log_decision_writes_audit_row():
    orchestrator.log_decision(
        event_type="plan_modification",
        trigger_signal="rear_delt volume low for 4w",
        reasoning_chain="increase rear-delt frequency",
        alternative_rejected="drop side-delt volume",
        future_validation_tag="rear_delt sets/wk in next snapshot",
    )
    row = get_duckdb().execute(
        "SELECT event_type, trigger_signal, reasoning_chain, alternative_rejected, "
        "future_validation_tag FROM decision_log ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row[0] == "plan_modification"
    assert row[1] == "rear_delt volume low for 4w"


def test_active_injury_flags_autoregulation():
    get_duckdb().execute(
        "INSERT INTO injury_status (location, status, severity, "
        "contraindicated_exercises, safe_alternatives) "
        "VALUES ('left_elbow','active',4,['Skull Crusher'],['Pushdown'])"
    )
    wm = orchestrator.initialize_session(today=date(2025, 7, 8))
    assert wm.autoregulation_required is True
    assert len(wm.active_injuries) == 1