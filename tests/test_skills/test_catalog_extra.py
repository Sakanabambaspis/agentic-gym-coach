"""exercise_catalog/canonicalize edge cases — unknowns, case, aliases, overlap maps."""

from models import MuscleGroup
from models.exercise_catalog import (
    SECONDARY_OVERLAP, _ALIAS_TO_CANONICAL, canonicalize, secondary_exercises,
)


def test_exact_canonical_name_round_trips():
    name, mg, review = canonicalize("Skull Crusher")
    assert (name, mg, review) == ("Skull Crusher", MuscleGroup.triceps, False)


def test_alias_hit_maps_to_canonical():
    assert canonicalize("Overhead Press") == ("Shoulder Press", MuscleGroup.side_delt, False)


def test_alias_hits_are_case_sensitive():
    # exact-table lookup is case-sensitive; wrong case falls to keyword guess
    name, mg, review = canonicalize("overhead press")
    assert review is True
    assert mg == MuscleGroup.side_delt  # keyword still guesses the right group
    assert name == "overhead press"     # but returns the RAW name (audit P1)


def test_keyword_fallback_returns_raw_name_with_review():
    name, mg, review = canonicalize("Meadows Row")
    assert (name, mg, review) == ("Meadows Row", MuscleGroup.mid_back, True)


def test_unknown_exercise_defaults_to_core_and_review():
    name, mg, review = canonicalize("Zercher Carry")
    assert review is True
    assert mg == MuscleGroup.core
    assert name == "Zercher Carry"


def test_empty_string_is_unknown_core():
    name, mg, review = canonicalize("")
    assert (name, mg, review) == ("", MuscleGroup.core, True)


def test_unicode_name_is_flagged_not_rejected():
    name, mg, review = canonicalize("デッドリフト")
    assert review is True
    assert name == "デッドリフト"


def test_sqlish_name_passes_through_literally():
    s = "Robert'); DROP TABLE sessions;--"
    name, mg, review = canonicalize(s)
    assert name == s and review is True


def test_secondary_overlap_reverse_map_is_consistent():
    for canon, secondaries in SECONDARY_OVERLAP.items():
        assert canon in _ALIAS_TO_CANONICAL, f"{canon} not canonical"
        assert _ALIAS_TO_CANONICAL[canon][0] == canon
        for m in secondaries:
            assert canon in secondary_exercises(m), f"{canon} missing from reverse map for {m}"


def test_secondary_exercises_unknown_muscle_returns_empty():
    assert secondary_exercises(MuscleGroup.serratus) == []  # no entry credits serratus
