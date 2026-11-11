# Run the current paper analysis locally

From the repository root, create a Python environment and install:

```sh
python -m venv .venv-analysis
# Activate it, or call its Python executable directly.
python -m pip install -r requirements-analysis.txt
python -m jupyterlab
```

Open main.ipynb, select this Python kernel, restart and Run All Cells. Keep the
notebook beside its support files and bundled data. The repository includes
substantial sealed raw evidence; the accepted primary snapshot alone is about
1.4GB. Default execution reads saved results, rebuilds four figures and thirteen
canonical CSV tables, and starts no simulator or new bootstrap draws.

For a fresh headless kernel in the same environment:

```sh
python -m replay_tools.primary_192.execute_notebook
```

Actual production checks passed on Linux/Python3.12, including an independent
space-containing copy with original author/model/data paths denied. Generic
Python3 kernel metadata is supplied. Other operating systems/font versions have
not been tested here; figure pixels are checked in the recorded environment.
requirements-analysis.lock records that environment. No native FishSim binary,
compiler or network is needed for saved-data analysis after installation.

The primary model frontend is documented separately under
model_examples/primary_192/PRIMARY_MODEL_SETUP.md. Its source is installed,
but its native release remains pending artifact-specific engineering; the
notebook's native toggle is off. Older short examples have different scope.

Frozen input hashes are intentional. Preserve the canonical notebook/package
for reproduction; make a separate copy for exploratory edits. The prior
notebook and profile are archived under archive/notebooks/.

Saving execution outputs and selecting a different kernel does not invalidate the current notebook. The fixed logical cells and typed optional settings are checked against an immutable template. See [PRIMARY_REPLAY_SETUP.md](PRIMARY_REPLAY_SETUP.md); native execution remains closed until its separate release.

The recommended headless driver is analysis-only: it rejects `RUN_NATIVE=True` before starting a kernel and writes a fresh proof under ignored `outputs/headless_*/`. The original root `execute_notebook.py` is preserved for historical provenance; use the versioned command above for current headless analysis.


## Completed H2/G12 saved-data addition

The current notebook has16cells/8code and regenerates21tables: the unchanged13 discovery/primary tables plus8 completed-H2/programme tables. It retains four paper figures and all original seven code cells. The follow-up uses the same16schools, not32; H2 intervals are95% pointwise and the additional programme intervals98.75%, leaving the original97.5% primary unchanged. Default native execution remains off; the existing primary replay certificate does not certify H2 dynamics.
