"""sync_adapters — render the canonical coach prompt into runtime agent files.

docs/COACH_PROMPT.md is the single source of the Coach persona. This script
renders it (plus per-runtime frontmatter) into each adapter's native agent
file. The opencode adapter was removed (MCP is the tool surface now);
ADAPTERS is therefore empty — this script is the extension point for the
next native adapter:

    ADAPTERS.append((FRONTMATTER, _REPO / ".claude" / "agents" / "coach.md"))
    python scripts/sync_adapters.py

Use `--check` to verify rendered files are in sync (exits 1 on drift — run
it after editing COACH_PROMPT.md when any adapter is registered).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_PROMPT = _REPO / "docs" / "COACH_PROMPT.md"

# (frontmatter, target_path) per native runtime adapter. MCP-only runtimes
# need no entry — they read COACH_PROMPT.md directly (see docs/adapters.md).
ADAPTERS: list[tuple[str, Path]] = []


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
