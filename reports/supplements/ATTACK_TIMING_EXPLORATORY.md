# Exploratory attack timing in the completed primary study

This supplement reanalyses the **already published H1/G36 primary simulations**: sixteen schools, two randomness labels within each school, matched species-alone controls and both encounter grids. It adds no model runs or independent schools. The timing analysis was specified after the primary feeding results were known and is exploratory, with one fixed 2T window. T denotes uncalibrated model time. The current paper, its prespecified mutual-feeding result, the main notebook and four figures are unchanged.

## What “recent” means

A dolphin launch is classified as recent only when that same dolphin had already received a recorded local detection of a realized bird water entry, the entry occurred no later than the launch, and the entry-to-launch lag is at most 2T. Delivery and window comparisons use the recorded clocks exactly, without a look-ahead allowance. These detections are retrospective instrumentation, **not inputs to the dolphin controller**.

We classify every recorded dolphin launch in all 64 mixed labelled encounters and reconcile it with eligible oral contacts, captures, resolved attempts without oral contact and still-unresolved final attacks. Contacts and captures are divided by **all launches** in each class, including explicitly counted right-censored attempts at the actual encounter end. These are observed all-launch rates, not completed-bout success probabilities or censor-adjusted efficiency estimates.

## Recent launches and observed capture rates

| Encounter grid | Mean recent-launch fraction | Schools for fraction | Paired recent − not-recent captures per launch | Schools with both-label class rates |
|---|---:|---:|---:|---:|
| coarse | 87.59% | 16 | -0.00533 | 13 |
| fine | 90.28% | 16 | -0.03848 | 12 |

The two labels are averaged within each school before schools receive equal weight. A rate with a zero launch denominator is undefined. If either label is undefined, the corresponding school rate remains undefined; no label is dropped or replaced by zero. Every school row is retained, with explicit defined-label and defined-school counts. The paired rate differences above use thirteen coarse-grid and twelve fine-grid schools. **Subtracting marginal recent and not-recent means would give a different quantity**, because those means can use different sets of schools.

The paired point estimates are negative on both grids. They describe observed captures per launch and do not measure an isolated timing effect. Interpretation is limited by sparse not-recent launches, unequal follow-up, censoring, prey geometry and encounter phase. The complete output retains the contact-rate comparisons as well as captures; it does not select a favourable metric or grid.

## All eight school-level associations

The predictor is the school’s two-label mean fraction of recent launches. The responses are matched partner capture gains per individual over the planned 36T encounter, using the same school, label and grid controls: twelve dolphins or thirty-six gannets. Pearson correlations and Spearman correlations with averaged tied ranks are both retained.

| Grid | Partner-gain response | Pearson r | Spearman ρ | Complete school pairs |
|---|---|---:|---:|---:|
| coarse | Dolphin | +0.1190 | -0.0811 | 16 |
| coarse | Gannet | +0.5210 | +0.4765 | 16 |
| fine | Dolphin | -0.1190 | -0.2212 | 16 |
| fine | Gannet | +0.4508 | +0.3606 | 16 |

Dolphin associations are weak and vary in sign; gannet associations are positive on both grids. These are descriptive associations without confidence intervals, p-values, permutation tests, lag scans or a new success criterion. Geometry, prey accessibility, bird activity and encounter phase can influence both the predictor and feeding gains. The analysis does **not establish attack synchronisation, deliberate coordination or a causal timing mechanism**. The original primary inference is unchanged.

## Inspect or recompute the saved summaries

[Exact accepted timing output](../../data/primary_timing_2026-11-11/timing_diagnostics.json) · [Pure stdlib metrics module](../../data/primary_timing_2026-11-11/timing.py) · [Published primary raw-data snapshot](../../data/primary_validation192_2026-11-11/SNAPSHOT.json). The JSON retains all 64 worlds, 32 school-grid rows, 18 metric summaries, eight coefficients, class denominators, nonoral and censored counts, and every undefined value. These are FishSim-generated simulations, not measurements of people or wild animals.

From the repository root, this stdlib-only example recomputes the two fine-grid gannet correlations from the saved school fractions. It starts no model and needs no private permissions or additional packages:

```python
import json, runpy
from fractions import Fraction
from pathlib import Path
base = Path("data/primary_timing_2026-11-11")
correlation = runpy.run_path(str(base / "timing.py"))["correlation"]
rows = json.loads((base / "timing_diagnostics.json").read_text())["school_points"]
rows = [r for r in rows if r["grid"] == "fine"]
metric = lambda r, k: None if r["metrics"][k] is None else Fraction(r["metrics"][k]["exact"])
pairs = [(metric(r, "recent_launch_fraction"), metric(r, "G_partner_gain")) for r in rows]
pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
for method in ("Pearson", "Spearman"):
    print(correlation([x for x, y in pairs], [y for x, y in pairs], method))
```

Expected coefficients are approximately +0.4507774 and +0.3606199, each with n=16. This example checks saved summary arithmetic; it does not reconstruct the raw event classification or replay physical dynamics.

## Evidence fingerprints

The output was independently reconstructed from the accepted primary controls and all 64 mixed raw event/bird/opportunity log sets. Every class count, school metric and association matched; the largest floating-point discrepancy was 5.55×10⁻¹⁷. Full physical, private-stream and metadata acceptance remains the original primary evidence. Only scientific scalar output and the pure metrics code are included here; internal permissions, operator records and audit bodies are excluded.

| Evidence | SHA256 |
|---|---|
| Exact timing JSON | `223165c2d7b5e37886a27517dda346ec0347c5971e94be75038a0fc0b45ddecf` |
| Pure metrics source | `56e1785c7f29ae9c9f2bb083314092b487f790d0dc20b019eb2678a2fda6f91e` |
| Published primary snapshot | `1ab5c57ff5d6077f9239254c7f12b06249b1c23b34d5c5e37c695dd299864cd6` |
| Primary export receipt | `c88ba37b1506416d12a87de9b7fee56264ee793cf663520cacee0cab80cd25ab` |
| Independent raw/numeric timing review | `e9ada868e826662630dab947a6803dd0acddf103eee485bf7f4393f12bb384b7` |
| Accepted timing result review | `a8e8f22ab30bbd066e234c85c259d11b66e2679f085ad8b043ceed2e2918ac32` |
