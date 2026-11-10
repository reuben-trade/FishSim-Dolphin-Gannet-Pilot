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
python execute_notebook.py
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
