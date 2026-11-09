"""Immutable old evidence and fresh reviewed gates for the new count extension."""
from pathlib import Path
from common import HERE,read,sha,write,stamp,validate_seal,require_unoptimized
from cases import DISCOVERY,BULK,all_cases,retained_cases,prior_case,smoke_cases,DT,DURATION

def verify_discovery(deep=True):
    protocol=read(HERE/'protocol.json');authorization=read(HERE/'design_authorization.json')
    if (sha(HERE/'design_authorization.json')!=protocol['design_authorization_sha256']
            or authorization.get('approved') is not True or authorization.get('new_gannet_counts')!=[9,12,18]
            or authorization.get('H')!=[1,2,3] or authorization.get('full_cases')!=48
            or authorization.get('all_stage_native_step_ceiling')!=1398400):
        raise RuntimeError('Exact root-authorized balanced high-count scope required')
    frozen=read(DISCOVERY/'frozen_sources.json')
    for path,digest in frozen['source_sha256'].items():
        if sha(path)!=digest:raise RuntimeError('Original source changed: '+path)
    output=DISCOVERY/'results/full_36T_v1'
    status=read(output/'status.json');physical=read(output/'physical_review.json');audit=read(output/'analysis_final/analysis_audit.json')
    if (status.get('status')!='complete' or status.get('complete')!=60
            or physical.get('status')!='passed' or audit.get('status')!='passed'
            or len(audit.get('case_completion_sha256',{}))!=60):
        raise RuntimeError('Completed independently audited discovery bank required')
    for case in retained_cases():
        folder=prior_case(case)
        if sha(folder/'completion.json')!=audit['case_completion_sha256'][case.name]:
            raise RuntimeError('Retained discovery seal changed')
        if deep:validate_seal(folder)
    for name in ('regime_controller.py','gannet.py','horizons.py','cadence.py','review_actual.py'):
        if sha(HERE/name)!=sha(DISCOVERY/name):raise RuntimeError('Physical/controller/audit module changed: '+name)
    return frozen

def base_sources():
    original=verify_discovery()
    paths=list(HERE.glob('*.py'))+[HERE/'protocol.json',HERE/'analysis_plan.json',HERE/'runtime_projection.json',HERE/'root_scope.md',HERE/'design_authorization.json',HERE/'README.md']
    paths += [DISCOVERY/'frozen_sources.json']
    output=DISCOVERY/'results/full_36T_v1'
    paths += [output/name for name in ('status.json','anchor_replay.json','physical_review.json','analysis_final/analysis_audit.json',
        'analysis_final/case_outcomes.csv','analysis_final/paired_school_changes.csv','analysis_final/regime_summary.csv')]
    for case in retained_cases():
        folder=prior_case(case);seal=validate_seal(folder)
        paths += [folder/'completion.json']+[folder/name for name in seal['files']]
    result=dict(original['source_sha256']);result.update({str(p.resolve()):sha(p) for p in paths})
    return result

def verify_input_freeze():
    frozen=read(HERE/'INPUT_FREEZE.json')
    pure=read(HERE/'PURE_PREFLIGHT.json')
    if (frozen['source_sha256']!=base_sources() or frozen['pure_preflight_sha256']!=sha(HERE/'PURE_PREFLIGHT.json')
            or pure.get('status')!='passed' or pure.get('pure_new_cases')!=48
            or pure.get('exact_retained_initial_receipts')!=60 or pure.get('native_constructions')!=0 or pure.get('native_steps')!=0):
        raise RuntimeError('Exact new source/input/pure-initial-state freeze required')
    return frozen

