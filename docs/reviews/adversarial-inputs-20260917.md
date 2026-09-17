# Adversarial Input Catalog — agentic-gym-coach (2026-09-17)

Observations only; no code was changed. Companion to `design-audit-20260916.md`
(P1/P2/P4/P8 evidence deepened here).

## Method

- Throwaway DB: `GYM_COACH_DUCKDB=/tmp/gym_adversarial*.duckdb`, schema applied
  via Alembic (same pattern as `conftest.py`), set **before** `skills.init`
  import. Production DB never touched.
- Each CLI probe ran `coach_tools.py <cmd> '<json>'` in a **fresh subprocess**
  (true exit codes, true process-crash detection), with row counts of all six
  tables snapshotted before/after every probe (`db_delta` below).
- 87 CLI probes + 8 orchestrator scenarios. Orchestrator probes ran in-process
  per subprocess scenario (it has no CLI/MCP surface — itself an audit finding
  P3).
- Notation: `exit 0` = success JSON on stdout; `exit 1` = `{"error": ...}`
  JSON; `exit 2` = unknown command. "RAISED X" = raw Python exception (no
  wrapper) for orchestrator calls.

**Headline: 79/87 CLI probes behaved safely (error JSON or correct output, DB
never corrupted, no process crashes, SQL injection fully parameterized), but 5
adversarial inputs were *accepted and persisted* that poison later behavior,
and the orchestrator layer has no error contract at all.**

## Cross-cutting findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | **Safety gate fails open end-to-end.** Seeded `contraindicated_exercises=["skullcrushers"]`, then `safety_check {"exercise": "Skull Crusher"}` → `{"safe": true, "reason": "no active contraindication"}`. Reproduced live through the real tools on a persisted DB. | `inj_10` + live re-check (see §Safety) |
| F2 | **Injury write path accepts out-of-vocabulary garbage.** `location="elbow"`, `status="banana"`, `severity=3.7`→3, `severity="3"`→3 all stored. | `inj_02`, `inj_03`, `inj_07`, `inj_08` |
| F3 | **`profile_set {}` writes a valid *empty* profile** — the onboarding gate (`onboarding_required = profile is None`) then reports onboarded for a user with zero information. One call silently disarms the onboarding flow. | `prf_01` → `user_profiles +1`, exit 0 |
| F4 | **Per-set array validator has a hole.** `reps=[8,7], rpe=[8]` correctly rejected, but `reps=[], rpe=[], weight_kg=[60.0]` is **accepted** — the validator only compares non-empty lists (`models/session.py:47`: `if x`), so "two arrays empty, one has 1 entry" passes. | `log_03` (rejected) vs `log_04` (accepted) |
| F5 | **Numeric garbage accepted and persisted:** `sets=1000000000` (stored; would poison every volume sum), `rpe=[11]` (no upper bound), `rpe=[1e400]`→`[inf]` (stored as `inf`). Contrast: `weight_kg=[1e308]` is rejected only at the DB layer (`ConversionException: ... out of range for FLOAT`) after validation passed. | `log_07`, `log_08`, `log_10`, `log_11` |
| F6 | **Inconsistent numeric coercion.** `window_days="28"` and `window_days=3.7`→3 are silently accepted (`int()`), `severity="3"`/`3.7` likewise — but `window_days="abc"` and `severity="high"` are `ValueError`s. Same syntactic class of mistake, two different outcomes depending on value. | `trd_05`, `trd_08`, `inj_07`, `inj_08` vs `trd_06`, `inj_04` |
| F7 | **Negative numbers diverge by command.** `sessions {"limit": -1}` → `BinderException` error JSON (DuckDB rejects negative LIMIT); `trend {"window_days": -28}` → **exit 0 with an empty report** (inverted window silently means "no data"). | `ses_03` vs `trd_04` |
| F8 | **The orchestrator has no error contract.** `initialize_session`/`finalize_session` raise raw `TypeError`/`AttributeError`/`ValidationError`/`ValueError` with no wrapper — any future surface wiring gets tracebacks, not the `{"error": ...}` posture. | §Orchestrator table |
| F9 | **Deferred-crash chain reproduced with real tools only:** `injuries_seed {"location": "elbow", ...}` → `{"ok": true}` → **every subsequent** `initialize_session` raises `ValueError: 'elbow' is not a valid PainLocation`. Tier-1 assembly stays dead until someone hand-deletes the row. | `inj_02` then `init_bad_injury_row` |
| F10 | **CLI has an OS-level payload ceiling.** A 1 MB `post_feedback` cannot even be spawned: `OSError: [Errno 7] Argument list too long` (Linux per-arg limit ≈128 KB). 100 KB passes and is stored. MCP callers are unaffected; CLI-only agents hit an unclassifiable spawn error, not a tool error. | `log_24b` vs `log_24` |
| F11 | **Tier-1 token cap: unenforced but currently unreachable.** With *all 13* muscle groups as priorities (worst case), `initialize_session` working memory = **796 tokens** < 3000. The cap is still not enforced anywhere (audit P3), and MEMORY_PROTOCOL's planned additions (today's workout, last-3-sessions) would consume the remaining headroom — but today nothing can blow it via this path. | `token_cap` scenario on clean DB |
| F12 | **`snapshot` on an empty DB invents a phase.** Zero sessions, zero snapshots → writes a `phase_snapshots` row with `phase="maintenance"`. Honest per the `_DEFAULT_PHASE` policy, but the anchor document now exists with no underlying data. Also: future-dated sessions (2030) are invisible to a 2026 snapshot window (uses `date.today()`). | `snp_01`, `snp_02` |

