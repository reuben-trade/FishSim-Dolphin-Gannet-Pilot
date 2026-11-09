# FishSim: dolphin–gannet pilot and regime map

Open **FishSim_Professor_Notebook.ipynb** and choose **Run → Run All Cells**. The default notebook reconstructs the current report from sealed evidence, checks all protected inputs, rebuilds four figures, and exports 19 CSV tables. Its 21 code cells take **zero native simulation steps**. Saved outputs are included.

**Main finding:** the original shared-rule pilots gave dolphin gains of **17.1% and 16.1%**. The complete exploratory H × G map now shows seven positive and two negative mean same-H dolphin responses. Its largest mixed dolphin return was **H=1T with six gannets: 91→113 captures (+24.2%)**, with gains in all four schools. This also exceeded the best-tested dolphin-only herding minimum, H=1T. At H=2T with six birds, dolphins changed 86→103 and gannets 24→53, with both species gaining in all four schools; the dolphin interval against the stronger H=1T baseline crossed zero.

The full map uses **four previously observed schools and one capture-stream setting**, with exploratory pointwise intervals. It retains every setting and sign. The original positive follow-up used two fresh schools under two settings; those original totals have not been replaced by replay aggregates. The independent eight-school check remains separate: refining the timestep changed mean dolphin effects from +1 to 0 and gannet effects from +5.125 to +2.5 captures per school. The fine dolphin mean combines **four positive, three negative and one zero school effect**. The original positive cohorts and the new map were not rerun on the fine grid. Numerical convergence and general mutual facilitation remain unestablished.

Read the [current report](reports/current/Feeding_Frenzy_Working_Draft.pdf) or [complete response map](reference_figures_v5/fig3_regime_map.png). The inventory contains 132 full feeding execution records: 72 historical records plus 60 corrected-v2 sweep records, **including eight exact historical replays**. Replays, shared controls, grid repetitions and longer horizons do not add independent schools. The stopped v1 recorder attempt is retained only as immutable supporting provenance.

## Local setup: analysis and figures

Use Python 3.10 or newer. From a terminal opened in this folder:

**macOS or Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-analysis.txt
python -m jupyterlab
```

**Windows PowerShell** (activation is unnecessary):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-analysis.txt
.\.venv\Scripts\python.exe -m jupyterlab
```

