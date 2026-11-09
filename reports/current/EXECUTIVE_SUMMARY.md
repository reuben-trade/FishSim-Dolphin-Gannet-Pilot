# FishSim dolphin–gannet pilot: executive summary

**9 November 2026 — complete balanced map, including the four-school 9/12/18-gannet extension**

## Main finding

Adding gannets increased mean dolphin catches in **14 of 18** tested herding-duration/group-size settings; one was unchanged and three were negative. The largest mixed dolphin total tied at **1T herding with nine or eighteen gannets: 91→127 captures (+39.6%)**, with dolphin gains in all four schools. Nine birds are reported by the fewer-birds tie convention, not as a confirmed optimum. At 1T/nine birds, gannets changed 34→52, with three school gains and one tie.

With **2T herding and twelve gannets, both species gained in all four schools**: dolphins 86→110 (+27.9%) and gannets 31→57. Mixed dolphins also exceeded the stronger, best-tested H=1T dolphin-only benchmark 91→110 (+20.9%); the exploratory pointwise interval remained positive. Six and eighteen birds at H=2T also gave joint gains in every school, although their stronger-baseline intervals crossed or touched zero.

These are conditional model results. All settings use the same four previously observed schools and one stochastic setting per school. Searching this bank and reporting pointwise intervals does not establish an optimum, independent validation or a general biological advantage.

## What was compared

- Every encounter began with 160 fish and lasted 36T. Dolphin-bearing encounters used 12 dolphins; gannet-only controls omitted dolphins. Time and length are uncalibrated model units.
- Dolphins followed the same exposed-prey herd–strike rule in both conditions. Each cycle requires H of continuous local near-prey pressure, followed by one feasible strike and recovery. H is a herding proxy, not verification of a completed bait ball.
- The balanced map crosses H = 1, 2 and 3T with one, three, six, nine, twelve and eighteen gannets. Each mixed setting was compared with its **same-H dolphin-only baseline** and a **same-count gannet-only control**.
- Fish state, dolphin starts/readiness and initial dolphin random streams were matched within each comparison. The four school setups differed in fish configuration, predator readiness and school-linked random streams.
- Birds had idealised global prey information within their depth limits and targeted accessible dense clusters. Capture required eligible physical mouth contact, then a fixed 0.7 success draw. No post-dive capture bonus was imposed.

## Complete dolphin results

Totals pool the same four schools. Percentages compare mixed catches with the no-gannet baseline in that row.

| Herding minimum | Dolphins alone | 1 bird | 3 birds | 6 birds | 9 birds | 12 birds | 18 birds |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1T | 91 | 98 (+7.7%) | 107 (+17.6%) | 113 (+24.2%) | 127 (+39.6%) | 126 (+38.5%) | 127 (+39.6%) |
| 2T | 86 | 90 (+4.7%) | 95 (+10.5%) | 103 (+19.8%) | 103 (+19.8%) | 110 (+27.9%) | 103 (+19.8%) |
| 3T | 73 | 68 (-6.8%) | 72 (-1.4%) | 78 (+6.8%) | 77 (+5.5%) | 73 (+0.0%) | 65 (-11.0%) |

At 1T/nine birds, dolphin school gains were +8, +12, +5 and +11 fish. Gannet changes were +8, 0, +7 and +3: the fourth school tied its control, so this is not four-school joint improvement. Mean changes per predator over 36T were +0.75 dolphin captures (pointwise 95% interval +0.54 to +0.96) and +0.50 gannet captures (+0.17 to +0.83). The nine- and eighteen-bird dolphin totals tie; their school outcomes and bird returns differ.

At 2T/twelve birds, mean gains were +0.50 captures per dolphin (+0.21 to +0.71) and +0.54 per bird (+0.17 to +0.92). Against the stronger H=1T D-only benchmark, the dolphin mean gain was +0.40 (+0.21 to +0.58). All intervals resample the same four school vectors; none is adjusted for searching 18 settings.

## Why does longer herding show a smaller dolphin benefit?

The saved records support three related observations. The six-bird comparisons below retain the original discovery subset; Figure 4 and the notebook extend the diagnostics to every count through 18. At H=1T with nine birds, eligible dolphin contacts changed 130→179, launches 251→281 and food 91→127 under the same conditional success rule.

**Longer herding leaves fewer strike opportunities within a fixed encounter.** With six gannets, mean recorded herding time per dolphin increased from 6.12T at H=1 to 13.29T at H=3; attack-mode time fell from 17.33T to 11.29T. Conditional mouth-contact success remained fixed, so additional herding carries a time cost without an automatic increase in capture probability.

