<!-- Scientific overview preserved from the repository README, 9 November 2026. Relative links rebased for docs/. -->

# FishSim: dolphin–gannet pilot and regime map

Open [**main.ipynb**](../main.ipynb) and choose **Run → Run All Cells** from the repository root. Its **10 code cells** verify preserved inputs, reconstruct the current paper’s saved results, display four matching figures and export six summary tables. Default execution takes **zero native steps and generates no new bootstrap draws**. Two optional bounded model-example cells remain off by default. Saved outputs are included.

The default now matches the current “Who Benefits?” manuscript through eighteen gannets. The complete earlier raw-evidence workflow remains runnable as [main_2026-11-09_v6.ipynb](../main_2026-11-09_v6.ipynb), with its 21 code cells, 19 tables and prior four-figure report archived separately.

**Main finding:** original shared-rule pilots gave dolphin gains of **17.1% and 16.1%**. The completed balanced map has **14 positive, one zero and three negative** mean same-H dolphin responses across all 18 tested settings. The largest mixed dolphin total tied at **H=1T with nine or eighteen gannets: 91→127 captures (+39.6%)**, with dolphin gains in all four schools at both counts. Nine birds are reported by the fewer-birds tie convention, not as a confirmed optimum. At H=1T/G=9, gannets changed 34→52, with three school gains and one tie.

Both species gained in every school at H=2T with six, twelve or eighteen birds. **H=2T/G=12 gave dolphins 86→110 and gannets 31→57**; it also exceeded the stronger best-tested H=1T dolphin-only benchmark 91→110, with a positive exploratory pointwise interval. Largest dolphin return and consistent joint gains are distinct questions.

The full map uses **four previously observed schools and one capture-stream setting**, with exploratory pointwise intervals. It retains every setting and sign. The original positive follow-up used two fresh schools under two settings; those original totals have not been replaced by replay aggregates. The independent eight-school check remains separate: refining the timestep changed mean dolphin effects from +1 to 0 and gannet effects from +5.125 to +2.5 captures per school. The fine dolphin mean combines **four positive, three negative and one zero school effect**. The original positive cohorts and the new map were not rerun on the fine grid. Numerical convergence and general mutual facilitation remain unestablished.

Read the [current report](../reports/current/Feeding_Frenzy_Working_Draft.pdf) or [complete response map](../reference_figures_v6/fig3_regime_map.png). The inventory contains **180 full feeding execution records**: 132 preserved records plus 48 new higher-count encounters. The earlier corrected-v2 sweep includes **eight exact historical replays**. The expanded discovery map uses 60 retained outcomes plus 48 new encounters on the SAME four schools; the first-school 12-case pilot is a subset of those 48. Replays, shared controls, grid repetitions and longer horizons do not add independent schools. The stopped v1 recorder attempt is retained only as immutable supporting provenance.

## Complete discovery map

All 18 mixed settings are retained below. Captures sum the same four previously observed schools and one capture setting 61001. D controls have the same H; G controls have the same bird count. The stronger D-only benchmark is H=1T, 91 captures. Pointwise uncertainty and all 72 school contrasts are in Figure 3 and the notebook.