Robustness positives (verified, not assumed): all SQL-ish inputs
(`"Robert'); DROP TABLE sessions;--"` as exercise name, injury location, and
safety-check query) were stored/matched literally via parameterized queries —
**no injection anywhere, DB intact after every probe**; unicode names work;
10 KB names and 100 KB feedback store fine; `{"error", "detail"}` shape and
exit codes were consistent across every CLI failure; no probe crashed or hung
the process (9 distinct Python/DB exception class names observed as the
`error` field — see P8).

## Per-command results (12 DISPATCH commands)

Exit codes: 0 = success JSON, 1 = `{"error", "detail"}` JSON, 2 = unknown
command. `db` = table row deltas.

### log_session
| Input (abridged) | Exit | Behavior |
|---|---|---|
| `{}` | 1 | `ValidationError ... Field required` (missing date + exercises) |
| `exercises: []` | 0 | **Empty session logged**, `session_id` returned, row written |
| `reps=[8,7], rpe=[8]` | 1 | equal-length validator: rejected, nothing written |
| `reps=[], rpe=[], weight_kg=[60.0]` | 0 | **F4 hole:** accepted, written |
| `sets: 0` / `sets: -3` | 1 | `ge=1` rejected |
| `sets: 1000000000` | 0 | **accepted, stored** (verified in DB) |
| `rpe: [11]` | 0 | **accepted, stored** (no upper bound) |
| `rpe: [-1]` | 1 | negative rejected |
| `rpe: [1e400]` (JSON `Infinity`) | 0 | **stored as `inf`** (verified) |
| `weight_kg: [1e308]` | 1 | `ConversionException` (FLOAT overflow at DB), nothing written |
| `form_quality: 0` / `6` | 1 | bounds `1..5` rejected |
| `date: "2030-13-45"` / `"2030-02-30"` | 1 | invalid month/day rejected |
| `date: 123` | 1 | `Datetimes provided to dates should have zero time` |
| `phase: "bulking"` | 1 | unknown PhaseType rejected with full vocab list |
| `exercises: {"name": "Bench"}` (dict) | 1 | `Input should be a valid list` |
| `exercises: [{}]` | 1 | `name: Field required` |
| name = `"Robert'); DROP TABLE sessions;--"` | 0 | stored literally; needs_review flag; DB intact |
| name = `"デッドリフト"` | 0 | stored; needs_review (keyword fallback) |
| name = `"Bulgarian Split Squat"` | 0 | alias hit → canonicalized to **"Squat"** (variant name lost in DB; raw survives only in log.md) |
| name = 10 000 × `"B"` | 0 | stored; needs_review |
| `post_feedback` 100 KB | 0 | stored |
| `post_feedback` 1 MB | — | **never reached the tool:** OS `E2BIG` at spawn (F10) |
| `pain_flag: true` | 0 | logged; `anomaly_flags: [pain_flag]` |

