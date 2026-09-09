"""User profile + memory-note models — the v2 "who am I coaching" state.

The profile is validated data, not prompt text: goals, training age, schedule,
equipment, and muscle priorities drive orchestrator/snapshot behavior
directly. `physique_target` names the aesthetic outcome (ripped / athletic /
bulky); achieving it spans BOTH vendored skills — training (helms-training-
pyramid) and nutrition (helms-nutrition-pyramid) — and the coach routes
accordingly.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import MuscleGroup


class GoalKind(str, Enum):
    hypertrophy = "hypertrophy"
    strength = "strength"
    powerlifting = "powerlifting"
    general_fitness = "general_fitness"
    fat_loss = "fat_loss"
    rehab_support = "rehab_support"


class PhysiqueTarget(str, Enum):
    ripped = "ripped"        # low BF emphasis — cut rules + training retention
    athletic = "athletic"    # balanced mass + condition
    bulky = "bulky"          # mass emphasis — accumulation + surplus (diet side)


class TrainingAge(str, Enum):
    novice = "novice"
    intermediate = "intermediate"
    advanced = "advanced"


class EquipmentAccess(str, Enum):
    full_gym = "full_gym"
    home = "home"
    minimal = "minimal"


class NoteKind(str, Enum):
    preference = "preference"
    lesson = "lesson"
    milestone = "milestone"
    observation = "observation"


class Goal(BaseModel):
    kind: GoalKind
    physique_target: PhysiqueTarget | None = None
    target_muscles: list[MuscleGroup] = Field(default_factory=list)
    metric: str | None = None        # e.g. "first pull-up", "2x BW squat"
    deadline: date | None = None
    notes: str | None = None


class UserProfile(BaseModel):
    display_name: str | None = None
    goals: list[Goal] = Field(default_factory=list)
    training_age: TrainingAge | None = None
    days_per_week: int | None = Field(default=None, ge=1, le=7)
    session_length_min: int | None = Field(default=None, ge=15, le=240)
    equipment_access: EquipmentAccess = EquipmentAccess.full_gym
    priority_muscles: list[MuscleGroup] = Field(default_factory=list)
    liked_exercises: list[str] = Field(default_factory=list)
    disliked_exercises: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class MemoryNote(BaseModel):
    id: UUID | None = None
    created_at: datetime | None = None
    kind: NoteKind = NoteKind.observation
    text: str
    tags: list[str] = Field(default_factory=list)
