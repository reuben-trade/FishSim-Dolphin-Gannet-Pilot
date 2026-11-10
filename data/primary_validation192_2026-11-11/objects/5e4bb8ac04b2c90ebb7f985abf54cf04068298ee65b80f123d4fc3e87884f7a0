"""Approved initialization checks only: native construction with step forbidden."""
from copy import deepcopy
from dataclasses import asdict
import gc
import hashlib
import json
from pathlib import Path

import numpy as np

from build import build, clean, sha
from cases import all_cases, SEEDS, CAPTURE_SEED, prior_case
from evidence import original_h2_labels
from preflight import species_projection
from run import snapshot
from research.prey_mediated.scenario import TravellingSchool
from research.prey_mediated.surface_safe_school import SurfaceSafeSchool

HERE = Path(__file__).resolve().parent


def state_digest(state):
    digest = hashlib.sha256()
    for name, value in asdict(state).items():
        a = np.asarray(value)
        digest.update(name.encode())
        digest.update(str(a.dtype).encode())
        digest.update(str(a.shape).encode())
        digest.update(a.tobytes())
    return digest.hexdigest()


def validate():
    pure = json.loads((HERE/'preflight.json').read_text())
    if pure.get('status') != 'passed' or pure.get('pure_cases') != 60 or pure.get('native_constructions') != 0:
        raise RuntimeError('All60 pure preparations must pass before approved zero-step initialization')
    # Root explicitly authorized these zero-step constructions after the pure
    # preflight. Guard the actual step method against accidental integration.
    old_step = SurfaceSafeSchool.step
    def prohibited(*args, **kwargs):
        raise RuntimeError('Native stepping is forbidden in zero-step initialization')
    SurfaceSafeSchool.step = prohibited
    receipts, states, rows = {}, {}, []
    try:
        for case in all_cases():
            engine, meta = build(case.school_seed, case.policy, capture_seed=CAPTURE_SEED, presence=case.presence)
            actual = engine.school.state()
            receipt = snapshot(engine)
            assert actual.step_index >= 0 and abs(actual.time-20.) < 1e-8
            receipts[case.name] = receipt
            states[case.name] = state_digest(actual)
            if case.anchor:
                prior = prior_case(case)
                assert original_h2_labels(receipt) == json.loads((prior/'initial_engine.json').read_text())
                with np.load(prior/'initial_school.npz') as z:
                    assert all(np.array_equal(np.asarray(v), z[k]) for k, v in asdict(actual).items())
            rows.append(dict(**case.asdict(), actual_initial_school_sha256=states[case.name]))
            del engine
            gc.collect()
        for seed in SEEDS:
            subset = [c for c in all_cases() if c.school_seed == seed]
            assert len({states[c.name] for c in subset}) == 1, 'Native fish initialization changed across the grid'
            base = next(c for c in subset if c.dolphins and c.herding_minimum == 2. and c.gannets == 0)
            for case in subset:
                r = receipts[case.name]
                assert r['ownership'] == receipts[base.name]['ownership'] and r['tie_rng'] == receipts[base.name]['tie_rng']
                if case.dolphins:
                    expected = deepcopy(species_projection(receipts[base.name], 'D'))
                    for controller in expected['controllers'].values():
                        controller['parameters']['pressure_minimum'] = case.herding_minimum
                        controller['simple']['herding_minimum'] = case.herding_minimum
                    assert species_projection(r, 'D') == expected
                if case.gannets:
                    control = next(c for c in subset if not c.dolphins and c.gannets == case.gannets)
                    assert species_projection(r, 'G') == species_projection(receipts[control.name], 'G')
        return dict(status='passed', native_constructions=60, native_steps=0,
            actual_initial_anchor_matches=8, independent_schools=4, actual_cases=60,
            step_method_guard='SurfaceSafeSchool.step replaced by exception during entire check',
            checks='Exact actual loaded fish identity across all15cells/school; eight original full initial receipts; D differs only in explicit H parameters across all levels; shared G-only/mixed starts and all private streams',
            rows=rows)
    finally:
        SurfaceSafeSchool.step = old_step


if __name__ == '__main__':
    result = validate()
    (HERE/'native_zero_step.json').write_text(json.dumps(clean(result), indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
