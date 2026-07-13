# AGENTS.md — THIN_MUSCLE_OS

Workspace state: **Phase 9 complete + Coach agent integrated.** All 6 skills implemented and tested (38 tests + 1 slow perf test passing), production DuckDB holds 64 historical sessions, opencode Coach agent + 8 custom tools expose the system to the user via the CLI.

## Read order & precedence
Read before writing any code or answering architecture questions:
1. **SPEC.md** — DB schema, tech stack, skill inventory, project structure
2. **MEMORY_PROTOCOL.md** — three-tier memory, state transitions, safety guards
3. **AGENT_INSTRUCTIONS.md** — analysis protocols, communication style
4. **`.opencode/agents/coach.md`** — the Coach agent's system prompt (inlines the core rules below)

Conflict resolution: `SPEC.md > MEMORY_PROTOCOL.md > AGENT_INSTRUCTIONS.md`. Schema and safety always win.

## Tech stack (pinned in requirements.txt)
duckdb==1.5.4 · polars==1.42.1 · lancedb==0.34.0 · pydantic==2.13.4 · alembic==1.18.5 · pytest==9.1.1 · plotly==6.8.0 · Python 3.11+

> Pins bumped from SPEC defaults to Python-3.14-compatible versions (original pins had no cp314 wheels). SPEC pin list is superseded by requirements.txt.

- OLAP: `data/gym_coach.duckdb` (persistent file mode)
- Vectors: `data/lance_db/`
- Migrations: `migrations/` (Alembic — never hand-edit schema)

## Source of truth

**The DuckDB file is canonical.** `log.md` is no longer used for live logging. The historical `log.md` was relocated to `docs/reference/sample_log.md` as a frozen historical reference; new sessions enter the system exclusively through the **Coach agent** (see `.opencode/agents/coach.md`) via the `coach_log_session` tool, or via `python scripts/ingest_log.py <file>` for one-shot bulk imports.

## Raw logging inputs (the only thing the user writes)
The user logs **raw data with minimal effort** via natural language to the Coach agent (or a direct CLI call):
- Gym sessions: "Log today: Squat 3x5 @ RPE 8" → Coach calls `coach_log_session`
- Body weight *(planned, not implemented)*
- Calories *(planned, not implemented)*

Everything else (effective volume, recovery score, phase snapshots, trends, safety gating, weekly summaries, 1RM estimates, anomaly flags) is a **derived product of analysis skills over raw logs**. The user never does analysis themselves.

Historical `log.md` format (preserved in `docs/reference/sample_log.md` for context):
- Date: `MM/DD`
- Weight: kg · `—` = unrecorded or bodyweight
- RPE 1–10 · carried forward from prior set if blank
- Notes: free text (injury, deload, descending load, bodyweight, etc.)

## Commands
| Command | Action |
|---|---|
| `/init` | Scaffold dirs, install deps, init Alembic, bootstrap DB, generate skill stubs + tests |
| `/implement <skill>` | Implement skill + unit tests + verify perf target |
| `/test <skill>` | Run unit tests, report coverage |
| `/migrate <desc>` | Generate + apply Alembic migration |
| `/snapshot` | Trigger phase snapshot generation |
| `/calibrate` | Monthly calibration check |
| `/status` | DB size, skill impl progress, last snapshot, active injuries |
| `/help` | List commands + impl progress |

## Modularity & maintainability
- **Skills are standalone, deterministic Python modules** in `skills/`. Each returns Pydantic models (not dicts). No LLM logic lives here — reasoning happens in the orchestrator.
- Adding/changing a skill → add a module + `tests/test_skills/test_<name>.py`. Pydantic return types enforce the caller contract, so swapping implementations doesn't break callers.
- New analysis scripts/CLIs → drop into `skills/` (if called by the LLM) or a top-level script (if standalone). Keep a single skill = a single file, one public function.
- `models/` holds all Pydantic schemas separately so skills share types without coupling.
- Schema changes go through Alembic migrations only — never hand-edit `data/gym_coach.duckdb`.

## Repo-specific constraints (differ from defaults)
- **Polars, never Pandas** — strict.
- **Pydantic V2** validates all inputs/outputs at DuckDB boundaries.
- **`form_quality < 3`** → that set's volume is discounted 50% in all analytics (SPEC §1.3).
- **`pain_flag = true`** → immediate warning + session tagged for review.
- **Always query `injury_status`** — never assume tendon state.
- **`safety_gate.check_exercise_safety()` is deterministic** — if it returns unsafe, never suggest that exercise; offer `SafetyResult` alternatives instead.
- **No LLM reasoning inside `skills/`** — skills are pure code.
- **Tier 3 semantic memory writes require explicit user command** ("save to long-term memory"). Never auto-write. Tier 1/2 may auto-write.
- **Vector DB stores paths + metadata**, never raw image blobs.
- **Tier 1 working memory < 3K tokens** — orchestrator hard limit.
- **Cite retrieved values explicitly** — never paraphrase from memory. If retrieval returns null, say "I don't have that data." Do not guess.
- **Log every plan modification** to the decision audit trail: trigger signal, reasoning chain, alternative rejected, future validation tag.

## Error posture
- Halt on failure. Report exact failure point + affected data + recovery options. Log to audit trail as `system_error`.
- Never silently retry, interpolate, or fabricate physiological data. Missing = "I don't have that data."

## Validation checklist (before marking any feature complete)
- [ ] DuckDB queries <100ms on 10K-row synthetic set
- [ ] `check_exercise_safety()` blocks contraindicated exercises deterministically
- [ ] Pydantic rejects malformed session logs before DB write
- [ ] Unit tests cover edge cases: empty arrays, null RPE, pain during exercise
- [ ] Phase snapshot generates without manual intervention
- [ ] Full offline operation (no cloud except optional vision API for `visual_delta`)