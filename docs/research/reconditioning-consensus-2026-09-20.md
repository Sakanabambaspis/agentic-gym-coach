# Why the Helms Training book never says "reconditioning" — and what the evidence says about returning after a layoff

**Date:** 2026-09-20 · **Type:** primary-source research note
**Location note:** this file created `docs/research/` (new directory). The repo keeps review notes in `docs/reviews/`, but those are code-review artifacts; a research note is a different genre, so it gets its own directory rather than being shoehorned into `docs/reviews/`.

## The question

`models/enums.py` defines `PhaseType.reconditioning` ("return from layoff or into base work") under a docstring attributing the phase vocabulary to "Helms' block-periodization vocabulary (…Training ch04)". The vendored book text contains zero hits for "reconditioning" or "layoff". Where does the term actually come from, what does science say about reconditioning, and is the repo's usage defensible?

## What the vendored book actually says

Greps over `docs/knowledge/helms-training-pyramid/` (all `.md`, 2026-09-20): **zero hits** for reconditioning, layoff, detrain, decondition, "time off", "return to training", maintenance, "general adaptation", supercompensation, transitional, preparatory.

**Vocabulary it does use** (all in ch04 + `glossary.md`): accumulation → intensification → realization blocks (glossary.md:3,15,69; chapters/ch04:16,23–25), deload (ch04:11,22), reactive deload checklist (ch04:11), mesocycle/macro/microcycle (glossary:47), block/linear/undulating periodization (ch04:14–19), **intro cycle** (ch04:13), taper/peaking, functional/nonfunctional overreaching, overtraining, fitness-fatigue model (ch03). Notably the book has *no* GAS/supercompensation framing at all — its periodization chapter is RPE-and-volume-led, not classical-phase-led.

**What it says about interruptions (closest analogs):**
- Missed **session** protocol: "Missed workout → pick up where you left off" (ch02 worked example) — a horizon of days, never months.
- **Intro cycle**: "an intro week acclimates you *before* a volume block — run ~75% of planned volume at ~1 RPE lower" (ch04:13; glossary:43). This is the book's only conservative-ramp mechanism, and it sits *inside* continuous training.
- Restart after stall: "finish the cycle… → deload week → **restart 5–10% lighter**" (ch09:11).

**Scope:** a principles book for *continuous* trainees. SKILL.md "Scope & Limits": authors "explicitly defer injury treatment to sports-medicine specialists"; ch02's pain protocol stops at "see a specialist when it persists." Detraining physiology is simply out of scope — the repo already says this about timelines (COACH_PROMPT: gap threshold is "NOT book doctrine — the books don't cover detraining timelines"), but not about the word itself.

**Repo provenance:** `migrations/versions/0001_initial_schema.py` shows v1's original phase enum was `internship_maintenance, bridge_reconditioning, specialization_lean_bulk, diet_break, mini_cut` — no Helms lineage. Migration 0002 (2026-09-09) remapped `bridge_reconditioning → reconditioning` as part of "the goal-agnostic **Helms-style** vocabulary", and the `enums.py` docstring then claimed the whole set "follow[s] Helms' block-periodization vocabulary (ch04)". That is true for **4 of 8** values (accumulation, intensification, realization, deload); maintenance, reconditioning, cut, lean_bulk are repo conventions (cutting is covered *topically* in ch08/ch09, not as a ch04 phase name).

## The term "reconditioning" — origin and fields of use

