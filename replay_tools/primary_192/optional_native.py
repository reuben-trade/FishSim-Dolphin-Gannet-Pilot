"""Finite professor replay after actual artifact-specific certification.

Importing this module and creating an argument plan are native-free. Execution
requires a non-null, hash-bound release and the unchanged original gate. No
user-authored approval JSON, simulator import or in-kernel model construction.
"""
from __future__ import annotations
import argparse,datetime,hashlib,importlib.util,json,os,subprocess,sys,uuid
from pathlib import Path
from contextlib import contextmanager

ARTIFACTS={'historical':'eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558',
 'source-built':'cc21f00f355e1d25e8ecb48bd6aa50a7c9b63f909d921f4864a96e91d9ef2d4b'}
INTERFACE_ENTRY='model_examples/primary_192/run_primary_model.py'
RELEASE_PATH='model_examples/primary_192/PRIMARY_MODEL_RELEASE.json'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inside(root,name):
    path=Path(name)
    if path.is_absolute():raise ValueError('Bundled paths must be relative')
    path=(root/path).resolve()
    if not path.is_relative_to(root):raise ValueError('Bundled path escapes package')
    return path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

AUTHORITY_ENV=('FISHSIM_PRIMARY_RUNTIME','FISHSIM_PRIMARY_REQUEST','FISHSIM_PRIMARY_DISPATCH')

def executable_path(value):
    # Resolve relative spelling, but preserve a venv's executable symlink.
    return os.path.abspath(os.path.expanduser(os.fspath(value)))

def child_environment(parent=None):
    environment=dict(os.environ if parent is None else parent)
    for name in ('PYTHONOPTIMIZE',*AUTHORITY_ENV):environment.pop(name,None)
    environment['PYTHONDONTWRITEBYTECODE']='1'
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):environment[name]='1'
    return environment

@contextmanager
def clean_parent_gate_context():
    absent=object();previous={name:os.environ.get(name,absent)for name in AUTHORITY_ENV}
    for name in AUTHORITY_ENV:os.environ.pop(name,None)
    try:yield
    finally:
        for name,value in previous.items():
            if value is absent:os.environ.pop(name,None)
            else:os.environ[name]=value


def validate_settings(enabled,duration,kind,workers):
    from .notebook_template import config_value
    import ast
    values={'RUN_NATIVE':enabled,'NATIVE_DURATION_T':duration,'NATIVE_ARTIFACT':kind,'NATIVE_WORKERS':workers}
    for name,value in values.items():config_value(name,ast.Constant(value))
    return values


def validate_release(root,kind):
    """Pure proof validation before any subprocess, output directory or lease."""
    root=Path(root).resolve()
    if kind not in ARTIFACTS:raise ValueError('Choose historical or source-built')
    binding=read(root/'NOTEBOOK_RELEASE_BINDINGS.json');release=binding.get('native_release',{})
    if release.get('status')!='ACTUAL_BOTH_ARTIFACTS_RELEASE_ACCEPTED' or release.get('certificate_sha256') is None:
        raise RuntimeError('Native replay remains closed: actual zero/4T/36T release proofs have not been bound')
    if release.get('certificate_path')!=RELEASE_PATH:raise RuntimeError('Unexpected release certificate path')
    certificate=inside(root,RELEASE_PATH)
    if sha(certificate)!=release['certificate_sha256']:raise RuntimeError('Release certificate changed')
    if release.get('root_release_acceptance_sha256') is None:raise RuntimeError('Root release acceptance is not bound')
    acceptance=inside(root,release['root_release_acceptance_path'])
    if sha(acceptance)!=release['root_release_acceptance_sha256']:raise RuntimeError('Release acceptance changed')
    accepted=read(acceptance)
    # The final acceptance schema is deliberately not invented in this source
    # draft. The binding step must freeze its concrete schema before activation.
    if release.get('acceptance_contract') is None:raise RuntimeError('Actual release acceptance contract is still pending')
    contract=release['acceptance_contract']
    for key,value in contract.items():
        if accepted.get(key)!=value:raise RuntimeError('Actual release acceptance differs:'+key)
    if not contract or contract.get('status')!='passed':raise RuntimeError('A nonempty passed acceptance contract is required')
    pins=read(Path(__file__).with_name('SOURCE_PINS.json'))
    interface=root/'model_examples/primary_192'
    for name,h in pins['interface_files'].items():
        if sha(interface/name)!=h:raise RuntimeError('Reviewed native interface changed:'+name)
    if any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules):raise RuntimeError('Use an isolated model process')
    previous=list(sys.path)
    with clean_parent_gate_context():
        try:
            sys.path.insert(0,str(interface))
            import primary_runtime as runtime
            import primary_gate as gate
            if Path(runtime.__file__).resolve()!=interface/'primary_runtime.py' or Path(gate.__file__).resolve()!=interface/'primary_gate.py':raise RuntimeError('Foreign native gate modules')
            # Both must be actually certified before this notebook profile activates.
            for artifact in ARTIFACTS:
                path,record=gate.validate_release(artifact)
                if path.resolve()!=certificate or record['active_native_sha256']!=ARTIFACTS[artifact]:raise RuntimeError('Artifact-specific release differs')
        finally:sys.path[:]=previous
    return dict(certificate_sha256=sha(certificate),active_native_sha256=ARTIFACTS[kind],kind=kind)

