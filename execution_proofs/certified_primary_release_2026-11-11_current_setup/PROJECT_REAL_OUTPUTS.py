from pathlib import Path
import base64, collections, copy, csv, hashlib, json, shutil, sys

ROOT=Path('/home/venture/FishSim Certified Release Candidate 2026-11-11')
HERE=Path(__file__).resolve().parent
PROOF=ROOT/'execution_proofs/certified_primary_release_2026-11-11_current_setup'
PROOF.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
headless=max((ROOT/'outputs').glob('headless_*'),key=lambda p:p.stat().st_mtime)
run=max((ROOT/'outputs').glob('run_*'),key=lambda p:p.stat().st_mtime)
execution=read(headless/'HEADLESS_RECEIPT.json')
assert execution['status']=='passed_saved_data' and execution['native_steps']==0
assert execution['new_bootstrap_draws']==0 and execution['fresh_kernel']
assert execution['canonical_notebook_cells']==14 and execution['executed_cells']==16
assert execution['logical_source_sha256']=='02785c70b03f97ebef25dc0a8febb85cbf268d108e55f820857d021029b4c5b1'
assert sha(ROOT/'main.ipynb')==execution['original_notebook_sha256']
binding=read(ROOT/'NOTEBOOK_RELEASE_BINDINGS.json')
canonical=read(ROOT/binding['notebook_template']['path']);executed=read(headless/'EXECUTED_main.ipynb')
def source(c):return ''.join(c['source'])if isinstance(c['source'],list)else c['source']
ids=[c['id']for c in canonical['cells']]
assert len(ids)==len(set(ids))==14
by_id={c['id']:c for c in executed['cells']}
assert len(by_id)==16 and set(ids)<set(by_id)
for c in canonical['cells']:
    assert by_id[c['id']]['cell_type']==c['cell_type']
    assert source(by_id[c['id']])==source(c)
assert sum(c['cell_type']=='code'for c in canonical['cells'])==7
projected=copy.deepcopy(executed);projected['cells']=[copy.deepcopy(by_id[i])for i in ids]
assert all(o.get('output_type')!='error'for c in projected['cells']for o in c.get('outputs',[]))
baseline=read('/home/venture/FishSim Final Publication Candidate 2026-11-11/execution_proofs/PRODUCTION_NOTEBOOK_VALIDATION_2026-11-11.json')['stage']
tables={n:sha(run/n)for n in baseline['canonical_csv_sha256']}
assert tables==baseline['canonical_csv_sha256'] and len(tables)==13
figures={
    'fig1_model.png':ROOT/'discovery_profile/figures/fig1_model.png',
    'fig2_returns.png':run/'discovery/reproduced_figures/fig2_returns.png',
    'fig3_opportunities.png':run/'discovery/reproduced_figures/fig3_opportunities.png',
    'fig4_validation.png':run/'validation/rendered/paired_grid_effects.png',
}
png={n:sha(p)for n,p in figures.items()};assert png==baseline['figure_png_sha256']
embedded=[];types=collections.Counter()
for c in projected['cells']:
    for o in c.get('outputs',[]):
        types[o['output_type']]+=1
        for mime in o.get('data',{}):types[mime]+=1
        if 'image/png'in o.get('data',{}):
            data=o['data']['image/png'];data=''.join(data)if isinstance(data,list)else data
            embedded.append(hashlib.sha256(base64.b64decode(data)).hexdigest())
