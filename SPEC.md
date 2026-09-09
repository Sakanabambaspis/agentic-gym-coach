DESIGN SPECIFICATION: Agentic Gym Coach (v2)

POSITIONING
A general-purpose, local-first gym coach engine. Any user, any goal. Professional doctrine comes exclusively from two vendored book-skills (procedural disclosure, no LLM-invented physiology or nutrition science); the user's goals, constraints, and history are validated data (DuckDB), never prompt text. A deterministic safety layer gates every exercise suggestion against recorded injuries.

1. KNOWLEDGE ARCHITECTURE
The only professional knowledge sources (v1 documents were removed as unsourced):
- docs/knowledge/helms-training-pyramid/ — Muscle & Strength Pyramid: Training (2nd ed.)
- docs/knowledge/helms-nutrition-pyramid/ — Muscle & Strength Nutrition Pyramid (v1.0)

Precedence: (1) deterministic safety layer, (2) vendored skills (doctrine), (3) mechanics docs. Each skill's SKILL.md is a topic router; agents load at most one knowledge file per turn (procedural disclosure).

2. DATA ARCHITECTURE
Local-first embedded stack: DuckDB (data/gym_coach.duckdb), Polars (never Pandas), Pydantic V2 at every boundary, Alembic migrations (never hand-edit schema).

2.1 Tables (post migration 0002)
- sessions — date, phase VARCHAR (vocab: PhaseType enum in models/enums.py), pre_recovery_score, exercises STRUCT(name, muscle_group ENUM, sets, reps[], rpe[], weight_kg[], tempo, form_quality, pain_flag, notes)[], post_feedback
- injury_status — location VARCHAR (vocab: PainLocation enum), status, severity 0–10, contraindicated_exercises[], safe_alternatives[]
- phase_snapshots — snapshot_date PK, phase VARCHAR, body_weight_kg, waist_cm, specialization_lifts JSON, tendon_status_summary JSON, key_insight, next_phase_adjustment
- decision_log — event_type, trigger_signal, reasoning_chain, alternative_rejected, future_validation_tag (audit trail)
- user_profiles — id UUID PK, updated_at TIMESTAMPTZ, payload JSON (append-only history; latest row = current UserProfile; goal changes audited)
- memory_notes — id UUID PK, created_at, kind, text, tags[] (Tier 3; manual-save only; substring/tag search)

2.2 Vocabulary policy
DB stores phase/location as VARCHAR; models/enums.py is the controlled vocabulary, enforced by Pydantic at the boundary. Extending a vocabulary = edit the enum, no migration. (Supersedes v1 SPEC §1.2 "enforce via SQL ENUM".)

2.3 Volume semantics (Training ch03)
Volume currency = effective hard sets per muscle per week: sets × form_mult (form_quality < 3 ⇒ 0.5), primary + secondary contributions 1:1 (models/exercise_catalog.SECONDARY_OVERLAP), bodyweight sets count. Tonnage is reference detail only. est_1rm from reps ≤ 6 sets only ("~5RM or heavier", ch04).

3. SKILL INVENTORY (deterministic Python, no LLM logic)
- session_logger.log_session(SessionInput) -> LogConfirmation  (<50ms)
- safety_gate.check_exercise_safety(str) -> SafetyResult  (<10ms, deterministic)
- recovery.compute_recovery_score(date) -> RecoveryScore  (<30ms)
- trend_analysis.get_specialization_trend(muscle, window_days, end_date) -> TrendReport; hard_sets_by_muscle(start, end)  (<50ms)
- snapshot.generate_phase_snapshot() -> PhaseSnapshot (incl. computed block_state)  (<200ms)
- profile.get_profile()/set_profile()/derive_priority_muscles()
- memory.add_note()/search_notes()  (Tier 3, manual-save policy)
- visual_delta.compare_photos(a, b) -> VisualDelta  (stub; optional vision API)

4. SURFACES
- CLI: python coach_tools.py <cmd> '<json>' (JSON stdout; {"error":...} + exit 1)
- MCP: mcp_server.py (stdio; 12 coach tools + coach_doctrine) — the cross-runtime tool surface
- Persona: docs/COACH_PROMPT.md (canonical; rendered into runtime agent files by scripts/sync_adapters.py)
- Native adapter: .opencode/ (agents + TS tools). See docs/adapters.md.

5. INVARIANTS
- Skills are pure deterministic code; reasoning happens in the orchestrator/agent.
- Safety gate result is binding: safe=false ⇒ never suggest the exercise.
- Tier 3 memory writes require an explicit user command; never auto-write.
- Cite retrieved values; missing data = "I don't have that data." Never fabricate.
- Every plan modification (incl. goal changes) lands in decision_log.
- Full offline operation (no cloud except optional vision API for visual_delta).
- Tests never touch production data (conftest.py env redirect). Single-process pytest.
