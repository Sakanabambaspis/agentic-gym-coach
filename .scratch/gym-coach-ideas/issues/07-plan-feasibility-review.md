# 07 — Plan feasibility review (revision round)

**What to build:** before delivering ANY training or nutrition plan, the
coach runs an explicit feasibility self-review of its own draft and warns
the user about anything impossible or counterproductive — then adjusts or
proceeds only on the user's informed insistence (consistent with the soft
gates, docs/adr/0001). This is a revision round between "draft" and
"deliver", not a new gate.

Feasibility checks to consider (each maps to doctrine the books already
state — the review cites, never invents):

- [ ] Schedule fit: planned sessions vs `weekly_availability` windows (both
      day coverage and window duration), and the committed
      `days_per_week` vs what the windows actually support (resolves the
      "4 committed / 2 windows" case the 2026-09-20 review flagged as
      unspecified)
- [ ] Volume vs session length: can the weekly volume split fit inside the
      available windows?
- [ ] Equipment fit: prescribed exercises vs `equipment_access`
- [ ] Goal realism: rate prescriptions vs deadline (cut 0.5–1.0% BW/week,
      Nutrition ch02; gain rates by training age) — flag deadlines the math
      can't reach
- [ ] Recovery budget: high `life_stress` + aggressive volume → warn
      (Training ch02 cumulative stress bucket)
- [ ] Book-flagged counterproductive patterns: copying pro schedules,
      cramming missed sessions back-to-back at full load, magic-macro
      thinking, rigid restraint (ch01/ch02 both books)

**Shape:** first version is a COACH_PROMPT decision procedure (LLM-time
revision round with warnings); a deterministic schedule-fit helper in
`skills/` is a possible follow-up — add it only if the LLM-time check
proves unreliable in use.

**Why:** the persona currently drafts plans from stored data without an
explicit "is this actually doable for THIS person's week/body/equipment?"
pass. The 2026-09-20 review found the window-vs-commitment relationship
undefined; the intake's best-effort fluid fields (windows, vague answers)
make an explicit feasibility pass the natural companion.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] COACH_PROMPT: feasibility revision-round procedure with warning format
      ("what's infeasible → why → what would make it work")
- [ ] Warnings are cited (window/field values shown), never vague
- [ ] Soft-gate consistency: user can insist on an infeasible plan, output
      is then a provisional plan that names the infeasibility (ADR 0001)
- [ ] Tests: any deterministic helper added gets its own
      `tests/test_skills/test_<name>.py`; persona changes pass the
      surface-drift guards
