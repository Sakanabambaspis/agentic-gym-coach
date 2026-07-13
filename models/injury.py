"""Injury state + safety-gate models (SPEC §1.2 injury_status, §2.1 safety_gate)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import InjuryState, PainLocation


class InjuryStatus(BaseModel):
    """Row from the `injury_status` table — the safety source of truth."""

    id: UUID | None = None
    location: PainLocation
    status: InjuryState
    severity: int = Field(ge=0, le=10)
    contraindicated_exercises: list[str] = Field(default_factory=list)
    safe_alternatives: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class SafetyResult(BaseModel):
    """Return type of safety_gate.check_exercise_safety().

    Deterministic: `safe=False` ⇒ the caller MUST NOT suggest `exercise`.
    """

    exercise: str
    safe: bool
    alternatives: list[str] = Field(default_factory=list)
    reason: str = ""