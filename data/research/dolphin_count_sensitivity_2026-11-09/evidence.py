"""Fresh bounded gates; absent complete-map selection keeps all native work closed."""
from pathlib import Path
from common import HERE, read, sha, validate_seal, require_unoptimized
from cases import (UPPER, UPPER_BULK, SEEDS, DT, DURATION, CAPTURE_SEED, all_cases,
    phase_cases, phase_record, phase_output, phase_limit, selected_regimes)
from reference import MAP, MAP_AUDIT, MAP_REVIEW, read_map, reference_path
from select_regimes import select, validate_complete_rows

AUTHORITY = Path('/tmp/FishSim_D24_Study_Design_Authorization_2026-11-09.json')


def validate_selection():
    if not (HERE/'selected_regimes.json').exists():
        raise RuntimeError('D24 native work is not authorized: complete upper-map selection and independent review are absent')
    authority, protocol = read(AUTHORITY), read(HERE/'protocol.json')
    if (authority.get('approved') is not True or authority.get('populations') != [12,24]
            or authority.get('school_seeds') != list(SEEDS) or authority.get('capture_seed') != CAPTURE_SEED
            or authority.get('dt') != DT or authority.get('duration_T') != DURATION
            or authority.get('maximum_full_cases') != 16 or authority.get('all_stage_native_step_ceiling') != 473600
            or protocol.get('design_authorization', {}).get('sha256') != sha(AUTHORITY)):
        raise RuntimeError('Exact D24 design authorization required')
    selected = read(HERE/'selected_regimes.json')
    candidate = read(HERE/'selection_candidate.json')
    selection_review = read(HERE/'INDEPENDENT_SELECTION_REVIEW.json')
    audit, review = read(MAP_AUDIT), read(MAP_REVIEW)
    upper_status = read(UPPER_BULK/'full_36T_v1/status.json')
    upper_physical = read(UPPER_BULK/'full_36T_v1/physical_review.json')
    rows = read_map(); lookup = validate_complete_rows(rows); computed = select(rows)
    bindings = candidate.get('input_bindings', {})
    if (audit.get('status') != 'passed' or audit.get('cells') != 140 or audit.get('mixed_map_cells') != 24
            or audit.get('files', {}).get(MAP.name) != sha(MAP)
            or review.get('status') != 'passed' or review.get('total_cases') != 140
            or review.get('analysis_audit_sha256') != sha(MAP_AUDIT)
            or review.get('case_completion_sha256') != audit.get('case_completion_sha256')
            or upper_status.get('status') != 'complete' or upper_status.get('complete') != 32
            or upper_physical.get('status') != 'passed'
            or review.get('status_sha256') != sha(UPPER_BULK/'full_36T_v1/status.json')
            or review.get('physical_review_sha256') != sha(UPPER_BULK/'full_36T_v1/physical_review.json')
            or bindings.get('csv_sha256') != sha(MAP) or bindings.get('analysis_audit_sha256') != sha(MAP_AUDIT)
            or bindings.get('independent_map_review_sha256') != sha(MAP_REVIEW)):
        raise RuntimeError('Complete independently audited 140-outcome map must precede D24 work')
    if (any(candidate.get(k) != v for k,v in computed.items())
            or selected.get('status') != 'reviewed_complete_map_selection'
            or selected.get('regimes') != candidate['regimes'] or selected.get('input_bindings') != bindings
            or selected.get('candidate_selection_sha256') != sha(HERE/'selection_candidate.json')
            or selected.get('independent_selection_review_sha256') != sha(HERE/'INDEPENDENT_SELECTION_REVIEW.json')
            or selection_review.get('status') != 'passed'
            or selection_review.get('candidate_selection_sha256') != sha(HERE/'selection_candidate.json')):
        raise RuntimeError('Independent A/B selection must bind the integer-ranked complete D12 map')
    for k, row in lookup.items():
        path = reference_path(*k)
        if sha(path/'completion.json') != audit['case_completion_sha256'][row['case_name']]:
            raise RuntimeError('A completed D12-map case seal changed')
    if len(all_cases()) > 16 or len(phase_cases('smoke')) > 4:
        raise RuntimeError('Selected D24 inventory exceeds design')
    return rows


