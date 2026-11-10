# Repository guide

Start with [main.ipynb](../main.ipynb), the [current paper](../reports/current/) and the [local setup](LOCAL_ANALYSIS_SETUP.md). The current notebook reproduces thirteen canonical tables and four figures from saved evidence; it starts no model and makes no new bootstrap draws.

| Area | Purpose |
| --- | --- |
| `main.ipynb`, `FINAL_NOTEBOOK_PROFILE.json` | Current discovery plus separate complete sixteen-school validation |
| `data/primary_validation192_2026-11-11/` | Accepted portable snapshot: 192 validation encounters and exact source/evidence objects |
| `discovery_profile/` | Preserved discovery analysis: full 24-setting map, selected D24 check and older diagnostic subsets |
| `paper_profiles/final_primary192_2026-11-11/` | Current six-page paper source, four figures and thirteen table exports |
| `reports/current/` | Convenient aliases for the current manuscript and figures |
| `execution_proofs/` | Actual kernel, relocation, scientific review and guarded Doc publication receipts |
| `validation_tools/` | Saved-data acceptance reader and frozen validation plotter |
| `model_examples/primary_192/` | Reviewed full-primary replay source; native release remains separately gated |
| `tools/watch_replays.py` | Saved-run 3D viewer, retaining its validated 108-encounter catalogue |
| `paper_profiles/current_through36_D24_2026-11-10/` | Unchanged previous paper and analysis profile |
| `archive/notebooks/`, `archive/docs/` | Earlier active notebook and documentation |
| `reports/supplements/` | Prospective plans and unchanged descriptive progress snapshots |
| `frozen_model/`, `study_sources/`, `runtime_validation/` | Historical sources, inputs, native binaries and bounded engineering evidence |

The independent validation uses sixteen new schools, two labels averaged within each school, matched presence arms and two encounter grids. These 192 cases are separate from the four-school discovery map and its population follow-up; execution counts are not independent sample sizes. The primary snapshot contains about 1.4 GB of sealed raw/source evidence. Its relative content-addressed objects can be read without the author's paths.

The active package preserves the prior 10,077 protected input paths and adds versioned current evidence. Historical filenames and source pins remain intentional. Do not edit sealed inputs in place: some old recordings share immutable inodes. Generated root `outputs/` directories are ignored. See [NOTEBOOK_MAINTENANCE.md](../NOTEBOOK_MAINTENANCE.md) before changing the active notebook.

The separately reviewed primary replay source is disabled in default analysis and awaits artifact-specific native release certification. Older `run_v6_example.py` examples cover D12/H1/G9 and D12/H2/G12 short runs; they do not reproduce the new H1/G36 ensemble. [PROVENANCE.md](../PROVENANCE.md) retains upstream FishSim attribution and licenses.
