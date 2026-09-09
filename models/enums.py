"""Controlled vocabularies — validated at the Pydantic boundary.

v2: the DB stores phase/location as VARCHAR (migration 0002); these enums are
the single source of the allowed vocabulary. Extending a vocabulary no longer
requires a migration — add a value here and the validation layer enforces it.

Phase names follow Helms' block-periodization vocabulary (Muscle & Strength
Pyramid: Training ch04) so program state maps 1:1 onto the doctrine.
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
    maintenance = "maintenance"            # off-season / no specific push
    reconditioning = "reconditioning"      # return from layoff or into base work
    accumulation = "accumulation"          # volume block (sets up, RPE 5–8)
    intensification = "intensification"    # load/RPE climb (sets down)
    realization = "realization"            # taper / test / display fitness
    deload = "deload"                      # planned low-stress week
    cut = "cut"                            # fat-loss phase (training + diet)
    lean_bulk = "lean_bulk"                # gaining phase (training + diet)


class PainLocation(str, Enum):
    left_elbow = "left_elbow"
    right_elbow = "right_elbow"
    left_knee = "left_knee"
    right_knee = "right_knee"
    left_shoulder = "left_shoulder"
    right_shoulder = "right_shoulder"
    left_hip = "left_hip"
    right_hip = "right_hip"
    lower_back = "lower_back"
    none = "none"


class InjuryState(str, Enum):
    active = "active"
    resolving = "resolving"
    resolved = "resolved"
    chronic_baseline = "chronic_baseline"
