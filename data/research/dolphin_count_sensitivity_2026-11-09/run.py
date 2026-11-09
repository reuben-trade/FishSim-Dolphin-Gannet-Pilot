"""Bounded D24 phase scheduling; no constructor or step at import/plan."""
import os
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import fcntl
import json
from pathlib import Path
from common import HERE, ROOT, sha, stamp, write as write_json, reserve
from cases import (SEEDS, DT, CAPTURE_SEED, TASK_LEASE, phase_cases, phase_output, phase_record, execution_stages, selected_regimes)
from evidence import require_approval, verify_source_freeze
from physical_run import run_case

def _execute_wave(cases, output, duration, workers, completed, record, planned):
    if not cases:return
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(run_case,c.school_seed,c.policy,str(output),duration,CAPTURE_SEED,True,c.presence):c for c in cases}
        for future in as_completed(pending):
            case=pending[future];summary=future.result()
            completed.append(dict(case=case.asdict(),species=summary['species'],wall_seconds=summary['wall_seconds']))
            write_json(record/'status.json',dict(status='running',complete=len(completed),planned=planned,at=stamp(),cases=completed))
            print(json.dumps(dict(complete=len(completed),case=case.name,species=summary['species'])),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan',action='store_true')
    for name in ('smoke','pilot','remainder'):mode.add_argument('--'+name,action='store_true')
    parser.add_argument('--workers',type=int,choices=tuple(range(1,9)),default=8)
    args=parser.parse_args()
    if args.plan:
        selected = (HERE/'selected_regimes.json').exists()
        print(json.dumps(dict(status='plan_only', native_constructions=0, native_steps=0, actual_selection_present=selected,
            independent_schools=4, full_maximum_native_steps=460800, smoke_maximum_native_steps=12800, all_stage_maximum_native_steps=473600,
            stages={s:[dict(name=n,cases=len(c)) for n,c in execution_stages(s)] for s in ('smoke','pilot','remainder')} if selected else {})))
        return
    stage=next(s for s in ('smoke','pilot','remainder') if getattr(args,s))
    require_approval(stage);output=phase_output(stage);record=phase_record(stage)
    if record.exists():parser.error('Fresh phase record only; preserve prior attempts without automatic retry')
    expected={c.name for c in phase_cases('pilot')} if stage=='remainder' else set()
    existing={p.name for p in (output/'cases').glob('*')} if output.exists() else set()
    if existing!=expected:parser.error('Phase output contains unexpected or partial case folders')
    reserve(output);record.mkdir(parents=True);output.mkdir(parents=True,exist_ok=True)
    completed=[];duration=4. if stage=='smoke' else 36.;planned=len(phase_cases(stage))
    maximum=planned*round(duration/DT)
    if planned > (4 if stage in ('smoke','pilot') else 12):raise RuntimeError('Bounded D24 phase inventory exceeded')
    execution=dict(status='running',at=stamp(),mode=stage,duration=duration,workers=args.workers,
        maximum_native_steps=maximum,protocol_sha256=sha(HERE/'protocol.json'),frozen_sources_sha256=sha(HERE/'frozen_sources.json'))
    write_json(record/'execution.json',execution)
    try:
        # Acquire task coordination OUTERMOST, then the unchanged historical native lease.
        with TASK_LEASE.open('a+') as task, (ROOT/'research/herding_gannet_paired_pilot_2026-11-08/native.lock').open('a+') as legacy:
            fcntl.flock(task.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            fcntl.flock(legacy.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            for name,cells in execution_stages(stage):
                _execute_wave(cells,output,duration,args.workers,completed,record,planned)
                write_json(record/(name+'_stage.json'),dict(status='complete',at=stamp(),cases=[c.name for c in cells]))
            verify_source_freeze()
            total=sum(read_summary_steps(output,c['case']['case_name']) for c in completed)
            if len(completed)!=planned or total>maximum:raise RuntimeError('Phase case/step ceiling violated')
            write_json(record/'status.json',dict(status='complete',at=stamp(),complete=len(completed),planned=planned,cases=completed,total_native_steps=total))
            execution.update(status='complete',finished_at=stamp(),total_native_steps=total)
            write_json(record/'execution.json',execution)
    except BaseException as error:
        write_json(record/'status.json',dict(status='failed_or_partial',at=stamp(),complete=len(completed),planned=planned,error=repr(error),cases=completed,
            interpretation='Preserve failures/partials. No replacement or automatic retry.'))
        raise


def read_summary_steps(output,name):return json.loads((output/'cases'/name/'summary.json').read_text())['native_steps']

if __name__=='__main__':main()
