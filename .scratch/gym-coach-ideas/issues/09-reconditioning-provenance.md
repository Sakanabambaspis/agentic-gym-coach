# 09 — Reconditioning: provenance relabel (low priority)

**What to build:** a small honesty fix per
`docs/research/reconditioning-consensus-2026-09-20.md`. The phase itself is
substantively defensible — its meaning matches standard applied-S&C usage
and the coached behavior (return reduced, ramp conservatively) matches the
detraining/retraining evidence — but it is misattributed: "reconditioning"
appears nowhere in the Helms Training book, and only 4 of 8 enum values
(accumulation, intensification, realization, deload) are book-attested.

- [ ] `models/enums.py` docstring: attribute only the 4 attested values to
      Helms ch04; label maintenance/reconditioning/cut/lean_bulk as repo
      conventions — noting reconditioning aligns with standard applied-S&C
      usage (NSCA Essentials ch23; Army FM 7-22 ch13), not Helms doctrine
      (mirror the `REASSESSMENT_GAP_WEEKS` heuristic labeling)
- [ ] COACH_PROMPT: beside the post-gap reconditioning recommendation, add
      the provenance line (repo convention, consistent with applied S&C
      practice), mirroring the existing not-book-doctrine caveat on the gap
      threshold; cite the intro cycle (~75% volume, ~1 RPE lower) as the
      Helms-attested dosing analog
- [ ] Optional: CONTEXT.md glossary entry for reconditioning citing the
      research note
- [ ] Do NOT touch migration 0002 — historical migrations stay as written

**Why low priority:** no behavior change — the coached plan is already what
the external consensus supports; this is provenance honesty only.

**Blocked by:** None.

**Status:** backlog — low priority.
