"""profile — validated user profile: goals, training age, schedule, priorities.

The profile is the v2 replacement for v1's hardcoded user assumptions: the
orchestrator derives priority muscles from it, the snapshot targets it, and
goal changes are audited to decision_log (a goal change is the biggest plan
modification there is).

Storage: append-only rows in user_profiles (latest row = current). Every
set_profile() writes a new row, so goal history is preserved ("why did we
prioritize X in June?").

Contract: deterministic, offline. get_profile() returns None when no profile
exists — callers must surface onboarding, never invent defaults.
"""

from __future__ import annotations

from datetime import datetime, timezone

from models import Goal, UserProfile

from .init import get_duckdb


def get_profile() -> UserProfile | None:
    """Latest profile row, or None (⇒ the coach must run onboarding)."""
    row = get_duckdb().execute(
        "SELECT payload FROM user_profiles ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    p = UserProfile.model_validate_json(row[0])
    return p


def set_profile(profile: UserProfile) -> UserProfile:
    """Append a new profile version; audit goal changes to decision_log."""
    prev = get_profile()
    profile = profile.model_copy(update={"updated_at": datetime.now(timezone.utc)})
    get_duckdb().execute(
        "INSERT INTO user_profiles (updated_at, payload) VALUES (?, ?)",
        [profile.updated_at, profile.model_dump_json()],
    )
    if prev is not None and _goals_key(prev.goals) != _goals_key(profile.goals):
        removed = [g.kind.value for g in prev.goals if g not in profile.goals]
        added = [g.kind.value for g in profile.goals if g not in prev.goals]
        get_duckdb().execute(
            """
            INSERT INTO decision_log (event_type, trigger_signal, reasoning_chain,
                                      alternative_rejected, future_validation_tag)
            VALUES ('goal_change', ?, ?, ?, ?)
            """,
            [
                f"goal change: removed={removed or 'none'} added={added or 'none'}",
                "user-declared goal update during coach session",
                "keeping prior goals against user intent",
                "re-run phase snapshot 4 weeks after change; compare trend",
            ],
        )
    return profile


def derive_priority_muscles(profile: UserProfile | None) -> list:
    """Priority muscles: declared > goal targets > [] (balanced programming).

    Returns MuscleGroup values in stable order (declared order first, then
    any goal target muscles not already present).
    """
    if profile is None:
        return []
    out = list(profile.priority_muscles)
    for g in profile.goals:
        for m in g.target_muscles:
            if m not in out:
                out.append(m)
    return out


def _goals_key(goals: list[Goal]) -> list[str]:
    # Sorted kind+target signature — ignores cosmetic field edits.
    return sorted(f"{g.kind.value}:{','.join(m.value for m in g.target_muscles)}" for g in goals)