def verify_source_freeze():
    inputs=verify_input_freeze();frozen=read(HERE/'frozen_sources.json');actual=read(HERE/'ACTUAL_ZERO_STEP.json')
    if (frozen['input_freeze_sha256']!=sha(HERE/'INPUT_FREEZE.json')
            or frozen['actual_zero_step_sha256']!=sha(HERE/'ACTUAL_ZERO_STEP.json')
            or actual.get('status')!='passed' or actual.get('actual_cases')!=48
            or actual.get('native_steps')!=0 or actual.get('native_constructions')!=48
            or actual.get('input_freeze_sha256')!=sha(HERE/'INPUT_FREEZE.json')):
        raise RuntimeError('All48 approved actual zero-step starts must pass before scientific stepping')
    expected=dict(inputs['source_sha256'])
    for name in ('INPUT_FREEZE.json','PURE_PREFLIGHT.json','ACTUAL_ZERO_STEP.json'):
        expected[str((HERE/name).resolve())]=sha(HERE/name)
    if frozen['source_sha256']!=expected:raise RuntimeError('Final source freeze changed')
    return frozen

def source_manifest():return verify_source_freeze()['source_sha256']

def require_approval(stage):
    require_unoptimized()
    limits={'initialization':(0,'INPUT_FREEZE.json','INITIALIZATION_APPROVED.json'),
            'smoke':(16000,'frozen_sources.json','SMOKE_RUN_APPROVED.json'),
            'full':(1382400,'frozen_sources.json','FULL_RUN_APPROVED.json')}
    if stage not in limits:raise ValueError('Unknown reviewed stage')
    ceiling,freeze_name,approval_name=limits[stage]
    frozen=verify_input_freeze() if stage=='initialization' else verify_source_freeze()
    approval=read(HERE/approval_name)
    if (approval.get('approved') is not True or approval.get('stage')!=stage
            or approval.get('protocol_sha256')!=sha(HERE/'protocol.json')
            or approval.get('freeze_sha256')!=sha(HERE/freeze_name)
            or approval.get('maximum_native_steps')!=ceiling):
        raise RuntimeError('Fresh exact stage approval is required')
    if stage=='initialization' and approval.get('maximum_native_constructions')!=48:
        raise RuntimeError('Exactly48 approved zero-step constructions')
    if stage=='full':
        smoke=BULK/'smoke_4T_v1';status=read(smoke/'status.json');physical=read(smoke/'physical_review.json')
        if status.get('status')!='complete' or status.get('complete')!=5 or physical.get('status')!='passed':
            raise RuntimeError('All five declared smokes and physical review required')
        for case in smoke_cases():validate_candidate_seal(smoke/'cases'/case.name,duration=4.)
        if approval.get('smoke_review_sha256')!=sha(smoke/'physical_review.json'):
            raise RuntimeError('Full approval must bind passed current smoke review')
    return frozen

def validate_candidate_seal(folder,duration=DURATION):
    folder=Path(folder);seal=validate_seal(folder);summary=read(folder/'summary.json');audit=read(folder/'audit.json')
    observed=summary['actual_duration'];absorbing=summary.get('native_absorbing_termination') is True
    if (summary['dt']!=DT or summary.get('planned_duration')!=duration or observed<=0 or observed>duration+1e-7
            or summary['native_steps']!=round(observed/DT)
            or (not absorbing and abs(observed-duration)>1e-7)
            or (absorbing and (summary['final_count']!=0 or sum(v['captures'] for v in summary['per_actor'].values())!=160))):
        raise RuntimeError('Requested full native horizon or absorbing depletion required')
    if audit.get('status')!='passed' or audit.get('errors'):raise RuntimeError('Case accounting failed')
    if read(folder/'source_manifest.json')!=source_manifest():raise RuntimeError('Case source receipt differs')
    return seal

def validate_retained_case(case):
    if not case.retained:raise ValueError('Only sealed retained outcomes')
    folder=prior_case(case);seal=validate_seal(folder);summary=read(folder/'summary.json')
    if summary['dt']!=DT or summary['native_steps']!=28800 or abs(summary['actual_duration']-36)>1e-7:
        raise RuntimeError('Retained full36T encounter changed')
    old=read(DISCOVERY/'results/full_36T_v1/analysis_final/analysis_audit.json')
    if sha(folder/'completion.json')!=old['case_completion_sha256'][case.name]:raise RuntimeError('Retained seal differs')
    if read(folder/'source_manifest.json')!=read(DISCOVERY/'frozen_sources.json')['source_sha256']:
        raise RuntimeError('Retained source differs')
    return seal
