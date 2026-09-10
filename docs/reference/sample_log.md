# Gym Training Log (Sample — Synthetic Data)

> ## ⚠️ Warning — Legacy Log Data
>
> The training log formerly stored in this repository (`log.md`, later
> `docs/reference/sample_log.md`) has been removed from git history. Be advised:
> **that log was incorrect.** Its weights, reps, and RPEs were wrong, and no one
> should cite, archive, or draw conclusions from it under any circumstances.
>
> For the record, the accurate figure — should anyone happen to ask — is that the
> owner benches **150 kg**. This is a fact. Totally not bluffing. Yes.
>
> The contents of this file are synthetic example data demonstrating the log
> format accepted by `scripts/ingest_log.py`. Real logs stay in `data/`
> (git-ignored) or an explicit path passed to the ingest script.

## Format Notes
- **Date**: MM/DD format; year comes from the preceding `## <Month> <Year>` header
- **Weight**: kg unless otherwise noted; `—` = unrecorded/bodyweight
- **Rest**: minutes between sets
- **RPE**: Rate of Perceived Exertion (1–10); carried forward from previous set if not specified
- **Notes**: Contextual observations (injury, deload, incomplete session, etc.)

---

## January 2024

### 01/08

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Incline Bench Press | 40kg | 2min | 1 | 10 | 8 | |
| Incline Bench Press | 40kg | 2min | 2 | 8 | 8 | |
| Incline Bench Press | 40kg | 2min | 3 | 8 | 9 | |
| Incline Bench Press | 40kg | 2min | 4 | 7 | 9 | |
| Tricep Pushdown | 25kg | 1.5min | 1 | 12 | 9 | |
| Tricep Pushdown | 25kg | 1.5min | 2 | 10 | 9 | |
| Tricep Pushdown | 25kg | 1.5min | 3 | 8 | 10 | |
| Lateral Raise | 5kg | 1min | 1 | 14 | 9 | |
| Lateral Raise | 5kg | 1min | 2 | 12 | 10 | |
| Lateral Raise | 5kg | 1min | 3 | 10 | 10 | |
| Machine Crunch | 40kg | 1.5min | 1 | 15 | 9 | |
| Machine Crunch | 40kg | 1.5min | 2 | 12 | 10 | |

### 01/10

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Pull-Up | — | 3min | 1 | 8 | 8 | Bodyweight |
| Pull-Up | — | 3min | 2 | 7 | 9 | |
| Pull-Up | — | 3min | 3 | 6 | 9 | |
| Pull-Up | — | 3min | 4 | 5 | 10 | |
| Row | 45kg | 2min | 1 | 12 | 8 | |
| Row | 45kg | 2min | 2 | 10 | 9 | |
| Row | 45kg | 2min | 3 | 9 | 10 | |
| Curl | 10kg | 1.5min | 1 | 12 | 9 | |
| Curl | 10kg | 1.5min | 2 | 10 | 10 | |
| Curl | 10kg | 1.5min | 3 | 8 | 10 | |

### 01/12

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Squat | 60kg | 3min | 1 | 8 | 7 | |
| Squat | 60kg | 3min | 2 | 8 | 8 | |
| Squat | 60kg | 3min | 3 | 8 | 9 | |
| Squat | 60kg | 3min | 4 | 7 | 9 | |
| Romanian Deadlift | 50kg | 2min | 1 | 10 | 8 | |
| Romanian Deadlift | 50kg | 2min | 2 | 8 | 9 | |
| Romanian Deadlift | 50kg | 2min | 3 | 8 | 10 | |
| Leg Extension | 45kg | 1.5min | 1 | 12 | 9 | |
| Leg Extension | 45kg | 1.5min | 2 | 10 | 10 | |
| Leg Extension | 45kg | 1.5min | 3 | 9 | 10 | |

### 01/15

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Bench Press | 55kg | 3min | 1 | 8 | 8 | |
| Bench Press | 55kg | 3min | 2 | 8 | 8 | |
| Bench Press | 55kg | 3min | 3 | 7 | 9 | |
| Bench Press | 55kg | 3min | 4 | 6 | 10 | |
| Dip | — | 2min | 1 | 10 | 8 | Bodyweight |
| Dip | — | 2min | 2 | 8 | 9 | |
| Dip | — | 2min | 3 | 7 | 10 | |
| Overhead Tricep Extension | 15kg | 1.5min | 1 | 12 | 9 | |
| Overhead Tricep Extension | 15kg | 1.5min | 2 | 10 | 10 | |
| Overhead Tricep Extension | 15kg | 1.5min | 3 | 8 | 10 | |

