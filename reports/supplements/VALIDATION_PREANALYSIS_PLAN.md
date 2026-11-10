# Validation pre-analysis plan: fixed H1/G36 study

**This is a public configuration archive posted after feeding began, not formal preregistration.** The protocol and analysis rules were fixed before the full validation launch at **16:44:36 Perth /08:44:36 UTC on 10 November 2026**. Public posting occurs later, after some single-species control encounters had completed. No claim is made that this plan was publicly available before data collection.

<!-- PUBLIC_POSTING_LINE -->
First public push confirmed: **10 November 2026,09:39:53 UTC /17:39:53 Perth**, first archive commit `3f2222adaef5301c1a2453b684cf90069431d545`. This is the observed successful-push confirmation time, not a backdated claim of pre-data posting. The machine-readable [posting record](../../prospective_plans/independent_validation_2026-11-10/POSTING_RECORD.json) preserves both times.
<!-- END_PUBLIC_POSTING_LINE -->

The [current paper](../current/Feeding_Frenzy_Working_Draft.pdf) remains the earlier discovery report on four previously examined schools. This archive contains **no validation feeding effects**. The new validation will not be pooled with those discovery schools.

## Fixed configuration and case inventory

- **16 previously un-fed schools**, seeds 39065501–39065516. Eight were already prepared without predators; eight were newly prepared. Encounter states are archived at 20T. The original 20–56T preparation screen determines disposition; 56–92T is diagnostic only. There are no feeding-based replacements or exclusions.
- **Two nested stochastic-world labels**, 71001 and 71002, per school:32 worlds, not32 independent schools. Labels change capture, tie and gannet-target streams; readiness remains fixed by school and identity. Common starts and actors match across treatment arms and encounter grids within each world.
- **Three arms:** 12 dolphins alone; 36 gannets alone; 12 dolphins with 36 gannets. Dolphin hunting behaviour stays the same with and without birds: fixed exposed-prey targeting after minimum herding duration H=1T. Fish 160 and eligible oral-contact capture probability q=0.7 are unchanged.
- **Two encounter grids:** coarse dt 0.00125T and fine dt 0.000625T, each lasting a nominal 36T. There are 96 planned cases per grid and 64 per arm, giving **192 unique case identities**. Coherent early prey depletion retains the nominal 36T food denominator.

[The planned 192-case CSV](../../prospective_plans/independent_validation_2026-11-10/case_inventory.csv) was generated purely from [the exact archived case source](../../prospective_plans/independent_validation_2026-11-10/cases.py), without reading feeding results or constructing/stepping the simulator. It can be [checked locally](../../prospective_plans/independent_validation_2026-11-10/README.md).

Fine dt is the **prespecified primary grid**. Coarse dt is a comparison/sensitivity treatment, never a selectable winner. Both use the same coarse-prepared 20T starts; this tests encounter discretisation conditional on those starts, not end-to-end preparation convergence. H1/G36 was selected from the completed D12 discovery map before these validation outcomes; it is not reselected on validation data.

## Primary estimand and decision

For each species, calculate mixed-minus-matched-single-species capture differences within each school and label. Average both labels **within the school**, divide by 12 dolphins or 36 gannets, then average the 16 school effects. The unit is **fish captured per individual over 36T**, including travel, herding, failures and recovery. Per-time rates divide by 36 separately. Absolute food, partner gains and group totals answer different questions; relative change is undefined if its matched control mean is zero.

The primary analysis uses paired school-mean Student-t intervals: **97.5% two-sided intervals**, df 15, fixed critical value 2.4898797034798923. The predeclared joint-benefit criterion is met only if **both fine-grid species lower bounds exceed zero**, and only after all 192 cases are complete and audited. The two marginal intervals target approximate 95% familywise coverage under their school-independence/t assumptions. The criterion alone does not establish absence of benefit; each estimate and interval must be interpreted.

A fixed **50,000-draw whole-school bootstrap** is sensitivity only: PCG64, seed 8611030, quantiles 0.0125/0.9875, with one common school-vector resample preserving both labels, species and grids. It cannot replace the t method according to which result passes. Coarse effects and paired fine-minus-coarse differences are secondary.

All raw label/school effects, signs, school SD and SE will remain visible. Within-school stochastic-world variance W is the mean squared label-effect difference divided by 2; conditional repeat MCSE is sqrt(W/32). This component is shown separately and is not added again to the total school-level SE. The labels are not pure capture-probability noise.

## Completion and progress rules

The four fixed four-school blocks each contain 48 cases. For each grid, all dolphin-only and bird-only controls complete before mixed cases. **All blocks are mandatory regardless of signs.** Complete audited paired-block progress at 4/8/12 schools may be reported descriptively, with both grids and labels, but with **no interim confidence intervals, primary decision, outcome-based stopping, model tuning or timestep selection**. No missing outcomes are filled with zero and discovery cases are not added to the validation estimate.

Technical failures and preparation dispositions are retained. Partial/unsealed cases stop for review rather than being silently retried or replaced. Completed sealed cases may resume without being stepped again. Any later amendment must have a separate dated record; this frozen archive is preserved.

## Exact records and chronology

The archived [protocol](../../prospective_plans/independent_validation_2026-11-10/protocol.json), [analysis plan](../../prospective_plans/independent_validation_2026-11-10/analysis_plan.json), [root design authority](../../prospective_plans/independent_validation_2026-11-10/ROOT_DESIGN_AUTHORIZATION.json) and [execution-freeze manifest](../../prospective_plans/independent_validation_2026-11-10/frozen_sources.json) retain their exact author bytes. The execution-freeze SHA256 is `253071467e55b4cdbe91f75ba1de3f1bb80d65344e9cba05aadb86bccb08da0b`.

Independent source, actual-start and six 4T engineering gates preceded full feeding. Their records and hashes are listed in [GATE_RECEIPT_HASHES.json](../../prospective_plans/independent_validation_2026-11-10/GATE_RECEIPT_HASHES.json); copied review records retain their original stage and timestamps. Source review was recorded at 08:23:24 UTC, actual-start review at 08:26:56, engineering review at 08:42:16, and feeding approval at 08:44:12, before the reported 08:44:36 launch. The actual-start gate covers 192 native initialisations and zero simulation steps; the six 4T engineering cases total 28,800 steps and are separate from feeding inference.

Original absolute paths are author-environment provenance. This compact archive identifies the frozen configuration, planned identities and gates; it does not duplicate the full 2,127-input source/raw bundle or claim a portable model rerun. Model units, capture calibration and biological generalisation remain limitations even if a statistical criterion is met.
