# Repository guide

For ordinary use, start with [main.ipynb](../main.ipynb), the
[3D viewer](VISUALISATION.md) and the [current paper](../reports/current/).
The root contains historical names as well as current entry points because
the notebook verifies 9,335 exact input paths and hashes. A file that looks
old is not necessarily disposable.

| Area | Purpose |
| --- | --- |
| `main.ipynb` | Current paper analysis; native execution disabled by default |
| `tools/watch_replays.py` | Local saved-run 3D viewer |
| `paper_profiles/current_through36_2026-11-10/` | Current analysis inputs, figures and six output tables |
| `reports/current/` | Current manuscript and figures |
| `run_v6_example.py`, `regime_runtime*.py` | Optional bounded parameter-map model examples |
| `run_current_model.py`, `current_runtime*.py` | Separate coarse/fine replication runner |
| `frozen_model/`, `study_sources/`, `current_model_inputs/` | Preserved source, native binaries and model inputs |
| `data/` | Saved feeding encounters, trajectories and event records |
| `validation/`, `runtime_validation/` | Analysis checks and bounded native/build provenance |
| `snapshots/`, `reports/snapshots/` | Earlier evidence and report versions |
| `archive/` | Older generated exports and historical delivery receipt |

The full response map, denominators, experimental conditions, interpretation
and platform limits are in the [scientific overview](STUDY_OVERVIEW.md).
Earlier alternative-policy comparisons remain historical; the current
parameter map uses one fixed exposed-prey dolphin rule.

## Cleanup performed

- The README is now a concise entry page with footage, a viewer command and
  notebook/report links. The previous complete scientific text is preserved
  in `docs/STUDY_OVERVIEW.md`.
- 112 generated figure/table/engineering-output files are preserved under
  `archive/legacy_outputs_2026-11-09/`; the older delivery receipt is archived
  separately. [Relocation hashes](../archive/relocations_2026-11-09.json)
  identify every original path and unchanged byte sequence.
- Root `outputs/` is ignored for future regenerated exports. Current-paper
  outputs remain in their versioned profile; regenerated figures, logs and
  caches there are ignored while the six tracked CSVs stay tracked. Generated evidence and vendor
  code are marked for GitHub’s diff/language classification.
- Frozen data, runtime binaries, model rules, manifests and third-party
  licenses have not been removed or rewritten.

Some old receipts still contain their original output paths. They describe
historical execution; the archive map gives the retained files’ new paths.
Running an older notebook regenerates its root `outputs/` folders.

Moving the remaining pinned root modules or manifests requires a versioned
layout migration and renewed reproduction checks. Deleting them would break
the current analysis and historical reproduction paths.

See [NOTEBOOK_MAINTENANCE.md](../NOTEBOOK_MAINTENANCE.md) before rebuilding
the active notebook, and [PROVENANCE.md](../PROVENANCE.md) for source notices.

The full current inventory has 212 feeding execution records; its discovery map has 140 outcomes on four known schools. `upper_count_evidence_v7.py --diagnostics` separately reconstructs raw events, seals, starts, phases, r90 and the fixed whole-school bootstrap without model execution. The compact main notebook generates no new bootstrap draws. The3D catalogue remains the validated 108-encounter through 18 subset.