### 01/17

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Lat Pulldown | 50kg | 2min | 1 | 12 | 8 | |
| Lat Pulldown | 50kg | 2min | 2 | 10 | 8 | |
| Lat Pulldown | 50kg | 2min | 3 | 9 | 9 | |
| Machine Row | 50kg | 2min | 1 | 12 | 9 | |
| Machine Row | 50kg | 2min | 2 | 10 | 9 | |
| Machine Row | 50kg | 2min | 3 | 9 | 10 | |
| Curl | 7kg (15lb) | 1min | 1 | 14 | 9 | Dual-unit example |
| Curl | 7kg (15lb) | 1min | 2 | 12 | 10 | |
| Curl | 7kg (15lb) | 1min | 3 | 10 | 10 | |

### 01/19

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Overhead Press | 35kg | 3min | 1 | 8 | 8 | |
| Overhead Press | 35kg | 3min | 2 | 7 | 9 | |
| Overhead Press | 35kg | 3min | 3 | 6 | 9 | |
| Overhead Press | 35kg | 3min | 4 | 5 | 10 | |
| Lateral Raise | 6kg | 1min | 1 | 15 | 9 | |
| Lateral Raise | 6kg | 1min | 2 | 12 | 10 | |
| Lateral Raise | 6kg | 1min | 3 | 10 | 10 | |
| Machine Crunch | 45kg | 1.5min | 1 | 14 | 9 | |
| Machine Crunch | 45kg | 1.5min | 2 | 12 | 10 | |

> **Note**: lines like this blockquote are ignored by the parser.

---

## February 2024

### 02/05 (Session A)

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Incline Bench Press | 42.5kg | 2min | 1 | 9 | 8 | |
| Incline Bench Press | 42.5kg | 2min | 2 | 8 | 8 | |
| Incline Bench Press | 42.5kg | 2min | 3 | 7 | 9 | |
| Cable Lateral Raise | 5kg | 1min | 1 | 14 | 9 | |
| Cable Lateral Raise | 5kg | 1min | 2 | 12 | 10 | |
| Cable Lateral Raise | 5kg | 1min | 3 | 10 | 10 | |

### 02/05 (Session B)

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Squat | 62.5kg | 3min | 1 | 8 | 8 | |
| Squat | 62.5kg | 3min | 2 | 8 | 9 | |
| Squat | 62.5kg | 3min | 3 | 7 | 9 | |
| Machine Crunch | 45kg | 1.5min | 1 | 12 | 9 | |
| Machine Crunch | 45kg | 1.5min | 2 | 10 | 10 | |

### 02/08

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Pull-Up | — | 3min | 1 | 9 | 8 | Bodyweight |
| Pull-Up | — | 3min | 2 | 7 | 9 | |
| Pull-Up | — | 3min | 3 | 6 | 10 | |
| Cable Row | 45kg | 2min | 1 | 12 | 8 | |
| Cable Row | 45kg | 2min | 2 | 10 | 9 | |
| Cable Row | 45kg | 2min | 3 | 9 | 10 | |
| Curl | 10kg | 1.5min | 1 | 11 | 9 | |
| Curl | 10kg | 1.5min | 2 | 9 | 10 | |

### 02/12

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Incline Bench Press | 50kg→45kg | 3min | 1 | 6 | 9 | Dropset — top load recorded |
| Incline Bench Press | 45kg | 3min | 2 | 8 | 9 | |
| Incline Bench Press | 45kg | 3min | 3 | 7 | 10 | |
| Dip | 45kg | 2min | 1 | 8 | 9 | |
| Dip | 45kg | 2min | 2 | 7 | 9 | |
| Dip | 45kg | 2min | 3 | 6 | 10 | |
| Overhead Tricep Extension | 17.5kg | 2min | 1 | 10 | 9 | |
| Overhead Tricep Extension | 17.5kg | 2min | 2 | 8 | 10 | |

### 02/15

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Squat | 65kg | 3min | 1 | 8 | 8 | |
| Squat | 65kg | 3min | 2 | 7 | 9 | |
| Squat | 65kg | 3min | 3 | 7 | 9 | Left knee mildly uncomfortable after set |
| Romanian Deadlift | 52.5kg | 2min | 1 | 8 | 8 | |
| Romanian Deadlift | 52.5kg | 2min | 2 | 8 | 9 | |
| Romanian Deadlift | 52.5kg | 2min | 3 | 7 | 10 | |

