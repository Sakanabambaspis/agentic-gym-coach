# 04 — Personal FAQ compilation (problem → doctrine routing memory)

**What to build:** the coach compiles a user's recurring problems ("shoulders
don't feel worked", "knees on deep squats") into personalized entries: problem
phrasing → resolved triage outcome → routed knowledge path. On the next
mention, the compiled entry is retrieved instead of re-deriving the answer.
This is durable personal memory and is deliberately NOT built yet — the user
wants a design discussion first.

**Blocked by:** Design discussion with the user (hard gate). Recommended to
build after ticket 01 (soft) so entries can reuse the freshness-verdict style
rather than inventing their own staleness handling.

**Status:** needs-design-discussion — do not implement until the write
policy and staleness model are agreed with the user.

Draft acceptance criteria (to be finalized at the design discussion):

- [ ] Write policy decided — likely explicit-command only (Tier-3 note
      semantics); never auto-write
- [ ] Entries must ROUTE to validated knowledge paths; paraphrasing doctrine
      into the entry body recreates the unsourced-v1-knowledge problem —
      forbidden
- [ ] Entries invalidate when their context changes (injury resolved, goal
      changed) — freshness model agreed with the user
- [ ] Search/consult surface added and COACH_PROMPT gains a
      consult-before-routing rule for problem statements
- [ ] Tests: roundtrip, tag/search, invalidation, and the no-auto-write gate
