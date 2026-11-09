"""Pure exact-state/roster checks; no native model is constructed."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import numpy as np
from common import HERE,read,sha,write,require_unoptimized
from cases import SEEDS,all_cases,retained_cases,prior_case,smoke_cases,execution_stages,phase_cases,DT
from build import prepare_case
from horizons import species_projection
from evidence import verify_discovery

def restrict(receipt,species,identities=None):
    result=deepcopy(species_projection(receipt,species))
    if identities is None:return result
    result['actors']=[a for a in result['actors'] if a['actor_id'] in identities]
    for name in ('actor_policy','capture_rng','controllers'):
        result[name]={k:v for k,v in result[name].items() if k in identities}
    return result

def state_digest(state):
    result=hashlib.sha256()
    for name,value in asdict(state).items():
        a=np.asarray(value);result.update(name.encode());result.update(str(a.dtype).encode())
        result.update(str(a.shape).encode());result.update(a.tobytes())
    return result.hexdigest()

def validate():
    require_unoptimized();verify_discovery()
    old={};states={};rows=[];heading_roundoff=0.
    for case in retained_cases():
        prepared=prepare_case(case);prior=prior_case(case)
        archived=read(prior/'initial_engine.json')
        if prepared.receipt()!=archived:raise RuntimeError('Retained full initial receipt changed: '+case.name)
        with np.load(prior/'initial_school.npz',allow_pickle=False) as saved:
            # Native construction normalizes headings by tiny roundoff. The
            # original raw checkpoint bytes are source-bound; exact equality
            # of the resulting native headings is required at the next gate.
            if not all(np.array_equal(np.asarray(value),saved[name]) for name,value in asdict(prepared.initial).items() if name!='directions'):
                raise RuntimeError('Retained fish checkpoint changed')
            difference=float(np.max(np.abs(prepared.initial.directions-saved['directions'])))
            if not np.isfinite(difference) or difference>1e-12:
                raise RuntimeError('Pure/archive heading normalization discrepancy exceeds recorded roundoff bound')
            heading_roundoff=max(heading_roundoff,difference)
        old[case.name]=archived;states[case.school_seed]=state_digest(prepared.initial)
    for case in all_cases():
        prepared=prepare_case(case);receipt=prepared.receipt()
        if state_digest(prepared.initial)!=states[case.school_seed]:raise RuntimeError('New count changes fish initialization')
        base_d=next(c for c in retained_cases() if c.school_seed==case.school_seed and c.dolphins and c.gannets==0 and c.herding_minimum==(case.herding_minimum or 1.))
        if receipt['ownership']!=old[base_d.name]['ownership'] or receipt['tie_rng']!=old[base_d.name]['tie_rng']:
            raise RuntimeError('Shared prey ownership/tie initialization changed')
        if case.dolphins and restrict(receipt,'D')!=restrict(old[base_d.name],'D'):
            raise RuntimeError('Dolphin physics/readiness/private/controller starts change with bird count')
        base_g=next(c for c in retained_cases() if c.school_seed==case.school_seed and not c.dolphins and c.gannets==18)
        if restrict(receipt,'G',{f'G{i}' for i in range(18)})!=restrict(old[base_g.name],'G'):
            raise RuntimeError('Original eighteen bird states/private streams changed')
        original={a['actor_id']:a for a in old[base_g.name]['actors']}
        for actor in receipt['actors']:
            if not actor['actor_id'].startswith('G'):continue
            site=original[f"G{int(actor['actor_id'][1:])%3}"]
            for key in ('position','heading','mode','time'):
                if actor[key]!=site[key]:raise RuntimeError('Nested site state changed')
        if prepared.scenario.dt!=DT or any(a.config.spacing_enabled or a.capture_probability!=.7 for a in prepared.actors):
            raise RuntimeError('Frozen grid/point-body/q assumptions changed')
        rows.append(dict(**case.asdict(),initial_school_sha256=state_digest(prepared.initial),actors=len(prepared.actors)))
    if (len(rows)!=32 or len({r['case_name'] for r in rows})!=32
            or sum(round(36/DT) for _ in rows)!=921600
            or sum(round(4/DT) for _ in smoke_cases())!=16000
            or [len(v) for _,v in execution_stages('pilot')]!=[2,6]
            or [len(v) for _,v in execution_stages('remainder')]!=[6,18]
            or {c.name for c in phase_cases('pilot')} & {c.name for c in phase_cases('remainder')}):
        raise RuntimeError('Balanced new count design/step ceiling changed')
    return dict(status='passed',native_constructions=0,native_steps=0,pure_new_cases=32,
        exact_retained_initial_receipts=108,independent_schools=4,
        pure_to_archived_native_heading_max_abs_roundoff=heading_roundoff,
        pure_heading_roundoff_bound=1e-12,actual_native_heading_comparison='Exact np.array_equal at actual initialization gate; no tolerance',
        initial_conditions='All108 Python actor/controller/private receipts exact; raw checkpoint files unchanged; archived fish positions/IDs/clocks exact; native heading normalization must replay exactly at actual gate',
        roster='Gi starts at original G(i modulo3) site;24/36 are balanced8/12 per site; no spacing/avoidance',rows=rows)

if __name__=='__main__':
    path=HERE/'PURE_PREFLIGHT.json'
    if path.exists():raise RuntimeError('Never overwrite a preflight receipt')
    result=validate();write(path,result);print({k:v for k,v in result.items() if k!='rows'})
