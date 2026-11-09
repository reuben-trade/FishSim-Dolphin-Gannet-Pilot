"""Explicit gates for a new model example, unrelated to historical study gates."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

from regime_runtime import HERE as ADAPTER, STUDY, read, sha, verify_runtime, interface_hashes


def _context():
    runtime = Path(os.environ['FISHSIM_REGIME_EXAMPLE_RUNTIME']).resolve()
    approval_path = Path(os.environ['FISHSIM_REGIME_EXAMPLE_REQUEST']).resolve()
    declaration = verify_runtime(runtime)
    approval = read(approval_path)
    required = dict(schema='fishsim_regime_example_execution_request_v1', explicit_local_opt_in=True,
                    independent_review=False, request_kind='local_model_execution',
                    runtime_declaration_sha256=sha(runtime / 'REGIME_RUNTIME_DECLARATION.json'))
    if any(approval.get(k) != v for k, v in required.items()):
        raise RuntimeError('Explicit local execution request must bind this distinct derived runtime')
    if 'approved' in approval:
        raise RuntimeError('Local execution requests must not impersonate independent approval receipts')
    if approval.get('historical_anchor_authorization') is not False:
        raise RuntimeError('Example authorization must not claim historical anchor replay authority')
    if approval.get('interface_files') != interface_hashes():
        raise RuntimeError('Local request generator/interface bytes differ from the source binding')
    review = read(ADAPTER / 'INTERFACE_SOURCE_REVIEW.json')
    if (review.get('schema') != 'fishsim_regime_example_interface_source_review_v1'
            or review.get('status') != 'passed' or review.get('review_kind') != 'independent_source_review'
            or review.get('interface_files') != interface_hashes()
            or review.get('package_manifests') != declaration['package_manifests']):
        raise RuntimeError('The complete execution interface needs independent source review before native work')
    return runtime, declaration, approval_path, approval


def require_example_case(seed, policy, presence, capture_seed, duration, output):
    runtime, declaration, _, approval = _context()
    expected = dict(school_seed=seed, policy=policy, presence=presence, capture_seed=capture_seed,
                    duration_T=duration)
    if approval.get('stage') != 'bounded_example_integration' or expected not in approval.get('cases', []):
        raise RuntimeError('This exact new example case/horizon needs a fresh scoped review')
    steps = round(duration / .00125)
    if duration not in (.5, 2., 4.) or abs(steps * .00125 - duration) > 1e-12:
        raise ValueError('Example integration is bounded to .5T/2T/4T, with no full-study run mode')
    if capture_seed != 61001 or not approval.get('maximum_native_steps', 0) >= sum(
            round(c['duration_T'] / .00125) for c in approval['cases']):
        raise RuntimeError('Invalid private-stream label or integration budget')
    output = Path(output).resolve()
    if output != Path(approval['output']).resolve():
        raise ValueError('New example output differs from its one-shot reviewed destination')
    if output == runtime or output.is_relative_to(runtime):
        raise ValueError('New outputs must be outside the immutable runtime input tree')
    if shutil.disk_usage(declaration['package']).free < 2**30 or shutil.disk_usage(output).free < 2*2**30:
        raise RuntimeError('Preserve1GiB source-filesystem and2GiB output-filesystem reserves')


def require_example_build(seed, policy, presence, capture_seed, stage):
    """New artifact gate only; never activate the archived study approvals."""
    runtime, declaration, _, approval = _context()
    if capture_seed != 61001:
        raise RuntimeError('Only the exact frozen capture-stream label61001 is allowed')
    if approval.get('stage') == 'zero_step_initialization':
        if stage != 'initialization' or approval.get('native_constructions') != 108 or approval.get('maximum_native_steps') != 0:
            raise RuntimeError('Only the separately reviewed108 zero-step constructions are allowed')
    elif approval.get('stage') == 'bounded_example_integration':
        valid = [c for c in approval.get('cases', []) if c['school_seed'] == seed
                 and c['policy'] == policy and c['presence'] == presence and c['capture_seed'] == capture_seed
                 and c['duration_T'] in (.5, 2., 4.) and stage == ('smoke' if c['duration_T'] == 4. else 'full')]
        if len(valid) != 1:
            raise RuntimeError('Constructor identity differs from the new bounded example scope')
    else:
        raise RuntimeError('No reviewed new example construction stage exists')


def example_source_manifest():
    runtime, declaration, approval_path, _ = _context()
    files = {str(runtime / p): h for p, h in declaration['runtime_files'].items()}
    files[str(runtime / 'REGIME_RUNTIME_DECLARATION.json')] = sha(runtime / 'REGIME_RUNTIME_DECLARATION.json')
    files[str(approval_path)] = sha(approval_path)
    files.update({str(ADAPTER / name): digest for name, digest in interface_hashes().items()})
    files[str(ADAPTER / 'INTERFACE_SOURCE_REVIEW.json')] = sha(ADAPTER / 'INTERFACE_SOURCE_REVIEW.json')
    request = read(approval_path)
    for key in ('zero_step_receipt', 'zero_step_seal'):
        if key in request:
            entry = request[key]
            if sha(entry['path']) != entry['sha256']:
                raise RuntimeError('Retained zero-step evidence changed')
            files[entry['path']] = entry['sha256']
    if 'zero_step_seal' in request:
        for filename, digest in read(request['zero_step_seal']['path'])['files'].items():
            if sha(filename) != digest:
                raise RuntimeError('Retained zero-check request/source evidence changed')
            files[filename] = digest
    return files
