# Original shared-policy regime map: corrected recording attempt

The stopped first attempt is preserved in full. It used103,362 native steps,
including three smokes and three completed anchors plus one partial anchor.
The actual trajectories/controller states/events/private streams replayed exactly;
only two complementary sampled-time summary exports used observed instead of
nominal duration. This separate attempt changes those two exports only, keeps
the exact comparator, and reruns every smoke and anchor from fresh outputs.
The new cap is1,737,600 steps and the combined ceiling is1,840,962. Previous
approvals and raw executions are not reused.

This study preserves the exposed-prey herd–strike pilot and maps two declared
parameters: continuous local herding minimum H = 1, 2 or 3T, and 0, 1, 3 or 6
gannets with the same twelve dolphins. G-only controls at each positive bird
count measure the reciprocal effect. All four previously observed school
geometries use capture-stream label 61001, dt=0.00125 and a 36T encounter.
There are 60 condition-school cells and four independent school units.

Only the explicit H threshold and nested bird roster change. The original
fish binary, local threat response, exposed-prey ranking, dense-patch bird
controller, physical capabilities and q=0.7 eligible-contact rule remain fixed.
G0 is used for one bird; G0–G2 for three. Six birds add independent stable IDs
G3–G5 at the same three launch locations, using the original readiness and
private-stream formulas. This changes local multiplicity in a point-body model
without bird collisions or avoidance; one versus three also changes coverage.

The eight original H2/G0-or3 cells must reproduce the archived full trajectories,
scientific controller memory, events, food accounts and private streams before
the other 52 full cells start. The four D-only anchors finish before mixed
anchors. Remaining D-only controls finish before remaining mixed cells. Replayed
anchors remain the original evidence and do not add independent samples.

Preparation is complete: 29 focused tests, all60 pure preparations, and all60
actual native zero-step initializations passed. The actual initialization check
forbids stepping and reproduces all eight archived starting receipts and fish
arrays. No smoke or full encounter has run. `frozen_sources.json` binds 422
source/input/evidence files, the pure check and actual initialization check.

The three prespecified 4T smokes are school39061001 H1/D-only, H3/D+6G and
G-only/one bird. They total at most9600 native steps. Full execution adds at
most1,728,000 steps, with a combined cap1,737,600. Use at most three workers,
one numerical thread per worker. No automatic retries, replacement schools,
post-outcome tuning or omitted negative cells are permitted.

Both execution modes require a separate root-review receipt matching the exact
protocol and frozen-source SHA256 values. `SMOKE_RUN_APPROVED.json` must declare
`approved: true`, `stage: "smoke"`, `protocol_sha256` and
`frozen_sources_sha256`. The full receipt uses `FULL_RUN_APPROVED.json` and
`stage: "full"`; it is valid only after all three smokes and their physical
review pass. Neither receipt exists in this candidate.

Plan and software checks from the repository root:

```bash
.venv/bin/python -m pytest -q research/pilot_regime_sweep_2026-11-09_v2/test_regime.py
.venv/bin/python research/pilot_regime_sweep_2026-11-09_v2/run.py --plan --output research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1
```

After the corresponding root approval, the execution commands are:

```bash
.venv/bin/python research/pilot_regime_sweep_2026-11-09_v2/run.py --smoke --workers 3 --output research/pilot_regime_sweep_2026-11-09_v2/results/smoke_4T_v1
.venv/bin/python research/pilot_regime_sweep_2026-11-09_v2/review_actual.py --output research/pilot_regime_sweep_2026-11-09_v2/results/smoke_4T_v1
.venv/bin/python research/pilot_regime_sweep_2026-11-09_v2/run.py --execute --workers 3 --output research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1
.venv/bin/python research/pilot_regime_sweep_2026-11-09_v2/review_actual.py --output research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1
.venv/bin/python research/pilot_regime_sweep_2026-11-09_v2/analyze.py --input research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1
```

The primary effect compares mixed dolphins against the same-H D-only control.
A separate comparison uses the best-tested D-only H across this discovery bank,
with smallest-H tie breaking. The whole-school bootstrap reselects that best H
within each draw. The observed H is recorded before future held-out validation.
Gannet returns use per-bird rates against count-matched G-only controls. All
maps and raw school contrasts retain positive, zero and negative outcomes.

These four schools have already been observed. The intervals are exploratory
pointwise estimates with four school vectors; shared controls do not multiply
replication. Earlier fine-grid sensitivity remains unresolved. This study does
not establish a global optimum, biological cooperation or numerical convergence.
Original reports, notebooks and published artifacts are unchanged.
