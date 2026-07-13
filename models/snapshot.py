"""Skill return types: trend, recovery, snapshot, visual-delta.

Kept together because they're flat report models with no shared state.
Each is the contract a skill returns; callers never get a dict.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from .enums import MuscleGroup, PhaseType


class TrendReport(BaseModel):
    """Return of trend_analysis.get_specialization_trend()."""

    muscle: MuscleGroup
    window_days: int
    effective_volume: float = 0.0  # sets*reps*load, form-discounted
    avg_rpe: float | None = None
    est_1rm_kg: float | None = None
    stalled: bool = False
    trend_direction: str = "unknown"  # 'up' | 'down' | 'plateau'
    sessions_in_window: int = 0
    detail: dict[str, Any] = Field(default_factory=dict)


class RecoveryScore(BaseModel):
    """Return of recovery.compute_recovery_score()."""

    date: date
    score: int = Field(ge=0, le=100)
    adjustment: str = ""  # e.g. "deload recommended", "may push"
    components: dict[str, Any] = Field(default_factory=dict)


class PhaseSnapshot(BaseModel):
    """Return of snapshot.generate_phase_snapshot()."""

    snapshot_date: date
    phase: PhaseType | None = None
    body_weight_kg: float | None = None
    waist_cm: float | None = None
    specialization_lifts: dict[str, float] = Field(default_factory=dict)  # {exercise: est_1rm}
    tendon_status_summary: dict[str, Any] = Field(default_factory=dict)
    key_insight: str = ""
    next_phase_adjustment: str = ""


class VisualDelta(BaseModel):
    """Return of visual_delta.compare_photos() — API-bound, optional."""

    date_a: date
    date_b: date
    muscle_group_changes: dict[str, Any] = Field(default_factory=dict)
    cached: bool = True
    note: str = ""  # carries the reason when offline / unconfigured (never fabricated data)