# FishSim: local research notebook

Open **FishSim_Professor_Notebook.ipynb** and choose **Run → Run All Cells**. The default run verifies the bundled evidence, rebuilds all four figures in the first thesis working draft, and exports four CSV tables. It does not execute the fish simulator. The saved notebook already contains the executed outputs for review.

The evidence snapshot contains eight development encounters and eight fresh exposed-policy replication encounters, each lasting 36 model-time units. It excludes the earlier C-policy pilot and any later overnight experiments. The two capture streams in each fresh school are repeated stochastic runs of the same starting geometry, not additional independent schools.

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
- Space and model time are uncalibrated. The numerical timestep is 0.00125T; the 36T horizon is not a measured real-world encounter duration. These are fixed-model pilot results without a numerical convergence claim, energy budget, long-term evolutionary learning, or reciprocal-benefit demonstration.
- Fresh replication has two independent starting schools, with two capture streams each. Development was used to select the exposed policy. Keep its outcomes separate from the fresh replication when judging evidence.

## Files

`data/` contains the original complete sealed case outputs and prior analysis tables. `INPUT_MANIFEST.json` protects those inputs, frozen model code and plotting code. `frozen_model/` contains the actual runtime source closure, fresh prepared checkpoints, native binary and C++ build source. Historical JSON manifests remain intact there; optional execution makes a private runtime copy under `work/` and records only path relocations. `outputs/` holds regenerated figures and tables and any explicitly requested new runs. `validation/` records notebook and integration checks. `reference_figures/` preserves the first working draft's four figures.

New simulations never overwrite the bundled historical evidence. The repository-only bundling utility is omitted from this standalone distribution. See [PROVENANCE.md](PROVENANCE.md) for source attribution and retained third-party license notices.

## Validation performed

All 16 default code cells were executed in a fresh Python process and clean namespace. They verified all 16 sealed cases and 2,479 protected files, produced four CSV tables, and reproduced all four paper figures pixel-identically on the authoring environment. No native simulator was imported by the default cells. This validates their code execution; an interactive Jupyter frontend was not installed on that host.

Separately, the optional runner passed an actual 0.5T D / 0.5T DG integration pair using one worker, the exact pinned native binary and unchanged behavioral code/checkpoints: 800 native steps total, both original case audits and completion seals passed. The short check validates the execution path, not feeding outcomes. Receipts are in `validation/default_notebook.json` and `validation/native_smoke.json`.
