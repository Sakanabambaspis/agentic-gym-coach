"""Coach agent tool dispatcher.

Invoked by the MCP server (mcp_server.py) or directly from the shell:
`python coach_tools.py <cmd> <json>`.
All output is JSON to stdout. Errors print {"error": ...} and exit 1.

bash 0.5s budget per call. Skills are pure deterministic code.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _parse_date(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def cmd_log_session(args: dict):
    from models import SessionInput
    from skills.session_logger import log_session
    inp = SessionInput.model_validate(args)
    return log_session(inp).model_dump(mode="json")


def cmd_safety_check(args: dict):
    from skills.safety_gate import check_exercise_safety
    return check_exercise_safety(args["exercise"]).model_dump(mode="json")


def cmd_recovery(args: dict):
    from skills.recovery import compute_recovery_score
    d = _parse_date(args.get("date")) or date.today()
    return compute_recovery_score(d).model_dump(mode="json")


def cmd_trend(args: dict):
    from models import MuscleGroup
    from skills.trend_analysis import get_specialization_trend
    muscle = MuscleGroup(args["muscle"])
    return get_specialization_trend(
        muscle,
        window_days=int(args.get("window_days", 28)),
        end_date=_parse_date(args.get("end_date")),
    ).model_dump(mode="json")


def cmd_snapshot(args: dict):
    from skills.snapshot import generate_phase_snapshot
    return generate_phase_snapshot().model_dump(mode="json")


def cmd_sessions(args: dict):
    from skills.init import get_duckdb
    limit = int(args.get("limit", 10))
    rows = get_duckdb().execute(
        "SELECT id, date, phase, pre_recovery_score, post_feedback "
        "FROM sessions ORDER BY date DESC, created_at DESC LIMIT ?",
        [limit],
    ).fetchall()
    cols = ["id", "date", "phase", "pre_recovery_score", "post_feedback"]
    return [dict(zip(cols, r)) for r in rows]


def cmd_injuries_list(args: dict):
    from skills.init import get_duckdb
    rows = get_duckdb().execute(
        "SELECT id, location, status, severity, contraindicated_exercises, "
        "safe_alternatives, updated_at "
        "FROM injury_status ORDER BY updated_at DESC"
    ).fetchall()
    cols = ["id", "location", "status", "severity",
            "contraindicated_exercises", "safe_alternatives", "updated_at"]
    return [dict(zip(cols, r)) for r in rows]


def cmd_injuries_seed(args: dict):
    from skills.init import get_duckdb
    get_duckdb().execute(
        "INSERT INTO injury_status(location, status, severity, "
        "contraindicated_exercises, safe_alternatives) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            args["location"],
            args["status"],
            int(args["severity"]),
            args.get("contraindicated_exercises", []),
            args.get("safe_alternatives", []),
        ],
    )
    return {"ok": True, "message": f"seeded {args['location']}={args['status']}"}


def cmd_profile_get(args: dict):
    from skills.profile import get_profile
    p = get_profile()
    return p.model_dump(mode="json") if p else {"profile": None}


def cmd_profile_set(args: dict):
    from models import UserProfile
    from skills.profile import set_profile
    p = set_profile(UserProfile.model_validate(args))
    return p.model_dump(mode="json")


def cmd_memory_save(args: dict):
    from models import NoteKind
    from skills.memory import add_note
    note = add_note(
        args["text"],
        kind=NoteKind(args.get("kind", "observation")),
        tags=args.get("tags", []),
    )
    return note.model_dump(mode="json")


def cmd_memory_search(args: dict):
    from skills.memory import search_notes
    notes = search_notes(
        query=args.get("query"),
        tags=args.get("tags"),
        limit=int(args.get("limit", 20)),
    )
    return [n.model_dump(mode="json") for n in notes]


DISPATCH = {
    "log_session": cmd_log_session,
    "safety_check": cmd_safety_check,
    "recovery": cmd_recovery,
    "trend": cmd_trend,
    "snapshot": cmd_snapshot,
    "sessions": cmd_sessions,
    "injuries_list": cmd_injuries_list,
    "injuries_seed": cmd_injuries_seed,
    "profile_get": cmd_profile_get,
    "profile_set": cmd_profile_set,
    "memory_save": cmd_memory_save,
    "memory_search": cmd_memory_search,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(json.dumps({"available": list(DISPATCH)}))
        return
    cmd = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    fn = DISPATCH.get(cmd)
    if fn is None:
        print(json.dumps({"error": f"unknown command '{cmd}'", "available": list(DISPATCH)}))
        sys.exit(2)
    try:
        result = fn(args)
        if hasattr(result, "model_dump_json"):
            print(result.model_dump_json(indent=2))
        else:
            print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": type(e).__name__, "detail": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()