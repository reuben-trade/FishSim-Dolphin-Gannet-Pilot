# Actual-model execution and source provenance

Figure reproduction and evidence analysis require no native library. This document concerns only the optional **new simulation** section.

## The historical binary

`frozen_model/lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so`

SHA-256: `eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558`

This existing binary is pinned by the original model setup. It was used with CPython 3.12.13 on Linux x86-64. The ELF library requires glibc 2.43, GLIBCXX_3.4.32, CXXABI_1.3.15 and libgomp. Copying the file to macOS, Windows, or an older Linux installation does not make it executable there. No other operating system or rebuilt binary has been validated by this package.

On a compatible machine, create a separate CPython 3.12 environment and install `requirements-model-tested.txt`. The historical FishSim package eagerly imports NumPy, SciPy, NetworkX, Matplotlib and Numba; all are required even for the native-import check. JupyterLab can additionally be installed if this environment will run the notebook.

```bash
python3.12 -m venv .venv-model
source .venv-model/bin/activate
python -m pip install -r requirements-model-tested.txt
python run_model.py --check
```

The check verifies protected inputs, prepares a private runtime copy, checks the platform, then imports the actual pinned extension in a fresh process. It takes zero model steps. Missing dependencies or incompatible C++ runtime libraries produce an error rather than an alternative simulation.

```bash
# Explicit integration check: 0.5T D then 0.5T DG, one worker.
python run_model.py --quick --workers 1 --output outputs/my_quick_check

# One complete 36T matched pair using the exposed policy.
python run_model.py --full --school 39063501 --capture-seed 61001 --workers 1 --output outputs/my_full_pair

# All eight fresh-replication cases: two schools × two streams × D/DG.
python run_model.py --full --all-replication --workers 4 --output outputs/my_replication
```

Output folders must be new. Every new case receives the original runner's audit and completion seal. The wrapper records command, native step count and path-relocation receipt. It copies Python, native and checkpoint files byte for byte. Only absolute paths inside copied JSON are rebased to the runtime folder. Original manifests remain unchanged under `frozen_model/`.

## Included C++ source and genuine build recipe

`frozen_model/src/`, `frozen_model/extern/pybind11/`, `frozen_model/extern/eigen3/` and `frozen_model/CMakeLists.txt` are copied from the research repository. Source hashes match the archived source manifest recorded beside the accepted binary. The original build cache and Ninja rules are preserved in `native_build_reference/`. They document a C++17 Release build with GCC 15, OpenMP, pybind11 and link-time optimization. The accepted extension and the original build output have identical SHA-256 hashes.

These facts establish source provenance. They are **not** an attestation that another toolchain will reproduce the historical binary byte for byte. No cross-platform rebuild has been run or validated here.

An investigator can build a candidate in a separate workspace using CMake and an appropriate compiler. For example, from a copy of `frozen_model/` with the chosen Python development environment active:

```bash
cmake -S . -B candidate-build -DCMAKE_BUILD_TYPE=Release -DPython_EXECUTABLE="$(which python)"
cmake --build candidate-build --target cmodel --parallel 2
```

Do not install this candidate over the supplied pinned binary. Linux, macOS and Windows require their respective compiler, Python development and OpenMP support; no platform-specific toolchain recipe is claimed tested here. The old cache contains absolute historical paths and is reference evidence, not a relocatable cache to reuse.

Before using a candidate for scientific runs, create a separate provenance record covering source, toolchain, compiler flags and new binary hash; test the actual native import; verify checkpoint loading and finite, deterministic short trajectories; re-run physical-contact, capture accounting, controller gating, RNG replay and matching audits; and compare paired outputs against the historical baseline. The original native-hash pin intentionally rejects a new binary. A separately reviewed model declaration is required to accept it; this notebook does not bypass the pin.
