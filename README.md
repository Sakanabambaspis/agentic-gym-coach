# THIN_MUSCLE_OS — Agentic Gym Coach

Local-first fitness analytics for the lean-muscle (薄肌) physique. Track raw gym sessions, get derived metrics — effective volume, recovery scores, 1RM estimates, phase snapshots, stall detection, safety gating against tendinopathy.

## Tech

Python 3.11+ · DuckDB (OLAP) · Polars · LanceDB (vectors) · Pydantic V2 · Alembic · Plotly · opencode (agent harness)

## Quick start

```bash
pip install -r requirements.txt
opencode            # launches the Coach agent — log sessions or ask training questions
```

Talk to the Coach in plain English:
```
Log today: Incline Bench Press 3x8 @ RPE 8, Lateral Raise 4x12 @ RPE 9
How's my rear delt doing over the last 4 weeks?
Should I do Skull Crushers tonight?
Plan a 4-week side-delt specialization block.
```

Press **Tab** to switch to Build / Plan agents if you want to code on the workspace itself.

Bulk-import a historical markdown log (one-shot, replaces `sessions` table):
```bash
python scripts/ingest_log.py --reset docs/reference/sample_log.md
```

Run tests (fast suite):
```bash
python -m pytest -q
```

Run performance guard (10K rows, <100ms):
```bash
python -m pytest -m slow -q
```

## Source of truth

`data/gym_coach.duckdb` is canonical. `docs/reference/sample_log.md` is the frozen historical log (64 sessions already ingested). New logs enter the DB only through the Coach's `coach_log_session` tool or `scripts/ingest_log.py`.

## Structure

- `.opencode/agents/coach.md` — Coach agent system prompt (inlines core safety rules)
- `.opencode/tools/coach_*.ts` — 8 custom tools (thin TS wrappers over `coach_tools.py`)
- `coach_tools.py` — Python dispatcher: `python coach_tools.py <cmd> <json>`
- `docs/knowledge/` — methodology, tendinopathy, progression, exercise catalog, safety
- `models/` — Pydantic schemas (session, injury, snapshot, memory, exercise catalog)
- `migrations/` — Alembic (DuckDB schema changes only through migration)
- `skills/` — Six deterministic analysis modules: `session_logger`, `safety_gate`, `recovery`, `trend_analysis`, `snapshot`, `visual_delta`
- `orchestrator.py` — Tier 1 working memory + decision audit trail
- `scripts/ingest_log.py` — bulk markdown importer (one-shot)
- `data/` — DuckDB + LanceDB (gitignored)

## Commands

| `/status` | DB health, skill coverage, last snapshot |
| `/snapshot` | Generate 4-week phase snapshot (also via `coach_snapshot` tool) |
| `/calibrate` | Monthly calibration pass |
| `/help` | Full command list |

The Coach also surfaces training actions live in conversation — just ask.

## Design

- Skills are pure code (zero LLM logic). Analysis results feed the LLM orchestrator.
- `form_quality < 3` → 50% volume discount. `pain_flag = true` → session tagged for review.
- `safety_gate.check_exercise_safety()` is deterministic — never suggests contraindicated exercises.
- Queries <100ms on 10K-row synthetic datasets.
- Full offline operation. Vision API optional for `visual_delta`.
