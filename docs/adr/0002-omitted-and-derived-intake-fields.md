# Omitted and derived intake fields; freshness as one fact

---
status: accepted
date: 2026-09-20
---

First real-use feedback on the standardized intake (ADR 0001) showed several
fields were either not load-bearing or not knowable at intake. Three
decisions:

1. **Meals omitted.** The book's own verdict makes meal frequency
   non-load-bearing: "energy expenditure is identical from 2–7 meals",
   "frequency itself is neutral", consistency of pattern matters only at the
   margin — and timing is the fourth-most-important dial that "novices
   should mostly skip" (Nutrition ch05). A stored count would be a fiction
   for inconsistent eaters; the coach reads ch05 when a timing question
   actually arises.
2. **Social support omitted.** The field is too abstract and its effect too
   unpredictable to act on — there is no way to know how supportive friends
   impact hypertrophy. ch08 strategies stay available as routing knowledge
   when the user raises the topic; nothing is stored.
3. **Priority muscles are derived, never asked.** Specialization targets
   depend on the goal and current physique and change block to block; the
   coach derives them (`skills.profile.derive_priority_muscles`: goal
   targets, plus declared priorities as a confirmed override) instead of
   collecting them at intake.

Plus the freshness stance: rather than a per-field refresh-cadence policy
(deferred — see docs/IDEAS.md #7), the persona carries one fact — *stored
data are not permanent; confirm before a plan leans on them* — and the
books' own procedures give the per-circumstance guidance.

Consequences: `weekly_availability` windows (new) are best-effort and
non-blocking — vague answers are formatted into windows by the coach;
exercise likes/dislikes are non-blocking (they emerge through training);
empty `goals` and empty `weekly_availability` both mean "never asked"
(empty_is_missing is declared per field, not dispatched by name); and
`meals_per_day`/`social_support`/`SocialSupport` are gone from the schema
(old payloads stay valid — Pydantic ignores stale keys).