def validate_reference(folder, expected_completion=None):
    folder = Path(folder); seal = validate_seal(folder)
    if expected_completion is not None and sha(folder/'completion.json') != expected_completion:
        raise RuntimeError('Reused reference completion differs from selected map')
    summary, audit = read(folder/'summary.json'), read(folder/'audit.json')
    observed = summary['actual_duration']; terminal = summary.get('native_absorbing_termination') is True
    if (summary['dt'] != DT or summary.get('planned_duration', DURATION) != DURATION
            or observed <= 0 or observed > DURATION+1e-7 or summary['native_steps'] != round(observed/DT)
            or (not terminal and abs(observed-DURATION) > 1e-7) or (terminal and summary['final_count'] != 0)
            or audit.get('status') != 'passed' or audit.get('errors')):
        raise RuntimeError('Reused reference is not a completed physically audited 36T outcome')
    return seal


def base_sources():
    rows = validate_selection(); inherited = read(UPPER/'frozen_sources.json')['source_sha256']
    for p, digest in inherited.items():
        if sha(p) != digest:
            raise RuntimeError('Published/upper frozen source changed: '+p)
    paths = list(HERE.glob('*.py'))+[HERE/n for n in ('README.md','protocol.json','analysis_plan.json',
        'selection_candidate.json','selected_regimes.json','INDEPENDENT_SELECTION_REVIEW.json')]
    paths += [AUTHORITY, MAP, MAP_AUDIT, MAP_REVIEW, UPPER/'frozen_sources.json',
        UPPER_BULK/'full_36T_v1/status.json', UPPER_BULK/'full_36T_v1/physical_review.json']
    lookup = validate_complete_rows(rows)
    for k in lookup:
        paths.append(reference_path(*k)/'completion.json')
    needed = {(s,h,g,12) for s in SEEDS for h,g in selected_regimes()}
    needed |= {(s,h,0,12) for s in SEEDS for h,_ in selected_regimes()}
    needed |= {(s,None,g,0) for s in SEEDS for _,g in selected_regimes()}
    for k in needed:
        folder = reference_path(*k); seal = validate_reference(folder, lookup[k]['completion_sha256'])
        paths.extend([folder/'completion.json']+[folder/name for name in seal['files']])
    result = dict(inherited); result.update({str(p.resolve()):sha(p) for p in paths})
    return result


def verify_input_freeze():
    frozen, pure = read(HERE/'INPUT_FREEZE.json'), read(HERE/'PURE_PREFLIGHT.json')
    if (frozen.get('source_sha256') != base_sources() or frozen.get('pure_preflight_sha256') != sha(HERE/'PURE_PREFLIGHT.json')
            or pure.get('status') != 'passed' or pure.get('fixture_only') is not False
            or pure.get('actual_regimes_selected') is not True or pure.get('pure_D24_fixture_states') != len(all_cases())
            or pure.get('native_constructions') != 0 or pure.get('native_steps') != 0):
        raise RuntimeError('Fresh selected-regime source/input/pure-state freeze required')
    return frozen


def verify_source_freeze():
    inputs = verify_input_freeze(); frozen, actual = read(HERE/'frozen_sources.json'), read(HERE/'ACTUAL_ZERO_STEP.json')
    expected = dict(inputs['source_sha256'])
    for name in ('INPUT_FREEZE.json','PURE_PREFLIGHT.json','ACTUAL_ZERO_STEP.json'):
        expected[str((HERE/name).resolve())] = sha(HERE/name)
    if (frozen.get('source_sha256') != expected or frozen.get('input_freeze_sha256') != sha(HERE/'INPUT_FREEZE.json')
            or frozen.get('actual_zero_step_sha256') != sha(HERE/'ACTUAL_ZERO_STEP.json')
            or actual.get('status') != 'passed' or actual.get('actual_cases') != len(all_cases())
            or actual.get('native_constructions') != len(all_cases()) or actual.get('native_steps') != 0
            or actual.get('input_freeze_sha256') != sha(HERE/'INPUT_FREEZE.json')):
        raise RuntimeError('Fresh exact actual-start verification required before scientific steps')
    return frozen


