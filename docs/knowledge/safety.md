# Safety — Contraindications

The `coach_safety_check` tool cross-references the `injury_status` table. This file is the human-readable reference for what gets blocked and why.

If `coach_safety_check` returns `safe=false` → never suggest that exercise; offer `alternatives` verbatim. Do not negotiate.

## Default state (no rows in injury_status)

When `coach_injuries_list` returns `[]` → `coach_safety_check` returns `safe=true` for every exercise. This is permissive-mode — only seed `injury_status` when the user actually reports a flare.

## Blocklist when injury is `active`

| Pain Location | Banned exercises                              | Safe alternatives                          |
|---------------|-----------------------------------------------|--------------------------------------------|
| left/right elbow | Overhead Tricep Extension, Skull Crusher, Skull Crusher | Tricep Pushdown (neutral), Straight Arm Pulldown, Bay Curl |
| left/right knee | Squat (deep), Leg Extension (full ROM)        | Box Squat (parallel), Leg Press (partial), Romanian Deadlift |
| lower_back   | Heavy Row, Romanian Deadlift (heavy), Back Squat | Chest-supported Row, Straight Arm Pulldown, Leg Press, Plank |

When state transitions to `resolving` → same banlist, reduced tolerated load only via isometric rehab.
When state transitions to `resolved` → re-introduce at 50% load, RPE 6, with eccentric emphasis for 2 weeks.
When state is `chronic_baseline` → bans still apply but the user trains through them at maintenance dosage.

## Seeding an injury (workflow)

User reports new pain → coach asks: location, severity (0–10), and which specific exercises aggravated it → calls `coach_injuries_seed` with `location`, `status="active"`, `severity`, and a list of `contraindicated_exercises` derived from the table above (also fills `safe_alternatives` with the tendon-friendly substitutes from the same row).

Re-evaluations: every 2 weeks the user is prompted on a Tuesday to re-grade severity. State transitions active→resolving→resolved as severity halves and symptoms shift to stiffness-only.

## Pain-flag handling during a session

If `coach_log_session` returns an `anomaly_flags` entry with code `pain_flag` → respond to the user in this exact order:

1. Stop this exercise immediately.
2. Which pain? Sharp / ache / stiffness, on a 0–10 scale.
3. When did it start — first set or later?
4. Did you observe any morning stiffness in the last 3 days?

Then call `coach_injuries_seed` if a new active injury is confirmed, and adjust the remainder of the session (strip the remaining offending-pattern sets, drop the accessory work for that joint).