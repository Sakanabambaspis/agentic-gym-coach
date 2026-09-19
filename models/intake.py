"""Intake-assessment models — the standardized "bucket list" of everything
the coach needs before programming decisions, and the report of what the
database already holds.

The checklist is DATA (INTAKE_CHECKLIST), not prompt prose: one entry per
intake factor, each citing its vendored-book source or carrying an explicit
HEURISTIC label (unsourced doctrine was deliberately removed from this repo —
a heuristic field must say so, see docs/IDEAS.md #1). skills.intake.assess_
intake() scans stored state against this list; the coach cites what's
present (asking "still accurate?"), asks only for what's missing, in
checklist order, and applies the soft per-domain gates (COACH_PROMPT
"Standardized intake assessment").

Excluded from the bucket list on purpose (docs/adr/0001-...md and
docs/adr/0002-omitted-and-derived-intake-fields.md): sleep as a static field
(both books treat recovery questions as recurring check-ins), food
allergies/dislikes (the nutrition book is anti-preference-exclusion),
budget/cooking skill, clinical screening, motivation scoring — and, after
first-use feedback: meals (frequency is book-neutral, Nutrition ch05),
social support (too abstract, effect unpredictable), priority muscles
(derived from goals + observed weak points, never asked). They stay
answerable as ordinary coaching questions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GateDomain(str, Enum):
    """Which decision domain a field gates. `both` = goal-level context the
    training AND nutrition books both consume (e.g. the goal itself)."""

    training = "training"
    nutrition = "nutrition"
    both = "both"


class FieldStatus(str, Enum):
    collected = "collected"  # a value exists in storage (caveat: confirm it's still true)
    missing = "missing"      # nothing stored — the coach must ask


class IntakeField(BaseModel):
    """One bucket-list entry: what to know, where it lives, what it gates."""

    name: str            # canonical checklist key (snake_case)
    source: str          # book citation, or "HEURISTIC — ..." (never neither)
    storage: str         # "profile.<attr>" or "injury_status"
    gates: GateDomain
    blocks_gate: bool = True  # False = reported when missing, but never holds a gate open
    # list-typed profile fields only: True = empty list means "never asked"
    # (strict presence — goals, weekly_availability); False = empty is a valid
    # "nothing applies" answer. Declared here so the resolver carries no
    # per-name special cases.
    empty_means_missing: bool = False
    note: str = ""       # how the coach uses it / how to collect it


class FieldReport(IntakeField):
    """Outcome of scanning one IntakeField against stored state.

    Subclasses IntakeField so the report carries the field's own name/source/
    gates/blocks_gate verbatim (flat JSON for the LLM surface) with no
    field-by-field copying to drift.
    """

    status: FieldStatus
    value: Any = None    # JSON-safe stored value; always None when missing


class IntakeReport(BaseModel):
    """Return of intake.assess_intake() — the whole checklist, scanned.

    `*_ready` means no BLOCKING field gating that domain is missing (soft
    gates: the coach withholds domain plans until ready, but may produce a
    provisional plan with explicit limitations if the user insists —
    COACH_PROMPT). `weeks_since_last_session` is staleness context for the
    confirm-present step (threshold: skills.snapshot.REASSESSMENT_GAP_WEEKS,
    a heuristic).
    """

    fields: list[FieldReport] = Field(default_factory=list)
    weeks_since_last_session: float | None = None
    training_ready: bool = False
    nutrition_ready: bool = False
    missing: list[str] = Field(default_factory=list)
    # convenience view of `missing` grouped by domain ("training"/"nutrition");
    # redundant with fields/missing/*_ready by design — the LLM surface cites
    # whichever shape is cheapest per turn
    missing_by_gate: dict[str, list[str]] = Field(default_factory=dict)


# The bucket list — single source of truth for the standardized intake.
# Order mirrors the books' own priority hierarchies (Training ch01: adherence
# → volume/intensity/frequency → …; Nutrition ch01: energy → macros → …):
# goals first, then training-gated factors, then nutrition-gated factors.
INTAKE_CHECKLIST: list[IntakeField] = [
    IntakeField(
        name="goals", source="Training ch02 (deadlines), ch08 (goal column); Nutrition ch02 (rates by goal)",
        storage="profile.goals", gates=GateDomain.both, empty_means_missing=True,
        note=("kind + physique_target + target_muscles + deadline; deadline drives taper and diet timing. "
              "A vision stated vaguely is recorded as-is (notes/metric) — it is provisional and sharpens "
              "as understanding grows. Empty is NOT an answer: 'no specific goal' is kind=general_fitness"),
    ),
    IntakeField(
        name="training_age", source="Training ch04 (classify by RATE OF PROGRESS — workout-to-workout / week-to-week / month-to-month — not years lifting)",
        storage="profile.training_age", gates=GateDomain.training,
        note="sets volume tier, frequency, progression model, gain-rate bracket",
    ),
    IntakeField(
        name="days_per_week", source="Training ch02 ('start with what you can do'), ch08 (2–6 days; 3–5 for 90% of people)",
        storage="profile.days_per_week", gates=GateDomain.training,
        note="committed training days; the WHEN comes from weekly_availability",
    ),
    IntakeField(
        name="weekly_availability", source="Training ch02 ('start with what you can do' — match the program to the actual week) — window structure HEURISTIC",
        storage="profile.weekly_availability", gates=GateDomain.training, blocks_gate=False,
        empty_means_missing=True,
        note=("time windows per weekday; venue captures a closing gym. Vague answers are fine — "
              "the coach formats them into windows; plan the week around them"),
    ),
    IntakeField(
        name="life_stress", source="Training ch02 (life stress and training stress are one cumulative bucket)",
        storage="profile.life_stress", gates=GateDomain.training,
        note=("work/sleep/family load; high stress ⇒ the training side must drop. A rolling "
              "recent-overall impression — re-confirm at check-ins, expected to move"),
    ),
    IntakeField(
        name="injuries", source="Training ch02 (pain is information), ch05 (pain caps volume; substitutions)",
        storage="injury_status", gates=GateDomain.training, blocks_gate=False,
        note=("rows in injury_status; seed via coach_injuries_seed on any report. "
              "No rows = no reported injuries, so this never holds the gate open — "
              "persona rule 2 (always check injuries) guarantees the ask. "
              "Re-confirm periodically: shelf-life tracking is deferred (docs/IDEAS.md #1)."),
    ),
    IntakeField(
        name="exercise_likes", source="Training ch05 (lifters who choose exercises out-gain fixed selection)",
        storage="profile.liked_exercises", gates=GateDomain.training, blocks_gate=False,
        note=("enjoyment drives adherence (ch02); bounded by proficiency. Emerges over the "
              "first blocks — the coach proposes, records reactions here"),
    ),
    IntakeField(
        name="exercise_dislikes", source="Training ch02 (enjoyment drives effort), ch05 (preference is a sanctioned selection input)",
        storage="profile.disliked_exercises", gates=GateDomain.training, blocks_gate=False,
        note=("hated exercises get swapped for pain-free comparable patterns. Emerges through "
              "training — not knowable at intake, never forced"),
    ),
    IntakeField(
        name="concurrent_sports", source="Training ch02 (interference effect; one activity takes priority)",
        storage="profile.concurrent_sports", gates=GateDomain.training,
        note="other sports/cardio: ordering mitigations + priority principle apply",
    ),
    IntakeField(
        name="rpe_calibrated", source="Training ch08 (novices track RPE without programming by it until calibrated)",
        storage="profile.rpe_calibrated", gates=GateDomain.training,
        note="false/None ⇒ loads prescribed by feel + repetition, not RPE targets",
    ),
    IntakeField(
        name="has_tested_maxes", source="Training ch08 ('no tested 1RM on a lift → RPE alone'), ch09 (test a 3–5RM with spotters)",
        storage="profile.has_tested_maxes", gates=GateDomain.training,
        note="whether real percentages can be computed or RPE-only applies",
    ),
    IntakeField(
        name="session_length_min", source="HEURISTIC — the books DERIVE session length from frequency (Training ch08), they never ask it",
        storage="profile.session_length_min", gates=GateDomain.training,
        note="kept because real schedules constrain session count × length",
    ),
    IntakeField(
        name="equipment_access", source="HEURISTIC — not an intake item in the books; implied by machine-exercise classes (Training ch08) and substitution rules (ch09)",
        storage="profile.equipment_access", gates=GateDomain.training,
        note="None until the user answers — never assume full_gym",
    ),
    IntakeField(
        name="sex", source="Nutrition ch03 (female fiber floor 20g vs 25g), ch05 (refeed gate pairing with bodyfat)",
        storage="profile.sex", gates=GateDomain.nutrition,
        note="gates refeed thresholds and fiber floor",
    ),
    IntakeField(
        name="age_years", source="Nutrition ch03 (insulin-resistance predictor; defaults assume under ~60)",
        storage="profile.age_years", gates=GateDomain.nutrition,
        note="macro-branch gate, not a volume prescription",
    ),
    IntakeField(
        name="bodyweight_kg", source="Nutrition ch02 (BW×10 maintenance, protein g/lb, %-BW rates), ch03, ch04 (fluids)",
        storage="profile.bodyweight_kg", gates=GateDomain.nutrition,
        note="the single most load-bearing nutrition number; prefer the tracked snapshot series once available",
    ),
    IntakeField(
        name="bodyfat_pct", source="Nutrition ch05 (refeed gate: ~12% M / ~20% F)",
        storage="profile.bodyfat_pct", gates=GateDomain.nutrition,
        note="only needed when cutting — ask-when-relevant",
    ),
    IntakeField(
        name="activity_level", source="Nutrition ch02 (maintenance multipliers 1.3–2.2 by daily-life activity)",
        storage="profile.activity_level", gates=GateDomain.nutrition,
        note="NEAT bracket; the equation is a hypothesis corrected by weekly weight averages",
    ),
    IntakeField(
        name="diet_phase_duration_weeks", source="Nutrition ch05 (≥3 months dieting → schedule diet breaks)",
        storage="profile.diet_phase_duration_weeks", gates=GateDomain.nutrition,
        note="current continuous cut/gain duration, not past diet history",
    ),
    IntakeField(
        name="tracking_tier", source="Nutrition ch07 (four tiers; 'miss = drop a tier and continue')",
        storage="profile.tracking_tier", gates=GateDomain.nutrition,
        note="willingness/experience selects the prescription tier",
    ),
    IntakeField(
        name="eating_out_per_week", source="Nutrition ch08 (frequency caps by phase: prep ~monthly / cut 1–2×/wk)",
        storage="profile.eating_out_per_week", gates=GateDomain.nutrition,
        note="hidden-oil error margin ordering applies",
    ),
    IntakeField(
        name="alcohol_per_week", source="Nutrition ch08 (7 kcal/g; ≤15% of daily kcal; ≤2×/wk)",
        storage="profile.alcohol_per_week", gates=GateDomain.nutrition,
        note="drinks/week; automatic tier-drop while drinking",
    ),
    IntakeField(
        name="supplement_notes", source="Nutrition ch06 (audit whatever stack the user reports via the three-filter test)",
        storage="profile.supplement_notes", gates=GateDomain.nutrition,
        note="freeform current stack; never invent product claims",
    ),
    IntakeField(
        name="caffeine_intake", source="Nutrition ch06 (caffeine dosing is tolerance-dependent; habitual intake is load-bearing)",
        storage="profile.caffeine_intake", gates=GateDomain.nutrition,
        note="freeform, e.g. '2 coffees/day'",
    ),
    IntakeField(
        name="family_diabetes_history", source="Nutrition ch03 (insulin-resistance macro-branch gate)",
        storage="profile.family_diabetes_history", gates=GateDomain.nutrition,
        note="ask-when-relevant (nutrition plan); phrased sensitively",
    ),
    IntakeField(
        name="pcos", source="Nutrition ch03 (insulin-resistance macro-branch gate)",
        storage="profile.pcos", gates=GateDomain.nutrition,
        note="ask-when-relevant (nutrition plan); phrased sensitively",
    ),
    IntakeField(
        name="oligomenorrhea", source="Nutrition ch03 (>35-day cycles; over-represented in strength sports)",
        storage="profile.oligomenorrhea", gates=GateDomain.nutrition,
        note="ask-when-relevant (nutrition plan); phrased sensitively",
    ),
]