def source_manifest():
    return verify_source_freeze()['source_sha256']


def require_approval(stage):
    require_unoptimized(); validate_selection()
    if stage not in ('initialization','smoke','pilot','remainder'):
        raise ValueError('Only separately bounded D24 phases; no aggregate full-run permission')
    freeze_name = 'INPUT_FREEZE.json' if stage == 'initialization' else 'frozen_sources.json'
    frozen = verify_input_freeze() if stage == 'initialization' else verify_source_freeze()
    review_name = 'INDEPENDENT_SOURCE_REVIEW.json' if stage == 'initialization' else 'INDEPENDENT_INITIALIZATION_REVIEW.json'
    independent = read(HERE/review_name)
    if independent.get('status') != 'passed' or independent.get('freeze_sha256') != sha(HERE/freeze_name):
        raise RuntimeError('Fresh independent source/initialization review must bind this freeze')
    approval = read(HERE/(stage.upper()+'_APPROVED.json'))
    ceiling = 0 if stage == 'initialization' else phase_limit(stage)
    cells = all_cases() if stage == 'initialization' else phase_cases(stage)
    if (approval.get('approved') is not True or approval.get('stage') != stage
            or approval.get('protocol_sha256') != sha(HERE/'protocol.json') or approval.get('freeze_sha256') != sha(HERE/freeze_name)
            or approval.get('independent_review_sha256') != sha(HERE/review_name) or approval.get('maximum_native_steps') != ceiling
            or approval.get('workers') != (1 if stage == 'initialization' else 8)
            or approval.get('case_names') != [c.name for c in cells]
            or (stage == 'initialization' and approval.get('maximum_native_constructions') != len(cells))):
        raise RuntimeError('Fresh exact D24 phase approval required')
    if stage in ('pilot','remainder'):
        priors = [('smoke','INDEPENDENT_SMOKE_REVIEW.json')]
        if stage == 'remainder':
            priors.append(('pilot','INDEPENDENT_PILOT_REVIEW.json'))
        for prior, independent_name in priors:
            status, physical = read(phase_record(prior)/'status.json'), read(phase_record(prior)/'physical_review.json')
            review = read(HERE/independent_name)
            if (status.get('status') != 'complete' or status.get('complete') != len(phase_cases(prior))
                    or physical.get('status') != 'passed' or review.get('status') != 'passed'
                    or review.get('physical_review_sha256') != sha(phase_record(prior)/'physical_review.json')
                    or approval.get(prior+'_review_sha256') != sha(phase_record(prior)/'physical_review.json')
                    or approval.get('independent_'+prior+'_review_sha256') != sha(HERE/independent_name)):
                raise RuntimeError('Complete independently audited '+prior+' phase required')
            for case in phase_cases(prior):
                validate_candidate_seal(phase_output(prior)/'cases'/case.name, 4. if prior == 'smoke' else DURATION)
    return frozen


def validate_candidate_seal(folder, duration=DURATION):
    folder = Path(folder); seal = validate_seal(folder)
    summary, audit = read(folder/'summary.json'), read(folder/'audit.json')
    observed = summary['actual_duration']; terminal = summary.get('native_absorbing_termination') is True
    if (summary['dt'] != DT or summary.get('planned_duration') != duration or observed <= 0 or observed > duration+1e-7
            or summary['native_steps'] != round(observed/DT) or (not terminal and abs(observed-duration) > 1e-7)
            or (terminal and (summary['final_count'] != 0 or sum(v['captures'] for v in summary['per_actor'].values()) != 160))
            or audit.get('status') != 'passed' or audit.get('errors') or read(folder/'source_manifest.json') != source_manifest()):
        raise RuntimeError('Exact D24 native horizon/accounting/source seal required')
    return seal
