# FishSim: local research notebook

Open **FishSim_Professor_Notebook.ipynb** and choose **Run → Run All Cells**. The default run verifies 24 sealed feeding encounters and three separate timing engineering checks, rebuilds all four figures in the 9 November report snapshot, and exports eight CSV tables. It does not execute the fish simulator. The saved notebook already contains the executed outputs for review.

The current evidence snapshot contains eight development encounters, eight fresh exposed-policy replication encounters, and eight matching gannet-only/depth encounters, each lasting 36 model-time units. It excludes the earlier C-policy pilot and the later eight-school 72T study. The latter is running separately; no partial results enter this notebook. The two capture streams in each fresh school are repeated stochastic runs of the same starting geometry, not additional independent schools.

## Local setup: analysis and figures

Use Python 3.10 or newer. From a terminal opened in this folder:

**macOS or Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-analysis.txt
python -m jupyterlab
```

**Windows PowerShell** (activation is unnecessary):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-analysis.txt
.\.venv\Scripts\python.exe -m jupyterlab
```

Open the notebook from JupyterLab's file browser. Keep the notebook beside its support files and data folder. The analysis path uses NumPy, Matplotlib and Python's standard library; JupyterLab supplies the interface, and tzdata supplies the Perth timezone on systems without an operating-system timezone database. No pandas, compiler, native FishSim binary or internet connection is required after installation. Installation follows the [official Jupyter instructions](https://jupyter.org/install).

Analysis code is designed to work across operating systems. Validation receipts record the actual tested environment; macOS and Windows execution has not been tested here. Identical figure pixels are checked on the authoring environment. Other font or Matplotlib versions may produce small rendering differences while retaining the same data.

## Optional execution of the actual model

The final notebook section is disabled by default. It calls the unchanged frozen model through `run_model.py` in a new process. `QUICK_RUN = True` executes a 0.5T dolphin-only encounter followed by its 0.5T dolphin–gannet match. This checks integration and is too short to test the 2T feeding cycle. A full matched pair uses 36T per encounter; the complete replication option runs both schools and both capture streams, eight cases. Runtime depends on the computer and can be tens of minutes.

The supplied historical binary requires **CPython 3.12, Linux x86-64, glibc 2.43 or newer, compatible C++ runtime and OpenMP**. It is not a portable macOS/Windows binary and will fail on many older Linux distributions. Read [NATIVE_SETUP.md](NATIVE_SETUP.md) before enabling model execution. Its explicit compatibility check prevents an unsupported binary from being silently substituted. The complete C++ source and real build recipe are included, but a rebuild is a new binary requiring separate validation.

## Scientific interpretation

- Twelve dolphins use the same herd–strike cycle with and without three gannets. A launch requires 2T of continuous proximity to currently observed fish within radius 4.5, followed by a physically feasible strike. This pressure clock does **not** certify school compaction or synchronized pod cooperation.
- The exposed policy ranks feasible fish by low observed neighbour count within radius 2; dense fish remain eligible. It does not explicitly wait for a gannet dive or for post-dive scatter.
- Gannets observe underwater fish globally within the permitted depth, form density clusters, choose a cluster with probability proportional to its accessible population, and target a locally dense part of that cluster.
- Capture probability 0.7 is conditional on a resolved physical oral contact. It is not a 70% success probability per launch or dive. These runs were not calibrated to the field study's dive-success observations; the field categories should not be interpreted as repeated attempts on the same fish.
- Space and model time are uncalibrated. The numerical timestep is 0.00125T; the 36T horizon is not a measured real-world encounter duration. These are fixed-model pilot results without a numerical convergence claim, energy budget, or long-term evolutionary learning. Matching G-only controls show joint gains in two of four stochastic comparisons, from two independent schools; gannet benefits are uneven. This is not evidence for a general reciprocal advantage.
- Fresh replication has two independent starting schools, with two capture streams each. Development was used to select the exposed policy. Keep its outcomes separate from the fresh replication when judging evidence.

## Evidence snapshots and preservation

The active notebook imports `notebook_support_v2.py` and uses `DATASET_2026-11-09.json` plus `INPUT_MANIFEST_2026-11-09.json`. It verifies the original first-draft manifest as well as the new snapshot. All 24 cases retain their original complete file seals. The eight new G-only/depth cases include the unshifted controls needed for the joint-benefit comparison; translated depths are analysed separately.

The original `DATASET.json`, `INPUT_MANIFEST.json`, `notebook_support.py`, `paper_figure_source.py`, `reference_figures/` and 16 original case directories are unchanged. The first executed notebook and its validation receipt are preserved in `snapshots/first_draft_2026-11-08/`. Current figures are rebuilt from `paper_figure_source_current.py` and compared with `reference_figures_current/`. New tables and figures go to `outputs/current_tables/` and `outputs/current_figures/`.

`SOURCE_CLOSURE_2026-11-09.json` maps every source named by the new G-only case manifests to byte-identical bundled files in `frozen_model/`, `data/` or `study_sources/`. `REPORT_SNAPSHOT_2026-11-09.json` records the report text belonging to the current figure snapshot. Historical absolute paths remain provenance; analysis resolves bundled paths directly.

The optional `run_model.py` and frozen runtime are unchanged from the tested first-draft delivery. This optional path still runs the documented original D/DG pair or eight-case fresh replication, not the later depth or 72T study. `snapshot_tools.py` is a maintainer utility for additive, explicitly versioned evidence inventories; it performs no simulation and rejects changed old evidence. `create_notebook.py` and `create_notebook_current.py` are authoring utilities, not steps a professor needs to run.

## Supporting timing evidence

[Timing engineering records](supporting_evidence/timing/README.md) retain three sealed4T,8T and36T checks, their protocols and independent audits. They are verified separately during Run All and excluded from the24case feeding inventory and pooled analysis. The36T check was selected after baseline screening; it produced one partial hold, zero requested1T releases and unchanged catches. It is engineering validation, not independent confirmation of a feeding benefit.

## Validation performed

The default notebook is executed in a fresh Python process and clean namespace. Its receipt records verification of all 24 sealed cases, preservation of the original 16-case manifest, exact G-only/DG initial-state and private-stream matching, eight exported tables, and four figures pixel-identical to the current report references on the tested environment. Default analysis imports no native simulator and takes zero simulation steps. Other platforms or font versions can produce small rendering differences; macOS/Windows execution has not been tested here.

The unchanged optional runner previously passed an actual 0.5T D / 0.5T DG integration pair using the pinned native binary: 800 native steps total, both original audits and seals passed. The short check verifies that execution path, not feeding outcomes. Receipts are `validation/current_notebook_2026-11-09.json` and the preserved `validation/native_smoke.json`.
