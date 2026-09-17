"""Session-log Pydantic models — validate the raw inputs before DuckDB write.

SPec §1.2 `sessions` table + §1.3 ingestion rules.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import AnomalyCode, MuscleGroup, PhaseType

# Per-set plausibility bounds. None = unrecorded (bodyweight / not tracked).
# Upper bounds are generous human headroom, not physiology: they exist so
# garbage (rpe=11, sets=1e9, weight=1e308) fails at the boundary instead of
# poisoning volume sums or crashing at the DB layer (adversarial F5).
_PER_SET_BOUNDS: dict[str, tuple[float, float]] = {
    "reps": (0, 100),
    "rpe": (0, 10),
    "weight_kg": (0, 2000),
}


class ExerciseModel(BaseModel):
    """One exercise within a session. Arrays are per-set.

    `muscle_group` is optional on input — the user logs raw exercise names
    and session_logger fills it via the exercise_catalog so the user never
    has to categorize. It's set to non-null before the DB write.
    """

    name: str
    muscle_group: MuscleGroup | None = None
    sets: int = Field(ge=1, le=50)  # per-movement headroom; a 1e9 `sets` breaks every volume sum
    reps: list[float | None] = Field(default_factory=list)
    rpe: list[float | None] = Field(default_factory=list)  # 1-10, None = unrecorded
    weight_kg: list[float | None] = Field(default_factory=list)  # per-set load; None=bodyweight/unrecorded
    tempo: str | None = None  # e.g. "3-1-X-1"
    form_quality: int = Field(default=5, ge=1, le=5)
    pain_flag: bool = False
    notes: str | None = None

    @field_validator("reps", "rpe", "weight_kg")
    @classmethod
    def _sane_per_set_values(cls, v: list[float | None], info) -> list[float | None]:
        lo, hi = _PER_SET_BOUNDS[info.field_name]
        for x in v:
            if x is None:
                continue
            if not math.isfinite(x):
                raise ValueError(f"{info.field_name} values must be finite numbers")
            if not lo <= x <= hi:
                raise ValueError(f"{info.field_name} values must be within {lo:g}..{hi:g} (got {x:g})")
        return v

    @model_validator(mode="after")
    def _per_set_arrays_aligned(self) -> "ExerciseModel":
        # Per-set arrays must describe the same sets: a bodyweight log may omit
        # weight entirely, so fully-empty arrays are PADDED with None (None =
        # unrecorded) instead of rejected. True length conflicts (reps=[8,7],
        # rpe=[8]) are malformed and rejected before the DB write (SPEC §1.3).
        # Analytics explode these lists per set and polars crashes on unequal
        # lengths, so everything stored must be explode-safe (adversarial F4).
        lengths = {name: len(getattr(self, name))
                   for name in ("reps", "rpe", "weight_kg")}
        non_empty = {n for n in lengths.values() if n}
        if len(non_empty) > 1:
            raise ValueError(
                "reps/rpe/weight_kg are per-set arrays and must be equal length "
                f"(got reps={lengths['reps']}, rpe={lengths['rpe']}, "
                f"weight_kg={lengths['weight_kg']}); "
                "use null entries for unrecorded sets"
            )
        target = max(non_empty) if non_empty else 0
        for name, n in lengths.items():
            if target and n == 0:
                setattr(self, name, [None] * target)
        return self


class SessionModel(BaseModel):
    """Full persisted row (post-write). Read shape from `sessions` table."""

    id: UUID | None = None
    date: date
    phase: PhaseType
    pre_recovery_score: int | None = Field(default=None, ge=0, le=100)
    exercises: list[ExerciseModel]
    post_feedback: str | None = None
    created_at: datetime | None = None


class SessionInput(BaseModel):
    """What the caller passes to session_logger.log_session().

    `phase` is optional — if omitted the current phase from phase_snapshots
    is used. This keeps user logging frictionless (they never set phase).
    """

    date: date
    phase: PhaseType | None = None
    pre_recovery_score: int | None = Field(default=None, ge=0, le=100)
    exercises: list[ExerciseModel]
    post_feedback: str | None = None


class AnomalyFlag(BaseModel):
    """One anomaly raised during a log write."""

    code: AnomalyCode
    detail: str


class LogConfirmation(BaseModel):
    """Return type of session_logger.log_session()."""

    session_id: UUID
    date: date
    anomaly_flags: list[AnomalyFlag] = Field(default_factory=list)
    message: str = "session logged"