# Design Audit — agentic-gym-coach (2026-09-16)

Report-only audit against *A Philosophy of Software Design* (Ousterhout). Scope:
`orchestrator.py`, `mcp_server.py`, `coach_tools.py`, `conftest.py`, `models/*.py`,
`skills/*.py`, `scripts/*.py`, read against `SPEC.md`, `AGENTS.md`,
`MEMORY_PROTOCOL.md`, `docs/COACH_PROMPT.md`, `docs/adapters.md`, migrations.

Constraints respected: project rules (doctrine lives only in vendored book-skills;
`skills/` deterministic Python; safety gate stays deterministic; no LLM logic in
skills) are treated as **constraints of this audit, not findings**. Nothing outside
`docs/reviews/` was modified. Pitfalls that would require redesigning the SPEC's
data/knowledge architecture are recorded as **open questions** (§3), not solved.

---

## 1. Top design pitfalls

### P1 — The injury write boundary validates and canonicalizes nothing (worst finding: silent safety-gate miss)

**Evidence.**
- `coach_tools.py:82-96` (`cmd_injuries_seed`) inserts `args["location"]`,
  `args["status"]`, and the `contraindicated_exercises` / `safe_alternatives`
  string lists **raw** into `injury_status`. No Pydantic model, no
  `canonicalize()` — unlike every other write path (`cmd_log_session` validates
  via `SessionInput`, `cmd_profile_set` via `UserProfile`,
  `cmd_memory_save` via `NoteKind`).
- `skills/safety_gate.py:23` canonicalizes only the **query** side, and
  `skills/safety_gate.py:29` matches with `list_contains(contraindicated_exercises, ?)`
  — exact, case-sensitive element equality.
- `models/exercise_catalog.py:143-148`: for keyword-fallback hits `canonicalize()`
  returns the **raw input string** (not a canonical name) with `needs_review=True`;
  fully unknown names fall back to `(key, MuscleGroup.core, True)`.
- `docs/COACH_PROMPT.md:41` invites free text into this path: "contraindications
  come from what the user reports aggravates the injury".
- Deferred crash: `orchestrator.py:41` constructs `PainLocation(loc)` /
  `InjuryState(st)` from the stored VARCHARs — a non-vocabulary location/status
  written today raises `ValueError` on a *later* `initialize_session()`.

