"""Plan/check a small example of the archived H×G model, using new output files.

Preparation is native-free. Actual zero-step/integration commands remain gated
until an independent reviewer records an exact new runtime execution scope.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from regime_runtime import HERE, prepare_runtime, read, safe_output, sha, verify_package, verify_runtime

SEEDS = (39061001, 39061002, 39063501, 39063502)
SETTINGS = {'headline': dict(H=1, G=9, duration_T=4.),
            'joint': dict(H=2, G=12, duration_T=2.)}


def parse(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan', action='store_true', help='Verify packaged inputs and print a Native-free plan')
    mode.add_argument('--prepare', action='store_true', help='Copy new runtime and prove108 pure Python preparations; no extension import')
    mode.add_argument('--check', action='store_true', help='Future reviewed actual108-start zero-step initialization check')
    mode.add_argument('--quick', action='store_true', help='Future reviewed2T/4T example, not a feeding-effect estimate')
    mode.add_argument('--integration', action='store_true', help='Future reviewed0.5T integration check only')
    parser.add_argument('--package-root', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, help='A new/existing derived runtime outside protected inputs')
    parser.add_argument('--output', type=Path, help='Fresh output directory, or receipt file for --check')
    parser.add_argument('--request', type=Path, help='Developer harness only: explicit local request from run_v6_example.py')
    parser.add_argument('--school', type=int, choices=SEEDS, default=SEEDS[0])
    parser.add_argument('--setting', choices=SETTINGS, default='headline', help='headline=H1/G9/4T; joint=H2/G12/2T')
    parser.add_argument('--duration', type=float, choices=(.5, 2., 4.), help='Bounded engineering horizon only; defaults follow setting')
    parser.add_argument('--presences', nargs='+', choices=('D', 'G', 'DG'), default=['D', 'DG'])
    parser.add_argument('--candidate-native', type=Path)
    parser.add_argument('--candidate-record', type=Path)
    args = parser.parse_args(argv)
    if len(set(args.presences)) != len(args.presences):
        parser.error('Presence arms must be unique')
    if bool(args.candidate_native) != bool(args.candidate_record):
        parser.error('A separate native build needs both --candidate-native and --candidate-record')
    if args.integration and args.duration not in (None, .5):
        parser.error('--integration is exactly0.5T; use --quick for2T/4T')
    if (args.quick or args.integration) and {'D', 'DG'}.issubset(args.presences):
        if args.presences.index('D') > args.presences.index('DG'):
            parser.error('The D-only arm must precede its mixed comparison')
    return parser, args


def plan(args):
    verify_package(args.package_root)
    setting = SETTINGS[args.setting]
    duration = .5 if args.integration else (args.duration if args.duration is not None else setting['duration_T'])
    selected = []
    for presence in args.presences:
        policy = 'Gonly' + str(setting['G']) if presence == 'G' else f'H{setting["H"]}_G{0 if presence == "D" else setting["G"]}'
        selected.append(dict(school_seed=args.school, policy=policy, presence=presence,
                             capture_seed=61001, duration_T=duration))
    return dict(schema='fishsim_regime_example_plan_v3', status='plan_only',
                scientific_scope='V6 frozen 108-start model on four schools, coarse dt=.00125; bounded examples H1/G9 and H2/G12',
                example_setting=args.setting, example_cases=selected, actual_zero_step_check_cases=108,
                planned_integration_native_steps=sum(round(x['duration_T'] / .00125) for x in selected),
                native_imports=0, native_constructions=0, native_steps=0,
                unchanged_model='Exact archived scientific Python/checkpoints/native C++ sources; derived builder/execution AST replaces historical operational gates only',
                execution_status='Not yet initialization/integration validated for this new regime harness',
                interpretation='Bounded 0.5T/2T/4T illustrates model execution only and cannot estimate partner benefit. The saved 36T ensemble remains the analysis evidence.',
                backend='Linux CPython3.12; explicit separately rebuilt native artifact may be selected. Docker/other platform invocation not verified for this interface.')


def main(argv=None):
    parser, args = parse(argv)
    proposed = plan(args)
    print(json.dumps(proposed, indent=2), flush=True)
    if args.plan:
        return
    if sys.flags.optimize:
        parser.error('Use ordinary Python without -O/PYTHONOPTIMIZE for model validation')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    runtime = args.runtime or Path(tempfile.gettempdir()) / ('fishsim_regime_example_' + stamp) / 'model'
    runtime = runtime.resolve()
    if runtime.exists():
        declaration = verify_runtime(runtime)
        if declaration['package'] != str(args.package_root.resolve()):
            parser.error('Existing runtime belongs to another package')
        if args.candidate_native and declaration['actual_native_sha256'] != sha(args.candidate_native):
            parser.error('Existing runtime uses another native artifact')
    else:
        runtime = prepare_runtime(args.package_root, runtime, args.candidate_native, args.candidate_record)
    environment = os.environ.copy()
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment.pop('PYTHONOPTIMIZE', None)
    environment['PYTHONPATH'] = os.pathsep.join([str(HERE), str(runtime), str(runtime / 'lib')])
    worker = HERE / 'regime_runtime_worker.py'
    if args.prepare:
        output = args.output or runtime.parent / 'PURE_PREPARATION.json'
        safe_output(output, args.package_root)
        if output.exists():
            parser.error('Pure receipt output must be new')
        subprocess.run([sys.executable, '-B', str(worker), '--runtime', str(runtime), '--pure', '--output', str(output)],
                       cwd=runtime, env=environment, check=True)
        print(json.dumps(dict(status='pure_preparation_passed', runtime=str(runtime), receipt=str(output), native_steps=0)), flush=True)
        return
    if args.request is None:
        parser.error('Native initialization/integration has not been authorized: use run_v6_example.py or provide its explicit --request')
    approved = read(args.request)
    if args.check:
        output = args.output or runtime.parent / 'ACTUAL_ZERO_STEP_EXAMPLE.json'
        if output.exists():
            parser.error('Actual initialization receipt must be new')
        worker_mode = '--check'
    else:
        if approved.get('cases') != proposed['example_cases']:
            parser.error('Exact requested example cases/horizons differ from independently reviewed scope')
        horizon = proposed['example_cases'][0]['duration_T']
        output = args.output or runtime.parent / (f'{args.setting}_example_{horizon:g}T' if args.quick else 'integration_0p5T')
        worker_mode = '--integrate'
    output = safe_output(output, args.package_root)
    if output == runtime or output.is_relative_to(runtime):
        parser.error('Outputs must be outside derived runtime input files')
    subprocess.run([sys.executable, '-B', str(worker), '--runtime', str(runtime), '--request', str(args.request.resolve()),
                    worker_mode, '--output', str(output)], cwd=runtime, env=environment, check=True)


if __name__ == '__main__':
    main()
