"""Model-level validation edge cases (Pydantic boundary; no DB touched)."""

from datetime import date

import pytest

from models import ExerciseModel, SessionInput, UserProfile

D = date(2030, 1, 10)


def _ex(**kw) -> dict:
    base = dict(name="Bench Press", sets=1, reps=[5], rpe=[8], weight_kg=[60.0])
    base.update(kw)
    return base


def test_mismatched_array_lengths_rejected():
    with pytest.raises(Exception, match="equal length"):
        ExerciseModel(**_ex(reps=[5, 5], rpe=[8]))


def test_all_empty_arrays_accepted():
    m = ExerciseModel(**_ex(reps=[], rpe=[], weight_kg=[]))
    assert m.reps == [] and m.rpe == [] and m.weight_kg == []


def test_omitted_arrays_padded_with_nulls():
    # FIXED (adversarial F4): an omitted array means "not tracked" and is
    # padded with None so everything stored is polars-explode-safe.
    m = ExerciseModel(**_ex(reps=[], rpe=[], weight_kg=[60.0]))
    assert m.reps == [None] and m.rpe == [None] and m.weight_kg == [60.0]


def test_partial_length_conflict_rejected():
    with pytest.raises(Exception, match="equal length"):
        ExerciseModel(**_ex(reps=[5, 5], weight_kg=[60.0]))


def test_rpe_above_10_rejected():
    # FIXED (adversarial F5): rpe is bounded 0..10 at the boundary.
    with pytest.raises(Exception):
        ExerciseModel(**_ex(rpe=[11]))


def test_infinite_weight_rejected():
    with pytest.raises(Exception):
        ExerciseModel(**_ex(weight_kg=[float("inf")]))


def test_sets_above_50_rejected():
    # A 1e9 `sets` poisoned every volume sum (adversarial F5); 50 is headroom.
    with pytest.raises(Exception):
        ExerciseModel(**_ex(sets=51))


def test_null_rpe_entries_allowed():
    m = ExerciseModel(**_ex(reps=[5, 5], rpe=[None, 8], weight_kg=[60.0, 60.0]))
    assert m.rpe == [None, 8.0]


def test_sets_bounds():
    with pytest.raises(Exception):
        ExerciseModel(**_ex(sets=0))
    ExerciseModel(**_ex(sets=1))  # lower bound OK


def test_form_quality_bounds():
    for bad in (0, 6):
        with pytest.raises(Exception):
            ExerciseModel(**_ex(form_quality=bad))
    ExerciseModel(**_ex(form_quality=1))
    ExerciseModel(**_ex(form_quality=5))


def test_session_input_phase_optional_and_default_none():
    s = SessionInput(date=D, exercises=[ExerciseModel(**_ex())])
    assert s.phase is None
    assert s.pre_recovery_score is None


def test_session_input_rejects_bad_phase_vocab():
    with pytest.raises(Exception):
        SessionInput(date=D, phase="bulking", exercises=[])


def test_pre_recovery_score_bounds():
    for bad in (-1, 101):
        with pytest.raises(Exception):
            SessionInput(date=D, pre_recovery_score=bad, exercises=[])


def test_user_profile_defaults_are_coherent():
    p = UserProfile()
    assert p.equipment_access is not None
    assert p.goals == [] and p.priority_muscles == []
