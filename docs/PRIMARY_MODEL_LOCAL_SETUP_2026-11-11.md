# Primary H1/G36 replay: setup and tested scope

Open `main.ipynb` from the repository root for the current paper analysis.
Default Run All reads saved evidence, exports thirteen tables and four figures,
and takes zero model steps. Ordinary output/kernel-metadata saves are supported.

The bundled release includes accepted artifact-specific 4T and 36T replay
proofs for both binaries. Native replay is a separate opt-in in the final cell;
it remains off during ordinary saved-data analysis. The notebook checks the
installed certificate and acceptance records before starting model work.

## Environment

The native artifacts have a known Linux x86-64 CPython 3.12 scope. Use the pinned
model dependencies plus Jupyter requirements in a Python3.12 environment:

```sh
python3.12 -m venv .venv-model
.venv-model/bin/python -m pip install -r requirements-model-tested.txt -r requirements-analysis.txt
.venv-model/bin/python -m ipykernel install --user --name fishsim-primary-model
```

Select that kernel for optional native execution. The default saved-data
analysis can keep its separate analysis environment. Binary/platform details
remain in `NATIVE_SETUP.md`; a fresh installation or Windows/macOS/ARM support
is not implied by the recorded engineering checks. The local workflow QA uses
explicitly recorded existing dependency environments, not a fresh pip install.

## Optional notebook cell

Save edits to the four leading literals in the final cell:

```python
RUN_NATIVE = False          # Set True to opt in to the certified replay
NATIVE_DURATION_T = 4        # 4 for a short check; 36 for the paper horizon
NATIVE_ARTIFACT = "historical"  # or "source-built"
NATIVE_WORKERS = 6           # an integer from 1 to 6
```

With `True` and a valid release, the ordinary GUI-like route prepares a fresh
runtime, checks all 192 initialized identities without stepping, runs the six
fixed first-world cases and applies the exact saved-data owner checker. The
CLI records its local opt-in requests automatically; the professor does not
write approval JSON. Existing or partial outputs are never overwritten.

The run uses school 39065501, label 71001, both grids and D/G/DG arms. A 4T
example has 28,800 integration steps; its distinct 36T version has 259,200.
The native execution receipt is separate from the preceding saved-analysis
receipt. Data and model settings remain fixed: twelve dolphins, thirty-six
birds, H1, 160 fish, q=0.7 conditional contact success.

The facade rejects the old analysis-only headless launcher's `.headless`
environment markers before native delegation. Use a clean GUI kernel or the
separate certified finite CLI. The recommended headless analysis command always
requires `RUN_NATIVE=False`:

```sh
python -m replay_tools.primary_192.execute_notebook
```

The installed model interface is under `model_examples/primary_192/`, not the
older `model_examples/primary/` spelling. For its native-free argument plan:

```sh
python model_examples/primary_192/run_primary_model.py --package-root . --plan
```

## A fixed example is not the ensemble result

The selected world is retained even when one species loses. Its accepted
**36T group capture counts**, from the original study, are:

| Grid | Dolphin-only → mixed dolphins | Bird-only → mixed birds |
| --- | ---: | ---: |
| Coarse | 25 → 26 | 16 → 24 |
| Fine | 25 → 32 | 17 → 3 |

These are full-horizon reference counts, not expected 4T counts. The source is
[`validation_case_counts.csv`](../paper_profiles/final_primary192_2026-11-11/tables/validation_case_counts.csv),
with exact selected rows archived in the release profile. The fine-grid bird
loss is not replaced by a favourable world. Mutual-feeding inference comes
from the complete sixteen-school/two-label ensemble in the paper, not this
six-case software check.

Actual artifact engineering covers the first-world six cases on both grids
at each tested horizon. The original interface offers `--all-ensemble`, but a
fresh replay of all 192 encounters through this professor route is not claimed
as tested. The short local notebook QA checks orchestration and source
independence; it does not substitute for separate actual 36T backend proofs or
create new independent feeding evidence.

## What was actually checked

Both the historical and source-built binaries passed the 192 initialized
identity checks, six 4T examples and six 36T examples. A separate, real notebook
Run All in a space-containing package copy then exercised the local opt-in
route with the historical binary: 192 zero-step starts followed by the six 4T
cases, exactly 198 constructors and 28,800 steps. All six saved trajectories,
events and private state matched the accepted references. The source-built
binary has separate backend proofs; it was not the binary used for this
additional notebook orchestration test.

The instrumented notebook test took about 27 minutes; repeated integrity
hashing of the copied runtime during the 192-start check dominated that time.
Default saved-data analysis takes about 12 seconds on the tested host. These
are observations from existing Linux x86-64 CPython 3.12.13 environments, not
fresh-install or other-platform guarantees. The notebook QA used the existing
analysis environment with missing model dependencies read from the existing
model environment; no dependencies were freshly installed for that test.

The source-read guard covered thirteen Python processes, with one isolated
saved-data renderer outside that hook. Its twelve Python child joins, one
kernel system-information probe and two fontconfig metadata probes were
reconciled. Seven native workers had measured module paths and numeric thread
settings, with no unexpected author-source reads. This is Python audit-hook
coverage after startup, not a claim about every native system call.

The [accepted QA archive](../notebook_profiles/certified_primary_release_2026-11-11/local_qa/README.md)
contains the independent/root receipts, source pins, guard records and the
preserved metadata-review failure history. Absolute paths inside those records
describe the authoring environment; they are not paths required from the
professor. The installed replay resolves its certificate proofs inside this
repository and creates fresh local runtime/output directories automatically.
Earlier `PENDING` binding files and the source-only facade draft are retained
as history; the current bindings and accepted receipts supersede their status.
