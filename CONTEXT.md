# Agentic Gym Coach

A local-first gym-coach engine: a deterministic DuckDB core holds the user's
physiological state; an LLM coach reasons over it through `coach_*` tools,
with doctrine sourced exclusively from two vendored Helms book-skills.

## Language

**Intake assessment**:
The standardized bucket list of everything the coach must know before making
programming decisions, plus the act of scanning stored state against it.
There is exactly one intake with one mode of operation — a first-ever user
and a returning user run the same scan; they differ only in how much it finds.
_Avoid_: onboarding (implies a one-time event), re-onboarding, re-assessment mode

**Bucket list (INTAKE_CHECKLIST)**:
The canonical list of intake fields in `models/intake.py`. Every entry cites
its vendored book chapter or is explicitly labeled HEURISTIC — never neither.
_Avoid_: questionnaire, form

**Gate**:
A per-domain readiness flag (`training_ready` / `nutrition_ready`) that is
false while any blocking field gating that domain is missing. Gates are soft:
they stop the coach from *volunteering* plans, not from answering.
_Avoid_: blocking requirement, hard gate

**Provisional plan**:
A plan produced despite a closed gate, on explicit user insistence, which
opens by naming every missing field and the limitation each imposes.
Never produced silently.
_Avoid_: best-guess plan, fallback plan

**Collected**:
A field whose storage holds a real answer. An explicit `false` is collected;
an emptied list field on the profile is collected ("asked, nothing applies")
— except the fields flagged empty-means-missing (`goals`,
`weekly_availability`), where empty means never-asked. An empty injury table
is missing: no rows = nothing reported. Only absence means missing.
_Avoid_: valid, known-good (collected values can still be stale)

**Derived field**:
A value the coach computes from collected data and observation instead of
asking (priority muscles, from goal targets and observed weak points).
Never an intake question; stored only after the user confirms.
_Avoid_: computed field, inference

**Staleness signal (session_gap)**:
Weeks since the last logged session, computed at snapshot/session start.
Crossing the threshold (`REASSESSMENT_GAP_WEEKS`, a labeled heuristic — the
books do not cover detraining timelines) makes confirming collected values
mandatory before programming.
_Avoid_: detraining detection (implies book-sourced physiology)

**Effective hard sets**:
The volume currency: sets discounted 50% when form_quality < 3,
overlap-inclusive, bodyweight sets counted. Never report tonnage or raw reps
as volume.
_Avoid_: volume (unqualified), tonnage

**Training age**:
Classification by rate of progress (workout-to-workout = novice,
week-to-week = intermediate, month-to-month = advanced), never years lifting.
_Avoid_: experience level, years training

**Working memory (Tier 1)**:
The session-scoped state snapshot injected at session start (~3K-token hard
cap). Its `onboarding_required` flag is the legacy name for "profile is null"
— the intake scan then reports everything missing.
_Avoid_: context window, chat history
