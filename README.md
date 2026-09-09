# Agentic Gym Coach

A general-purpose, local-first gym coach you talk to like a real one. It
onboards your goals, remembers your profile, logs your sessions, gates every
exercise suggestion against your injuries, and answers training + nutrition
questions from vendored professional sources — never invented science.

**First conversation (onboarding):** it asks your goals (hypertrophy,
strength, fat loss, …), physique target (ripped / athletic / bulky), training
age, schedule, equipment, and injuries — then coaches toward YOUR profile.

```text
You:  I want to put size on my side delts. 4 days a week, commercial gym.
Coach: <onboards profile> → builds a program from the training pyramid,
       volume matched to your training age, 2×/week delts.

You:  Log today: Incline Bench 3x8 @ RPE 8, Lateral Raise 4x12 @ RPE 9
You:  Should I do skull crushers tonight?        → deterministic safety gate
You:  How many calories to get ripped?           → nutrition pyramid ch02
You:  My bench is stuck.                         → plateau flowchart, free wins first
You:  Remember I hate barbell rows.              → long-term memory (manual only)
```

## How it works

- **Doctrine from books, not vibes.** Two vendored skills — *Muscle & Strength
  Pyramid: Training* (2nd ed.) and *Muscle & Strength Nutrition Pyramid* — are
  the only professional knowledge, loaded on demand (procedural disclosure).
- **You are data.** Goals, training age, schedule, priorities, injuries, and
  memory notes live in DuckDB as validated, versioned records — the coach
  never hardcodes who you are. Goal changes are audited.
- **It verifies.** `coach_safety_check` cross-references `injury_status`
  before any exercise suggestion. Deterministic — no negotiation.
- **It measures honestly.** Volume = effective hard sets (form-discounted,
  overlap-inclusive). 1RM estimates only from ~5RM-or-heavier sets. Missing
  data is stated, never fabricated.
- **It works everywhere.** One Python core; every MCP-capable runtime
  (Claude Code, ZCode, Cursor, Codex CLI, …) attaches the same
  `mcp_server.py`.

## Stack

Python 3.11+ · DuckDB · Polars · Pydantic V2 · Alembic · MCP

## One-time setup

```bash
uv venv .venv && uv pip install -r requirements.txt
alembic upgrade head      # bootstrap data/gym_coach.duckdb
python scripts/ingest_log.py --reset   # optional: import historical log.md
```

## Run the Coach

- **Any MCP runtime:** point it at `.venv/bin/python mcp_server.py` and use
  [docs/COACH_PROMPT.md](docs/COACH_PROMPT.md) as the agent's system prompt —
  see [docs/adapters.md](docs/adapters.md) for per-runtime wiring.

## Running tests

```bash
python -m pytest -q          # 56 tests, ~3s
python -m pytest -m slow -q  # perf guard on 10K rows
```

## Design principles

- Skills are pure deterministic code — zero LLM logic inside them.
- The safety gate is the only source of truth for contraindications.
- Volume is hard sets (form_quality < 3 discounts 50%), never tonnage.
- Long-term memory writes never happen without an explicit user command.
- The DuckDB file is canonical; full offline operation.
