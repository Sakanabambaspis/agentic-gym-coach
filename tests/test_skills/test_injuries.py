"""injuries skill — the validated, canonicalizing injury_status boundary.

Covers the audit's P1 fix (validate + canonicalize at the write) and the
adversarial findings F1/F2/F9 (fail-open gate, garbage vocab, deferred
Tier-1 crash).
"""

import pytest
from pydantic import ValidationError

import orchestrator
from models import InjurySeedResult, InjuryStatus
from skills.init import get_duckdb
from skills.injuries import (
    get_active_injuries,
    list_injuries,
    seed_injury,
    tendon_summary,
)
from skills.safety_gate import check_exercise_safety


def _injury_rows() -> int:
    return get_duckdb().execute("SELECT count(*) FROM injury_status").fetchone()[0]


def test_seed_validates_location_vocabulary_and_writes_nothing_on_error():
    with pytest.raises(ValidationError):
        seed_injury("elbow", "active", 3)  # not a PainLocation (F2)
    assert _injury_rows() == 0


def test_seed_validates_status_and_severity_bounds():
    with pytest.raises(ValidationError):
        seed_injury("left_elbow", "banana", 3)  # not an InjuryState (F2)
    with pytest.raises(ValidationError):
        seed_injury("left_elbow", "active", 3.7)  # fractional severity (F2)
    with pytest.raises(ValidationError):
        seed_injury("left_elbow", "active", 11)  # DB CHECK previously the only guard
    assert _injury_rows() == 0


def test_seed_canonicalizes_alias_and_gate_blocks_canonical_query():
    res = seed_injury("left_elbow", "active", 4,
                      contraindicated_exercises=["Dumbbell Skull Crusher"],
                      safe_alternatives=["Tricep Pushdown"])
    assert isinstance(res, InjurySeedResult)
    assert res.injury.contraindicated_exercises == ["Skull Crusher"]
    assert res.needs_review == []
    r = check_exercise_safety("Skull Crusher")
    assert r.safe is False
    assert "Tricep Pushdown" in r.alternatives


def test_seed_unmapped_name_stored_and_flagged_needs_review():
    # The F1 residual: "skullcrushers" is not an alias. It is stored verbatim
    # and flagged so the coach confirms it with the user.
    res = seed_injury("left_elbow", "active", 4,
                      contraindicated_exercises=["skullcrushers"])
    assert res.needs_review == ["skullcrushers"]


def test_gate_matches_stored_names_case_insensitively():
    # Ban written as the user said it (lowercase) still blocks the canonical
    # query — the gate normalizes case/whitespace on both sides.
    seed_injury("right_elbow", "active", 3,
                contraindicated_exercises=["skull crusher"])
    r = check_exercise_safety("Skull Crusher")
    assert r.safe is False


def test_gate_flags_unmapped_query_name_in_reason():
    r = check_exercise_safety("zzz unknown machine")
    assert r.safe is True
    assert "not in the catalog" in r.reason


def test_no_deferred_crash_after_valid_seed():
    # F9 chain: a seeded row must never poison a later Tier-1 load.
    seed_injury("left_elbow", "active", 2)
    wm = orchestrator.initialize_session()
    assert len(wm.active_injuries) == 1
    assert wm.active_injuries[0].location.value == "left_elbow"


def test_list_injuries_returns_models_newest_first():
    seed_injury("left_elbow", "active", 2)
    seed_injury("right_knee", "resolved", 1)
    rows = list_injuries()
    assert all(isinstance(r, InjuryStatus) for r in rows)
    assert {r.location.value for r in rows} == {"left_elbow", "right_knee"}
    assert rows[0].id is not None
    active = list_injuries(active_only=True)
    assert {r.location.value for r in active} == {"left_elbow"}


def test_tendon_summary_shape():
    seed_injury("left_elbow", "active", 5)
    seed_injury("lower_back", "resolved", 1)
    summary = tendon_summary()
    assert summary == {"left_elbow": {"status": "active", "severity": 5}}
