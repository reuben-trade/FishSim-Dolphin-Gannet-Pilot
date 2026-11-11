# H2/G12 validation progress: first complete paired 48-case block

This descriptive snapshot covers four schools, with two randomness labels nested within each school, three matched presence arms and both encounter grids. Each group sum covers eight labelled worlds. It is a subset of the planned 192-case study; all cases continue regardless of signs. No confidence intervals or automated success/failure decision are reported.

The completed H1/G36 primary result and its 97.5% criterion are unchanged. This H2/G12 follow-up reuses the same sixteen-school cohort; these first four schools do not add independent schools to the primary. Both herding duration and bird count change between settings, so neither factor is isolated.

## All six group returns

| Grid | Arm | Dolphin captures | Gannet captures | Fish per dolphin over 36T | Fish per gannet over 36T |
|---|---|---:|---:|---:|---:|
| coarse | D | 165 | 0 | 1.71875 | — (no gannets) |
| coarse | G | 0 | 63 | — (no dolphins) | 0.65625 |
| coarse | DG | 180 | 154 | 1.875 | 1.604167 |
| fine | D | 175 | 0 | 1.822917 | — (no gannets) |
| fine | G | 0 | 62 | — (no dolphins) | 0.645833 |
| fine | DG | 182 | 117 | 1.895833 | 1.21875 |

## Matched partner gains

| Grid | Species | Alone → mixed captures | Ratio-of-totals change | Mean gain per individual over 36T | School gains / ties / losses | Joint-positive school means |
|---|---|---:|---:|---:|---:|---:|
| coarse | D | 165 → 180 | 9.090909% | 0.15625 | 2 / 2 / 0 | 2/4 |
| coarse | G | 63 → 154 | 144.444444% | 0.947917 | 4 / 0 / 0 | 2/4 |
| fine | D | 175 → 182 | 4% | 0.072917 | 2 / 0 / 2 | 1/4 |
| fine | G | 62 → 117 | 88.709677% | 0.572917 | 3 / 0 / 1 | 1/4 |

School signs refer to two-label averaged effects, not to all individual runs. Percentages are changes in matched aggregate totals, not means of school percentages. Both species have twelve individuals in H2/G12. Food uses the nominal 36T denominator, including valid absorbing prey depletion.

## All four school means on both grids

| Grid | School | Dolphin gain per individual over 36T | Gannet gain per individual over 36T |
|---|---:|---:|---:|
| coarse | 39065501 | 0 | 1.416667 |
| coarse | 39065502 | 0.083333 | 0.958333 |
| coarse | 39065503 | 0.541667 | 0.333333 |
| coarse | 39065504 | 0 | 1.083333 |
| fine | 39065501 | -0.125 | 0.708333 |
| fine | 39065502 | 0.125 | -0.041667 |
| fine | 39065503 | 0.5 | 0.541667 |
| fine | 39065504 | -0.208333 | 1.083333 |

These are early descriptive results, not the final sixteen-school secondary estimates or the additional four-endpoint programme analysis. They do not establish numerical convergence. The current paper, main notebook and Doc are unchanged.

## Data and audit method

[All 48 simulation case scalars](../../data/lower_count_progress48_2026-11-11/lower_count_prefix48_cases.csv) · [Compact results provenance](../../data/lower_count_progress48_2026-11-11/RESULTS_PROVENANCE.json). These are user-generated FishSim model outputs, not observations of people or wild animals. The CSV uses the same simulation metadata/count fields as the already published primary-study table. It is a compact scalar snapshot, not a full raw-trajectory archive or an H2 native-replay package.

**The original audit failure remains recorded as a failure.** The initial unmodified frozen auditor (`6c101893…`) failed its timestamp-prefix comparison; the preserved failure witness has SHA256 `3d6b02bdc605dc9fdd8cccb68d226d2b9dc395828f1f4af726abb55e0093d38b`. All 48 raw/physical phase checks passed. Across six smoke/full pairs, the initial states, trajectory arrays, tie streams and all earlier log records matched exactly. The only additions were two D06 launch records (transition and phase) and one cycle-launch record from continuation beyond the common 4T sample, with no oral/removal difference. Localization to the first continuation step is a source/saved-state inference because no committing-step counter was stored.

A separately source-reviewed boundary adapter (`32bc044c…`) subsequently passed a composite review using the unchanged base raw/physical checks and the exact documented boundary treatment. This is **not an unmodified-auditor CLI pass**. Independent integer/Fraction arithmetic verified every reported group return and school mean. No model or frozen study source, raw data or clock tolerance was changed, and no simulation was retried. The compact provenance file records the method and evidence fingerprints; internal execution permissions, operator records and source archives are not part of this public payload.
