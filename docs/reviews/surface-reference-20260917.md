# Surface Reference — three-way consistency table (2026-09-17)

Exhaustive per-command comparison of the three places every coach tool lives
(AGENTS.md's own "three places" rule, line 45):

1. **CLI** — `coach_tools.py <cmd> '<json>'` (DISPATCH handler behavior)
2. **MCP** — `mcp_server.py` wrapper (name, signature, docstring)
3. **Persona** — `docs/COACH_PROMPT.md` tool descriptions

Deepens audit finding **P4** with per-command evidence. Actual handler behavior
was verified by execution (see `adversarial-inputs-20260917.md`).

**Scoreboard: 12/12 commands map 1:1 between DISPATCH and MCP names; 6 of 12
commands have at least one CLI↔MCP↔persona inconsistency; plus 2 surface-level
gaps (`coach_ingest` ghost, `coach_doctrine` CLI-less) and 1 capability gap
(`pre_recovery_score` unreachable via MCP).**

## Mismatch register

| # | Severity | Mismatch |
|---|---|---|
| M1 | high | **Ghost tool**: COACH_PROMPT.md:33,42 documents `coach_ingest`; it exists in neither DISPATCH nor MCP. Persona instructs the LLM to call a nonexistent tool. |
| M2 | high | **Recovery bands fiction**: `mcp_server.py:66` docstring teaches "0-59 rest, 60-84 light, 85+ train"; code (`skills/recovery.py:84-92`) implements <60 deload, <80 autoregulate, <100 may train, 100 push-ready. The LLM plans off the docstring. |
| M3 | medium | **`pre_recovery_score` unreachable via MCP**: handler/`SessionInput` accept it, but neither the MCP signature nor the COACH_PROMPT schema exposes it. Through MCP (the primary surface) it is always null — the `sessions.pre_recovery_score` column is dead from the primary surface. |
| M4 | medium | **Duplicated defaults** (same number in two files, drift-prone): `window_days=28` (mcp:71 + cli:48), `limit=10` (mcp:83 + cli:60), `limit=20` (mcp:124 + cli:128), `kind="observation"` (mcp:117 + cli:117). |
| M5 | medium | **Validation asymmetry CLI vs MCP**: MCP declares `severity: int`, `window_days: int`, `limit: int` — the MCP runtime rejects `3.7`/`"28"` before the handler. The CLI accepts and silently coerces them (`int("3")`, `int(3.7)→3`, `int("28")`). Same logical call, different acceptance rules per surface (adversarial F6). |
| M6 | medium | **`coach_doctrine` has no CLI counterpart** and breaks the error contract: returns a plain `"error: unknown doctrine topic ..."` string instead of the `{"error", "detail"}` JSON (audit P8). CLI-only agents must read repo files directly instead (documented in adapters.md, but the persona/tooling asymmetry is real). |
| M7 | low | **injuries_seed docstring vs persona tension**: MCP says "Only when the user explicitly reports a new injury or state change"; COACH_PROMPT:41 additionally tells the coach to seed "the skill's injury guidance" and user-reported aggravators — the docstring's restriction is procedural and unenforced, and the persona pushes free-text exercise names into `contraindicated_exercises` (the P1/F1 fail-open path). |
| M8 | low | **Output-type inconsistency**: `sessions`, `injuries_list`, and `memory_search` return raw dicts/lists (no Pydantic model), while every other command returns a model dumped `mode="json"`. Dates serialize via `json.dumps(default=str)` on one path vs `model_dump` on the other — same rendering today, two mechanisms. |
| M9 | low | **trend docstring under-documents output**: MCP/CLI personas list "hard sets, avg RPE, est 1RM, stall flag" but the report also carries `trend_direction`, `sessions_in_window`, and a `detail` block (`tonnage_kg`, `unloaded_sets`, `overlap_sets`, `epley_all_reps`) that the persona never mentions. |
| M10 | low | **snapshot docstring hides the write**: "Generate/refresh the 4-week phase snapshot" does not say it unconditionally DELETE+INSERTs the `phase_snapshots` row on every call (audit P7 / Q3). |

## Per-command three-way table

Convention: ✔ = consistent across all three sources; ⚠ = see mismatch IDs.

### 1. log_session / coach_log_session
- **CLI**: `log_session '<json>'` — keys `date*`, `exercises*`, `phase?`, `post_feedback?`, plus undocumented `pre_recovery_score?` (M3).
- **MCP**: `coach_log_session(date: str, exercises: list[dict], phase: str | None = None, post_feedback: str | None = None) -> dict`.
- **Persona**: schema matches MCP exactly (COACH_PROMPT:37).
- **Handler**: `SessionInput.model_validate` → `log_session` → `LogConfirmation`; error JSON + exit 1 on any failure.
- Verdict: ✔ except M3.
### 2. safety_check / coach_safety_check
- **CLI**: `safety_check '<json>'` — `exercise*`. **MCP**: `coach_safety_check(exercise: str) -> dict`. **Persona**: "before suggesting any exercise" (COACH_PROMPT:12-14).
- **Handler**: canonicalize → contraindication match → `SafetyResult`. Deterministic as documented; fail-open on canonicalization misses (audit P1 — not a doc mismatch, a code defect).
- Verdict: ✔ (docs match each other and the intended behavior).
### 3. recovery / coach_recovery
- **CLI**: `recovery '<json>'` — `date?` → today. **MCP**: `coach_recovery(date: str | None = None) -> dict`. **Persona**: "0–100 heuristic" only.
- **Handler**: `_parse_date` → `compute_recovery_score` → `RecoveryScore` with `adjustment` bands.
- Verdict: ⚠ M2 (docstring bands vs code bands).
### 4. trend / coach_trend
- **CLI**: `trend '<json>'` — `muscle*`, `window_days?=28`, `end_date?`. **MCP**: `coach_trend(muscle: str, window_days: int = 28, end_date: str | None = None) -> dict`.
- **Handler**: `MuscleGroup(args["muscle"])` → `get_specialization_trend`.
- Verdict: ⚠ M4 (duplicated default), M5 (int coercion CLI-only), M9 (undocumented output fields).
### 5. snapshot / coach_snapshot
- **CLI**: `snapshot '{}'` (args ignored). **MCP**: `coach_snapshot() -> dict`. **Persona**: "4-week anchor incl. `block_state`".
- **Handler**: `generate_phase_snapshot()` — computes AND upserts today's row.
- Verdict: ⚠ M10.
### 6. sessions / coach_sessions
- **CLI**: `sessions '<json>'` — `limit?=10`. **MCP**: `coach_sessions(limit: int = 10) -> dict`. **Persona**: listed with `{limit?}`.
- **Handler**: raw SQL SELECT (id, date, phase, pre_recovery_score, post_feedback) → list of dicts.
- Verdict: ⚠ M4, M8.
### 7. injuries_list / coach_injuries_list
- **CLI**: `injuries_list '{}'`. **MCP**: `coach_injuries_list() -> dict`. **Persona**: COACH_PROMPT:15-17 ("call on first interaction") + :41.
- **Handler**: raw SQL SELECT → list of dicts (garbage rows echoed verbatim — no model).
- Verdict: ⚠ M8.
### 8. injuries_seed / coach_injuries_seed
- **CLI**: `injuries_seed '<json>'` — `location*`, `status*`, `severity*`, `contraindicated_exercises?=[]`, `safe_alternatives?=[]`.
- **MCP**: `coach_injuries_seed(location: str, status: str, severity: int, contraindicated_exercises: list[str] | None = None, safe_alternatives: list[str] | None = None) -> dict` (None→[]).
- **Persona**: COACH_PROMPT:41 (see M7).
- **Handler**: raw INSERT, no validation, no canonicalization (audit P1; adversarial F2/F9).
- Verdict: ⚠ M5, M7; the load-bearing defect is P1.
### 9. profile_get / coach_profile_get
- **CLI**: `profile_get '{}'`. **MCP**: `coach_profile_get() -> dict`. **Persona**: "null ⇒ run onboarding".
- **Handler**: `get_profile()` → `{"profile": null}` or profile JSON.
- Verdict: ✔ docs-wise; empty-profile-wipe hazard is F3 (adversarial), not a doc mismatch.
### 10. profile_set / coach_profile_set
- **CLI**: `profile_set '<json>'` — full UserProfile dict. **MCP**: `coach_profile_set(profile: dict) -> dict`. **Persona**: "echo for confirmation" (matches MCP docstring).
- **Handler**: `UserProfile.model_validate` → `set_profile` (append-only + goal-change audit).
- Verdict: ✔; note `{}` is a valid "update" (F3) — docstrings say "Create/update" and don't exclude it.
### 11. memory_save / coach_memory_save
- **CLI**: `memory_save '<json>'` — `text*`, `kind?="observation"`, `tags?=[]`. **MCP**: `coach_memory_save(text: str, kind: str = "observation", tags: list[str] | None = None) -> dict`.
- **Persona + MCP docstring**: explicit-command-only policy, matches MEMORY_PROTOCOL Tier 3. Handler enforces non-empty text + NoteKind.
- Verdict: ⚠ M4 (duplicated `kind` default only).
### 12. memory_search / coach_memory_search
- **CLI**: `memory_search '<json>'` — `query?`, `tags?`, `limit?=20`. **MCP**: `coach_memory_search(query: str | None = None, tags: list[str] | None = None, limit: int = 20) -> dict`.
- **Handler**: substring AND any-tag, newest first, limit. Docstring "substring + any-tag" is accurate (though it omits that query and tags combine with AND).
- Verdict: ⚠ M4, M8.

### (+1) coach_doctrine — MCP only
- **MCP**: `coach_doctrine(topic: str | None = None) -> str` — `'index'` routing table or file content, 14 000-char cap, path-confined.
- **CLI**: no counterpart (M6). **Persona**: routes knowledge loading through files; mentions doctrine tool only in `.zcode` skill ("If the runtime exposes coach_doctrine").
- Verdict: ⚠ M6.

## Ghost / missing surfaces

| Item | CLI | MCP | Persona | Status |
|---|---|---|---|---|
| `coach_ingest` | ✗ | ✗ | ✔ documented (lines 33, 42) | **M1 — remove from persona or implement (Q2)** |
| `coach_doctrine` | ✗ | ✔ | implied | documented asymmetry (adapters.md) |
| `orchestrator.initialize_session` / `finalize_session` | ✗ | ✗ | ✗ | unreachable from every surface (audit P3 / Q1) |

## Defaults inventory (single place each should live — audit ticket T5)

| Parameter | CLI (coach_tools.py) | MCP (mcp_server.py) | Equal today? |
|---|---|---|---|
| `trend.window_days` | 28 (line 48) | 28 (line 71) | yes — duplicated |
| `sessions.limit` | 10 (line 60) | 10 (line 83) | yes — duplicated |
| `memory_search.limit` | 20 (line 128) | 20 (line 124) | yes — duplicated |
| `memory_save.kind` | "observation" (line 117) | "observation" (line 117) | yes — duplicated |
| `injuries_seed.*_exercises` | `[]` (lines 92-93) | None→[] (lines 100-101) | yes — duplicated |

## Takeaway

The wrapper layers are faithful *today* (all 12 names map, all present
defaults agree), but nothing enforces that: the two drift incidents already in
the tree (M1 ghost tool, M2 wrong bands) both entered through the
persona/docstring side, exactly where AGENTS.md's manual three-places rule has
no check. The cheapest structural fix remains audit T5(c): a drift test
comparing MCP signatures to DISPATCH handlers, plus deleting or implementing
the ghost.
