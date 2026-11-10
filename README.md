# FishSim: dolphin–gannet pilot

Saved simulations, 3D replays and reproducible analysis of dolphin–gannet feeding around a fish school.

## Watch a recorded 3D encounter

[![Recorded dolphins and gannets attacking around a fish school, with live capture counters](docs/media/dolphins-gannets-2026-11-09.gif)](docs/media/dolphins-gannets-2026-11-09.webm)

**12 dolphins · 6 gannets · H=2T · 160 initial fish.** This shows the entire saved 0–36T encounter from run `s39063501_H2_G6_DG_c61001`, in about 30 seconds of playback. Orange markers are dolphins, green markers are gannets and blue markers are fish. The clock, capture counters, attack states and water surface remain visible.

[Full video (WebM)](docs/media/dolphins-gannets-2026-11-09.webm) · [Recording settings and source hashes](docs/media/dolphins-gannets-2026-11-09.json)

The recording uses actual saved positions. T is uncalibrated model time; marker size is schematic. No simulation, predator behaviour or capture probability was changed for this recording.

## Start here

| Task | Entry point |
| --- | --- |
| Watch and compare saved runs in 3D | `python tools/watch_replays.py` · [Viewing guide](docs/VISUALISATION.md) |
| Reproduce the current paper’s figures and tables | [main.ipynb](main.ipynb) |
| Read the current paper | [Working draft PDF](reports/current/Feeding_Frenzy_Working_Draft.pdf) |
| Review all findings, assumptions and experimental conditions | [Scientific overview](docs/STUDY_OVERVIEW.md) |
| Find code, data, archives and validation records | [Repository guide](docs/REPOSITORY_GUIDE.md) |

## Open the interactive 3D viewer

From a terminal in the repository root:

```bash
python -m pip install -r requirements-analysis.txt
python tools/watch_replays.py
```

The script opens a local browser viewer covering **108 saved encounters**, including the 9/12/18-gannet extension. This viewer catalogue remains that validated subset; the current paper and bundled raw data additionally include the completed 24/36-bird extension. Select individual runs or compare A/B, inspect their settings and capture returns, then play, pause or scrub the shared clock. Switch between 3D, top and side views; drag the 3D view to rotate it. Dolphins, gannets and individual capture counters are shown together.

This reads bundled recordings and starts no simulation. It needs no native FishSim binary. For a remote/headless machine or a specific port, see the [viewing guide](docs/VISUALISATION.md).

## Run the analysis notebook

Open **[main.ipynb](main.ipynb)** in JupyterLab and choose **Run → Run All Cells**. Viewing instructions are also in its opening cell.

```bash
python -m jupyterlab
```

The default seven code cells reproduce four figures and thirteen canonical summary tables from saved results. They take zero native model steps and generate no new bootstrap draws. Actual full-study reproduction passed in fresh kernels and a separate space-containing checkout. [Detailed setup and platform notes](docs/LOCAL_ANALYSIS_SETUP.md). Optional native replay remains disabled and its release is separate.

## What this study shows

The complete prespecified validation supports **mutual feeding benefits within the model** at minimum herding H=1T with twelve dolphins and thirty-six gannets. Sixteen new schools each have two nested randomness labels, matched dolphin-only/bird-only/mixed groups, and both encounter timesteps: **192 full encounters**.

On the primary fine grid, dolphins catch **719→905 fish (+25.9%)** and gannets **292→536 (+83.6%)**. Mean partner gains per individual over 36T are **+0.484 [0.225,0.744]** for dolphins and **+0.212 [0.093,0.330]** for gannets, using the locked 97.5% marginal Student t intervals. Both lower bounds exceed zero, meeting the prespecified criterion. School means include losses: dolphins 14 gains/1 tie/1 loss, gannets 14 gains/2 losses; both species gain in 12/16 schools. Labels are averaged within each school, not counted as extra schools.

The four-school discovery map remains separate, with all 24 H×bird-count settings and every sign retained. Its selected 45.1% dolphin gain is not the new validation estimate. The selected D24 follow-up also remains separate and shows lower food per dolphin despite greater group catches. The new paired-grid intervals do not establish convergence; units, conditional q=0.7, information assumptions and field realism remain uncalibrated. Read the [current paper](reports/current/Feeding_Frenzy_Working_Draft.pdf), [executive summary](reports/current/EXECUTIVE_SUMMARY.md) or [scientific overview](docs/STUDY_OVERVIEW.md).

The [pre-analysis plan](reports/supplements/VALIDATION_PREANALYSIS_PLAN.md) and earlier [48](reports/supplements/VALIDATION_PROGRESS_48.md), [96](reports/supplements/VALIDATION_PROGRESS_96.md) and [144-case](reports/supplements/VALIDATION_PROGRESS_144.md) snapshots remain unchanged. The separate [accessibility supplement](reports/supplements/HIGH_COUNT_ACCESSIBILITY.md) uses the older 128 bird-bearing discovery encounters. Planned [H2/G12](reports/supplements/LOWER_COUNT_FOLLOWUP_PLAN.md) and [crossed](reports/supplements/CROSSED_FOLLOWUP_PLAN.md) follow-ups have no feeding results here.

## Model execution and repository history

New simulations are separate from replay and default notebook analysis. The reviewed [primary H1/G36 replay source](model_examples/primary_192/PRIMARY_MODEL_SETUP.md) has distinct 4T and 36T modes; native release remains pending its separate artifact-specific engineering checks. It is not activated by the default notebook. Read [V6_MODEL_SETUP.md](V6_MODEL_SETUP.md) for bounded parameter-map examples, [CURRENT_MODEL_SETUP.md](CURRENT_MODEL_SETUP.md) for the coarse/fine replication runner, or [NATIVE_SETUP.md](NATIVE_SETUP.md) for the historical runner.

Earlier generated exports and the old delivery receipt are grouped under [archive/](archive/README.md). Hash-pinned source, data and historical filenames remain intact because the notebook checks their exact paths. The [repository guide](docs/REPOSITORY_GUIDE.md) identifies the files needed for everyday use. Third-party notices remain in [PROVENANCE.md](PROVENANCE.md).
