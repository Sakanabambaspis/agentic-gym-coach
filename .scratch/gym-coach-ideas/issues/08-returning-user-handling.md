# 08 — Returning-user handling (staleness policy for a rotted profile)

**What to build:** the standardized intake solves first-contact collection
(one bucket list, one scan, ask only for what's missing). What it does NOT
yet define is what the coach DOES when a known user returns after a long
gap: which stored fields to re-confirm vs re-collect vs re-baseline, in
what order, with what expectations. Today there is only a signal
(`skills.snapshot.session_gap` → `reassessment_recommended`) and one
persona sentence. This ticket designs the returning-user policy.

**Design inputs already recorded:**
- `docs/research/reconditioning-consensus-2026-09-20.md` — detraining/
  retraining evidence (muscle memory is well-supported; strength holds
  ~4 weeks then decays; regain is faster than initial gain; injury risk on
  abrupt return is real but mixed) + the provenance finding that
  `reconditioning` is repo convention, not Helms doctrine (see ticket 09)
- `docs/IDEAS.md` #7 — per-field refresh-cadence sketch (per_session /
  weekly / per_block / on_change_only) with agent discretion bounded to
  "confirm earlier on surprise, never later than policy"
- ticket 01 — information shelf life (STALE_AFTER map sketch); injuries
  re-confirmation is the concrete instance
- The persona's current one-fact rule: "stored data are not permanent —
  confirm before a plan leans on them"

**Scope questions to settle:**
- Freshness policy: adopt idea #7's cadence as data on INTAKE_CHECKLIST,
  or a coarser rule (always re-confirm bodyweight/schedule/injuries;
  re-derive priorities from goals + current state)?
- What gets re-baselined vs confirmed: loads/RPE targets after a gap;
  training_age re-classification (ch04 rate of progress); the goals vision
- The return phase and its dosing: `reconditioning` or the book's intro
  cycle (~75% volume, ~1 RPE lower) as the Helms-attested analog (see
  ticket 09 for the provenance fix)
- How freshness surfaces: intake-report fields vs working-memory flags

**Context:** the shipped onboarding feature is deliberately limited to a
standardized basket of information for NEW users; this ticket is the
deferred half — returning users.

**Blocked by:** ticket 01 would inform it; not strictly blocking.

**Status:** ready-for-agent — priority after the core flow stabilizes.
