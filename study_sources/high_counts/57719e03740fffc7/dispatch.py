"""Reviewed scheduling amendment around an unchanged, sealed scientific runner."""
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from contextlib import contextmanager
import argparse,fcntl,hashlib,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FROZEN=ROOT/'research/high_count_regime_extension_2026-11-09'
sys.path[:0]=[str(FROZEN),str(ROOT),str(ROOT/'lib')]
import cases as identities
import run as scientific_runner
import evidence as scientific_evidence
from common import reserve
from review_actual import audit_case
from analyze import case_row,write_csv

BULK=identities.BULK
OUTPUT=BULK/'full_36T_v1'
PILOT_SEED=39061001
LIMITS={'pilot':345600,'remainder':1036800}
MAX_WORKERS=8

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.now(ZoneInfo('Australia/Perth')).isoformat()
def write(path,value):
    path=Path(path);temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(path)
def phase_dir(phase):return BULK/f'dispatch_{phase}_v1'

def phase_cases(phase):
    if phase not in LIMITS:raise ValueError('Unknown bounded execution phase')
    return tuple(c for c in identities.all_cases() if (c.school_seed==PILOT_SEED)==(phase=='pilot'))

def stages(phase):
    cells=phase_cases(phase)
    if phase=='pilot':
        return (('all_three_G_only',tuple(c for c in cells if not c.dolphins)),
            ('all_nine_mixed',tuple(c for n in identities.NEW_COUNTS for c in cells if c.dolphins and c.gannets==n)))
    return (('all_nine_G_only',tuple(c for c in cells if not c.dolphins)),
        ('all_twenty_seven_mixed',tuple(c for n in identities.NEW_COUNTS for c in cells if c.dolphins and c.gannets==n)))

def bound_sources():
    authorization=read(HERE/'parallelism_authorization.json');amendment=read(HERE/'amendment.json')
    if (authorization.get('approved') is not True or authorization.get('maximum_worker_processes')!=MAX_WORKERS
            or authorization.get('numeric_threads_per_process')!=1
            or amendment.get('parallelism_authorization_sha256')!=sha(HERE/'parallelism_authorization.json')
            or amendment.get('pure_parallel_resource_audit_sha256')!=sha(HERE/'pure_parallel_resource_audit.json')):
        raise RuntimeError('Exact independently authorized parallelism is required')
    frozen=scientific_evidence.verify_source_freeze()
    paths=list(HERE.glob('*.py'))+[HERE/'amendment.json',HERE/'parallelism_authorization.json',HERE/'pure_parallel_resource_audit.json',FROZEN/'frozen_sources.json']
    paths += [FROZEN/name for name in ('INITIALIZATION_APPROVED.json','SMOKE_RUN_APPROVED.json',
        'INDEPENDENT_SOURCE_REVIEW.json','INDEPENDENT_INITIALIZATION_REVIEW.json','INDEPENDENT_SMOKE_REVIEW.json')]
    smoke=BULK/'smoke_4T_v1'
    if read(smoke/'status.json').get('complete')!=5 or read(smoke/'physical_review.json').get('status')!='passed':
        raise RuntimeError('All original five physical smokes must pass')
    paths += [smoke/'status.json',smoke/'physical_review.json']
    for case in identities.smoke_cases():
        folder=smoke/'cases'/case.name;seal=scientific_evidence.validate_candidate_seal(folder,duration=4.)
        paths += [folder/'completion.json']+[folder/name for name in seal['files']]
    result=dict(frozen['source_sha256']);result.update({str(p.resolve()):sha(p) for p in paths})
    return result

def verify_freeze():
    frozen=read(HERE/'DISPATCH_FREEZE.json')
    if frozen['source_sha256']!=bound_sources():raise RuntimeError('Dispatch/source/smoke equivalence freeze changed')
    return frozen

def require_phase(phase):
    if not __debug__:raise RuntimeError('Unoptimized assertions required')
    verify_freeze();approval=read(HERE/(phase.upper()+'_RUN_APPROVED.json'))
    if (approval.get('approved') is not True or approval.get('phase')!=phase
            or approval.get('dispatch_freeze_sha256')!=sha(HERE/'DISPATCH_FREEZE.json')
            or approval.get('amendment_sha256')!=sha(HERE/'amendment.json')
            or approval.get('maximum_native_steps')!=LIMITS[phase]
            or approval.get('bridge_template_sha256')!=sha(HERE/'COMPATIBILITY_BRIDGE_TEMPLATE.json')):
        raise RuntimeError('Fresh exact bounded dispatch phase approval required')
    if phase=='remainder':
        review=read(phase_dir('pilot')/'pilot_review.json')
        if (review.get('status')!='passed' or review.get('cases')!=12
                or approval.get('pilot_review_sha256')!=sha(phase_dir('pilot')/'pilot_review.json')):
            raise RuntimeError('Completed pilot audit and independently bound remainder approval required')
    return approval

