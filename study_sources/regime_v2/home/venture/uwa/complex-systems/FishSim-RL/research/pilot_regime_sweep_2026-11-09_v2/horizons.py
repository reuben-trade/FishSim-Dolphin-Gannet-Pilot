"""Native-free fixed-horizon accounting, including explicit complete depletion."""
from __future__ import annotations
from copy import deepcopy
import math


def horizon_record(*, nominal_T, observed_T, initial_count, final_count,
                   per_actor, native_steps, structure, terminal=False):
    if not all(math.isfinite(v) and v >= 0 for v in (nominal_T, observed_T)):
        raise ValueError('Finite nonnegative clocks required')
    if observed_T > nominal_T+1e-7:
        raise ValueError('A horizon record cannot use later observations')
    if terminal and final_count != 0:
        raise ValueError('Only complete prey depletion is an absorbing feeding outcome')
    if not terminal and abs(observed_T-nominal_T)>1e-7:
        raise ValueError('Incomplete nondepleted observations cannot fill a later horizon')
    if sum(v['captures'] for v in per_actor.values()) != initial_count-final_count:
        raise ValueError('Horizon capture/removal conservation failed')
    species={}
    for name in ('D','G'):
        rows=[v for who,v in per_actor.items() if who.startswith(name)]
        captures=sum(v['captures'] for v in rows)
        species[name]=dict(count=len(rows),captures=captures,
            launches=sum(v['launches'] for v in rows),contacts=sum(v['contacts'] for v in rows),
            captures_per_actor_per_nominal_T=captures/(len(rows)*nominal_T) if rows and nominal_T else None,
            observed_effort_T=observed_T*len(rows),
            observed_distance=sum(sum(v.get('distance',{}).values()) for v in rows))
    return dict(status='complete',nominal_horizon_T=nominal_T,
        observed_native_duration_T=observed_T,native_steps=native_steps,
        absorbing_no_food_continuation=bool(terminal and observed_T<nominal_T-1e-7),
        termination='complete_prey_depletion' if terminal else 'observed_horizon',
        initial_count=initial_count,final_count=final_count,species=species,
        per_actor=deepcopy(per_actor),school_structure=deepcopy(structure),
        effort_interpretation='observed physical effort only; no post-depletion extrapolation',
        food_interpretation='actual unique captures; all later counts fixed after complete prey depletion')


def species_projection(receipt, species):
    return dict(actors=[a for a in receipt['actors'] if a['species']==species],
        actor_policy={k:v for k,v in receipt['actor_policy'].items() if k.startswith(species)},
        ownership=receipt['ownership'],capture_rng={k:v for k,v in receipt['capture_rng'].items() if k.startswith(species)},
        tie_rng=receipt['tie_rng'],controllers={k:v for k,v in receipt['controllers'].items() if k.startswith(species)})
