"""Bounded fresh-school preparation with the original sampler and screening law.

Import and --inspect are native-free. --execute is the explicit native boundary.
Two fixed candidates are retained without replacements or feeding-outcome selection.
"""
from __future__ import annotations

import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
BASELINE = ROOT / 'research/prey_mediated/BASELINE_V1.json'
HISTORICAL_SCENARIO = ROOT / 'research/prey_mediated/results/short_angular_physical_g3_v1/manifest.json'
ORIGINAL_PROTOCOL = ROOT / 'research/herding_study_2026-11-06/protocol.json'
ORIGINAL_RUNNER = ROOT / 'research/herding_study_2026-11-06/run.py'
ORIGINAL_DECLARATION = ROOT / 'research/herding_study_2026-11-07/v2_numeric_execution_v1.json'
SEEDS = (39063501, 39063502)
DT = .00125
BURN = 20.
SCREEN = 36.
SAMPLE = .5
NATIVE_SHA256 = 'eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp():
    return datetime.now(ZoneInfo('Australia/Perth')).isoformat()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def bindings():
    native = read(ORIGINAL_DECLARATION)['native']
    assert native['sha256'] == NATIVE_SHA256 and sha(native['path']) == NATIVE_SHA256
    files = [Path(__file__), BASELINE, HISTORICAL_SCENARIO, ORIGINAL_PROTOCOL, ORIGINAL_RUNNER,
             ORIGINAL_DECLARATION,
             ROOT / 'research/prey_mediated/scenario.py',
             ROOT / 'research/prey_mediated/metrics.py',
             ROOT / 'research/multispecies_feeding_study_2026-11-05/model_setup.py']
    return dict(native=native, source_sha256={str(p): sha(p) for p in files})


def declaration():
    from research.prey_mediated.scenario import ScenarioConfig
    original = read(ORIGINAL_PROTOCOL)['preparation']
    assert original['duration'] == BURN and original['stability_duration'] == SCREEN
    assert original['factory'] == 'TravellingSchool'
    assert read(BASELINE)['scenario'] == read(HISTORICAL_SCENARIO)['config']
    config = replace(ScenarioConfig(**read(BASELINE)['scenario']), dt=DT)
    inherited = read(ORIGINAL_DECLARATION)['source_sha256']
    for path in (ORIGINAL_RUNNER, ROOT / 'research/prey_mediated/scenario.py',
                 ROOT / 'research/prey_mediated/metrics.py'):
        assert sha(path) == inherited[str(path)], ('Original preparation source changed', str(path))
    assert config.n == 160 and config.native_noise == 0.
    return dict(status='planned', at=stamp(), scope='bounded_exposed_policy_replication_preparation',
        school_seeds=list(SEEDS), seeds=list(SEEDS), scenario=asdict(config), preparation_dt=DT,
        encounter_checkpoint_time=BURN, stability_screen_duration=SCREEN,
        preparation_horizon=BURN + SCREEN, expected_steps_per_school=round((BURN + SCREEN) / DT),
        sample_interval=SAMPLE, sampler='research.prey_mediated.scenario.make_initial_state',
        factory='research.prey_mediated.scenario.TravellingSchool',
        original_algorithm=str(ORIGINAL_RUNNER) + ':prepare_schools',
        original_preparation=original, workers=2, numeric_threads_per_worker=1,
        criteria=dict(finite_and_submerged=True, retained_fish=160,
            minimum_route_speed_fraction=.6, minimum_route_interval_fraction=.9,
            minimum_largest_component_fraction=.9, minimum_connected_sample_fraction=.9),
        replacement_rule='none; retain both fixed candidate dispositions',
        calibration='none', numerical_convergence='not assessed; one unchanged preparation grid',
        no_predators=True, feeding_encounters=0, **bindings())


