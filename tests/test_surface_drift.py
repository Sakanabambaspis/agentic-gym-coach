"""Surface-drift guard (audit T5c) — AGENTS.md's three-places rule has no
manual check, and both drift incidents found in the tree (ghost coach_ingest,
wrong recovery bands in a docstring) entered through the persona/docstring
side. These tests make that drift fail CI.
"""

import inspect
import re
from pathlib import Path

import coach_tools
import mcp_server

_REPO = Path(__file__).resolve().parent.parent


def test_every_dispatch_command_has_mcp_wrapper():
    for cmd in coach_tools.DISPATCH:
        assert hasattr(mcp_server, f"coach_{cmd}"), cmd


def test_mcp_wrapper_defaults_come_from_coach_tools():
    """Defaults are single-sourced in coach_tools; wrappers import them."""
    cases = [
        ("coach_trend", "window_days", coach_tools.DEFAULT_TREND_WINDOW_DAYS),
        ("coach_sessions", "limit", coach_tools.DEFAULT_SESSIONS_LIMIT),
        ("coach_memory_search", "limit", coach_tools.DEFAULT_SEARCH_LIMIT),
        ("coach_memory_save", "kind", coach_tools.DEFAULT_MEMORY_KIND),
    ]
    for tool, param, expected in cases:
        default = inspect.signature(getattr(mcp_server, tool)).parameters[param].default
        assert default == expected, f"{tool}.{param} drifted from coach_tools"


def test_recovery_docstring_matches_code_bands():
    # M2: the docstring once taught "0-59 rest, 60-84 light, 85+ train".
    doc = inspect.getdoc(mcp_server.coach_recovery) or ""
    assert "deload" in doc and "autoregulate" in doc and "push-ready" in doc
    assert "60-84" not in doc and "85+" not in doc


def test_persona_documents_only_real_tools():
    text = (_REPO / "docs" / "COACH_PROMPT.md").read_text(encoding="utf-8")
    assert "coach_ingest" not in text  # M1: the ghost tool must stay gone
    for name in sorted(set(re.findall(r"coach_[a-z_]+", text))):
        if name in ("coach_", "coach_doctrine"):  # generic mention / documented MCP-only asymmetry
            continue
        assert hasattr(mcp_server, name), f"persona references nonexistent tool {name}"


def test_persona_exposes_pre_recovery_score():
    # M3: the sessions.pre_recovery_score column was dead from the MCP surface.
    text = (_REPO / "docs" / "COACH_PROMPT.md").read_text(encoding="utf-8")
    assert "pre_recovery_score" in text
    sig = inspect.signature(mcp_server.coach_log_session)
    assert "pre_recovery_score" in sig.parameters
