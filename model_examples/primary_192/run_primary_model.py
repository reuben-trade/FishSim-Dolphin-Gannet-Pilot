"""Private primaryH1/G36 replay: default plan is native-free;4T and36T distinct."""
from __future__ import annotations
import argparse,contextlib,json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from primary_runtime import HERE,inventory,identity,steps,interfaces,read,sha,write,safe,prepare,verify_runtime

def select(args):
    if args.all_ensemble:
        if any(x is not None for x in (args.school,args.label,args.grid,args.arms)):raise ValueError('Complete ensemble cannot combine partial selection flags')
        cases=inventory()
    else:
        grids=('coarse','fine') if args.grid=='both' else (args.grid or 'fine',)
        arms=('D,G,DG' if args.arms is None else args.arms).split(',')
        if len(arms)!=len(set(arms)):raise ValueError('Duplicate arms')
        cases=[identity(39065501 if args.school is None else args.school,71001 if args.label is None else args.label,g,a) for g in grids for a in arms]
    return [dict(c,duration_T=float(args.duration)) for c in cases]

def plan(args):
    jobs=select(args)
    return dict(schema='primary_professor_model_plan_v1',status='private_source_preparation_execution_CLOSED',
        chosen_jobs=jobs,cases=len(jobs),workers=args.workers,maximum_native_steps=steps(jobs),
        exact_primary_inventory=192,independent_school_inputs=16,nested_world_labels=2,
        selected_duration_T=args.duration,short_demo_is_full36T_replay=False,
        native_kind=args.native_kind,artifact_validation='No native starts or integrations performed through this interface',
        release_scope='No36T mode until artifact-specific actual full36T proofs for bothgrids/three arms',
        ensemble_validation='Not claimed; engineering proposal covers firstschool/label only plus all192starts',
        future_engineering=dict(zero_constructions=384,zero_steps=0,short_cases=12,short_steps=57600,
            full36T_cases=12,full36T_steps=518400,total_native_steps=576000,global_workers_maximum=8),
        native_imports=0,native_constructions=0,native_steps=0)

def environment(runtime,request):
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',FISHSIM_PRIMARY_RUNTIME=str(runtime),FISHSIM_PRIMARY_REQUEST=str(request))
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[k]='1'
    return env

@contextlib.contextmanager
def selected_context(runtime,request):
    keys=('FISHSIM_PRIMARY_RUNTIME','FISHSIM_PRIMARY_REQUEST');old={k:os.environ.get(k) for k in keys}
    os.environ.update(FISHSIM_PRIMARY_RUNTIME=str(runtime),FISHSIM_PRIMARY_REQUEST=str(request))
    try:yield
    finally:
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v

def local_request(args,runtime,output,stage):
    from primary_gate import validate_release
    release,artifact=validate_release(args.native_kind);d=verify_runtime(runtime)
    if d['native_kind']!=args.native_kind:raise RuntimeError('Requested artifact kind differs from prepared runtime')
    if d['source_mode']!='production_snapshot':raise RuntimeError('Professor execution needs accepted portable production snapshot')
    jobs=select(args) if stage=='run' else []
    request=dict(schema='primary_local_opt_in_v1',explicit_local_opt_in=True,independent_review=False,
        interface_files=interfaces(),runtime_declaration_sha256=sha(runtime/'PRIMARY_RUNTIME.json'),
        active_native_sha256=d['active_native_sha256'],release_sha256=sha(release),stage=stage,
        output=str(output),jobs=jobs,workers=args.workers,maximum_native_steps=steps(jobs),native_constructions=192 if stage=='zero' else len(jobs))
    if stage=='run':
        if args.zero_receipt is None:raise ValueError('Run requires this runtime’s prior --zero-receipt')
        request['zero_receipt']=dict(path=str(args.zero_receipt.resolve()),sha256=sha(args.zero_receipt))
    path=output.with_name(output.name+'.local_request.json')
    if path.exists():raise FileExistsError('Local request already exists')
    write(path,request);return path

