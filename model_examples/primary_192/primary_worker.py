"""Isolated per-artifact model worker; private preparation never enters native paths."""
from __future__ import annotations
import argparse,hashlib,importlib.abc,importlib.util,json,os,platform,sys
from pathlib import Path
from dataclasses import asdict
from primary_runtime import HERE,STUDY,inventory,identity,read,sha,write,verify_runtime
FIELDS=('positions','directions','prey_ids','time','step_index','surface_reflections')
LEASE=Path('/tmp/FishSim_Native_Execution_Lease_2026-11-09.lock')
_LEASE_STATE=None

def install_author_path_guard(runtime=None,output=None):
    """Process-local negative path proof; never renames the active study."""
    protected=(Path('/home/venture/uwa/complex-systems/FishSim-RL'),
        Path('/home/venture/FishSim_Independent_Validation_2026-11-10'),
        Path('/home/venture/FishSim-Dolphin-Gannet-Pilot'))
    dependencies=protected[0]/'.venv'
    allowed=[HERE.resolve(),Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve()]
    allowed += [Path(p).resolve() for p in sys.path if p and Path(p).name in ('site-packages','dist-packages')]
    if runtime is not None:allowed.append(Path(runtime).resolve())
    output_path=Path(output).resolve() if output is not None else None
    # Interpreter/library OS metadata is dependency input, not author study
    # data. No arbitrary/tmp, Downloads, model-root or author-bank access.
    system=[Path(p) for p in ('/usr','/lib','/lib64','/etc','/proc','/sys','/dev')]
    attempts=[]
    def guard(event,args):
        if event not in ('open','os.listdir','os.scandir') or not args or isinstance(args[0],int):return
        value=args[0]
        if not isinstance(value,(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(value)).resolve()
        if output_path is not None and path==output_path:return
        if any(path==p or path.is_relative_to(p) for p in allowed+system):return
        attempts.append(str(path));raise RuntimeError('Pure file-view proof forbids non-view/author model/data paths:'+str(path))
    sys.addaudithook(guard)
    return attempts

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def digest(state):
    import numpy as np
    h=hashlib.sha256()
    for name in FIELDS:
        a=np.asarray(state[name]);h.update(name.encode());h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()
def paths(runtime):sys.path[:0]=[str(runtime/STUDY),str(runtime),str(runtime/'lib')]
class DenyNative(importlib.abc.MetaPathFinder):
    def __init__(self):self.attempts=[]
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='fish_sim' or fullname.startswith('fish_sim.'):
            self.attempts.append(fullname);raise RuntimeError('Pure preparation forbids simulator imports')
        return None
def forbid_model(frame,event,arg):
    if event=='call' and frame.f_code.co_qualname in ('Encounter.__init__','Encounter.step','TravellingSchool.__init__','TravellingSchool.step','SurfaceSafeSchool.__init__','SurfaceSafeSchool.step','_native_school'):
        raise RuntimeError('Pure preparation attempted a model boundary')
def case_for(row):
    from cases import Case
    return Case(row['school_seed'],row['grid'],row['presence'],row['capture_seed'])

def pure(runtime,output):
    author_attempts=install_author_path_guard(runtime,output)
    declaration=verify_runtime(runtime);blocked=DenyNative();sys.meta_path.insert(0,blocked);previous=sys.getprofile();sys.setprofile(forbid_model)
    try:
        paths(runtime);builder=load('primary_build',runtime/STUDY/'primary_build.py')
        expected=read(runtime/'reference_inputs/ACTUAL_ZERO_STEP.json');oldpure=read(runtime/'reference_inputs/PURE_PREFLIGHT.json')
        zeros={r['case_name']:r for r in expected['rows']};raws={r['case_name']:r for r in oldpure['rows']};rows=[]
        import numpy as np
        for row in inventory():
            c=case_for(row);prepared=builder.prepare_case(c);engine=prepared.receipt();state=asdict(prepared.initial)
            engine_hash=hashlib.sha256(json.dumps(engine,sort_keys=True).encode()).hexdigest()
            if engine_hash!=zeros[c.name]['actual_engine_receipt_sha256'] or engine_hash!=raws[c.name]['pure_receipt_sha256']:raise AssertionError('Exact Python actor/controller/private start mismatch:'+c.name)
            raw_hash=hashlib.sha256(prepared.initial.positions.tobytes()+prepared.initial.directions.tobytes()).hexdigest()
            if raw_hash!=raws[c.name]['raw_fish_sha256']:raise AssertionError('Raw20T checkpoint mismatch')
            actual=expected['actual_school_references'][str(c.school_seed)]
            if not np.array_equal(state['positions'],actual['positions']) or not np.array_equal(state['prey_ids'],actual['prey_ids']):raise AssertionError('Actual versus raw fish positions/IDs differ')
            error=float(np.max(abs(np.asarray(state['directions'])-np.asarray(actual['directions'])),initial=0.))
            if error>1e-12:raise AssertionError('Archived heading normalization bound exceeded')
            rows.append(dict(case_name=c.name,pure_receipt_sha256=engine_hash,raw_fish_sha256=raw_hash,raw_to_native_heading_max_delta=error))
    finally:sys.setprofile(previous);sys.meta_path.remove(blocked)
    if blocked.attempts or author_attempts or any(k=='fish_sim' or k.startswith('fish_sim.') for k in sys.modules):raise AssertionError('Forbidden native import/author access')
    write(output,dict(status='passed',schema='primary_model_pure192_v1',cases=rows,pure_cases=192,independent_schools=16,
        runtime_declaration_sha256=sha(runtime/'PRIMARY_RUNTIME.json'),active_native_sha256=declaration['active_native_sha256'],
        native_imports=0,native_constructions=0,native_steps=0,original_author_model_and_data_paths_forbidden=True,
        original_author_access_attempts=0,scope='Real Python states only; active binary never loaded or constructed'))

def authorize(runtime,output,mode,job_index=None):
    from primary_gate import context
    runtime=Path(runtime).resolve();output=Path(output).resolve()
    _,declaration,request_path,request=context(runtime,output,mode)
    if mode=='zero':
        if output.exists():raise FileExistsError('Zero receipt already exists')
        job=None
    else:
        if type(job_index)is not int or not 0<=job_index<len(request['jobs']):raise RuntimeError('Invalid authorized job index')
        job=request['jobs'][job_index];identity(job['school_seed'],job['capture_seed'],job['grid'],job['presence'])
        leaf=output/f"{job['duration_T']:g}T"/'cases'/job['case_name']
        if leaf.exists():raise FileExistsError('Preserve existing/partial model output:'+str(leaf))
    return declaration,request_path,request,job

def configure(runtime,output,mode,job_index=None):
    d,path,request,job=authorize(runtime,output,mode,job_index)
    if _LEASE_STATE!=(str(Path(runtime).resolve()),str(Path(output).resolve()),sha(path)):
        raise RuntimeError('Native entry requires the worker-owned/inherited canonical lease')
    if sys.flags.optimize or sys.version_info[:2]!=(3,12) or platform.system()!='Linux' or platform.machine()!='x86_64':raise RuntimeError('Known artifacts require unoptimized Linux x86-64 CPython3.12')
    paths(runtime);import fish_sim.cmodel as native
    if sha(native.__file__)!=d['active_native_sha256']:raise RuntimeError('Imported artifact differs')
    return d,request,job

def zero(runtime,output):
    d,request,_=configure(runtime,output,'zero');builder=load('primary_build',runtime/STUDY/'primary_build.py');runner=load('primary_execution',runtime/STUDY/'primary_execution.py')
    expected=read(runtime/'reference_inputs/ACTUAL_ZERO_STEP.json');zeros={r['case_name']:r for r in expected['rows']};done=[]
    def no_step(frame,event,arg):
        if event=='call' and frame.f_code.co_name in ('step','advance') and 'prey_mediated' in frame.f_code.co_filename:raise RuntimeError('Actual zero starts must not step')
    previous=sys.getprofile();sys.setprofile(no_step)
    try:
        for row in inventory():
            c=case_for(row);engine,_=builder.build(c,stage='initialization');snapshot=runner.snapshot(engine)
            h=hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest();fish=digest(asdict(engine.school.state()))
            if h!=zeros[c.name]['actual_engine_receipt_sha256'] or fish!=zeros[c.name]['actual_fish_sha256']:raise AssertionError('Exact actual initialized state differs:'+c.name)
            done.append(c.name)
    finally:sys.setprofile(previous)
    write(output,dict(status='passed',schema='primary_model_actual_zero192_v1',exact_case_names=done,native_constructions=192,native_steps=0,
        active_native_sha256=d['active_native_sha256'],runtime_declaration_sha256=sha(runtime/'PRIMARY_RUNTIME.json'),
        scope='Actual initialization only; not a4T/36T or full-ensemble feeding replay'))

def one_job(runtime,output,index):
    d,request,job=configure(runtime,output,'run',index)
    load('primary_build',runtime/STUDY/'primary_build.py');runner=load('primary_execution',runtime/STUDY/'primary_execution.py')
    parent=output/f"{job['duration_T']:g}T";parent.mkdir(parents=True,exist_ok=True)
    result=runner.run_case(case_for(job),str(parent),job['duration_T'],True)
    if result['native_steps']>round(job['duration_T']/job['dt']):raise AssertionError('Job step ceiling exceeded')
    return result

def main():
    global _LEASE_STATE
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--mode',choices=('pure','zero','run'),required=True)
    parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--job-index',type=int);parser.add_argument('--lease-fd',type=int);parser.add_argument('--dispatch',type=Path)
    a=parser.parse_args();runtime=a.runtime.resolve();output=a.output.resolve();os.environ['FISHSIM_PRIMARY_RUNTIME']=str(runtime)
    if a.mode=='pure':
        d=verify_runtime(runtime)
        from primary_runtime import safe
        safe(output,d['package'])
        if output.exists() or output.is_relative_to(runtime) or runtime.is_relative_to(output):raise RuntimeError('Pure output must be fresh outside inputs')
        pure(runtime,output)
        return
    # Full argv binding happens BEFORE any lease/native import, and repeats at
    # configure() so direct zero()/one_job() cannot switch runtime/output.
    _,request_path,request,_=authorize(runtime,output,a.mode,a.job_index)
    import fcntl
    inherited=a.lease_fd is not None
    if inherited:
        if a.dispatch is None:raise RuntimeError('Inherited lease needs master dispatch')
        dispatch=read(a.dispatch)
        if dispatch.get('parent_pid')!=os.getppid() or dispatch.get('request_sha256')!=sha(request_path) or dispatch.get('runtime')!=str(runtime) or dispatch.get('output')!=str(output):raise RuntimeError('Worker/master lease dispatch differs')
        fd=a.lease_fd;st=os.fstat(fd);canonical=LEASE.stat()
        if (st.st_dev,st.st_ino)!=(canonical.st_dev,canonical.st_ino):raise RuntimeError('Lease descriptor is not canonical')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        _LEASE_STATE=(str(runtime),str(output),sha(request_path))
        (zero if a.mode=='zero' else lambda r,o:one_job(r,o,a.job_index))(runtime,output)
        # Never unlock the inherited open-file-description; master owns it.
    else:
        with LEASE.open('a+') as handle:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:
                _LEASE_STATE=(str(runtime),str(output),sha(request_path))
                (zero if a.mode=='zero' else lambda r,o:one_job(r,o,a.job_index))(runtime,output)
            finally:fcntl.flock(handle,fcntl.LOCK_UN)

if __name__=='__main__':main()
