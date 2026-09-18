# Standardized intake with soft per-domain gates, one mode

---
status: accepted
date: 2026-09-19
---

Onboarding used to be a prompt-scripted event that fired only when no profile
existed, so returning users got coached off possibly rotted data. We replaced
it with a **code-driven intake**: the bucket list lives as data
(`models/intake.py::INTAKE_CHECKLIST`, every field citing its Helms chapter or
labeled HEURISTIC), and `skills/intake.py::assess_intake()` deterministically
scans stored state to report collected vs missing — the coach asks only for
what the scan says is missing, cites what is stored ("still accurate?"), and
writes answers back through the normal profile/injury paths.

Three decisions were deliberate alternatives, not defaults:

1. **Code over prompt.** Presence-checking "what does the DB already hold" is
   a deterministic computation; prompt-only scripting made it untestable and
   let the checklist drift from the profile schema (a drift-guard test now
   pins storage paths to `UserProfile.model_fields`).
2. **Soft gates with a provisional-plan escape hatch.** `training_ready` /
   `nutrition_ready` stop the coach from *volunteering* plans when gating data
   is missing, but on explicit user insistence ("just give me something") it
   produces a provisional plan that names each missing field and its
   limitation. Hard refusal was rejected: it front-loads ~15 questions before
   any value, and blocks training answers on nutrition data the training book
   never consumes.
3. **One mode, not two.** We considered a separate "returning-user
   re-assessment" flow; instead the same scan serves everyone — staleness is
   handled by the `session_gap` signal (`REASSESSMENT_GAP_WEEKS`, a heuristic,
   since the books don't cover detraining timelines) which makes confirming
   collected values mandatory before programming.

Consequences: first interactions may ask more questions than before (the full
bucket list); list-typed profile fields treat empty as a valid stored answer
(the one exception is `goals`, where empty is indistinguishable from
never-asked and "no specific goal" has its own vocabulary value —
`general_fitness`); `equipment_access` lost its `full_gym` default so an
unanswered field reports missing instead of laundering the default into a
collected value; and a user with no reported injuries never holds a gate open
(the persona's standing "always check injuries" rule guarantees the ask).
