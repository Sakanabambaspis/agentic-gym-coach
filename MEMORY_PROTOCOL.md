MEMORY PROTOCOL: Multi-Session State Management

CORE PHILOSOPHY
Memory is not a chat history; it is a physiological state machine. The agent must never rely on LLM context windows to remember training history, injury status, or program phases. All persistent state lives in structured storage. The LLM only reasons overretrieved state.

⚠️ CARDINAL RULE: If data matters for tomorrow’s session, it MUST be written to DuckDB/LanceDB today. Context window memory is ephemeral and untrustworthy. Treat it as RAM; treat the database as disk.

THE THREE-TIER MEMORY ARCHITECTURE

Tier 1: Working Memory (Session Context)
Scope: Current active session + immediate prerequisites.
Storage: In-memory Pydantic objects injected into system prompt at session start.
Max Size: ~3K tokens. Hard limit enforced by orchestrator.
Contents:
    Today’s planned workout (from sessions table where date = today)
    Last 3 sessions of same exercises (via get_specialization_trend)
    Active injury flags (via check_exercise_safety)
    Current phase parameters (from latest phase_snapshots)
    Pre-session recovery score (via compute_recovery_score)
Lifecycle: Loaded at session init → Updated in real-time during logging → Discarded at session end (persisted changes already written to Tier 2).
Refresh Trigger: User says "refresh plan" or recovery score changes mid-session.

Tier 2: Episodic Memory (Recent History & Trends)
Scope: Rolling 90 days of structured data + compressed weekly summaries.
Storage: DuckDB (metrics) + LanceDB (subjective notes with metadata).
Retrieval Method: Hybrid search via skills. NEVER dump raw tables into context.
Compression Protocol:
    Daily: Raw session logs stored as-is.
    Weekly (Auto): planned weekly summary compression (aggregates daily logs into per-muscle effective hard sets, avg RPE, pain incidents, key subjective themes, progress vs. target). NOT YET IMPLEMENTED in v2 — the phase snapshot covers the 4-week view until it lands.
    Monthly: generate_phase_snapshot() creates anchor document. Weekly summaries older than 90 days are archived but remain queryable.
Query Patterns:
    Quantitative: SQL/Polars via trend_analysis.py
    Qualitative: Semantic search via LanceDB with metadata filters (date_range, muscle_group, pain_flag)
    Hybrid: Combine both results in orchestrator before LLM reasoning

Tier 3: Semantic Memory (Long-Term Identity & Knowledge)
Scope: Goal definition, validated preferences, milestone archive.
Storage (v2): DuckDB — `user_profiles` (validated, append-only UserProfile JSON; latest row = current) + `memory_notes` (freeform notes, substring/tag search). LanceDB semantic search is deferred to v3 (no offline embedder in deps); the protocol's intent is unchanged, only the storage engine.
Write Policy: memory_notes — MANUAL APPROVAL REQUIRED ("save this" / "remember this"); never auto-write. user_profiles — written after the coach echoes the profile and the user confirms (onboarding or goal change); goal changes are audited to decision_log automatically.
Contents:
    Goal definitions (kind, physique_target, target muscles, metrics, deadlines)
    Validated exercise preferences ("chest-supported rows > barbell rows")
    Injury history archive (resolved events with lessons learned)
    Milestones and coaching observations
Retrieval Trigger: Session start (profile drives priorities), phase transitions, program redesigns, meta-questions ("why do we prioritize X?"), anomaly resolution requiring historical context.

STATE TRANSITION PROTOCOLS

2.1 Session Start Sequence
Pseudocode for orchestrator
def initialize_session():
    # 0. Onboarding gate — a coach without a profile asks, never assumes
    profile = get_profile()          # None ⇒ flag onboarding_required

    # 1. Load Tier 1 working memory
    recovery = compute_recovery_score(today)
    injuries = get_active_injuries()
    phase = get_current_phase()
    priorities = derive_priority_muscles(profile)   # profile-driven, not hardcoded
    last_sessions = {m: get_specialization_trend(m, window=14) for m in priorities}

    # 2. Inject into system prompt as structured block
    working_memory = WorkingMemoryState(
        recovery=recovery,
        injuries=injuries,
        phase=phase,
        onboarding_required=profile is None,
        recent_trends=last_sessions
    )

    # 3. Safety pre-check
    if recovery.score < 60 or injuries.active_count > 0:
        flag_autoregulation_required(working_memory)

    return working_memory

