"""profile edge cases — missing/empty profile, priority derivation, goal-change audit."""

from skills.init import get_duckdb
from skills.profile import derive_priority_muscles, get_profile, set_profile
from models import Goal, GoalKind, MuscleGroup, UserProfile


def test_missing_profile_is_none_and_derives_no_priorities():
    assert get_profile() is None
    assert derive_priority_muscles(None) == []


def test_profile_with_no_goals_or_priorities_derives_empty():
    set_profile(UserProfile())  # all-defaults profile
    p = get_profile()
    assert p is not None
    assert derive_priority_muscles(p) == []


def test_priority_muscles_declared_then_goal_targets_appended():
    set_profile(UserProfile(
        priority_muscles=[MuscleGroup.lats],
        goals=[Goal(kind=GoalKind.hypertrophy,
                    target_muscles=[MuscleGroup.side_delt, MuscleGroup.lats])],
    ))
    p = get_profile()
    assert derive_priority_muscles(p) == [MuscleGroup.lats, MuscleGroup.side_delt]


def test_every_set_profile_appends_a_row():
    set_profile(UserProfile(display_name="a"))
    set_profile(UserProfile(display_name="b"))
    n = get_duckdb().execute("SELECT count(*) FROM user_profiles").fetchone()[0]
    assert n == 2
    assert get_profile().display_name == "b"


def test_goal_change_is_audited_unchanged_is_not():
    set_profile(UserProfile(goals=[Goal(kind=GoalKind.hypertrophy,
                                        target_muscles=[MuscleGroup.lats])]))
    set_profile(UserProfile(goals=[Goal(kind=GoalKind.hypertrophy,
                                        target_muscles=[MuscleGroup.lats])]))  # same goals
    n0 = get_duckdb().execute(
        "SELECT count(*) FROM decision_log WHERE event_type='goal_change'").fetchone()[0]
    assert n0 == 0
    set_profile(UserProfile(goals=[Goal(kind=GoalKind.strength,
                                        target_muscles=[MuscleGroup.lats])]))
    n1 = get_duckdb().execute(
        "SELECT count(*) FROM decision_log WHERE event_type='goal_change'").fetchone()[0]
    assert n1 == 1


def test_empty_goals_to_real_goal_is_audited():
    set_profile(UserProfile())
    set_profile(UserProfile(goals=[Goal(kind=GoalKind.fat_loss)]))
    n = get_duckdb().execute(
        "SELECT count(*) FROM decision_log WHERE event_type='goal_change'").fetchone()[0]
    assert n == 1