def candidate(seed, output, frozen):
    """Execute exactly one original 20T preparation and 36T no-predator screen."""
    from research.prey_mediated.scenario import ScenarioConfig, make_initial_state, TravellingSchool
    from research.prey_mediated.metrics import snapshot_metrics
    started = time.monotonic()
    directory = Path(output) / f's{seed}'
    directory.mkdir(exist_ok=False)
    config = ScenarioConfig(**frozen['scenario'])
    initial = make_initial_state(seed, config)
    np.savez_compressed(directory / 'construction.npz', **asdict(initial))
    raw_digest = hashlib.sha256(initial.positions.tobytes() + initial.directions.tobytes()).hexdigest()
    school = TravellingSchool(config, initial)
    steps = round((BURN + SCREEN) / DT)
    samples = []
    saved = None
    write(directory / 'progress.json', dict(status='running', at=stamp(), seed=seed, elapsed=0., native_steps=0))
    for step in range(steps + 1):
        elapsed = step * DT
        if step % round(SAMPLE / DT) == 0:
            state = school.state()
            metrics = snapshot_metrics(state.positions, state.directions, state.directions * config.speed)
            samples.append(dict(time=elapsed, **{k: metrics[k] for k in
                ('rg', 'polarization', 'largest_component_fraction', 'centroid_x', 'centroid_y', 'centroid_z')}))
        if step == round(BURN / DT):
            saved = school.state()
            np.savez_compressed(directory / 'encounter.npz', **asdict(saved))
        if step % round(2. / DT) == 0 or step == steps:
            write(directory / 'progress.json', dict(status='running', at=stamp(), seed=seed,
                elapsed=elapsed, native_steps=step, wall_seconds=time.monotonic() - started))
        if step == steps:
            break
        school.step()
    final = school.state()
    np.savez_compressed(directory / 'screen_final.npz', **asdict(final))
    write(directory / 'metrics.json', samples)
    selected = [row for row in samples if row['time'] >= BURN]
    speeds = [(b['centroid_x'] - a['centroid_x']) / (b['time'] - a['time'])
              for a, b in zip(selected, selected[1:])]
    speed_fraction = float(np.mean(np.asarray(speeds) >= .6 * config.speed))
    connected_fraction = float(np.mean([row['largest_component_fraction'] >= .9 for row in selected]))
    finite_submerged = bool(np.isfinite(school.positions).all() and np.all(school.positions[:, 2] <= 0.))
    valid = bool(finite_submerged and school.n == config.n and speed_fraction >= .9 and connected_fraction >= .9)
    assert saved is not None and saved.step_index == round(BURN / DT)
    assert final.step_index == steps and abs(final.time - BURN - SCREEN) < 1e-8
    for path, digest in frozen['source_sha256'].items():
        assert sha(path) == digest, ('Preparation source changed', path)
    assert sha(frozen['native']['path']) == NATIVE_SHA256
    result = dict(status='complete', at=stamp(), school_seed=seed, accepted=valid,
        checkpoint=dict(path=str((directory / 'encounter.npz').resolve()),
                        sha256=sha(directory / 'encounter.npz'), preparation_dt=DT, time=saved.time),
        construction_sha256=sha(directory / 'construction.npz'), initial_array_sha256=raw_digest,
        screen_final_sha256=sha(directory / 'screen_final.npz'), native_steps=steps,
        checkpoint_metrics=next(row for row in samples if row['time'] == BURN),
        acceptance_checks=dict(finite_submerged=finite_submerged, retained_fish=school.n,
            route_speed_passing_fraction=speed_fraction, connectivity_passing_fraction=connected_fraction),
        stability_min_route_speed=float(min(speeds)),
        surface_reflections_at_checkpoint=saved.surface_reflections,
        surface_reflections_at_screen_end=school.surface_reflections,
        wall_seconds=time.monotonic() - started)
    write(directory / 'summary.json', result)
    write(directory / 'progress.json', dict(result, elapsed=BURN + SCREEN))
    write(directory / 'completion.json', dict(status='complete', at=stamp(),
        files={p.name: sha(p) for p in directory.iterdir() if p.is_file()}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--inspect', action='store_true')
    modes.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE / 'checkpoints')
    args = parser.parse_args()
    frozen = declaration()
    if args.inspect:
        print(json.dumps(clean(frozen), indent=2))
        return
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    write(output / 'execution.json', frozen)
    completed = []
    with (HERE / 'preparation.lock').open('a') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            with ProcessPoolExecutor(max_workers=2) as pool:
                futures = {pool.submit(candidate, seed, output, frozen): seed for seed in SEEDS}
                for future in as_completed(futures):
                    result = future.result()
                    completed.append(result)
                    write(output / 'status.json', dict(status='running', at=stamp(), complete=len(completed), planned=2))
                    try:
                        print(json.dumps(clean(result)), flush=True)
                    except BrokenPipeError:
                        pass
            completed.sort(key=lambda row: row['school_seed'])
            accepted = all(row['accepted'] for row in completed)
            report = dict(frozen, status='complete', at=stamp(), preparation_gate_passed=accepted,
                candidates=completed, checkpoints={str(row['school_seed']): dict(row['checkpoint'], accepted=row['accepted'],
                    screen_status='passed' if row['accepted'] else 'failed') for row in completed},
                total_native_steps=sum(row['native_steps'] for row in completed),
                total_model_time_T=len(completed) * (BURN + SCREEN),
                wall_seconds=time.monotonic() - started)
            write(output / 'manifest.json', report)
            write(output / 'status.json', dict(status='complete', at=stamp(), complete=2, planned=2,
                preparation_gate_passed=accepted, wall_seconds=time.monotonic() - started))
        except BaseException as error:
            write(output / 'status.json', dict(status='failed_or_partial', at=stamp(),
                complete=len(completed), planned=2, error=repr(error)))
            raise


if __name__ == '__main__':
    main()
