# THIN_MUSCLE_OS — Agentic Gym Coach

Local-first fitness coach for the lean-muscle physique (薄肌). Chat with it like a real coach — it knows your logs, respects your tendinopathy, and never forgets your priorities.

```bash
cd agentic_gym_coach
opencode          # launches the Coach — default agent on Tab
```

**Log sessions in plain language:**
```
Log today: Incline Bench 3x8 @ RPE 8, Lateral Raise 4x12 @ RPE 9, Pull-Up 3x6
```

**Ask anything:**
```
How's my rear delt doing?                 → trend analysis
Should I do Skull Crushers tonight?       → safety gate (deterministic)
Plan a 4-week side-delt block.            → phase planning with knowledge docs
What's my recovery looking like?          → recovery score
```

The Coach reads your session history, checks your active injuries, applies physiological rules, and proposes plans — all through conversation. No dashboards to click. No forms to fill.

## How it works

- **You talk.** The Coach runs on opencode — the same CLI you already have.
- **It remembers.** Every session is validated by Pydantic and persisted to DuckDB.
- **It verifies.** `coach_safety_check` cross-references `injury_status` before suggesting any exercise. Deterministic — never suggests a contraindicated movement.
- **It analyzes.** Effective volume (form_quality < 3 discounted 50%), Epley 1RM, stall detection, recovery heuristics. All derived from raw logs, all pure Python.
- **It plans.** 薄肌 specialization methodology inlined: upper chest → side delts → rear delts → back detail, with realistic volume landmarks and RPE autoregulation.

## Stack

Python 3.11+ · DuckDB · Polars · Pydantic V2 · Alembic · opencode (agent runtime)

## Files you should know

| What | Where |
|---|---|
| Coach agent | `.opencode/agents/coach.md` |
| Custom tools | `.opencode/tools/coach_*.ts` |
| Dispatcher | `coach_tools.py` |
| Gym knowledge | `docs/knowledge/*.md` |
| 6 analysis skills | `skills/{session_logger,safety_gate,recovery,trend_analysis,snapshot,visual_delta}.py` |
| Pydantic models | `models/` |
| DuckDB schema | `migrations/` (Alembic) |
| Frozen historical log | `docs/reference/sample_log.md` |

## One-time setup

```bash
pip install -r requirements.txt
python scripts/ingest_log.py --reset          # import 64 historical sessions
opencode                                       # start chatting with Coach
```

## Running tests

```bash
python -m pytest -q                            # 38 tests, ~6s
python -m pytest -m slow -q                    # perf guard on 10K rows
```

## Design principles

- Skills are pure deterministic code — zero LLM logic inside them.
- `form_quality < 3` discounts that set's volume 50%. `pain_flag = true` tags the session for review.
- `safety_gate` is the only source of truth for contraindications. If it says unsafe, no alternative is suggested.
- The DuckDB file is canonical — `log.md` is retired to a frozen reference.
- Full offline operation. Optional vision API for `visual_delta`.
- Tier 3 semantic memory (long-term) never writes without explicit user command.
