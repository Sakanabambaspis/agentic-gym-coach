"""profile unit tests — roundtrip, history append, goal-change audit, priorities."""

from models import (
    Goal, GoalKind, MuscleGroup, PhysiqueTarget, TrainingAge, UserProfile,
)
from skills.init import get_duckdb
from skills.profile import derive_priority_muscles, get_profile, set_profile


def _profile(**over):
    base = dict(
        goals=[Goal(kind=GoalKind.hypertrophy, physique_target=PhysiqueTarget.athletic,
                    target_muscles=[MuscleGroup.side_delt])],
        training_age=TrainingAge.intermediate,
        days_per_week=4,
        priority_muscles=[MuscleGroup.rear_delt],
    )
    base.update(over)
    return UserProfile(**base)


def test_get_profile_empty_returns_none():
    assert get_profile() is None


def test_set_and_get_roundtrip():
    p = set_profile(_profile())
    got = get_profile()
    assert got is not None
    assert got.training_age == TrainingAge.intermediate
    assert got.goals[0].kind == GoalKind.hypertrophy
    assert got.goals[0].physique_target == PhysiqueTarget.athletic
    assert got.priority_muscles == [MuscleGroup.rear_delt]
    assert p.updated_at is not None


def test_set_profile_appends_history():
    set_profile(_profile())
    set_profile(_profile(days_per_week=5))
    n = get_duckdb().execute("SELECT count(*) FROM user_profiles").fetchone()[0]
    assert n == 2
    assert get_profile().days_per_week == 5  # latest wins


def test_goal_change_writes_decision_log():
    set_profile(_profile())
    set_profile(_profile(goals=[
        Goal(kind=GoalKind.fat_loss, physique_target=PhysiqueTarget.ripped)
    ]))
    row = get_duckdb().execute(
        "SELECT event_type, trigger_signal FROM decision_log "
        "WHERE event_type='goal_change' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    assert "fat_loss" in row[1]


def test_non_goal_change_no_audit_row():
    set_profile(_profile())
    set_profile(_profile(days_per_week=6))  # same goals
    n = get_duckdb().execute(
        "SELECT count(*) FROM decision_log WHERE event_type='goal_change'"
    ).fetchone()[0]
    assert n == 0


def test_derive_priority_muscles():
    assert derive_priority_muscles(None) == []
    # declared priorities come first, goal targets appended
    p = _profile()
    assert derive_priority_muscles(p) == [MuscleGroup.rear_delt, MuscleGroup.side_delt]
    # no declared priorities -> goal targets only
    p2 = _profile(priority_muscles=[])
    assert derive_priority_muscles(p2) == [MuscleGroup.side_delt]
    # nothing declared anywhere -> balanced (empty)
    p3 = _profile(priority_muscles=[], goals=[])
    assert derive_priority_muscles(p3) == []
