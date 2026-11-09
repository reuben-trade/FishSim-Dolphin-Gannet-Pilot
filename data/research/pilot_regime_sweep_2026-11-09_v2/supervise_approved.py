"""Operational foreground supervisor; never changes or retries a model case.

The scientific runner and analysis remain bound by their existing source
freeze. This wrapper only calls those exact commands, records a heartbeat,
and stops after the first failed stage. No publication is performed.
"""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUTPUT=HERE/'results/full_36T_v1'
HEARTBEAT=HERE/'results/full_36T_v1.heartbeat.json'
RECEIPT=HERE/'results/full_36T_v1.supervisor.json'
LOG=HERE/'results/full_36T_v1.foreground.log'


def stamp():return datetime.now(ZoneInfo('Australia/Perth')).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n')
    os.replace(temporary,path)


def heartbeat(stage,child,started):
    cases=[]
    for path in sorted((OUTPUT/'cases').glob('*/progress.json')):
        try:
            row=read(path)
            complete=(path.parent/'completion.json').exists()
            cases.append(dict(case=path.parent.name,complete=complete,
                native_steps_at_last_progress=row.get('native_steps',0),
                elapsed_T=row.get('elapsed',0),wall_seconds=row.get('wall_seconds',0)))
        except (OSError,ValueError):pass
    value=dict(at=stamp(),supervisor_pid=os.getpid(),child_pid=child.pid,stage=stage,
        supervisor_wall_seconds=time.monotonic()-started,complete_cells=sum(r['complete'] for r in cases),
        planned_cells=60,native_steps_lower_bound=sum(r['native_steps_at_last_progress'] for r in cases),
        maximum_full_native_steps=1728000,prior_smoke_steps=9600,
        anchor_replay_passed=(OUTPUT/'anchor_replay.json').exists(),cases=cases)
    write(HEARTBEAT,value)
    print(json.dumps({k:v for k,v in value.items() if k!='cases'}),flush=True)


def main():
    sys.path.insert(0,str(HERE))
    from evidence import require_approval
    require_approval('full')
    if OUTPUT.exists() or RECEIPT.exists() or LOG.exists():
        raise RuntimeError('Fresh foreground operation required; no retry or output reuse')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    record=dict(status='running',started_at=stamp(),supervisor_pid=os.getpid(),
        supervisor_source_sha256=sha(__file__),protocol_sha256=sha(HERE/'protocol.json'),
        frozen_sources_sha256=sha(HERE/'frozen_sources.json'),
        full_approval_sha256=sha(HERE/'FULL_RUN_APPROVED.json'),maximum_native_steps=1728000,
        prior_smoke_steps=9600,retries=0,publication=False,stages=[])
    write(RECEIPT,record)
    commands=(('feeding',[sys.executable,str(HERE/'run.py'),'--execute','--workers','3','--output',str(OUTPUT)]),
        ('physical_review',[sys.executable,str(HERE/'review_actual.py'),'--output',str(OUTPUT)]),
        ('analysis',[sys.executable,str(HERE/'analyze.py'),'--input',str(OUTPUT)]))
    with open(LOG,'x') as log:
        for stage,command in commands:
            child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            entry=dict(stage=stage,started_at=stamp(),command=command,pid=child.pid)
            record['stages'].append(entry);write(RECEIPT,record)
            while True:
                heartbeat(stage,child,started)
                try:
                    code=child.wait(timeout=30)
                    break
                except subprocess.TimeoutExpired:pass
            heartbeat(stage,child,started)
            entry.update(finished_at=stamp(),exit_code=code)
            if code:
                record.update(status='failed',failed_stage=stage,finished_at=stamp(),
                    interpretation='Stopped after first failed stage; no retry, relaxed replay or expansion')
                write(RECEIPT,record)
                raise SystemExit(code)
            write(RECEIPT,record)
    record.update(status='complete',finished_at=stamp(),wall_seconds=time.monotonic()-started,
        physical_review_sha256=sha(OUTPUT/'physical_review.json'),
        analysis_audit_sha256=sha(OUTPUT/'analysis_final/analysis_audit.json'))
    write(RECEIPT,record)
    print(json.dumps(dict(status='complete',output=str(OUTPUT),receipt=str(RECEIPT))),flush=True)


if __name__=='__main__':main()
