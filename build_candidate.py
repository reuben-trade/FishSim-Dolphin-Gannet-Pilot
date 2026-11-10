"""Prepare this additive private profile; never writes to the public checkout."""
from pathlib import Path
import hashlib,json,shutil
import nbformat
ROOT=Path(__file__).resolve().parent
BASE=Path('/home/venture/FishSim-Dolphin-Gannet-Pilot')
DISC=BASE/'paper_profiles/current_through36_D24_2026-11-10'
PORT=Path('/home/venture/uwa/complex-systems/FishSim-RL/research/validation_portable_export_2026-11-10')
REPORT=Path('/home/venture/uwa/complex-systems/FishSim-RL/research/validation_reporting_2026-11-10')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
if not (ROOT/'discovery_profile').exists():
    shutil.copytree(DISC,ROOT/'discovery_profile',ignore=shutil.ignore_patterns('__pycache__','.ipynb_checkpoints'))
(ROOT/'validation_tools/validation_reporting').mkdir(parents=True,exist_ok=True)
shutil.copy2(PORT/'portable_reader.py',ROOT/'validation_tools/portable_reader.py')
for n in ('render.py','gate.py','source_pins.json'):shutil.copy2(REPORT/n,ROOT/'validation_tools/validation_reporting'/n)
shutil.copy2(BASE/'requirements-analysis.txt',ROOT/'requirements-analysis.txt')
shutil.copy2(DISC/'requirements-analysis.lock',ROOT/'requirements-analysis.lock')
for source,name in [(Path('/tmp/FishSim_Portable_Primary_Independent_Review_2026-11-10_v2.json'),'portable_reader_peer_v2.json'),(Path('/home/venture/FishSim_Primary_Model_Operational_Peer_Review_2026-11-10_v2.json'),'primary_model_operational_peer_v2.json'),(Path('/tmp/FishSim_Primary_Model_Physical_Source_Review_2026-11-10_v1.json'),'primary_model_physical_source_peer_v1.json')]:
    target=ROOT/'provenance'/name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
old=json.loads((BASE/'MAIN_NOTEBOOK_PROFILE.json').read_text())
tables={Path(p).name:h for p,h in old['csv_tables'].items()}
figs={f'{n}.{e}':sha(DISC/'figures'/f'{n}.{e}') for n in ('fig1_model','fig2_returns','fig3_opportunities') for e in ('png','pdf')}
profile=dict(schema='fishsim_final_paper_notebook_profile_v1',status='PRIVATE_PREPARATION_PRIMARY192_PENDING',notebook='main.ipynb',
    discovery=dict(root='discovery_profile',tables=tables,figures=figs,scope='Completed through36 D12 map, selected D24 follow-up, separate eight-school H2/G3 numerical check and older48 bird-bearing departure subset. Discovery is not pooled with validation.'),
    validation=dict(kind='PENDING',snapshot_manifest=None,snapshot_manifest_sha256=None,export_receipt_sha256=None,independent_final_sha256=None,metadata_sidecar_sha256=None,root_activation=None,root_activation_sha256=None,
        expected_cases=192,independent_school_clusters=16,nested_labels=2,primary_grid='fine',primary_intervals='97.5% Student t, df15, critical2.4898797034798923',bootstrap='cached50000 PCG64 seed8611030; zero new draws',
        W='mean((effect_label1-effect_label2)^2/2)',conditional_MCSE='sqrt(W/32); not added again to schoolSD/4',
        publication='PENDING exact192+original8ff FINAL+5cc metadata PASS+root activation; no partial96/144 accepted'),
    paper_figures=dict(figure1='Archived PNG/PDF unchanged',figures2_to3='Regenerated privately by unchanged discovery builder; archived assets remain byte-identical',figure4='Future accepted192 paired_grid_effects from unchanged frozen renderer4040; absolute_and_partner remains supplemental only'),
    optional_native=dict(enabled=False,stage='PENDING_SEPARATE_ARTIFACT_ZERO_4T_36T_CERTIFICATION',entrypoint='model_examples/primary_192/run_primary_model.py',setup='model_examples/primary_192/PRIMARY_MODEL_SETUP.md',source_entry_sha256='eb02a2e45258b120c86c082f4b750ebc49111c07a65a19f9f139a89e99c22f7e',combined_source_peer_sha256='e6e163278d4f2476138acef4fa7cd9c6094d448805807bb58566adc22c742d67',release_certificate_sha256=None,route='Reviewed primary-H1/G36 v2 source route installed; native release PENDING artifact-specific actual zero/4T/36T engineering'),
    source_context=dict(discovery_profile_sha256=sha(BASE/'MAIN_NOTEBOOK_PROFILE.json'),old_paper_pdf_sha256=old['report_sha256'],portable_reader_sha256=sha(PORT/'portable_reader.py'),renderer_sha256=sha(REPORT/'render.py')))
