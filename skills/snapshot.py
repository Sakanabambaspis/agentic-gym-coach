"""snapshot — compress last 4 weeks into a phase anchor document.

Builds a PhaseSnapshot from recent sessions + injury_status + user profile
and persists a phase_snapshots row (upsert by snapshot_date). Specialty 1RMs
come from Epley over qualifying sets only (reps <= 6 — "~5RM or heavier",
Training ch04). Volume is effective hard sets, overlap-inclusive, via
trend_analysis.hard_sets_by_muscle (single shared definition).

`block_state` is COMPUTED, NOT PERSISTED: weeks/blocks since the last
deload-phase session — input to the mandatory-deload floor ("deload by the
3rd mesocycle regardless", Training ch04). body_weight_kg / waist_cm are
None until a daily logging path exists — honest "I don't have that data".

Insight targets come from the user profile's priority muscles; no profile ⇒
the snapshot says so instead of inventing targets.

This skill PROPOSES (never auto-writes) Tier 3 semantic-memory updates; it
only persists the phase_snapshots row.

Contract: <200ms. Aggregated metrics must match recomputed values within 5%.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import polars as pl

from models import PhaseSnapshot

from .init import get_duckdb
from .profile import derive_priority_muscles, get_profile
from .trend_analysis import _EPLEY_MAX_REPS, hard_sets_by_muscle

# Representative lifts / muscle: {canonical_exercise: muscle_label}
REPRESENTATIVE_LIFTS = [
    "Incline Bench Press", "Shoulder Press", "Reverse Fly", "Pull-Up", "Row",
]
_WINDOW_DAYS = 28


def _fetch_all_sets(start: date, end: date) -> pl.DataFrame:
    sql = """
        SELECT date, name, reps, rpe, weight_kg, form_quality
        FROM (
            SELECT s.date,
                   UNNEST(s.exercises).name AS name,
                   UNNEST(s.exercises).reps AS reps,
                   UNNEST(s.exercises).rpe AS rpe,
                   UNNEST(s.exercises).weight_kg AS weight_kg,
                   UNNEST(s.exercises).form_quality AS form_quality
            FROM sessions s WHERE s.date BETWEEN ? AND ?
        )
    """
    return get_duckdb().execute(sql, [start, end]).pl()


def _specialization_1rms(sets_df: pl.DataFrame) -> dict[str, float]:
    if sets_df.height == 0:
        return {}
    per_set = sets_df.explode(["reps", "rpe", "weight_kg"])
    per_set = per_set.with_columns(
        pl.when(
            pl.col("weight_kg").is_not_null() & pl.col("reps").is_not_null()
            & (pl.col("reps") <= _EPLEY_MAX_REPS)
        )
        .then(pl.col("weight_kg") * (1.0 + pl.col("reps") / 30.0))
        .alias("est_1rm")
    )
    out: dict[str, float] = {}
    for ex in REPRESENTATIVE_LIFTS:
        val = per_set.filter(pl.col("name") == ex).select(pl.col("est_1rm").max()).item()
        if val is not None:
            out[ex] = round(float(val), 1)
    return out


def _current_phase() -> str | None:
    row = get_duckdb().execute(
        "SELECT phase FROM phase_snapshots ORDER BY snapshot_date DESC LIMIT 1"
    ).fetchone()
    if row:
        return row[0]
    row = get_duckdb().execute(
        "SELECT phase, count(*) c FROM sessions GROUP BY phase ORDER BY c DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def _tendon_summary() -> dict[str, Any]:
    rows = get_duckdb().execute(
        "SELECT location, status, severity FROM injury_status WHERE status <> 'resolved'"
    ).fetchall()
    return {loc: {"status": st, "severity": sev} for loc, st, sev in rows}


def _block_state(today: date) -> dict[str, Any]:
    # Mandatory-deload floor input (Training ch04): time since last deload.
    row = get_duckdb().execute(
        "SELECT MAX(date) FROM sessions WHERE phase = 'deload'"
    ).fetchone()
    last = row[0] if row else None
    if last is None:
        return {"weeks_since_deload": None, "blocks_since_deload": None}
    weeks = (today - last).days / 7.0
    return {"weeks_since_deload": round(weeks, 1), "blocks_since_deload": int(weeks // 4)}


def _insight(vol_by_muscle: dict[str, float]) -> tuple[str, str]:
    # ponytail: templated deterministic insight — NOT LLM prose. The orchestrator
    # expands with citations. Targets come from the profile, never hardcoded.
    profile = get_profile()
    if profile is None:
        return (
            "no user profile set — priorities unknown",
            "run onboarding and set goals via coach_profile_set",
        )
    targets = [m.value for m in derive_priority_muscles(profile)]
    if not targets:
        return (
            "profile has no priority muscles — balanced full-body programming",
            "declare goal target muscles or priority_muscles to enable targeting",
        )
    min_muscle = min(targets, key=lambda m: vol_by_muscle.get(m, 0.0))
    min_sets = vol_by_muscle.get(min_muscle, 0.0)
    if min_sets == 0:
        insight = f"no work logged for priority target {min_muscle} in last 4w"
        adjust = f"program at least one weekly session targeting {min_muscle}"
    else:
        insight = f"{min_muscle} is the lowest-volume priority target ({min_sets:g} hard sets/4w)"
        adjust = f"consider one more weekly session targeting {min_muscle} (Training ch03: add 1-2 sets only if plateaued AND recovering)"
    return insight, adjust


def generate_phase_snapshot() -> PhaseSnapshot:
    today = date.today()
    start = today - timedelta(days=_WINDOW_DAYS)
    sets_df = _fetch_all_sets(start, today)

    spec_lifts = _specialization_1rms(sets_df)
    vol = hard_sets_by_muscle(start, today)
    insight, adjust = _insight(vol)
    snap = PhaseSnapshot(
        snapshot_date=today,
        phase=_current_phase(),
        body_weight_kg=None,  # ponytail: no daily body_weight table yet — add when user logs it
        waist_cm=None,
        specialization_lifts=spec_lifts,
        tendon_status_summary=_tendon_summary(),
        key_insight=insight,
        next_phase_adjustment=adjust,
        block_state=_block_state(today),
    )

    d = get_duckdb()
    d.execute("DELETE FROM phase_snapshots WHERE snapshot_date = ?", [today])
    d.execute(
        """
        INSERT INTO phase_snapshots
            (snapshot_date, phase, body_weight_kg, waist_cm,
             specialization_lifts, tendon_status_summary, key_insight, next_phase_adjustment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [snap.snapshot_date, snap.phase, snap.body_weight_kg, snap.waist_cm,
         spec_lifts, snap.tendon_status_summary, snap.key_insight, snap.next_phase_adjustment],
    )
    return snap
