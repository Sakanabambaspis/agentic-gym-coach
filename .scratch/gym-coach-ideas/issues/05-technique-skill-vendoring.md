# 05 — Technique knowledge via vendored book-skill

**What to build:** the coach can triage "not feeling the muscle" (COACH_PROMPT
triage: expectation → selection → stimulus) but cannot give per-exercise
technique cues — the vendored Helms books are programming books, and the repo
rule forbids hand-writing physiology. The compliant fix: vendor an
execution/technique-focused book-skill into `docs/knowledge/` with the same
treatment as the two existing skills (verbatim SKILL.md router, chapters,
topic index — no hand-written content), then extend the routing table so
"how do I fix my lateral raise form" resolves to book-sourced cues instead of
"not covered."

**Blocked by:** A suitable book provided by the user (external input — same
as the nutrition skill was supplied on the desktop).

**Status:** awaiting-source — blocked until the user supplies the book.

- [ ] Book-skill vendored verbatim under `docs/knowledge/<name>/` with
      router + chapter + topic index structure matching the existing skills
- [ ] COACH_PROMPT routing table and doctrine-source list extended; safety >
      skills > mechanics precedence unchanged
- [ ] `coach_doctrine` serves the new files (index + per-file read, char cap)
- [ ] One-knowledge-file-per-turn rule and the honesty rule ("not covered"
      when the books are silent) explicitly retained in COACH_PROMPT
- [ ] AGENTS.md/SPEC skill inventory updated; no code changes expected
      beyond the doctrine surface
