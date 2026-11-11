# FishSim: completed discovery and independent validation

Open [main.ipynb](../main.ipynb) from the repository root and Run All Cells. Its 16 logical cells contain 8 code cells; default execution rebuilds 4 numbered figures and 21 canonical CSVs (9 discovery/population, 4 primary validation, 8 H2/programme) with zero model steps and no new bootstrap draws. [Local setup](LOCAL_ANALYSIS_SETUP.md).

## Primary sixteen-school result

The fixed H1/G36 rule was tested on 16 new schools with 2 nested labels, D-only/G-only/DG arms and coarse/fine encounter grids: 192 completed cases. The fine grid is primary. Labels are averaged before the 16-school mean; neither 32 worlds nor 192 executions are treated as independent schools. Same 20T coarse-prepared starts are used on both encounter grids.

| Species | Fine alone→mixed captures | Relative change | Mean gain per individual over 36T | 97.5% t interval |
|---|---:|---:|---:|---:|
| Dolphins |719→905|+25.9%|+0.484375|[0.224689,0.744061]|
| Gannets |292→536|+83.6%|+0.211806|[0.093497,0.330114]|

Both lower bounds exceed zero under the prespecified fine-grid criterion. These two marginal intervals target nominal 95% simultaneous coverage, subject to school independence and Student t assumptions (df 15). Bootstrap 50,000-draw endpoints are a separate cached sensitivity, not a replacement decision. Means include school losses: D 14 positive/1 tie/1 negative, G 14 positive/2 negative; joint gains 12/16. Individual labelled worlds include further losses.

Coarse totals are D 708→889 and G 243→460. Paired fine-minus-coarse gains are D+0.0130 [−0.2208,0.2469] and G+0.0234 [−0.1349,0.1818] fish per individual over 36T. These wide secondary intervals are not an equivalence or convergence proof. All 32 labelled food totals, 16 school vectors and both grids remain in the notebook.

The unchanged dolphin rule herds before striking; there is no bird-triggered bonus. Conditional oral-contact success remains q=0.7. The model result concerns captured fish, not energetic profit, fitness or deliberate coordination. All 192 and the original independent FINAL plus additional metadata proof passed before final publication. Older 48/96/144 snapshots and the public plan retain their actual posting chronology.

## Completed H2/G12 follow-up — same sixteen schools

The follow-up adds 192 encounters on the **same sixteen school clusters**, with new matched H2 dolphin-only and G12-only controls, both labels and both grids. It does not add sixteen independent schools. Fine-grid dolphins catch **679→732 (+7.8%)**, mean **+0.138 fish per dolphin over 36T**, with a **95% pointwise t interval [−0.026, 0.302]**; the mean dolphin benefit remains uncertain. Gannets catch **297→540 (+81.8%)**, mean **+0.633 [0.430, 0.836]** per bird. School means include D10 gains/2ties/4losses and G15gains/1loss; joint gains occur in9/16.

Coarse-grid totals are D691→721 and G268→656. The bird fine-minus-coarse partner gain is −0.378 [−0.641, −0.114] fish per bird, indicating numerical magnitude sensitivity. The additional four-fine-endpoint programme criterion is **not met** at98.75% marginal intervals; it leaves the original H1/G36 primary97.5% criterion unchanged. Both H and bird count change, so this comparison isolates neither factor. All six H2 contrasts, school/world losses, SD/SE and cached bootstrap sensitivity remain in the eight follow-up tables; no new bootstrap draws are made.

## Discovery context

The following complete map/population material concerns four previously observed schools. It is retained rather than pooled with the new sixteen-school estimate. Original shared-rule pilots (+17.1%/+16.1%) and the older eight-school H2/G3 check remain archived separately. In that older setting, halving the timestep changed mean dolphin gains from +1 to 0 fish/school; the new H1/G36 result does not validate every discovery setting.

## Complete discovery map

All24 mixed settings are retained below. Totals cover the same four known schools and capture setting 61001. D controls match H; G controls match bird count. The stronger D-only benchmark is H1 with 91 captures. The notebook supplies all 96 school contrasts and pointwise uncertainty; the outcome-selected intervals are not independent confirmation; H1/G36 now has a separate sixteen-school validation below.

