"""orchestrator — the integration layer wiring skills into session flow.

This is NOT a skill (it holds no LLM logic; reasoning happens higher). It
gives the LLM-time orchestrator:
  - initialize_session(): build Tier 1 working memory (MEMORY_PROTOCOL §2.1)
  - finalize_session(): validate+persist via session_logger, log anomalies to
    the audit trail, clear Tier 1 (§2.2)
  - log_decision(): write an audit-trail row to decision_log (SPEC §3.2)

All reads/writes go through the determinstic skills + the DB; never fabricate.
"""

from __future__ import annotations

from datetime import date

from models import (
    InjuryState, PainLocation, PhaseType, SessionInput,
    WorkingMemoryState,
)
from models.injury import InjuryStatus
from skills.init import get_duckdb
from skills.profile import derive_priority_muscles, get_profile
from skills.recovery import compute_recovery_score
from skills.session_logger import log_session
from skills.trend_analysis import get_specialization_trend

_TIER1_LIMIT_TOKENS = 3000

_current_wm: WorkingMemoryState | None = None


def _active_injuries() -> list[InjuryStatus]:
    rows = get_duckdb().execute(
        "SELECT location, status, severity, contraindicated_exercises, safe_alternatives "
        "FROM injury_status WHERE status <> 'resolved'"
    ).fetchall()
    out: list[InjuryStatus] = []
    for loc, st, sev, contra, alts in rows:
        out.append(InjuryStatus(
            location=PainLocation(loc), status=InjuryState(st), severity=sev,
            contraindicated_exercises=list(contra or []),
            safe_alternatives=list(alts or []),
        ))
    return out


def _current_phase() -> PhaseType | None:
    row = get_duckdb().execute(
        "SELECT phase FROM phase_snapshots ORDER BY snapshot_date DESC LIMIT 1"
    ).fetchone()
    if row and row[0]:
        return PhaseType(row[0])
    row = get_duckdb().execute(
        "SELECT phase FROM sessions GROUP BY phase ORDER BY count(*) DESC LIMIT 1"
    ).fetchone()
    return PhaseType(row[0]) if row and row[0] else None


def initialize_session(today: date | None = None) -> WorkingMemoryState:
    today = today or date.today()
    recovery = compute_recovery_score(today)
    injuries = _active_injuries()
    phase = _current_phase()
    profile = get_profile()
    priorities = derive_priority_muscles(profile)
    recent = {m: get_specialization_trend(m, window_days=14) for m in priorities}
    autoreg = recovery.score < 60 or len(injuries) > 0
    wm = WorkingMemoryState(
        date=today, recovery=recovery, active_injuries=injuries,
        phase=phase, autoregulation_required=autoreg,
        onboarding_required=profile is None, recent_trends=recent,
    )
    global _current_wm
    _current_wm = wm
    return wm  # ponytail: caller (LLM) must re-prompt if wm.estimate_tokens() > _TIER1_LIMIT_TOKENS


def finalize_session(data: SessionInput) -> object:
    from models import LogConfirmation  # local import avoids cycle at module load
    conf = log_session(data)
    if conf.anomaly_flags:
        log_decision(
            event_type="anomaly",
            trigger_signal="; ".join(f"{f.code}={f.detail}" for f in conf.anomaly_flags),
            reasoning_chain="auto-detected during session_log write",
            alternative_rejected="none",
            future_validation_tag="review next session of same muscle group",
        )
    clear_working_memory()
    return conf


def log_decision(*, trigger_signal: str, reasoning_chain: str,
                 alternative_rejected: str, future_validation_tag: str,
                 event_type: str = "plan_modification") -> None:
    get_duckdb().execute(
        """
        INSERT INTO decision_log (event_type, trigger_signal, reasoning_chain,
                                   alternative_rejected, future_validation_tag)
        VALUES (?, ?, ?, ?, ?)
        """,
        [event_type, trigger_signal, reasoning_chain, alternative_rejected, future_validation_tag],
    )


def get_working_memory() -> WorkingMemoryState | None:
    return _current_wm


def clear_working_memory() -> None:
    global _current_wm
    _current_wm = None