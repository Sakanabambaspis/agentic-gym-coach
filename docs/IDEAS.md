# IDEAS.md — Dev notebook

Future feature ideas and design sketches. Nothing here is built; entries move
to the spec/implementation when the user picks them up. House rule applies:
**no physiology/nutrition doctrine may be invented here** — system-level ideas
only. Doctrine gaps are resolved by vendoring a book-skill, never by hand-
writing content into this notebook.

---

## 1. Information shelf life (freshness flags)

**Idea.** Not every stored datum stays valid. Give profile/snapshot inputs an
explicit shelf life; when a decision needs a stale input, the coach flags it
and asks for fresh data instead of computing from rotted numbers (e.g. a
2-year-old max rep).

**What the books back up:**
- Nutrition ch02: every calorie number is a *hypothesis* — NEAT and metabolic
  adaptation move it; adjust by weekly-average weight trends only. Bodyweight
  inputs effectively expire weekly.
- Nutrition ch02: the 2-week tracking method for maintenance is explicitly
  **invalid** for novices and lifters returning from layoff (rapid muscle
  change skews the 3500-kcal math) — a documented instance of "this method
  rots for this population".
- Training ch04: training age is defined by *rate of progress* (workout-to-
  workout / week-to-week / month-to-month), so it is re-classifiable at every
  block — it is a measurement, not a biographical fact.
- The repo already implements perfect shelf life for the load-bearing numbers:
  est_1RM and hard-set volume are **derived from the session window on every
  call** and never stored. The gap is only static profile fields
  (`training_age`, `bodyweight_kg` snapshot, equipment/goals) which carry no
  staleness marking.

**What the books do NOT cover:** detraining timelines (how fast which
adaptations decay after X weeks off). The only layoff mention is the caveat
above. A shelf-life table for "returning lifter" state therefore needs a
future vendored source — until then any detraining half-lives we pick are
heuristics and must be labeled as such.

**Sketch.** A `STALE_AFTER` map (field → duration or condition) consulted at
prescription time; `coach_snapshot` or a new `coach_profile_check` surfaces
`{field, age_days, verdict}`; COACH_PROMPT rule: "before any concrete
prescription that consumes a stale field, flag it and re-collect." No
migration needed (payload JSON); tests on the verdict logic. Concrete
instance (user, 2026-09-20): injury_status rows are "short lived" and should
be reconfirmed every once in a while — the injury entries of the intake
checklist already point here.

**Status:** idea — user approved direction, awaiting build decision.

## 2. Personal FAQ compilation (per-user problem→doctrine routing)

**Idea.** The coach compiles a user's recurring problems ("shoulders don't
feel worked", "knees on deep squats") into a personalized FAQ: problem phrasing
→ triage outcome → routed knowledge file. On the next mention, retrieve the
compiled answer instead of re-deriving it.

**Why it needs careful handling:**
- It is Tier-3-adjacent: personal, durable, and written *about* the user —
  likely deserves the same explicit-command write policy as memory notes
  (MEMORY_PROTOCOL), or its own stricter one.
- Staleness interacts with idea #1: a compiled FAQ entry silently outlives the
  context it was derived from (injury resolved, goal changed).
- Routing targets must be validated paths into `docs/knowledge/` — a FAQ that
  paraphrases doctrine instead of routing to it recreates the v1
  "unsourced knowledge" problem the repo explicitly removed.

**Sketch.** New table (`faq_entries(problem_text, resolution, knowledge_path,
tags, updated_at)`) + `coach_faq_save/search` tools + a COACH_PROMPT rule to
consult it on problem statements before routing fresh. Write policy decided
at build time with the user.

**Status:** idea — user deferred; discuss design before building.

## 3. Returning-user re-onboarding

**Idea.** `onboarding_required` currently fires only when no profile exists.
A user returning after a long gap (months) gets no re-assessment. Add a
weeks-since-last-session check that arms a *lighter* re-onboarding: confirm
goals/schedule/equipment still true, re-check injuries, recommend
`PhaseType.reconditioning`, re-baseline expectations by training age.

**Constraint.** The gap threshold is not in the books (see #1's detraining
gap) — pick a heuristic, label it, make it configurable. Pure code: a query
on `MAX(sessions.date)` in the orchestrator/snapshot; no migration.

**Status:** implemented (2026-09-19), generalized — built as part of the
standardized intake redesign (one flow, no modes; `docs/adr/0001`). The gap
signal shipped as the intake's staleness nudge
(`skills/snapshot.session_gap`, `REASSESSMENT_GAP_WEEKS` heuristic) rather
than a separate re-assessment mode.

## 7. Field freshness cadence

**Idea.** Intake fields differ by archetypal volatility that persists
between users (user framing, 2026-09-20): a schedule is day-to-day volatile,
physique numbers change slowly, stress moves per session, a goal vision
evolves on the timescale of self-understanding. The 2026-09-19 intake
deliberately ships only one persona fact ("stored data are not permanent —
confirm before a plan leans on them", ADR 0002) to avoid agent-side drift;
the machinery is this ticket.

**Sketch.** Pin a refresh cadence per checklist field as data
(`per_session` / `weekly` / `per_block` / `on_change_only`), grounded in
book statements where they exist — bodyweight weekly (ch02 seven-day
averages), training age re-classified per block (ch04 rate of progress),
stress as a per-session recovery check (ch03/ch04) — and labeled heuristic
elsewhere. Agent discretion bounded: confirm EARLIER on surprise, never
later than policy. Candidate assignments from the discussion: per_session →
life_stress; weekly → bodyweight, habits (eating out/alcohol),
availability; per_block → goals vision, training age, derived priorities,
preferences, injuries re-confirmation, tested maxes; on_change_only → sex,
age, equipment.

**Status:** idea — user deferred ("not our responsibility yet"); design
starting point recorded here.

## 4. Form/technique knowledge via vendored skill

**Idea.** The coach can triage "not feeling the muscle" (expectation →
selection → stimulus, now in COACH_PROMPT) but cannot give per-exercise
technique cues — the Helms books are programming books. The compliant fix is
vendoring an execution-focused book-skill (technique atlas) into
`docs/knowledge/` and adding it to the routing table. Until then, the honest
answer to "how do I fix my lateral raise form" is "not covered — say so."

**Status:** idea — blocked on a suitable book to vendor.

## 5. Sleep / stress as logged inputs

**Idea.** The recovery score sees only training load, pain, and day spacing.
Sleep and stress are handled procedurally (checklist questions) because there
is no logging path for them. Both books reference them (Training ch02
recovery-budget; deload checklists; plateau free-wins "sleeping 8+ h"). A
simple per-day sleep-hours/stress-rating input on `coach_log_session` (or a
`coach_checkin` tool) would let the recovery heuristic and deload checklist
consume real data instead of questions.

**Constraint.** Changing `coach_log_session`'s contract touches models,
session_logger, MCP wrapper, dispatcher, COACH_PROMPT (three-places rule), and
tests. Keep optional/null-safe so old logs stay valid.

**Status:** idea.

## 6. Claude Code native adapter

**Idea.** `scripts/sync_adapters.py` `ADAPTERS` is an empty extension point
after opencode removal. A Claude Code adapter would render `COACH_PROMPT.md` +
frontmatter to `.claude/agents/gym-coach.md`. Today Claude Code is served via
`.mcp.json` + AGENTS.md read-order, which works; the adapter is a
nicety, not a need.

**Status:** idea — offer when relevant.
