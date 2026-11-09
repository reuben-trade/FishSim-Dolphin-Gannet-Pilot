# FishSim: local research notebook

Open **FishSim_Professor_Notebook.ipynb** and choose **Run → Run All Cells**. The default run verifies 72 sealed feeding encounters and three separate timing checks, reconstructs 72 new-study horizon records, regenerates all four current report figures, and exports 14 CSV tables. It imports no native simulator and takes zero simulation steps. Saved outputs are included for review.

The snapshot retains 24 earlier encounters, 24 coarse-grid encounters across eight new schools, and 24 fine-grid encounters on those **same eight schools**. The numerical grids are paired treatments, not sixteen independent schools. Earlier two-school evidence remains separate.

**Main finding:** halving dt changes the mean dolphin partner effect from +1 to 0 captures per school, and the gannet effect from +5.125 to +2.5. Dolphin effect signs agree in 3/8 schools and gannet signs in 6/8. This substantial numerical sensitivity prevents claims of convergence or stable dolphin facilitation. The coarse 72T outcomes remain secondary continuations; the fine grid covers 36T only.

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
- Space and model time are uncalibrated. The coarse timestep is 0.00125T and the fine timestep is 0.000625T; the 36T horizon is not a measured real-world encounter duration. These are fixed-model pilot results without a numerical convergence claim, energy budget, or long-term evolutionary learning. The earlier two-school G-only controls gave joint gains in two of four repetitions; this evidence is kept separate from the newer eight-school grid comparison. This is not evidence for a general reciprocal advantage.
- The earlier follow-up has two independent schools and two capture streams each. The later cohort has eight new schools, paired across grids. Neither grid repetition nor the second horizon adds independent schools. Development was used to select the policy.

## Evidence snapshots and preservation

The active notebook imports `notebook_support_v4.py` and uses `DATASET_2026-11-09_0433.json` and `INPUT_MANIFEST_2026-11-09_0433.json`. All previous inventories, manifests, case seals, support modules and reference figures remain unchanged. Saved previous notebooks and receipts are under `snapshots/`.

Current plotting source is `paper_figure_source_v4.py`, with `reference_figures_v4/`. New grid tables go to `outputs/final_grid_tables/`; earlier/coarse tables remain in their separate folders. Figures are written to `outputs/final_figures/`. `SOURCE_CLOSURE_2026-11-09_0433.json` maps every finer-case source reference to its exact bundled file. The final report text/source/PDF snapshot is versioned under `reports/snapshots/2026-11-09_0433/`; `reports/current/` is the current presentation alias.

The default notebook rebuilds the current report from sealed evidence. The unchanged optional `run_model.py` still runs only the documented historical 36T D/DG pair or original eight-case replication. It does not rerun the newer ensembles. New-study source and frozen configurations are supplied, but no newer optional runtime has been silently substituted or claimed validated.

## Supporting timing evidence

[Timing engineering records](supporting_evidence/timing/README.md) retain three sealed 4T,8T and 36T checks, their protocols and independent audits. They are verified separately during Run All and excluded from the 72-case feeding inventory and pooled analysis. The 36T check was selected after baseline screening; it produced one partial hold, zero requested 1T releases and unchanged catches. It is engineering validation, not independent confirmation of a feeding benefit.

## Validation performed

All 22 default cells passed in a fresh process. They verify 72 feeding cases and 72 new-study sealed horizon records, exact cross-grid initial fish/actor/controller/private-RNG matching, raw event counts, the frozen coarse bootstrap, and the paired numerical tables. All four figure pixels match the final report references on the tested environment. A relocated-folder check removes PYTHONPATH and uses a path containing spaces. Analysis executes zero native steps.

Fourteen CSV tables are exported, with earlier cohorts, coarse horizons and paired grid differences kept separate. The finer results are a two-grid sensitivity test, not convergence evidence. Three timing engineering cases are verified separately and never pooled as feeding replicates.

The unchanged optional runner's earlier 0.5T D/DG smoke passed 800 native steps; it is too short to test feeding. Simulation compatibility constraints remain in NATIVE_SETUP.md. Other operating systems and font versions can produce rendering differences; macOS/Windows execution is not validated here.

Receipts are `validation/final_notebook_2026-11-09_0433.json`, its relocated-folder companion, and the preserved prior receipts.
