# Progression & Autoregulation

The user logs minimal data (sets, reps, RPE). Use RPE as the autoregulation signal — not a fixed percentage table.

## RPE → load rules

RPE 10 = no reps in reserve (RIR 0). RPE 9 = 1 RIR. RPE 8 = 2 RIR. RPE 7 = 3 RIR.

Target RPE zones by exercise role:

| Role                  | Target RPE | Why                                |
|-----------------------|------------|------------------------------------|
| Heavy primary          | 8–9        | Hypertrophy-grade, controlled bar speed |
| Secondary compound     | 7–8        | Reserve for fatigue accumulation   |
| Isolation / pump      | 9–10       | Local failure, low systemic cost   |
| Rehab isometric       | 6          | Pain-free dose, not failure         |

If the user logs an RPE >2 zones hotter than programmed for the same load → drop load next session by 5–10% and investigate (sleep, calories, tendon).

## Progression scheme per specialization block (4 weeks)

- **Week 1 (introduction)**: build to RPE 7 with target load; record baseline.
- **Week 2 (push)**: +5% load OR +1 set at the same target RPE, whichever keeps RPE ≤ target zone.
- **Week 3 (push)**: same as Week 2, but only if recovery ≥ 70 and average RPE last week ≤ target.
- **Week 4 (realize / deload decision)**: if recovery fell below 60 or week-3 RPE spiked → deload (load −20%, target sets × 0.5). Otherwise hold load, plan next block.

Stall definition (already computed in `coach_trend`): `trend_direction == "stalled"` when est_1RM fails to advance across 2 sessions with similar RPE. On stall → deload + reset the load by 5% before progressing again.

## Deload rules

- Triggered by: recovery < 50, two consecutive sessions with RPE spike (logged > 2 above target), active tendon flare, or week 4 of a specialization block.
- Standard deload: total volume half (-50%), load 60–70% of last working load, no set to failure.
- Duration: 1 week. Re-test baseline on week 5.

## Plan modification triggers (write to decision_log via orchestrator when used)

- `trend_direction == "stalled"` → cycle exercise or reset load
- `recovery_score < 60` for two consecutive checks → reduce weekly volume 20%
- `pain_flag == true` in last session → exercise contraindicated 10–14d (seed injury_status)
- `form_quality < 3` logged twice in same exercise → reduce load 10%, add technique work