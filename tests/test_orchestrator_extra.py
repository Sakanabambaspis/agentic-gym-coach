"""orchestrator edge cases — phase fallback chain, audit defaults, vocab crash (F9)."""

from datetime import date, timedelta

import pytest

from models import ExerciseModel, MuscleGroup, PhaseType, SessionInput
from skills.init import get_duckdb
from skills.session_logger import log_session

T = date(2030, 1, 10)


def _log(d: date, phase=None):
    kw = {"phase": phase} if phase else {}
    log_session(SessionInput(date=d, exercises=[], **kw))


def test_working_memory_set_by_initialize_and_cleared():
    # NOTE: module-global _current_wm may be set by earlier tests in the run —
    # initialize overwrites it, so assert the set->clear cycle, not initial None.
    import orchestrator
    wm = orchestrator.initialize_session(today=T)
    assert orchestrator.get_working_memory() is wm
    orchestrator.clear_working_memory()
    assert orchestrator.get_working_memory() is None


def test_log_decision_default_event_type_is_plan_modification():
    import orchestrator
    orchestrator.log_decision(
        trigger_signal="t: test signal",
        reasoning_chain="t: reasoning",
        alternative_rejected="t: rejected",
        future_validation_tag="t: tag",
    )
    row = get_duckdb().execute(
        "SELECT event_type FROM decision_log WHERE trigger_signal = 't: test signal'"
    ).fetchone()
    assert row is not None
    assert row[0] == "plan_modification"


def test_finalize_session_audits_every_anomaly_code():
    import orchestrator
    inp = SessionInput(date=T, exercises=[
        ExerciseModel(name="Skull Crusher", sets=2, reps=[10, 9], rpe=[8, 8],
                      weight_kg=[20.0, 20.0], pain_flag=True, form_quality=2),
    ])
    conf = orchestrator.finalize_session(inp)
    codes = {f.code for f in conf.anomaly_flags}
    assert {"pain_flag", "form_quality_low"} <= codes
    stored = get_duckdb().execute(
        "SELECT trigger_signal FROM decision_log WHERE event_type = 'anomaly'"
    ).fetchone()[0]
    assert "pain_flag" in stored and "form_quality_low" in stored
    # finalize also cleared Tier 1
    assert orchestrator.get_working_memory() is None


def test_phase_fallback_no_data_is_none():
    import orchestrator
    wm = orchestrator.initialize_session(today=T)
    assert wm.phase is None


def test_phase_fallback_modal_session_phase_when_no_snapshot():
    import orchestrator
    _log(T - timedelta(days=1), phase="cut")
    _log(T - timedelta(days=2), phase="cut")
    _log(T - timedelta(days=3), phase="deload")
    wm = orchestrator.initialize_session(today=T)
    assert wm.phase == PhaseType.cut  # modal wins (2x cut vs 1x deload)


def test_phase_fallback_latest_snapshot_wins():
    import orchestrator
    _log(T - timedelta(days=1), phase="cut")
    get_duckdb().execute(
        "INSERT INTO phase_snapshots (snapshot_date, phase, specialization_lifts, "
        "tendon_status_summary, key_insight, next_phase_adjustment) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [T - timedelta(days=1), "realization", "{}", "{}", "", ""],
    )
    wm = orchestrator.initialize_session(today=T)
    assert wm.phase == PhaseType.realization


def test_initialize_session_trends_cover_all_priorities():
    import orchestrator
    from skills.profile import set_profile
    from models import UserProfile
    set_profile(UserProfile(priority_muscles=[MuscleGroup.lats, MuscleGroup.quads]))
    wm = orchestrator.initialize_session(today=T)
    assert set(wm.recent_trends.keys()) == {MuscleGroup.lats, MuscleGroup.quads}
    assert wm.onboarding_required is False


def test_unknown_injury_vocab_cannot_enter_via_surface():
    # REPLACES the F9 characterization test now that T1 landed (validation at
    # the injuries write path): the tool surface can no longer poison Tier-1.
    # Raw SQL bypassing the skill boundary remains out of scope by design.
    from coach_tools import DISPATCH
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        DISPATCH["injuries_seed"]({"location": "elbow", "status": "active", "severity": 4})
    import orchestrator
    wm = orchestrator.initialize_session(today=T)  # Tier-1 loads fine
    assert wm.active_injuries == []


def test_tier1_cap_trims_lowest_priority_trend_and_audits(monkeypatch):
    # T4: MEMORY_PROTOCOL §1's 3K cap is now enforced. Shrink the cap to force
    # a trim (natural load peaks at ~800 tokens per adversarial F11).
    import orchestrator
    from skills.profile import set_profile
    from models import UserProfile
    set_profile(UserProfile(priority_muscles=[
        MuscleGroup.lats, MuscleGroup.quads, MuscleGroup.biceps,
    ]))
    monkeypatch.setattr(orchestrator, "_TIER1_LIMIT_TOKENS", 200)
    wm = orchestrator.initialize_session(today=T)
    assert wm.estimate_tokens() <= 200
    assert MuscleGroup.biceps not in wm.recent_trends  # lowest priority trimmed first
    row = get_duckdb().execute(
        "SELECT trigger_signal FROM decision_log "
        "WHERE event_type = 'anomaly' AND trigger_signal LIKE '%tier1 exceeded%'"
    ).fetchone()
    assert row is not None  # the trim is audited, never silent


def test_log_decision_rejects_typo_event_type():
    # T7: a typo'd event_type used to write an unfilterable audit row silently.
    import orchestrator
    with pytest.raises(ValueError):
        orchestrator.log_decision(
            event_type="anomalies",
            trigger_signal="t: typo",
            reasoning_chain="t", alternative_rejected="t", future_validation_tag="t",
        )