| H (T) | Gannets | D alone → mixed | Same-H D change | D change vs best H | G alone → mixed | Both gain |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 91 → 98 | +7.7% | +7.7% | 13 → 12 | 0/4 |
| 1 | 3 | 91 → 107 | +17.6% | +17.6% | 24 → 22 | 1/4 |
| 1 | 6 | 91 → 113 | +24.2% | +24.2% | 24 → 37 | 3/4 |
| 1 | 9 | 91 → 127 | +39.6% | +39.6% | 34 → 52 | 3/4 |
| 1 | 12 | 91 → 126 | +38.5% | +38.5% | 31 → 37 | 3/4 |
| 1 | 18 | 91 → 127 | +39.6% | +39.6% | 31 → 44 | 2/4 |
| 2 | 1 | 86 → 90 | +4.7% | -1.1% | 13 → 13 | 0/4 |
| 2 | 3 | 86 → 95 | +10.5% | +4.4% | 24 → 29 | 1/4 |
| 2 | 6 | 86 → 103 | +19.8% | +13.2% | 24 → 53 | 4/4 |
| 2 | 9 | 86 → 103 | +19.8% | +13.2% | 34 → 42 | 2/4 |
| 2 | 12 | 86 → 110 | +27.9% | +20.9% | 31 → 57 | 4/4 |
| 2 | 18 | 86 → 103 | +19.8% | +13.2% | 31 → 75 | 4/4 |
| 3 | 1 | 73 → 68 | -6.8% | -25.3% | 13 → 13 | 0/4 |
| 3 | 3 | 73 → 72 | -1.4% | -20.9% | 24 → 30 | 1/4 |
| 3 | 6 | 73 → 78 | +6.8% | -14.3% | 24 → 51 | 2/4 |
| 3 | 9 | 73 → 77 | +5.5% | -15.4% | 34 → 47 | 0/4 |
| 3 | 12 | 73 → 73 | +0.0% | -19.8% | 31 → 66 | 2/4 |
| 3 | 18 | 73 → 65 | -11.0% | -28.6% | 31 → 48 | 1/4 |

## Local setup: current-paper analysis and figures

Python 3.12 was tested. The exact authoring environment is recorded in [the profile lock file](../paper_profiles/current_through18_2026-11-09/requirements-analysis.lock); the general requirements below resolve compatible local dependencies. From a terminal opened in this folder:

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

For the v6 parameter-map model, [short matched examples](../V6_MODEL_SETUP.md) are now available through `run_v6_example.py`: H1/G9 for 4T or H2/G12 for 2T. The notebook prints a native-free plan and leaves execution disabled. On the tested Linux x86-64 CPython 3.12 environment, both binaries passed 108 exact actual starts and ten bounded cases totalling 20,000 steps. The frozen preparation records retain their original pre-validation status strings; separate dated receipts record these completed checks. This frontend does not run a full 36T ensemble or add feeding-effect evidence.

The additive [current-model setup](../CURRENT_MODEL_SETUP.md) documents `run_current_model.py`. It executes the existing eight-school **H=2 coarse/fine replication**, rather than the newer H × G sweep. It does not execute the H×G sweep, including H=1T with nine or eighteen birds. That runner remains available independently; the notebook now prints the v6 example plan and leaves `RUN_V6_MODEL = False` by default. Its optional demonstration uses 0.5T or 4T; neither is a feeding-benefit experiment.

The original Linux host passed 2,400 bounded integration steps. A separately source-built Linux amd64 image passed compilation/import, 48 initial-state checks and six bounded encounters totalling 15,200 steps through BuildKit. The image checks had two failed bird contacts and no captures, so successful removal and a full feeding ensemble remain untested with that binary. The host Docker bind-mount command and Windows/macOS/ARM execution have not been tested end to end. Source/build instructions and compact receipts are included; the large private OCI image/cache is excluded.

The unchanged historical `run_model.py` remains available separately for the original 36T D/DG pair or original two-school/two-setting eight-case replication. Its 0.5T quick pair checks integration and ends before the 2T herding interval. The supplied historical binary requires **CPython 3.12, Linux x86-64, glibc 2.43 or newer, compatible C++ runtime and OpenMP**. Read [NATIVE_SETUP.md](../NATIVE_SETUP.md) before using it. The historical source archive, binary, hash declarations and earlier instructions remain unchanged; a rebuilt binary has separate execution provenance.

## Scientific interpretation

