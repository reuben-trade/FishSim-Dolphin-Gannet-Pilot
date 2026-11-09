# FishSim dolphin–gannet pilot: executive summary

**9 November 2026 — completed discovery sweep; higher-gannet feeding pilot running**

## Main finding

Adding gannets increased dolphin catches in seven of nine tested herding-duration/group-size settings. The largest dolphin gain was **24.2% with 1T herding and six gannets**, positive in all four starting schools. With **2T herding and six gannets, both species gained in all four schools**.

These are promising results within the implemented model. They identify conditions for further testing; four previously observed schools and one stochastic setting per school do not establish a general biological advantage or an optimum group size.

## What was compared

- Every encounter began with 160 fish and lasted 36T. Dolphin-bearing encounters used 12 dolphins; gannet-only controls omitted dolphins. Time and length are uncalibrated model units.
- Dolphins followed the same exposed-prey herd–strike rule in both conditions. Each cycle requires H of continuous local near-prey pressure, followed by one feasible strike and recovery. H is a herding proxy, not verification of a completed bait ball.
- The sweep crossed H = 1, 2 and 3T with one, three and six gannets. Each mixed setting was compared with its **same-H dolphin-only baseline** and a **same-count gannet-only control**.
- Fish state, dolphin starts/readiness and initial dolphin random streams were matched within each comparison. The four school setups differed in fish configuration, predator readiness and school-linked random streams.
- Birds had idealised global prey information within their depth limits and targeted accessible dense clusters. Capture required eligible physical mouth contact, then a fixed 0.7 success draw. No post-dive capture bonus was imposed.

## Complete dolphin results

Totals pool the same four schools. Percentages compare mixed catches with the no-gannet baseline in that row.

| Herding minimum | Dolphins alone | One gannet | Three gannets | Six gannets |
|---|---:|---:|---:|---:|
| 1T | 91 | 98 (+7.7%) | 107 (+17.6%) | **113 (+24.2%)** |
| 2T | 86 | 90 (+4.7%) | 95 (+10.5%) | **103 (+19.8%)** |
| 3T | 73 | 68 (−6.8%) | 72 (−1.4%) | 78 (+6.8%) |

At 1T/six gannets, dolphin gains were +4, +9, +4 and +5 fish. Gannet totals increased from 24 alone to 37 mixed, but one school had a gannet loss; its exploratory interval includes zero.

At 2T/six gannets, dolphin totals increased from 86 to 103 and gannet totals from 24 to 53. Both species gained in every school. Against the stronger, best-tested dolphin-only baseline of 91 captures at H=1T, mixed dolphins still caught 103, but uncertainty in that stronger comparison includes zero.

## Why does longer herding show a smaller dolphin benefit?

The saved records support three related observations.

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

The sweep comprised 60 executions, including eight exact historical replays, and took **3 hours 18 minutes** with three workers, including final checks. All case seals, physical/accounting checks, raw catches and the whole-school bootstrap passed independent review. The independent sample remains four schools. Intervals are exploratory and pointwise across a searched parameter grid.

Earlier shared-rule pilots showed dolphin gains of 17.1% and 16.1%. A separate eight-school study gave 168→176 dolphin catches at 36T on the original timestep, 179→179 on a halved timestep, and 352→380 at the secondary 72T horizon on the original timestep. Those finer runs did not repeat the original positive cohorts or this new sweep. They show why numerical sensitivity and generalisation remain open questions.

School identity is not an ecological explanation. The present sweep cannot separate starting-state/readiness effects from random capture, target-choice and tie-resolution effects. Captures also exclude energetic costs, learning and fitness.

## Next experiment: increase gannet numbers

The current priority is a balanced extension to **9, 12 and 18 gannets at all three herding durations**. Existing 1/3/6-bird results and same-H dolphin-only controls will be retained; each new count receives its own gannet-only control. This adds **48 full encounters**, or at most **1,382,400 feeding steps**, before bounded integration checks.

Counts 9/12/18 place 3/4/6 birds at each of the same three launch sites. This preserves the launch footprint while testing greater local multiplicity. Predators are point-represented and have no body-spacing avoidance, so high-count outcomes describe idealised pressure and competition rather than calibrated real crowding.

The extension is running with **eight single-thread workers**, with a first feeding pilot on one school at every new setting before the remaining schools. By 18:00 Perth, complete nine- and twelve-gannet panels had passed two independent raw/physical reviews; the eighteen-gannet panel remained pending. The [separate preliminary pilot tables](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/reports/current/PRELIMINARY_HIGH_COUNT_PILOT.md) include all three H settings, matched controls and the same-school six-bird reference. These are n=1 point outcomes with no across-school error bars, not replacements for the four-school discovery results above. The provisional estimate is **about 2–3 hours for all 48 feeding encounters with eight workers**, plus final checks; it will be updated from measured throughput. All settings will be retained regardless of outcome. Six birds is the upper boundary of the completed four-school sweep, not an established optimum.

Fresh-school feeding and stochastic-repeat runs are on hold in favour of this expansion. The eight-school predator-free preparation that had already begun was retained to completion; it produced no feeding outcomes. Complete one-school pilot panels are available separately; the full higher-count four-school results remain pending.

## Report and reproducibility

The report presents one dolphin model, the separate positive pilots and replication, the complete parameter map, and prey/contact diagnostics within four figures. Its central claim is conditional feeding benefit under a fixed local dolphin rule. The completed map should not be described as evidence of intentional interspecies cooperation or an unrestricted best strategy.

- [Current report PDF](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/reports/current/Feeding_Frenzy_Working_Draft.pdf)
- [Runnable analysis notebook](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/FishSim_Professor_Notebook.ipynb)
- [Complete discovery summary table](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/data/research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1/analysis_final/regime_summary.csv)

The notebook reproduces the saved evidence, four figures and 19 tables without running native simulations. Its optional model runner has a separate, narrower tested scope, documented in the repository.