put(ROOT/'FINAL_NOTEBOOK_PROFILE.json',profile)
cells=[]
def md(s):cells.append(nbformat.v4.new_markdown_cell(s))
def code(s):cells.append(nbformat.v4.new_code_cell(s))
md('''# Feeding Frenzy

Open **main.ipynb** from this folder, select a Python 3 kernel, restart it, and choose **Run All Cells**. Install the analysis environment with `python -m pip install -r requirements-analysis.txt`; see `SETUP.md` for local Jupyter instructions.

The notebook reproduces the completed discovery analysis and adds the separate, prespecified sixteen-school validation when its final accepted snapshot is available. Data status is printed below. Default execution reads saved data, takes **zero model steps**, and makes **zero new bootstrap draws**. Model replay is a separate optional workflow, disabled below.''')
code('''from pathlib import Path
import json, os, sys
from IPython.display import display, HTML, Image, Markdown

PROJECT_ROOT = Path.cwd().resolve()
assert (PROJECT_ROOT / "FINAL_NOTEBOOK_PROFILE.json").is_file(), "Open main.ipynb from this folder."
sys.path.insert(0, str(PROJECT_ROOT))
from integration import Session, html_table
PROFILE_FILE = os.environ.get("FISHSIM_NOTEBOOK_PROFILE", "FINAL_NOTEBOOK_PROFILE.json")
session = Session(PROJECT_ROOT, PROFILE_FILE)
print(session.backend_status)
print(f"Verified {session.input_files} bundled files. Saved-data analysis only; zero native steps and new bootstrap draws.")
if session.synthetic:
    display(Markdown("**SYNTHETIC TEST DATA ONLY — NOT STUDY RESULTS.**"))''')
md('''## Discovery results

The main map contains twenty-four H×gannet settings on four previously examined schools, with the completed 1/3/6/9/12/18/24/36-gannet counts. The additional D24 check uses the same four schools and exact reused controls. These selected results remain discovery evidence; the validation schools below are separate.

The compact display highlights H1/G36 and H2/G12. The complete map, opportunity decomposition, population endpoints, older forty-eight-run departure subset and separate eight-school H2/G3 numerical check remain accessible in nine exported CSVs. All nine are reconstructed and checked against the original deterministic exports.''')
code('''discovery = session.discovery()
selected = [r for r in discovery["mapped"]["cells"] if (r["H_T"], r["gannets"]) in ((1.0, 36), (2.0, 12))]
display(HTML(html_table(selected, ["H_T", "gannets", "D_alone_per_individual", "D_mixed_per_individual", "G_alone_per_individual", "G_mixed_per_individual", "D_mean_change", "G_mean_change", "both_gain_schools"])))
display(HTML("<details><summary>Selected D24 population endpoints</summary>" + html_table(discovery["population"]["endpoints"]) + "</details>"))
print("Nine discovery tables:", discovery["table_root"].relative_to(PROJECT_ROOT))
print(discovery["departure"]["scope"])
print(discovery["numerical"]["scope"])''')
md('''## Figures 1–3

Figure 1 is the unchanged archived illustration. Figures 2 and 3 are regenerated from the completed saved evidence with the unchanged discovery builder and retained interval caches. Gannet counts use their actual numerical spacing. Higher group captures and per-individual food are distinct outcomes; per-bird returns generally decline without being monotonic at every adjacent count. Rebuilding takes place in this run's fresh output directory; the archived PNG/PDF pairs are never overwritten. The older helper's numerical Figure 4 is not used for the new final-paper Figure 4.''')
code('''for path in discovery["figures"]:
    display(Image(filename=str(path)))
    print(path.relative_to(PROJECT_ROOT))''')
md('''## Independent validation

The complete design is sixteen prepared schools × two nested randomness labels × two grids × three matched presence arms = **192 cases**. The two labels are averaged within each school; the independent sample size is sixteen, rather than thirty-two. Dolphins number twelve and gannets thirty-six, with H=1 and nominal 36T encounters. Discovery cases are not pooled.

Partner gains are `(mixed captures − alone captures) / species count`, in fish per individual over 36T. Fine-grid dolphin and gannet endpoints are primary. Their prespecified 97.5% two-sided Student t intervals use df=15 and critical value 2.4898797034798923; the joint criterion requires both lower bounds above zero. Coarse and paired fine-minus-coarse estimates are secondary. A non-passing joint criterion remains a valid reportable result.

SD is the spread of the sixteen school means; SE=SD/4. W and conditional Monte Carlo SE describe nested-label variation. **MCSE is not added to SE again.** Cached 50,000-draw whole-school bootstrap intervals are a separate sensitivity and are checked without new sampling. Missing cells or partial96/144 prefixes cannot enter this final section.''')
code('''if session.validation_result is None:
    print("Validation pending: no final estimates, confidence intervals or Figure 4 are asserted.")
else:
    if session.synthetic:
        display(Markdown("**SYNTHETIC TEST DATA ONLY — NOT STUDY RESULTS.**"))
    overview = session.validation_overview()
    display(HTML(html_table(overview, ["contrast", "mean", "school_SD", "SE", "t_97_5_low", "t_97_5_high", "n_schools"])))
    display(HTML("<details><summary>Nested-label variation, signs and cached bootstrap sensitivity</summary>" + html_table(overview, ["contrast", "n_worlds", "W", "conditional_MCSE", "school_signs", "cached_bootstrap_97_5"]) + "</details>"))
    print("Fine-grid joint criterion:", session.validation_result["primary_joint_criterion_met"])
    print(session.validation_result["bootstrap_verification"])''')
