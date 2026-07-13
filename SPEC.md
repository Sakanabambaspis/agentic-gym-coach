DESIGN SPECIFICATION: Agentic Gym Coach Workspace (Project: THIN_MUSCLE_OS)

CORE DIRECTIVE & PERSONA
You are building an autonomous fitness analytics workspace for a "Master Coach + Senior Backend Engineer" user. The system must prioritize physiological precision, retrieval speed (<100ms), and tendon safety over generic tracking.
Aesthetic Goal: 薄肌 (Lean Muscle/Greek God) – Prioritizes upper chest, side delts, rear delts, back detail.
Medical Constraint: Chronic elbow/knee tendinopathy history. Safety gates are non-negotiable.
Engineering Standard: Code-first analytics. No heavy LLM frameworks for data ops. Structured state > unstructured text.

DATA ARCHITECTURE (The Notebook → Database)
Create a local-first, embedded data stack. Do NOT use external cloud databases unless explicitly requested.

1.1 Tech Stack Selection
OLAP Engine: DuckDB (persistent file mode: data/gym_coach.duckdb)
DataFrame Library: Polars (strictly preferred over Pandas for performance)
Vector Store: LanceDB (embedded, zero-copy integration with DuckDB/Polars)
Schema Management: Alembic or raw SQL migrations in migrations/ folder
Serialization: Pydantic V2 for all data models

1.2 Core Schema Requirements
Implement these tables with exact typing. Use enums for controlled vocabularies.

-- Controlled Vocabularies (Enforce Strictly)
CREATE TYPE muscle_group AS ENUM ('side_delt', 'rear_delt', 'upper_chest', 'mid_back', 'lats', 'biceps', 'triceps', 'quads', 'hamstrings', 'glutes', 'core', 'serratus');
CREATE TYPE phase_type AS ENUM ('internship_maintenance', 'bridge_reconditioning', 'specialization_lean_bulk', 'diet_break', 'mini_cut', 'deload');
CREATE TYPE pain_location AS ENUM ('left_elbow', 'right_elbow', 'left_knee', 'right_knee', 'lower_back', 'none');

-- Primary Session Log
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    phase phase_type NOT NULL,
    pre_recovery_score INT CHECK (pre_recovery_score BETWEEN 0 AND 100),
    exercises STRUCT(
        name VARCHAR,
        muscle_group muscle_group,
        sets INT,
        reps INT[],          -- Array per set
        rpe FLOAT[],         -- Array per set
        tempo VARCHAR,       -- e.g., '3-1-X-1'
        form_quality INT CHECK (form_quality BETWEEN 1 AND 5),
        pain_flag BOOLEAN,
        notes TEXT
    )[],
    post_feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Injury State Machine (Critical Safety Layer)
