"""Controlled vocabularies — mirror DuckDB ENUM types (SPEC §1.2).

Keep values lowercase snake_case; they map 1:1 to the SQL ENUM labels.
"""

from enum import Enum


class MuscleGroup(str, Enum):
    side_delt = "side_delt"
    rear_delt = "rear_delt"
    upper_chest = "upper_chest"
    mid_back = "mid_back"
    lats = "lats"
    biceps = "biceps"
    triceps = "triceps"
    quads = "quads"
    hamstrings = "hamstrings"
    glutes = "glutes"
    core = "core"
    calves = "calves"
    serratus = "serratus"


class PhaseType(str, Enum):
    internship_maintenance = "internship_maintenance"
    bridge_reconditioning = "bridge_reconditioning"
    specialization_lean_bulk = "specialization_lean_bulk"
    diet_break = "diet_break"
    mini_cut = "mini_cut"
    deload = "deload"


class PainLocation(str, Enum):
    left_elbow = "left_elbow"
    right_elbow = "right_elbow"
    left_knee = "left_knee"
    right_knee = "right_knee"
    lower_back = "lower_back"
    none = "none"


class InjuryState(str, Enum):
    active = "active"
    resolving = "resolving"
    resolved = "resolved"
    chronic_baseline = "chronic_baseline"