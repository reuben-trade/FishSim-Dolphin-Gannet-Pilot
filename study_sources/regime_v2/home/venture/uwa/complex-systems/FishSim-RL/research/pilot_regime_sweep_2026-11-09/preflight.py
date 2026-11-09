"""All60 pure preparations; never construct, import or step native fish bindings."""
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from build import prepare_case, sha, clean, validate_sealed_case
from cases import all_cases, prior_case, SEEDS
from evidence import original_h2_labels

HERE = Path(__file__).resolve().parent


def species_projection(receipt, species):
    return dict(actors=[a for a in receipt['actors'] if a['species'] == species],
        actor_policy={k: v for k, v in receipt['actor_policy'].items() if k.startswith(species)},
        capture_rng={k: v for k, v in receipt['capture_rng'].items() if k.startswith(species)},
        controllers={k: v for k, v in receipt['controllers'].items() if k.startswith(species)})


def validate():
    prepared = {case.name: prepare_case(case) for case in all_cases()}
    rows = []
    for case in all_cases():
        p = prepared[case.name]
        receipt = p.receipt()
        with np.load(p.metadata['checkpoint_path']) as z:
            assert all(np.array_equal(np.asarray(v), z[k]) for k, v in asdict(p.initial).items()), 'Checkpoint changed'
        if case.anchor:
            prior = prior_case(case)
            validate_sealed_case(prior)
            old = json.loads((prior/'initial_engine.json').read_text())
            assert original_h2_labels(receipt) == old, 'Pure initial engine/streams differ from sealed anchor'
            # Native construction re-normalizes the saved unit headings. We
            # compare untouched checkpoint provenance here; exact loaded fish
            # arrays and full trajectories are required by later replay gates.
            with np.load(prior/'initial_school.npz') as z:
                for k, v in asdict(p.initial).items():
                    if k == 'directions':
                        assert np.max(abs(np.asarray(v)-z[k])) < 1e-10
                    else:
                        assert np.array_equal(np.asarray(v), z[k]), k
        if case.dolphins:
            control = next(q for q in prepared.values() if q.case.school_seed == case.school_seed
                and q.case.dolphins and q.case.herding_minimum == case.herding_minimum and q.case.gannets == 0)
            assert species_projection(receipt, 'D') == species_projection(control.receipt(), 'D')
            assert receipt['tie_rng'] == control.receipt()['tie_rng']
        if case.gannets:
            control = next(q for q in prepared.values() if q.case.school_seed == case.school_seed
                and not q.case.dolphins and q.case.gannets == case.gannets)
            assert species_projection(receipt, 'G') == species_projection(control.receipt(), 'G')
            assert receipt['tie_rng'] == control.receipt()['tie_rng']
            assert asdict(p.scenario) == asdict(control.scenario)
        for species in ('D', 'G'):
            assert sum(a.state.species == species for a in p.actors) == p.metadata['counts'][species]
        if case.gannets == 6:
            actors = {a.state.actor_id: a for a in p.actors}
            for i in range(3):
                a, b = actors[f'G{i}'], actors[f'G{i+3}']
                assert a.state.position == b.state.position and a.config == b.config and a.mouth == b.mouth
                assert receipt['capture_rng'][f'G{i}'] != receipt['capture_rng'][f'G{i+3}']
        rows.append(dict(**case.asdict(), checkpoint_sha256=p.metadata['checkpoint_sha256'],
                         prior_anchor_match=bool(case.anchor)))
    return dict(status='passed', native_constructions=0, native_steps=0, pure_cases=60,
        anchor_initial_receipts=8, independent_schools=4, rows=rows,
        native_fish_identity='Pending approved construction/full eight-anchor replay; pure input checkpoints unchanged',
        checks='Original anchor actors/configs/readiness/private streams; exact fixed-H D controls and count-matched G controls; nested bird locations')


if __name__ == '__main__':
    result = validate()
    (HERE/'preflight.json').write_text(json.dumps(clean(result), indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