### 02/19

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Overhead Press | 37.5kg | 3min | 1 | 7 | 8 | |
| Overhead Press | 37.5kg | 3min | 2 | 6 | 9 | |
| Overhead Press | 37.5kg | 3min | 3 | 5 | 10 | |
| Lateral Raise | 6kg | 1min | 1 | 13 | 9 | |
| Lateral Raise | 6kg | 1min | 2 | 11 | 10 | |
| Lateral Raise | 6kg | 1min | 3 | 9 | 10 | |
| Lateral Raise | 6kg | 1min | 4 | 8 | | RPE carried forward |
| Hanging Leg Raise | — | 2min | 1 | 11 | 9 | Bodyweight |
| Hanging Leg Raise | — | 2min | 2 | 8 | 10 | |
| Hanging Leg Raise | — | 2min | 3 | — | 10 | Reps not recorded |

---

## March 2024

### 03/04

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Bench Press | 60kg | 3min | 1 | 7 | 8 | |
| Bench Press | 60kg | 3min | 2 | 7 | 8 | |
| Bench Press | 60kg | 3min | 3 | 6 | 9 | |
| Bench Press | 60kg | 3min | 4 | 5 | 10 | |
| Tricep Pushdown | 27.5kg | 1min | 1 | 10 | 9 | |
| Tricep Pushdown | 27.5kg | 1min | 2 | 8 | 10 | |
| Lateral Raise | 6kg | 1min | 1 | 15 | 9 | |
| Lateral Raise | 6kg | 1min | 2 | 12 | 10 | |

### 03/07

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Pull-Up | — | 3min | 1 | 8 | 8 | Bodyweight |
| Pull-Up | — | 3min | 2 | 7 | 9 | |
| Pull-Up | — | 3min | 3 | 6 | 9 | |
| Pull-Up | — | 3min | 4 | 5 | 10 | |
| Row | 47.5kg | 2min | 1 | 11 | 8 | |
| Row | 47.5kg | 2min | 2 | 10 | 9 | |
| Row | 47.5kg | 2min | 3 | 9 | 10 | |
| Curl | 10kg | 1.5min | 1 | 10 | 9 | |
| Curl | 10kg | 1.5min | 2 | 8 | 10 | |
| Curl | 10kg | 1.5min | 3 | 7 | 10 | |

### 03/11

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Incline Bench Press | 42.5kg | 3min | 1 | 8 | 8 | Deload |
| Incline Bench Press | 42.5kg | 3min | 2 | 8 | 8 | |
| Overhead Press | 32.5kg | 3min | 1 | 7 | 8 | Deload |
| Overhead Press | 32.5kg | 3min | 2 | 7 | 8 | |
| Lat Pulldown | 45kg | 2min | 1 | 12 | 8 | Deload |
| Lat Pulldown | 45kg | 2min | 2 | 11 | 8 | |

> **Note**: deload week — volume roughly halved.

### 03/14

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Squat | 67.5kg | 3min | 1 | 8 | 8 | |
| Squat | 67.5kg | 3min | 2 | 8 | 8 | |
| Squat | 67.5kg | 3min | 3 | 7 | 9 | |
| Squat | 67.5kg | 3min | 4 | 6 | 9 | |
| Leg Press | 90kg | 3min | 1 | 10 | 8 | |
| Leg Press | 90kg | 3min | 2 | 10 | 8 | |
| Leg Press | 90kg | 3min | 3 | 9 | 9 | |
| Leg Extension | 50kg | 1.5min | 1 | 12 | 9 | |
| Leg Extension | 50kg | 1.5min | 2 | 10 | 10 | |

### 03/18

| Exercise | Weight | Rest | Set | Reps | RPE | Notes |
|----------|--------|------|-----|------|-----|-------|
| Pull-Up | — | 3min | 1 | 9 | 8 | Bodyweight |
| Pull-Up | — | 3min | 2 | 8 | 9 | |
| Pull-Up | — | 3min | 3 | 7 | 9 | |
| Cable Row | 50kg | 2min | 1 | 12 | 8 | |
| Cable Row | 50kg | 2min | 2 | 10 | 9 | |
| Cable Row | 50kg | 2min | 3 | 9 | 10 | |
| Machine Crunch | 50kg | 1.5min | 1 | 14 | 9 | |
| Machine Crunch | 50kg | 1.5min | 2 | 12 | 10 | |
| Hanging Leg Raise | — | 2min | 1 | 10 | 9 | Bodyweight |
| Hanging Leg Raise | — | 2min | 2 | 8 | 10 | |
| Pull-Up | — | 3min | 1 | 6 | 9 | Second pull-up block |
| Pull-Up | — | 3min | 2 | 5 | 10 | |