CREATE TABLE injury_status (
    id UUID PRIMARY KEY,
    location pain_location NOT NULL,
    status VARCHAR NOT NULL, -- 'active', 'resolving', 'resolved', 'chronic_baseline'
    severity INT CHECK (severity BETWEEN 0 AND 10),
    contraindicated_exercises VARCHAR[], -- List of banned exercise names
    safe_alternatives VARCHAR[],
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase Snapshots (Compressed State Anchors)
CREATE TABLE phase_snapshots (
    snapshot_date DATE PRIMARY KEY,
    phase phase_type,
    body_weight_kg DECIMAL(5,2),
    waist_cm DECIMAL(5,2),
    specialization_lifts JSONB, -- {"exercise": "est_1rm"}
    tendon_status_summary JSONB,
    key_insight TEXT,
    next_phase_adjustment TEXT
);

1.3 Data Ingestion Rules
All writes MUST go through Pydantic validators before hitting DuckDB.
form_quality < 3 automatically discounts that set’s volume by 50% in all analytics.
pain_flag = true triggers immediate warning log and tags the session for review.

TOOLING & SCRIPTS (The Agent’s Hands)
Create a skills/ directory. Each skill is a standalone Python module with typed inputs/outputs. The LLM calls these via function calling; it NEVER writes raw SQL for analysis.

2.1 Required Skills Inventory
Skill File   Function Signature   Purpose   Performance Target
trend_analysis.py   get_specialization_trend(muscle: MuscleGroup, window_days: int = 28) -> TrendReport   Returns effective volume, RPE trend, strength estimate, stall detection.   < 50ms

safety_gate.py   check_exercise_safety(exercise: str) -> SafetyResult   Cross-references injury_status table. Returns safe/unsafe + alternatives.   < 10ms

recovery.py   compute_recovery_score(date: date) -> RecoveryScore   Aggregates sleep, HRV, recent load, pain. Returns 0-100 + adjustment recommendation.   < 30ms

snapshot.py   generate_phase_snapshot() -> PhaseSnapshot   Compresses last 4 weeks into anchor document. Saves to DB + semantic memory.   < 200ms

visual_delta.py   compare_photos(date_a: date, date_b: date) -> VisualDelta   Calls vision API, returns structured muscle group changes. Caches results.   N/A (API bound)

session_logger.py   log_session(data: SessionInput) -> LogConfirmation   Validates, transforms, writes to DuckDB. Returns confirmation + anomaly flags.   < 50ms

2.2 Skill Implementation Standards
No LLM inside skills. Skills are deterministic code. Reasoning happens in the orchestrator.
Return Pydantic models, not dicts. Enables strict contract enforcement.
Include docstrings with examples. The coding agent needs these to generate correct function-calling schemas.
Unit tests required. Create tests/test_skills/ with synthetic data fixtures. Every skill must pass tests before deployment.

AGENT COGNITION (The Skill Files / System Prompt)
Embed these cognitive frameworks into the agent’s system prompt or AGENT_INSTRUCTIONS.md.

3.1 Analysis Mindset Protocols
ANALYSIS PROTOCOLS
ANOMALY FIRST: Always check for stalls, pain spikes, or recovery drops BEFORE reporting progress.
EFFECTIVE VOLUME ONLY: Never report raw sets/reps. Always apply form_quality discount and pain filtering.
TEMPORAL WEIGHTING: Recent 7 days > previous 21 days for subjective feedback. Injury events have PERMANENT weight.
CAUSAL BRIDGING: When user reports subjective feeling ("flat", "pump", "pain"), ALWAYS cross-reference with objective data (volume, calories, sleep) before responding. Generate hypothesis, not just acknowledgment.
SAFETY OVERRIDE: If check_exercise_safety() returns unsafe, NEVER suggest that exercise regardless of user request or program template. Offer alternatives from SafetyResult.

3.2 Decision Audit Trail Requirement
Every plan modification MUST log to decision_log table:
Trigger signal (what data prompted change)
Reasoning chain (why this specific adjustment)
Alternative rejected (what else was considered)
Future validation tag (how we’ll know if this was correct)

3.3 Communication Style
Pre-session: Concise directive. Recovery score → Key adjustment → Today’s priority. No fluff.
Post-session: Acknowledge + auto-tag feedback. Only flag anomalies.
Weekly review: Data visualization artifact + 3-bullet insight + 1 actionable recommendation.
NEVER say "Based on your logs..." Say "Your rear delt effective volume is +18% over 4 weeks." Be the instrument, not the narrator.

PROJECT STRUCTURE TEMPLATE
Instruct the coding agent to scaffold exactly this structure:

gym-coach-workspace/
├── SPEC.md                  # This document
├── AGENT_INSTRUCTIONS.md    # Cognitive protocols for LLM
├── data/
│   ├── gym_coach.duckdb     # Persistent OLAP store
│   └── lance_db/            # Embedded vector store
├── migrations/              # Schema version control
├── skills/
│   ├── init.py
│   ├── trend_analysis.py
│   ├── safety_gate.py
│   ├── recovery.py
│   ├── snapshot.py
│   ├── visual_delta.py
│   └── session_logger.py
├── models/                  # Pydantic schemas
│   ├── session.py
│   ├── injury.py
│   └── snapshot.py
├── tests/
│   ├── fixtures/            # Synthetic test data
│   └── test_skills/
├── notebooks/               # Exploratory analysis (optional)
└── requirements.txt         # duckdb, polars, lancedb, pydantic, pytest

VALIDATION CHECKLIST FOR CODING AGENT
Before considering implementation complete, verify:
[ ] DuckDB queries execute in <100ms on 10K row synthetic dataset
[ ] check_exercise_safety() blocks contraindicated exercises deterministically
[ ] Pydantic validation rejects malformed session logs before DB write
[ ] Unit tests cover edge cases (empty arrays, null RPE, pain during exercise)
[ ] Agent can generate phase snapshot without manual intervention
[ ] System works fully offline (no cloud dependencies except optional vision API)