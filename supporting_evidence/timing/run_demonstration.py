"""Single post-hoc36T engineering demonstration; no simulation without --execute.

Uses the frozen prior runner in a fresh subprocess and wraps its build boundary.
No shared source file is changed. Each invocation has one fixed declared arm.
"""
from __future__ import annotations
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import argparse
from copy import deepcopy
from datetime import datetime
import fcntl
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import ModuleType
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'research/exposed_replication_2026-11-08'
sys.path.insert(0,str(HERE))
from timing import install, VERSION

PINS={'build.py':'c16c381c56348a038218114d82d72f515963414c142791eafa1f59c6507cc4b2',
      'run.py':'de560d99c13d0235225a55ccb5c606734d736a4584c38c570f0816a9bc42ed86'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.now(ZoneInfo('Australia/Perth')).isoformat()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def run_arm(arm,output,duration):
    if arm!='lag1' or duration!=36.:
        raise ValueError('Only declared single lag1/36T post-hoc engineering demonstration')
    for name,digest in PINS.items():
        if sha(PRIOR/name)!=digest:raise RuntimeError('Frozen baseline source changed: '+name)
    output=Path(output).resolve()
    if output.exists():raise ValueError('Fresh output directory required')
    if shutil.disk_usage(HERE).free<300*1024**2:raise RuntimeError('Less than300MiB free disk reserve')
    baseline_build=load('_timing_frozen_build',PRIOR/'build.py')
    baseline_run=load('_timing_frozen_runner',PRIOR/'run.py')
    source_manifest=baseline_run.source_manifest
    def sources():
        return {**source_manifest(),**{str(HERE/name):sha(HERE/name)
            for name in ('timing.py','run.py','test_timing.py','analyze.py','protocol.json','run_demonstration.py','demonstration_protocol.json','review_demonstration.py','retrospective_opportunities.py','results/retrospective_36T/screening.json')}}
    baseline_run.source_manifest=sources
    record={}
    def build(seed,policy,capture_seed=61002,presence='DG'):
        if (seed,capture_seed,presence,policy)!=(39063501,61002,'DG',arm):
            raise ValueError('Only fixed first-school DG feasibility input')
        engine,metadata=baseline_build.build(seed,'exposed',capture_seed,presence)
        wrapped,bus=install(engine,enabled=arm=='lag1',lag=1.)
        record['bus']=bus
        metadata=deepcopy(metadata)
        metadata.update(study=HERE.name,policy=arm,underlying_dolphin_policy='exposed',
            timing_version=VERSION,timing_enabled=arm=='lag1',timing_lag_T=1.,
            timing_protocol_sha256=sha(HERE/'protocol.json'),demonstration_protocol_sha256=sha(HERE/'demonstration_protocol.json'),duration=duration,
            timing_interpretation='causal local launch deferral; not an arrival-lag guarantee')
        return wrapped,metadata
    facade=ModuleType('build');facade.build=build;facade.__file__=str(Path(__file__).resolve())
    sys.modules['build']=facade
    output.mkdir(parents=True)
    (output/'execution.json').write_text(json.dumps(dict(status='running',at=stamp(),arm=arm,
        duration=duration,school_seed=39063501,capture_seed=61002,source_sha256=sources(),
        native_model_time_budget_T=duration,full_timing_study=False),indent=2)+'\n')
    summary=baseline_run.run_case(39063501,arm,output,duration,61002,True,'DG')
    case=output/'cases'/f's39063501_{arm}_DG_c61002'
    bus=record['bus']
    with gzip.open(case/'timing_events.jsonl.gz','wt') as handle:
        for row in bus.records:handle.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n')
    (case/'timing_final.json').write_text(json.dumps(bus.state_dict(),indent=2)+'\n')
    launches=[r for r in bus.records if r['kind']=='actual_gannet_launch']
    delayed=[r for r in launches if r['timing'] and r['timing']['ever_deferred']]
    summary['timing']=dict(actual_G_launches=len(launches),actual_previously_deferred_G_launches=len(delayed),
        gate_calls=sum(r['kind']=='timing_gate' for r in bus.records),
        deferred_launches=delayed,stage='single post-hoc opportunity-selected engineering demonstration')
    (case/'timing_summary.json').write_text(json.dumps(summary['timing'],indent=2)+'\n')
    original_completion=json.loads((case/'completion.json').read_text())
    (case/'runner_completion.json').write_text(json.dumps(original_completion,indent=2)+'\n')
    (case/'completion.json').write_text(json.dumps(dict(status='complete',at=stamp(),
        files={p.name:sha(p) for p in case.iterdir() if p.is_file() and p.name!='completion.json'}),indent=2)+'\n')
    (output/'status.json').write_text(json.dumps(dict(status='complete',at=stamp(),arm=arm,
        actual_model_time_T=duration,native_steps=summary['native_steps'],
        species=summary['species'],timing=summary['timing']),indent=2)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--arm',choices=('lag1',),required=True)
    parser.add_argument('--duration',type=float,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(native_steps=0,arm=args.arm,duration=args.duration,
            protocol=str(HERE/'demonstration_protocol.json'),status='plan_only')))
        return
    with (HERE/'native.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=run_arm(args.arm,args.output,args.duration)
    print(json.dumps(dict(status='complete',species=result['species'],timing=result['timing'])))


if __name__=='__main__':main()