- The dolphin baseline uses the **same rule and H without gannets**. H is continuous near-prey pressure, varied over 1, 2 and 3T; it does not certify completed herding or complementary pod coverage. All travel, herding, failures and recovery count in feeding return.
- The exposed-prey preference ranks feasible fish by low neighbour count within radius 2. Dense fish remain eligible, and outward motion is not required. The dolphin controller has no bird-count/dive cue or post-dive capture bonus.
- Gannets identify density clusters globally within depth limits, sample clusters by accessible fish count, and target a dense accessible location. Counts 1/3/6/9/12/18 use a nested roster at the original three launch locations. Counts 9/12/18 place 3/4/6 birds at each site; count also changes coverage or local multiplicity. Predator body-spacing avoidance is absent.
- Primary effects compare mixed dolphins with same-H D-only controls. Gannet effects use per-bird returns against count-matched G-only controls reused across H. A stronger secondary comparison selects the best-tested D-only H across the four-school bank and reselects it within each whole-school bootstrap draw. This is not a per-school oracle or an unrestricted optimum.
- Pointwise 95% intervals for the 18-cell discovery map have n=4 and no multiplicity correction. Selection of a large cell does not provide independent confirmation. All 72 school contrasts, absolute returns and negative cells are supplied.
- The conditional eligible oral-contact probability 0.7 is uncalibrated; it is not success per launch/dive or first-versus-second field attacks. Model time/length, energetic profitability and biological cooperation are not calibrated by these food counts.
- The coarse timestep is 0.00125T; the fine timestep is 0.000625T. A 36T encounter therefore uses 28,800 or 57,600 numerical updates without changing duration. Coarse 72T is a secondary continuation on the same eight schools, with no fine 72T counterpart.
- Fish-state/contact/food diagnostics are descriptive associations. School identity also seeds readiness and private random streams; one stochastic setting per discovery school cannot separate a causal geometry effect from stochastic variation. A future held-out validation is a separate planned study, not a completed result here.

## Evidence snapshots and preservation

The current paper profile is [paper_profiles/current_through18_2026-11-09](../paper_profiles/current_through18_2026-11-09/README.md). It checks 44 frozen scientific/departure/model-document inputs and all preserved package hashes, reconstructs 108 outcomes and 72 paired effects, and retains the original confidence endpoints without new resampling. Figure1 is archived; Figures2–4 are redrawn from completed exports. School-radius values are retained time means, rather than newly reconstructed trajectories. The 48-run departure diagnostic covers only the older 1/3/6-bird subset; the separate numerical check uses the same eight H2/G3 schools on both grids.

The current default exports six CSVs under `paper_profiles/current_through18_2026-11-09/outputs/`. It does not rerun the full raw-event reconstruction. That earlier workflow remains in `main_2026-11-09_v6.ipynb`, `notebook_support_v6.py`, the preserved high-count inventory/manifest and `reference_figures_v6/`. Its report is archived under `reports/snapshots/2026-11-09_v6_through18/`. All 8,028 earlier scientific inputs and 56 additive model files remain byte-identical. Versioned manifests, earlier notebooks, case seals, the stopped-v1 provenance and all unfavourable settings remain included.

The original alternative-policy comparisons remain historical. The current paper uses one fixed exposed-prey dolphin rule. Native C++ fish dynamics are inherited from [yangyushi/FishSim](https://github.com/yangyushi/FishSim); this project adds predator controllers, experiment harnesses and analysis.

## Supporting engineering evidence

[Timing engineering records](../supporting_evidence/timing/README.md) retain the original three sealed 4T, 8T and 36T checks. They are verified separately and excluded from feeding inference. The late timing check produced one partial hold with unchanged captures and does not establish a timing benefit. Regime integration checks, stopped-attempt records and the additive runtime's bounded tests also remain engineering/provenance evidence rather than independent feeding replicates.

## Validation

The current profile is checked in a fresh IPython kernel, from a relocated Git checkout with spaces in its path and PYTHONPATH removed. Canonical code is pinned before kernel creation, so an edited native toggle or subprocess command causes validation to stop. Checks cover preserved inputs, all 44 profile files,108 condition-school outcomes,72 paired contrasts, six deterministic CSV exports and four figure pixel comparisons against the current report. The current compiled paper has five body pages and ten references on page six.

The compact profile checks saved interval endpoints against an archived plot receipt; it does not create new bootstrap draws or rederive raw fish trajectories. The separately archived v6 notebook retains the broader raw-event/seal reconstruction and resampling checks. Neither workflow imports the native simulator by default. Passing saved-data reproduction establishes this execution path, not numerical convergence, biological validation or performance on untested platforms.

The active entry is `main.ipynb`. See [NOTEBOOK_MAINTENANCE.md](../NOTEBOOK_MAINTENANCE.md) for the versioned generator and report profile. Historical generators and snapshots retain their original names.
