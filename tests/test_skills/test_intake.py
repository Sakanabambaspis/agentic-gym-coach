"""intake unit tests — bucket-list scan, per-domain soft gates, drift guards."""

import json
import re
from datetime import date, timedelta

from models import (
    INTAKE_CHECKLIST,
    ActivityLevel,
    ExerciseModel,
    FieldStatus,
    Goal,
    GoalKind,
    MuscleGroup,
    SessionInput,
    Sex,
    SocialSupport,
    StressLevel,
    TrackingTier,
    TrainingAge,
    UserProfile,
)
from skills.injuries import seed_injury
from skills.intake import assess_intake
from skills.profile import set_profile
from skills.session_logger import log_session

TODAY = date.today()


def _full_profile() -> UserProfile:
    """Every checklist-backed profile field set — the scan must call it ready."""
    return UserProfile(
        display_name="Test User",
        goals=[Goal(kind=GoalKind.hypertrophy, target_muscles=[MuscleGroup.quads])],
        priority_muscles=[MuscleGroup.quads],
        training_age=TrainingAge.intermediate,
        days_per_week=4,
        life_stress=StressLevel.moderate,
        liked_exercises=["Squat"],
        disliked_exercises=["Crunch"],
        concurrent_sports=["climbing"],
        rpe_calibrated=True,
        has_tested_maxes=False,
        session_length_min=60,
        equipment_access="home",
        sex=Sex.female,
        age_years=30,
        bodyweight_kg=60.0,
        bodyfat_pct=25.0,
        activity_level=ActivityLevel.active,
        diet_phase_duration_weeks=10,
        tracking_tier=TrackingTier.better,
        meals_per_day=4,
        eating_out_per_week=1,
        alcohol_per_week=2,
        social_support=SocialSupport.supportive,
        supplement_notes="creatine 5g",
        caffeine_intake="1 coffee/day",
        family_diabetes_history=False,
        pcos=False,
        oligomenorrhea=False,
    )


def _training_only_profile() -> UserProfile:
    """Both-gated + training-gated fields only — training ready, nutrition not."""
    return UserProfile(
        goals=[Goal(kind=GoalKind.strength)],
        priority_muscles=[],
        training_age=TrainingAge.novice,
        days_per_week=3,
        life_stress=StressLevel.low,
        liked_exercises=["Bench Press"],
        disliked_exercises=[],
        concurrent_sports=[],
        rpe_calibrated=False,
        has_tested_maxes=True,
        session_length_min=45,
        equipment_access="minimal",
    )


def _names(report):
    return {f.name for f in report.fields}


def test_empty_database_reports_everything_missing():
    report = assess_intake(today=TODAY)
    assert _names(report) == {f.name for f in INTAKE_CHECKLIST}
    assert all(f.status is FieldStatus.missing for f in report.fields)
    assert report.missing == [f.name for f in INTAKE_CHECKLIST]  # checklist order
    assert report.training_ready is False
    assert report.nutrition_ready is False
    assert report.weeks_since_last_session is None  # no sessions at all
    assert report.missing_by_gate["training"] and report.missing_by_gate["nutrition"]


def test_full_intake_is_ready_for_both_domains():
    set_profile(_full_profile())
    seed_injury("left_elbow", "resolving", 3)
    log_session(SessionInput(date=TODAY - timedelta(days=1), exercises=[]))
    report = assess_intake(today=TODAY)
    assert report.missing == []
    assert report.training_ready is True
    assert report.nutrition_ready is True
    assert report.weeks_since_last_session == 0.1
    assert report.missing_by_gate == {"training": [], "nutrition": []}


def test_training_only_profile_gates_nutrition_not_training():
    set_profile(_training_only_profile())
    report = assess_intake(today=TODAY)
    assert report.training_ready is True
    assert report.nutrition_ready is False
    assert report.missing_by_gate["training"] == []
    assert "bodyweight_kg" in report.missing_by_gate["nutrition"]
    # both-gated fields were satisfied, so they gate nothing
    assert "goals" not in report.missing_by_gate["nutrition"]


def test_injury_table_satisfies_injuries_field_without_profile():
    seed_injury("lower_back", "chronic_baseline", 2)
    report = assess_intake(today=TODAY)
    injuries = next(f for f in report.fields if f.name == "injuries")
    assert injuries.status is FieldStatus.collected
    assert injuries.value  # the stored rows, JSON-safe
    assert "injuries" not in report.missing


def test_absent_injury_rows_are_missing_not_assumed_clear():
    report = assess_intake(today=TODAY)
    assert "injuries" in report.missing


def test_explicit_false_is_collected_not_missing():
    set_profile(UserProfile(family_diabetes_history=False))
    report = assess_intake(today=TODAY)
    field = next(f for f in report.fields if f.name == "family_diabetes_history")
    assert field.status is FieldStatus.collected
    assert field.value is False


def test_report_serializes_to_json():
    set_profile(_full_profile())
    report = assess_intake(today=TODAY)
    payload = json.loads(report.model_dump_json())  # enums/goals must be JSON-safe
    goals = next(f for f in payload["fields"] if f["name"] == "goals")
    assert goals["value"][0]["kind"] == "hypertrophy"


def test_every_checklist_field_cites_a_source_or_heuristic():
    # Drift guard: an unsourced field is exactly the v1 mistake this repo removed.
    for f in INTAKE_CHECKLIST:
        ok = f.source.startswith("HEURISTIC") or re.search(r"ch0[1-9]", f.source)
        assert ok, f


def test_checklist_storage_paths_resolve_against_profile_schema():
    for f in INTAKE_CHECKLIST:
        if f.storage == "injury_status":
            continue
        assert f.storage.startswith("profile."), f
        assert f.storage.split(".", 1)[1] in UserProfile.model_fields, f


def test_profile_without_goals_reports_missing_and_closes_both_gates():
    # Empty goals is "never asked", not an answer — 'no specific goal' is
    # recorded as kind=general_fitness. Both gates must stay closed.
    set_profile(UserProfile(
        training_age=TrainingAge.novice,
        days_per_week=3,
        bodyweight_kg=70.0,
        sex=Sex.male,
        activity_level=ActivityLevel.active,
    ))
    report = assess_intake(today=TODAY)
    goals = next(f for f in report.fields if f.name == "goals")
    assert goals.status is FieldStatus.missing
    assert report.training_ready is False
    assert report.nutrition_ready is False
    assert "goals" in report.missing_by_gate["training"]
    assert "goals" in report.missing_by_gate["nutrition"]


def test_unanswered_equipment_access_is_missing_not_default_full_gym():
    set_profile(UserProfile(sex=Sex.male))  # any profile; equipment never answered
    report = assess_intake(today=TODAY)
    equipment = next(f for f in report.fields if f.name == "equipment_access")
    assert equipment.status is FieldStatus.missing
    assert equipment.value is None
