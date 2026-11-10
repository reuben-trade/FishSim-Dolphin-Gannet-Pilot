"""Read-only freeze, stage authorization and exact original-anchor replay gates."""
from copy import deepcopy
from dataclasses import asdict
import gzip
import json
from pathlib import Path

import numpy as np

from build import sha, clean, validate_sealed_case
from cases import all_cases, execution_stages, prior_case, smoke_cases, DT, DURATION
from regime_controller import VERSION

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR_VERSION = 'simple_continuous_proximity_herd2T_one_strike_v1'


def original_h2_labels(value):
    """Remove only the explicitly declared H2 schema/version additions."""
    if isinstance(value, dict):
        out = {k: original_h2_labels(v) for k, v in value.items()}
        if 'simple' in out and 'herding_minimum' in out['simple']:
            if out['simple'].pop('herding_minimum') != 2.:
                raise ValueError('Only H2 can be compared with original anchors')
        return out
    if isinstance(value, list):
        return [original_h2_labels(v) for v in value]
    return PRIOR_VERSION if value == VERSION else value


def source_manifest():
    paths = [HERE/name for name in ('build.py', 'cases.py', 'regime_controller.py', 'gannet.py',
        'cadence.py', 'horizons.py', 'evidence.py', 'preflight.py', 'test_regime.py',
        'run.py', 'analyze.py', 'review_actual.py', 'native_zero_step.py', 'protocol.json', 'analysis_plan.json', 'runtime.json',
        'previous_attempt_manifest.json', 'recording_change_review.json')]
    previous = json.loads((HERE/'previous_attempt_manifest.json').read_text())
    for path, digest in previous['files'].items():
        if sha(path) != digest:
            raise RuntimeError('Prior stopped attempt must remain immutable: '+path)
        paths.append(Path(path))
    # Bind every direct imported model module, plus immutable archived source
    # and input dependencies actually recorded by all eight original anchors.
    paths += [ROOT/'research/prey_mediated'/name for name in ('scenario.py', 'reactive_school.py',
        'surface_safe_school.py', 'predators.py', 'encounter.py', 'contacts.py', 'virtual_capture.py')]
    for stage, cases in execution_stages():
        if stage != 'anchor_replay':
            continue
        for case in cases:
            prior = prior_case(case)
            seal = validate_sealed_case(prior)
            paths += [prior/'completion.json']+[prior/name for name in seal['files']]
            bindings = json.loads((prior/'source_manifest.json').read_text())
            for path, digest in bindings.items():
                if sha(path) != digest:
                    raise RuntimeError('Archived source dependency changed: '+path)
            paths += [Path(path) for path in bindings]
    paths += [ROOT/'research/herding_study_2026-11-07'/name for name in (
        'patch_tracking_v2.py', 'geometry_feasibility_v2.py', 'acceleration_v2.py',
        'committed_encounter.py', 'controller_v2.py', 'setup_v2.py', 'v2_numeric_execution_v1.json')]
    paths += [ROOT/'research/herding_study_2026-11-06'/name for name in ('policy.py', 'study_setup.py')]
    paths += [ROOT/'research/multispecies_feeding_study_2026-11-05/model_setup.py',
        ROOT/'research/adaptive_v2_completion_2026-11-08/accounting_v2.py',
        ROOT/'research/project_finish_2026-11-06/contact_logging_v2.py',
        ROOT/'research/overnight_workload_2026-11-08/workload_common.py',
        ROOT/'research/overnight_workload_2026-11-08/v2_engineering_probe_2026-11-08/v2_native_probe.py',
        ROOT/'research/fine_dt_replication_2026-11-09/run.py',
        ROOT/'research/exposed_replication_2026-11-08/checkpoints/manifest.json']
    declaration = json.loads((ROOT/'research/herding_study_2026-11-07/v2_numeric_execution_v1.json').read_text())
    paths.append(Path(declaration['native']['path']))
    baseline_path = ROOT/'research/prey_mediated/BASELINE_V1.json'
    paths += [baseline_path, ROOT/'research/prey_mediated/results/short_angular_physical_g3_v1/manifest.json',
        ROOT/'research/prey_mediated/results/short_angular_physical_g3_v1/native.json']
    baseline = json.loads(baseline_path.read_text())
    paths += [ROOT/entry['checkpoint'] for entry in baseline['development_checkpoints'] if entry['seed']==190001]
    for case in all_cases():
        anchor = next(c for c in execution_stages()[0][1] if c.school_seed == case.school_seed)
        config = json.loads((prior_case(anchor)/'config.json').read_text())
        if config.get('checkpoint_path'):
            paths.append(Path(config['checkpoint_path']))
        else:
            paths.append(Path(declaration['checkpoints'][str(case.school_seed)]['path']))
    return {str(path.resolve()): sha(path) for path in sorted(set(paths))}


