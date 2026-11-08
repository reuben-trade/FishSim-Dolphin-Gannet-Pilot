# FishSim: local research notebook

Open **FishSim_Professor_Notebook.ipynb** and choose **Run → Run All Cells**. The default run verifies 48 sealed feeding encounters and three separate timing engineering checks, rebuilds all four figures in the 9 November report snapshot, and exports twelve CSV tables. It does not execute the fish simulator. The saved notebook already contains the executed outputs for review.

The active snapshot preserves the earlier 24 encounters and adds 24 D/G/DG encounters across eight new independent schools. Each new encounter supplies separately sealed 36T primary and 72T secondary results; the horizons are not independent samples. Earlier two-school evidence is displayed separately and is not pooled into eight-school estimates. The finer-timestep follow-up is still running and excluded.

At the primary horizon, mean dolphin change is+1 capture per school with a 97.5% marginal interval−2.375 to+5; gannets gain+5.125 with interval 2.75 to 7. The dolphin benefit is unresolved. These small-sample model results do not establish a general mutual feeding advantage.

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

The supplied historical binary requires **CPython 3.12, Linux x 86-64, glibc 2.43 or newer, compatible C++ runtime and OpenMP**. It is not a portable macOS/Windows binary and will fail on many older Linux distributions. Read [NATIVE_SETUP.md](NATIVE_SETUP.md) before enabling model execution. Its explicit compatibility check prevents an unsupported binary from being silently substituted. The complete C++ source and real build recipe are included, but a rebuild is a new binary requiring separate validation.

## Scientific interpretation

- Twelve dolphins use the same herd–strike cycle with and without three gannets. A launch requires 2T of continuous proximity to currently observed fish within radius 4.5, followed by a physically feasible strike. This pressure clock does **not** certify school compaction or synchronized pod cooperation.
- The exposed policy ranks feasible fish by low observed neighbour count within radius 2; dense fish remain eligible. It does not explicitly wait for a gannet dive or for post-dive scatter.
- Gannets observe underwater fish globally within the permitted depth, form density clusters, choose a cluster with probability proportional to its accessible population, and target a locally dense part of that cluster.
- Capture probability 0.7 is conditional on a resolved physical oral contact. It is not a 70% success probability per launch or dive. These runs were not calibrated to the field study's dive-success observations; the field categories should not be interpreted as repeated attempts on the same fish.
- Space and model time are uncalibrated. The numerical timestep is 0.00125T; the 36T horizon is not a measured real-world encounter duration. These are fixed-model pilot results without a numerical convergence claim, energy budget, or long-term evolutionary learning. Matching G-only controls show joint gains in two of four stochastic comparisons, from two independent schools; gannet benefits are uneven. This is not evidence for a general reciprocal advantage.
- Fresh replication has two independent starting schools, with two capture streams each. Development was used to select the exposed policy. Keep its outcomes separate from the fresh replication when judging evidence.

## Evidence snapshots and preservation

The active notebook imports `notebook_support_v3.py` and uses `DATASET_2026-11-09_0231.json` and `INPUT_MANIFEST_2026-11-09_0231.json`. It verifies 48 completed encounters,48 exact horizon records from the new 24 encounters, and both previous input manifests. Original case files and earlier source/reference sets remain byte-identical.

The original 16-case inventory/manifest and the later 24-case inventory/manifest remain available. Their saved notebooks and validation receipts are preserved under `snapshots/`. The v 3 figure source is `paper_figure_source_v3.py`, with matching `reference_figures_v3/`. Current figures are written to `outputs/eight_school_figures/`; four new-cohort tables go to `outputs/eight_school_tables/`, alongside eight separately reconstructed earlier tables.

`SOURCE_CLOSURE_2026-11-09_0231.json` maps the new cohort's historical source references to exact bundled files. `REPORT_SNAPSHOT_2026-11-09_0231.json` and `reports/snapshots/2026-11-09_0231/` retain its report text, compiledPDF and source. The report at `reports/current/` is the current presentation alias. Source and report snapshots are versioned rather than rewritten.

The optional `run_model.py` and historical runtime remain unchanged. That optional path runs the documented original 36T D/DG pair or original eight-case replication, not this new eight-school 72T cohort. Reconstructing the current report requires no native simulator. `snapshot_tools.py` is a maintainer utility for additive inventories; all `create_notebook*` scripts are authoring utilities rather than professor setup steps.

## Supporting timing evidence

[Timing engineering records](supporting_evidence/timing/README.md) retain three sealed 4T,8T and 36T checks, their protocols and independent audits. They are verified separately during Run All and excluded from the 24case feeding inventory and pooled analysis. The 36T check was selected after baseline screening; it produced one partial hold, zero requested 1T releases and unchanged catches. It is engineering validation, not independent confirmation of a feeding benefit.

## Validation performed

All 20 default cells were executed in a fresh process and clean namespace. They verify the 48 feeding cases and 48 new sealed horizon records, check exact within-school fish/actor/private-stream starts, reconstruct oral-event captures, recompute the frozen 10,000-draw school-vector bootstrap, export 12 tables, and reproduce all four current figure pixels on the tested environment. Three engineering checks remain outside feeding statistics. No native simulator is imported by default analysis.

The relocated-folder check uses a path containing spaces and removes PYTHONPATH. Other operating systems and font versions can produce rendering differences; macOS/Windows execution has not been tested here. The unchanged optional runner's earlier 0.5T D/DG smoke passed 800 native steps; it is too short to test feeding.

Receipts: `validation/eight_school_notebook_2026-11-09_0231.json`, its relocated-folder companion, and the preserved earlier validation files.
