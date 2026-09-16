# 02 — Returning-user re-onboarding

**What to build:** today the onboarding gate fires only when no profile
exists. A user returning after a months-long gap gets coached off a possibly
rotted profile. This ticket adds detection (weeks since last logged session)
and a *lighter* returning-user flow: confirm goals/schedule/equipment are
still true, re-check injuries, recommend the `reconditioning` phase, and
re-baseline expectations by training age — distinct from full first-time
onboarding, which stays as-is.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Weeks-since-last-session is computed from session history at session
      start and exposed on the working-memory/snapshot surface
- [ ] Crossing the gap threshold arms a returning-user re-assessment flow in
      COACH_PROMPT (confirm profile fields, injury re-check, reconditioning
      recommendation) — separate from the no-profile onboarding gate
- [ ] Goal/schedule changes made during re-assessment go through the normal
      profile write path (goal changes auto-audit to the decision log)
- [ ] The gap threshold is labeled a heuristic (not book-sourced — see ticket
      01's detraining caveat), configurable in one place
- [ ] Tests cover: no sessions at all, gap just under threshold, gap just
      over threshold, re-assessment with unchanged profile
