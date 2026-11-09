"""Strict old-evidence preservation and fresh bounded phase gates."""
from pathlib import Path
from common import HERE,read,sha,write,stamp,validate_seal,require_unoptimized
from cases import (DISCOVERY,HIGH,HIGH_BULK,DISPATCH,BULK,all_cases,retained_cases,prior_case,
    smoke_cases,phase_cases,phase_record,DT,DURATION)

PRIOR_FINAL=HIGH_BULK/'full_36T_v1'
PRIOR_INDEPENDENT=HIGH_BULK/'independent_complete_map_review.json'

def verify_discovery(deep=True):
    protocol=read(HERE/'protocol.json');authority=read(HERE/'design_authorization.json')
    if (sha(HERE/'design_authorization.json')!=protocol['design_authorization_sha256']
            or authority.get('approved') is not True or authority.get('new_gannet_counts')!=[24,36]
            or authority.get('herding_minima_T')!=[1,2,3] or authority.get('new_full_cases')!=32
            or authority.get('all_stage_native_step_ceiling')!=937600):
        raise RuntimeError('Exact root-authorized balanced upper-count scope required')
    frozen=read(DISPATCH/'DISPATCH_FREEZE.json')
    for path,digest in frozen['source_sha256'].items():
        if sha(path)!=digest:raise RuntimeError('Prior frozen source changed: '+path)
    status=read(PRIOR_FINAL/'status.json');physical=read(PRIOR_FINAL/'physical_review.json')
    audit=read(PRIOR_FINAL/'analysis_final/analysis_audit.json');independent=read(PRIOR_INDEPENDENT)
    if (sha(PRIOR_INDEPENDENT)!='1c5d5063e9bea9e8eb1c2f533da433ee73b14f726d7dec9c76accf191d94be01'
            or status.get('status')!='complete' or status.get('complete')!=48
            or physical.get('status')!='passed' or audit.get('status')!='passed'
            or len(audit.get('case_completion_sha256',{}))!=108):
        raise RuntimeError('Completed independent108-outcome bank required')
    for case in retained_cases():
        folder=prior_case(case)
        if sha(folder/'completion.json')!=audit['case_completion_sha256'][case.name]:
            raise RuntimeError('Retained completed-case seal changed')
        if deep:validate_seal(folder)
    for name in ('regime_controller.py','gannet.py','horizons.py','cadence.py','review_actual.py'):
        if sha(HERE/name)!=sha(HIGH/name):raise RuntimeError('Physical/controller/audit module changed: '+name)
    return frozen

def base_sources():
    original=verify_discovery()
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('protocol.json','analysis_plan.json','runtime_projection.json',
        'root_scope.md','design_authorization.json','README.md')]
    paths += [DISPATCH/'DISPATCH_FREEZE.json',PRIOR_INDEPENDENT]
    paths += [PRIOR_FINAL/n for n in ('status.json','physical_review.json','dispatch_analysis_binding.json',
        'analysis_final/analysis_audit.json','analysis_final/case_outcomes.csv',
        'analysis_final/paired_school_changes.csv','analysis_final/regime_summary.csv')]
    for case in retained_cases():
        folder=prior_case(case);seal=validate_seal(folder)
        paths += [folder/'completion.json']+[folder/name for name in seal['files']]
    result=dict(original['source_sha256']);result.update({str(p.resolve()):sha(p) for p in paths})
    return result

def verify_input_freeze():
    frozen=read(HERE/'INPUT_FREEZE.json');pure=read(HERE/'PURE_PREFLIGHT.json')
    if (frozen['source_sha256']!=base_sources() or frozen['pure_preflight_sha256']!=sha(HERE/'PURE_PREFLIGHT.json')
            or pure.get('status')!='passed' or pure.get('pure_new_cases')!=32
            or pure.get('exact_retained_initial_receipts')!=108
            or pure.get('native_constructions')!=0 or pure.get('native_steps')!=0):
        raise RuntimeError('Exact source/input/pure-state freeze required')
    return frozen

