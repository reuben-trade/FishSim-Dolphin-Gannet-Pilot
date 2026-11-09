# FishSim executive summary —10 November 2026

The completed count extension finds **mutual feeding benefits within the model** at several settings, using an unchanged dolphin rule and matched single-species controls. The full map now contains 140 condition-school outcomes and 24 mixed settings on the same four previously observed schools.

At **H=1T/G=36**, dolphins capture 132 fish versus 91 without birds (+45.1%), and gannets 94 versus 16 without dolphins. Both species gain in every school. This is the largest dolphin total observed, but only five fish above the 127 reached at G9 and G18. The comparison does not establish 36 as an optimum.

At **H=2T/G=12**, dolphins 86→110 (+27.9%) and gannets 31→57 (+83.9%), again with both species gaining in all four schools. Dolphins also exceed the best-tested H1 bird-free benchmark 91→110 (+20.9%). A smaller flock therefore supports mutual benefit too, with a different distribution of food.

## Complete response map

All24 settings and signs are retained. Counts are four-school totals. D controls have the same H; G controls have the same bird count. There are 18 positive, two exact-zero and four negative mean dolphin changes; corresponding gannet counts are 20/two/two. Individual predators, reused controls and repeated settings are not independent schools.

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

## What the model does

Dolphins maintain local pressure, wait at least H=1/2/3 model-time units near prey, then choose a physically feasible target with a preference for fewer neighbours. H does not certify a compact school or completed herding. The same rule runs with and without birds, with no bird-count cue, dive-triggered rule or capture bonus.

Gannets identify globally known accessible density groups, sample groups by accessible population and target a dense location. More birds occupy a nested roster at the original three launch sites:24/36 birds place 8/12 at each site. Predators are point-represented and have no body-spacing avoidance.

The 0.7 capture probability applies only at eligible physical oral contact. It is uncalibrated and is not success per strike or dive. The fish move through the inherited FishSim C++ engine, coupled to Python predator controllers; this is not a newly authored all-Python fish simulator.

## Opportunities and food shares

For H1, D-only has 251 dolphin launches,130 eligible contacts and 91 captures. With 36 birds the totals are 284/174/132. These realised changes accompany more contact opportunities with capture probability fixed. School-radius and contact diagnostics are descriptive; they do not isolate a causal scattering mechanism.

Food per bird generally declines as flocks grow, but not monotonically at every adjacent count. H1/G36 gives 0.653 fish per bird over 36T, versus 0.111 in its matched bird-only group. H2/G12 gives 1.188 per bird, versus 0.646 without dolphins. Larger group totals and stronger partner effects do not imply more food per individual. Competition for finite prey is plausible, but it has not been separated from access, disturbance or total predator abundance.

## Limits and separate evidence

The map uses one capture setting and four previously examined schools. Its pointwise 95% intervals are exploratory, unadjusted across 24 settings and not independent confirmation of selected cells. School identity also seeds readiness/private streams; starting geometry and chance are not causally separated. Time and length are uncalibrated;36T is not 36 seconds, and catches do not measure energetic profit, fitness or intentional cooperation.

Original shared-rule pilots gave dolphin gains 17.1% and 16.1% in distinct earlier cohorts. They remain archived. The separate eight-school H2/G3 check changed mean dolphin effects from+1 to 0 fish/school when the timestep was halved, and gannet effects from+5.125 to+2.5. Its fine dolphin mean combines four gains, three losses and one tie. That result neither refines the selected H1/G36/H2/G12 settings nor proves their benefits vanish; their numerical robustness and fresh-school generalisation remain untested.

The departure diagnostic remains the older 48 bird-bearing G1/3/6 encounters, not all 128 bird-bearing runs in this map. It does not establish that continued bird diving is required to maintain dolphin gains.

## Current artifacts and next tests

The six-page paper has four figures and ten references. [main.ipynb](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/main.ipynb) reproduces its figures and six summary tables with ten code cells, zero model steps and no new bootstrap draws. The full raw-data inventory has 212 feeding execution records; replays, horizons and engineering checks add no independent schools. Earlier notebooks/manifests and the through 18 report remain preserved.

The interactive 3D viewer retains its validated 108-encounter through 18 catalogue. New upper-count raw cases are bundled separately. Optional native examples remain the bounded earlier H1/G9 and H2/G12 settings, disabled by default; they do not execute the entire new map.

The D24 comparison remains planned here until all its outcomes are audited, with matched D24-only controls and per-animal returns. Attack synchronisation is a future controlled test, not a demonstrated mechanism or completed experiment.

[Current report](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/reports/current/Feeding_Frenzy_Working_Draft.pdf) · [All current study details](https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot/blob/main/docs/STUDY_OVERVIEW.md)
