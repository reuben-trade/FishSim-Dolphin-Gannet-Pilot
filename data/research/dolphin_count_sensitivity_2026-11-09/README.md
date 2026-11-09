# Dolphin population sensitivity candidate

This is an isolated, native-free preparation for a focused comparison of 24
dolphins with the completed 12-dolphin study. No D24 feeding results exist here.
The native entry points reject every call until the complete upper map, actual
selection, independent reviews, source freezes and fresh phase approvals exist. There is no scientific
selection, execution freeze, initialization approval, smoke approval or full-run
approval in this directory.

The question is whether doubling the dolphins changes the **per-dolphin benefit
from adding gannets**, rather than merely increasing the group's total catch.
For each school and selected H/G setting, define

`benefit(N) = captures(D_N + G)/(N × 36T) − captures(D_N only)/(N × 36T)`.

The primary interaction is `benefit(24) − benefit(12)`. Also retain both benefit
values, the difference in mixed per-dolphin feeding rate, group capture totals,
and each gannet's partner effect. Each population uses its own same-H dolphin-only
control. The corresponding completed D12 and count-matched gannet-only outcomes
are reused by exact source/completion SHA mapping; reused outcomes add no schools.

## Selection and bounded scope

Wait for the **complete** H1/2/3 × G1/3/6/9/12/18/24/36 D12 map and its passed
independent physical/raw/analysis review. Select only from those D12 outcomes:

1. A: the largest pooled mixed dolphin catch across all four schools.
2. B: the largest pooled mixed dolphin catch among settings where **both** species
   have a strictly positive partner effect in **each** of the four schools.

Ties use fewer birds, then lower H. If no B setting qualifies, retain only A;
if A and B coincide, retain one regime with both labels. No D24 result influences
selection. Keep all 24 D12 map cells and every new D24 sign visible. Selection is
exploratory on four previously observed schools, not independent validation.

`select_regimes.py` refuses an incomplete, duplicated or misnormalized 140-row
map. Its CLI requires a passed analysis audit whose SHA binds the input CSV and
writes a **candidate** selection; independent review remains required before it
can become `selected_regimes.json`. That file has intentionally not been created.

H1/G9 and H2/G12 are **software fixtures only**, never scientific defaults.

Use school seeds 39061001, 39061002, 39063501 and 39063502; capture stream 61001;
160 initial fish; dt 0.00125; nominal encounter 36T. Deduplicate shared same-H
D24-only controls. One selected regime needs 8 full cases; two regimes with a
shared H need 12; two regimes with different H need 16. First run the fixed first
school subset, then the remaining three schools, without result-driven additions.
Four-T smokes cover each distinct selected H/G and corresponding D24-only setting
on the first school, at most four cases. Maximum full steps: 460800; maximum smoke
steps: 12800; all-stage ceiling: 473600. Initializations take zero steps.

## Unchanged behavior and explicit assumptions

D00–D11 retain their completed states, controller states, readiness and private
capture streams. D12–D23 add one stable-identity dolphin at each original starting
slot (`Di` uses `D(i modulo 12)`). The original 12-slot footprint remains fixed;
this changes population and local multiplicity without adding spatial coverage.
Every new dolphin gets the same generic controller, speed, sensing, mouth,
conditional contact probability 0.7 and recovery rules. Its private readiness and
capture stream follow the original identity-based seed formulas.

Herding geometry derives from the fish patch and the dolphin's position. There
is no actor-ID role table, cooperative message passing or direct gannet-event
trigger. A native-free equal-input probe checks that all 24 identities propose
the same feasible attack when given equal physical state and observation.

All predators are point bodies with spacing and avoidance disabled. At D24,
two dolphins initially occupy each original slot. This is a deliberately simple
population sensitivity, not a calibrated model of crowding or increased hunting
area. Fish behavior, target choice, launch guards, q, mouth/contact resolution,
private stream arithmetic, sampling cadence and unique-prey accounting remain
unchanged. Model units remain uncalibrated; coarse-grid convergence has not been
established. No success rate has been altered to produce an advantage.

The 15 physical/accounting helpers in `physical_run.py` are AST-identical to the
published frozen high-count runner, and the complete `run_case` body after native
construction is AST-identical. Its pre-construction approval routes use separate
pilot/remainder gates. Controller, gannet, horizon, cadence and physical-auditor
modules are byte-identical. Count-dependent changes are in roster preparation,
case identity, metadata and analysis normalization. Scheduling, zero-step, review
and supervisor CLIs are prepared, with native gates closed by the absent selection.

