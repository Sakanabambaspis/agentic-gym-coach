"""Exercise catalog — alias → (canonical_name, muscle_group).

The user logs raw exercise strings (minimal effort). This module is the
canonicalization layer: ingestion looks up every raw name here and writes
the canonical name + muscle_group into DuckDB so trend_analysis groups
cleanly without the user ever categorizing anything themselves.

Extensibility: unknown exercises fall back to keyword matching, are mapped
best-effort, and flagged for review (returned via `canonicalize(...).needs_review`)
so the user can confirm the mapping — ingestion never blocks on an unknown.
"""

from __future__ import annotations

from .enums import MuscleGroup

# Each entry: (canonical_name, muscle_group, [aliases])
_ENTRIES: list[tuple[str, MuscleGroup, list[str]]] = [
    # Upper chest (specialization target)
    ("Incline Bench Press", MuscleGroup.upper_chest,
     ["Incline Press", "Machine Incline Press", "Dumbbell Incline Press", "Incline Dumbbell Press"]),
    ("Decline Push-Up", MuscleGroup.upper_chest, []),  # mirrors press pattern
    # Side delts (specialization target)
    ("Shoulder Press", MuscleGroup.side_delt,
     ["Barbell Shoulder Press", "Machine Shoulder Press", "Dumbbell Shoulder Press",
      "Strict Press", "Overhead Press"]),
    ("Lateral Raise", MuscleGroup.side_delt,
     ["Cable Lateral Raise", "Machine Lateral Raise", "Dumbbell Lateral Raise"]),
    # Rear delts (specialization target)
    ("Reverse Fly", MuscleGroup.rear_delt, ["Machine Reverse Fly"]),
    # Back / lats (detail)
    ("Pull-Up", MuscleGroup.lats, ["Pull Up", "Close Grip Pull-Up"]),
    ("Straight Arm Pulldown", MuscleGroup.lats, []),
    ("Row", MuscleGroup.mid_back,
     ["Penlay Row", "Pendlay Row", "Cable Row", "Neutral Grip Cable Row",
      "Wide Grip Cable Row", "Wide Grip Row", "Machine Row",
      "Reverse Row", "Wide Grip Reverse Row"]),
    # Arms
    ("Dip", MuscleGroup.triceps, []),
    ("Overhead Tricep Extension", MuscleGroup.triceps, []),
    ("Tricep Pushdown", MuscleGroup.triceps, []),
    ("Skull Crusher", MuscleGroup.triceps, ["Dumbbell Skull Crusher"]),
    ("Hammer Curl", MuscleGroup.biceps, []),
    ("Bay Curl", MuscleGroup.biceps, []),
    ("Dumbbell Curl", MuscleGroup.biceps, ["Curl"]),
    # Quads
    ("Squat", MuscleGroup.quads, ["Bulgarian Split Squat", "Split Squat"]),
    ("Leg Extension", MuscleGroup.quads, []),
    ("Leg Press", MuscleGroup.quads, []),
    # Hamstrings / glutes
    ("Romanian Deadlift", MuscleGroup.hamstrings, []),
    ("Leg Curl", MuscleGroup.hamstrings, ["Single-Leg Curl"]),
    # Calves
    ("Calf Raise", MuscleGroup.calves, ["Smith Calf Raise"]),
    # Core
    ("Crunch", MuscleGroup.core, ["Machine Crunch"]),
    ("Hanging Leg Raise", MuscleGroup.core, ["Leg Raise"]),
]

_ALIAS_TO_CANONICAL: dict[str, tuple[str, MuscleGroup]] = {}
_canonical_names: set[str] = set()
for _canon, _mg, _aliases in _ENTRIES:
    _ALIAS_TO_CANONICAL[_canon] = (_canon, _mg)
    _canonical_names.add(_canon)
    for _a in _aliases:
        _ALIAS_TO_CANONICAL[_a] = (_canon, _mg)


# ponytail: keyword fallback for unseen exercises. Extend the keyword lists
# as new exercises appear. An exercise whose only keyword is ambiguous
# (e.g. "Press" alone) maps to best-guess and flags needs_review=True.
_KEYWORD_RULES: list[tuple[str, MuscleGroup]] = [
    ("incline", MuscleGroup.upper_chest),
    ("lateral", MuscleGroup.side_delt),
    ("rear delt", MuscleGroup.rear_delt),
    ("reverse fly", MuscleGroup.rear_delt),
    ("row", MuscleGroup.mid_back),
    ("pull", MuscleGroup.lats),
    ("curl", MuscleGroup.biceps),
    ("tricep", MuscleGroup.triceps),
    ("skull", MuscleGroup.triceps),
    ("dip", MuscleGroup.triceps),
    ("squat", MuscleGroup.quads),
    ("leg extension", MuscleGroup.quads),
    ("leg press", MuscleGroup.quads),
    ("split", MuscleGroup.quads),
    ("deadlift", MuscleGroup.hamstrings),
    ("leg curl", MuscleGroup.hamstrings),
    ("calf", MuscleGroup.calves),
    ("crunch", MuscleGroup.core),
    ("leg raise", MuscleGroup.core),
    ("shoulder press", MuscleGroup.side_delt),
    ("overhead press", MuscleGroup.side_delt),
    ("push-up", MuscleGroup.upper_chest),
    ("pushup", MuscleGroup.upper_chest),
]


def canonicalize(raw_name: str) -> tuple[str, MuscleGroup, bool]:
    """Return (canonical_name, muscle_group, needs_review).

    Exact alias match → needs_review=False. Keyword fallback → True so the
    user can confirm the guessed mapping via /status review.
    """
    key = raw_name.strip()
    if key in _ALIAS_TO_CANONICAL:
        can, mg = _ALIAS_TO_CANONICAL[key]
        return can, mg, False
    low = key.lower()
    for kw, mg in _KEYWORD_RULES:
        if kw in low:
            return key, mg, True
    # ponytail: unmapped → still loggable, flagged for review
    return key, MuscleGroup.core, True