# Runtime Adapters — running the Coach anywhere

The repo is the deployment unit. The Python core (`skills/`, `coach_tools.py`,
DuckDB) is runtime-agnostic; every agent runtime attaches through MCP (the
primary surface) or the CLI. The persona lives in **`docs/COACH_PROMPT.md`**
(canonical) — point your harness's agent at it. The former opencode native
adapter (`.opencode/`, `opencode.json`) was removed; opencode-class runtimes
attach like everything else, via MCP.

## One-time setup (all runtimes)

```bash
uv venv .venv && uv pip install -r requirements.txt
alembic upgrade head        # bootstrap data/gym_coach.duckdb
```

## MCP-capable runtimes (Claude Code, ZCode, Cursor, Codex CLI, Continue, …)

`mcp_server.py` exposes all 12 coach tools + `coach_doctrine` (procedural
disclosure over MCP) over stdio. All runtimes share this one server.

**Claude Code** — repo-root `.mcp.json` is picked up automatically (or
`claude mcp add gym-coach -- .venv/bin/python mcp_server.py`). For the
persona, create a subagent (`.claude/agents/coach.md`) whose body is
`docs/COACH_PROMPT.md` — or register it in `scripts/sync_adapters.py`'s
`ADAPTERS` list and run the script to render it automatically.

**ZCode** — add the server in your workspace MCP configuration pointing at
`<repo>/.venv/bin/python mcp_server.py` (working directory = repo root), and
load `docs/COACH_PROMPT.md` as the coach agent's system prompt. The vendored
skills under `docs/knowledge/*/SKILL.md` are also directly loadable as
SKILL.md-format skills if your runtime discovers them.

**Cursor / Codex CLI / Continue / others** — any stdio MCP server entry with
command `<repo>/.venv/bin/python`, args `["mcp_server.py"]`, cwd `<repo>`
works. Use `coach_doctrine` with `topic="index"` when the runtime cannot read
the repo's knowledge files directly.

## Any bash-capable agent, no MCP

It can drive everything through `python coach_tools.py <cmd> '<json>'`
(JSON to stdout; `{"error": ...}` + exit 1 on failure) once it reads
`docs/COACH_PROMPT.md` for the workflow. You lose only the typed tool
schemas.

## Adding a native agent-file adapter

If a runtime needs its own agent file rather than MCP config: add a
`(frontmatter, target_path)` entry to `ADAPTERS` in
`scripts/sync_adapters.py`, then run `python scripts/sync_adapters.py`
(`--check` verifies drift after you edit COACH_PROMPT.md). Both wrappers
(CLI and MCP) dispatch through the same handlers in `coach_tools.py` —
change handlers there, never the wrappers.