def verify_source_freeze():
    inputs=verify_input_freeze();frozen=read(HERE/'frozen_sources.json');actual=read(HERE/'ACTUAL_ZERO_STEP.json')
    if (frozen['input_freeze_sha256']!=sha(HERE/'INPUT_FREEZE.json')
            or frozen['actual_zero_step_sha256']!=sha(HERE/'ACTUAL_ZERO_STEP.json')
            or actual.get('status')!='passed' or actual.get('actual_cases')!=32
            or actual.get('native_steps')!=0 or actual.get('native_constructions')!=32
            or actual.get('input_freeze_sha256')!=sha(HERE/'INPUT_FREEZE.json')):
        raise RuntimeError('All32 approved exact actual starts required before stepping')
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
        'pilot':(230400,'frozen_sources.json','PILOT_RUN_APPROVED.json'),
        'remainder':(691200,'frozen_sources.json','REMAINDER_RUN_APPROVED.json')}
    if stage not in limits:raise ValueError('Unknown bounded phase; no aggregate full-run authority')
    ceiling,freeze_name,approval_name=limits[stage]
    frozen=verify_input_freeze() if stage=='initialization' else verify_source_freeze()
    approval=read(HERE/approval_name)
    if (approval.get('approved') is not True or approval.get('stage')!=stage
            or approval.get('protocol_sha256')!=sha(HERE/'protocol.json')
            or approval.get('freeze_sha256')!=sha(HERE/freeze_name)
            or approval.get('maximum_native_steps')!=ceiling
            or approval.get('workers')!=(1 if stage=='initialization' else 8)
            or approval.get('case_names')!=[c.name for c in (all_cases() if stage=='initialization' else phase_cases(stage))]):
        raise RuntimeError('Fresh exact phase approval required')
    if stage=='initialization' and approval.get('maximum_native_constructions')!=32:
        raise RuntimeError('Exactly32 approved zero-step constructions')
    if stage in ('pilot','remainder'):
        smoke=phase_record('smoke');status=read(smoke/'status.json');physical=read(smoke/'physical_review.json')
        if status.get('status')!='complete' or status.get('complete')!=5 or physical.get('status')!='passed':
            raise RuntimeError('All five smokes and physical review required')
        for case in smoke_cases():validate_candidate_seal(BULK/'smoke_4T_v1/cases'/case.name,duration=4.)
        if approval.get('smoke_review_sha256')!=sha(smoke/'physical_review.json'):
            raise RuntimeError('Phase approval must bind current smoke review')
    if stage=='remainder':
        pilot=phase_record('pilot');status=read(pilot/'status.json');physical=read(pilot/'physical_review.json')
        independent=read(HERE/'INDEPENDENT_PILOT_REVIEW.json')
        if (status.get('status')!='complete' or status.get('complete')!=8 or physical.get('status')!='passed'
                or independent.get('status')!='passed'
                or approval.get('pilot_review_sha256')!=sha(pilot/'physical_review.json')
                or approval.get('independent_pilot_review_sha256')!=sha(HERE/'INDEPENDENT_PILOT_REVIEW.json')):
            raise RuntimeError('Complete independently audited pilot required before remainder')
        for case in phase_cases('pilot'):validate_candidate_seal(BULK/'full_36T_v1/cases'/case.name)
    return frozen

def validate_candidate_seal(folder,duration=DURATION):
    folder=Path(folder);seal=validate_seal(folder);summary=read(folder/'summary.json');audit=read(folder/'audit.json')
    observed=summary['actual_duration'];absorbing=summary.get('native_absorbing_termination') is True
    if (summary['dt']!=DT or summary.get('planned_duration')!=duration or observed<=0 or observed>duration+1e-7
            or summary['native_steps']!=round(observed/DT)
            or (not absorbing and abs(observed-duration)>1e-7)
            or (absorbing and (summary['final_count']!=0 or sum(v['captures'] for v in summary['per_actor'].values())!=160))):
        raise RuntimeError('Exact native horizon or valid absorbing depletion required')
    if audit.get('status')!='passed' or audit.get('errors'):raise RuntimeError('Case accounting failed')
    if read(folder/'source_manifest.json')!=source_manifest():raise RuntimeError('Case source receipt differs')
    return seal

def validate_retained_case(case):
    if not case.retained:raise ValueError('Only sealed retained outcomes')
    folder=prior_case(case);seal=validate_seal(folder);summary=read(folder/'summary.json')
    if summary['dt']!=DT or summary['native_steps']!=28800 or abs(summary['actual_duration']-36)>1e-7:
        raise RuntimeError('Retained full36T encounter changed')
    old=read(PRIOR_FINAL/'analysis_final/analysis_audit.json')
    if sha(folder/'completion.json')!=old['case_completion_sha256'][case.name]:raise RuntimeError('Retained seal differs')
    origin=DISCOVERY if case.gannets<=6 else HIGH
    if read(folder/'source_manifest.json')!=read(origin/'frozen_sources.json')['source_sha256']:
        raise RuntimeError('Retained source differs')
    return seal
