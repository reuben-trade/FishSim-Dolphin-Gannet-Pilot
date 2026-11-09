"""Pure initialization and source checks; native construction is prohibited."""
import ast
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from cases import HERE, ROOT, SEEDS, FIXTURES, Case, cases_for, DT
from build import prepare_case, clean
from horizons import species_projection

ORIGINAL = ROOT/'research/high_count_regime_extension_2026-11-09'
PUBLISHED = Path('/home/venture/FishSim-Dolphin-Gannet-Pilot/data/research/high_count_regime_extension_2026-11-09')
DISCOVERY = ROOT/'research/pilot_regime_sweep_2026-11-09_v2'
HIGH_CASES = Path('/tmp/FishSim_High_Count_Extension_2026-11-09/full_36T_v1/cases')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restrict(receipt, species, identities=None):
    value = deepcopy(species_projection(receipt, species))
    if identities is not None:
        value['actors'] = [a for a in value['actors'] if a['actor_id'] in identities]
        for name in ('actor_policy', 'capture_rng', 'controllers'):
            value[name] = {k:v for k,v in value[name].items() if k in identities}
    return value


def fixture_archive(case):
    from reference import reference_path
    return reference_path(case.school_seed, case.herding_minimum, case.gannets, 12)


def state_digest(state):
    digest = hashlib.sha256()
    for name, value in asdict(state).items():
        array = np.asarray(value)
        digest.update(name.encode()); digest.update(str(array.dtype).encode())
        digest.update(str(array.shape).encode()); digest.update(array.tobytes())
    return digest.hexdigest()


