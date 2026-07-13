# THIN_MUSCLE_OS — Agentic Gym Coach

Local-first fitness analytics for the lean-muscle (薄肌) physique. Track raw gym sessions, get derived metrics — effective volume, recovery scores, 1RM estimates, phase snapshots, stall detection, safety gating against tendinopathy.

## Tech

Python 3.11+ · DuckDB (OLAP) · Polars · LanceDB (vectors) · Pydantic V2 · Alembic · Plotly

## Quick start

```bash
pip install -r requirements.txt
```

Backfill existing logs:
```bash
python scripts/ingest_log.py log.md         # append new sessions
python scripts/ingest_log.py --reset        # rebuild from scratch
```

Run tests (fast suite):
```bash
python -m pytest -q
```

Run performance guard (10K rows, <100ms):
```bash
python -m pytest -m slow -q
```

## Structure

- `models/` — Pydantic schemas (session, injury, snapshot, memory, exercise catalog)
- `migrations/` — Alembic (DuckDB schema changes only through migration)
- `skills/` — Six deterministic analysis modules: `session_logger`, `safety_gate`, `recovery`, `trend_analysis`, `snapshot`, `visual_delta`
- `orchestrator.py` — Tier 1 working memory + decision audit trail
- `scripts/ingest_log.py` — Markdown parser for `log.md`
- `data/` — DuckDB + LanceDB (gitignored, reproducible from `log.md`)

## Commands

| `/status` | DB health, skill coverage, last snapshot |
| `/snapshot` | Generate 4-week phase snapshot |
| `/calibrate` | Monthly calibration pass |
| `/help` | Full command list |

## Design

- Skills are pure code (zero LLM logic). Analysis results feed the LLM orchestrator.
- `form_quality < 3` → 50% volume discount. `pain_flag = true` → session tagged for review.
- `safety_gate.check_exercise_safety()` is deterministic — never suggests contraindicated exercises.
- Queries <100ms on 10K-row synthetic datasets.
- Full offline operation. Vision API optional for `visual_delta`.
