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

from pydantic import BaseModel, Field, field_validator

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


class Sex(str, Enum):
    male = "male"
    female = "female"


class ActivityLevel(str, Enum):
    """Daily-life activity outside lifting — Nutrition ch02 fallback-equation
    multipliers (all brackets already assume lifting 3–6×/wk)."""

    sedentary = "sedentary"          # 1.3–1.6
    lightly_active = "lightly_active"  # 1.5–1.8
    active = "active"                # 1.7–2.0
    very_active = "very_active"      # 1.9–2.2


class StressLevel(str, Enum):
    """Perceived life stress outside training — Training ch02 counts it in the
    same recovery budget as training stress ("one cumulative stress bucket":
    when the life side spikes, the training side must drop)."""

    low = "low"
    moderate = "moderate"
    high = "high"


class Weekday(str, Enum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class AvailabilityWindow(BaseModel):
    """One trainable slot in the user's real week (Training ch02: 'start with
    what you can do'). Times are local 24h 'HH:MM', normalized to zero-padded
    form ("7:00" → "07:00"); end may encode a closing gym. Best-effort by
    design — vague answers formatted by the coach are fine.
    """

    weekday: Weekday
    start: str | None = None
    end: str | None = None
    venue: str | None = None

    @field_validator("start", "end")
    @classmethod
    def _normalize_time(cls, v: str | None) -> str | None:
        # Accepts anything a human might say ("7:00", "07:00", " 7:5 ") and
        # stores one canonical "HH:MM"; impossible times are rejected, not
        # stored (99:99, 24:00, 23:60).
        if v is None:
            return v
        parts = v.strip().split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError(f"time must be 24h HH:MM, got {v!r}")
        h, m = int(parts[0]), int(parts[1])
        if h > 23 or m > 59:
            raise ValueError(f"hour must be 0-23 and minute 0-59, got {v!r}")
        return f"{h:02d}:{m:02d}"


class TrackingTier(str, Enum):
    """Nutrition ch07 tracking levels, best → habit. Tier drops are planned
    events on missed data, so the coach needs to know where the user starts."""

    best = "best"      # full macros at phase-dependent tolerances
    better = "better"  # protein target + calories
    good = "good"      # calories only
    habit = "habit"    # habits + 7-day weight average (gated by the estimation test)


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
    # When those days can happen — best-effort windows, formatted by the coach
    # from whatever the user says ("Fri after 7, school gym closes at 8").
    weekly_availability: list[AvailabilityWindow] = Field(default_factory=list)
    session_length_min: int | None = Field(default=None, ge=15, le=240)
    # None until the user answers — never assume full_gym (the intake scan
    # must report it missing, not launder the default into a collected value).
    equipment_access: EquipmentAccess | None = None
    priority_muscles: list[MuscleGroup] = Field(default_factory=list)
    liked_exercises: list[str] = Field(default_factory=list)
    disliked_exercises: list[str] = Field(default_factory=list)
    # Nutrition-side inputs (Nutrition ch02–ch05 prescriptions are per-bodyweight,
    # sex-, age-, and bodyfat-dependent). bodyweight_kg is the onboarding snapshot;
    # the tracked series lives in phase_snapshots.body_weight_kg.
    sex: Sex | None = None
    age_years: int | None = Field(default=None, ge=14, le=100)
    bodyweight_kg: float | None = Field(default=None, gt=0, le=400)
    bodyfat_pct: float | None = Field(default=None, gt=0, le=70)
    activity_level: ActivityLevel | None = None
    # Training-side lifestyle & history — standardized-intake x-factors.
    # life_stress: Training ch02 (one cumulative stress bucket with training).
    # concurrent_sports: Training ch02 (interference effect; priority principle).
    # rpe_calibrated: Training ch08 (novices don't program by RPE until calibrated).
    # has_tested_maxes: Training ch08/ch09 ("no tested 1RM → RPE alone").
    life_stress: StressLevel | None = None
    concurrent_sports: list[str] = Field(default_factory=list)
    rpe_calibrated: bool | None = None
    has_tested_maxes: bool | None = None
    # Nutrition-side lifestyle & history — standardized-intake x-factors.
    # diet_phase_duration_weeks: Nutrition ch05 (≥3 months dieting → diet breaks).
    # tracking_tier: Nutrition ch07 (tier drops are planned events — need the start point).
    # eating_out_per_week / alcohol_per_week: Nutrition ch08 frequency caps.
    # supplement_notes / caffeine_intake: Nutrition ch06 (three-filter stack audit;
    #   caffeine dosing is tolerance-dependent) — freeform, e.g. "2 coffees/day".
    # (meals_per_day and social_support were omitted from the intake — see
    #  docs/adr/0002-omitted-and-derived-intake-fields.md.)
    diet_phase_duration_weeks: int | None = Field(default=None, ge=0, le=520)
    tracking_tier: TrackingTier | None = None
    eating_out_per_week: int | None = Field(default=None, ge=0, le=21)
    alcohol_per_week: int | None = Field(default=None, ge=0, le=100)
    supplement_notes: str | None = None
    caffeine_intake: str | None = None
    # Nutrition ch03 insulin-resistance macro-branch gates (age, family diabetes
    # history, PCOS, oligomenorrhea). Ask when relevant to a nutrition plan,
    # phrased sensitively; never guess a value.
    family_diabetes_history: bool | None = None
    pcos: bool | None = None
    oligomenorrhea: bool | None = None
    updated_at: datetime | None = None


class MemoryNote(BaseModel):
    id: UUID | None = None
    created_at: datetime | None = None
    kind: NoteKind = NoteKind.observation
    text: str
    tags: list[str] = Field(default_factory=list)
