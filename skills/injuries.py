"""injuries — the single owner of the injury_status table (safety source of truth).

Every read and write of injury_status goes through here; no other module
knows the table's schema (previously spread across five modules). Writes are
validated and canonicalized:

- location/status/severity are constructed as models.InjuryStatus, so an
  out-of-vocabulary value or out-of-range severity fails at write time with
  a standard validation error — instead of being stored and crashing a later
  Tier-1 load far from the faulty write (adversarial F2/F9).
- every contraindicated/alternative exercise name is canonicalized via the
  exercise catalog, so a ban written as the user said it is stored under the
  same name the safety gate queries. Names the catalog can't map are stored
  verbatim but returned in `needs_review` — the coach must confirm them with
  the user before trusting the gate on them (the known fail-open residual,
  adversarial F1 / audit Q4).
"""

from __future__ import annotations

from typing import Any

from models import InjurySeedResult, InjuryState, InjuryStatus, PainLocation, canonicalize

from .init import get_duckdb

_COLS = "location, status, severity, contraindicated_exercises, safe_alternatives"


def _row_to_model(row: tuple, *, with_id: bool = False) -> InjuryStatus:
    loc, st, sev, contra, alts = row[-5:]
    return InjuryStatus(
        id=row[0] if with_id else None,
        location=PainLocation(loc),
        status=InjuryState(st),
        severity=sev,
        contraindicated_exercises=list(contra or []),
        safe_alternatives=list(alts or []),
    )


def _canonicalize_names(names: list[str]) -> tuple[list[str], list[str]]:
    """Map names through the exercise catalog → (stored, needs_review)."""
    stored, review = [], []
    for name in names:
        can, _mg, needs_review = canonicalize(name)
        stored.append(can)
        if needs_review:
            review.append(can)
    return stored, review


def list_injuries(active_only: bool = False) -> list[InjuryStatus]:
    """Injury rows as models, newest first (`active_only` skips resolved)."""
    sql = f"SELECT id, {_COLS} FROM injury_status"
    if active_only:
        sql += " WHERE status <> 'resolved'"
    sql += " ORDER BY updated_at DESC"
    return [_row_to_model(r, with_id=True) for r in get_duckdb().execute(sql).fetchall()]


def get_active_injuries() -> list[InjuryStatus]:
    """Non-resolved injuries — the Tier-1 working-memory slice."""
    return list_injuries(active_only=True)


def seed_injury(location: str, status: str, severity: int,
                contraindicated_exercises: list[str] | None = None,
                safe_alternatives: list[str] | None = None) -> InjurySeedResult:
    """Validate, canonicalize, and insert one injury row.

    Raises pydantic ValidationError on out-of-vocabulary location/status or
    out-of-range severity — nothing is written. Canonical alias hits are
    stored under the canonical name; unmapped names are stored verbatim and
    listed in `needs_review` for user confirmation.
    """
    injury = InjuryStatus(
        location=location, status=status, severity=severity,
        contraindicated_exercises=list(contraindicated_exercises or []),
        safe_alternatives=list(safe_alternatives or []),
    )
    stored_contra, review = _canonicalize_names(injury.contraindicated_exercises)
    stored_alts, alt_review = _canonicalize_names(injury.safe_alternatives)

    get_duckdb().execute(
        f"INSERT INTO injury_status ({_COLS}) VALUES (?, ?, ?, ?, ?)",
        [injury.location.value, injury.status.value, injury.severity,
         stored_contra, stored_alts],
    )
    stored = injury.model_copy(update={
        "contraindicated_exercises": stored_contra,
        "safe_alternatives": stored_alts,
    })
    return InjurySeedResult(injury=stored, needs_review=sorted(set(review + alt_review)))


def contraindication_hits(canonical_name: str) -> list[tuple[str, str, list[str]]]:
    """Non-resolved injury rows whose contraindicated_exercises contain the
    name — matched case/whitespace-insensitively, so a ban stored as the user
    said it ("skull crusher") still blocks the canonical query ("Skull
    Crusher"). The safety gate's only sanctioned read of injury_status."""
    return get_duckdb().execute(
        """
        SELECT location, status, safe_alternatives
        FROM injury_status
        WHERE status <> 'resolved'
          AND list_contains(
                list_transform(contraindicated_exercises, s -> trim(lower(s))),
                trim(lower(?)))
        """,
        [canonical_name],
    ).fetchall()


def tendon_summary() -> dict[str, Any]:
    """{location: {status, severity}} for non-resolved injuries (snapshot anchor)."""
    rows = get_duckdb().execute(
        "SELECT location, status, severity FROM injury_status WHERE status <> 'resolved'"
    ).fetchall()
    return {loc: {"status": st, "severity": sev} for loc, st, sev in rows}
