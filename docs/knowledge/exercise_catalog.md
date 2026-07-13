# Exercise Catalog

Canonical names + muscle groups + brief form cues. This file mirrors `models/exercise_catalog.py` — keep them in sync.

The user may log raw aliases; `session_logger` canonicalizes them automatically. Read this file when the user asks "what exercises hit X?" or when planning a session.

## Upper Chest (specialization)

- **Incline Bench Press** — aliases: Incline Press, Machine Incline, Dumbbell Incline. Cue: bar path from lower chest to upper chest; 30° incline best.
- **Decline Push-Up** — feet elevated. Bodyweight option to spare shoulders.

## Side Delts (specialization)

- **Shoulder Press** — aliases: Barbell/Machine/Dumbbell Shoulder Press, Strict Press, Overhead Press. Cue: bar to clavicle, press to lockout behind the head slightly.
- **Lateral Raise** — aliases: Cable/Machine/Dumbbell Lateral Raise. Cue: lead with elbows, not hands; no shrug.

## Rear Delts (specialization)

- **Reverse Fly** — aliases: Machine Reverse Fly. Cue: pause at end ROM; shoulder blades apart.

## Lats (back detail)

- **Pull-Up** — aliases: Pull Up, Close Grip Pull-Up. Cue: initiate with lats, retract shoulder blades.
- **Straight Arm Pulldown** — uses cable. Lat isolation without elbow flexion load (tendon-friendly).

## Mid-Back

- **Row** — aliases: Pendlay Row, Cable Row, Neutral/Wide Grip Cable Row, Machine Row, Reverse Row. Cue: pull elbows behind torso; pause.

## Biceps

- **Hammer Curl** — neutral grip, brachialis emphasis.
- **Bay Curl** — bayesian-style cable setup; tension peaks at lengthened position.
- **Dumbbell Curl** — aliases: Curl. Standard.

## Triceps

- **Dip** — high systemic load, long-head bias.
- **Overhead Tricep Extension** — **elbow-risky**: long head at lengthened position. Avoid in flare.
- **Tricep Pushdown** — neutral grip, tendon-friendly. Default alternative to skull crushers.
- **Skull Crusher** — aliases: Dumbbell Skull Crusher. **Elbow-risky**: prefer cable pushdown if any elbow history.

## Quads

- **Squat** — aliases: Bulgarian Split Squat, Split Squat. Knee-risky at deep rom; consider box squat variant.
- **Leg Extension** — knee-risky at full lockout; partial-range preferred.
- **Leg Press** — safer for knee tendon due to back support; moderate depth.

## Hamstrings / Glutes

- **Romanian Deadlift** — hip-hinge, no knee compression.
- **Leg Curl** — aliases: Single-Leg Curl.

## Calves

- **Calf Raise** — aliases: Smith Calf Raise.

## Core

- **Crunch** — aliases: Machine Crunch.
- **Hanging Leg Raise** — aliases: Leg Raise.

## Adding a new exercise

If a user signs an exercise not listed → `session_logger` flags `needs_review=true`. When you see such a flag, ask the user: "Confirm muscle group for <exercise>?" then propose adding it to `models/exercise_catalog.py` (offered as a code change to the user, NEVER auto-applied — this Coach agent does not edit code).