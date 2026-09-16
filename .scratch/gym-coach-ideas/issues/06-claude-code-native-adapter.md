# 06 — Claude Code native adapter

**What to build:** Claude Code currently reaches the coach via `.mcp.json` +
AGENTS.md read-order. This ticket registers a native adapter so the sync
script renders the canonical coach prompt (plus frontmatter) into a Claude
Code agent file, letting Claude Code run the coach as a subagent as well.
The `ADAPTERS` list is already an empty extension point designed for exactly
this; `--check` drift mode must cover the new target.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `ADAPTERS` gains one entry; running the sync script creates the native
      agent file with correct frontmatter
- [ ] Rendered file preserves the non-negotiable rules verbatim (safety
      gate, memory write policy, never-edit-code restriction)
- [ ] `--check` passes right after sync and reports drift after a manual
      edit of the rendered file
- [ ] Deterministic render (same input → byte-identical output), covered by
      a test; MCP-only setups are completely unaffected