def argument_plan(root,kind='historical',duration=4,model_python=None,work_root=None,profile_file='FINAL_NOTEBOOK_PROFILE.json',workers=6):
    """Structural plan only. It never imports a model or validates fake proofs."""
    root=Path(root).resolve()
    if type(workers)is not int or workers not in range(1,7):raise ValueError('Notebook workers must be an integer1..6')
    if kind not in ARTIFACTS or type(duration)is not int or duration not in (4,36):raise ValueError('Only declared artifacts and 4T/36T horizons')
    python=executable_path(model_python or sys.executable)
    work=Path(work_root).expanduser().resolve() if work_root else Path.home()/'FishSim-primary-replays'/('run_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    work=work.resolve()
    if work==root or work.is_relative_to(root) or root.is_relative_to(work):raise ValueError('Fresh local work must be outside the package')
    if work.exists():raise FileExistsError('Never overwrite or resume a local replay')
    profile=read(inside(root,profile_file));snapshot=inside(root,profile['validation']['snapshot_manifest'])
    if snapshot.name!='SNAPSHOT.json':raise ValueError('Use the accepted snapshot manifest file')
    runtime=work/'runtime';zero=work/'zero192.json';output=work/f'first-world-{duration}T';owner=work/f'owner-{duration}T.json'
    entry=inside(root,INTERFACE_ENTRY);checker=inside(root,'replay_tools/primary_192/check_primary_replay_v2.py')
    base=[python,'-B',str(entry),'--package-root',str(root),'--native-kind',kind,'--runtime',str(runtime)]
    commands=[base+['--prepare','--snapshot',str(snapshot)],base+['--check','--output',str(zero)],
      base+['--run','--duration',str(duration),'--school','39065501','--label','71001','--grid','both','--arms','D,G,DG','--workers',str(workers),'--zero-receipt',str(zero),'--output',str(output)],
      [python,'-B',str(checker),'--interface-root',str(root/'model_examples/primary_192'),'--runtime',str(runtime),'--output',str(output),'--duration',str(duration),'--receipt',str(owner)]]
    return dict(status='SOURCE_ARGUMENT_PLAN_ONLY_NOT_EXECUTED',commands=commands,work_root=str(work),runtime=str(runtime),zero_receipt=str(zero),output=str(output),owner_receipt=str(owner),native_kind=kind,duration_T=duration,cases=6,school=39065501,label=71001,grids=['coarse','fine'],arms=['D','G','DG'],zero_constructions=192,integration_constructions=6,maximum_native_steps=28800 if duration==4 else 259200,workers=workers,full192_ensemble_replayed=False,native_steps_executed=0,profile_file=profile_file)

def run(root,kind='historical',duration=4,model_python=None,work_root=None,profile_file='FINAL_NOTEBOOK_PROFILE.json',workers=6):
    root=Path(root).resolve()
    proof=validate_release(root,kind)  # Always before planning or writing outputs.
    plan=argument_plan(root,kind,duration,model_python,work_root,profile_file,workers)
    environment=child_environment()
    # The unchanged CLI repeats actual release/request checks and automatically
    # creates its local opt-in requests; no custom authority argument is passed.
    for argv in plan['commands']:subprocess.run(argv,check=True,cwd=root,env=environment)
    executed=read(Path(plan['output'])/'execution.json');zero=read(plan['zero_receipt']);owner=read(plan['owner_receipt'])
    if executed['jobs']!=6 or executed['native_steps']!=plan['maximum_native_steps'] or executed['active_native_sha256']!=proof['active_native_sha256']:raise RuntimeError('Completed local scope differs')
    if zero['native_constructions']!=192 or zero['native_steps']!=0 or zero['active_native_sha256']!=proof['active_native_sha256']:raise RuntimeError('Local zero-start scope differs')
    if owner['status']!='passed' or owner['duration_T']!=duration or owner['exact_full_trajectory_and_event_replay'] is not True:raise RuntimeError('Saved-data owner check did not pass')
    result=dict(status='completed_explicit_professor_local_replay',saved_analysis_receipt_is_separate=True,**proof,duration_T=duration,cases=6,zero_constructions=192,integration_constructions=6,model_steps=executed['native_steps'],owner_receipt_sha256=sha(plan['owner_receipt']),source_execution_sha256=sha(Path(plan['output'])/'execution.json'),full192_ensemble_fidelity_claimed=False,new_feeding_inference=False,work_root=plan['work_root'])
    path=Path(plan['work_root'])/'LOCAL_REPLAY_RECEIPT.json'
    with path.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(allow_abbrev=False);mode=p.add_mutually_exclusive_group();mode.add_argument('--plan',action='store_true');mode.add_argument('--run',action='store_true');p.add_argument('--package-root',type=Path,required=True);p.add_argument('--native-kind',choices=tuple(ARTIFACTS),default='historical');p.add_argument('--duration',type=int,choices=(4,36),default=4);p.add_argument('--model-python',type=Path);p.add_argument('--work-root',type=Path);p.add_argument('--profile',default='FINAL_NOTEBOOK_PROFILE.json');p.add_argument('--workers',type=int,choices=range(1,7),default=6);a=p.parse_args()
    action=run if a.run else argument_plan
    print(json.dumps(action(a.package_root,a.native_kind,a.duration,a.model_python,a.work_root,a.profile,a.workers),indent=2))
