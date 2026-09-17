"""coach_tools dispatcher contract — error vocabulary (T8), strict int args
(F6/F7), boundary guards (F3, injuries T1), single-sourced defaults (M4)."""

import pytest
from duckdb import Error as DuckDBError
from pydantic import ValidationError

import coach_tools
from coach_tools import (
    DISPATCH,
    DEFAULT_TREND_WINDOW_DAYS,
    _int_arg,
    cmd_injuries_seed,
    cmd_profile_set,
    cmd_sessions,
    cmd_trend,
    error_payload,
)


# --- error vocabulary -------------------------------------------------------

def test_input_errors_map_to_invalid_input():
    p = error_payload(ValueError("bad muscle"))
    assert p == {"error": "invalid_input", "exception": "ValueError", "detail": "bad muscle"}


def test_keyerror_and_attributeerror_map_to_invalid_input():
    assert error_payload(KeyError("exercise"))["error"] == "invalid_input"
    assert error_payload(AttributeError("'int' has no strip"))["error"] == "invalid_input"


def test_db_errors_map_to_db_and_unknown_to_internal():
    assert error_payload(DuckDBError("lock"))["error"] == "db"
    assert error_payload(RuntimeError("boom"))["error"] == "internal"


# --- strict integer arguments (adversarial F5/F6/F7) ------------------------

def test_int_arg_rejects_strings_floats_bools():
    with pytest.raises(ValueError, match="integer"):
        _int_arg({"n": "28"}, "n", 10)
    with pytest.raises(ValueError, match="integer"):
        _int_arg({"n": 3.7}, "n", 10)
    with pytest.raises(ValueError, match="integer"):
        _int_arg({"n": True}, "n", 10)


def test_int_arg_enforces_bounds():
    with pytest.raises(ValueError, match=">= 1"):
        _int_arg({"n": -28}, "n", 28, minimum=1)
    with pytest.raises(ValueError, match="<= 3650"):
        _int_arg({"n": 4000}, "n", 28, maximum=3650)
    assert _int_arg({}, "n", 7) == 7  # default path untouched


def test_trend_window_mirrors_mcp_validation():
    with pytest.raises(ValueError):
        cmd_trend({"muscle": "quads", "window_days": "28"})
    with pytest.raises(ValueError):
        cmd_trend({"muscle": "quads", "window_days": -28})  # was a silent empty report


def test_trend_default_still_applies():
    out = cmd_trend({"muscle": "quads"})
    assert out["window_days"] == DEFAULT_TREND_WINDOW_DAYS
    assert out["effective_volume"] == 0.0


def test_sessions_limit_zero_ok_negative_rejected():
    assert cmd_sessions({"limit": 0}) == []
    with pytest.raises(ValueError):
        cmd_sessions({"limit": -1})  # was a DuckDB BinderException shape


# --- boundary guards --------------------------------------------------------

def test_empty_profile_refused_and_not_written():
    with pytest.raises(ValueError, match="empty"):
        cmd_profile_set({})
    from skills.profile import get_profile
    assert get_profile() is None  # onboarding gate stays armed (F3)


def test_injuries_seed_via_dispatch_canonicalizes_and_gates():
    # The audit's done-when: messy spelling seeded through the real tool, then
    # the gate blocks the canonical query.
    out = cmd_injuries_seed({
        "location": "left_elbow", "status": "active", "severity": "4",
        "contraindicated_exercises": ["Dumbbell Skull Crusher"],
        "safe_alternatives": ["Tricep Pushdown"],
    })
    assert out["ok"] is True
    assert out["needs_review"] == []
    assert out["injury"]["contraindicated_exercises"] == ["Skull Crusher"]
    from skills.safety_gate import check_exercise_safety
    r = check_exercise_safety("Skull Crusher")
    assert r.safe is False


def test_injuries_seed_via_dispatch_rejects_bad_vocab():
    with pytest.raises(ValidationError):
        DISPATCH["injuries_seed"]({"location": "elbow", "status": "active", "severity": 3})
