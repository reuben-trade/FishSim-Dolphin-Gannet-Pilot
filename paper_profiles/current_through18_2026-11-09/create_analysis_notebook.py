"""Author main.ipynb for the current through-18 paper; execution is separate."""
from pathlib import Path
import nbformat

R=Path(__file__).resolve().parent
cells=[]
def md(t):cells.append(nbformat.v4.new_markdown_cell(t))
def code(t):cells.append(nbformat.v4.new_code_cell(t))
md('''# Feeding Frenzy — current-paper analysis through 18 gannets

**Entry point:** open `main.ipynb` from this analysis-profile folder, restart the kernel, and choose **Run All Cells**.

Default execution verifies the frozen input hashes, reconstructs individual returns and paired changes, checks the original interval table, rebuilds the four report figures and exports the numerical summaries under `outputs/`. It checks the original eight-school timestep comparison and the departure/launch-gap diagnostics. **No model runs, native FishSim imports or new bootstrap draws occur.**

The scope is the current paper's completed four-school **1/3/6/9/12/18-gannet** bank and the separate eight-school numerical check. The detailed departure analysis remains explicitly restricted to the **older 48 bird-bearing encounters at 1/3/6 birds**. No 24/36-bird pilot is pooled into this four-school map. A newer mutable repository is not read. Original confidence-interval endpoints are retained, not resampled. Figure 1 is archived, and r90 uses archived per-school time means rather than recomputing raw fish trajectories.

To install the tested analysis/kernel environment, use Python 3.12 and `python -m pip install -r requirements-analysis.lock`. The exact versions used for this executed copy are printed below. JupyterLab is an optional interface; the supplied validation runner uses `nbclient` and a fresh IPython kernel.''')
code('''from pathlib import Path
import json, sys
from IPython.display import display, HTML, Image, Markdown

ROOT = Path.cwd().resolve()
assert (ROOT / "analysis_support.py").is_file(), "Open this notebook from its current-paper analysis-profile folder."
sys.path.insert(0, str(ROOT))
import analysis_support as analysis
print(json.dumps(analysis.environment(), indent=2))
print("Simulation execution is absent from the default notebook.")''')
md('''## Verify the completed evidence

All fourteen frozen scientific inputs and thirteen departure exports are checked against their SHA-256 provenance records **before** outcomes are analysed. The seventeen frozen model documentation/receipt files are also checked without importing or running the model: 44 verified inputs in total. The departure JSON adds original launch clocks needed to check that long gaps were followed by resumed launches. No diagnostics runner or controller decisions are executed.''')
code('''inputs = analysis.verify_inputs()
print(f"Verified {len(inputs)} frozen input files; no repository fallback.")''')
md('''## Reconstruct absolute returns and paired species effects

There are 108 condition–school encounters (the original 60 plus 48 higher-count additions), including eight historical replays, on four previously examined schools. Mixed dolphins are compared with dolphin-only encounters at the same herding duration; mixed birds with bird-only encounters at the same count. School weights are equal. Replays, reused controls and repeated settings do not add independent schools.

The code computes all 72 school-level contrasts directly from capture counts and checks them against the saved paired table. It reconstructs all eighteen means and sign counts, then checks every saved mean and confidence endpoint against a separately archived figure receipt. **This validates retention of the original 95% pointwise intervals; it does not generate new bootstrap samples or establish out-of-sample coverage.** Exact aggregate ties are classified using integer capture sums before division.

The largest dolphin return is tied at H1/G9 and H1/G18 (127 versus 91 fish). H1/G9 uses fewer birds. H2/G12 benefits both species in all four schools (dolphins 110 versus 86; birds 57 versus 31) and also exceeds the best tested dolphin-only duration (91 fish). These settings were selected from the same map and are not independent confirmations.''')
code('''mapped = analysis.map_analysis()
display(HTML(analysis.html_table(mapped["cells"], [
    "H_T", "gannets", "D_alone_per_individual", "D_mixed_per_individual",
    "G_alone_per_individual", "G_mixed_per_individual", "D_mean_change", "G_mean_change", "both_gain_schools"])))
print(mapped["interval_policy"])
print("Reconstructed school effects and response means were exported to outputs/.")''')
md('''## Strike frequency and contact yield

Launches are initiated strikes; eligible contacts reach the geometric mouth-contact rule. Contact yield below is **pooled contacts / pooled launches**, rather than a mean of school-specific ratios. Counts retain the complete 36T encounter. Late launches may be incomplete. H changes trajectory as well as waiting time, so these descriptive contrasts do not isolate a causal mechanism.''')
code('''display(HTML(analysis.html_table(mapped["opportunities"], [
    "H_T", "gannets", "pooled_D_launches", "pooled_D_contacts", "pooled_contacts_per_launch",
    "D_captures", "G_captures"])))''')
