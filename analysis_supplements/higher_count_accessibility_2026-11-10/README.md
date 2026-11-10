# Higher-count accessibility supplement

Read [the complete24-condition report](../../reports/supplements/HIGH_COUNT_ACCESSIBILITY.md). This is saved-output discovery analysis on four previously examined schools, not new feeding data or fresh-school validation. The current paper, main notebook and their four figures remain unchanged.

`analyze.py` is the byte-exact author analysis (SHA256838ded0738594d3551ecfea17a491f4d3eaf3ac21d599cafd4ad63133c04d22f). It retains its original absolute research paths and is not a portable entry point by itself. `AUTHOR_README.md` is its archived original usage note. The frozen audit binds644 inputs and four saved CSVs. `INPUT_MAP.json` maps those hashes to bundled files;643 reuse existing public bytes, and only the small geometry source is newly archived. Original absolute paths are provenance labels, not required local directories.

## Replay from sealed saved trajectories

From the repository root, with the analysis dependencies installed:

```bash
python -B analysis_supplements/higher_count_accessibility_2026-11-10/replay_saved_raw.py --verify-only
python -B analysis_supplements/higher_count_accessibility_2026-11-10/replay_saved_raw.py
```

The full command verifies644 input hashes, constructs a temporary old/high/upper/legacy directory view using hardlinks where possible and copies otherwise, and runs the unchanged author analysis with its directory globals redirected to that view. Raw inputs are only read. Results go to a new directory below `outputs/higher_count_accessibility/`; existing directories are never overwritten. Use `--output /path/to/new/directory` to select a different new result directory. The temporary view lives below repository `outputs/` and is removed afterwards.

Acceptance requires byte identity for all four frozen CSVs, reconciliation of the old 48 diagnostic cases, and unchanged input bytes. No native FishSim module, model stepping, controller decisions, target-selection randomness or bootstrap draws are used. The generated audit contains paths to the deleted temporary view; the durable `INPUT_MAP.json` and replay receipt link them back to public source files by SHA256. The independent review is root-recorded from the named peer's actual verification, as its receipt states.

The full adapter passed on Linux with Python 3.12.13 and NumPy 2.5.4: all four CSVs were byte-identical, all 644 source hashes stayed unchanged, and zero native steps or bootstrap draws were taken. This was a saved-raw replay lasting 19.06 seconds. Other platforms have not been tested. This adapter reproduces accessibility diagnostics from saved trajectories, not the36T feeding ensemble or the main notebook.

## Interpretation

Potential geometry includes busy/recovering birds and differs from actual readiness or a committed-target test. Boolean times use left-constant0.1T samples. Surviving-prey depth statistics change with removals. Keep the same four-school discovery scope, all 24 cells and old 48 reconciliation explicit; association does not isolate herding, scattering, competition or attack synchronisation.
