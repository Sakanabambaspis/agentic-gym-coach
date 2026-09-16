# 03 — Sleep and stress as logged inputs

**What to build:** the recovery score currently sees only training load,
pain, and day spacing; sleep and stress exist only as verbal checklist
questions in COACH_PROMPT. The user can log sleep hours and a stress rating
alongside (or independent of) a training session, and the recovery heuristic
and deload/plateau checklists then consume real values — e.g. "slept 5 h,
stress 8/10" logged with a session visibly depresses the recovery score and
answers the checklist's sleep flag with data instead of questions.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Optional `sleep_hours` and `stress_rating` accepted on session logging;
      null-safe so existing logs and old callers stay valid
- [ ] Values are bounded and validated at the Pydantic boundary like every
      other per-session input
- [ ] The recovery heuristic incorporates them when present (weights
      documented); when absent, behavior is unchanged
- [ ] Values are surfaced where the doctrine references them only (training
      ch02 recovery budget, deload checklist, plateau free-wins) — no
      invented physiology about *why*, only bookkeeping of what the user
      reported
- [ ] Tool-surface rule respected: dispatcher handler + MCP wrapper +
      COACH_PROMPT contract updated together
- [ ] Tests: null defaults, bounds rejection, recovery-score effect,
      old-log compatibility
