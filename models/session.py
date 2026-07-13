"""Session-log Pydantic models — validate the raw inputs before DuckDB write.

SPec §1.2 `sessions` table + §1.3 ingestion rules.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .enums import MuscleGroup, PhaseType


class ExerciseModel(BaseModel):
    """One exercise within a session. Arrays are per-set.

    `muscle_group` is optional on input — the user logs raw exercise names
    and session_logger fills it via the exercise_catalog so the user never
    has to categorize. It's set to non-null before the DB write.
    """

    name: str
    muscle_group: MuscleGroup | None = None
    sets: int = Field(ge=1)
    reps: list[float | None] = Field(default_factory=list)
    rpe: list[float | None] = Field(default_factory=list)  # 1-10, None = unrecorded
    weight_kg: list[float | None] = Field(default_factory=list)  # per-set load; None=bodyweight/unrecorded
    tempo: str | None = None  # e.g. "3-1-X-1"
    form_quality: int = Field(default=5, ge=1, le=5)
    pain_flag: bool = False
    notes: str | None = None

    @field_validator("reps", "rpe")
    @classmethod
    def _no_negative(cls, v: list[float | None]) -> list[float | None]:
        for x in v:
            if x is not None and x < 0:
                raise ValueError("reps/rpe cannot be negative")
        return v


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

    code: str  # 'pain_flag', 'form_quality_low', 'rpe_spike', ...
    detail: str


class LogConfirmation(BaseModel):
    """Return type of session_logger.log_session()."""

    session_id: UUID
    date: date
    anomaly_flags: list[AnomalyFlag] = Field(default_factory=list)
    message: str = "session logged"