**The additional contacts associated with gannets become smaller.**

| Herding minimum | Dolphin launches: alone → mixed | Eligible contacts: alone → mixed | Additional dolphin catches |
|---|---:|---:|---:|
| 1T | 251 → 267 | 130 → 156 | +22 |
| 2T | 197 → 208 | 121 → 136 | +17 |
| 3T | 168 → 164 | 100 → 107 | +5 |

**The prey-state change is also smaller at longer H.** The time-averaged outward-motion proxy of surviving fish changed from 10.4% to 33.8% at H=1, from 27.6% to 36.5% at H=2, and from 32.7% to 36.6% at H=3 when six gannets were added. Birds therefore added less outward motion over the longer-H baselines. Whether this mediates better prey accessibility remains untested. This proxy is not a count of accessible targets or a prerequisite for dolphin attacks. Whole-school radius did not consistently increase with gannets.

These are descriptive explanations, not a causal decomposition. Herding, disturbance, consumption and survivor selection change together. Longer H also coincided with greater gannet food at six birds: 37 captures at H=1, 53 at H=2 and 51 at H=3. The trade-off between dolphin strike time and bird opportunities warrants investigation.

## Strength and limits of the evidence

The first discovery sweep comprised 60 executions, including eight exact historical replays, and took **3 hours 18 minutes** with three workers. The balanced extension added 48 encounters with eight workers; feeding ran from 17:25 to 19:40 Perth, approximately **2 hours 15 minutes**, followed by final audits. All 108 retained/new outcomes, 48 new physical reviews, 72 paired contrasts, 18 summary cells, source/dispatch bindings and bootstrap calculations passed independent review. The sample remains four schools. The first-school 12-case pilot is a subset of the 48 new encounters, not an additional cohort.

Earlier shared-rule pilots showed dolphin gains of 17.1% and 16.1%. A separate eight-school study gave 168→176 dolphin catches at 36T on the original timestep, 179→179 on a halved timestep, and 352→380 at the secondary 72T horizon on the original timestep. Those finer runs did not repeat the original positive cohorts or this new sweep. They show why numerical sensitivity and generalisation remain open questions.

School identity is not an ecological explanation. The present sweep cannot separate starting-state/readiness effects from random capture, target-choice and tie-resolution effects. Captures also exclude energetic costs, learning and fitness.

## Higher-gannet extension: complete

The extension tested **9, 12 and 18 gannets at every H** on the same four schools, retaining all old 1/3/6-bird results and reusing same-H D-only controls. Each new count has its own G-only controls. All 48 full encounters completed, using exactly 1,382,400 feeding steps; the five preceding 4T engineering checks used 16,000 steps separately. Every setting was retained regardless of sign.

Counts 9/12/18 place 3/4/6 birds at each of the same three launch sites. Predators are point-represented and have no body-spacing avoidance, so the high-count outcomes describe idealised pressure and competition rather than calibrated crowding. More birds did not produce uniformly increasing dolphin returns: at H=3T, eighteen birds gave 73→65 captures, while twelve gave 73→73.

The [first-school preliminary tables](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/reports/current/PRELIMINARY_HIGH_COUNT_PILOT.md) remain separately archived with their n=1 scope; the complete four-school map supersedes them for ensemble interpretation. Fresh-school feeding and stochastic-repeat runs remain on hold. The eight-school predator-free preparation already completed contains no feeding outcomes. Numerical checks on these new counts and independent validation remain future work.

## Report and reproducibility

The report presents one dolphin model, the separate positive pilots and replication, the complete parameter map, and prey/contact diagnostics within four figures. Its central claim is conditional feeding benefit under a fixed local dolphin rule. The completed map should not be described as evidence of intentional interspecies cooperation or an unrestricted best strategy.

- [Current report PDF](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/reports/current/Feeding_Frenzy_Working_Draft.pdf)
- [Runnable analysis notebook](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/main.ipynb)
- [Complete discovery summary table](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/data/research/high_count_regime_extension_2026-11-09/results/full_36T_v1/analysis_final/regime_summary.csv)

The current main.ipynb reproduces the revised paper’s four figures and six summary tables without running simulations. The archived v6 notebook retains the full raw-evidence workflow and 19 tables. Its optional model runner has a separate, narrower tested scope, documented in the repository.