Open the notebook from JupyterLab's file browser. Keep the notebook beside its support files and data folder. The analysis path uses NumPy, Matplotlib and Python's standard library; JupyterLab supplies the interface, and tzdata supplies the Perth timezone on systems without an operating-system timezone database. No pandas, compiler, native FishSim binary or internet connection is required after installation. Installation follows the [official Jupyter instructions](https://jupyter.org/install).

Analysis code is designed to work across operating systems. Validation receipts record the actual tested environment; macOS and Windows execution has not been tested here. Identical figure pixels are checked on the authoring environment. Other font or Matplotlib versions may produce small rendering differences while retaining the same data.

## Optional execution of models

The additive [current-model setup](CURRENT_MODEL_SETUP.md) documents `run_current_model.py`. It executes the existing eight-school **H=2 coarse/fine replication**, rather than the newer H × G sweep. It does not execute the selected H=1T / six-gannet setting. The notebook prints a native-free execution plan and leaves `RUN_CURRENT_MODEL = False` by default. Its optional demonstration uses 0.5T or 4T; neither is a feeding-benefit experiment.

The original Linux host passed 2,400 bounded integration steps. A separately source-built Linux amd64 image passed compilation/import, 48 initial-state checks and six bounded encounters totalling 15,200 steps through BuildKit. The image checks had two failed bird contacts and no captures, so successful removal and a full feeding ensemble remain untested with that binary. The host Docker bind-mount command and Windows/macOS/ARM execution have not been tested end to end. Source/build instructions and compact receipts are included; the large private OCI image/cache is excluded.

The unchanged historical `run_model.py` remains available separately for the original 36T D/DG pair or original two-school/two-setting eight-case replication. Its 0.5T quick pair checks integration and ends before the 2T herding interval. The supplied historical binary requires **CPython 3.12, Linux x86-64, glibc 2.43 or newer, compatible C++ runtime and OpenMP**. Read [NATIVE_SETUP.md](NATIVE_SETUP.md) before using it. The historical source archive, binary, hash declarations and earlier instructions remain unchanged; a rebuilt binary has separate execution provenance.

## Scientific interpretation

- The dolphin baseline uses the **same rule and H without gannets**. H is continuous near-prey pressure, varied over 1, 2 and 3T; it does not certify completed herding or complementary pod coverage. All travel, herding, failures and recovery count in feeding return.
- The exposed-prey preference ranks feasible fish by low neighbour count within radius 2. Dense fish remain eligible, and outward motion is not required. The dolphin controller has no bird-count/dive cue or post-dive capture bonus.
- Gannets identify density clusters globally within depth limits, sample clusters by accessible fish count, and target a dense accessible location. One, three and six birds use a nested roster at the original three launch locations; count also changes coverage or local multiplicity. Predator body-spacing avoidance is absent.
- Primary effects compare mixed dolphins with same-H D-only controls. Gannet effects use per-bird returns against count-matched G-only controls reused across H. A stronger secondary comparison selects the best-tested D-only H across the four-school bank and reselects it within each whole-school bootstrap draw. This is not a per-school oracle or an unrestricted optimum.
- Pointwise 95% intervals for the nine-cell discovery map have n=4 and no multiplicity correction. Selection of a large cell does not provide independent confirmation. All 36 school contrasts, absolute returns and negative cells are supplied.
- The conditional eligible oral-contact probability 0.7 is uncalibrated; it is not success per launch/dive or first-versus-second field attacks. Model time/length, energetic profitability and biological cooperation are not calibrated by these food counts.
- The coarse timestep is 0.00125T; the fine timestep is 0.000625T. A 36T encounter therefore uses 28,800 or 57,600 numerical updates without changing duration. Coarse 72T is a secondary continuation on the same eight schools, with no fine 72T counterpart.
- Fish-state/contact/food diagnostics are descriptive associations. School identity also seeds readiness and private random streams; one stochastic setting per discovery school cannot separate a causal geometry effect from stochastic variation. A future held-out validation is a separate planned study, not a completed result here.

## Evidence snapshots and preservation

The current notebook imports `notebook_support_v5.py`, with `DATASET_2026-11-09_regime_v2.json` and `INPUT_MANIFEST_2026-11-09_regime_v2.json`. All previous inventories, manifests, case seals, support modules and reference figures remain unchanged. Prior notebooks and report versions remain under `snapshots/` and `reports/snapshots/`.

Current plotting source is `paper_figure_source_v5.py`, with `reference_figures_v5/`. Current figures go to `outputs/regime_figures/`; five new tables go to `outputs/regime_tables/`, while the 14 historical tables remain in their separate folders. `SOURCE_CLOSURE_2026-11-09_regime_v2.json` maps all 422 frozen inputs to bundled copies, including the 211 immutable files from the stopped v1 recorder attempt. Those stopped/partial cases are excluded from the 60-case map and inventory additions.

The original alternative-policy comparisons remain available in historical snapshots. The current main report follows one fixed exposed-prey dolphin rule; it studies partner presence and parameters rather than a C-versus-S comparison. Native C++ fish dynamics are inherited from [yangyushi/FishSim](https://github.com/yangyushi/FishSim); this project adds predator controllers, experiment harnesses and analysis.

## Supporting engineering evidence

[Timing engineering records](supporting_evidence/timing/README.md) retain the original three sealed 4T, 8T and 36T checks. They are verified separately and excluded from feeding inference. The late timing check produced one partial hold with unchanged captures and does not establish a timing benefit. Regime integration checks, stopped-attempt records and the additive runtime's bounded tests also remain engineering/provenance evidence rather than independent feeding replicates.

## Validation

The final publication receipt records execution of all 21 default cells from a fresh process and a relocated path containing spaces, with PYTHONPATH removed. Checks include all prior protected files, 60 corrected-v2 case seals, eight exact historical replays, 60 physical reviews, raw event counts, the nine-cell/36-pair reconstruction and frozen whole-school bootstrap with within-draw best-H selection. All four generated figures must match the report reference pixels on the tested environment; the active report has six body pages and references on page seven.

The 19 tables retain historical cohorts and new discovery settings separately. Default notebook execution imports no native simulator and advances zero native steps. The additive runtime manifest and source-built validation receipts are separate from the historical native binary and from the scientific feeding inventory. Analysis is designed for local Jupyter across platforms; actual environment and rendering limits are recorded in the validation receipts.