### safety_check
| Input | Exit | Behavior |
|---|---|---|
| `{}` (missing key) | 1 | `{"error": "KeyError", "detail": "'exercise'"}` |
| `""` | 0 | `safe: true` — empty string is a safe "exercise" |
| SQL-ish string | 0 | safe, returned literally; parameterized |
| `"Skullcrusher"` / `"skull crusher"` (no contraindication seeded) | 0 | `safe: true` |
| `"Skull Crusher"` **with** `"skullcrushers"` seeded | 0 | **`safe: true` — F1 live miss** |
| `"デッドリフト"` | 0 | `safe: true` (unknown = safe, fail-open; Q4 of the audit) |
| 100 KB string | 0 | safe (canonicalized keyword miss) |
| `123` (int) | 1 | `AttributeError: 'int' object has no attribute 'strip'` |

### recovery
| Input | Exit | Behavior |
|---|---|---|
| `{}` | 0 | defaults to today, score 100 "push-ready" on empty DB |
| `"not-a-date"` | 1 | `ValueError: Invalid isoformat string` |
| `"2030-02-30"` | 1 | `ValueError: day is out of range for month` |
| `"9999-12-31"` / `"1000-01-01"` | 0 | extreme dates handled (window arithmetic OK) |
| `123` | 1 | `TypeError: fromisoformat: argument must be str` |

### trend
| Input | Exit | Behavior |
|---|---|---|
| `{}` | 1 | `KeyError: 'muscle'` |
| `"chest"` / `"CHEST"` | 1 | `'chest' is not a valid MuscleGroup` (no case-folding — exact vocab only) |
| `window_days: -28` | 0 | **empty report, silent success** (F7) |
| `window_days: "28"` | 0 | accepted via `int()` |
| `window_days: "abc"` | 1 | `ValueError: invalid literal for int()` |
| `window_days: 10**9` | 1 | `OverflowError: days=1000000000; must have magnitude <= 999999999` |
| `window_days: 3.7` | 0 | silently truncated to 3 (F6) |
| `end_date: "2030-02-30"` | 1 | invalid day rejected |

### snapshot
| Input | Exit | Behavior |
|---|---|---|
| `{}` | 0 | generates + **writes** a `phase_snapshots` row even on empty DB (`phase="maintenance"`, F12); audit P7 applies (write-on-read) |
| `{"unexpected": 1}` | 0 | ignored — handler takes no args |

### sessions
| Input | Exit | Behavior |
|---|---|---|
| `{}` | 0 | last 10 sessions as **raw dicts** (not Pydantic models) |
| `limit: 0` | 0 | `[]` |
| `limit: -1` | 1 | `BinderException: LIMIT/OFFSET cannot be negative` |
| `limit: "abc"` | 1 | `ValueError: invalid literal for int()` |
| `limit: 3.7` | 0 | truncated to 3 |
| `limit: 10**18` | 0 | fine (returns all) |

### injuries_list / injuries_seed
| Input | Exit | Behavior |
|---|---|---|
| `injuries_list {}` | 0 | raw dicts of whatever is stored (garbage rows listed verbatim) |
| seed `{}` | 1 | `KeyError: 'location'` |
| `location: "elbow"` | 0 | **stored — out of PainLocation vocab (F2/F9)** |
| `status: "banana"` | 0 | **stored** |
| `severity: "high"` | 1 | `ValueError: invalid literal for int()` |
| `severity: -1` / `11` | 1 | DB `CHECK` rejected (`ConstraintException`) — only table-level guard |
| `severity: "3"` / `3.7` | 0 | silently coerced to 3 |
| `location` = SQL-ish + `contraindicated_exercises` = SQL-ish | 0 | stored literally; DB intact |
| `contraindicated_exercises: ["skullcrushers"]` | 0 | **stored unprefixed-canonical — later misses the gate (F1)** |
| `contraindicated_exercises: "not-a-list"` | 1 | `ConversionException` (VARCHAR[] cast) |

