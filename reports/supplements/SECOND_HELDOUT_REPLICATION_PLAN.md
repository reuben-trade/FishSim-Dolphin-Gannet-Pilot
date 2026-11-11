# Second held-out H1/G36 replication: prospective plan

**Prepared 11 November 2026. At this record, the simulation harness has passed source review; preparation and simulations for this new cohort have not started.**

This plan asks whether the H1/G36 feeding benefits extend to sixteen further, independent starting schools. It was developed **after the original sixteen-school result was known, but before preparing or feeding any school in this new cohort**. It is a prospective record, not formal preregistration. The [original validation plan](VALIDATION_PREANALYSIS_PLAN.md), [current notebook](../../main.ipynb) and [bundled original evidence](../../data/primary_validation192_2026-11-11/SNAPSHOT.json) remain available and unchanged.

## Fixed design

The new school seeds are **39166601–39166616**. They are distinct from the declared earlier cohorts; this check will be repeated before starting. The [H2/G12](LOWER_COUNT_FOLLOWUP_PLAN.md) and [crossed follow-ups](CROSSED_FOLLOWUP_PLAN.md) reuse the original sixteen schools, so those experiments do not increase the number of independent starting schools.

Keep twelve dolphins, thirty-six gannets, 160 initial fish and minimum herding duration H=1T. Predator behavior, launch locations, mouth-contact geometry and the probability of capture **given an eligible contact**, q=0.7, stay fixed. Each new school has two paired randomness labels, 71001/71002, matched dolphin-only, bird-only and mixed groups, and both encounter timesteps: coarse 0.00125T and primary fine 0.000625T. Encounters have a planned horizon of 36T. T is uncalibrated model time.

This gives **192 feeding encounters**: sixteen schools × two labels × three groups × two grids. Labels vary capture, tie and bird-target randomness while readiness remains paired. They are nested repeats: there are thirty-two labelled worlds, **not thirty-two independent schools**.

## Fresh preparation and complete reporting

Each school receives one continuous, predator-free 92T preparation on the coarse grid. Save its encounter checkpoint at 20T; use 20–56T for the unchanged eligibility screen and 56–92T for diagnostics only. The extra diagnostic interval cannot select schools. All treatments and both encounter grids use that school's same 20T checkpoint. This tests encounter-grid sensitivity, not preparation-grid convergence.

Retain every candidate disposition. A failed eligibility screen or technical failure stops the sequence for review, without replacement seeds, silent exclusions or automatic retries. Feeding proceeds in four fixed four-school blocks, coarse then fine, completing both single-species controls before mixed groups. **All 192 encounters are required regardless of benefit signs**; retain gains, ties and losses. Interim paired-block summaries are descriptive only, without confidence intervals or a primary decision.

## Locked analysis

For each species, divide mixed-minus-alone captures by its group size, average the two labels within each school, then weight the sixteen schools equally. Food is captures per individual over the planned 36T, including valid early prey depletion.

The two fine-grid effects are co-primary. Use two-sided **97.5% Student t intervals, df=15**; the mutual-benefit criterion requires both lower bounds above zero, only after all cases and independent audits are complete. These two intervals target approximately 95% simultaneous coverage under the school-level assumptions. Coarse effects and paired fine-minus-coarse contrasts are secondary; nonsignificant grid differences do not establish equivalence or convergence.

A fixed, saved 50,000-draw whole-school-vector bootstrap, PCG64 seed 8611030, is sensitivity analysis. It preserves species/grid pairing and cannot replace or rescue the t-based criterion. The original primary decision remains intact. **Pooling the old and new schools into an n=32 primary analysis is disabled**; any later combined analysis needs a separate prospective method.

## Sequence and limits

Starting requires complete, independently audited H2/G12 and crossed studies, whatever their signs, followed by fresh code, preparation, starting-state, short-check and feeding reviews. All new-cohort execution remains closed at this record.

The planned ceiling is **406 model initializations and 9,500,800 steps**: sixteen preparations, 192 zero-step checks, six short software checks and 192 full encounters. The provisional runtime is **14–18 hours after a future launch**, unconfirmed and subject to hardware, queueing and technical delays. This replication promises neither positive findings nor publication. Its conclusions concern simulated food, not fitness or field validity.
