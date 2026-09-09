"""trend_analysis — training trend over a rolling window (Polars).

Volume currency = **effective hard sets** per Helms (Muscle & Strength
Pyramid: Training ch03): count SETS in an intensity zone, never volume-load
(sets×reps×load distorts — 3×25×100 shows 78% more "volume" than 3×10×140
for equal hypertrophy). Rules:
  - primary AND secondary muscle contributions count 1:1 (secondary map:
    models.exercise_catalog.SECONDARY_OVERLAP, Helms ch03 overlap table)
  - form_quality < 3 discounts a set 50% (SPEC §1.3)
  - bodyweight/unloaded sets are hard sets (count 1.0 each); tonnage is
    reported in `detail` for reference only

est_1rm_kg: Epley over sets with reps <= 6 only ("estimate 1RM only from
~5RM-or-heavier performances", ch04). The uncapped Epley max is kept in
`detail.epley_all_reps`.

trend_direction: est-1RM trend across window halves when qualifying heavy
sets exist (±2%), else hard-set totals (strict compare). `stalled` = plateau
or down with >=4 sessions — a flag, not a verdict: the coach must run the
plateau flowchart (free-wins → recovery checklist) before acting on it.

Contract: <50ms on 10K-row synthetic set. Deterministic given the logged data.
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from models import MuscleGroup, TrendReport
from models.exercise_catalog import SECONDARY_OVERLAP, secondary_exercises

from .init import get_duckdb

_EPLEY_MAX_REPS = 6  # ~5RM-or-heavier doctrine (Training ch04)


def _fetch_entries(start: date, end: date) -> pl.DataFrame:
    """Entry-level rows: one row per exercise within a session."""
    sql = """
        SELECT date, name, mg, sets, reps, rpe, weight_kg, form_quality
        FROM (
            SELECT s.date,
                   UNNEST(s.exercises).name AS name,
                   CAST(UNNEST(s.exercises).muscle_group AS VARCHAR) AS mg,
                   UNNEST(s.exercises).sets AS sets,
                   UNNEST(s.exercises).reps AS reps,
                   UNNEST(s.exercises).rpe AS rpe,
                   UNNEST(s.exercises).weight_kg AS weight_kg,
                   UNNEST(s.exercises).form_quality AS form_quality
            FROM sessions s
            WHERE s.date BETWEEN ? AND ?
        )
    """
    return get_duckdb().execute(sql, [start, end]).pl()


def _with_form_mult(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.when(pl.col("form_quality") < 3).then(0.5).otherwise(1.0).alias("form_mult"),
    )


def hard_sets_by_muscle(start: date, end: date) -> dict[str, float]:
    """Effective hard sets per muscle group in [start, end], overlap-inclusive.

    Shared by snapshot — single definition of "weekly volume" across skills.
    """
    df = _fetch_entries(start, end)
    if df.height == 0:
        return {}
    df = _with_form_mult(df)
    out: dict[str, float] = {}
    for name, mg, sets, mult in df.select("name", "mg", "sets", "form_mult").iter_rows():
        credited = [mg] + [m.value for m in SECONDARY_OVERLAP.get(name, [])]
        for m in credited:
            out[m] = out.get(m, 0.0) + (sets or 0) * mult
    return {k: float(v) for k, v in out.items()}


def get_specialization_trend(
    muscle: MuscleGroup, window_days: int = 28, end_date: date | None = None
) -> TrendReport:
    # end_date lets the coach analyze/backtest historical slices; default today.
    anchor = end_date or date.today()
    start = anchor - timedelta(days=window_days)
    df = _fetch_entries(start, anchor)

    overlap_names = set(secondary_exercises(muscle))
    df = df.filter(
        (pl.col("mg") == muscle.value) | pl.col("name").is_in(list(overlap_names))
    )

    if df.height == 0:
        return TrendReport(
            muscle=muscle, window_days=window_days, effective_volume=0.0,
            avg_rpe=None, est_1rm_kg=None, stalled=False,
            trend_direction="unknown", sessions_in_window=0,
            detail={"unloaded_sets": 0, "overlap_sets": 0.0},
        )

    df = _with_form_mult(df)
    df = df.with_columns(
        pl.col("name").is_in(list(overlap_names)).alias("is_overlap"),
    )

    # --- hard sets (primary metric) ---------------------------------------
    hard_sets = df.select((pl.col("sets") * pl.col("form_mult")).sum()).item() or 0.0
    overlap_sets = (
        df.filter(pl.col("is_overlap"))
        .select((pl.col("sets") * pl.col("form_mult")).sum()).item() or 0.0
    )

    # --- per-set metrics (reference only) ----------------------------------
    per_set = df.explode(["reps", "rpe", "weight_kg"])
    tonnage = per_set.select(
        (pl.col("reps") * pl.col("weight_kg") * pl.col("form_mult")).sum()
    ).item() or 0.0
    avg_rpe = per_set.select(pl.col("rpe").mean()).item()

    qualifies = (
        pl.col("weight_kg").is_not_null() & pl.col("reps").is_not_null()
        & (pl.col("reps") <= _EPLEY_MAX_REPS)
    )
    est_1rm = per_set.filter(qualifies).select(
        (pl.col("weight_kg") * (1.0 + pl.col("reps") / 30.0)).max()
    ).item()
    epley_all = per_set.select(
        pl.when(pl.col("weight_kg").is_not_null() & pl.col("reps").is_not_null())
        .then(pl.col("weight_kg") * (1.0 + pl.col("reps") / 30.0))
        .max()
    ).item()
    unloaded = int(per_set.filter(pl.col("weight_kg").is_null()).height)

    # --- trend across first vs second half of the window (by date) ---------
    sessions = df["date"].unique().sort().len()
    trend_direction = "unknown"
    if sessions >= 4:
        dates = df["date"].unique().sort()
        mid = dates.len() // 2
        first_dates = set(dates.head(mid).to_list())
        in_first = pl.col("date").is_in(list(first_dates))

        tf_est = per_set.filter(in_first & qualifies).select(
            (pl.col("weight_kg") * (1.0 + pl.col("reps") / 30.0)).max()
        ).item()
        ts_est = per_set.filter(~in_first & qualifies).select(
            (pl.col("weight_kg") * (1.0 + pl.col("reps") / 30.0)).max()
        ).item()
        if tf_est is not None and ts_est is not None:
            # strength progress: est-1RM trend, ±2% band
            if ts_est > tf_est * 1.02:
                trend_direction = "up"
            elif ts_est < tf_est * 0.98:
                trend_direction = "down"
            else:
                trend_direction = "plateau"
        else:
            tf = df.filter(in_first).select(
                (pl.col("sets") * pl.col("form_mult")).sum()).item() or 0.0
            ts = df.filter(~in_first).select(
                (pl.col("sets") * pl.col("form_mult")).sum()).item() or 0.0
            if tf == 0 and ts == 0:
                trend_direction = "unknown"
            elif ts > tf:
                trend_direction = "up"
            elif ts < tf:
                trend_direction = "down"
            else:
                trend_direction = "plateau"

    stalled = trend_direction in ("plateau", "down")

    return TrendReport(
        muscle=muscle, window_days=window_days,
        effective_volume=float(hard_sets),
        avg_rpe=round(float(avg_rpe), 2) if avg_rpe is not None else None,
        est_1rm_kg=round(float(est_1rm), 1) if est_1rm is not None else None,
        stalled=stalled, trend_direction=trend_direction,
        sessions_in_window=int(sessions),
        detail={
            "tonnage_kg": round(float(tonnage), 1),
            "unloaded_sets": unloaded,
            "overlap_sets": float(overlap_sets),
            "epley_all_reps": round(float(epley_all), 1) if epley_all is not None else None,
        },
    )