### profile_get / profile_set
| Input | Exit | Behavior |
|---|---|---|
| `profile_get {}` (empty DB) | 0 | `{"profile": null}` |
| `profile_set {}` | 0 | **valid empty profile persisted (F3)** — onboarding gate disarmed |
| `goals: "not-a-list"` | 1 | rejected |
| `days_per_week: 99` | 1 | `le=7` rejected |
| `bodyweight_kg: -5` | 1 | `gt=0` rejected |
| `display_name: 123` + unknown field | 1 | type rejected; unknown field would be ignored (Pydantic default) but validation of known-bad fields fires first |

### memory_save / memory_search
| Input | Exit | Behavior |
|---|---|---|
| `{}` | 1 | `KeyError: 'text'` |
| `text: ""` / `"   "` | 1 | `ValueError: note text cannot be empty` |
| `kind: "banana"` | 1 | `'banana' is not a valid NoteKind` |
| `tags: "rows"` (string) | 1 | `ConversionException` (VARCHAR[] cast) — note: DB-layer, not Pydantic |
| `text: 123` | 1 | `AttributeError: 'int' object has no attribute 'strip'` |
| `search {}` | 0 | `[]` |
| `query: 123` | 1 | `BinderException: No function matches ... lower(INTEGER)` |
| `limit: -1` | 1 | `BinderException: LIMIT/OFFSET cannot be negative` |
| `limit: 10**12` | 0 | fine |

### dispatcher meta
| Input | Exit | Behavior |
|---|---|---|
| unknown command | 2 | `{"error": "unknown command '...'", "available": [...]}` |
| no args | 0 | help: `{"available": [...]}` |

## Orchestrator (no surface — direct calls, raw exceptions)

| Scenario | Result |
|---|---|
| `initialize_session(today=date(2030,1,11))` on clean DB | OK — `tokens=83, onboarding=True, phase=None, injuries=0` |
| `initialize_session(today="2030-01-01")` (string) | `RAISED TypeError: unsupported operand type(s) for -: 'str' and 'datetime.timedelta'` — no input validation at all |
| `initialize_session` after `injuries_seed {"location": "elbow"}` | `RAISED ValueError: 'elbow' is not a valid PainLocation` — **every subsequent call fails; F9 deferred-crash chain** |
| `finalize_session(None)` | `RAISED AttributeError: 'NoneType' object has no attribute 'phase'` |
| `finalize_session({"date": ...})` (dict) | `RAISED AttributeError: 'dict' object has no attribute 'phase'` |
| `finalize_session` with pain_flag exercise | OK — confirmation returned, `pain_flag` anomaly, `decision_log` +1 |
| `finalize_session` with mismatched arrays | `RAISED ValidationError` at model construction, nothing written |
| `initialize_session` with all 13 muscles prioritized | OK — `tokens=796` (< 3000; F11) |

## What lands in the DB (verified stored values)

```
sessions:   (2030-01-10, 'maintenance', 'Bench Press', sets=1000000000, rpe=[11.0])
sessions:   (2030-01-10, 'maintenance', 'Bench Press', sets=1, rpe=[inf])
injury:     ('elbow', 'active', 4, [])                       ← kills initialize_session
injury:     ("Robert'); DROP TABLE sessions;--", 'banana', 3, ['skullcrushers'])
profiles:   {"display_name":null,"goals":[...]}              ← written from `{}`
```

## Suggested priority read (links to audit tickets)

- F1/F2/F9 → audit T1/T2 (canonicalize + validate at the injuries boundary).
- F3 → add to T1 scope or a profile_set guard (refuse no-op empty profile, or
  require at least one goal) — ticket-sized addition.
- F4/F5 → extend `ExerciseModel` validators (arrays length parity incl. empties;
  `rpe ≤ 10`, finite floats; sane `sets` upper bound) — ticket-sized.
- F6/F7 → part of T8 (error vocabulary + coercion policy).
- F8 → part of T8/T4 (orchestrator error contract).
- F10 → document the CLI payload ceiling in `docs/adapters.md` (or accept; MCP
  unaffected).
