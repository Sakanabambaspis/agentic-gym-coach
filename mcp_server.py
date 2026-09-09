"""MCP server — exposes the coach tools over stdio for ANY MCP-capable runtime.

Claude Code, ZCode, Cursor, Codex CLI, Continue, etc. attach this
one server instead of per-runtime tool glue. It wraps the SAME handlers as
the CLI dispatcher (coach_tools.py) — change handlers there, never here.

Plus `coach_doctrine(topic)`: procedural disclosure over MCP — returns the
routing table, or a knowledge file's content, for runtimes that cannot read
the repo's files directly.

Run:    python mcp_server.py          (stdio transport)
Config: see docs/adapters.md and .mcp.json
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from mcp.server.mcpserver import MCPServer  # noqa: E402  (mcp 2.x: FastMCP → MCPServer)

import coach_tools  # noqa: E402

mcp = MCPServer(name="gym-coach")

# Bounded chapter delivery — routers stay light, content arrives on demand.
_MAX_DOCTRINE_CHARS = 14_000
_KNOWLEDGE = ROOT / "docs" / "knowledge"


def _run(cmd: str, args: dict) -> dict:
    """Dispatch to the shared handler; preserve the halt-and-report posture."""
    try:
        fn = coach_tools.DISPATCH[cmd]
    except KeyError:
        return {"error": f"unknown command '{cmd}'"}
    try:
        return fn(args)
    except Exception as e:  # surface the failure, never fabricate
        return {"error": type(e).__name__, "detail": str(e)}


@mcp.tool()
def coach_log_session(date: str, exercises: list[dict], phase: str | None = None,
                      post_feedback: str | None = None) -> dict:
    """Persist a training session (validated, canonicalized, anomaly-flagged).

    exercises: [{name, sets, reps[], rpe[], weight_kg[], tempo?, form_quality?, pain_flag?, notes?}] —
    arrays are per-set, equal length; weight_kg null = bodyweight/unrecorded.
    """
    return _run("log_session", {"date": date, "exercises": exercises,
                                "phase": phase, "post_feedback": post_feedback})


@mcp.tool()
def coach_safety_check(exercise: str) -> dict:
    """Deterministic injury gate: safe/unsafe + alternatives. If safe=false, the exercise MUST NOT be suggested."""
    return _run("safety_check", {"exercise": exercise})


@mcp.tool()
def coach_recovery(date: str | None = None) -> dict:
    """Heuristic 0-100 recovery score for a date (0-59 rest, 60-84 light, 85+ train)."""
    return _run("recovery", {"date": date})


@mcp.tool()
def coach_trend(muscle: str, window_days: int = 28, end_date: str | None = None) -> dict:
    """Effective hard sets, avg RPE, est 1RM (≤6-rep sets), and stall flag for a muscle group over a window."""
    return _run("trend", {"muscle": muscle, "window_days": window_days, "end_date": end_date})


@mcp.tool()
def coach_snapshot() -> dict:
    """Generate/refresh the 4-week phase snapshot (incl. block_state: time since last deload)."""
    return _run("snapshot", {})


@mcp.tool()
def coach_sessions(limit: int = 10) -> dict:
    """List recent sessions (id, date, phase, pre_recovery_score, post_feedback)."""
    return _run("sessions", {"limit": limit})


@mcp.tool()
def coach_injuries_list() -> dict:
    """Read the injury_status table (location, status, severity, contraindications, alternatives)."""
    return _run("injuries_list", {})


@mcp.tool()
def coach_injuries_seed(location: str, status: str, severity: int,
                        contraindicated_exercises: list[str] | None = None,
                        safe_alternatives: list[str] | None = None) -> dict:
    """Insert an injury record. Only when the user explicitly reports a new injury or state change."""
    return _run("injuries_seed", {"location": location, "status": status, "severity": severity,
                                  "contraindicated_exercises": contraindicated_exercises or [],
                                  "safe_alternatives": safe_alternatives or []})


@mcp.tool()
def coach_profile_get() -> dict:
    """Get the user profile (goals, training age, schedule, priorities). {profile: null} ⇒ run onboarding."""
    return _run("profile_get", {})


@mcp.tool()
def coach_profile_set(profile: dict) -> dict:
    """Create/update the user profile (validated, versioned; goal changes audited). Echo it to the user after setting."""
    return _run("profile_set", profile)


@mcp.tool()
def coach_memory_save(text: str, kind: str = "observation", tags: list[str] | None = None) -> dict:
    """Save a long-term memory note. ONLY on an explicit user command ('save this') — never auto-write."""
    return _run("memory_save", {"text": text, "kind": kind, "tags": tags or []})


@mcp.tool()
def coach_memory_search(query: str | None = None, tags: list[str] | None = None,
                        limit: int = 20) -> dict:
    """Search long-term memory notes (substring + any-tag)."""
    return _run("memory_search", {"query": query, "tags": tags, "limit": limit})


@mcp.tool()
def coach_doctrine(topic: str | None = None) -> str:
    """Procedural disclosure over MCP: list the knowledge routing table, or return a knowledge file's content.

    topic: 'index' (default) | 'training' | 'nutrition' | a file path relative
    to docs/knowledge/ (e.g. 'helms-training-pyramid/chapters/ch04-level-3-progression.md').
    """
    if topic in (None, "", "index"):
        lines = ["Knowledge routing (docs/knowledge/):"]
        for skill_dir in sorted(_KNOWLEDGE.iterdir()):
            if skill_dir.is_dir():
                lines.append(f"  {skill_dir.name}/ — {skill_dir.name}/SKILL.md (chapter + topic index)")
        lines.append("Pass a relative path (e.g. 'helms-training-pyramid/chapters/ch03-...md') to fetch content.")
        return "\n".join(lines)
    candidate = (_KNOWLEDGE / topic).resolve()
    if not str(candidate).startswith(str(_KNOWLEDGE)) or not candidate.is_file():
        return f"error: unknown doctrine topic '{topic}' — call with 'index' first"
    text = candidate.read_text(encoding="utf-8")
    if len(text) > _MAX_DOCTRINE_CHARS:
        text = text[:_MAX_DOCTRINE_CHARS] + "\n...[truncated — read the file directly for the rest]"
    return text


if __name__ == "__main__":
    mcp.run()
