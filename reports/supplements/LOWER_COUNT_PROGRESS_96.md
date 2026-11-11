# H2/G12 validation progress: cumulative 96 of 192 cases

This descriptive snapshot covers the first eight of the same sixteen validation schools, with two randomness labels nested within each school, matched dolphin-only, bird-only and mixed groups, and both encounter grids. Each group sum covers sixteen labelled worlds. All 192 follow-up cases continue regardless of signs. No interim confidence intervals or final success/failure decision are reported.

On the fine grid, dolphin captures are **329→370 (+12.5%)** and gannet captures **124→275 (+121.8%)**. After averaging the two labels within each school, dolphins have five gains, one tie and two losses; gannets have seven gains and one loss. Both species gain in four of eight school means. These signs do not mean every labelled run benefits.

The completed H1/G36 primary result and its 97.5% criterion are unchanged. This H2/G12 follow-up shares the primary study’s sixteen-school cohort; it does not add independent schools to that result. Both minimum herding duration and bird count change between the settings, so neither factor is isolated. Here H2 requires 2T of continuous local prey proximity before an eligible dolphin strike; both species have twelve individuals, with the same conditional capture probability q=0.7.

## All six group returns

| Grid | Arm | Dolphin captures | Gannet captures | Fish per dolphin over 36T | Fish per gannet over 36T |
|---|---|---:|---:|---:|---:|
| coarse | D | 335 | 0 | 1.744792 | — (no gannets) |
| coarse | G | 0 | 133 | — (no dolphins) | 0.692708 |
| coarse | DG | 368 | 323 | 1.916667 | 1.682292 |
| fine | D | 329 | 0 | 1.713542 | — (no gannets) |
| fine | G | 0 | 124 | — (no dolphins) | 0.645833 |
| fine | DG | 370 | 275 | 1.927083 | 1.432292 |

## Matched partner gains

| Grid | Species | Alone → mixed captures | Ratio-of-totals change | Mean gain per individual over 36T | School gains / ties / losses | Joint-positive school means |
|---|---|---:|---:|---:|---:|---:|
| coarse | D | 335 → 368 | 9.850746% | 0.171875 | 4 / 3 / 1 | 4/8 |
| coarse | G | 133 → 323 | 142.857143% | 0.989583 | 8 / 0 / 0 | 4/8 |
| fine | D | 329 → 370 | 12.462006% | 0.213542 | 5 / 1 / 2 | 4/8 |
| fine | G | 124 → 275 | 121.774194% | 0.786458 | 7 / 0 / 1 | 4/8 |

School means average the two paired label differences before giving the eight schools equal weight. Percentages are changes in matched aggregate totals, not averages of school percentages. Food uses the planned 36T encounter denominator, including valid absorbing prey depletion. The coarse and fine timesteps are 0.00125T and 0.000625T.

## All eight school means on both grids

| Grid | School | Dolphin gain per individual over 36T | Gannet gain per individual over 36T |
|---|---:|---:|---:|
| coarse | 39065501 | 0 | 1.416667 |
| coarse | 39065502 | 0.083333 | 0.958333 |
| coarse | 39065503 | 0.541667 | 0.333333 |
| coarse | 39065504 | 0 | 1.083333 |
| coarse | 39065505 | 0 | 0.875 |
| coarse | 39065506 | -0.125 | 1.666667 |
| coarse | 39065507 | 0.333333 | 1.125 |
| coarse | 39065508 | 0.541667 | 0.458333 |
| fine | 39065501 | -0.125 | 0.708333 |
| fine | 39065502 | 0.125 | -0.041667 |
| fine | 39065503 | 0.5 | 0.541667 |
| fine | 39065504 | -0.208333 | 1.083333 |
| fine | 39065505 | 0.166667 | 0.708333 |
| fine | 39065506 | 0.791667 | 1.041667 |
| fine | 39065507 | 0.458333 | 1.5 |
| fine | 39065508 | 0 | 0.75 |

These are cumulative descriptive results, not the final sixteen-school secondary estimates or the additional four-endpoint programme analysis. They do not establish numerical convergence. The [earlier 48-case snapshot](LOWER_COUNT_PROGRESS_48.md) remains unchanged. The current paper, main notebook and Doc are unchanged.

## Data and audit method

[All 96 simulation case scalars](../../data/lower_count_progress96_2026-11-11/lower_count_prefix96_cases.csv) · [Compact results provenance](../../data/lower_count_progress96_2026-11-11/RESULTS_PROVENANCE.json) · [Follow-up plan](LOWER_COUNT_FOLLOWUP_PLAN.md). These are user-generated FishSim model outputs, not observations of people or wild animals. The CSV retains every matched case, both labels and both grids, using the same scalar fields as the already published primary-study table. This compact snapshot is not a full raw-trajectory archive or an H2 native-replay package.

**Block 1’s original audit failure remains a failure.** Its initial unmodified frozen auditor failed the timestamp-prefix comparison; failure-witness SHA256: `3d6b02bdc605dc9fdd8cccb68d226d2b9dc395828f1f4af726abb55e0093d38b`. All 48 block-1 raw/physical phase checks passed. Across six smoke/full pairs, the initial states, trajectory arrays, tie streams and earlier log records matched exactly. The only additions were two D06 launch records (transition and phase) and one cycle-launch record from continuation beyond the common 4T sample, with no oral/removal difference. Localization to the first continuation step is a source/saved-state inference because no committing-step counter was stored. A separately source-reviewed boundary adapter passed the accepted block-1 composite review; this is **not an unmodified-auditor CLI pass**.

**Block 2 passed the unchanged original frozen auditor** for its 48 cases. The cumulative snapshot combines that pass with the accepted block-1 composite review, retaining their distinct methods. Independent integer/Fraction arithmetic verified all six group returns, four partner contrasts and sixteen school means against the accepted 96 scalar rows. No model or frozen study source, raw data or clock tolerance was changed, and no simulation was retried. Hash-only provenance records the accepted evidence and reporting method; internal audit bodies, operator records and source archives are excluded.
