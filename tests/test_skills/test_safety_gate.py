"""safety_gate unit tests — deterministic ban + alternatives + empty-table safe."""

from skills.init import get_duckdb
from skills.safety_gate import check_exercise_safety


def _seed_injury(loc="left_elbow", status="active", contra=None, alts=None):
    d = get_duckdb()
    d.execute(
        """
        INSERT INTO injury_status (location, status, severity,
                                    contraindicated_exercises, safe_alternatives)
        VALUES (?, ?, 5, ?, ?)
        """,
        [loc, status, contra or ["Skull Crusher"], alts or ["Tricep Pushdown"]],
    )


def test_empty_injury_table_is_safe():
    r = check_exercise_safety("Skull Crusher")
    assert r.safe is True
    assert r.alternatives == []


def test_contraindicated_exercise_is_unsafe_with_alternatives():
    _seed_injury(contra=["Skull Crusher"], alts=["Tricep Pushdown"])
    r = check_exercise_safety("Dumbbell Skull Crusher")  # alias -> Skull Crusher
    assert r.safe is False
    assert r.exercise == "Skull Crusher"
    assert "Tricep Pushdown" in r.alternatives


def test_non_contraindicated_stays_safe_with_active_injury():
    _seed_injury(contra=["Skull Crusher"])
    r = check_exercise_safety("Incline Bench Press")
    assert r.safe is True


def test_resolved_injury_does_not_block():
    _seed_injury(loc="right_elbow", status="resolved", contra=["Skull Crusher"])
    r = check_exercise_safety("Skull Crusher")
    assert r.safe is True  # resolved -> ignored


def test_alias_canonicalized_before_match():
    _seed_injury(contra=["Skull Crusher"], alts=["Tricep Pushdown"])
    r = check_exercise_safety("Dumbbell Skull Crusher")
    assert r.safe is False  # alias matches canonical banned name