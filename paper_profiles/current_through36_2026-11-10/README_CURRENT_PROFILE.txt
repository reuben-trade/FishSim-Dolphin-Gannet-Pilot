Feeding Frenzy — current-paper analysis through 36 gannets
10 November 2026

Open main.ipynb from this folder and choose Restart Kernel and Run All.
The public-repository maintainer may place this profile in a versioned subfolder
and make the repository-root main.ipynb select that folder in its first cell.

Setup with Python 3.12:
  python -m venv .venv
  .venv/bin/python -m pip install -r requirements-analysis.lock
  .venv/bin/python -m pip install jupyterlab
  .venv/bin/python -m jupyter lab

JupyterLab is an optional interface. A headless fresh-kernel check is:
  .venv/bin/python execute_notebook.py

DEFAULT SCOPE
The completed map contains four previously examined schools, minimum herding
durations H={1,2,3}T, positive gannet counts G={1,3,6,9,12,18,24,36}, and matched
single-species controls. Its 140 condition–school encounters contain 96 mixed
school-level contrasts and eight archived replays. Replays, repeated settings
and shared controls add no independent schools.

The notebook verifies every frozen input against the supplied SHA-256
provenance, including thirteen departure exports and seventeen frozen model
documentation/receipt files. It prints the exact verified input count.
It independently reconstructs integer capture contrasts, normalised returns,
equal-school means, sign counts and pooled contact yields. Saved uncertainty
endpoints are checked against the hash-bound independent raw-reader
reconstruction for all twenty-four settings; the older plot receipt is checked
only for its eighteen-setting scope. The upstream reader verified the frozen
10,000-draw procedure; this compact notebook generates zero bootstrap draws.
No new bootstrap samples, model imports or native simulation steps occur.

Numerical-check scope: the distinct eight-school H2/G3 comparison at original
and halved timestep; these are eight schools, not sixteen, and they do not
refine the highlighted H1/G36 and H2/G12 settings.

Departure scope: only the original 48 bird-bearing encounters at G1/G3/G6
(36 mixed and twelve bird-only), not the expanded map's 128 bird-bearing
encounters. Launch gaps, terminal search state and complete before/after
windows are checked from the retained detailed exports.

FIGURES
Figure 1 is reused unchanged from its archived historical illustration.
Figures 2–4 are redrawn from frozen completed counts, paired effects, saved
interval endpoints and independently verified per-school r90 time averages.
The upstream reader checked every raw trajectory frame against saved r90
metrics on all 140 cases with zero maximum error. Raw fish trajectories and
bootstrap draws are not recomputed in this compact profile.
The plot manifest identifies every input and plotted quantity. Figure 2 and
Figure 3 retain actual numeric gannet-count spacing through thirty-six.
Figure 4 upper panels use four-school H1/G36 and H2/G12; lower panels use the
different eight-school H2/G3 numerical check. These settings are not pooled.

OUTPUTS
outputs/reconstructed_school_effects.csv
outputs/reconstructed_response_means.csv
outputs/opportunity_decomposition.csv
outputs/numerical_sensitivity.csv
outputs/terminal_contact_loss.csv
outputs/complete_default_before_after_windows.csv
outputs/reproduced_figures/ (four PNG/PDF pairs and figure_manifest.json)
outputs/analysis_results.json
outputs/analysis_verification.json
outputs/notebook_execution_verification.json (fresh-kernel runner only)

MODEL EXECUTION
This saved-data notebook has no executable model cell. Read
MODEL_REPRODUCTION.txt and model_reproduction/ for the separate historical
execution route and native ABI constraints. The archived run_current_model.py
route is the eight-school H2/G3 study, not this twenty-four-setting map. The
public repository retains the earlier v6 analysis/optional-model profile as
supplemental material. No new model compatibility or ensemble result is
established by passing this saved-data notebook.

PAPER SOURCE
manuscript.json is the structured prose for the through-36 current-paper
update. render_report.py rebuilds main.tex, manuscript.txt and captions.json.
main.tex compiles offline with the cached Tectonic installation. main.pdf
contains five body pages plus one reference page, four figures and ten
references at the unchanged 10pt body font. Publication to the native Google
Doc and repository is a separate maintainer step and is not asserted here.
