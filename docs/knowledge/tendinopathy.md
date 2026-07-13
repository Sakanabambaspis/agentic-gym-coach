# Tendinopathy Management

User has chronic history of bilateral elbow and knee tendinopathy (overuse tendinosis, not acute tear). Tendons heal in months, not weeks. The goal is **irritation management**, not push-through-pain heroics.

## Pathophysiology (one sentence)

Tendinopathy is a failed-healing collagen response. Load tolerance is dose-dependent: a correctly-loaded tendon rebuilds, an overloaded one flares. The threshold moves day-to-day based on sleep, calories, stress, recent volume.

## Pain protocol — non-negotiable

1. **Pain during a set ≥ 4/10** → terminate that exercise immediately, flag `pain_flag=true` in the log, drop volume for that pattern in the next session by 50%.
2. **Pain after a set that resolves within 1 minute** → continue but lower load by 10% next set.
3. **Pain next morning (46–70h latency)** → that exercise is contraindicated for the next 10–14 days. Use `coach_injuries_seed` to mark that location `active`.
4. **Stiffness-only (no sharp pain)** → proceed, treat as chronic baseline. Warm-up extended to gradient-loaded singles.

## High-risk patterns for this user

| Pattern                                    | Risk          | Mitigation                          |
|--------------------------------------------|---------------|-------------------------------------|
| Skull Crusher / overhead tricep extension  | Elbow flare   | Replace with cable pushdown (neutral grip) — see `safety.md` |
| Heavy barbell bench with elbow flare       | Elbow flare   | Use closer grip, moderate range      |
| Leg extension to full lockout              | Knee flare    | Avoid end-ROM; partial-range only    |
| Heavy back squat (deep)                    | Knee flare    | Front squat / box squat to parallel  |
| High-rep crunch extensions                 | Lower back    | Replace with reverse hyper / RKC plank |

## Tendon-friendly loading heuristics

- **Eccentric tempo** 3–4s on the lowering phase for the affected pattern (proven tendinosis rehab stimulus).
- **Frequency > intensity** for tendon rehab: 2–3 light "tendon meals" per week beat 1 heavy session.
- **Isometrics** at 70% 1RM for 5×45s holds are rehab-grade for both elbow and knee flare-ups.
- **Heavy slow resistance (HSR)** after pain-free isometrics for 2 weeks: 3×10 @ 6–8 RPE, 3s ecc, 3s con.

## What "safe alternative" means

The `coach_safety_check` tool returns alternatives for any banned exercise — use them verbatim. Do not improvise. If the user asks for an alternative not in the list, call `coach_safety_check` again with that exercise before suggesting.

Read `safety.md` for the full contraindication list per active injury.