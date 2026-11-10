# Run the saved-data notebook locally

Use Python 3.12 or a compatible Python 3 analysis environment:

```sh
python3 -m venv .venv-analysis
# Linux/macOS:
source .venv-analysis/bin/activate
# Windows PowerShell instead: .venv-analysis\Scripts\Activate.ps1
python -m pip install -r requirements-analysis.txt
python -m jupyter lab main.ipynb
```

Open the notebook from this folder, choose the environment's Python 3 kernel,
restart it, and run all cells. If the kernel is missing, install/register it:
`python -m ipykernel install --user --name fishsim-analysis`.
`requirements-analysis.lock` records the original tested analysis versions.

Default execution verifies bundled hashes, reconstructs the nine completed
discovery tables and displays Figures 1–3. It starts no simulation and makes no
bootstrap draws. New outputs use a fresh folder under `outputs/` on every run.
The ordinary saved-data notebook works without a model binary or model install.

This private candidate leaves the final validation backend **PENDING**. It will
not fabricate estimates or use partial96/144 results. After all192 cases and
independent FINAL/metadata reviews are accepted, the publisher binds the actual
portable snapshot, receipt and root activation in `FINAL_NOTEBOOK_PROFILE.json`.
The logical notebook cells then work unchanged. Four additive validation tables
and a new Figure 4 will be generated from that accepted data; existing discovery
figures and all historical notebooks/manifests are preserved.

The optional native replay remains disabled. The reviewed primary H1/G36
frontend's separate setup and artifact release are needed for actual model runs;
a source review or successful saved-data notebook is not a native certificate.
The final published route will generate a local opt-in request automatically.
No professor-authored approval JSON is required.

For a headless run in the active analysis environment:
`python execute_notebook.py`. The notebook itself keeps the generic Python 3
kernel; the headless helper creates a local kernel specification for its own
interpreter. It never installs packages or compiles code.