def assert_physical_source():
    if (ORIGINAL/'run.py').read_bytes() != (PUBLISHED/'run.py').read_bytes():
        raise AssertionError('Original runner differs from published frozen runner')
    source = ast.parse((ORIGINAL/'run.py').read_text())
    candidate = ast.parse((HERE/'physical_run.py').read_text())
    funcs = {n.name:n for n in source.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    actual = {n.name:n for n in candidate.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    names = tuple(funcs)[:tuple(funcs).index('_execute_wave')]
    for name in names:
        if name == 'run_case':
            def tail(node):
                for i, statement in enumerate(node.body):
                    if (isinstance(statement, ast.Assign) and isinstance(statement.targets[0], ast.Tuple)
                            and [getattr(n, 'id', None) for n in statement.targets[0].elts] == ['engine', 'metadata']):
                        return ast.dump(ast.Module(body=node.body[i+1:], type_ignores=[]))
                raise AssertionError('Missing explicit native construction boundary')
            if tail(funcs[name]) != tail(actual[name]):
                raise AssertionError('Physical runner tail after native construction changed')
        elif ast.dump(funcs[name]) != ast.dump(actual[name]):
            raise AssertionError('Preserved resolved motion/accounting function changed: '+name)
    for name in ('regime_controller.py', 'gannet.py', 'horizons.py', 'cadence.py', 'review_actual.py'):
        if ((HERE/name).read_bytes() != (ORIGINAL/name).read_bytes()
                or (HERE/name).read_bytes() != (PUBLISHED/name).read_bytes()):
            raise AssertionError('Preserved scientific module changed: '+name)
    return names


def identity_independent_role_probe(prepared):
    """One pure feasible-attack proposal per identity with equal physical input.

    No fish factory, encounter, native step or food/contact resolution is used.
    This supplements the source check for absent actor-ID role lookup.
    """
    from regime_controller import SimpleHerdStrikePlanner
    from research.prey_mediated.predators import observe
    base = next(a for a in prepared.actors if a.state.actor_id == 'D00')
    x = np.asarray(base.state.position) + np.array([[2.,0.,0.], [2.,.2,0.], [2.,-.2,0.], [2.,0.,.2], [3.,0.,0.]])
    v = np.zeros_like(x)
    expected = None
    for i in range(24):
        identity = f'D{i:02d}'
        state = replace(base.state, actor_id=identity, mode='search', ready_at=base.state.time,
            mode_since=base.state.time)
        planner = SimpleHerdStrikePlanner(policy='exposed', parameters=prepared.planners['D00'].parameters)
        planner._memory = replace(planner._memory, phase='maintain',
            phase_started=state.time-4., maintenance_started=state.time-4.)
        obs = observe(state, x, v, np.arange(5), base.config)
        proposal = planner(state, obs, DT, base.config)
        def normalize(value):
            if isinstance(value, dict):
                return {k:normalize(v) for k,v in value.items()}
            if isinstance(value, list):
                return [normalize(v) for v in value]
            return '<identity>' if value == identity else value
        result = normalize(clean(dict(proposal=asdict(proposal), diagnostics=planner.last_diagnostics)))
        if expected is None:
            expected = result
        elif result != expected:
            raise AssertionError('Actor identity changes an otherwise identical pure proposal')
    if not expected['diagnostics']['launch_allowed']:
        raise AssertionError('Identity probe must cover a feasible launched attack')
    return 24


def validate(regimes=FIXTURES, selected=False):
    if not __debug__:
        raise RuntimeError('Unoptimized Python required for audit assertions')
    from research.prey_mediated.scenario import TravellingSchool
    original_constructor = TravellingSchool.__init__
    constructor_attempts = []
    def forbidden(*args, **kwargs):
        constructor_attempts.append(True)
        raise AssertionError('Native construction forbidden in D24 pure preflight')
    TravellingSchool.__init__ = forbidden
    try:
        functions = assert_physical_source()
        rows, bindings = [], {}
        originals = {f'D{i:02d}' for i in range(12)}
        role_checks = 0
        for case in cases_for(regimes):
            reference_case = replace(case, dolphin_count=12)
            prepared12 = prepare_case(reference_case)
            path = fixture_archive(reference_case)
            archived = json.loads((path/'initial_engine.json').read_text())
            if prepared12.receipt() != archived:
                raise AssertionError('Original D12 fixture receipt differs from completed archive')
            bindings[str(path/'initial_engine.json')] = sha(path/'initial_engine.json')
            prepared = prepare_case(case)
            receipt = prepared.receipt()
            if restrict(receipt, 'D', originals) != restrict(archived, 'D'):
                raise AssertionError('Original D00–D11 state/config/controller/private stream changed')
            if restrict(receipt, 'G') != restrict(archived, 'G'):
                raise AssertionError('Count-matched gannet states/config/controllers/private streams changed')
            if state_digest(prepared.initial) != state_digest(prepared12.initial):
                raise AssertionError('Dolphin count changes saved fish initialization')
            actors = {a.state.actor_id:a for a in prepared.actors}
            for i in range(12, 24):
                added, base = actors[f'D{i:02d}'], actors[f'D{i % 12:02d}']
                expected = replace(base.state, actor_id=added.state.actor_id, ready_at=added.state.ready_at)
                if (added.state != expected or added.config != base.config or added.mouth != base.mouth
                        or added.capture_probability != base.capture_probability
                        or receipt['controllers'][added.state.actor_id] != receipt['controllers'][base.state.actor_id]):
                    raise AssertionError('Added dolphin differs beyond stable identity/private readiness')
                if receipt['capture_rng'][added.state.actor_id] == receipt['capture_rng'][base.state.actor_id]:
                    raise AssertionError('New identities must have their own stable private capture stream')
            if prepared.metadata['counts'] != dict(fish=160, D=24, G=case.gannets):
                raise AssertionError('Population metadata is not count-aware')
            if case.school_seed == SEEDS[0] and case.gannets:
                role_checks += identity_independent_role_probe(prepared)
            rows.append(dict(**case.asdict(), school_state_sha256=state_digest(prepared.initial),
                exact_D12_reference_receipt_sha256=sha(path/'initial_engine.json')))
        if constructor_attempts:
            raise AssertionError('A prohibited constructor was attempted')
        return dict(status='passed', native_constructions=0, native_constructor_attempts=0, native_steps=0,
            fixture_only=not selected, actual_regimes_selected=selected, exact_archived_D12_receipts=len(rows),
            pure_D24_fixture_states=len(rows), same_physical_input_identity_attack_probes=role_checks,
            unchanged_runner_functions=[n for n in functions if n != 'run_case'],
            physical_runner_tail_exact_after_constructor=True, independent_schools=4,
            bindings=bindings, source_sha256={p.name:sha(p) for p in sorted(HERE.glob('*.py'))}, rows=rows)
    finally:
        TravellingSchool.__init__ = original_constructor


if __name__ == '__main__':
    if '--selected' in sys.argv:
        from evidence import validate_selection
        from cases import selected_regimes
        validate_selection(); result = validate(selected_regimes(), selected=True)
        path = HERE/'PURE_PREFLIGHT.json'
    else:
        result = validate()
        path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/FishSim_D24_Pure_Preflight_2026-11-09.json')
    with path.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows', 'bindings', 'source_sha256')}))
