"""snapshot — compress last 4 weeks into a phase anchor document.

Builds a PhaseSnapshot from recent sessions + injury_status and persists a
phase_snapshots row (upsert by snapshot_date). Specialty 1RMs come from
Epley over the last 28 days. body_weight_kg / waist_cm are None until a daily
logging path exists — honest "I don't have that data" per AGENTS.md.

This skill PROPOSES (never auto-writes) Tier 3 semantic-memory updates; it
only persists the phase_snapshots row. The orchestrator asks the user for
explicit approval before any Tier 3 write.

Contract: <200ms. Aggregated metrics must match recomputed values within 5%.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import polars as pl

from models import PhaseSnapshot

from .init import get_duckdb

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
        pl.when(pl.col("weight_kg").is_not_null() & pl.col("reps").is_not_null())
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


def _volume_by_muscle(sets_df: pl.DataFrame) -> dict[str, int]:
    if sets_df.height == 0:
        return {}
    sql = """
        SELECT mg, count(*) AS sets FROM (
            SELECT UNNEST(s.exercises).sets AS st,
                   UNNEST(s.exercises).muscle_group AS mg
            FROM sessions s WHERE s.date BETWEEN ? AND ?
        ) GROUP BY mg
    """
    rows = get_duckdb().execute(sql, [date.today() - timedelta(days=_WINDOW_DAYS), date.today()]).fetchall()
    return {r[0]: int(r[1]) for r in rows}


def _insight(vol_by_muscle: dict[str, int]) -> tuple[str, str]:
    # ponytail: templated deterministic insight — NOT LLM prose. The orchestrator
    # expands with citations. Highlights the under-trained specialization target.
    targets = ["side_delt", "rear_delt", "upper_chest", "lats", "mid_back"]
    min_muscle = min(targets, key=lambda m: vol_by_muscle.get(m, 0))
    min_sets = vol_by_muscle.get(min_muscle, 0)
    if min_sets == 0:
        insight = f"no direct work logged for specialization target {min_muscle} in last 4w"
        adjust = f"add at least one {min_muscle} session per week"
    else:
        insight = f"{min_muscle} is the lowest-volume specialization target ({min_sets} sets/28d)"
        adjust = f"add one weekly session targeting {min_muscle}"
    return insight, adjust


def generate_phase_snapshot() -> PhaseSnapshot:
    today = date.today()
    start = today - timedelta(days=_WINDOW_DAYS)
    sets_df = _fetch_all_sets(start, today)

    spec_lifts = _specialization_1rms(sets_df)
    vol = _volume_by_muscle(sets_df)
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