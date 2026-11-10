"""Saved-data engineering checks; never executes the simulator.

Checks allsix accepted first-world arms/grids at a chosen4T or36T horizon.
Successful short prefixes cannot substitute for an actual36T proof.
"""
from __future__ import annotations
import argparse,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
from primary_runtime import HERE,STUDY,identity,read,sha,write,verify_runtime,interfaces
from primary_worker import DenyNative

def records(path):
    with gzip.open(path,'rt') as f:return [json.loads(line) for line in f if line.strip()]
def equal(a,b):return a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes()
def compare(directory,reference,duration):
    for name in ('initial_engine.json','initial_shared.json'):
        if read(directory/name)!=read(reference/name):raise AssertionError('Exact initial state/private stream mismatch:'+name)
    for name in ('initial_school.npz','trajectories.npz'):
        with np.load(directory/name,allow_pickle=False) as actual,np.load(reference/name,allow_pickle=False) as expected:
            if set(actual.files)!=set(expected.files):raise AssertionError('Array field inventory differs')
            mask=expected['time']<=duration+1e-8 if name=='trajectories.npz' else None
            for field in actual.files:
                b=expected[field] if mask is None or field in ('actor_ids','prey_ids') else expected[field][mask]
                if not equal(actual[field],b):raise AssertionError('Exact trajectory/initial-array mismatch:'+field)
    for name in ('events.jsonl.gz','monitor.jsonl.gz','opportunities.jsonl.gz','bird_events.jsonl.gz','responses.jsonl.gz'):
        actual=records(directory/name);expected=[r for r in records(reference/name) if r['elapsed']<=duration+1e-8]
        if name=='opportunities.jsonl.gz' and any(r.get('reason')=='encounter_end' for r in actual):raise AssertionError('Unexpected encounter_end event in exact shared planner')
        if actual!=expected:raise AssertionError('Full event/prefix mismatch:'+name)
    expected_metrics=[r for r in read(reference/'school_metrics.json') if r['elapsed']<=duration+1e-8]
    if read(directory/'school_metrics.json')!=expected_metrics:raise AssertionError('Sampled geometry stream differs')
    if duration in (4,36):
        # Walltime/provenance differ; physical actor accounting and terminal
        # streams must match exactly for a full-horizon fidelity claim.
        for name in ('final_engine.json','tie_stream_calls.json'):
            if read(directory/name)!=read(reference/name):raise AssertionError('Full terminal private/controller state differs')
        with np.load(directory/'final_school.npz',allow_pickle=False) as a,np.load(reference/'final_school.npz',allow_pickle=False) as b:
            if set(a.files)!=set(b.files) or any(not equal(a[k],b[k]) for k in a.files):raise AssertionError('Full terminal native arrays differ')
        if read(directory/'summary.json')['per_actor']!=read(reference/'summary.json')['per_actor']:raise AssertionError('Full actor time/contact/food accounting differs')

def check(runtime,output,duration):
    d=verify_runtime(runtime);execution=read(output/'execution.json')
    if execution['active_native_sha256']!=d['active_native_sha256'] or execution['runtime_declaration_sha256']!=sha(runtime/'PRIMARY_RUNTIME.json'):raise AssertionError('Execution artifact/runtime binding differs')
    cases=[identity(39065501,71001,g,a) for g in ('coarse','fine') for a in ('D','G','DG')]
    expected_steps=28800 if duration==4 else 259200
    if execution['jobs']!=6 or execution['native_steps']!=expected_steps:raise AssertionError('Exact six-case complete horizon required')
    denial=DenyNative();sys.meta_path.insert(0,denial)
    try:
        sys.path[:0]=[str(runtime/STUDY),str(runtime),str(runtime/'lib')]
        path=runtime/STUDY/'review_actual.py'
        if sha(path)!='fb694fdf2e86dc023400c06a5a75467d5b89be44c154a367ee52fc02e207c52a':raise AssertionError('Physical audit predicate differs')
        spec=importlib.util.spec_from_file_location('_primary_replay_physical_review',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
        for c in cases:
            directory=output/f'{duration:g}T'/'cases'/c['case_name'];reference=runtime/'reference_inputs'/('smoke4T' if duration==4 else 'full36T')/c['case_name']
            seal=read(directory/'completion.json')
            if seal['status']!='complete' or any(sha(directory/p)!=h for p,h in seal['files'].items()):raise AssertionError('New replay case seal changed')
            compare(directory,reference,duration)
            proof=m.audit_case(directory)
            summary=read(directory/'summary.json')
            if summary['native_steps']!=round(duration/c['dt']) or abs(summary['actual_duration']-duration)>1e-7:raise AssertionError('Actual full horizon not achieved')
    finally:sys.meta_path.remove(denial)
    if denial.attempts or any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules):raise AssertionError('Saved-data checker imported a model')
    return dict(status='passed',schema='primary_model_exact_horizon_engineering_v1',interface_files=interfaces(),
        exact_case_names=[c['case_name'] for c in cases],duration_T=duration,source_execution_native_steps=expected_steps,
        active_native_sha256=d['active_native_sha256'],runtime_declaration_sha256=sha(runtime/'PRIMARY_RUNTIME.json'),
        exact_full_trajectory_and_event_replay=True,model_steps_by_reviewer=0,native_imports=0,
        full192_ensemble_fidelity_claimed=False,independent_review_claimed=False,
        scope='Only firstschool39065501/label71001 sixcoarse/finearms at this actual complete horizon; not new feeding evidence')

if __name__=='__main__':
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--duration',type=int,choices=(4,36),required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    if a.receipt.exists():raise FileExistsError('Never overwrite a replay check receipt')
    write(a.receipt,check(a.runtime.resolve(),a.output.resolve(),a.duration))
