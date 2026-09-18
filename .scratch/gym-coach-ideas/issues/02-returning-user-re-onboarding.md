# 02 — Returning-user re-onboarding

**What to build:** today the onboarding gate fires only when no profile
exists. A user returning after a months-long gap gets coached off a possibly
rotted profile. This ticket adds detection (weeks since last logged session)
and a *lighter* returning-user flow: confirm goals/schedule/equipment are
still true, re-check injuries, recommend the `reconditioning` phase, and
re-baseline expectations by training age — distinct from full first-time
onboarding, which stays as-is.

**Blocked by:** None — can start immediately.

**Status:** absorbed (2026-09-19) — superseded by the standardized intake
redesign (`docs/adr/0001-standardized-intake-soft-gates.md`). The detection
half shipped as designed; the two-flow idea was generalized into ONE intake
flow with no modes (the same scan serves first-time and returning users; the
gap signal makes confirming stored values mandatory before programming, and
`reconditioning` is the recommended return phase — see COACH_PROMPT
"Standardized intake assessment").

- [x] Weeks-since-last-session is computed from session history at session
      start and exposed on the working-memory/snapshot surface
      → `skills/snapshot.session_gap` → `PhaseSnapshot.session_gap` +
      `WorkingMemoryState.weeks_since_last_session`
- [x] Crossing the gap threshold arms a returning-user re-assessment flow in
      COACH_PROMPT (confirm profile fields, injury re-check, reconditioning
      recommendation) — generalized: the gap arms the intake's mandatory
      confirm-present step rather than a separate mode
- [x] Goal/schedule changes made during re-assessment go through the normal
      profile write path (goal changes auto-audit to the decision log)
      → unchanged `coach_profile_set` path; audited by
      `test_unchanged_profile_via_normal_write_path_audits_nothing`
- [x] The gap threshold is labeled a heuristic (not book-sourced — see ticket
      01's detraining caveat), configurable in one place
      → `skills/snapshot.REASSESSMENT_GAP_WEEKS`
- [x] Tests cover: no sessions at all, gap just under threshold, gap just
      over threshold, re-assessment with unchanged profile
      → `tests/test_skills/test_snapshot_extra.py` (session_gap block),
      `tests/test_orchestrator_extra.py` (staleness block)