2.2 Session End Sequence
def finalize_session(session_data: SessionInput):
    # 1. Validate & persist to Tier 2
    validated = SessionModel(**session_data)
    log_session(validated)  # Writes to DuckDB
    
    # 2. Auto-tag subjective feedback
    if validated.post_feedback:
        tag_and_store_subjective(validated.post_feedback, validated.date)
    
    # 3. Anomaly detection
    anomalies = detect_anomalies(validated)
    if anomalies:
        log_decision_trigger(anomalies)  # For audit trail
    
    # 4. Clear Tier 1 working memory
    clear_working_memory()
    
    # 5. Schedule compression if needed
    if is_week_end(validated.date):
        schedule_weekly_summary(validated.date)

2.3 Phase Transition Protocol
When user initiates new phase OR snapshot interval reached:
Run generate_phase_snapshot()
Present snapshot to user for review
On confirmation: write to phase_snapshots table + propose semantic memory updates
Update current phase in working memory config
Log transition event in decision audit trail

MEMORY SAFETY & INTEGRITY GUARDS

3.1 Write Protection Matrix
Memory Tier   Auto-Write Allowed?   Approval Required?   Validation Layer
Tier 1 (Working)   Yes (session-scoped)   No   Pydantic runtime validation

Tier 2 (Episodic)   Yes (structured logs)   No   Schema constraints + unit tests

Tier 2 (Summaries)   Yes (auto-generated)   No   Compression skill unit tests

Tier 3 (Semantic)   NO   YES (explicit user cmd)   Human review + diff preview

Decision Log   Yes (audit entries)   No   Structured schema enforcement

3.2 Drift Prevention Mechanisms
Monthly Calibration Check: Agent prompts user: "Based on my records, your current priority is X and elbow status is Y. Is this still accurate?" Discrepancies trigger semantic memory update proposal.
Snapshot Consistency Validation: Every snapshot cross-references raw logs. If aggregated metrics deviate >5% from recomputed values, flag data integrity issue.
Orphan Detection: Weekly scan for subjective notes without linked session data. Flag for manual tagging or archival.

3.3 Recovery from Memory Failure
If database corruption or missing data detected:
Halt all planning operations
Notify user with specific error + affected date range
Offer recovery options: restore from backup / rebuild from raw exports / manual re-entry
NEVER silently fabricate or interpolate missing physiological data
Log incident in decision audit trail as memory_integrity_event

IMPLEMENTATION CHECKLIST FOR CODING AGENT

Before marking memory system complete, verify:
[ ] Tier 1 injection stays under 3K tokens on max-load test case
[ ] Weekly summary generation produces consistent output across runs (deterministic)
[ ] Semantic memory write attempt without approval raises PermissionError
[ ] Hybrid search returns relevant subjective notes filtered by injury/muscle metadata
[ ] Session end sequence persists ALL data before clearing working memory
[ ] Phase snapshot matches manual recalculation within 5% tolerance
[ ] Monthly calibration prompt triggers correctly based on date logic
[ ] Full offline operation verified (no cloud calls except optional vision API)
[ ] Unit tests cover: empty sessions, null feedback, concurrent writes, schema migration

COGNITIVE BINDING: HOW TO REASON OVER MEMORY
Embed in agent instructions:

When answering ANY question about progress, status, or planning:
Identify which memory tier holds the answer
Call the appropriate skill to retrieve structured data
NEVER paraphrase from memory; cite retrieved values explicitly
If retrieval fails or returns null, say "I don't have that data" — do not guess
Cross-reference Tier 2 metrics with Tier 2 subjective notes before concluding
For long-term pattern questions, check Tier 3 semantic memory FIRST, then validate against Tier 2 trends
Always include temporal context ("over the last 4 weeks" not "recently")