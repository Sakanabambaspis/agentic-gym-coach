"""phase — the single resolver of "what phase are we in".

One definition, previously copy-pasted in three places with diverging
fallbacks (orchestrator / snapshot / session_logger):

    current_phase(): latest phase_snapshots row → modal phase across logged
    sessions → None (no data at all).

    phase_for_logging(): the phase to TAG a new session with — explicit user
    input wins, then current_phase(), then `maintenance` (the goal-agnostic
    off-season default, Training ch04). The fallback keeps the user from
    ever having to tag a phase by hand.
"""

from __future__ import annotations

from models import PhaseType

from .init import get_duckdb


def current_phase() -> PhaseType | None:
    """Latest snapshot's phase, else the modal session phase, else None."""
    row = get_duckdb().execute(
        "SELECT phase FROM phase_snapshots ORDER BY snapshot_date DESC LIMIT 1"
    ).fetchone()
    if row and row[0]:
        return PhaseType(row[0])
    row = get_duckdb().execute(
        "SELECT phase FROM sessions GROUP BY phase ORDER BY count(*) DESC LIMIT 1"
    ).fetchone()
    return PhaseType(row[0]) if row and row[0] else None


def phase_for_logging(explicit: PhaseType | None = None) -> PhaseType:
    """Phase to persist on a new session: explicit > current > maintenance."""
    if explicit is not None:
        return explicit
    return current_phase() or PhaseType.maintenance
