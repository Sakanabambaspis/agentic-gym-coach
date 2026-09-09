"""Exercise catalog — alias → (canonical_name, muscle_group, secondaries).

The canonicalization layer: ingestion looks up every raw name here and writes
the canonical name + muscle_group into DuckDB so trend_analysis groups
cleanly without the user ever categorizing anything themselves.

Secondaries implement Helms' overlap doctrine (Muscle & Strength Pyramid:
Training ch03): primary AND secondary muscle contributions count 1:1 toward
a muscle's weekly hard sets. trend_analysis credits them via
SECONDARY_OVERLAP.

Extensibility: unknown exercises fall back to keyword matching, are mapped
best-effort, and flagged for review (returned via `canonicalize(...).needs_review`)
so the user can confirm the mapping — ingestion never blocks on an unknown.
"""

from __future__ import annotations

from .enums import MuscleGroup

# Each entry: (canonical_name, muscle_group, [aliases], [secondary_muscles])
_ENTRIES: list[tuple[str, MuscleGroup, list[str], list[MuscleGroup]]] = [
    # Horizontal push — chest primary, triceps/delts secondary (ch03 table)
    ("Incline Bench Press", MuscleGroup.upper_chest,
     ["Incline Press", "Machine Incline Press", "Dumbbell Incline Press", "Incline Dumbbell Press"],
     [MuscleGroup.triceps, MuscleGroup.side_delt]),
    ("Decline Push-Up", MuscleGroup.upper_chest, [],
     [MuscleGroup.triceps, MuscleGroup.side_delt]),
    # Vertical push — delts primary (repo lumps delt heads), triceps secondary
    ("Shoulder Press", MuscleGroup.side_delt,
     ["Barbell Shoulder Press", "Machine Shoulder Press", "Dumbbell Shoulder Press",
      "Strict Press", "Overhead Press"],
     [MuscleGroup.triceps]),
    ("Lateral Raise", MuscleGroup.side_delt,
     ["Cable Lateral Raise", "Machine Lateral Raise", "Dumbbell Lateral Raise"], []),
    ("Reverse Fly", MuscleGroup.rear_delt, ["Machine Reverse Fly"], []),
    # Vertical pull — lats primary, rear delts + biceps secondary
    ("Pull-Up", MuscleGroup.lats, ["Pull Up", "Close Grip Pull-Up"],
     [MuscleGroup.rear_delt, MuscleGroup.biceps]),
    ("Straight Arm Pulldown", MuscleGroup.lats, [], [MuscleGroup.triceps]),
    # Horizontal pull — scapular retractors/lats primary, rear delts + biceps secondary
    ("Row", MuscleGroup.mid_back,
     ["Penlay Row", "Pendlay Row", "Cable Row", "Neutral Grip Cable Row",
      "Wide Grip Cable Row", "Wide Grip Row", "Machine Row",
      "Reverse Row", "Wide Grip Reverse Row"],
     [MuscleGroup.lats, MuscleGroup.rear_delt, MuscleGroup.biceps]),
    # Arms — isolation, no meaningful secondary
    ("Dip", MuscleGroup.triceps, [],
     [MuscleGroup.upper_chest, MuscleGroup.side_delt]),
    ("Overhead Tricep Extension", MuscleGroup.triceps, [], []),
    ("Tricep Pushdown", MuscleGroup.triceps, [], []),
    ("Skull Crusher", MuscleGroup.triceps, ["Dumbbell Skull Crusher"], []),
    ("Hammer Curl", MuscleGroup.biceps, [], []),
    ("Bay Curl", MuscleGroup.biceps, [], []),
    ("Dumbbell Curl", MuscleGroup.biceps, ["Curl"], []),
    # Squat pattern — quads primary, glutes + erectors (≈core) secondary
    ("Squat", MuscleGroup.quads, ["Bulgarian Split Squat", "Split Squat"],
     [MuscleGroup.glutes, MuscleGroup.core]),
    ("Leg Extension", MuscleGroup.quads, [], []),
    ("Leg Press", MuscleGroup.quads, [], [MuscleGroup.glutes, MuscleGroup.core]),
    # Hinge — hamstrings primary, glutes secondary
    ("Romanian Deadlift", MuscleGroup.hamstrings, [], [MuscleGroup.glutes]),
    ("Leg Curl", MuscleGroup.hamstrings, ["Single-Leg Curl"], []),
    # Horizontal hip extension — glutes primary, hams secondary
    ("Hip Thrust", MuscleGroup.glutes, ["Barbell Hip Thrust", "Glute Bridge", "Bridge"],
     [MuscleGroup.hamstrings]),
    ("Cable Kickback", MuscleGroup.glutes, ["Kickback"], []),
    # Isolation
    ("Calf Raise", MuscleGroup.calves, ["Smith Calf Raise"], []),
    ("Crunch", MuscleGroup.core, ["Machine Crunch"], []),
    ("Hanging Leg Raise", MuscleGroup.core, ["Leg Raise"], []),
]

_ALIAS_TO_CANONICAL: dict[str, tuple[str, MuscleGroup]] = {}
for _canon, _mg, _aliases, _secondaries in _ENTRIES:
    _ALIAS_TO_CANONICAL[_canon] = (_canon, _mg)
    for _a in _aliases:
        _ALIAS_TO_CANONICAL[_a] = (_canon, _mg)

# Helms ch03 overlap doctrine: an exercise's sets count 1:1 toward its
# SECONDARY muscles as well as its primary. Analytics-only — the sessions
# table keeps storing the single primary group.
SECONDARY_OVERLAP: dict[str, list[MuscleGroup]] = {
    _canon: _secondaries for _canon, _mg, _aliases, _secondaries in _ENTRIES
}


# Reverse map: muscle → canonical exercise names that credit it secondarily.
_SECONDARY_NAMES: dict[MuscleGroup, list[str]] = {}
for _canon, _secondaries in SECONDARY_OVERLAP.items():
    for _m in _secondaries:
        _SECONDARY_NAMES.setdefault(_m, []).append(_canon)


def secondary_exercises(muscle: MuscleGroup) -> list[str]:
    """Canonical names whose sets also count toward `muscle` (overlap)."""
    return _SECONDARY_NAMES.get(muscle, [])


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
    ("hip thrust", MuscleGroup.glutes),
    ("glute", MuscleGroup.glutes),
    ("kickback", MuscleGroup.glutes),
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