@contextmanager
def protected_compatibility_bridge(phase):
    """A compatibility flag exists only while this bounded driver owns the lease."""
    template=HERE/'COMPATIBILITY_BRIDGE_TEMPLATE.json';active=FROZEN/'FULL_RUN_APPROVED.json'
    with (ROOT/'research/herding_gannet_paired_pilot_2026-11-08/native.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if active.exists():raise RuntimeError('Refuse an existing standalone full approval')
        with active.open('xb') as handle:handle.write(template.read_bytes())
        try:
            scientific_evidence.require_approval('full')
            yield
        finally:
            if sha(active)!=sha(template):raise RuntimeError('Active bridge changed; preserve for review')
            archive=phase_dir(phase)/'activated_frozen_runner_bridge.json'
            with archive.open('xb') as handle:handle.write(active.read_bytes())
            active.unlink()

def run_bound_case(case,phase):
    approval=require_phase(phase)
    if case not in phase_cases(phase):raise RuntimeError('Case outside the bounded phase')
    result=scientific_runner.run_case(case.school_seed,case.policy,str(OUTPUT),36.,identities.CAPTURE_SEED,True,case.presence)
    summary=read(OUTPUT/'cases'/case.name/'summary.json')
    manifest=dict(case=case.asdict(),phase=phase,dispatch_freeze_sha256=sha(HERE/'DISPATCH_FREEZE.json'),
        amendment_sha256=sha(HERE/'amendment.json'),phase_approval_sha256=sha(HERE/(phase.upper()+'_RUN_APPROVED.json')),
        scientific_source_freeze_sha256=sha(FROZEN/'frozen_sources.json'),
        scientific_completion_sha256=sha(OUTPUT/'cases'/case.name/'completion.json'),native_steps=summary['native_steps'])
    path=OUTPUT/'case_dispatch_manifests'/f'{case.name}.json'
    if path.exists():raise RuntimeError('Never overwrite a dispatch companion')
    write(path,manifest)
    return dict(case=case.asdict(),native_steps=summary['native_steps'],species=summary['species'],wall_seconds=summary['wall_seconds'],
        dispatch_manifest_sha256=sha(path))

def verify_companions(completed):
    for row in completed:
        name=row['case']['case_name'];path=OUTPUT/'case_dispatch_manifests'/f'{name}.json';manifest=read(path)
        if (sha(path)!=row['dispatch_manifest_sha256'] or manifest['case']!=row['case']
                or manifest['dispatch_freeze_sha256']!=sha(HERE/'DISPATCH_FREEZE.json')
                or manifest['scientific_completion_sha256']!=sha(OUTPUT/'cases'/name/'completion.json')):
            raise RuntimeError('Each scientific case must retain its exact dispatch companion')

def describe_pilot_count(count):
    cells=[c for c in phase_cases('pilot') if c.gannets==count]
    if len(cells)!=4:raise RuntimeError('All four single-school count cells required')
    physical=[audit_case(OUTPUT/'cases'/c.name) for c in cells]
    rows=[case_row(OUTPUT/'cases'/c.name,c) for c in cells]
    birds=next(r for r in rows if not r['dolphins']);contrasts=[]
    for h in identities.HERDING_MINIMA:
        mixed=next(r for r in rows if r['herding_minimum_T']==h)
        alone=next(c for c in identities.retained_cases() if c.school_seed==PILOT_SEED and c.herding_minimum==h and c.gannets==0)
        d=case_row(identities.prior_case(alone),alone)
        contrasts.append(dict(school_seed=PILOT_SEED,H=h,G=count,D_alone=d['D_captures'],D_mixed=mixed['D_captures'],
            D_change=mixed['D_captures']-d['D_captures'],G_alone=birds['G_captures'],G_mixed=mixed['G_captures'],
            G_change=mixed['G_captures']-birds['G_captures']))
    dest=phase_dir('pilot')/f'G{count}_description';dest.mkdir(exist_ok=False)
    write_csv(dest/'all_four_case_outcomes.csv',rows);write_csv(dest/'all_three_H_contrasts.csv',contrasts)
    write(dest/'physical_descriptive_receipt.json',dict(status='passed',count=count,cases=4,independent_schools=1,
        physical=physical,uncertainty=False,selection=False,full48_still_required=True,
        interpretation='One fixed school only,allH included; descriptive feeding pilot,not an ensemble or evidence of robustness',
        dispatch_freeze_sha256=sha(HERE/'DISPATCH_FREEZE.json'),files={p.name:sha(p) for p in dest.iterdir() if p.is_file()}))

def execute(phase):
    require_phase(phase);reserve(OUTPUT);directory=phase_dir(phase);directory.mkdir(parents=True,exist_ok=False)
    if phase=='pilot':
        OUTPUT.mkdir(exist_ok=False);(OUTPUT/'case_dispatch_manifests').mkdir();completed=[]
    else:
        completed=read(OUTPUT/'status.json')['cases']
        if len(completed)!=12:raise RuntimeError('Exactly the completed pilot inventory must precede remainder')
        verify_companions(completed)
    execution=dict(status='running',phase=phase,at=stamp(),pid=os.getpid(),maximum_native_steps=LIMITS[phase],
        dispatch_freeze_sha256=sha(HERE/'DISPATCH_FREEZE.json'),phase_approval_sha256=sha(HERE/(phase.upper()+'_RUN_APPROVED.json')),
        case_names=[c.name for c in phase_cases(phase)],maximum_workers=MAX_WORKERS,numeric_threads_per_worker=1,stages=[])
    write(directory/'execution.json',execution)
    try:
        with protected_compatibility_bridge(phase):
            for name,cells in stages(phase):
                with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
                    pending={pool.submit(run_bound_case,c,phase):c for c in cells}
                    while pending:
                        finished,_=wait(pending,timeout=20,return_when=FIRST_COMPLETED)
                        for future in finished:
                            case=pending.pop(future);row=future.result();completed.append(row)
                            write(OUTPUT/'status.json',dict(status='running',complete=len(completed),planned=48,cases=completed,at=stamp()))
                            print(json.dumps(dict(phase=phase,complete=len(completed),case=case.name)),flush=True)
                            if phase=='pilot':
                                done={r['case']['case_name'] for r in completed}
                                for n in identities.NEW_COUNTS:
                                    required={c.name for c in phase_cases('pilot') if c.gannets==n}
                                    if required<=done and not (directory/f'G{n}_description').exists():describe_pilot_count(n)
                        progress=[]
                        for case in pending.values():
                            path=OUTPUT/'cases'/case.name/'progress.json'
                            if path.exists():
                                value=read(path);progress.append(dict(case=case.name,native_steps=value.get('native_steps',0),elapsed=value.get('elapsed',0)))
                        write(directory/'heartbeat.json',dict(at=stamp(),phase=phase,stage=name,complete=len(completed),active=progress))
                execution['stages'].append(dict(stage=name,status='complete',at=stamp(),cases=[c.name for c in cells]));write(directory/'execution.json',execution)
        verify_freeze();verify_companions(completed)
        own=[r for r in completed if r['case']['case_name'] in {c.name for c in phase_cases(phase)}]
        if len(own)!=len(phase_cases(phase)) or sum(r['native_steps'] for r in own)>LIMITS[phase]:raise RuntimeError('Bounded phase inventory/budget differs')
        execution.update(status='complete',finished_at=stamp(),native_steps=sum(r['native_steps'] for r in own));write(directory/'execution.json',execution)
        if phase=='pilot':
            panels=[read(directory/f'G{n}_description/physical_descriptive_receipt.json') for n in identities.NEW_COUNTS]
            physical=[r for panel in panels for r in panel['physical']]
            if len(physical)!=12 or {r['case'] for r in physical}!={c.name for c in phase_cases('pilot')}:raise RuntimeError('All12 pilot physical audits required')
            write(directory/'pilot_review.json',dict(status='passed',cases=12,native_steps=execution['native_steps'],independent_schools=1,
                dispatch_freeze_sha256=sha(HERE/'DISPATCH_FREEZE.json'),physical=physical,
                dispatch_companion_sha256={r['case']['case_name']:r['dispatch_manifest_sha256'] for r in own},
                interpretation='Single fixed-school descriptive pilot; all12 complete regardless signs; remaining36 still mandatory'))
            write(OUTPUT/'status.json',dict(status='pilot_complete_pending_reviewed_remainder',complete=12,planned=48,cases=completed,at=stamp()))
        else:
            write(OUTPUT/'status.json',dict(status='complete',complete=48,planned=48,cases=completed,at=stamp(),total_native_steps=sum(r['native_steps'] for r in completed)))
            with (directory/'final_audit_analysis.log').open('x') as log:
                for script in ('review_actual.py','analyze.py'):
                    command=[sys.executable,str(FROZEN/script)]+(['--output',str(OUTPUT)] if script=='review_actual.py' else ['--input',str(OUTPUT)])
                    subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            write(OUTPUT/'dispatch_analysis_binding.json',dict(status='passed',dispatch_freeze_sha256=sha(HERE/'DISPATCH_FREEZE.json'),
                original_analysis_sha256=sha(OUTPUT/'analysis_final/analysis_audit.json'),
                phase_execution_sha256={p:sha(phase_dir(p)/'execution.json') for p in LIMITS},
                companions={p.name:sha(p) for p in (OUTPUT/'case_dispatch_manifests').glob('*.json')}))
        print(json.dumps(dict(status='complete',phase=phase,cases=len(own),native_steps=execution['native_steps'])),flush=True)
    except BaseException as error:
        execution.update(status='failed_or_partial',error=repr(error),finished_at=stamp());write(directory/'execution.json',execution)
        raise

def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze',action='store_true');mode.add_argument('--pilot',action='store_true');mode.add_argument('--remainder',action='store_true')
    args=parser.parse_args()
    if args.freeze:
        path=HERE/'DISPATCH_FREEZE.json'
        if path.exists():raise RuntimeError('Never overwrite dispatch freeze')
        write(path,dict(status='frozen_before_any36Tfeeding',at=stamp(),source_sha256=bound_sources(),native_steps=0));print(path)
    else:execute('pilot' if args.pilot else 'remainder')

if __name__=='__main__':main()
