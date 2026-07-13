"""recovery — daily recovery score from logged signals.

The user logs minimal data (sessions/body weight/calories); sleep/HRV are not
logged. This skill derives recovery from what IS available: recent training
load (hard sets), pain events, and back-to-back training days. It is null-safe
for the missing sleep/HRV inputs (they simply don't contribute).

ponytail: the coefficients below are tunable knobs, not calibrated constants.
The composite is a transparent heuristic — fatigue = recent sets, pain is a
big negative, consecutive days add fatigue, rest days give a small bonus.
Re-tune against real outcomes once enough history exists.

Contract: <30ms. Score 0-100. <60 ⇒ orchestrator flags autoregulation required.
"""

from __future__ import annotations

from datetime import date, timedelta

from models import RecoveryScore

from .init import get_duckdb


def _days_since_last_session(before: date) -> int | None:
    """Days from the most recent session strictly before `before`, or None."""
    row = get_duckdb().execute(
        "SELECT MAX(date) FROM sessions WHERE date < ?", [before]
    ).fetchone()
    last = row[0]
    return (before - last).days if last is not None else None


def _sets_in_window(start: date, end: date) -> int:
    row = get_duckdb().execute(
        """
        SELECT coalesce(sum(sets), 0) FROM (
            SELECT UNNEST(s.exercises).sets AS sets
            FROM sessions s WHERE s.date BETWEEN ? AND ?
        )
        """,
        [start, end],
    ).fetchone()
    return int(row[0])


def _pain_in_window(start: date, end: date) -> int:
    row = get_duckdb().execute(
        """
        SELECT count(*) FROM (
            SELECT UNNEST(s.exercises).pain_flag AS pf
            FROM sessions s WHERE s.date BETWEEN ? AND ?
        ) WHERE pf
        """,
        [start, end],
    ).fetchone()
    return int(row[0])


def _trained_on(d: date) -> bool:
    return get_duckdb().execute(
        "SELECT count(*) FROM sessions WHERE date = ?", [d]
    ).fetchone()[0] > 0


def compute_recovery_score(target_date: date) -> RecoveryScore:
    score = 100
    pain_7 = _pain_in_window(target_date - timedelta(days=7), target_date - timedelta(days=1))
    score -= pain_7 * 20

    trained_y = _trained_on(target_date - timedelta(days=1))
    trained_b = _trained_on(target_date - timedelta(days=2))
    if trained_y and trained_b:
        score -= 15  # back-to-back fatigue
    elif trained_y:
        score -= 10

    sets_7 = _sets_in_window(target_date - timedelta(days=7), target_date - timedelta(days=1))
    score -= min(20, sets_7 / 2)  # ponytail: 40 sets/wk ~ ~20 penalty; tune to taste

    if not trained_y and not trained_b:
        score += 10  # well-rested

    score = max(0, min(100, int(score)))
    if score < 60:
        adjustment = "deload recommended; reduce intensity"
    elif score < 80:
        adjustment = "autoregulate; cap top-set RPE"
    elif score < 100:
        adjustment = "may train"
    else:
        adjustment = "push-ready"
    return RecoveryScore(
        date=target_date,
        score=score,
        adjustment=adjustment,
        components={
            "pain_events_7d": pain_7,
            "sets_7d": sets_7,
            "trained_yesterday": trained_y,
            "trained_day_before": trained_b,
            "days_since_last_session": _days_since_last_session(target_date),
        },
    )