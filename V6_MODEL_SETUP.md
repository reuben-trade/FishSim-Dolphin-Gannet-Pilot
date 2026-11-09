# Optional execution of the v6 model

The notebook's default **Run All** rebuilds the saved study results and takes no simulation steps. Its optional section now offers two short, matched D-only/DG examples from the same model:

| Setting | Herding minimum | Gannets in mixed arm | Duration of each arm |
|---|---:|---:|---:|
| `headline` | 1T | 9 | 4T |
| `joint` | 2T | 12 | 2T |

These illustrate model execution and positions. They do not reproduce the full 36T ensemble or estimate a feeding benefit. The first previously observed school, 39061001, is the default. The existing historical and H2 replication runners remain available separately.

## Run a short example

Native execution was tested on **Linux x86-64 with CPython 3.12** and the recorded scientific dependencies/system libraries. The new interface has not been tested through Docker, Windows, macOS or ARM. Saved-result analysis remains available without this native setup.

From the repository folder on a compatible machine:

```bash
python3.12 -m venv .venv-model
source .venv-model/bin/activate
python -m pip install -r requirements-model-tested.txt

# Hash checks and an execution plan; no native import or simulation steps.
python -B run_v6_example.py --plan

# Strict actual initialization of all 108 starts; zero simulation steps.
python -B run_v6_example.py --check

# Choose one bounded matched pair.
python -B run_v6_example.py --quick --setting headline
python -B run_v6_example.py --quick --setting joint
```

The default uses the separately source-built `cc21` artifact already included in `runtime_validation/source_build_linux_amd64/`. `--native-kind historical` selects the original `eb86` artifact, whose stricter ABI requirements are recorded in [NATIVE_SETUP.md](NATIVE_SETUP.md). A missing dependency, incompatible library or mismatched actual start stops execution.

For Jupyter, install and register the model environment's kernel while that environment is active:

```bash
python -m pip install jupyterlab ipykernel
python -m ipykernel install --user --name fishsim-v6-model \
  --display-name "FishSim v6 model (Python 3.12)"
python -m jupyterlab
```

Select that kernel in Jupyter's Kernel → Change Kernel menu, choose `EXAMPLE_SETTING`, and change `RUN_V6_MODEL` to `True` in the optional cell. A completed run displays a top-view position snapshot. It adds no default report figure export. The model requirements file alone does not install Jupyter or its kernel packages.

The first native request assembles a separate runtime and checks all 108 actual starts. A completed check is reused only when its source, binary, request and seal still match. The runtime is roughly 370 MB; its filesystem must retain 2 GiB free, and the package filesystem must retain 1 GiB. Use a separate writable directory outside the repository for `--runtime` and `--output`. Defaults use the operating system's temporary directory. A pair can take minutes; `--duration 0.5` offers a startup demonstration. Allowed durations are only 0.5T, 2T or 4T.

For example, to select external destinations:

```bash
python -B run_v6_example.py --quick --setting headline \
  --runtime /path/outside/repository/model \
  --output /path/outside/repository/new_pair
```

Outputs must be new. The command generates and retains the local execution request automatically; the professor does not author an approval JSON file. Reuse the runtime for later examples and choose fresh output paths. Printed paths identify the retained request, zero check and case outputs.

## What was verified

The dated [validation status](runtime_validation/headline_examples_v4/VALIDATION_STATUS.json) records:

- Exact actual fish arrays, actors, controllers and private random states for all 108 starts on each of the two binaries: 216 zero-step constructions.
- Ten short cases totalling 20,000 simulation steps, including both matched settings and a frontend reuse check.
- Independent physical-contact, private-stream, time-budget, source and unique-removal accounting. Saved short trajectories and decoded streams matched their archived prefixes on the tested cases; this does not establish full-horizon or compiler equivalence.

There were five failed oral contacts per binary and zero captures in these short checks. Successful-removal execution and a full feeding ensemble remain untested for `cc21`; zero catches were not treated as a validation failure or evidence of absent feeding benefit.

The [independent execution review](runtime_validation/headline_examples_v4/independent_execution_review.json), source review, declarations, derived code and zero-check receipts are bundled separately from feeding inference. The 26 MB raw short-output tree and the two full runtime copies are omitted. The complete original 36T feeding evidence remains included and unchanged.

The interface and its preparation declarations are frozen byte for byte. Their original `not_performed`/`unvalidated` preparation strings predate these completed checks; the separate dated validation status above records the later result. The immutable [source-review artifact](INTERFACE_SOURCE_REVIEW.json) attests to code review, while locally generated requests record a user's explicit execution choice. Neither grants historical experiment authority or turns these short examples into new study replicates.
