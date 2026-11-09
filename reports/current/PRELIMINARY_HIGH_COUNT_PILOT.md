# PRELIMINARY: higher-gannet feeding pilot

**9 November 2026, 18:00 Perth — complete 9- and 12-gannet panels; 18-gannet panel pending.**

These are descriptive results from **one previously observed school (39061001, n=1)**, capture setting 61001, at 36T. Each completed panel contains all three herding minima and its matched gannet-only control. The same dolphin rule is used with and without birds. H is the minimum duration of continuous local near-prey pressure, not confirmation of a completed bait ball.

Counts below are fish captured by the whole pod or bird group. Every dolphin-bearing encounter has 12 dolphins and begins with 160 fish. Time is an uncalibrated model unit. Dolphin effects use the same-H dolphin-only control; gannet effects use the same-count gannet-only control. The six-bird dolphin reference uses this same school and capture setting, rather than the four-school aggregate.

## Nine gannets: all four encounters complete

| H (T) | Dolphins alone | Dolphins with 6 birds | Dolphins with 9 birds | Dolphin change | Gannets alone → mixed | Both species gain here |
|---:|---:|---:|---:|---:|:---|:---|
| 1 | 23 | 27 | 31 | +8 (+34.8%) | 3 → 11 | Yes |
| 2 | 22 | 23 | 26 | +4 (+18.2%) | 3 → 2 | No |
| 3 | 19 | 19 | 15 | −4 (−21.1%) | 3 → 13 | No |

## Twelve gannets: all four encounters complete

| H (T) | Dolphins alone | Dolphins with 6 birds | Dolphins with 12 birds | Dolphin change | Gannets alone → mixed | Both species gain here |
|---:|---:|---:|---:|---:|:---|:---|
| 1 | 23 | 27 | 29 | +6 (+26.1%) | 4 → 6 | Yes |
| 2 | 22 | 23 | 29 | +7 (+31.8%) | 4 → 16 | Yes |
| 3 | 19 | 19 | 12 | −7 (−36.8%) | 4 → 7 | No |

## Interpretation and limits

Both completed bird counts produced dolphin gains at H=1 and H=2 and losses at H=3 on this school. Gannet returns varied with H. These outcomes do not select an overall winning group size, establish a monotonic response, or estimate how often another school would benefit.

There is no across-school SD or confidence interval for this pilot. The H settings, individual predators and shared controls are not independent school replicates. A single capture setting cannot separate starting-state/readiness effects from stochastic capture and target-choice effects. More birds share the original three launch sites; point-represented predators have no body-spacing avoidance, so these are idealised model conditions.

The 18-gannet panel is pending. These pilot encounters are a subset of the planned **48-case, four-school** extension. The remaining encounters and complete map will be assessed separately; all settings, including losses, will be retained. The [main report](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/reports/current/Feeding_Frenzy_Working_Draft.pdf) and [analysis notebook](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/FishSim_Professor_Notebook.ipynb) continue to present the completed four-school 1/3/6-bird study and its separate earlier cohorts. Their numerical-sensitivity caveat remains applicable; the higher-count pilot has not been tested on the finer timestep.

## Validation record

Two independent readers reconciled raw capture/contact/launch events, unique prey removals, per-actor totals, time budgets and sealed summaries. Case/source/dispatch bindings, physical checks, and matched initial fish/predator/controller/private-stream states passed for every encounter and control. Neither reader ran native simulation steps. The new raw evidence will be packaged with the completed extension rather than mixed into the current notebook prematurely.

- G9 physical/descriptive receipt SHA256: `b59cb77b6a60c25f935bb04120138faa2da508e39f7b13acc67f13a8c318a53d`; independent reader receipt: `1e445f4f59746078c31c4f3c602fa6532449ecce6e7e3ec7a16734e95d006f78`.
- G12 physical/descriptive receipt SHA256: `000fbe77a886bd8aac5f239a3ba9d2a314d10677d0b144e8f4c9adc60142022c`; independent reader receipt: `ebfffbdcc97fcb19d0c8b3b6f5a011e53e4f2c0fb2a55f74194800e3ba30da73`.
- Frozen scientific source SHA256: `573a30e4860cb36176140352c5d64be2c42de61c2456e0d1955f9ac8a5edf831`.
- Dispatch source SHA256: `0aec537f7f382a84dc851fe46f468187aa3083ec891ab23d8586311f6a1a23e4`.
