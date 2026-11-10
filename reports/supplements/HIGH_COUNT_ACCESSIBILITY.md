# Supplemental analysis: geometric prey access through 36 gannets

This is a descriptive reanalysis of the **same four previously examined schools**, with 12 dolphins, one capture-stream setting and the original 0.00125T timestep. It covers all 128 bird-bearing encounters from the 140-outcome discovery map: 96 mixed and 32 bird-only. Each lasts 36T. The saved 0.1T frames give 46,208 observations, not 46,208 independent replicates. The original 48-run departure diagnostic is reconciled exactly. There are no new simulations, schools, controller decisions or bootstrap draws.

The current six-page paper and `main.ipynb` are unchanged. New fresh-school validation is separate and contributes no results here.

## What geometric access measures

**Potential access time** is sampled time when at least one bird has at least one live fish passing the frozen new-target depth, range and travel-feasibility checks. It includes birds already attacking, busy or recovering: it is potential geometry, not time when a bird is ready to launch, a selected target or a completed contact. A committed attack may retain a target that no longer passes the new-target gate.

**Depth blackout** means live fish remain but none pass the operative depth cap/detection-depth test, irrespective of bird position. **Shallow but unreachable** means some fish pass that depth test but no bird has a live fish passing its range/travel checks. The operative new-target cap is about 7.93 model units for these bird settings. Boolean durations hold saved frames constant to the next 0.1T sample; transition boundaries have one-sample uncertainty. T and length are uncalibrated model units.

The **depth-eligible fraction** is the fraction of surviving fish passing only the depth test, time-averaged within each school and then averaged equally across four schools. It is different from the existence of one geometrically reachable target. Prey removal changes the surviving population, and dolphin presence changes prey trajectories, bird positions, access and removals together.

## H=1/G=36: longer potential windows, similar average depth-eligible fraction

Across four matched schools, adding 12 dolphins to 36 birds changes realised bird launches **355→921**, eligible oral contacts **26→130**, and captures **16→94**. School-mean potential access time changes **20.175→31.850T (+11.675T)**. Mean depth-blackout time changes **11.575→4.150T (−7.425T)**; blackouts shorten in every school, by 6.0, 9.7, 6.5 and 7.5T.

The other 4.250T of the mean access difference comes from less shallow-but-unreachable time. This is entirely one bird-only school (seed 39063502) with a 17T period; the other three have none. It should not be described as four replicated losses of shallow access. Meanwhile, mean depth-eligible live-fish fraction is almost unchanged: **0.291324→0.291007**. The longer potential window does not mean a larger average fraction of shallow fish in this contrast.

These observations associate successful mixed trajectories with longer potential-access windows and more realised attack/contact opportunities. They do not establish that herding caused the gain, isolate depth from bird travel, or prove that access duration alone explains feeding returns.

## Complete 24-condition comparison

Every row compares mixed groups with the same-count bird-only controls on the same four schools. Capture entries are four-school totals; all other entries are equal-school mean changes, mixed minus bird-only. Positive potential-access change means more geometric opportunity; negative blackout/unreachable change means less time without access. Fraction changes are **percentage points**, not percent changes. Values are rounded for display; exact school and frame data remain in the linked CSVs.

| H (T) | Birds | Bird captures alone→mixed | Δpotential access (T) | Δdepth blackout (T) | Δshallow unreachable (T) | Δdepth-eligible fraction (pp) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 13→12 | +1.025 | -1.025 | 0.000 | +6.095 |
| 1 | 3 | 24→22 | -0.300 | +0.300 | 0.000 | +0.667 |
| 1 | 6 | 24→37 | +3.225 | -1.975 | -1.250 | -0.160 |
| 1 | 9 | 34→52 | +4.275 | -4.275 | 0.000 | +5.313 |
| 1 | 12 | 31→37 | +2.875 | -2.875 | 0.000 | +6.203 |
| 1 | 18 | 31→44 | +0.775 | -2.875 | +2.100 | +6.368 |
| 1 | 24 | 21→80 | +12.175 | -8.425 | -3.750 | +5.424 |
| 1 | 36 | 16→94 | +11.675 | -7.425 | -4.250 | -0.032 |
| 2 | 1 | 13→13 | +1.850 | -1.850 | 0.000 | +0.289 |
| 2 | 3 | 24→29 | -0.225 | +0.225 | 0.000 | +3.991 |
| 2 | 6 | 24→53 | +7.900 | -5.625 | -2.275 | +16.050 |
| 2 | 9 | 34→42 | +0.300 | -0.300 | 0.000 | +4.751 |
| 2 | 12 | 31→57 | +4.050 | -4.050 | 0.000 | +14.516 |
| 2 | 18 | 31→75 | +5.700 | -5.700 | 0.000 | +7.952 |
| 2 | 24 | 21→72 | +10.225 | -6.475 | -3.750 | +6.149 |
| 2 | 36 | 16→66 | +12.550 | -8.300 | -4.250 | -2.609 |
| 3 | 1 | 13→13 | +1.850 | -1.850 | 0.000 | +5.810 |
| 3 | 3 | 24→30 | -0.675 | +0.675 | 0.000 | +4.306 |
| 3 | 6 | 24→51 | +7.725 | -5.450 | -2.275 | +5.108 |
| 3 | 9 | 34→47 | +3.925 | -3.925 | 0.000 | +1.469 |
| 3 | 12 | 31→66 | +4.350 | -4.350 | 0.000 | +18.173 |
| 3 | 18 | 31→48 | -2.875 | +1.225 | +1.650 | -3.398 |
| 3 | 24 | 21→54 | +3.300 | +0.450 | -3.750 | +2.151 |
| 3 | 36 | 16→47 | +10.275 | -6.025 | -4.250 | +0.009 |

Potential access increases in 20 of 24 conditions. It is not a sufficient explanation: bird captures improve despite shorter potential-access time at **H=2/G=3, H=3/G=3 and H=3/G=18**. All unfavourable and nearly unchanged responses remain in the table. These are post hoc associations from a previously explored bank, with n=4 and no new uncertainty intervals, not independent confirmation of a selected setting. Terminal-contact-loss flags describe the 36T boundary, not permanent abandonment or a demonstrated need for continuous diving.

## Data, source and replay

The [case](../../analysis_supplements/higher_count_accessibility_2026-11-10/outputs/case_accessibility.csv), [frame](../../analysis_supplements/higher_count_accessibility_2026-11-10/outputs/sampled_accessibility.csv), [paired-school](../../analysis_supplements/higher_count_accessibility_2026-11-10/outputs/paired_accessibility.csv) and [24-condition](../../analysis_supplements/higher_count_accessibility_2026-11-10/outputs/regime_accessibility.csv) tables are saved outputs. [Audit and portable replay instructions](../../analysis_supplements/higher_count_accessibility_2026-11-10/README.md) retain the exact author analysis and independent review. The author source contains original absolute research paths; the separate portable adapter reconstructs a temporary file view from 644 hash-mapped inputs already bundled here, including one newly archived geometry-code dependency. It starts no model and creates no bootstrap draws.
