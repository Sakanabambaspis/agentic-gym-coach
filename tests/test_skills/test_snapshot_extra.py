"""snapshot edge cases — insight branches, block_state, representative-lift invariant."""

from datetime import date, timedelta

from models import ExerciseModel, MuscleGroup, SessionInput
from skills.session_logger import log_session
from skills.snapshot import REPRESENTATIVE_LIFTS, _block_state, _insight
from skills.profile import set_profile
from models import Goal, GoalKind, UserProfile

T = date(2030, 1, 10)


def test_insight_without_profile_says_so():
    insight, adjust = _insight({})
    assert "no user profile set" in insight
    assert "intake" in adjust


def test_insight_with_profile_but_no_priorities():
    set_profile(UserProfile())  # no goals, no priority_muscles
    insight, adjust = _insight({})
    assert "no priority muscles" in insight


def test_insight_flags_zero_volume_target():
    set_profile(UserProfile(
        priority_muscles=[MuscleGroup.calves],
        goals=[Goal(kind=GoalKind.hypertrophy, target_muscles=[MuscleGroup.calves])],
    ))
    insight, adjust = _insight({})  # no volume at all
    assert "no work logged for priority target calves" in insight


def test_insight_names_lowest_volume_priority_target():
    set_profile(UserProfile(
        priority_muscles=[MuscleGroup.lats, MuscleGroup.biceps],
        goals=[],
    ))
    vol = {"lats": 12.0, "biceps": 3.0}
    insight, adjust = _insight(vol)
    assert "biceps" in insight
    assert "3" in insight  # the hard-set number is cited


def test_block_state_none_without_deload_history():
    assert _block_state(T) == {"weeks_since_deload": None, "blocks_since_deload": None}


def test_block_state_counts_weeks_and_blocks_since_deload():
    log_session(SessionInput(date=T - timedelta(days=70), phase="deload", exercises=[]))
    bs = _block_state(T)
    assert bs["weeks_since_deload"] == 10.0
    assert bs["blocks_since_deload"] == 2  # 70 days // 4-week blocks


def test_representative_lifts_are_canonical_names():
    # A drift guard: snapshot 1RM lookups only work if every representative
    # lift is a canonical (alias-table) name.
    from models.exercise_catalog import _ALIAS_TO_CANONICAL
    for lift in REPRESENTATIVE_LIFTS:
        assert lift in _ALIAS_TO_CANONICAL, f"{lift} is not a canonical name"
        assert _ALIAS_TO_CANONICAL[lift][0] == lift


def test_empty_exercise_model_roundtrip_in_window():
    # hard_sets_by_muscle over an empty window must be {} (not KeyError)
    from skills.trend_analysis import hard_sets_by_muscle
    assert hard_sets_by_muscle(T - timedelta(days=7), T) == {}


# --- session_gap (ticket 02: staleness signal, heuristic threshold) ----------

def test_session_gap_none_without_any_sessions():
    from skills.snapshot import session_gap
    gap = session_gap(T)
    assert gap.weeks_since_last_session is None
    assert gap.reassessment_recommended is False


def test_session_gap_just_under_threshold_not_recommended():
    from skills.snapshot import session_gap
    log_session(SessionInput(date=T - timedelta(days=55), exercises=[]))  # 7.9w < 8w
    gap = session_gap(T)
    assert gap.weeks_since_last_session == 7.9
    assert gap.reassessment_recommended is False


def test_session_gap_at_threshold_is_recommended():
    from skills.snapshot import session_gap
    log_session(SessionInput(date=T - timedelta(days=56), exercises=[]))  # exactly 8.0w
    gap = session_gap(T)
    assert gap.weeks_since_last_session == 8.0
    assert gap.reassessment_recommended is True  # >= semantics


def test_session_gap_just_over_threshold_recommended():
    from skills.snapshot import session_gap
    log_session(SessionInput(date=T - timedelta(days=57), exercises=[]))  # 8.1w
    gap = session_gap(T)
    assert gap.weeks_since_last_session == 8.1
    assert gap.reassessment_recommended is True


def test_gap_threshold_is_the_single_configurable_constant(monkeypatch):
    import skills.snapshot as snap_mod
    from skills.snapshot import session_gap
    log_session(SessionInput(date=T - timedelta(days=55), exercises=[]))  # 7.9w
    assert session_gap(T).reassessment_recommended is False
    monkeypatch.setattr(snap_mod, "REASSESSMENT_GAP_WEEKS", 7.0)
    assert session_gap(T).reassessment_recommended is True  # one constant flips it


def test_snapshot_exposes_session_gap():
    # generate_phase_snapshot uses date.today() internally — seed relative to it.
    from skills.snapshot import generate_phase_snapshot
    today = date.today()
    log_session(SessionInput(date=today - timedelta(days=57), exercises=[]))
    snap = generate_phase_snapshot()
    assert snap.session_gap.weeks_since_last_session == 8.1
    assert snap.session_gap.reassessment_recommended is True
