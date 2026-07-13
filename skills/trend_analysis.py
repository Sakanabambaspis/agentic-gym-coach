"""trend_analysis — specialization trend over a rolling window (Polars).

Returns effective volume, avg RPE, Epley 1RM estimate, and stall detection
for one muscle group over the last `window_days`. Computed in Polars (never
Pandas — repo constraint).

Definitions:
  - effective_volume: sum over matching sets of reps*weight*form_mult, where
    form_mult = 0.5 when form_quality<3 else 1.0. Sets with no recorded load
    (bodyweight/unrecorded, weight_kg IS NULL) contribute 0 tonnage but are
    counted separately as `unloaded_sets` in `detail` so the gap is visible,
    never fabricated.
  - est_1rm_kg: Epley max over weighted top sets (weight*(1+reps/30)).
  - trend_direction: second-half vs first-half effective tonnage of the window
    (>5% up / <-5% down / else plateau).
  - stalled: trend is plateau or down (the 1RM/tonnage isn't climbing).

Contract: <50ms on 10K-row synthetic set. Deterministic given the logged data.
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from models import MuscleGroup, TrendReport

from .init import get_duckdb


def _fetch_sets(muscle: MuscleGroup, start: date, end: date) -> pl.DataFrame:
    sql = """
        SELECT date, name, reps, rpe, weight_kg, form_quality, sets
        FROM (
            SELECT s.date,
                   UNNEST(s.exercises).name AS name,
                   UNNEST(s.exercises).muscle_group AS mg,
                   UNNEST(s.exercises).reps AS reps,
                   UNNEST(s.exercises).rpe AS rpe,
                   UNNEST(s.exercises).weight_kg AS weight_kg,
                   UNNEST(s.exercises).form_quality AS form_quality,
                   UNNEST(s.exercises).sets AS sets
            FROM sessions s
            WHERE s.date BETWEEN ? AND ?
        ) WHERE mg = ?
    """
    return get_duckdb().execute(sql, [start, end, muscle.value]).pl()


def get_specialization_trend(
    muscle: MuscleGroup, window_days: int = 28, end_date: date | None = None
) -> TrendReport:
    # ponytail: end_date defaults to today (SPEC contract). Passing it lets the
    # coach analyze/backtest historical slices — important because the backfilled
    # log.md spans months and a today-anchored window alone would hide all of it.
    anchor = end_date or date.today()
    start = anchor - timedelta(days=window_days)
    df = _fetch_sets(muscle, start, anchor)

    if df.height == 0:
        return TrendReport(
            muscle=muscle, window_days=window_days, effective_volume=0.0,
            avg_rpe=None, est_1rm_kg=None, stalled=False,
            trend_direction="unknown", sessions_in_window=0,
            detail={"unloaded_sets": 0},
        )

    per_set = df.explode(["reps", "rpe", "weight_kg"]).with_columns(
        pl.when(pl.col("form_quality") < 3).then(0.5).otherwise(1.0).alias("form_mult"),
    )

    tonnage = per_set.select(
        (pl.col("reps") * pl.col("weight_kg") * pl.col("form_mult")).sum()
    ).item()
    effective_volume = float(tonnage or 0.0)

    avg_rpe = per_set.select(pl.col("rpe").mean()).item()

    est_1rm = per_set.select(
        pl.when(pl.col("weight_kg").is_not_null() & pl.col("reps").is_not_null())
        .then(pl.col("weight_kg") * (1.0 + pl.col("reps") / 30.0))
        .max()
    ).item()

    # trend across first vs second half of the window (by date)
    df = df.sort("date")
    dates = df["date"].unique().sort()
    sessions = dates.len()
    if sessions >= 4:
        mid = sessions // 2
        first_dates = set(dates.head(mid).to_list())
        v_first = per_set.filter(pl.col("date").is_in(list(first_dates)))
        v_second = per_set.filter(~pl.col("date").is_in(list(first_dates)))
        tf = v_first.select((pl.col("reps") * pl.col("weight_kg") * pl.col("form_mult")).sum()).item() or 0.0
        ts = v_second.select((pl.col("reps") * pl.col("weight_kg") * pl.col("form_mult")).sum()).item() or 0.0
        if tf == 0 and ts == 0:
            trend_direction = "unknown"
        elif ts > tf * 1.05:
            trend_direction = "up"
        elif ts < tf * 0.95:
            trend_direction = "down"
        else:
            trend_direction = "plateau"
    else:
        trend_direction = "unknown"

    stalled = trend_direction in ("plateau", "down")
    unloaded = int(per_set.filter(pl.col("weight_kg").is_null()).height)

    return TrendReport(
        muscle=muscle, window_days=window_days,
        effective_volume=effective_volume,
        avg_rpe=round(float(avg_rpe), 2) if avg_rpe is not None else None,
        est_1rm_kg=round(float(est_1rm), 1) if est_1rm is not None else None,
        stalled=stalled, trend_direction=trend_direction,
        sessions_in_window=int(sessions),
        detail={"unloaded_sets": unloaded},
    )