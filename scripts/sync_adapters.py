"""sync_adapters — render the canonical coach prompt into runtime agent files.

docs/COACH_PROMPT.md is the single source of the Coach persona. This script
renders it (plus per-runtime frontmatter) into each adapter's agent file:

    .opencode/agents/coach.md   <- opencode native agent

Adding a runtime = add a (frontmatter, target_path) entry in ADAPTERS below,
then run `python scripts/sync_adapters.py`. Use `--check` to verify rendered
files are in sync (exits 1 on drift — run it after editing COACH_PROMPT.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_PROMPT = _REPO / "docs" / "COACH_PROMPT.md"

_OPENCODE_FRONTMATTER = """---
description: Your personal gym coach — onboards goals, logs sessions, analyzes trends, plans training and nutrition from vendored professional knowledge, while respecting injuries. Switch to this agent with Tab to log sessions or ask training/nutrition questions.
mode: primary
permission:
  edit: deny
  bash: allow
  read: allow
  glob: allow
  grep: allow
  list: allow
  skill: allow
  task: allow
  todowrite: allow
  coach_log_session: allow
  coach_safety_check: allow
  coach_recovery: allow
  coach_trend: allow
  coach_snapshot: allow
  coach_sessions: allow
  coach_injuries_list: allow
  coach_injuries_seed: allow
  coach_ingest: allow
  coach_profile_get: allow
  coach_profile_set: allow
  coach_memory_save: allow
  coach_memory_search: allow
  webfetch: deny
  external_directory: deny
---

"""

ADAPTERS: list[tuple[str, Path]] = [
    (_OPENCODE_FRONTMATTER, _REPO / ".opencode" / "agents" / "coach.md"),
]


def render() -> dict[Path, str]:
    body = _PROMPT.read_text(encoding="utf-8")
    return {target: frontmatter + body for frontmatter, target in ADAPTERS}


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    rendered = render()
    drifted = False
    for target, content in rendered.items():
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == content:
            print(f"ok       {target.relative_to(_REPO)}")
            continue
        drifted = True
        if check_only:
            print(f"DRIFT    {target.relative_to(_REPO)} (edit COACH_PROMPT.md, then re-run without --check)")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"rendered {target.relative_to(_REPO)}")
    return 1 if (check_only and drifted) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