**Principle violated.** Ch 5 (information hiding/leakage — the decision "only
canonical exercise names may live in `contraindicated_exercises`" is enforced by
*neither* the write path nor the read path; it is an invisible convention),
Ch 10 (define errors out of existence — a canonicalization miss produces no error
at all, it silently changes the gate's answer).

**Symptom.** User reports elbow pain from "skullcrushers"; the coach seeds
`contraindicated_exercises=["skullcrushers"]`. Next session:
`check_exercise_safety("Skull Crusher")` canonicalizes to `"Skull Crusher"`
(exact alias hit), `list_contains(["skullcrushers"], "Skull Crusher")` is false
→ `safe=true` → **the banned exercise is recommended, with no error anywhere**.
This directly undermines the binding invariant (AGENTS.md: "if it returns unsafe,
never suggest that exercise") — the gate doesn't return unsafe, it silently
returns the wrong answer. Second symptom: a location like `"elbow"` (not in
`PainLocation`) is stored fine and crashes Tier-1 assembly days later, far from
the faulty write.

### P2 — Core state queries are implemented as scattered private SQL instead of deep modules

**Evidence.**
- "Current phase" policy (latest snapshot → else modal session phase → else None)
  exists **three times with divergent fallbacks**: `orchestrator.py:48-57`
  (→ modal sessions → `None`), `skills/snapshot.py:79-88` (identical copy,
  returns `str`), `skills/session_logger.py:29-37` (→ `_DEFAULT_PHASE`
  maintenance, never consults sessions-mode). The literal SQL
  `"SELECT phase FROM phase_snapshots ORDER BY snapshot_date DESC LIMIT 1"`
  appears at all three sites.
- The `injury_status` schema (column names, active-status filter) is known by
  **five modules**: `orchestrator.py:33-45` (`_active_injuries`), 
  `skills/safety_gate.py:24-32`, `skills/snapshot.py:91-95` (`_tendon_summary`),
  `coach_tools.py:70-79` (`cmd_injuries_list` SELECT), `coach_tools.py:82-96`
  (INSERT). Plus two competing row→model mappings (`InjuryStatus` in
  orchestrator vs raw dicts in snapshot/dispatcher).
- `MEMORY_PROTOCOL.md` §2.1 pseudocode names the operations
  (`get_active_injuries()`, `get_current_phase()`) — they exist only as private,
  duplicated SQL. The dispatcher layer (`coach_tools.py`) — nominally a thin
  command surface per AGENTS.md:51 — contains table-schema SQL and writes.

**Principle violated.** Ch 4 (modules should be deep — the handlers that need
"active injuries" get a shallow raw-SQL recipe instead), Ch 5 (information
leakage: the schema and the "what counts as active / current" decisions are
spread across 3–5 files), Ch 17 (consistency — three phase fallbacks already
disagree).

**Symptom.** Change amplification, already real: changing the meaning of
"current phase" (e.g., "snapshot from the last 8 weeks only") requires
coordinated edits in 3 files, and the divergence means the same moment in time
can be phase `maintenance` when *writing* a session but phase `cut` (modal) when
*reading* it in the orchestrator. Renaming an `injury_status` column is a 5-file
edit (plus migrations).

### P3 — The orchestrator is unreachable from every documented surface, and the Tier-1 token cap is fiction

**Evidence.**
- `initialize_session` / `finalize_session` are called only by
  `tests/test_orchestrator.py` (repo-wide grep: no reference from
  `mcp_server.py`, `coach_tools.py`, or `docs/COACH_PROMPT.md`; MCP exposes 12
  tools + `coach_doctrine`, none of them session-init). The MEMORY_PROTOCOL §2.1
  "session start sequence" cannot actually run through the CLI or MCP.
- `MEMORY_PROTOCOL.md:13` says the ~3K-token Tier-1 limit is a "hard limit
  enforced by orchestrator"; `models/working_memory.py:6` repeats "enforced by
  the orchestrator". `orchestrator.py:28` defines `_TIER1_LIMIT_TOKENS = 3000`
  and **never compares it to anything** — `orchestrator.py:76` punts to
  "caller (LLM) must re-prompt if wm.estimate_tokens() > limit".
- `orchestrator.py:79` declares `finalize_session(...) -> object` (the actual
  return is `LogConfirmation`), and `orchestrator.py:80` carries a
  "local import avoids cycle at module load" comment for a `models` import that
  has no cycle (models never imports orchestrator) — a stale constraint claim.

**Principle violated.** Ch 13 (comments must describe what *is* — two documents
and a model docstring promise an enforcement that does not exist), Ch 2
(obscurity / unknown unknowns — a reader implements against the protocol
believing the cap holds), Ch 7 (a layer with no callers serves no abstraction).

**Symptom.** A profile with many goals/priority muscles produces
`recent_trends` entries per muscle; nothing stops Tier-1 from silently exceeding
3K tokens and flooding the LLM context with trend JSON — the exact failure the
protocol says cannot happen. And any runtime following the documented surfaces
has no way to execute the protocol's session-start flow at all.

### P4 — Tool-surface contract drift (already happened, not hypothetical)

**Evidence.**
- `docs/COACH_PROMPT.md:33` and `:42` document a `coach_ingest` tool. It exists
  in **neither** surface: no `coach_ingest` in `mcp_server.py`, no `ingest` key
  in `DISPATCH` (`coach_tools.py:133-146`). The canonical persona instructs the
  LLM to call a tool that does not exist.
- `mcp_server.py:66` documents recovery bands "0-59 rest, 60-84 light, 85+ train".
  The code (`skills/recovery.py:84-92`) implements <60 deload, <80 autoregulate,
  <100 "may train", 100 "push-ready". A score of 82 is "light/train" per the
  docstring the LLM reads, but "autoregulate; cap top-set RPE" per the code.
- Parameter defaults live in **both** wrappers: `window_days=28`
  (`mcp_server.py:71` + `coach_tools.py:48`), `limit=10` (`:83` + `:60`),
  `limit=20` (`:124` + `:128`), `kind="observation"` (`:117` + `:117`).
  AGENTS.md:45 itself admits a tool change touches three places (handler, MCP
  wrapper, COACH_PROMPT).

**Principle violated.** Ch 2 (change amplification — the symptom class is
already realized twice in a small codebase), Ch 13 (docstrings that teach the
agent wrong thresholds), Ch 7 (pass-through wrappers that duplicate rather than
delegate knowledge).

**Symptom.** The coach LLM calls `coach_ingest`, gets `unknown command`, and
hallucinates around it; it treats recovery 82 as "train" while the engine
intended "cap RPE". Every future default change risks a third instance of drift
because the same number must be edited in two files by hand.

### P5 — The Epley doctrine exists in five copies, one reached through a private-name import

**Evidence.**
- Formula `weight_kg * (1 + reps/30)`: `skills/trend_analysis.py:127, 131, 146,
  149` and `skills/snapshot.py:68` — five copies.
- `skills/snapshot.py:34`: `from .trend_analysis import _EPLEY_MAX_REPS,
  hard_sets_by_muscle` — snapshot reaches into trend_analysis's **private**
  namespace for the reps-≤-6 doctrine constant (`trend_analysis.py:36`).

**Principle violated.** Ch 5 (information leakage via invisible convention —
the underscore import leaks "this constant is private" while depending on it),
Ch 17 (consistency).

**Symptom.** A doctrine refinement ("estimate 1RM only from reps ≤ 5" or a
non-Epley formula) must be edited in two files and five lines; missing one makes
`coach_trend` and `coach_snapshot` report **different 1RMs for the same logged
data**, tripping the snapshot consistency guard (MEMORY_PROTOCOL §3.2, ≤5%
deviation) with phantom "data integrity" flags.

### P6 — Secondary vocabularies are stringly-typed despite the repo's own enums-as-vocabulary doctrine

**Evidence.**
- Repo doctrine (`models/enums.py:1-9`, SPEC §2.2): enums are *the* controlled
  vocabulary; DB stores VARCHAR, so extending vocabulary = edit the enum, no
  migration.
- Yet: `models/snapshot.py:26` `trend_direction: str` with allowed values only
  in a comment; `models/session.py:86` `AnomalyFlag.code: str` whose comment
  lists `'rpe_spike'` — a code **no code path ever emits** (repo-wide grep:
  only the comment); `decision_log.event_type` is free string literals in three
  files: `"plan_modification"` (`orchestrator.py:96`), `"anomaly"`
  (`orchestrator.py:85`), `"goal_change"` (`skills/profile.py:51`).

**Principle violated.** Ch 17 (consistency: the vocabulary policy is applied to
phase/location/muscle but not to three sibling vocabularies), Ch 14 (precision
of names: same "vocabulary" concept, two different mechanisms).

**Symptom.** A typo'd `event_type="anomalies"` passed to `orchestrator.log_decision`
silently writes an audit row that every downstream filter on `event_type`
misses — the audit trail (a SPEC invariant) becomes quietly lossy. The
documented-but-nonexistent `rpe_spike` code sends future maintainers hunting for
an implementation that isn't there.

### P7 — `generate_phase_snapshot` hides an unconditional table write behind a read-shaped name

**Evidence.**
- `skills/snapshot.py:156-167`: every call does `DELETE FROM phase_snapshots
  WHERE snapshot_date = ?` + INSERT. The name says "generate"; the MCP docstring
  (`mcp_server.py:78`) says "Generate/refresh"; `coach_snapshot` is also the
  LLM's only way to *read* `block_state` / tendon status
  (`docs/COACH_PROMPT.md:40, 146-147` directs routine deload checks through it).
- `MEMORY_PROTOCOL.md:100-105` (§2.3) says the snapshot is *proposed*, reviewed
  by the user, and written to `phase_snapshots` **on confirmation**. The code
  always writes. (No decision_log entry either, though the stored key_insight
  can change as the profile changes mid-day.)

**Principle violated.** Ch 18 (code should be obvious — a consultation tool with
a destructive side effect is a surprise violation), Ch 10 (the write-or-not
decision should be explicit in the interface, not buried in the body).

**Symptom.** "Where are we this block?" asked twice around a profile update
silently rewrites today's anchor document (different `key_insight`), and the
protocol's review gate never engages. *Resolution requires a SPEC/protocol
decision — see open question Q3; not solved here.*

### P8 — The error contract at both surfaces is "whatever Python raised"

**Evidence.**
- `coach_tools.py:165-167` and `mcp_server.py:42-43`: blanket
  `except Exception` → `{"error": type(e).__name__, "detail": str(e)}`. A
  vocabulary typo surfaces as a `ValidationError` whose detail is a multi-line
  pydantic traceback string; a DuckDB lock surfaces in the same shape. The
  exception class name *is* the entire error taxonomy.
- `mcp_server.py:145` (`coach_doctrine`) breaks the JSON error contract
  entirely: plain-text `"error: unknown doctrine topic '...'"` inside a string
  return, unlike every other tool's `{"error": ...}` object.

**Principle violated.** Ch 10 (exceptions are interface surface — translate and
aggregate at the boundary; the caller here is an LLM, which cannot parse
tracebacks reliably), Ch 17 (the error shape is inconsistent across one tool).

**Symptom.** The coach agent cannot distinguish "fix your arguments" (bad
muscle name) from "halt and report" (DB failure) from "unknown tool", so it
either retries forever or reports the wrong recovery posture — the
halt-and-report posture in AGENTS.md depends on a contract the code doesn't
provide.

---

## 2. Refactor backlog (prioritized; each ticket ≈ one evening, mechanical check)

> Rules for all tickets: no LLM logic enters `skills/`; the safety gate stays
> deterministic; doctrine strings unchanged; DB stays VARCHAR at these columns
> (no migration needed for T7); wrappers stay thin (change handlers, never the
> wrappers — AGENTS.md:51).

### T1 — P0: Canonicalize + validate at the injuries_seed boundary
**Scope.** `coach_tools.cmd_injuries_seed` (`coach_tools.py:82-96`): build
`models.InjuryStatus` from the args (Pydantic enforces `location`/`status`/
`severity 0-10` → invalid vocab now fails at write time with the standard error
JSON); run every entry of `contraindicated_exercises`/`safe_alternatives`
through `models.exercise_catalog.canonicalize()` and store the canonical names;
include the `needs_review` entries in the response message so the coach can
confirm guesses with the user.
**Done when.** New tests in `tests/test_skills/test_safety_gate.py`: seed messy
spellings via `coach_tools.DISPATCH["injuries_seed"]`, then
`check_exercise_safety("Skull Crusher")` returns `safe=false`; invalid
`location="elbow"` returns `{"error": ...}` and writes nothing. Full suite
passes; DISPATCH keys unchanged; no signature changes.

### T2 — P0: Extract `skills/injuries.py` (deep module hiding `injury_status`)
**Scope.** New module with `get_active_injuries() -> list[InjuryStatus]` (move
`orchestrator._active_injuries`), `list_injuries() -> list[InjuryStatus]`
(rewritten `cmd_injuries_list` returning models), `seed_injury(i: InjuryStatus)`
(the validated insert from T1 lives *here*; the dispatcher only parses args),
`tendon_summary() -> dict` (move `skills/snapshot._tendon_summary`). Rewire
`orchestrator.py:33-45`, `coach_tools.py:70-96`, `skills/snapshot.py:91-95` to
call it.
**Done when.** `grep -rn "injury_status" --include="*.py"` finds table SQL only
in `skills/injuries.py` (plus migrations/conftest/tests); suite passes; no
behavior change in existing tests.

### T3 — P1: One current-phase resolver
**Scope.** New `skills/phase.py`: `current_phase() -> PhaseType | None`
(latest snapshot → modal session phase → None) and `phase_for_logging() ->
PhaseType` (wraps it; falls back to the documented `maintenance` default).
Rewire `orchestrator.py:48-57`, `skills/session_logger.py:29-37`,
`skills/snapshot.py:79-88`.
**Done when.** `grep -rn "snapshot_date DESC LIMIT" --include="*.py"` has exactly
one non-test hit; suite passes; the divergent-fallback policy is stated in one
docstring.

### T4 — P1: Make the Tier-1 cap real; fix the orchestrator's contract
**Scope.** In `orchestrator.initialize_session`: after building `wm`, if
`wm.estimate_tokens() > 3000`, drop `recent_trends` entries (lowest-priority
muscles first) until under the cap and `log_decision(event_type="anomaly",
...)` recording the truncation (no model change needed). Change
`finalize_session` return annotation to `LogConfirmation`, hoist the import to
module top (verify no cycle exists — models does not import orchestrator), and
delete the stale cycle comment at `orchestrator.py:80`.
**Done when.** New test in `tests/test_orchestrator.py` with a profile declaring
many priority muscles asserts `wm.estimate_tokens() <= 3000` and that a
truncation row landed in `decision_log`; suite passes.

### T5 — P1: Align the tool-surface contracts
**Scope.** (a) Remove the two `coach_ingest` references from
`docs/COACH_PROMPT.md` (persona-file edit only; bulk import stays a
coding-agent job via `scripts/ingest_log.py` — implementing it over MCP would be
a SPEC change, see Q2). (b) Correct `coach_recovery`'s docstring bands
(`mcp_server.py:66`) to match `skills/recovery.py:84-92`. (c) Single-source the
defaults in the `coach_tools` handlers and add
`tests/test_coach_tools.py::test_mcp_wrapper_defaults_match_dispatch`
comparing `inspect.signature` defaults of every `coach_*` wrapper against the
DISPATCH handler defaults, so drift fails CI.
**Done when.** `grep -rn "coach_ingest" docs/` is empty; the new drift test
passes; deliberately editing a handler default without the wrapper makes the
new test fail (checked once by hand); suite passes.

### T6 — P2: One Epley definition
**Scope.** New `skills/metrics.py`: public `EPLEY_MAX_REPS = 6` (with the
Training-ch04 citation), `est_1rm(weight_kg, reps)` scalar, and a Polars
expression helper `est_1rm_expr(weight_col, reps_col)`. `trend_analysis.py` and
`skills/snapshot.py` use them; delete all five formula copies and the private
`_EPLEY_MAX_REPS` import (`skills/snapshot.py:34`).
**Done when.** `grep -rn "30.0" --include="*.py" skills/` shows no Epley
arithmetic outside `metrics.py`; `grep -rn "_EPLEY"` is empty; existing
trend/snapshot tests pass with unchanged expected values (pure extraction).

### T7 — P2: Enum-ify the secondary vocabularies
**Scope.** Add to `models/enums.py`: `TrendDirection` (`up/down/plateau/unknown`),
`AnomalyCode` (`pain_flag`, `form_quality_low`, `needs_review` — exactly what
`session_logger` emits), `DecisionEventType` (`plan_modification`, `anomaly`,
`goal_change`). Switch `TrendReport.trend_direction`, `AnomalyFlag.code`, and
`log_decision(event_type=...)` to them (values unchanged → VARCHAR-compatible,
no migration). Update the `stalled` check and the anomaly-join in
`finalize_session` to enum members; delete the phantom `rpe_spike` from the
comment (`models/session.py:86`).
**Done when.** Suite passes; `grep -rn "event_type" --include="*.py"` shows no
bare string literals outside `models/enums.py` and tests; no migration added.

### T8 — P2: Design the error vocabulary at the tool boundary
**Scope.** In `coach_tools.main` (and `_run` in `mcp_server.py` keeps reusing
it), replace the blanket handler with a mapping: `ValidationError` /
`KeyError` → `{"error": "invalid_input", ...}`, `duckdb.Error` →
`{"error": "db", ...}`, else `{"error": "internal", ...}`, always including the
original class name and detail fields. Document the three codes in the module
docstring so the persona can reference them. Align `coach_doctrine`'s error
string to at least keep a stable `error:` prefix (`mcp_server.py:145`).
**Done when.** New tests: invalid `muscle` → `invalid_input`; unknown command
unchanged; suite passes. (Persona rewording optional; the JSON shape is the
deliverable.)

### T9 — P3: Code-health sweep (small, mechanical)
**Scope.** (a) `skills/init.py:24`: import `Any` from `typing` (module currently
references an unimported name; latent `NameError` under `get_type_hints`).
(b) `scripts/ingest_log.py`: `--demo` is unreachable — `raise SystemExit(main(...))`
at line 203 always fires first; move the demo dispatch above it or drop `_demo`.
(c) `conftest.py:41-60`: replace the twelve duplicated `DELETE` statements with
one `_TABLES` tuple iterated before/after `yield`.
**Done when.** `.venv/bin/python scripts/ingest_log.py --demo` prints
`OK: parsed N sessions`; suite passes; the table list appears once in conftest.

### T10 — P2, BLOCKED on Q3: Snapshot preview/commit split
**Scope.** Only after Q3 is answered. If the protocol wins: split
`generate_phase_snapshot()` into pure `build_phase_snapshot() -> PhaseSnapshot`
(no writes) + `persist_phase_snapshot(snap)` (the DELETE+INSERT at
`skills/snapshot.py:156-167`); `coach_snapshot` calls build + persist only when
the flow allows, else returns the proposal with a `proposed: true` marker.
If auto-write stands: no code change; instead record the decision in
`AGENTS.md` so the code and MEMORY_PROTOCOL stop disagreeing.
**Done when.** Whatever branch: `coach_snapshot` docstring, code, and
MEMORY_PROTOCOL §2.3 all state the same write policy; suite passes.

---

## 3. Open questions for the user (not solved here)

- **Q1 — Who calls the orchestrator?** SPEC §4 pins the surface at "12 coach
  tools + coach_doctrine"; MEMORY_PROTOCOL §2.1/§2.2 define a session-start/end
  sequence implemented in `orchestrator.py` that no CLI command or MCP tool can
  invoke (tests only). Should `initialize_session`/`finalize_session` be exposed
  (SPEC change → 13-14 tools), or is the orchestrator test-only scaffolding for
  now? Until answered, T4 fixes only the internal contract.
- **Q2 — `coach_ingest`: implement or remove?** COACH_PROMPT promises a bulk
  import tool that doesn't exist. T5 assumes removal (no SPEC change). If you
  want MCP bulk import, that's a SPEC §4 change and a separate ticket.
- **Q3 — Snapshot write policy.** MEMORY_PROTOCOL §2.3: write on user
  confirmation after review. Code: unconditional upsert on every
  `coach_snapshot` call. Which wins? (Blocks T10.)
- **Q4 — Safety posture for unknown exercises.** `canonicalize()` maps unseen
  names to `needs_review` and the gate finds no contraindication → unknown
  exercises are safe by default (fail-open). Given P1, should an
  `needs_review` exercise near an injured area require explicit user
  confirmation before being suggested? This is a coaching-policy decision the
  vendored books don't cover — recorded, not decided.
- **Q5 — `PainLocation.none`.** The vocabulary contains a `none` location
  (`models/enums.py:51`); injury rows presumably never use it. Sentinel-in-enum
  or real value? Trivial, but it will confuse the next vocabulary extension.

## 4. Non-findings (checked, deliberately not flagged)

- `mcp_server.py`'s 12 pass-through wrappers are justified interface definitions
  (typed MCP schemas + LLM-facing docstrings); the problem is only the
  *duplicated* knowledge (P4), not the wrapping.
- `models/snapshot.py` bundling four flat return models is fine (Ch 9:
  together — they share no state and one import surface).
- Recovery's use of raw sets instead of effective sets is intentional fatigue
  accounting, not a volume-currency violation (SPEC §2.3 governs *volume
  reporting*, which `trend_analysis` implements correctly).
- `skills/init.py` env-at-import-time coupling is documented in AGENTS.md and
  conftest; noted in T9 only as health, not a pitfall.

---

*Audit performed read-only. Git state at time of writing: pre-existing untracked
`.zcode/` (workspace wiring described in docs/adapters.md, present before this
audit) plus this file — `docs/reviews/design-audit-20260916.md` — the only
artifact created.*
