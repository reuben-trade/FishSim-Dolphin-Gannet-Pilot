# Current eight-school model execution

This additive runner addresses a different task from the default analysis cells.
The analysis notebook reads saved encounters and recreates the paper. This runner
creates **new simulations of the current eight-school model**, on either numerical
grid, using the saved 20T starting schools. Existing evidence is never overwritten.

The original Linux host passed source/input checks, 48 initial-state checks and
four short integration encounters. A separately built Linux amd64 image has now
passed native compilation/import, all 48 initial-state checks, the two 0.5T pairs,
and one 4T fine-grid D/DG pair: 15,200 integration steps in the image.

Those container checks ran as a BuildKit validation target. The local
`--backend docker` bind-mount entry point has been reviewed but has not been run
end to end here. Windows/macOS host execution and ARM emulation are untested.
No full feeding ensemble was run with the rebuilt binary.
The bounded image checks recorded two failed bird contacts and no captures, so
they did not exercise successful capture/removal.

## What stays fixed

- The eight school seeds are 39064501–39064508; the capture setting is 61001.
- Coarse integration uses dt=0.00125T; fine integration uses dt=0.000625T.
- Dolphin and gannet rules, point-contact geometry, success probability, recovery,
  initial fish arrays and predator/private-RNG starts are copied unchanged.
- The coarse study uses 72T encounters with a 36T primary checkpoint. The fine
  study uses 36T encounters. Repeating a grid does not create new independent schools.
- Every execution writes a fresh output folder with the original contact/accounting
  audits and file seals. A current execution receipt records native steps and binary.

The historical `run_model.py`, original binary, manifests and saved results remain
unchanged. `run_current_model.py` is an explicitly separate current-model entry point.
It runs the eight-school coarse/fine replication, not the newer H × G regime sweep.

## Plan before running

From a package containing these additive files:

```bash
python run_current_model.py --plan --grid fine --all-schools --presences D G DG
```

This verifies the source mappings and eight checkpoints, prints the proposed
execution budget, and imports no native simulator. A full 24-case fine replication
has a maximum of 1,382,400 native steps. A full ensemble can take several hours.

## Compatible native Linux environment

The original binary needs CPython 3.12, Linux x86-64, glibc 2.43 or newer and the
documented C++/OpenMP runtime. Install `requirements-model-tested.txt` in a Python
3.12 environment, then use that environment's Python:

```bash
python run_current_model.py --check
python run_current_model.py --quick --grid fine --output outputs/current_quick_fine
```

The check imports the explicit native binary and constructs the 24 matched
school/presence starts on both grids, without stepping either grid. The quick
command runs one 0.5T dolphin-only encounter and its 0.5T dolphin–gannet match.
It is too short to test the 2T herding cycle or infer feeding effects.

On the original host, both grids passed this D/DG check: 400 steps per coarse
case and 800 per fine case, for 2,400 steps overall. The original physical and
private-stream audits and every case seal passed. The accepted evidence is in
`KNOWN_HOST_SMOKE_2026-11-09.json`; the earlier zero-step validation receipt is
retained unchanged. This establishes execution on that host, not portability.

Explicit full examples:

```bash
# One full fine-grid school, all three species-presence conditions.
python run_current_model.py --run --grid fine --school 39064501 --presences D G DG --duration 36 --output outputs/current_school1_fine

# The coarse eight-school ensemble, preserving its 72T horizon.
python run_current_model.py --run --grid coarse --all-schools --presences D G DG --duration 72 --workers 3 --output outputs/current_coarse_ensemble
```

`--workers` defaults to one. `--all-schools` and the longer horizon require explicit
commands. Failed runs are retained for inspection; no automatic retries or parameter
changes occur.

## Portable Linux container, used from local Jupyter

The proposed Docker image builds the **same C++ source**, rather than attempting to
load the historical glibc-2.43 binary on an older operating system. Its official
CPython 3.12.13 Debian base is pinned to a verified linux/amd64 manifest digest.
The model source hash map, compiler, Python version and new binary hash are recorded.
Scientific Python dependencies are pinned; the installed package list is retained.
The container does not install JupyterLab: the local notebook invokes Docker.
Model compilation uses one worker and records the invoked configure/build
commands, generated compile/link commands, compiler, cache and source hashes.
Execution containers have networking disabled; image building needs network access.

Build the validated model source with the pinned base and run the optional checks:

```bash
python prepare_docker_context.py --package-root . --output work/docker_context
docker build --platform linux/amd64 -t fishsim-pilot-runtime:py312 -f work/docker_context/Dockerfile.runtime work/docker_context
python run_current_model.py --backend docker --check
python run_current_model.py --backend docker --quick --grid fine --output outputs/current_quick_docker
```

To exercise the start of herding and strikes beyond the 0.5T startup check:

```bash
python run_current_model.py --backend docker --run --grid fine --school 39064501 --presences D DG --duration 4 --workers 1 --output outputs/current_4T_docker
```

The 4T pair is an engineering demonstration, not an estimate of feeding benefit.
The saved-data notebook remains the route for reproducing the reported results.

The build context contains model sources and build instructions only. Data, private
runtime caches, Git metadata and the historical binary are excluded. At execution,
Docker bind-mounts the local notebook package and writes new outputs there.

The runner can be called from a **local Jupyter notebook** with the notebook kernel's
Python; the Docker backend supplies its own Python 3.12 environment:

```python
import subprocess, sys

RUN_CURRENT_MODEL = False
if RUN_CURRENT_MODEL:
    subprocess.run([
        sys.executable, "run_current_model.py", "--backend", "docker",
        "--quick", "--grid", "fine", "--output", "outputs/my_current_quick_run"
    ], check=True)
```

Docker must already be installed and running on the user's computer. The container
target is Linux amd64. Direct macOS/Windows native binaries and ARM execution are not
asserted tested. A source rebuild is a separate binary, so it is recorded as such and
is not represented as the historical native artifact or as a numerical convergence check.

## Derived runtime provenance

Each private runtime copies the published scientific files unchanged and adds the
eight exact prepared checkpoints. Only JSON paths and an explicitly selected native
binary declaration are rebased. Fresh zero-step checks establish matching D/G/DG and
coarse/fine initial states, correct diagnostic cadence and current source freezes.

The historical preparation binary is retained explicitly in each derived checkpoint
manifest. A source-built binary is an execution binding; it does not relabel how the
saved fish checkpoints were prepared. If an audit is interrupted after rewriting its
JSON declarations, use a new `--work` folder rather than modifying the old cache.
Packaging additions requires a new input-manifest version; the pinned historical
`INPUT_MANIFEST_2026-11-09_0433.json` must stay unchanged.

Source-built runtimes also retain the exact historical binary in a separate
`historical_native` folder. The archived actor initializer checks that original
artifact while reading its historical reference; it does not execute it. The active
module remains in `lib/fish_sim` and is checked against the separately declared
source-build hash. In sealed case metadata, `config.native` names the historical
actor reference, while `config.native_sha256` names active execution. Runtime and
execution receipts record both roles explicitly.

`CURRENT_MODEL_DECLARATION.json` records these derived bindings, environment versions
and all copied input hashes. It is distinct from every historical case seal. New
simulations remain separate from the saved evidence used by the report.
