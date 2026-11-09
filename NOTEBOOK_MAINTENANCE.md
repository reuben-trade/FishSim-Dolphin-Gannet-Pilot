# Active notebook entry

`main.ipynb` is the current entry. Open it from the repository root, select the analysis environment described in README.md, and run all cells. Optional native execution remains off by default.

`MAIN_NOTEBOOK_PROFILE.json` identifies the exact report PDF, default-cell count, exported tables and four report figures expected for this entry. Validate or refresh its cached outputs with:

```bash
python refresh_main_notebook.py
python refresh_main_notebook.py --save
```

The validator rejects any changed code cell before executing the notebook, including a previously enabled native toggle or edited subprocess command. Restore the reviewed default cells first. The first command verifies execution without rewriting the notebook. The second also saves regenerated cell outputs to `main.ipynb`. Both rebuild only mutable exports and import no native simulator. They require the expected report bytes, all protected scientific/addon inputs, CSV bytes and report figure pixels to match.

The existing `create_notebook*.py` files and `SNAPSHOT_REFRESH_HANDOFF.md` describe historical snapshots. Several are protected by earlier input manifests. Preserve them exactly; do not run an older generator as the active update workflow. A future snapshot should use a new versioned generator targeting `main.ipynb`, update the explicit report profile, preserve prior notebook versions/manifests, then execute and validate every default cell from a fresh relocated checkout. Never edit sealed data in place: some protected files share immutable storage with their archived originals.

There is no repository CI workflow at this revision. Validation receipts are under `validation/`. Report prose and figures require their own reviewed source, data and page checks. A downloaded manuscript is not automatically the same report profile; reconcile its sources and preserve human edits before replacing the current profile.
