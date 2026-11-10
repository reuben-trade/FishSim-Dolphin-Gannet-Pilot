# Primary H1/G36 model replay — private candidate

This is the actual primary-study model and identity inventory, not the older
H1/G9 or H2/G12 demonstration. It offers a short4T mode and a distinct complete
36T mode. **Native execution remains closed.** No native constructor, simulator
import, compiler or native step has been run through this interface.

After certification, the intended professor path is:

Create a Linux x86-64 Python3.12 environment with
`python3.12 -m venv .venv-model`, then install the package's
`requirements-model-tested.txt` using that interpreter. No installer or compiler
is run by this preparation. To use the optional cells in Jupyter, install
`ipykernel` into that environment and register/select its Python3.12 kernel:
`.venv-model/bin/python -m ipykernel install --user --name fishsim-primary-model`.
The default saved-data notebook can keep its separate analysis environment.

```sh
# From the package root, using its pinned Python3.12 model environment:
python model_examples/primary/run_primary_model.py --package-root . --plan
python model_examples/primary/run_primary_model.py --package-root . \
  --prepare --snapshot /path/to/accepted-primary192-snapshot \
  --runtime "$HOME/FishSim-primary-replay/runtime"
python model_examples/primary/run_primary_model.py --package-root . \
  --check --runtime "$HOME/FishSim-primary-replay/runtime" \
  --output "$HOME/FishSim-primary-replay/zero192.json"
python model_examples/primary/run_primary_model.py --package-root . \
  --run --duration 36 --school 39065501 --label 71001 --grid both \
  --arms D,G,DG --workers 6 --runtime "$HOME/FishSim-primary-replay/runtime" \
  --zero-receipt "$HOME/FishSim-primary-replay/zero192.json" \
  --output "$HOME/FishSim-primary-replay/first-world-36T"
```

All destination paths must be fresh and outside the package/source/runtime
inputs. Existing or partial outcomes are retained; there is no overwrite or
automatic resume. A professor does not write approval JSON: after an exact
artifact-specific release exists, the frontend records a local opt-in request.
Today the release file is absent and `--check`/`--run` fail before a lease or
native import. The production snapshot/export also remains gated until all192
cases and the original independent FINAL plus metadata-sidecar reviews pass.

Use `--duration 4` for a short demonstration. It does not reproduce a full36T
encounter. To request the complete fixed ensemble after release, replace the
world/grid/arm selection with `--all-ensemble --duration 36 --workers 8`.
That is192 full encounters and at most8,294,400 native steps, not a quick
notebook cell. The optional runner supports this queue; completing its entire
ensemble through this new interface has not been validated or claimed.

The fixed model has16 starting schools39065501–39065516, labels71001/71002,
coarse dt0.00125T and fine dt0.000625T, matched D/G/DG arms,12 dolphins,36 birds,
160 starting fish and q0.7 conditional oral-contact success. H1 is continuous
local prey proximity before a feasible exposed-target strike. Settings and
private-stream formulas are unchanged. Bird identities G0–G35 remain nested at
the original three launch sites, with lexicographic actor ordering.

The default artifact is the historical eb8654a5… extension. Select
`--native-kind source-built` consistently on preparation, check and run to use
the published cc21f00f… artifact. Both are known Linux x86-64 CPython3.12
artifacts. G36/primary36T execution through this interface is untested for both
until the future engineering passes. No other ABI, rebuilt-binary equivalence,
Windows/macOS/ARM or container-interface portability is claimed.

## Preparation and immutable inputs

`--plan` uses the standard library only and takes zero native steps. Private
authoring checks may use `--prepare --author-inputs`; that mode is explicitly
not accepted for professor local execution. It verifies all2,127 frozen source
bindings and makes a separate file view with hardlinks or copy fallback.
Relocated declarations are unlinked before writing. No original source, public
input or active study is renamed, moved or edited.

The future portable path resolves original identities through the reviewed
snapshot's content-addressed crosswalk. `Snapshot` is followed by explicit
`validate_evidence`; low-level object validation is not mistaken for accepted
scientific evidence. Original absolute strings are opaque identities, never
fallback paths. The snapshot reader source is SHA-pinned. A missing reader,
missing object or unresolved source fails closed.

`--snapshot` accepts either the snapshot directory or its explicit
`SNAPSHOT.json` file, including paths containing spaces. Both forms normalize
to the same manifest file before reader construction. That exact file also
supplies the runtime declaration's manifest SHA, path and parent directory.
The production route rejects explicitly synthetic test snapshots.

Raw20T preparation checkpoints feed the constructor, so native heading
normalization occurs once. Saved post-constructor initial-school arrays are
comparison references. `--pure-check` prepares the real Python actors/planners
and private RNG states for all192 cases, then matches the frozen pure-receipt
and raw-checkpoint hashes. Archived post-constructor positions and prey IDs
match exactly; raw-to-normalized heading differences are checked separately
within1e-12. This is not an actual native-start proof. Native imports and model construction/steps are blocked by an
import finder and Python call monitor. A process-local I/O guard forbids reads
from the original author model, original data bank and public checkout while
allowing dependencies and the private file view. No live tree is moved for that
proof, and no fake native object is substituted.

The source derivation changes only operational imports/gates and output paths.
The pure assembly, actual constructor operations and entire physical/accounting
run body retain their parent AST. The inherited FishSim C++ engine is attributed
to yangyushi/FishSim; the project adds predator/controllers and experimental
analysis. The historical reference artifact used by legacy declarations remains
distinct from the explicitly selected active execution artifact.

## Future engineering, not authorised now

The proposal tests both artifacts separately on the same accepted reference
world39065501/71001, all three arms and both grids:

| Stage | Across both artifacts | Maximum native steps |
|---|---:|---:|
| Actual zero starts |384 constructors (192 per artifact)|0|
| Short4T replay |12 complete cases|57,600|
| Complete36T replay |12 complete cases|518,400|
| Total |24 integrations plus zero checks|576,000|

One canonical native lease and a global maximum of8 subprocess workers must
cover each engineering dispatch. Native model state is isolated per worker
process; artifacts are never loaded together. Source-built/historical output
trees remain separate. Any mismatch stops certification and is retained; a
short pass never certifies36T, and a fine-only pass never certifies both grids.

The owner must first bind complete primary192 original8ff FINAL acceptance and
the exact5cc metadata-sidecar PASS, then issue fresh finite source-bound native
authority. Actual zero checks must match all192 exact initialized fish, actors,
controllers and private streams. After zero and short replay acceptance, full
engineering compares complete36T trajectories, all event/contact streams,
terminal fish/controller/RNG state and actor time/food accounting against the
six accepted references. The byte-pinned physical audit is mandatory.

An independent release review must bind the same exact binary and runtime
declaration across zero, short and full proofs. It must name all192 zero starts
and the six first-world cases for each horizon. Only then can that artifact's
`PRIMARY_MODEL_RELEASE.json` enable local opt-in requests. The engineering
comparison is software fidelity evidence, not new feeding inference or extra
independent schools. Full192 replay fidelity is not inferred from twelve
first-world artifact checks.
