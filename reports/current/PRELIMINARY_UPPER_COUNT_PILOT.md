# PRELIMINARY: 24- and 36-gannet feeding pilot

**9 November 2026 — complete first-school pilot, n=1.**

All eight 36T encounters are complete and independently checked: H=1/2/3T with 24 or 36 gannets, plus a matched gannet-only control at each count. This is one previously observed school (39061001), capture setting 61001, not eight independent schools. Dolphin-bearing encounters use 12 dolphins and begin with 160 fish; dt=.00125T. The same dolphin rule and H are used with and without birds. Contact-success q=.7 is unchanged; time and length are uncalibrated model units.

Counts below are total fish captured. Dolphin changes compare the same-H no-bird baseline; gannet changes compare the same-count bird-only baseline. The 18-bird reference uses this same school and stochastic setting, rather than four-school pooled results.

| H (T) | Gannets | D alone | D with 18 birds (reference) | D mixed | D change | G alone → mixed | G change per bird /36T | Both gain here |
|---:|---:|---:|---:|---:|---:|:---|---:|:---|
| 1 | 24 | 23 | 29 | 32 | +9 (+39.1%) | 4 → 16 | +0.500 | Yes |
| 1 | 36 | 23 | 29 | 36 | +13 (+56.5%) | 7 → 26 | +0.528 | Yes |
| 2 | 24 | 22 | 30 | 29 | +7 (+31.8%) | 4 → 19 | +0.625 | Yes |
| 2 | 36 | 22 | 30 | 27 | +5 (+22.7%) | 7 → 25 | +0.500 | Yes |
| 3 | 24 | 19 | 17 | 18 | -1 (-5.3%) | 4 → 9 | +0.208 | No |
| 3 | 36 | 19 | 17 | 18 | -1 (-5.3%) | 7 → 17 | +0.278 | No |

In this single realization, both species gained at H=1 and H=2 for both counts. Dolphins caught one fewer fish at H=3 for both counts, while birds gained. These observations do not establish a winning count, a monotonic response or how often another school would benefit.

**No across-school SD or confidence interval is estimated for n=1.** Individual dolphins, the two counts, H settings and reused controls are not independent school replicates. One stochastic setting cannot separate starting-state/readiness effects from random capture and target-choice effects. Counts 24/36 place 8/12 point birds at each of the same three launch sites; body-spacing avoidance is absent.

These eight encounters are a subset of the declared 32-case extension. The remaining 24 encounters cover the other three schools and remain required regardless of signs. The [main report](Feeding_Frenzy_Working_Draft.pdf) and [notebook](../../main.ipynb) retain the completed four-school 1/3/6/9/12/18-bird map until the full 140-outcome audit passes. The new counts use the original coarse timestep and have not been tested on the finer grid.

The [point-outcome CSV](pilot_upper_count_point_outcomes.csv) and [independent reader receipt](preliminary_upper_count_pilot_receipt.json) retain all six rows, case/control seals and source bindings. Raw upper-count evidence will be packaged with the completed extension.

Validation reconciled raw per-actor/species captures, contacts and launches; unique prey removal; observed time budgets; exact initial fish/actor/controller/private-stream matches; source and completion seals; phase budget 230,400 steps; and all eight physical reviews. The separate independent audit also verified all five 4T engineering prefixes. Neither reader advanced simulation time. Other-school new feeding outcomes were not inspected.

- Scientific source freeze SHA256: `f37d767a57a14b44fe2c32cbb921471b07df3f98a9211a37f6f70db256f64738`.
- Independent complete-pilot review SHA256: `fac4578d572d30c21f055924971e7b5acd755e938bba8dd6338b6f7d922f8af0`.
- Physical review SHA256: `5aaf2f5bbc90ad87eea460783773f2191bd1efebde1403ae97813773e71e188c`.