def verify_source_freeze():
    frozen = json.loads((HERE/'frozen_sources.json').read_text())
    if source_manifest() != frozen['source_sha256']:
        raise RuntimeError('Frozen regime study source/input changed')
    if sha(HERE/'preflight.json') != frozen['preflight_sha256']:
        raise RuntimeError('Frozen pure preflight changed')
    preflight = json.loads((HERE/'preflight.json').read_text())
    if preflight.get('status') != 'passed' or preflight.get('pure_cases') != 60 or preflight.get('native_constructions') != 0:
        raise RuntimeError('All60 pure preparations and eight archived anchor checks required')
    if sha(HERE/'native_zero_step.json') != frozen['native_zero_step_sha256']:
        raise RuntimeError('Frozen actual zero-step matching changed')
    actual = json.loads((HERE/'native_zero_step.json').read_text())
    if (actual.get('status') != 'passed' or actual.get('actual_cases') != 60
            or actual.get('native_constructions') != 60 or actual.get('native_steps') != 0
            or actual.get('actual_initial_anchor_matches') != 8):
        raise RuntimeError('All60 actual zero-step initializations and eight exact anchor starts required')
    return frozen


def require_approval(stage):
    """No native construction or steps from the CLI before exact root review."""
    frozen = verify_source_freeze()
    if stage not in ('smoke', 'full'):
        raise ValueError('Unknown execution stage')
    path = HERE/('SMOKE_RUN_APPROVED.json' if stage == 'smoke' else 'FULL_RUN_APPROVED.json')
    if not path.exists():
        raise RuntimeError('Root approval required before native '+stage+' construction or stepping')
    receipt = json.loads(path.read_text())
    if (receipt.get('approved') is not True or receipt.get('stage') != stage
            or receipt.get('protocol_sha256') != sha(HERE/'protocol.json')
            or receipt.get('frozen_sources_sha256') != sha(HERE/'frozen_sources.json')):
        raise RuntimeError('Approval does not bind this exact protocol/source freeze and stage')
    return frozen


def _npz_equal(a, b):
    with np.load(a, allow_pickle=False) as x, np.load(b, allow_pickle=False) as y:
        return set(x.files) == set(y.files) and all(np.array_equal(x[k], y[k]) for k in x.files)


def validate_candidate_seal(path, duration=DURATION):
    path = Path(path)
    receipt = json.loads((path/'completion.json').read_text())
    if receipt.get('status') != 'complete' or any(sha(path/name) != digest for name, digest in receipt['files'].items()):
        raise RuntimeError('Candidate completion seal changed: '+str(path))
    summary = json.loads((path/'summary.json').read_text())
    observed = summary['actual_duration']
    absorbing = summary.get('native_absorbing_termination') is True
    if (summary['dt'] != DT or summary.get('planned_duration') != duration
            or summary['native_steps'] != round(observed/DT)
            or observed > duration+1e-7 or observed <= 0
            or (not absorbing and abs(observed-duration) > 1e-7)
            or (absorbing and (summary['final_count'] != 0 or sum(v['captures'] for v in summary['per_actor'].values()) != summary['initial_count']))):
        raise RuntimeError('Candidate does not contain the complete requested native horizon')
    if json.loads((path/'audit.json').read_text()).get('errors'):
        raise RuntimeError('Candidate physical accounting failed')
    bindings = json.loads((path/'source_manifest.json').read_text())
    if bindings != verify_source_freeze()['source_sha256']:
        raise RuntimeError('Candidate did not use the frozen model sources')
    return receipt


