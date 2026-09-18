"""intake — the standardized assessment scanner (one checklist, one mode).

assess_intake() scans stored state (user_profiles payload, injury_status,
session history) against models.intake.INTAKE_CHECKLIST and reports, per
field, what is collected vs missing, plus per-domain readiness. It NEVER
writes and never invents values — the coach cites collected values (asking
"still accurate?"), asks for missing ones in checklist order, and applies
the soft per-domain gates: no training/nutrition plan volunteered without
its gating data; a provisional plan with explicit limitations only when the
user insists (COACH_PROMPT "Standardized intake assessment").

There are no modes: the same scan serves a first-ever user (everything
missing), a returning user (old values cited back for confirmation), and a
mid-program check. weeks_since_last_session (threshold: the labeled
heuristic skills.snapshot.REASSESSMENT_GAP_WEEKS) is the staleness nudge
for the confirm-present step, not a switch.

Contract: deterministic, offline, read-only.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any

from models import (
    INTAKE_CHECKLIST,
    FieldReport,
    FieldStatus,
    GateDomain,
    IntakeReport,
    UserProfile,
)

from .injuries import InjuryStatus, list_injuries
from .profile import get_profile
from .snapshot import session_gap


def _is_present(value: Any) -> bool:
    """Presence = a real answer was stored. False/0 are answers; blanks aren't."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True  # bools, ints, floats, enums, dates — a stored value is an answer


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):  # pydantic (Goal, ...)
        return value.model_dump(mode="json")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _stored_value(storage: str, profile: UserProfile | None,
                  injuries: list[InjuryStatus]) -> tuple[Any, bool]:
    """Resolve one checklist storage path → (raw value, present?).

    List-typed profile fields (dislikes, concurrent sports, priority
    muscles, …) are present whenever a profile exists: an empty list is a
    valid stored answer ("asked, nothing applies"), and strict
    missing-detection on them could never complete. The one exception is
    `goals`: an empty goal list is indistinguishable from never-asked, and
    'no specific goal' has its own vocabulary value (general_fitness), so
    goals stay strictly presence-checked.
    """
    if storage == "injury_status":
        return injuries, _is_present(injuries)
    if not storage.startswith("profile."):
        raise ValueError(f"checklist storage path not understood: {storage}")
    value = getattr(profile, storage.split(".", 1)[1]) if profile else None
    if isinstance(value, (list, tuple)) and storage != "profile.goals":
        return value, profile is not None
    return value, _is_present(value)


def assess_intake(today: date | None = None) -> IntakeReport:
    """Scan stored state against the bucket list. Read-only; never guesses."""
    today = today or date.today()
    profile = get_profile()
    injuries = list_injuries()
    gap = session_gap(today)

    reports: list[FieldReport] = []
    for f in INTAKE_CHECKLIST:
        value, present = _stored_value(f.storage, profile, injuries)
        reports.append(FieldReport(
            **f.model_dump(),
            status=FieldStatus.collected if present else FieldStatus.missing,
            value=_json_safe(value) if present else None,
        ))

    missing_by_gate: dict[str, list[str]] = {"training": [], "nutrition": []}
    for r in reports:
        if r.status is not FieldStatus.missing or not r.blocks_gate:
            continue
        if r.gates in (GateDomain.training, GateDomain.both):
            missing_by_gate["training"].append(r.name)
        if r.gates in (GateDomain.nutrition, GateDomain.both):
            missing_by_gate["nutrition"].append(r.name)

    return IntakeReport(
        fields=reports,
        weeks_since_last_session=gap["weeks_since_last_session"],
        training_ready=not missing_by_gate["training"],
        nutrition_ready=not missing_by_gate["nutrition"],
        missing=[r.name for r in reports if r.status is FieldStatus.missing],
        missing_by_gate=missing_by_gate,
    )
