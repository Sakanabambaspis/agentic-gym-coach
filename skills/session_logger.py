"""session_logger — validate + persist one gym session to DuckDB.

Flow:
  1. Pydantic already validated `data` on construction (caller's job).
  2. Resolve `phase` if the user didn't set it (current phase from latest
     snapshot; default to internship_maintenance when none exists) so the
     user never has to tag a phase.
  3. Canonicalize each exercise: fill muscle_group from the catalog and
     store the canonical name (raw text survives in log.md).
  4. Raise anomaly flags: pain_flag, form_quality<3, unmapped exercise.
  5. INSERT into sessions, RETURNING the generated id.

Contract: <50ms. Never fabricates fields the user didn't provide.
"""

from __future__ import annotations

from datetime import date

from models import AnomalyFlag, ExerciseModel, LogConfirmation, PhaseType, SessionInput, canonicalize

from .init import get_duckdb

# ponytail: baseline phase when none is known. Not a fabricated measurement —
# it's the spec's maintenance phase, the safe default before any snapshot.
_DEFAULT_PHASE = PhaseType.internship_maintenance


def _resolve_phase(data: SessionInput) -> PhaseType:
    if data.phase is not None:
        return data.phase
    cur = get_duckdb().execute(
        "SELECT phase FROM phase_snapshots ORDER BY snapshot_date DESC LIMIT 1"
    ).fetchone()
    if cur and cur[0] is not None:
        return PhaseType(cur[0])  # DuckDB returns enum as plain string
    return _DEFAULT_PHASE


def _canonicalize_exercises(data: SessionInput) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []
    for ex in data.exercises:
        can_name, mg, needs_review = canonicalize(ex.name)
        if ex.muscle_group is None:
            ex.muscle_group = mg
        ex.name = can_name
        if needs_review:
            flags.append(AnomalyFlag(
                code="needs_review",
                detail=f"unmapped exercise '{ex.name}' guessed as {ex.muscle_group.value}",
            ))
        if ex.pain_flag:
            flags.append(AnomalyFlag(code="pain_flag", detail=f"{ex.name}: pain during exercise"))
        if ex.form_quality < 3:
            flags.append(AnomalyFlag(
                code="form_quality_low",
                detail=f"{ex.name}: form_quality={ex.form_quality} (volume -50% downstream)",
            ))
    return flags


def _to_struct_list(exercises: list[ExerciseModel]) -> list[dict]:
    return [
        {
            "name": ex.name,
            "muscle_group": ex.muscle_group.value if ex.muscle_group else None,
            "sets": ex.sets,
            "reps": ex.reps,
            "rpe": ex.rpe,
            "weight_kg": ex.weight_kg,
            "tempo": ex.tempo,
            "form_quality": ex.form_quality,
            "pain_flag": ex.pain_flag,
            "notes": ex.notes,
        }
        for ex in exercises
    ]


def log_session(data: SessionInput) -> LogConfirmation:
    phase = _resolve_phase(data)
    flags = _canonicalize_exercises(data)

    structs = _to_struct_list(data.exercises)
    row = get_duckdb().execute(
        """
        INSERT INTO sessions (date, phase, pre_recovery_score, exercises, post_feedback)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id, date
        """,
        [data.date, phase.value, data.pre_recovery_score, structs, data.post_feedback],
    ).fetchone()

    session_id, session_date = row[0], row[1]
    return LogConfirmation(
        session_id=session_id,
        date=session_date,
        anomaly_flags=flags,
        message="session logged",
    )