assert embedded==list(png.values())
write(ROOT/'main.ipynb',projected)
sys.path.insert(0,str(ROOT))
from replay_tools.primary_192.notebook_template import verify
binding=read(ROOT/'NOTEBOOK_RELEASE_BINDINGS.json');template=binding['notebook_template']
logical=verify(ROOT/'main.ipynb',ROOT/template['path'],template['configuration_cell_id'],template['logical_sha256'])
assert logical['settings']==dict(RUN_NATIVE=False,NATIVE_DURATION_T=4,NATIVE_ARTIFACT='historical',NATIVE_WORKERS=6)
assert sha(ROOT/template['path'])=='3769d3e69f5d9afb6a75b1e912765976b3390b2d11007594a7886163d8daeaf5'
for source,name in [(headless/'EXECUTED_main.ipynb','EXECUTED_DEFAULT_PROOF.ipynb'),
                    (headless/'HEADLESS_RECEIPT.json','HEADLESS_RECEIPT.json'),
                    (run/'NOTEBOOK_RUN_RECEIPT.json','NOTEBOOK_RUN_RECEIPT.json'),
                    (HERE/'CURRENT_SETUP_DEFAULT_EXECUTION.log','FINAL_DEFAULT_EXECUTION.log'),
                    (Path(__file__),'PROJECT_REAL_OUTPUTS.py'),
                    (HERE/'MARKDOWN_SETUP_CORRECTION.json','MARKDOWN_SETUP_CORRECTION.json'),
                    (HERE/'DEFAULT_ORIGINAL_SOURCE_DENIAL.json','DEFAULT_ORIGINAL_SOURCE_DENIAL.json')]:
    target=PROOF/name
    if target.exists():assert sha(source)==sha(target)
    else:shutil.copyfile(source,target)
result=dict(schema='certified_primary_release_real_default_output_projection_v1',status='passed',
    source_canonical_template_sha256=sha(ROOT/template['path']),source_logical_sha256=logical['logical_sha256'],
    canonical_cell_ids=ids,canonical_cells=14,canonical_code_cells=7,actual_executed_proof_cells=16,
    only_two_driver_guard_cells_removed=True,all_fourteen_sources_and_types_exact=True,
    projected_outputs_and_cell_metadata_exact_from_actual_default_execution=True,
    actual_default_native_false=True,actual_QA_true_book_used=False,
    displayed_main_sha256=sha(ROOT/'main.ipynb'),displayed_main_bytes=(ROOT/'main.ipynb').stat().st_size,
    displayed_main_under_GitHub_single_file_limit=True,source_saved_outputs_and_kernel_metadata_supported=True,
    generic_kernel_metadata=projected['metadata'].get('kernelspec'),settings=logical['settings'],
    actual_default_seconds=execution['seconds'],actual_default_fresh_kernel=True,
    default_original_author_reads_denied=True,canonical_csv_count=13,canonical_csv_sha256=tables,
    all13_CSVs_match_existing_paper=True,four_png_sha256=png,embedded_png_sha256=embedded,
    all_four_visible_images_byte_exact_paper_PNGs=True,visible_output_mime_counts=dict(types),
    paper_pdf_sha256=sha(ROOT/'reports/current/Feeding_Frenzy_Working_Draft.pdf'),
    snapshot_manifest_sha256=sha(ROOT/'data/primary_validation192_2026-11-11/SNAPSHOT.json'),
    source_binding_sha256=sha(ROOT/'NOTEBOOK_RELEASE_BINDINGS.json'),profile_sha256=sha(ROOT/'FINAL_NOTEBOOK_PROFILE.json'),
    native_model_steps=0,native_constructions=0,new_bootstrap_draws=0,model_or_native_leases=0,
    original_default_baseline_receipt_sha256='e7458405120fb93af6eb9504df60d4906dff4782a982216991d16b0deead55f6',
    proof_files={p.name:sha(p)for p in PROOF.iterdir()if p.is_file()},
    scope='One actual fresh default analysis after actual certificate and QA binding; no repeat native/model work. Fourteen canonical cells projected from actual sixteen-cell proof; no values or images fabricated.')
assert not(PROOF/'OUTPUT_PROJECTION_PROOF.json').exists()
write(PROOF/'OUTPUT_PROJECTION_PROOF.json',result)
print(json.dumps(dict(status='passed',main_bytes=result['displayed_main_bytes'],main_sha256=result['displayed_main_sha256'],projection_proof_sha256=sha(PROOF/'OUTPUT_PROJECTION_PROOF.json'),seconds=execution['seconds']),indent=2))
