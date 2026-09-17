# Performance Benchmark — agentic-gym-coach (2026-09-17)

Observations only; no code was changed. Verdict up front: **every SPEC skill
budget passes with 3–12× margin in-process; the one miss is CLI cold start
(~1.85 s vs the documented 0.5 s), 97% of which is `import lancedb` — a store
v2 never uses.**

## Environment

- Linux 7.0.0-31-generic x86_64, 12 cores (idle dev machine; absolute numbers
  will vary, ratios are robust).
- Repo venv: Python 3.13.14; pinned deps (duckdb 1.5.4, polars 1.42.1,
  pydantic 2.13.4, lancedb 0.34.0).
- Throwaway DB `/tmp/gym_perf.duckdb`, schema via Alembic, `GYM_COACH_DUCKDB`
  set before any `skills.init` import. Single process. Production DB untouched.
- Dataset: repo convention from the `-m slow` guard — **500 sessions × 20 sets
  = 10,000 set-rows**, dates spread over the 28-day window, plus 1 active
  injury row (with a contraindication) and 1 user profile. Bulk-insert took
  6.6 s (executemany, not part of any budget).

## Results vs SPEC §3 budgets (median of N timed runs, warm connection)

| Function | Runs | Min | Median | Max | Budget | Verdict |
|---|---|---|---|---|---|---|
| `session_logger.log_session` | 20 | 6.8 ms | **7.0 ms** | 7.3 ms | <50 ms | PASS (7×) |
| `safety_gate.check_exercise_safety` (safe input) | 50 | 0.8 ms | **0.8 ms** | 1.1 ms | <10 ms | PASS (12×) |
| `safety_gate.check_exercise_safety` (banned input) | 50 | 0.8 ms | **0.9 ms** | 1.2 ms | <10 ms | PASS (11×) |
| `recovery.compute_recovery_score` | 50 | 4.9 ms | **4.9 ms** | 5.3 ms | <30 ms | PASS (6×) |
| `trend_analysis.get_specialization_trend` (28d) | 20 | 7.4 ms | **8.2 ms** | 10.5 ms | <50 ms | PASS (6×) |
| `trend_analysis.hard_sets_by_muscle` (28d) | 20 | 3.7 ms | **4.0 ms** | 5.9 ms | <50 ms | PASS (13×) |
| `snapshot.generate_phase_snapshot` | 10 | 16.1 ms | **16.7 ms** | 19.5 ms | <200 ms | PASS (12×) |
| `profile.get_profile` (no budget; reference) | 50 | 1.0 ms | 1.2 ms | 1.4 ms | — | — |
| `profile.set_profile` (no budget; incl. goal-change audit) | 20 | 2.4 ms | 2.5 ms | 2.6 ms | — | — |
| `orchestrator.initialize_session` composite (1 priority muscle) | 20 | 8.0 ms | 8.2 ms | 9.0 ms | — | — |

Notes:
- The banned-input safety check is no slower than the safe path — the gate is
  a single indexed-ish scan of `injury_status`; fine at realistic injury-row
  counts.
- `initialize_session` at 8 ms confirms Tier-1 assembly is cheap enough to run
  per session start (relevant to audit Q1 — wiring it would cost nothing).
- First (cold) call per process adds ~50–100 ms of DuckDB connect + module
  import on top of the medians above — still inside every budget except the
  CLI case below.

## The one MISS: CLI cold start

| Measurement | Runs | Min | Median | Max | Budget | Verdict |
|---|---|---|---|---|---|---|
| `coach_tools.py recovery '{}'` full subprocess wall time | 5 | 1843 ms | **1852 ms** | 1931 ms | 500 ms ("bash 0.5s budget per call", `coach_tools.py:7`) | **MISS (3.7×)** |

**Attribution (import cost, measured separately):**

| Import | Time |
|---|---|
| `import lancedb` | **1.80 s** |
| `import duckdb` | 0.13 s |
| `import polars` | 0.19 s |
| `import pydantic` | 0.08 s |
| `import coach_tools` (module only — handlers import lazily) | 0.03 s |
| bare interpreter startup | 0.02 s |

`skills/init.py` does `import lancedb` at module top (line 18), so every CLI
invocation — and every MCP tool call that lazily imports a skill — pays ~1.8 s
for a vector store that AGENTS.md itself marks "deferred — Tier 3 uses DuckDB
tables in v2". **Ticket-sized fix, no behavior change:** move
`import lancedb` inside `get_lance()` (nothing in v2 calls it; if anything
did, it would still work). Expected CLI cold start after the fix: ~150–200 ms,
comfortably under the 0.5 s budget. MCP surfaces amortize imports across the
server process lifetime and are unaffected in steady state (only server
startup pays it).

## Slow-test guard

`.venv/bin/python -m pytest -m slow -q` → **1 passed, 136 deselected, 12.0 s**
(`test_perf_under_50ms_on_synthetic_set` builds the same 10K-set dataset
in-DB and asserts trend < 100 ms; measured trend median here is 8.2 ms —
12× margin on the SPEC's 50 ms).

## Full-suite regression check (new tests from this batch)

`.venv/bin/python -m pytest -q` → **136 passed, 1 deselected (slow), 4.5 s** —
includes the 77 new edge-case tests added in
`docs/reviews/`-batch-2 (`tests/**/test_*_extra.py`), all single-process,
offline, deterministic (fixed dates; no `date.today()` dependencies except
where the code under test owns the clock).

## Summary

- In-process skill contracts: **all PASS**, worst margin 6× (recovery), best 13×
  (hard_sets_by_muscle). No budget is at risk from data growth patterns tested
  here.
- The only real latency problem is environmental, not algorithmic: **lancedb
  import tax on every CLI call**. One-line lazy import fixes it (recorded as
  ticket-sized; not applied — this batch is report + tests only).
