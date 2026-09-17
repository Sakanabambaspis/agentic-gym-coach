"""orchestrator — the integration layer wiring skills into session flow.

This is NOT a skill (it holds no LLM logic; reasoning happens higher). It
gives the LLM-time orchestrator:
  - initialize_session(): build Tier 1 working memory (MEMORY_PROTOCOL §2.1)
  - finalize_session(): validate+persist via session_logger, log anomalies to
    the audit trail, clear Tier 1 (§2.2)
  - log_decision(): write an audit-trail row to decision_log (SPEC §3.2)

All reads/writes go through the deterministic skills + the DB; never fabricate.

Surface note (audit Q1): no CLI/MCP command exposes these yet — tests exercise
them, and they are the intended wiring point for a future session surface.
"""

from __future__ import annotations

from datetime import date

from models import (
    DecisionEventType,
    LogConfirmation,
    SessionInput,
    WorkingMemoryState,
)
from skills.init import get_duckdb
from skills.injuries import get_active_injuries
from skills.phase import current_phase
from skills.profile import derive_priority_muscles, get_profile
from skills.recovery import compute_recovery_score
from skills.session_logger import log_session
from skills.trend_analysis import get_specialization_trend

_TIER1_LIMIT_TOKENS = 3000  # MEMORY_PROTOCOL §1 hard cap

_current_wm: WorkingMemoryState | None = None


def initialize_session(today: date | None = None) -> WorkingMemoryState:
    today = today or date.today()
    recovery = compute_recovery_score(today)
    injuries = get_active_injuries()
    phase = current_phase()
    profile = get_profile()
    priorities = derive_priority_muscles(profile)
    recent = {m: get_specialization_trend(m, window_days=14) for m in priorities}
    autoreg = recovery.score < 60 or len(injuries) > 0
    wm = WorkingMemoryState(
        date=today, recovery=recovery, active_injuries=injuries,
        phase=phase, autoregulation_required=autoreg,
        onboarding_required=profile is None, recent_trends=recent,
    )
    _enforce_tier1_cap(wm)
    global _current_wm
    _current_wm = wm
    return wm


def _enforce_tier1_cap(wm: WorkingMemoryState) -> None:
    """Trim recent_trends (lowest-priority muscle first) until under the cap.

    MEMORY_PROTOCOL §1 calls ~3K tokens a hard limit enforced by the
    orchestrator — this makes that true. Trimming is audited to decision_log
    so a truncated Tier-1 load is never silent.
    """
    trimmed: list[str] = []
    while wm.estimate_tokens() > _TIER1_LIMIT_TOKENS and wm.recent_trends:
        dropped = list(wm.recent_trends)[-1]  # last-inserted = lowest priority
        del wm.recent_trends[dropped]
        trimmed.append(dropped.value)
    if trimmed:
        log_decision(
            event_type=DecisionEventType.anomaly,
            trigger_signal=(f"tier1 exceeded {_TIER1_LIMIT_TOKENS} tokens; "
                            f"dropped recent_trends for: {', '.join(trimmed)}"),
            reasoning_chain="MEMORY_PROTOCOL Tier-1 hard cap enforcement",
            alternative_rejected="keeping all trends (floods the LLM context)",
            future_validation_tag="recheck after the next profile change",
        )


def finalize_session(data: SessionInput) -> LogConfirmation:
    conf = log_session(data)
    if conf.anomaly_flags:
        log_decision(
            event_type=DecisionEventType.anomaly,
            trigger_signal="; ".join(f"{f.code.value}={f.detail}" for f in conf.anomaly_flags),
            reasoning_chain="auto-detected during session_log write",
            alternative_rejected="none",
            future_validation_tag="review next session of same muscle group",
        )
    clear_working_memory()
    return conf


def log_decision(*, trigger_signal: str, reasoning_chain: str,
                 alternative_rejected: str, future_validation_tag: str,
                 event_type: DecisionEventType | str = DecisionEventType.plan_modification) -> None:
    """Append an audit row. `event_type` is checked against the controlled
    vocabulary — a typo raises here instead of writing an unfilterable row."""
    et = DecisionEventType(event_type)
    get_duckdb().execute(
        """
        INSERT INTO decision_log (event_type, trigger_signal, reasoning_chain,
                                   alternative_rejected, future_validation_tag)
        VALUES (?, ?, ?, ?, ?)
        """,
        [et.value, trigger_signal, reasoning_chain, alternative_rejected, future_validation_tag],
    )


def get_working_memory() -> WorkingMemoryState | None:
    return _current_wm


def clear_working_memory() -> None:
    global _current_wm
    _current_wm = None