md('''## Validation tables and Figure 4

Four additive CSVs retain all192 case counts, all16 school vectors, all64 school×label×grid world records, and all six estimate/SD/SE/t/W/MCSE/bootstrap summaries. The nested world rows are not independent schools. Group counts, food per individual and food per T have separate columns.

When final data are accepted, Figure 4 shows paired school effects at the original and halved timestep, with nested-label points and the prespecified t intervals. It is generated by the unchanged frozen renderer from the verified portable-reader payload. The accompanying absolute-return panel is supplemental, not an additional numbered paper figure. Synthetic test figures carry a visible watermark and never enter the paper.''')
code('''validation_exports = session.export_validation()
if validation_exports is not None:
    display(Image(filename=str(validation_exports["figure4"])))
    print("Four validation tables:", validation_exports["tables"].relative_to(PROJECT_ROOT))
    print("Figure 4 PNG/PDF:", validation_exports["figure4"].relative_to(PROJECT_ROOT))
    # Full in-memory records are available without scrolling through them by default:
    validation_cases = session.validation_result["counts"]
    validation_school_vectors = session.validation_result["school_points"]
    validation_world_records = session.validation_result["world_points"]
    assert (len(validation_cases), len(validation_school_vectors), len(validation_world_records)) == (192, 16, 64)
else:
    print("Final validation tables and Figure 4 remain pending.")''')
md('''## Optional model replay

The saved-data analysis above cannot start the simulator. A separate reviewed primary H1/G36 frontend supplies explicit 4T and 36T requests and the fixed192-case inventory. Its source review is not a native replay certificate: actual artifact-specific zero, short and full-horizon checks are still required before release.

Read the bundled [primary model setup](model_examples/primary_192/PRIMARY_MODEL_SETUP.md) for the separate workflow. The source-reviewed entry point is `model_examples/primary_192/run_primary_model.py`, called with `--package-root PROJECT_ROOT`; production preparation takes the actual `SNAPSHOT.json` file. The optional route below remains disabled. After publication, its setup document will give the ordinary local prepare → zero-check → replay commands; the frontend records the user's opt-in automatically. The professor will not need to write an approval JSON. The older H1/G9 and H2/G12 examples remain historical supplemental workflows.''')
code('''RUN_NATIVE = False
if RUN_NATIVE:
    raise RuntimeError("The optional primary replay is not released by this preparation profile. Use its separately certified setup after publication.")
print("Optional native replay disabled.")
print(session.profile["optional_native"]["route"])
print("Primary replay source:", session.profile["optional_native"]["entrypoint"])
print("Setup:", session.profile["optional_native"]["setup"])''')
md('''## Completion

The receipt records the data kind, exact profile, table/figure scope, independent-school count and zero model/resampling activity. Notebook execution validates this saved-data reproduction path; it does not establish biological realism or native replay fidelity.''')
code('''receipt = session.finish()
assert receipt["native_model_imports"] == receipt["native_steps"] == receipt["new_bootstrap_draws"] == 0
print(json.dumps(receipt, indent=2))
print("Outputs:", session.output.relative_to(PROJECT_ROOT))''')
for index, cell in enumerate(cells):
    cell['id']='cell_'+hashlib.sha256((str(index)+'\n'+cell['source']).encode()).hexdigest()[:16]
book=nbformat.v4.new_notebook(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python')))
nbformat.write(book,ROOT/'main.ipynb')
# The backend profile is intentionally mutable after final acceptance; the
# immutable package manifest pins source, notebook and complete discovery bytes.
files={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.relative_to(ROOT).parts[0] not in ('outputs','execution_proofs','.headless','proofs') and '__pycache__' not in p.parts and p.name not in ('PACKAGE_INPUTS.json','FINAL_NOTEBOOK_PROFILE.json') and not p.name.startswith(('HANDOFF','CANDIDATE_'))}
put(ROOT/'PACKAGE_INPUTS.json',dict(schema='fishsim_final_notebook_immutable_inputs_v1',files=files))
print(json.dumps(dict(cells=len(cells),code_cells=sum(c.cell_type=='code' for c in cells),inputs=len(files),discovery_tables=len(tables),figure_pairs=3)))
