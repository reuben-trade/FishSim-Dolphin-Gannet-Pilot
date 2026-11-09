"""Opt-in local example of the published v6 model; default is native-free plan."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from regime_runtime import (HERE, interface_hashes, prepare_runtime, read, safe_output,
                            sha, verify_package, verify_runtime, write)
from run_regime_model import parse as parse_core, plan as core_plan

REQUEST_SCHEMA = 'fishsim_regime_example_execution_request_v1'


def request_payload(runtime, stage, output, cases=(), zero_receipt=None, zero_seal=None):
    """Pure declaration of a local opt-in, never an independent approval."""
    runtime, output = Path(runtime).resolve(), Path(output).resolve()
    declaration = verify_runtime(runtime)
    safe_output(output, declaration['package'])
    if output == runtime or output.is_relative_to(runtime):
        raise ValueError('Execution outputs cannot be inside immutable runtime inputs')
    if stage not in ('zero_step_initialization', 'bounded_example_integration'):
        raise ValueError('Unknown bounded example request stage')
    selected = list(cases)
    if stage == 'zero_step_initialization':
        if selected or zero_receipt or zero_seal:
            raise ValueError('Zero-step request has no integration cases or inherited zero evidence')
        maximum = 0
    else:
        if not selected or zero_receipt is None or zero_seal is None:
            raise ValueError('Bounded integration requires cases and immutable zero-check evidence')
        identities = [(x['school_seed'], x['policy'], x['presence']) for x in selected]
        if len(set(identities)) != len(identities):
            raise ValueError('Each requested model case may run only once')
        if any(x['capture_seed'] != 61001 or x['duration_T'] not in (.5, 2., 4.) for x in selected):
            raise ValueError('Only the frozen stream label and bounded horizons are allowed')
        for i, case in enumerate(selected):
            if case['presence'] == 'DG':
                h = case['policy'].split('_G')[0]
                if not any(c['school_seed'] == case['school_seed'] and c['policy'] == h + '_G0'
                           and c['presence'] == 'D' for c in selected[:i]):
                    raise ValueError('The matched D-only arm must precede mixed execution')
        maximum = sum(round(x['duration_T'] / .00125) for x in selected)
    value = dict(schema=REQUEST_SCHEMA, request_kind='local_model_execution',
        explicit_local_opt_in=True, independent_review=False, historical_anchor_authorization=False,
        at=datetime.now(timezone.utc).isoformat(), stage=stage, output=str(output),
        runtime_declaration_sha256=sha(runtime / 'REGIME_RUNTIME_DECLARATION.json'),
        interface_files=interface_hashes(), request_generator='run_v6_example.py',
        request_generator_sha256=sha(__file__), cases=selected, maximum_native_steps=maximum,
        native_constructions=108 if stage == 'zero_step_initialization' else len(selected),
        durable_record=True, interpretation='Local opt-in model execution request; not researcher approval or historical study authority')
    if zero_receipt is not None:
        value['zero_step_receipt'] = dict(path=str(Path(zero_receipt).resolve()), sha256=sha(zero_receipt))
        value['zero_step_seal'] = dict(path=str(Path(zero_seal).resolve()), sha256=sha(zero_seal))
    return value


def write_request(path, payload):
    """Retain the declaration beside outputs; never use a transient request file."""
    path = Path(path)
    if path.exists():
        raise ValueError('Retain prior execution requests; choose a fresh output folder')
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, payload)
    return path


def validate_zero(runtime, receipt, seal):
    runtime, receipt, seal = Path(runtime).resolve(), Path(receipt).resolve(), Path(seal).resolve()
    declaration = verify_runtime(runtime)
    bound, zero = read(seal), read(receipt)
    if (bound.get('schema') != 'fishsim_regime_example_zero_seal_v1'
            or bound.get('status') != 'passed' or bound.get('receipt_path') != str(receipt)
            or bound.get('receipt_sha256') != sha(receipt)
            or bound.get('runtime_declaration_sha256') != sha(runtime / 'REGIME_RUNTIME_DECLARATION.json')
            or bound.get('interface_files') != interface_hashes()):
        raise RuntimeError('Saved zero-check seal does not bind this exact immutable runtime/interface')
    for filename, digest in bound['files'].items():
        if sha(filename) != digest:
            raise RuntimeError('Retained zero-check receipt/request/source review changed: ' + filename)
    if (zero.get('status') != 'passed' or zero.get('native_steps') != 0
            or zero.get('native_constructions') != 108 or len(zero.get('cases', [])) != 108
            or len({x['case']['case_name'] for x in zero['cases']}) != 108
            or zero.get('actual_native_sha256') != declaration['actual_native_sha256']
            or zero.get('runtime_declaration_sha256') != sha(runtime / 'REGIME_RUNTIME_DECLARATION.json')):
        raise RuntimeError('Saved check does not contain all108 exact actual initializations')
    request = Path(bound['request_path'])
    if zero.get('execution_request_sha256') != sha(request):
        raise RuntimeError('Zero-step receipt is not bound to its permanent local request')
    if zero.get('interface_source_review_sha256') != sha(HERE / 'INTERFACE_SOURCE_REVIEW.json'):
        raise RuntimeError('The source review changed after zero-step validation')
    return zero


def worker(runtime, request, mode, output):
    environment = os.environ.copy()
    environment.pop('PYTHONOPTIMIZE', None)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['PYTHONPATH'] = os.pathsep.join([str(HERE), str(runtime), str(runtime / 'lib')])
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[name] = '1'
    subprocess.run([sys.executable, '-B', str(HERE / 'regime_runtime_worker.py'), '--runtime', str(runtime),
                    '--request', str(request), mode, '--output', str(output)], cwd=runtime,
                   env=environment, check=True)


def ensure_zero(runtime):
    folder = runtime.parent / 'zero_check'
    receipt, seal, request = folder / 'ACTUAL_ZERO_STEP_EXAMPLE.json', folder / 'ZERO_CHECK_SEAL.json', folder / 'execution_request.json'
    if receipt.exists() or seal.exists():
        validate_zero(runtime, receipt, seal)
        return receipt, seal, True
    if folder.exists():
        raise RuntimeError('Preserve incomplete zero-check outputs; select a fresh --runtime instead of automatic retry')
    payload = request_payload(runtime, 'zero_step_initialization', receipt)
    write_request(request, payload)
    worker(runtime, request, '--check', receipt)
    zero = read(receipt)
    files = {str(p.resolve()): sha(p) for p in (receipt, request, HERE / 'INTERFACE_SOURCE_REVIEW.json')}
    write(seal, dict(schema='fishsim_regime_example_zero_seal_v1', status='passed',
        receipt_path=str(receipt.resolve()), receipt_sha256=sha(receipt), request_path=str(request.resolve()),
        runtime_declaration_sha256=sha(runtime / 'REGIME_RUNTIME_DECLARATION.json'),
        interface_files=interface_hashes(), files=files))
    validate_zero(runtime, receipt, seal)
    return receipt, seal, False


def preflight_pair_output(output, runtime, package):
    """Reject bad destinations before a first actual initialization check."""
    output, runtime = Path(output).resolve(), Path(runtime).resolve()
    safe_output(output, package)
    if output == runtime or output.is_relative_to(runtime) or output.exists():
        raise ValueError('Pair output must be fresh and outside immutable runtime inputs')
    request = output.parent / (output.name + '_execution_request.json')
    if request.exists():
        raise ValueError('Retain prior local requests; choose a fresh pair output')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=output.parent):
        pass
    return output, request


def parse(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--check', action='store_true', help='Explicitly initialize108 starts, zero steps; reuse a valid completed check')
    mode.add_argument('--quick', action='store_true', help='Explicitly run a bounded matched D/DG example after strict zero checking')
    parser.add_argument('--package-root', type=Path, default=HERE)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--output', type=Path, help='Fresh pair output directory; requests remain in its permanent parent')
    parser.add_argument('--setting', choices=('headline', 'joint'), default='headline')
    parser.add_argument('--duration', type=float, choices=(.5, 2., 4.))
    parser.add_argument('--school', type=int, choices=(39061001, 39061002, 39063501, 39063502), default=39061001)
    parser.add_argument('--candidate-native', type=Path)
    parser.add_argument('--candidate-record', type=Path)
    parser.add_argument('--native-kind', choices=('source-built', 'historical'), default='source-built')
    args = parser.parse_args(argv)
    if not args.check and not args.quick:
        args.plan = True
    if bool(args.candidate_native) != bool(args.candidate_record):
        parser.error('A separate rebuilt module needs both binary and build record')
    if args.check and args.output is not None:
        parser.error('--output selects a quick pair; zero-check receipts stay beside --runtime')
    return parser, args


def main(argv=None):
    parser, args = parse(argv)
    core = ['--plan', '--package-root', str(args.package_root), '--setting', args.setting, '--school', str(args.school)]
    if args.duration is not None:
        core += ['--duration', str(args.duration)]
    _, values = parse_core(core)
    proposed = core_plan(values)
    proposed['frontend'] = 'run_v6_example.py'
    proposed['default_native_execution'] = False
    binary, record = args.candidate_native, args.candidate_record
    if binary is None and args.native_kind == 'source-built':
        base = args.package_root.resolve() / 'runtime_validation/source_build_linux_amd64'
        binary, record = base / 'cmodel.cpython-312-x86_64-linux-gnu.so', base / 'NATIVE_BUILD.json'
        pins = read(HERE / 'REGIME_RUNTIME_INPUTS.json')['published_source_built_native']
        if sha(binary) != pins['binary_sha256'] or sha(record) != pins['record_sha256']:
            parser.error('Published separately built artifact/record changed')
    proposed['selected_native_kind'] = 'explicit_separate_source_build' if binary else 'historical_pinned_binary'
    proposed['selected_native_sha256'] = sha(binary) if binary else 'eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'
    proposed['native_compatibility'] = 'Linux x86-64 CPython3.12 artifact; new-interface execution is unvalidated; other platforms need separately verified runtime support'
    print(json.dumps(proposed, indent=2), flush=True)
    if args.plan:
        return
    if sys.flags.optimize:
        parser.error('Use ordinary Python without -O/PYTHONOPTIMIZE')
    key = hashlib.sha256(json.dumps(dict(interface=interface_hashes(), package=str(args.package_root.resolve()),
        native=sha(binary) if binary else 'historical'), sort_keys=True).encode()).hexdigest()[:16]
    runtime = (args.runtime or Path(tempfile.gettempdir()) / ('fishsim_v6_example_' + key) / 'model').resolve()
    if args.quick:
        requested_output = args.output or runtime.parent / 'runs' / datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f') / 'cases_output'
        output, request = preflight_pair_output(requested_output, runtime, args.package_root)
    if runtime.exists():
        declaration = verify_runtime(runtime)
        if declaration['package'] != str(args.package_root.resolve()):
            parser.error('Runtime belongs to a different protected package')
        expected_native = sha(binary) if binary else 'eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'
        if declaration['actual_native_sha256'] != expected_native:
            parser.error('Runtime uses another active native artifact')
    else:
        runtime = prepare_runtime(args.package_root, runtime, binary, record)
    zero, seal, reused = ensure_zero(runtime)
    print(json.dumps(dict(status='exact_zero_check_reused' if reused else 'exact_zero_check_passed',
                          receipt=str(zero), native_steps=0, additional_zero_constructions=0 if reused else 108)), flush=True)
    if args.check:
        return
    payload = request_payload(runtime, 'bounded_example_integration', output,
                              proposed['example_cases'], zero, seal)
    write_request(request, payload)
    worker(runtime, request, '--integrate', output)
    print(json.dumps(dict(status='bounded_example_complete', output=str(output), request=str(request),
                          zero_check_reused=reused, interpretation=proposed['interpretation'])), flush=True)


if __name__ == '__main__':
    main()
