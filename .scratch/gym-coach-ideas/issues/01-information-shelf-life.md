# 01 — Information shelf life (freshness flags)

**What to build:** when the coach is about to make a concrete prescription
(macro targets, maintenance calories, training-age-based progression), stale
profile inputs are detected and surfaced instead of silently consumed. A
bodyweight recorded three months ago triggers "give me a fresh weigh-in"
before any per-bodyweight math runs; a training age declared a year ago gets
re-classified by current rate of progress before progression models are
applied. Doctrine anchors already in-system: nutrition ch02 (calorie numbers
are weekly hypotheses; the 2-week maintenance method is explicitly invalid
for novices and returning lifters) and training ch04 (training age is
re-measurable every block). Detraining decay timelines are NOT covered by the
vendored books — any such threshold must be labeled a heuristic and live in
one configurable place.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Every perishable profile field has a shelf-life rule (duration or
      re-measure condition) declared in one place
- [ ] The snapshot surface (or an equivalent check tool) returns
      `{field, as_of, age, verdict: fresh|stale|unknown}` for each ruled field
- [ ] COACH_PROMPT gains the rule: no concrete prescription from a stale
      field — flag it and re-collect first
- [ ] Heuristic thresholds (especially anything detraining-related) are
      marked as not-book-sourced, configurable, and documented as such
- [ ] Tests cover fresh/stale/unknown verdicts and date boundaries; no
      Alembic migration required (profile is payload JSON)
