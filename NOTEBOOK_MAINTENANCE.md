# Active notebook entry

Open `main.ipynb` from the repository root. `MAIN_NOTEBOOK_PROFILE.json` pins the exact current report, ten default code cells, six summary tables and four matching figure files. Optional native execution remains off.

```bash
python refresh_main_notebook.py
python refresh_main_notebook.py --save
```

The validator checks canonical code before kernel creation, then runs all cells in a fresh kernel using the calling Python interpreter. A previously enabled native toggle or altered command is rejected. It verifies frozen hashes, CSV bytes and current report pixels. `--save` also refreshes cached notebook outputs. Install the analysis requirements first; a notebook/kernel environment is needed. The tested Python3.12 environment is recorded in the versioned profile.

The active generator is `create_main_notebook_current_paper_2026_11_09.py`. It selects the frozen current-paper cells, adapts the package/profile paths and retains two optional v6 cells using PROJECT_ROOT. It writes root `main.ipynb`; it does not execute the model. Its generated outputs require validation before publication.

After regenerating `main.ipynb`, restore its recorded-replay viewing help from a Terminal opened in the repository root:

```bash
python tools/update_notebook_viewer_help.py
python tools/update_notebook_viewer_help.py --check
```

This idempotent postprocessor changes only the introductory Markdown. It preserves the 21-cell structure, all 10 reviewed code cells and their pinned hash, cached outputs and metadata. The pinned generator and notebook profile remain unchanged. The help points to `python tools/watch_replays.py`, the [visualisation guide](docs/VISUALISATION.md) and the [README](README.md); playback reads saved data and starts no native simulation. Run the normal fresh-kernel validator after regeneration and postprocessing.

All older `create_notebook*.py` files and `SNAPSHOT_REFRESH_HANDOFF.md` describe historical versions and must stay unchanged. Current-paper profile files, the old 8028 scientific inputs and 56 model-addon files are protected by additive manifests. Future paper revisions need a new versioned profile/generator, preserved history, a matching report pin and fresh default-cell/figure/table checks. Never edit sealed data in place: some immutable originals share storage.

`main_2026-11-09_v6.ipynb` retains the earlier 21-code-cell full raw-evidence workflow. Open it with the repository root as cwd. Its report is under reports/snapshots/2026-11-09_v6_through18. No repository CI workflow exists at this revision; validation receipts are under validation/. Native Google Doc publication uses a fresh current-Doc revision and text guard, preserving human edits.
