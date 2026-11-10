# Current notebook and optional primary replay

The default notebook is ready to reproduce the paper from saved data. Native
replay remains disabled while its separate artifact-specific zero, 4T and 36T
certification is incomplete. The existing model setup is preserved as a
historical preparation record; this addendum uses the installed
`model_examples/primary_192/` path.

## Ordinary Jupyter use

Create the analysis environment as described in [LOCAL_ANALYSIS_SETUP.md](LOCAL_ANALYSIS_SETUP.md),
open `main.ipynb`, select its kernel and Run All Cells. You can save outputs,
change kernel metadata and Run All again in the same kernel. Verification
checks the fixed logical cells rather than the active notebook's serialized
outputs. The old notebook remains byte-exact in
`archive/notebooks/primary192_saved_data_2026-11-11/`.

The four leading settings in the final optional cell accept only these values:

| Setting | Allowed values |
| --- | --- |
| `RUN_NATIVE` | `False` or `True`, as a literal boolean |
| `NATIVE_DURATION_T` | `4` or `36`, as an integer |
| `NATIVE_ARTIFACT` | `"historical"` or `"source-built"` |
| `NATIVE_WORKERS` | An integer from `1` to `6` |

Keep `RUN_NATIVE = False` for ordinary analysis. Save setting edits before
Run All. Altered analysis/native workflow code is rejected; use a separate
exploratory notebook for other changes. The versioned template and all other
old package inputs remain verified.

## After native certification

Setting `RUN_NATIVE = True` first validates the actual installed release and
its artifact-specific proofs. Missing certification raises before any model
subprocess or work directory is created. The current release bindings are
pending, so this route is closed today.

After certification, use the tested Linux x86-64 CPython 3.12 model environment
and pinned model dependencies. Select that kernel for native replay; install
`ipykernel` there and register it if needed. The saved-data analysis can retain
its separate environment. No Windows, macOS, ARM or Docker claim is made for
this interface.

The optional route prepares a fresh runtime, performs its 192 exact zero-step
initializations, and executes six first-school/first-label cases: dolphin-only,
gannet-only and mixed, on both grids. The model CLI creates the local opt-in
requests; the professor does not write approval JSON. Choose 4T for a short
example or 36T for the full paper horizon. At six cases, the respective step
ceilings are 28,800 and 259,200; this is separate from default analysis.

The saved-data owner checker is additive under
`replay_tools/primary_192/check_primary_replay_v2.py`. It retains the original
physical predicates and exact reference comparisons with a portable source
seal adapter. The original checker and native interface stay unchanged.
The first-world example does not rerun the entire 192-case study or create
new independent feeding evidence. Its own execution receipt is separate from
the saved-analysis receipt printed before it.

For an argument plan without native execution, after installing the addendum:

```sh
python -m replay_tools.primary_192.optional_native --package-root . --plan \
  --duration 36 --native-kind historical --workers 6
```

No native release is inferred from that plan. The default saved-data notebook
continues to produce thirteen canonical CSVs and four numbered figures.

The headless saved-analysis entry is deliberately analysis-only and rejects a native-enabled configuration before kernel startup. After certification, actual native replay uses the GUI notebook or the separate finite CLI. Each headless analysis proof goes into a fresh ignored output directory; historical receipts remain intact.
