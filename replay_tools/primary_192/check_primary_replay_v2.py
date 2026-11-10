"""Versioned saved-data owner checker; no simulator, constructors or leases.

Retains original exact compare(), physical audit functions and tolerances.
Only the author-directory seal import is replaced with an explicit portable
source/preparation/runtime/request adapter; independent review stays separate.
"""
from __future__ import annotations
import argparse,ast,hashlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
import portable_seal_adapter as adapter

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def function_asts(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

def derived_physical_source(path):
    source=path.read_text();tree=ast.parse(source);before=function_asts(tree);matches=0
    for node in tree.body:
        if isinstance(node,ast.ImportFrom) and node.module=='evidence':
            if [(a.name,a.asname) for a in node.names]!=[('validate_candidate_seal',None)]:raise RuntimeError('Unexpected original seal dependency')
            node.module='portable_seal_adapter';matches+=1
    if matches!=1 or before!=function_asts(tree):raise RuntimeError('Physical audit functions changed')
    return compile(ast.fix_missing_locations(tree),str(path)+'[portable-seal-import-only]','exec'),hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()

class DenyNative(importlib.abc.MetaPathFinder):
    def __init__(self):self.attempts=[]
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='fish_sim' or fullname.startswith('fish_sim.'):
            self.attempts.append(fullname);raise RuntimeError('Saved-data checker forbids simulator imports')

def check(runtime,output,duration,interface_root=None):
    if sys.flags.optimize:raise RuntimeError('Unoptimized Python required')
    pins=adapter.read(HERE/'SOURCE_PINS.json');runtime=Path(runtime).resolve();output=Path(output).resolve()
    if interface_root is None:
        interface_root=HERE if (HERE/'primary_runtime.py').is_file() else Path(adapter.read(runtime/'PRIMARY_RUNTIME.json')['package'])/'model_examples/primary_192'
    interface_root=Path(interface_root).resolve()
    for name,h in pins['interface_files'].items():
        if adapter.sha(interface_root/name)!=h:raise RuntimeError('Reviewed source differs:'+name)
    if adapter.sha(interface_root/'check_primary_replay.py')!=pins['original_owner_checker_sha256']:raise RuntimeError('Original exact replay checker changed')
    if any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules):raise RuntimeError('Fresh non-native process required')
    denied=DenyNative();sys.meta_path.insert(0,denied);original_path=sys.path.copy()
    try:
        sys.path.insert(0,str(interface_root))
        import primary_runtime as pr
        import primary_gate as gate
        if Path(pr.__file__).resolve()!=interface_root/'primary_runtime.py' or Path(gate.__file__).resolve()!=interface_root/'primary_gate.py':raise RuntimeError('Foreign operational modules')
        original=load('_unchanged_primary_owner_checker',interface_root/'check_primary_replay.py')
        execution=adapter.read(output/'execution.json');d=pr.verify_runtime(runtime)
        cases=[pr.identity(39065501,71001,g,a) for g in ('coarse','fine') for a in ('D','G','DG')]
        expected_steps=28800 if duration==4 else 259200
        if execution['jobs']!=6 or execution['native_steps']!=expected_steps:raise RuntimeError('Exact six-case full horizon required')
        if set(execution['case_completion_sha256'])!={f'{duration:g}T/'+c['case_name'] for c in cases}:raise RuntimeError('Execution inventory differs')
        context=adapter.configure(pr,gate,runtime,output,execution,cases,duration)
        source=runtime/pr.STUDY/'review_actual.py'
        if adapter.sha(source)!=pins['original_physical_review_sha256']:raise RuntimeError('Original physical predicates changed')
        code,predicate_sha=derived_physical_source(source)
        module=type(sys)('_primary_portable_physical_review');module.__file__=str(source);sys.modules[module.__name__]=module;exec(code,module.__dict__)
        receipts=[]
        for c in cases:
            directory=output/f'{duration:g}T'/'cases'/c['case_name'];reference=runtime/'reference_inputs'/('smoke4T' if duration==4 else 'full36T')/c['case_name']
            original.compare(directory,reference,duration)
            receipts.append(module.audit_case(directory))
            summary=adapter.read(directory/'summary.json')
            if summary['native_steps']!=round(duration/c['dt']) or abs(summary['actual_duration']-duration)>1e-7:raise RuntimeError('Actual full horizon not achieved')
    finally:
        sys.path[:]=original_path;sys.meta_path.remove(denied)
    if denied.attempts or any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules):raise RuntimeError('Saved checker imported simulator')
    return dict(status='passed',schema='primary_model_exact_horizon_engineering_v1',interface_files=pr.interfaces(),exact_case_names=[c['case_name'] for c in cases],duration_T=duration,source_execution_native_steps=expected_steps,active_native_sha256=d['active_native_sha256'],runtime_declaration_sha256=adapter.sha(runtime/'PRIMARY_RUNTIME.json'),exact_full_trajectory_and_event_replay=True,model_steps_by_reviewer=0,native_imports=0,native_constructions=0,full192_ensemble_fidelity_claimed=False,independent_review_claimed=False,scope='Owner saved-data check only; firstschool39065501/label71001 bothgrids/three arms at actual complete horizon. Original physical functions/tolerances and exact compare are retained; independent bb920 review remains mandatory.',operational_adapter_version=2,original_owner_checker_sha256=pins['original_owner_checker_sha256'],original_physical_review_sha256=pins['original_physical_review_sha256'],original_physical_function_asts_sha256=predicate_sha,portable_source_preparation_reconstruction=context['reconstruction'],request_sha256=adapter.sha(context['request']),dispatch_sha256=adapter.sha(context['dispatch']),physical_cases=receipts,owner_checker_sha256=adapter.sha(Path(__file__)),seal_adapter_sha256=adapter.sha(HERE/'portable_seal_adapter.py'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--interface-root',type=Path);parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--duration',type=int,choices=(4,36),required=True);parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
    if args.receipt.exists():raise FileExistsError('Never overwrite an owner receipt')
    result=check(args.runtime,args.output,args.duration,interface_root=args.interface_root)
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    with args.receipt.open('xb') as handle:handle.write(adapter.encoded(result))
    print(json.dumps(dict(status=result['status'],cases=len(result['physical_cases']),duration_T=args.duration,native_steps_by_checker=0)))
