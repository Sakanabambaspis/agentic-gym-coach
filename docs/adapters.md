# Runtime Adapters — running the Coach anywhere

The repo is the deployment unit. The Python core (`skills/`, `coach_tools.py`,
DuckDB) is runtime-agnostic; every agent runtime attaches through one of the
adapters below. The persona lives in **`docs/COACH_PROMPT.md`** (canonical) —
never edit a rendered agent file directly; edit the prompt and run
`python scripts/sync_adapters.py`.

## One-time setup (all runtimes)

```bash
uv venv .venv && uv pip install -r requirements.txt
alembic upgrade head        # bootstrap data/gym_coach.duckdb
```

## opencode (native adapter, default)

The Coach is the default primary agent on Tab: `.opencode/agents/coach.md`
(rendered from COACH_PROMPT.md) + native TS tools in `.opencode/tools/`,
allow-listed in `opencode.json`. After changing COACH_PROMPT.md:

```bash
python scripts/sync_adapters.py          # re-render; --check verifies drift
```

## Any MCP-capable runtime (Claude Code, ZCode, Cursor, Codex CLI, Continue, …)

`mcp_server.py` exposes all 12 coach tools + `coach_doctrine` (procedural
disclosure over MCP) over stdio. All runtimes share this one server.

**Claude Code** — repo-root `.mcp.json` is picked up automatically (or
`claude mcp add gym-coach -- .venv/bin/python mcp_server.py`). Pair with the
canonical prompt by pointing a Claude Code agent/subagent's system prompt at
`docs/COACH_PROMPT.md`, or render an adapter entry in `scripts/sync_adapters.py`
(`ADAPTERS` list) and re-run it.

**ZCode** — add the server in your workspace MCP configuration pointing at
`<repo>/.venv/bin/python mcp_server.py` (working directory = repo root), and
load `docs/COACH_PROMPT.md` as the coach agent's system prompt. The vendored
skills under `docs/knowledge/*/SKILL.md` are also directly loadable as
SKILL.md-format skills if your runtime discovers them.

**Cursor / Codex CLI / Continue / others** — any stdio MCP server entry with
command `<repo>/.venv/bin/python`, args `["mcp_server.py"]`, cwd `<repo>`
works. Use `coach_doctrine` with `topic="index"` when the runtime cannot read
the repo's knowledge files directly.

## Adding a new runtime

1. If it speaks MCP: configure it against `mcp_server.py` — done.
2. If it needs a native agent file: add `(frontmatter, target_path)` to
   `ADAPTERS` in `scripts/sync_adapters.py`, re-run it, and add the runtime's
   tool wiring (or just its bash access to `coach_tools.py`).
3. Both wrappers (CLI and MCP) dispatch through the same handlers in
   `coach_tools.py` — change handlers there, never the wrappers.
