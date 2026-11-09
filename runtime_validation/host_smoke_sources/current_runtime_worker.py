"""Private-process checks and execution of the unchanged current model sources."""
from __future__ import annotations
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import sys
from unittest.mock import patch
import numpy as np
from current_runtime import STUDIES, read, write, sha, require_python


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def changes(a, b, path=''):
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return [] if np.array_equal(a, b) else [path]
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [path + '/<keys>']
        return [p for key in a for p in changes(a[key], b[key], path + '/' + str(key))]
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return [path + '/<length>']
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in changes(x, y, path + '/' + str(i))]
    return [] if a == b else [path]


def configure(runtime):
    require_python()
    if platform.system() != 'Linux':
        raise RuntimeError('Use the Docker backend for actual execution outside Linux.')
    sys.path[:0] = [str(runtime / 'lib'), str(runtime)]
    import fish_sim.cmodel as native
    copied = read(runtime / 'RUNTIME_COPY_RECEIPT.json')
    if sha(native.__file__) != copied['actual_native_sha256']:
        raise RuntimeError('Imported native binary differs from the explicit runtime declaration.')
    return copied


def audit(runtime):
    copied = configure(runtime)
    coarse_dir = runtime / 'research' / STUDIES['coarse']
    fine_dir = runtime / 'research' / STUDIES['fine']
    coarse_build = load('_runtime_coarse_build', coarse_dir / 'build.py')
    coarse_run = load('_runtime_coarse_run', coarse_dir / 'run.py')
    fine_build = load('_runtime_fine_build', fine_dir / 'build.py')
    fine_run = load('_runtime_fine_run', fine_dir / 'run.py')
    from research.prey_mediated.encounter import Encounter
    from research.prey_mediated.scenario import TravellingSchool
    from horizons import species_projection
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError('Current-runtime initial-state audit must not step the model.')
    cases = []
    with patch.object(Encounter, 'step', forbidden), patch.object(TravellingSchool, 'step', forbidden):
        for seed in range(39064501, 39064509):
            snapshots = {}
            fish = {}
            for presence in ('D', 'G', 'DG'):
                a, ma = coarse_build.build(seed, 'exposed', 61001, presence)
                b, mb = fine_build.build(seed, 'exposed', 61001, presence)
                assert not changes(asdict(a.school.state()), asdict(b.school.state()))
                assert not changes(coarse_run.snapshot(a), coarse_run.snapshot(b))
                assert changes(asdict(a.scenario), asdict(b.scenario)) == ['/dt']
                assert a.scenario.dt == .00125 and b.scenario.dt == .000625
                assert a.school.state().step_index == b.school.state().step_index == 16000
                assert abs(a.school.state().time - 20) < 1e-8
                assert ma['capture_probability'] == mb['capture_probability'] == .7
                assert ma['checkpoint_sha256'] == mb['checkpoint_sha256']
                snapshots[presence] = coarse_run.snapshot(a)
                fish[presence] = asdict(a.school.state())
                cases.append(dict(school_seed=seed, presence=presence,
                                  checkpoint_sha256=ma['checkpoint_sha256'], native_steps=0))
            for species in ('D', 'G'):
                assert not changes(species_projection(snapshots[species], species),
                                   species_projection(snapshots['DG'], species))
            assert not changes(fish['D'], fish['G']) and not changes(fish['D'], fish['DG'])
    assert not calls
    cadence = load('_runtime_fine_cadence', fine_dir / 'cadence.py')
    for duration in (4., 36.):
        fine_steps, coarse_steps = round(duration / .000625), round(duration / .00125)
        assert [n * .000625 for n in range(fine_steps + 1) if cadence.sample_due(n, fine_steps)] == \
               [n * .00125 for n in range(coarse_steps + 1) if n % 80 == 0 or n == coarse_steps]
        assert [n * .000625 for n in range(fine_steps + 1) if cadence.progress_due(n, fine_steps)] == \
               [n * .00125 for n in range(coarse_steps + 1) if n % 800 == 0 or n == coarse_steps]
    zero = dict(status='passed', total_cases=24, native_steps=0, cases=cases,
                validator='current_runtime_worker.audit; derived runtime, not a historical receipt',
                scope='Cross-grid and D/G/DG fish, predator, controller and private-RNG initial matching')
    write(coarse_dir / 'preflight.json', zero)
    write(fine_dir / 'preflight.json', zero)
    write(fine_dir / 'cadence_validation.json', dict(status='passed', native_steps=0,
        validator='current_runtime_worker.audit', sample_interval_T=.1, progress_interval_T=1.,
        fine_sample_steps=160, fine_progress_steps=1600, checked_horizons_T=[4., 36.]))
    # The new declarations deliberately replace path/native bindings, not code.
    write(coarse_dir / 'frozen_sources.json', dict(
        derived_runtime=True, source_sha256=coarse_run.source_manifest(),
        preflight_sha256=sha(coarse_dir / 'preflight.json'),
        protocol_sha256=sha(coarse_dir / 'protocol.json')))
    write(fine_dir / 'frozen_sources.json', dict(
        derived_runtime=True, source_sha256=fine_run.source_manifest(),
        preflight_sha256=sha(fine_dir / 'preflight.json'),
        cadence_validation_sha256=sha(fine_dir / 'cadence_validation.json'),
        protocol_sha256=sha(fine_dir / 'protocol.json')))
    coarse_run.verify_source_freeze()
    fine_run.verify_source_freeze()
    files = {str(p.relative_to(runtime)): sha(p) for p in sorted(runtime.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
             and p.name != 'CURRENT_MODEL_DECLARATION.json'}
    report = dict(status='passed', at=datetime.now(timezone.utc).isoformat(),
        signature=copied['signature'], native_kind=copied['native_kind'],
        actual_native_sha256=copied['actual_native_sha256'], native_steps=0,
        zero_step_cases=24, paired_grids=2, current_source_and_checkpoint_code_unchanged=True,
        source_freezes='Derived, explicitly relocated current-run declarations; historical originals preserved',
        runtime_files=files, python=sys.version, platform=platform.platform(),
        packages={name: importlib.metadata.version(name) for name in
                  ('numpy', 'scipy', 'matplotlib', 'networkx', 'numba')},
        adapter_sha256=sha(__file__), integration_execution='not asserted by this zero-step check')
    write(runtime / 'CURRENT_MODEL_DECLARATION.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'runtime_files'}), flush=True)


def execute_case(runtime, grid, seed, presence, duration, output):
    configure(runtime)
    declaration = read(runtime / 'CURRENT_MODEL_DECLARATION.json')
    assert declaration['status'] == 'passed'
    for relative, digest in declaration['runtime_files'].items():
        assert sha(runtime / relative) == digest, relative
    study = runtime / 'research' / STUDIES[grid]
    sys.path.insert(0, str(study))
    load('build', study / 'build.py')
    runner = load('_current_execution_runner', study / 'run.py')
    result = runner.run_case(seed, 'exposed', output, duration, 61001, True, presence)
    print(json.dumps(dict(status='passed', result=result, native_steps=round(duration / runner.DT),
                          grid=grid, school_seed=seed, presence=presence,
                          native_kind=declaration['native_kind'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--audit', action='store_true')
    parser.add_argument('--grid', choices=STUDIES)
    parser.add_argument('--school', type=int)
    parser.add_argument('--presence', choices=('D', 'G', 'DG'))
    parser.add_argument('--duration', type=float)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    if args.audit:
        audit(runtime)
    else:
        execute_case(runtime, args.grid, args.school, args.presence, args.duration, args.output.resolve())


if __name__ == '__main__':
    main()
