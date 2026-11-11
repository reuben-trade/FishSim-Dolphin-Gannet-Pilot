"""Closed finite local-native notebook QA coordinator; --plan is the default.

Execution is not granted by this source. A later exact ROOT authority, actual
both-artifact certificate, copied-package receipt and guard config are required.
"""
from __future__ import annotations
import argparse,hashlib,json,os,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def require(value,message):
    if not value:raise RuntimeError(message)

def execute(authority_path):
    authority_path=Path(authority_path).resolve();a=read(authority_path)
    require(a.get('schema')=='professor_local_notebook_qa_authority_v1'and a.get('approved')is True,'No actual finite ROOT QA authority')
    require(a.get('recorded_by')=='/root'and a.get('separate_from_576000_engineering')is True,'Separate ROOT QA approval required')
    require(a['maximum_native_constructions']==198 and a['maximum_native_steps']==28800 and a['native_cases']==6 and a['workers']==6,'Fixed198/28800/six-case QA only')
    for name,h in a['source_files'].items():require(sha(HERE/name)==h,'QA source changed:'+name)
    require(a.get('both_artifact_full36_independent_passed')is True and a.get('all_prior_native_terminal_and_lease_released')is True,'Full engineering and lease-release prerequisites required')
    for item in a['prerequisite_files'].values():require(item['path']is not None and sha(item['path'])==item['sha256'],'Actual accepted prerequisite changed')
    root=Path(a['relocated_package']).resolve();control=Path(a['control_directory']).resolve();guard=Path(a['guard_directory']).resolve()
    require(root.is_dir()and control.is_dir()and guard.is_dir(),'Previously reviewed relocated package/control/guard needed')
    require(sha(guard/'sitecustomize.py')==sha(HERE/'qa_startup_guard.py'),'Copied startup guard source differs')
    require(a['analysis_python']==sys.executable and sys.version_info[:3]==(3,12,13),'Use the recorded existing analysis3.12.13 interpreter without resolving its venv symlink')
    require(a['expected_native_kind']=='historical'and a['school_seed']==39065501 and a['capture_label']==71001 and a['duration_T']==4,'Fixed world/horizon, no reselection')
    require(sha(root/'model_examples/primary_192/PRIMARY_MODEL_RELEASE.json')==a['actual_certificate_sha256'],'Actual release certificate differs')
    require(sha(a['copied_package_receipt']['path'])==a['copied_package_receipt']['sha256'],'Relocated byte-copy proof differs')
    binding=read(root/'NOTEBOOK_RELEASE_BINDINGS.json');require(binding['native_release']['certificate_sha256']==a['actual_certificate_sha256'],'Notebook actual certificate binding differs')
    # Pure actual-certificate gate precedes all kernel/model construction.
    sys.path.insert(0,str(root))
    from replay_tools.primary_192.certified_native_v1 import validate_release
    validate_release(root,'historical')
    import nbformat
    from nbclient import NotebookClient
    book=nbformat.read(root/'main.ipynb',as_version=4)
    native=next(c for c in book.cells if c.cell_type=='code'and c.source.startswith('RUN_NATIVE = False'))
    native.source=native.source.replace('RUN_NATIVE = False','RUN_NATIVE = True',1)
    require('NATIVE_DURATION_T = 4'in native.source and 'NATIVE_ARTIFACT = "historical"'in native.source and 'NATIVE_WORKERS = 6'in native.source,'Canonical four literal settings differ')
    nbformat.write(book,root/'main.ipynb')
    from replay_tools.primary_192.notebook_template import verify
    template=binding['notebook_template'];verified=verify(root/'main.ipynb',root/template['path'],template['configuration_cell_id'],template['logical_sha256']);require(verified['settings']['RUN_NATIVE']is True,'Exact logical native opt-in required')
    # Normal GUI-like context, deliberately outside ROOT/.headless markers.
    environment=os.environ.copy()
    for name in ('PYTHONOPTIMIZE','FISHSIM_PRIMARY_RUNTIME','FISHSIM_PRIMARY_REQUEST','FISHSIM_PRIMARY_DISPATCH','PYTHONPATH','IPYTHONDIR','JUPYTER_RUNTIME_DIR','JUPYTER_PATH'):environment.pop(name,None)
    environment.update(PYTHONPATH=str(guard),PYTHONDONTWRITEBYTECODE='1',IPYTHONDIR=str(control/'gui_profile'),JUPYTER_RUNTIME_DIR=str(control/'gui_runtime'),JUPYTER_PATH=str(control/'kernel_specs'),FISHSIM_LOCAL_QA_GUARD_CONFIG=a['guard_config']['path'],FISHSIM_LOCAL_QA_GUARD_CONFIG_SHA256=a['guard_config']['sha256'],FISHSIM_LOCAL_QA_GUARD_SHA256=sha(guard/'sitecustomize.py'))
    require(sha(a['guard_config']['path'])==a['guard_config']['sha256'],'Actual guard config differs')
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):environment[name]='1'
    # Native outputs follow the unmodified normal HOME-based helper route.
    work_parent=Path.home()/'FishSim-primary-replays';before={p.name for p in work_parent.iterdir()}if work_parent.exists()else set()
    specdir=control/'kernel_specs/kernels/professor_local_qa';specdir.mkdir(parents=True,exist_ok=False)
    (specdir/'kernel.json').write_text(json.dumps(dict(argv=[a['analysis_python'],'-B','-m','ipykernel_launcher','-f','{connection_file}'],display_name='Normal GUI-like local professor QA',language='python')))
    # The coordinator uses its own Jupyter path to find the exact model kernel.
    os.environ['JUPYTER_PATH']=str(control/'kernel_specs')
    probe=nbformat.v4.new_code_cell("import sitecustomize as qa_guard\nassert qa_guard._LOGGED_STARTUP\nassert qa_guard.blocked_read_probe()\nprint('QA guard startup and original-read denial passed; zero model constructors.')")
    book.cells.insert(0,probe)
    # Exactly one GUI-like RunAll, including the actual local opt-in cell.
    NotebookClient(book,timeout=2400,kernel_name='professor_local_qa',allow_errors=False,resources={'metadata':{'path':str(root)}}).execute(env=environment)
    after={p.name for p in work_parent.iterdir()};new=after-before;require(len(new)==1,'Exactly one fresh local helper work directory required')
    work=work_parent/new.pop();local=read(work/'LOCAL_REPLAY_RECEIPT.json');execution=read(work/'first-world-4T/execution.json');zero=read(work/'zero192.json')
    require(local['cases']==6 and local['duration_T']==4 and local['model_steps']==28800 and zero['native_constructions']==192 and zero['native_steps']==0,'Actual finite local execution differs')
    require(local['active_native_sha256']=='eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558','Only actual historical artifact allowed')
    require(execution['jobs']==6 and execution['native_steps']==28800,'Actual six-case phase differs')
    requests=[work/'zero192.json.local_request.json',work/'first-world-4T.local_request.json']
    # The helper's output.with_name convention is exact; no author approvals.
    for request in requests:
        value=read(request);require(value['schema']=='primary_local_opt_in_v1'and value['explicit_local_opt_in']is True and 'approved'not in value,'Actual professor automatic local opt-in branch required')
    nbformat.write(book,control/'EXECUTED_LOCAL_QA.ipynb')
    result=dict(status='owner_complete_pending_independent_guard_and_scope_review',native_constructions=198,native_steps=28800,kernel_route='Normal GUI-like actual main.RunAll with True4T/historical',source_unchanged_e6=True,local_work=str(work),actual_certificate_sha256=a['actual_certificate_sha256'],authority_sha256=sha(authority_path),local_receipt_sha256=sha(work/'LOCAL_REPLAY_RECEIPT.json'),guard_audit_directory=read(a['guard_config']['path'])['audit_directory'],independent_claim=False,new_scientific_inference=False)
    with (control/'OWNER_QA_RECEIPT.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true');parser.add_argument('--authority',type=Path);args=parser.parse_args()
    if args.execute:
        require(args.authority is not None,'Actual fresh ROOT QA authority required');execute(args.authority)
    else:print(json.dumps(read(HERE/'QA_PLAN.json'),indent=2))
