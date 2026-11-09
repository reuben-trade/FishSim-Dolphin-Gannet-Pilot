"""Explicit current eight-school model execution; analysis stays simulation-free.

Run --plan first. New simulations use private copied inputs and fresh outputs.
The Docker backend executes the same scientific sources with a separately
declared source-built native module; it does not replace historical evidence.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import time
from current_runtime import (prepare_runtime, read, write, sha, verify_inputs,
                             require_python, reject_source_destination)

HERE = Path(__file__).resolve().parent


def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan', action='store_true', help='Verify source inputs and print budget; zero native imports/steps')
    mode.add_argument('--check', action='store_true', help='Import native module and construct all matching starts; zero steps')
    mode.add_argument('--quick', action='store_true', help='0.5T D/DG integration pair; too short for feeding')
    mode.add_argument('--run', action='store_true', help='Explicit current-model encounters')
    parser.add_argument('--backend', choices=('native', 'docker'), default='native')
    parser.add_argument('--package-root', type=Path, default=HERE)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--grid', choices=('coarse', 'fine'), default='fine')
    parser.add_argument('--school', type=int, choices=tuple(range(39064501, 39064509)), default=39064501)
    parser.add_argument('--all-schools', action='store_true')
    parser.add_argument('--presences', nargs='+', choices=('D', 'G', 'DG'), default=['D', 'DG'])
    parser.add_argument('--duration', type=float, choices=(4., 36., 72.), default=36.)
    parser.add_argument('--workers', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--candidate-native', type=Path)
    parser.add_argument('--candidate-record', type=Path)
    parser.add_argument('--image', default='fishsim-pilot-runtime:py312')
    args = parser.parse_args()
    if args.all_schools and not (args.run or args.plan):
        parser.error('--all-schools requires --run or --plan')
    if args.grid == 'fine' and args.duration == 72.:
        parser.error('The current fine-grid experiment covers 36T; use coarse for 72T.')
    if len(set(args.presences)) != len(args.presences):
        parser.error('Do not repeat presence conditions.')
    if args.quick and (args.all_schools or args.presences != ['D', 'DG']):
        parser.error('--quick is exactly one 0.5T D/DG pair.')
    return parser, args


def inside_package(path, package):
    path = path.resolve()
    try:
        return PurePosixPath('/workspace').joinpath(*path.relative_to(package).parts)
    except ValueError:
        raise ValueError('Docker work/output folders must be inside the notebook package.')


def docker_command(args, package, output, image_id):
    if ',' in str(package) or ',' in str(HERE):
        raise ValueError('Docker bind-mount paths must not contain commas.')
    command = ['docker', 'run', '--rm', '--network', 'none', '--platform', 'linux/amd64']
    if hasattr(os, 'getuid'):
        command += ['--user', str(os.getuid()) + ':' + str(os.getgid())]
    command += ['--mount', 'type=bind,source=' + str(package) + ',target=/workspace',
                '--mount', 'type=bind,source=' + str(HERE) + ',target=/runner,readonly',
                '-e', 'MPLCONFIGDIR=/tmp/fishsim-matplotlib',
                '-e', 'PYTHONUNBUFFERED=1',
                '-e', 'FISHSIM_RUNTIME_IMAGE_ID=' + image_id,
                '-w', '/workspace', image_id,
                'python', '/runner/run_current_model.py', '--backend', 'native',
                '--package-root', '/workspace', '--grid', args.grid,
                '--school', str(args.school), '--workers', str(args.workers),
                '--presences', *args.presences,
                '--candidate-native', '/opt/fishsim-native/cmodel.cpython-312-x86_64-linux-gnu.so',
                '--candidate-record', '/opt/fishsim-native/NATIVE_BUILD.json']
    if args.work:
        command += ['--work', str(inside_package(args.work, package))]
    if args.check:
        command += ['--check']
    elif args.quick:
        command += ['--quick']
    else:
        command += ['--run', '--duration', str(args.duration)]
    if args.all_schools:
        command += ['--all-schools']
    if output is not None:
        command += ['--output', str(inside_package(output, package))]
    return command


def main():
    parser, args = parse()
    if not args.plan and sys.flags.optimize:
        parser.error('Model validation/execution must run without Python -O or PYTHONOPTIMIZE.')
    package = args.package_root.resolve()
    verify_inputs(package)
    schools = list(range(39064501, 39064509)) if args.all_schools else [args.school]
    duration = .5 if args.quick else args.duration
    dt = .00125 if args.grid == 'coarse' else .000625
    cases = [(seed, presence) for seed in schools for presence in args.presences]
    planned = dict(status='plan_only' if args.plan else 'requested', backend=args.backend,
        grid=args.grid, schools=schools, presences=args.presences, capture_seed=61001,
        duration_per_case_T=duration, dt=dt, cases=len(cases), workers=args.workers,
        maximum_native_steps=0 if args.check else round(duration / dt) * len(cases),
        native_steps=0, scientific_code='unchanged current published sources',
        interpretation='0.5T is integration only; full runs are new outputs, separate from saved evidence.')
    print(json.dumps(planned, indent=2), flush=True)
    if args.plan:
        return
    output = args.output or package / 'outputs/current_model_runs' / datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output = output.resolve()
    reject_source_destination(output, [package / 'frozen_model', package / 'data',
        package / 'study_sources', HERE / 'current_model_inputs'])
    if not args.check and output.exists():
        parser.error('Output must be a new folder; saved runs are preserved.')
    if args.backend == 'docker':
        image_id = subprocess.check_output(['docker', 'image', 'inspect', args.image,
            '--format', '{{.Id}}'], text=True).strip()
        subprocess.run(docker_command(args, package, None if args.check else output, image_id), check=True)
        return
    require_python()
    if platform.system() != 'Linux':
        parser.error('Actual native execution is Linux-only; use --backend docker on other systems.')
    runtime = prepare_runtime(package, args.work or package / 'work',
                              args.candidate_native, args.candidate_record)
    if not args.check and output.is_relative_to(runtime):
        parser.error('Simulation outputs must be outside the private runtime input tree.')
    environment = os.environ.copy()
    environment.pop('PYTHONOPTIMIZE', None)
    environment['PYTHONPATH'] = os.pathsep.join([str(HERE), str(runtime / 'lib'), str(runtime)])
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[key] = '1'
    worker = HERE / 'current_runtime_worker.py'
    if not (runtime / 'CURRENT_MODEL_DECLARATION.json').exists():
        subprocess.run([sys.executable, str(worker), '--runtime', str(runtime), '--audit'],
                       cwd=runtime, env=environment, check=True)
    declaration = read(runtime / 'CURRENT_MODEL_DECLARATION.json')
    assert declaration['status'] == 'passed' and declaration['native_steps'] == 0
    if args.check:
        print(json.dumps(dict(status='current_runtime_check_passed', native_steps=0,
                              declaration=str(runtime / 'CURRENT_MODEL_DECLARATION.json'))), flush=True)
        return
    output.mkdir(parents=True)
    started = time.monotonic()
    def one(case):
        seed, presence = case
        command = [sys.executable, str(worker), '--runtime', str(runtime), '--grid', args.grid,
                   '--school', str(seed), '--presence', presence, '--duration', str(duration),
                   '--output', str(output)]
        log = output / f's{seed}_{presence}.log'
        with log.open('w') as handle:
            subprocess.run(command, cwd=runtime, env=environment, stdout=handle,
                           stderr=subprocess.STDOUT, check=True)
        folder = output / 'cases' / f's{seed}_exposed_{presence}_c61001'
        audit, seal = read(folder / 'audit.json'), read(folder / 'completion.json')
        assert audit['status'] == 'passed' and seal['status'] == 'complete'
        for name, digest in seal['files'].items():
            assert sha(folder / name) == digest, str(folder / name)
        return dict(school_seed=seed, presence=presence, status='passed',
                    actual_native_steps=read(folder / 'summary.json')['native_steps'],
                    completion_sha256=sha(folder / 'completion.json'))
    completed = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, case) for case in cases]
        for future in as_completed(futures):
            completed.append(future.result())
            print('Completed current-model cases: ' + str(len(completed)) + '/' + str(len(cases)), flush=True)
    receipt = dict(status='passed', current_model=True, mode='quick_integration' if args.quick else 'current_encounters',
        grid=args.grid, dt=dt, duration_per_case_T=duration, cases=completed,
        native_steps=sum(row['actual_native_steps'] for row in completed),
        native_kind=declaration['native_kind'], actual_native_sha256=declaration['actual_native_sha256'],
        historical_actor_reference_native=declaration.get('historical_actor_reference_native'),
        native_field_roles=declaration['native_field_roles'],
        container_image_id=os.environ.get('FISHSIM_RUNTIME_IMAGE_ID'),
        execution_wrapper_sha256=sha(__file__), worker_sha256=sha(worker),
        behavioral_code_modified=False, prepared_checkpoint_arrays_modified=False,
        derived_runtime_declaration=str(runtime / 'CURRENT_MODEL_DECLARATION.json'),
        wall_seconds=time.monotonic() - started, interpretation=planned['interpretation'])
    write(output / 'current_model_execution.json', receipt)
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    main()