## Analysis and remaining gates

`analyze.paired_statistics` computes contrasts from integer counts before division,
so mathematical zeros remain exactly zero without a sign tolerance. It resamples the four **whole-school vectors** jointly
across both dolphin populations, selected regimes and species. It reports sample
SD, exploratory pointwise bootstrap 95% intervals and positive/zero/negative
school counts. Independent n is 4, never 24 dolphins or 96 actor observations.
The 36T feeding denominator remains fixed if the fish are completely depleted;
physical effort stops at observed depletion, with no invented empty-school motion.

Before any native work: complete the upper map, bind reused inputs by SHA, review
and freeze the actual selection and source closure, then issue fresh phase gates.
Every eventual native phase must hold the shared outer execution lease
`/tmp/FishSim_Native_Execution_Lease_2026-11-09.lock` before any legacy study lock,
join every child before release, and run after the upper-count extension. Preserve
all original code, raw outcomes, failed/partial cases and earlier evidence. Use
at most eight worker processes with numerical threads fixed to one. Work/output
belongs under `/tmp/FishSim_Dolphin_Count_Sensitivity_2026-11-09`, maintaining at
least 1 GiB root and 2 GiB output reserves. Do not duplicate existing raw banks.

Run the native-free checks from the research repository:

```bash
.venv/bin/python -m pytest -q research/dolphin_count_sensitivity_2026-11-09/test_study.py
.venv/bin/python research/dolphin_count_sensitivity_2026-11-09/preflight.py
```

## Prepared execution contract, still gated

`run.py --plan` is native-free and reports no selected phases while selection is
absent. `run.py --smoke`, `--pilot` and `--remainder` each require a distinct fresh
approval. Each phase completes its entire `dolphin_only_controls` process pool,
writes that completion barrier, then creates the mixed pool. No mixed job is
submitted before the new same-H D24-only controls finish. Pools join before the
shared outer lease and historical inner lease are released.

The future selection handoff comprises `selection_candidate.json`, a passed
`INDEPENDENT_SELECTION_REVIEW.json` binding its SHA, and `selected_regimes.json`.
The final selection copies the candidate's `regimes` and `input_bindings`, changes
status to `reviewed_complete_map_selection`, and adds `candidate_selection_sha256`
and `independent_selection_review_sha256`. The candidate CLI also binds the
complete upper map's independent review; every selection is recomputed from all
140 rows at the gate. No fixture can become a selected-regime preflight or freeze.

After that handoff, `preflight.py --selected` writes `PURE_PREFLIGHT.json` and
`freeze.py --stage inputs` can prepare `INPUT_FREEZE.json`. A passed independent
source review binds the input-freeze SHA; a fresh `INITIALIZATION_APPROVED.json`
authorizes exactly the selected number of constructors and zero steps. The
zero-step checker forbids all three school/encounter step entry points and checks
actual fish arrays, including normalized headings, against the completed D12
archive. The execution freeze and passed independent initialization review then
precede any smoke permission.

Each approval is named `INITIALIZATION_APPROVED.json`, `SMOKE_APPROVED.json`,
`PILOT_APPROVED.json` or `REMAINDER_APPROVED.json`; it binds `stage`, `protocol_sha256`,
`freeze_sha256`, `independent_review_sha256`, exact ordered `case_names`, `workers`
(1 for initialization, 8 otherwise), and exact `maximum_native_steps`. Initialization
also binds `maximum_native_constructions`. Source/initialization reviews have
`status: passed` and `freeze_sha256`. Pilot and remainder approvals additionally
bind the physical and independent smoke reviews; remainder also binds physical
and independent pilot reviews. Those independent phase reviews bind
`physical_review_sha256`. These are expected future artifacts, not files produced
by this preparation.

`supervise.py --stage ...` runs the gated native phase, its physical review, and
either an all-settings n1 pilot description or final raw analysis. It preserves
failures, uses no retry, and terminates/joins its own process group before exit.
Final analysis rechecks every new sealed raw log and the exact reused comparator
logs, conserves unique prey removals, reconciles counts/contacts/launches, and emits
all school points, per-animal effects, group totals and bootstrap summaries. Raw
reference banks are reused in place by SHA rather than copied.