md('''## Separate eight-school numerical check

The same eight H=2T/three-bird schools were examined at the original and halved timestep. They are eight schools, not sixteen. Original 97.5% marginal intervals apply to the two primary species comparisons; no fine-grid interval is added. The totals below always label **alone** and **mixed** explicitly. This check does not directly refine H1/G9 or H2/G12: numerical robustness of those favourable settings remains open.''')
code('''numerical = analysis.numerical_check()
display(HTML(analysis.html_table(numerical["rows"])))
print(numerical["scope"])''')
md('''## Depth access, launch pauses and terminal flock contact loss

This analysis is restricted to the **48 original bird-bearing encounters at one, three or six gannets**, rather than all 96 bird-bearing encounters in the expanded map. The code reconstructs rarity from their saved endpoint records and temporary gaps from the original launch clocks. It checks final cumulative counts and percentages in the saved timecourse exports, then verifies availability of complete 6T windows around the final committed attack end.

Whole-flock loss means all birds finish in search mode with no eligible new target. It differs from a final launch pause. The two loss cases show depth exclusion followed by target travel-feasibility failure after prey become shallow again. Globally informed birds may know where prey are while those prey remain ineligible for a new attack. This is not a demonstrated detection failure or a proof that dolphin surface herding is necessary.

Only one mixed run has full before/after windows around the final committed attack end; 24 are right-censored and 11 end too late. The single-school default is separate from pooled H1/six-bird totals.''')
code('''departure = analysis.departure_check()
print(json.dumps({k: departure[k] for k in [
    "bird_bearing_runs", "mixed_runs", "bird_only_runs", "schools", "whole_flock_loss_ids",
    "terminal_no_launch_final_6T_ids", "resumed_after_6T_gap_count", "full_final_attack_end_windows",
    "unavailable_reasons", "default"]}, indent=2))
display(HTML(analysis.html_table(analysis.table(ROOT / "departure_evidence/four_final_6T_no_launch_runs.csv"))))''')
md('''## Rebuild and display the four report figures

The builder reads only bundled completed exports. Figure 1 is the unchanged historical illustration; Figures 2–4 are redrawn from the completed through-18 counts, paired effects, original confidence endpoints and archived r90 summaries. Figure 2 retains actual numeric bird-count spacing. Per-bird returns generally decline but are not monotonic at every adjacent count. Generated PDF/PNG files and their data manifest are in `outputs/reproduced_figures/`.

Figure 3's panels are launches, contacts per launch, contacts per dolphin and r90. Figure 4's upper panels compare H1/G9 and H2/G12 on the four discovery schools; its lower panels are the separate eight-school H2/G3 grid check. Thin lines connect the same school, diamonds are means and bars are the stated intervals. A confidence interval is uncertainty in the paired mean, not the spread of individual schools.''')
code('''figures = analysis.render_figures()
captions = json.loads((ROOT / "captions.json").read_text()) if (ROOT / "captions.json").is_file() else {}
for name in figures["figures"]:
    display(Image(filename=str(Path(figures["path"]) / f"{name}.png")))
    if name in captions:
        display(Markdown(captions[name]))
print(json.dumps(figures, indent=2))''')
md('''## Actual model execution is a different workflow

Read **`MODEL_REPRODUCTION.txt`** and the exact documents in `model_reproduction/` for the frozen code/configuration snapshot, optional execution route and native ABI requirements. This compact analysis package does not include a portable full-ensemble model launcher.

The archived `run_current_model.py` route executes the **eight-school H2/three-bird numerical study**, not the eighteen-setting H×G map. The latter requires its frozen source-compatible checkpoint/configuration layout and preserved execution safeguards. The historical binary requires CPython 3.12, Linux x86-64, glibc 2.43 or newer and the documented C++/OpenMP runtime. The separate rebuilt Linux binary has bounded engineering checks, not a full feeding-ensemble validation. The public repository retains the prior v6 analysis and optional-model profile as versioned supplemental material.

There is no executable model cell here. This default notebook is the fast saved-output reproduction path and cannot start simulations. The model environment is distinct from the analysis-kernel versions printed above.''')
md('''## Completion checks

Input hashes are checked again after analysis. The verification receipt records the actual environment, deterministic comparisons, figure scope and zero model/bootstrap activity. The companion execution runner separately records completion in a fresh kernel, cell counts and elapsed wall time. A successful notebook execution is evidence for this saved-data path, not numerical convergence or biological validation.''')
code('''verification = analysis.finish(inputs, mapped, numerical, departure, figures)
assert verification["native_model_imports"] == 0
assert verification["native_simulation_steps"] == 0
assert verification["new_bootstrap_draws"] == 0
print(json.dumps({k: verification[k] for k in [
    "status", "input_files_verified", "paired_effects_checked", "map_cases", "map_schools",
    "numerical_check_schools", "departure_runs", "seconds_in_kernel",
    "native_model_imports", "native_simulation_steps", "new_bootstrap_draws"]}, indent=2))''')

n=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (current-paper analysis)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.13'}})
nbformat.write(n,R/'main.ipynb')
print('Wrote',len(cells),'cells; execution is separate.')