def execute(runtime,request_path,output,stage):
    """One supervisor, one canonical lease, at most8 isolated native workers.

    Every request is validated before opening a lease. Per-case workers repeat
    argv bindings and receive the inherited lease descriptor; no double unlock.
    """
    from primary_gate import context
    with selected_context(runtime,request_path):_,d,_,request=context(runtime,output,stage)
    if output.exists():raise FileExistsError('Preserve existing/partial output; no automatic resume')
    dispatch=output.with_name(output.name+'.dispatch.json')
    if dispatch.exists():raise FileExistsError('Master dispatch already exists')
    import fcntl
    lease=Path('/tmp/FishSim_Native_Execution_Lease_2026-11-09.lock')
    with lease.open('a+') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            write(dispatch,dict(parent_pid=os.getpid(),runtime=str(runtime),output=str(output),request_sha256=sha(request_path)))
            env=environment(runtime,request_path);env['FISHSIM_PRIMARY_DISPATCH']=str(dispatch)
            base=[sys.executable,'-B',str(HERE/'primary_worker.py'),'--mode',stage,'--runtime',str(runtime),
                '--output',str(output),'--lease-fd',str(handle.fileno()),'--dispatch',str(dispatch)]
            if stage=='zero':subprocess.run(base,check=True,env=env,cwd=HERE,pass_fds=(handle.fileno(),))
            else:
                output.mkdir(parents=True,exist_ok=False)
                def job(index):
                    subprocess.run(base+['--job-index',str(index)],check=True,env=env,cwd=HERE,pass_fds=(handle.fileno(),))
                    return index
                completed=[]
                with ThreadPoolExecutor(max_workers=request['workers']) as pool:
                    futures={pool.submit(job,i):i for i in range(len(request['jobs']))}
                    for future in as_completed(futures):completed.append(future.result())
                total=0;seals={}
                for j in request['jobs']:
                    folder=output/f"{j['duration_T']:g}T"/'cases'/j['case_name'];s=read(folder/'summary.json')
                    total+=s['native_steps'];seals[f"{j['duration_T']:g}T/{j['case_name']}"]=sha(folder/'completion.json')
                if total>request['maximum_native_steps']:raise RuntimeError('Global request step ceiling exceeded')
                write(output/'execution.json',dict(status='complete_pending_independent_replay_review',jobs=len(completed),
                    native_steps=total,maximum_native_steps=request['maximum_native_steps'],workers=request['workers'],
                    runtime_declaration_sha256=sha(runtime/'PRIMARY_RUNTIME.json'),active_native_sha256=d['active_native_sha256'],
                    request_sha256=sha(request_path),dispatch_sha256=sha(dispatch),case_completion_sha256=seals,
                    interpretation='Local replay only; not a new independent feeding cohort or validation claim'))
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);m=p.add_mutually_exclusive_group()
    for mode in ('plan','prepare','pure-check','check','run'):m.add_argument('--'+mode,action='store_true')
    p.add_argument('--package-root',type=Path,required=True);p.add_argument('--runtime',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--snapshot',type=Path);p.add_argument('--author-inputs',action='store_true')
    p.add_argument('--native-kind',choices=('historical','source-built'),default='historical')
    p.add_argument('--duration',type=int,choices=(4,36),default=36);p.add_argument('--school',type=int);p.add_argument('--label',type=int)
    p.add_argument('--grid',choices=('coarse','fine','both'));p.add_argument('--arms');p.add_argument('--all-ensemble',action='store_true')
    p.add_argument('--workers',type=int,choices=range(1,9),default=1);p.add_argument('--zero-receipt',type=Path);p.add_argument('--authority',type=Path)
    a=p.parse_args(argv)
    if not any((a.prepare,a.pure_check,a.check,a.run)):print(json.dumps(plan(a),indent=2));return
    if a.runtime is None:p.error('--runtime required')
    runtime=a.runtime.resolve()
    if a.prepare:
        if a.snapshot is None and not a.author_inputs:p.error('--snapshot required; private --author-inputs is pure preparation only')
        d=prepare(a.package_root,runtime,a.native_kind,a.snapshot);print(json.dumps(dict(status='prepared_native_free',runtime=str(runtime),source_mode=d['source_mode']),indent=2));return
    if a.output is None:p.error('--output required')
    output=safe(a.output,a.package_root)
    if output.exists() or output.is_relative_to(runtime) or runtime.is_relative_to(output):raise RuntimeError('Fresh output outside input tree required')
    if a.pure_check:
        subprocess.run([sys.executable,'-B',str(HERE/'primary_worker.py'),'--mode','pure','--runtime',str(runtime),'--output',str(output)],check=True,env=environment(runtime,Path('/nonexistent/pure_no_authority')),cwd=HERE);return
    stage='zero' if a.check else 'run'
    request=a.authority.resolve() if a.authority else local_request(a,runtime,output,stage)
    execute(runtime,request,output,stage)

if __name__=='__main__':main()