"Reconditioning" = restoring something to good condition (industrial usage survives in materials-engineering titles, e.g. propeller reconditioning, [PMID 41010147](https://pubmed.ncbi.nlm.nih.gov/41010147/)). In human performance it is standard vocabulary in three fields, meaning **structured return to conditioning after layoff, deconditioning, or injury**:

- **S&C / athletic development (NSCA):** the official CSCS textbook has a dedicated chapter — *Essentials of Strength Training and Conditioning*, 5th ed. Ch. 23 "Rehabilitation, Reconditioning, and Medical Issues" (4th ed.: "Rehabilitation and Reconditioning") — [nsca.com TOC](https://www.nsca.com/education/articles/books-and-resources/essentials-of-strength-training-and-conditioning-5th-edition/). Reconditioning bridges medical rehab and full training, with progression tied to tissue-healing timelines.
- **Military:** US Army **FM 7-22, *Holistic Health and Fitness*** (Oct 2020), Chapter 13 "Reconditioning Program" — an institutional program for soldiers returning from injury or failing fitness standards ([armypubs.army.mil](https://armypubs.army.mil/)).
- **Clinical / PT:** 353 PubMed titles contain "reconditioning" ([PubMed search](https://pubmed.ncbi.nlm.nih.gov/?term=%22reconditioning%22%5BTitle%5D), 2026-09-20), e.g. exercise reconditioning in type-2-diabetes remission ([PMID 41855034](https://pubmed.ncbi.nlm.nih.gov/41855034/)), postoperative physiotherapy reconditioning ([PMID 39996184](https://pubmed.ncbi.nlm.nih.gov/39996184/)).
- **UKSCA** (UK Strength & Conditioning Association) uses it for the S&C coach's post-injury role ("rehab is for treating injury; reconditioning is a preparation-based model… based on the principles of athletic development") — but my only citable capture is a [UKSCA social post](https://www.instagram.com/reel/DaUsGfpjghG/); **weakly sourced, treat as practitioner lore until pinned to a UKSCA publication.**
- **Periodization-world analog:** Bompa's *Anatomical Adaptation* phase (early preparatory phase, post-transition) is the textbook slot for rebuilding base after an off-season/layoff — corroborated here only via [secondary sources](https://www.academia.edu/129071488/Periodization_training_for_sports); moderately evidenced.

So the term is legitimate and widely used — it just comes from **S&C/rehab/military** vocabularies, not from the Helms book.

## The science: detraining rates, muscle memory, retraining speed

- **Muscle memory (myonuclei):** mouse overload → new myonuclei appear before hypertrophy and are retained through severe atrophy; retention *slowed* atrophy ([Bruusgaard et al. 2010, PNAS](https://pubmed.ncbi.nlm.nih.gov/20713720/)). Review: fibers with extra myonuclei regrow faster on re-overload; mechanism may persist ≥15 years in humans ([Gundersen 2016, J Exp Biol](https://pubmed.ncbi.nlm.nih.gov/26792335/)). Human epigenetic memory: methylation changes persist through unloading and predict faster reload gains ([Seaborne et al. 2018, Sci Rep](https://pubmed.ncbi.nlm.nih.gov/29382913/)); see also [Egner et al. 2013, J Physiol](https://pubmed.ncbi.nlm.nih.gov/24167222/). *Caveat: human myonuclear permanence is still debated; the retraining-is-faster observation itself is robust.*
- **Rates of loss:** strength generally holds ~4 weeks of total inactivity, then declines with falling EMG (neural, not just muscle); capillary density drops within 2–3 weeks; fiber CSA "declines rapidly" in strength athletes; recently gained strength is lost fastest ([Mujika & Padilla 2001, MSSE review](https://pubmed.ncbi.nlm.nih.gov/11474330/)).
- **Cycled detraining:** 24 weeks of 6-week blocks alternating with 3-week layoffs produced CSA/strength gains comparable to continuous training ([Ogasawara et al. 2013, EJAP](https://pubmed.ncbi.nlm.nih.gov/23053130/)) — a 3-week layoff is not a catastrophe.
- **Maintenance dose is small (young):** 1/9th of volume, 1×/week, preserved hypertrophy for 32 weeks in young adults; older adults needed a higher dose ([Bickel et al. 2011, MSSE](https://pubmed.ncbi.nlm.nih.gov/21131862/)).
- **Tendons lag muscle:** tendon structure adapts (and dis-adapts) on month timescales vs days-weeks for neural strength — the physiological rationale for conservative loading on return ([Magnusson & Kjaer 2019, J Physiol review](https://pubmed.ncbi.nlm.nih.gov/29920664/)).

## Consensus recommendations for returning lifters

No position stand prescribes a formal "reconditioning" phase *for gym trainees* — the structured-program precedent is institutional (NSCA textbook chapter; FM 7-22; PT literature). The ACSM resistance-training stand supports the *principle* of individualized, gradual progression (e.g. 2–10% load increments once rep targets are exceeded) ([ACSM 2002, MSSE](https://pubmed.ncbi.nlm.nih.gov/11828249/)) but does not address detraining timelines.

**Injury risk on abrupt return is real but not settled:** after COVID-19 lockdowns, Bundesliga matches showed ~3.1× the pre-lockdown injury rate controlling for games played (0.84 vs 0.27 injuries/game; 17% of injuries in the first match back) ([Seshadri et al. 2021](https://pubmed.ncbi.nlm.nih.gov/33681759/)); an NCAA D1 sample showed elevated post-lockdown rates ([Angileri et al. 2023](https://pubmed.ncbi.nlm.nih.gov/37576455/)); but Spanish competitive athletes showed no significant increase ([Prieto-Fresco et al. 2022](https://pubmed.ncbi.nlm.nih.gov/36612741/)). Honest verdict: **moderately supported, mechanism-plausible (tendons lag), evidence mixed.**

The consistently supported practical synthesis: strength decays slowly at first (neural retention), size decays faster, and **regain is faster than initial gain** — so returning below pre-layoff volume/load and ramping conservatively is well-supported practice. The Helms book's own intro-cycle numbers (≈75% volume, ≈1 RPE lower; restart 5–10% lighter after stalls) are the nearest *Helms-attested* prescriptions for how to dose such a ramp.

## Implications for this repo — is `reconditioning` defensible?

**Substance: yes.** The phase comment ("return from layoff or into base work") matches what the term means in S&C/military/PT usage, and the coached behavior (reduced volume/load, conservative ramp) aligns with Ogasawara, Bickel, Mujika & Padilla, and the ACSM progression principle. **Attribution: no.** `models/enums.py` attributes it to Helms ch04; it is not there.

Recommended (recommendation only — decision is the repo owner's):
1. Re-scope the `enums.py` docstring to mirror how the repo already labels `REASSESSMENT_GAP_WEEKS`: "accumulation/intensification/realization/deload follow Helms ch04; maintenance/reconditioning/cut/lean_bulk are repo conventions. *Reconditioning aligns with standard applied-S&C usage (NSCA Essentials ch23; Army FM 7-22 ch13), not Helms doctrine.*"
2. Add one line in the COACH_PROMPT intake step ("reconditioning" = repo convention consistent with applied S&C practice) beside the existing not-book-doctrine caveat on the gap threshold.
3. Optionally add a CONTEXT.md glossary entry citing this file, and note the intro cycle (75% volume, −1 RPE) as the Helms-attested dosing analog for the phase.
4. Update migration 0002's "Helms-style vocabulary" comment only if touching migrations anyway (historical migrations are usually left alone).

*Weak points in this note:* UKSCA usage and the Bompa AA-phase claim rest on secondary/social sources; the injury-risk-on-return literature is mixed; "reconditioning" PubMed counts are point-in-time.