def compare_anchor(case, candidate):
    if not case.anchor:
        raise ValueError('A full original anchor is required')
    prior = prior_case(case)
    oldseal = validate_sealed_case(prior)
    newseal = validate_candidate_seal(candidate)
    checks = {}
    for name in ('initial_school.npz', 'final_school.npz', 'trajectories.npz'):
        checks[name] = _npz_equal(prior/name, Path(candidate)/name)
    for name in ('initial_engine.json', 'final_engine.json', 'tie_stream_calls.json'):
        old = json.loads((prior/name).read_text())
        new = original_h2_labels(json.loads((Path(candidate)/name).read_text()))
        checks[name] = old == new
    for name in ('events.jsonl.gz', 'opportunities.jsonl.gz', 'bird_events.jsonl.gz', 'responses.jsonl.gz'):
        with gzip.open(prior/name, 'rt') as old, gzip.open(Path(candidate)/name, 'rt') as new:
            a = [json.loads(line) for line in old]
            b = original_h2_labels([json.loads(line) for line in new])
        checks[name] = a == b
    oldsummary = json.loads((prior/'summary.json').read_text())
    newsummary = json.loads((Path(candidate)/'summary.json').read_text())
    for name in ('species', 'per_actor', 'water_entries', 'initial_count', 'final_count', 'actual_duration', 'native_steps'):
        checks['summary_'+name] = oldsummary[name] == newsummary[name]
    if not all(checks.values()):
        raise RuntimeError('H2 physical anchor replay failed: '+str({k: v for k, v in checks.items() if not v}))
    return dict(case=case.asdict(), status='passed', checks=checks,
        prior_completion_sha256=sha(prior/'completion.json'),
        candidate_completion_sha256=sha(Path(candidate)/'completion.json'),
        schema_allowance='Only new simple-controller version and explicit H2 parameter are normalized')


def validate_anchor_stage(output):
    rows = [compare_anchor(case, Path(output)/'cases'/case.name) for case in execution_stages()[0][1]]
    return dict(status='passed', anchor_cells=8, native_steps=8*round(DURATION/DT),
        replay_is_not_new_independent_evidence=True, checks=rows,
        protocol_sha256=sha(HERE/'protocol.json'), frozen_sources_sha256=sha(HERE/'frozen_sources.json'))


def require_anchor_stage(output):
    path = Path(output)/'anchor_replay.json'
    if not path.exists():
        raise RuntimeError('Eight full original anchors must replay before remaining52 cells')
    previous = json.loads(path.read_text())
    if (previous.get('status') != 'passed' or previous.get('anchor_cells') != 8
            or previous.get('protocol_sha256') != sha(HERE/'protocol.json')
            or previous.get('frozen_sources_sha256') != sha(HERE/'frozen_sources.json')):
        raise RuntimeError('Anchor replay gate has the wrong protocol/source binding')
    anchors = execution_stages()[0][1]
    if len(previous.get('checks', [])) != 8:
        raise RuntimeError('Eight exact replay receipts required')
    for case, row in zip(anchors, previous['checks']):
        path = Path(output)/'cases'/case.name
        if (row.get('case') != case.asdict() or row.get('status') != 'passed'
                or not all(row['checks'].values())
                or row['prior_completion_sha256'] != sha(prior_case(case)/'completion.json')
                or row['candidate_completion_sha256'] != sha(path/'completion.json')):
            raise RuntimeError('Anchor replay receipt changed')
        validate_candidate_seal(path)
    return previous
