"""safety_gate — deterministic exercise safety check against injury_status.

Flow:
  1. Canonicalize the input exercise name (so aliases hit the ban list).
  2. Query injury_status for active/resolving/chronic_baseline rows whose
     contraindicated_exercises array contains that canonical name.
  3. If a match: unsafe + return that row's safe_alternatives. The caller
     MUST NOT suggest the exercise; offer the alternatives.
  4. Else: safe.

Contract: deterministic, <10ms. Never assumes tendon state — only the
injury_status table is the source of truth. An empty table ⇒ everything safe.
"""

from __future__ import annotations

from models import SafetyResult, canonicalize

from .init import get_duckdb


def check_exercise_safety(exercise: str) -> SafetyResult:
    can_name, _mg, _review = canonicalize(exercise)
    rows = get_duckdb().execute(
        """
        SELECT location, status, safe_alternatives
        FROM injury_status
        WHERE status <> 'resolved'
          AND list_contains(contraindicated_exercises, ?)
        """,
        [can_name],
    ).fetchall()
    if not rows:
        return SafetyResult(exercise=can_name, safe=True, reason="no active contraindication")
    location, status, alts = rows[0]
    return SafetyResult(
        exercise=can_name,
        safe=False,
        alternatives=list(alts) if alts else [],
        reason=f"{location}: {status} — exercise contraindicated",
    )