| H (T) | Gannets | D alone → mixed | Same-H D change | D change vs best H | G alone → mixed | Both gain |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 91 → 98 | +7.7% | +7.7% | 13 → 12 | 0/4 |
| 1 | 3 | 91 → 107 | +17.6% | +17.6% | 24 → 22 | 1/4 |
| 1 | 6 | 91 → 113 | +24.2% | +24.2% | 24 → 37 | 3/4 |
| 1 | 9 | 91 → 127 | +39.6% | +39.6% | 34 → 52 | 3/4 |
| 1 | 12 | 91 → 126 | +38.5% | +38.5% | 31 → 37 | 3/4 |
| 1 | 18 | 91 → 127 | +39.6% | +39.6% | 31 → 44 | 2/4 |
| 1 | 24 | 91 → 126 | +38.5% | +38.5% | 21 → 80 | 4/4 |
| 1 | 36 | 91 → 132 | +45.1% | +45.1% | 16 → 94 | 4/4 |
| 2 | 1 | 86 → 90 | +4.7% | -1.1% | 13 → 13 | 0/4 |
| 2 | 3 | 86 → 95 | +10.5% | +4.4% | 24 → 29 | 1/4 |
| 2 | 6 | 86 → 103 | +19.8% | +13.2% | 24 → 53 | 4/4 |
| 2 | 9 | 86 → 103 | +19.8% | +13.2% | 34 → 42 | 2/4 |
| 2 | 12 | 86 → 110 | +27.9% | +20.9% | 31 → 57 | 4/4 |
| 2 | 18 | 86 → 103 | +19.8% | +13.2% | 31 → 75 | 4/4 |
| 2 | 24 | 86 → 103 | +19.8% | +13.2% | 21 → 72 | 3/4 |
| 2 | 36 | 86 → 105 | +22.1% | +15.4% | 16 → 66 | 4/4 |
| 3 | 1 | 73 → 68 | -6.8% | -25.3% | 13 → 13 | 0/4 |
| 3 | 3 | 73 → 72 | -1.4% | -20.9% | 24 → 30 | 1/4 |
| 3 | 6 | 73 → 78 | +6.8% | -14.3% | 24 → 51 | 2/4 |
| 3 | 9 | 73 → 77 | +5.5% | -15.4% | 34 → 47 | 0/4 |
| 3 | 12 | 73 → 73 | +0.0% | -19.8% | 31 → 66 | 2/4 |
| 3 | 18 | 73 → 65 | -11.0% | -28.6% | 31 → 48 | 1/4 |
| 3 | 24 | 73 → 73 | +0.0% | -19.8% | 21 → 54 | 1/4 |
| 3 | 36 | 73 → 72 | -1.4% | -20.9% | 16 → 47 | 1/4 |

## Selected-regime dolphin population check

At H1/G36, doubling the pod by placing one extra dolphin at each original slot increases mixed group food from132 to229, while the D24-only control rises from91 to183. Adding gannets therefore still improves dolphin group food by25.1%, with positive changes in all four schools. Pooled bird catches change16→80 with D24, compared with16→94 with D12; birds gain in three schools and lose in one. The bird mean benefit remains positive.

Mixed food per dolphin is **2.385 with D24 versus2.750 with D12**, lower in every school. Per-dolphin partner gain is0.479 versus0.854 fish per36T; the paired difference is−0.375, with exploratory pointwise95% interval[−0.8125,−0.0208]. Thus more group food does not imply greater individual return. These are the same four known schools, one discovery-selected regime and one coarse timestep. The check does not identify an optimal pod size or isolate competition as the cause. All six endpoint means, sample SDs, intervals and school signs are exported by the notebook.

## Current setup and evidence

[Local setup](LOCAL_ANALYSIS_SETUP.md) documents the default saved-data route. `FINAL_NOTEBOOK_PROFILE.json` binds the accepted portable 192 snapshot; `PACKAGE_INPUTS.json` pins the reviewed 467 analysis/model-source inputs. The snapshot contains all 192 raw seals, 6 engineering cases and 2,127 original source/input identities in relative content-addressed objects. It is a full inspection/reproduction bundle, not new simulation output generated by the notebook.

The current paper is [completed_h2_2026-11-11](../paper_profiles/completed_h2_2026-11-11/README.md). Old through36/D24 profiles and all prior protected inputs remain unchanged. Departure diagnostics cover only 48 older bird-bearing G1/3/6 encounters; the older grid check uses its own 8 schools. Detailed historical discussion is preserved in [the archived overview](../archive/docs/discovery_D24_2026-11-10/STUDY_OVERVIEW.md).

## Optional native model route

The [certified primary H1/G36 replay](PRIMARY_MODEL_LOCAL_SETUP_2026-11-11.md) has accepted checks for both historical and source-built binaries: six fixed-world cases on both grids at 4T and 36T. A separate instrumented, relocated notebook check exercised the historical 4T route. These are software checks, add no independent schools and do not claim a fresh replay of all 192 feeding encounters. Native execution remains off by default; the tested native scope is Linux x86-64 CPython 3.12. Historical H1/G9/H2/G12 examples and the eight-school H2/G3 runner remain separately documented as historical examples.

The inherited C++ fish engine is from [yangyushi/FishSim](https://github.com/yangyushi/FishSim); this project adds predator controllers, experimental protocols and analysis. No new model steps or bootstrap draws are taken by default reproduction. Linux/Python 3.12 actual analysis and space-path relocation passed; untested platforms are not certified.
