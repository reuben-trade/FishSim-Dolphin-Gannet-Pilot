"""Native-free verification of all108 retained/new encounters and18mixed cells.

Refuses partial data. Historical v5 evidence/code stays immutable. The new48
encounters use the same four previously observed schools and are not new
independent schools. No scientific runner or native module is imported.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
import regime_evidence_v5 as old

ROOT=Path(__file__).resolve().parent
SCIENCE=ROOT/'data/research/high_count_regime_extension_2026-11-09'
DISPATCH=ROOT/'data/research/high_count_pilot_dispatch_2026-11-09_v2'
BULK=SCIENCE/'results'
FULL=BULK/'full_36T_v1'
OLD=ROOT/'data/research/pilot_regime_sweep_2026-11-09_v2'
CLOSURE=ROOT/'SOURCE_CLOSURE_2026-11-09_high_counts.json'
SCIENCE_SHA='573a30e4860cb36176140352c5d64be2c42de61c2456e0d1955f9ac8a5edf831'
DISPATCH_SHA='0aec537f7f382a84dc851fe46f468187aa3083ec891ab23d8586311f6a1a23e4'
SEEDS=old.SEEDS
HS=old.HS
GS=(0,1,3,6,9,12,18)
NEW_GS=(9,12,18)
DURATION=36.
read,sha,compare_csv=old.read,old.sha,old.compare_csv


def identities(counts=GS):
    out=[]
    for seed in SEEDS:
        for h in HS:
            for g in counts:
                policy=f'H{h:g}_G{g}';presence='DG' if g else 'D'
                out.append(dict(school_seed=seed,herding_minimum_T=h,gannets=g,dolphins=12,
                    policy=policy,presence=presence,capture_seed=61001,dt=.00125,duration_T=36.,
                    anchor_replay=h==2 and g in (0,3),case_name=f's{seed}_{policy}_{presence}_c61001'))
        for g in counts:
            if not g:continue
            policy=f'Gonly{g}'
            out.append(dict(school_seed=seed,herding_minimum_T=None,gannets=g,dolphins=0,
                policy=policy,presence='G',capture_seed=61001,dt=.00125,duration_T=36.,
                anchor_replay=False,case_name=f's{seed}_{policy}_G_c61001'))
    return out


def folder(case):
    return (FULL if case['gannets'] in NEW_GS else OLD/'results/full_36T_v1')/'cases'/case['case_name']


def readiness():
    names=['status.json','physical_review.json','analysis_final/analysis_audit.json','dispatch_analysis_binding.json']
    missing=[n for n in names if not (FULL/n).is_file()]
    if missing:return dict(status='not_ready',missing=missing,native_steps=0)
    status,physical,audit,binding=[read(FULL/n) for n in names]
    passed=(status.get('status')=='complete' and status.get('complete')==48
        and physical.get('status')=='passed' and len(physical.get('cases',[]))==48
        and all(r.get('status')=='passed' for r in physical['cases'])
        and audit.get('status')=='passed' and audit.get('new_cases')==48
        and audit.get('retained_cases')==60 and audit.get('cells')==108
        and audit.get('mixed_map_cells')==18 and audit.get('independent_schools')==4
        and binding.get('status')=='passed')
    return dict(status='ready' if passed else 'not_ready',native_steps=0)


def source_checks():
    if sha(SCIENCE/'frozen_sources.json')!=SCIENCE_SHA or sha(DISPATCH/'DISPATCH_FREEZE.json')!=DISPATCH_SHA:
        raise ValueError('Reviewed scientific/dispatch source version differs')
    science,dispatch=read(SCIENCE/'frozen_sources.json'),read(DISPATCH/'DISPATCH_FREEZE.json')
    expected=dict(science['source_sha256'])
    for name,digest in dispatch['source_sha256'].items():
        if name in expected and expected[name]!=digest:raise ValueError('Conflicting source declarations')
        expected[name]=digest
    if CLOSURE is None:paths={name:Path(name) for name in expected}
    else:
        closure=read(CLOSURE)
        if len(closure)!=len(expected) or {r['original_path']:r['sha256'] for r in closure}!=expected:
            raise ValueError('Scientific/dispatch source-closure identities differ')
        paths={r['original_path']:ROOT/r['bundled_path'] for r in closure}
    for name,digest in expected.items():
        if sha(paths[name])!=digest:raise ValueError('Frozen input changed: '+name)
    for name,key in [('INPUT_FREEZE.json','input_freeze_sha256'),('ACTUAL_ZERO_STEP.json','actual_zero_step_sha256')]:
        if sha(SCIENCE/name)!=science[key]:raise ValueError('Scientific preparation binding differs')
    inputs,pure,zero=[read(SCIENCE/n) for n in ['INPUT_FREEZE.json','PURE_PREFLIGHT.json','ACTUAL_ZERO_STEP.json']]
    if (inputs['pure_preflight_sha256']!=sha(SCIENCE/'PURE_PREFLIGHT.json')
            or pure.get('status')!='passed' or pure.get('pure_new_cases')!=48
            or pure.get('exact_retained_initial_receipts')!=60 or pure.get('native_steps')!=0
            or zero.get('status')!='passed' or zero.get('actual_cases')!=48 or zero.get('native_steps')!=0):
        raise ValueError('All48 pure/actual zero-step preparation gates must pass')
    for phase,n,ceiling in [('pilot',12,345600),('remainder',36,1036800)]:
        approval=read(DISPATCH/(phase.upper()+'_RUN_APPROVED.json'))
        if (approval.get('approved') is not True or approval.get('phase')!=phase
                or approval.get('dispatch_freeze_sha256')!=DISPATCH_SHA
                or approval.get('amendment_sha256')!=sha(DISPATCH/'amendment.json')
                or approval.get('maximum_cases')!=n or approval.get('maximum_native_steps')!=ceiling):
            raise ValueError('Dispatch phase scope/source binding differs')
    return science


def raw_case(folder,case,frozen,reader):
    row=reader.raw_row(folder,case,frozen)
    summary=read(folder/'summary.json')
    engine=read(folder/'initial_engine.json')
    roster={r['actor_id']:r['species'] for r in engine['actors']}
    expected_ids={f'D{i:02d}' for i in range(case['dolphins'])}|{f'G{i}' for i in range(case['gannets'])}
    if (len(roster)!=len(engine['actors']) or set(roster)!=expected_ids or set(summary['per_actor'])!=set(roster)
            or any(set(engine[field])!=set(roster) for field in ['actor_policy','capture_rng','controllers'])
            or sum(v=='D' for v in roster.values())!=case['dolphins']
            or sum(v=='G' for v in roster.values())!=case['gannets']
            or any(not name.startswith(species) for name,species in roster.items())):
        raise ValueError('Exact actor/initial-policy/private-controller roster differs')
    if summary['initial_count']!=160:raise ValueError('Unexpected initial fish count')
    with gzip.open(folder/'events.jsonl.gz','rt') as handle:events=[json.loads(line) for line in handle]
    for event in events:
        if event.get('kind')=='oral' or (event.get('kind')=='transition' and event.get('reason')=='launch'):
            if event.get('actor_id') not in summary['per_actor']:raise ValueError('Unknown actor in raw account')
        elapsed=event.get('elapsed')
        if elapsed is not None and not -1e-7<=elapsed<=summary['actual_duration']+1e-7:
            raise ValueError('Event lies outside observed native duration')
    captured=[]
    for actor,account in summary['per_actor'].items():
        oral=[e for e in events if e.get('kind')=='oral' and e.get('actor_id')==actor and e.get('closes_bout')]
        catches=[e for e in oral if e['status']=='captured']
        launches=[e for e in events if e.get('kind')=='transition' and e.get('actor_id')==actor and e.get('reason')=='launch']
        if (len(catches),len(oral),len(launches))!=(account['captures'],account['contacts'],account['launches']):
            raise ValueError('Per-actor raw accounting differs')
        if abs(sum(account['time'].values())-summary['actual_duration'])>1e-6:
            raise ValueError('Per-actor observed time budget differs')
        captured.extend(e['prey_id'] for e in catches)
    import numpy as np
    with np.load(folder/'initial_school.npz',allow_pickle=False) as initial:
        if not set(captured)<=set(initial['prey_ids'].tolist()):raise ValueError('Captured foreign prey ID')
    if len(captured)!=len(set(captured)) or len(captured)!=160-summary['final_count']:
        raise ValueError('Unique prey-removal conservation differs')
    return row


def same_start(a,b,species):
    import numpy as np
    with np.load(a/'initial_school.npz',allow_pickle=False) as x,np.load(b/'initial_school.npz',allow_pickle=False) as y:
        if set(x.files)!=set(y.files) or not all(np.array_equal(x[k],y[k]) for k in x.files):
            raise ValueError('Initial fish states differ')
    x,y=read(a/'initial_engine.json'),read(b/'initial_engine.json')
    actors=lambda d:{r['actor_id']:r for r in d['actors'] if r['species']==species}
    if actors(x)!=actors(y):raise ValueError('Initial predator physical/readiness states differ')
    for field in ['capture_rng','actor_policy','controllers']:
        choose=lambda d:{k:v for k,v in d[field].items() if k.startswith(species)}
        if choose(x)!=choose(y):raise ValueError('Initial predator controller/private streams differ: '+field)
    if x['tie_rng']!=y['tie_rng']:raise ValueError('Initial tie stream differs')


def reconstruct_map(rows, plan):
    """One common four-school bootstrap including selection within every draw."""
    lookup = {(r['school_seed'],r['herding_minimum_T'],r['gannets'],bool(r['dolphins'])):r for r in rows}
    if len(lookup) != 108 or len(rows) != 108:
        raise ValueError('Complete unique108-case map required')
    settings = [(h,g) for h in HS for g in GS[1:]]
    control = np.array([[lookup[s,h,0,True]['D_rate'] for h in HS] for s in SEEDS])
    best_index = int(np.argmax(control.mean(axis=0)))
    control_totals = [sum(lookup[s,h,0,True]['D_captures'] for s in SEEDS) for h in HS]
    if best_index != int(np.argmax(control_totals)):
        raise ValueError('Best-tested H must use exact capture-total ties, choosing smaller H')
    best_h = HS[best_index]
    vectors, mixed, pairs = [], [], []
    for seed in SEEDS:
        vector, returns = [], []
        for h,g in settings:
            d0, dg, g0 = lookup[seed,h,0,True], lookup[seed,h,g,True], lookup[seed,None,g,False]
            d, b = dg['D_rate']-d0['D_rate'], dg['G_rate']-g0['G_rate']
            vector.append([d,b]); returns.append(dg['D_rate'])
            pairs.append(dict(school_seed=seed,herding_minimum_T=h,gannets=g,
                D_rate_alone=d0['D_rate'],D_rate_mixed=dg['D_rate'],D_rate_change=d,
                G_rate_alone=g0['G_rate'],G_rate_mixed=dg['G_rate'],G_rate_change=b,
                D_capture_change=dg['D_captures']-d0['D_captures'],
                G_capture_change=dg['G_captures']-g0['G_captures'],best_tested_Donly_H=best_h,
                D_rate_change_vs_best_tested_Donly=dg['D_rate']-lookup[seed,best_h,0,True]['D_rate'],
                both_rate_changes_positive=d>0 and b>0))
        vectors.append(vector);mixed.append(returns)
    values, mixed = np.array(vectors), np.array(mixed)
    boot = plan['bootstrap']
    if (boot['draws'],boot['seed'],boot['quantiles']) != (10000,88493009,[.025,.975]):
        raise ValueError('Declared bootstrap changed')
    indices = np.random.default_rng(boot['seed']).integers(0,4,size=(boot['draws'],4))
    bounds = np.quantile(values[indices].mean(axis=1),boot['quantiles'],axis=0)
    means = values.mean(axis=0)
    best_bounds = np.quantile(mixed[indices].mean(axis=1)-control[indices].mean(axis=1).max(axis=1)[:,None],
                              boot['quantiles'],axis=0)
    summary = []
    for j,(h,g) in enumerate(settings):
        r = dict(herding_minimum_T=h,gannets=g,independent_schools=4)
        for k,species in enumerate(('D','G')):
            r.update({species+'_mean_rate_change':float(means[j,k]),
                species+'_pointwise95_low':float(bounds[0,j,k]),species+'_pointwise95_high':float(bounds[1,j,k]),
                species+'_positive_schools':int((values[:,j,k]>0).sum()),
                species+'_zero_schools':int((values[:,j,k]==0).sum()),
                species+'_negative_schools':int((values[:,j,k]<0).sum())})
        r.update(both_positive_schools=int(((values[:,j,0]>0)&(values[:,j,1]>0)).sum()),
            best_tested_Donly_H=best_h,best_tested_Donly_mean_rate=float(control[:,best_index].mean()),
            D_mixed_mean_rate=float(mixed[:,j].mean()),
            D_mean_rate_change_vs_best_tested_Donly=float(mixed[:,j].mean()-control[:,best_index].mean()),
            D_vs_best_tested_pointwise95_low=float(best_bounds[0,j]),D_vs_best_tested_pointwise95_high=float(best_bounds[1,j]))
        summary.append(r)
    return pairs,summary



def all_rows():
    frozen=read(SCIENCE/'frozen_sources.json');prior=read(OLD/'frozen_sources.json')
    rows=[]
    for case in identities():
        retained=case['gannets'] not in NEW_GS
        row=raw_case(folder(case),case,prior if retained else frozen,old)
        row['execution_origin']='retained_discovery' if retained else 'new_high_count_extension'
        rows.append(row)
    return rows


def diagnostic_rows():
    rows=[]
    for case in identities():
        state=[r for r in read(folder(case)/'school_metrics.json') if r['n_live']>0]
        times=np.array([r['elapsed'] for r in state])
        if len(times)<2 or not (np.diff(times)>0).all() or times[-1]>36+1e-7:
            raise ValueError('Insufficient or nonmonotonic school-state frames')
        row=dict(case_name=case['case_name'],school_seed=case['school_seed'],
            herding_minimum_T=case['herding_minimum_T'],gannets=case['gannets'],presence=case['presence'],
            state_duration_T=float(times[-1]-times[0]),state_frames=len(state),
            state_condition='Observed live-school frames; survivor-conditional, not causal mediation')
        for field in ['r90','outward_fraction','largest_component_fraction','mean_depth']:
            v=np.array([r[field] for r in state],float)
            if not np.isfinite(v).all():raise ValueError('Nonfinite school diagnostic')
            row['time_mean_'+field]=float(np.sum((v[1:]+v[:-1])/2*np.diff(times))/(times[-1]-times[0]))
        rows.append(row)
    return rows


def verify_complete():
    if readiness()['status']!='ready':raise ValueError('All48 new cases and fullmap receipts required')
    frozen=source_checks()
    prior=old.verify_complete(OLD,closure=ROOT/'SOURCE_CLOSURE_2026-11-09_regime_v2.json',bundle_root=ROOT)
    if prior['cells']!=60 or prior['anchor_replay_executions']!=8:raise ValueError('Inherited discovery bank differs')
    cases=identities();new=[r for r in cases if r['gannets'] in NEW_GS]
    if {p.name for p in (FULL/'cases').iterdir() if p.is_dir()}!={r['case_name'] for r in new}:
        raise ValueError('New48-case matrix differs')
    rows=all_rows();byname={r['case_name']:r for r in rows}
    seals={r['case_name']:r['completion_sha256'] for r in rows}
    newseals={r['case_name']:seals[r['case_name']] for r in new}
    physical=read(FULL/'physical_review.json');audit=read(FULL/'analysis_final/analysis_audit.json')
    if physical['review_source_sha256']!=sha(SCIENCE/'review_actual.py'):
        raise ValueError('Current physical review source differs')
    if {r['case']:r['completion_sha256'] for r in physical['cases']}!=newseals:
        raise ValueError('Physical review must bind all48 current seals')
    if audit['case_completion_sha256']!=seals or audit['new_case_completion_sha256']!=newseals:
        raise ValueError('Analysis must bind all108 retained/new seals')
    for name,digest in audit['files'].items():
        if sha(FULL/'analysis_final'/name)!=digest:raise ValueError('Stored analysis output changed')
    companions={}
    for case in new:
        name=case['case_name'];path=FULL/'case_dispatch_manifests'/(name+'.json');c=read(path)
        phase='pilot' if case['school_seed']==SEEDS[0] else 'remainder'
        if (c['case']!=case or c['phase']!=phase or c['dispatch_freeze_sha256']!=DISPATCH_SHA
                or c['scientific_source_freeze_sha256']!=SCIENCE_SHA
                or c['amendment_sha256']!=sha(DISPATCH/'amendment.json')
                or c['phase_approval_sha256']!=sha(DISPATCH/(phase.upper()+'_RUN_APPROVED.json'))
                or c['scientific_completion_sha256']!=seals[name] or c['native_steps']!=byname[name]['native_steps']):
            raise ValueError('Case dispatch companion/source/phase differs')
        companions[path.name]=sha(path)
        bird=next(r for r in new if r['school_seed']==case['school_seed'] and r['gannets']==case['gannets'] and not r['dolphins'])
        if case['dolphins']:
            alone=next(r for r in cases if r['school_seed']==case['school_seed'] and r['herding_minimum_T']==case['herding_minimum_T'] and not r['gannets'])
            same_start(folder(case),folder(alone),'D');same_start(folder(case),folder(bird),'G')
    binding=read(FULL/'dispatch_analysis_binding.json')
    if (binding['dispatch_freeze_sha256']!=DISPATCH_SHA
            or binding['original_analysis_sha256']!=sha(FULL/'analysis_final/analysis_audit.json')
            or binding['companions']!=companions):raise ValueError('Final dispatch/analysis binding differs')
    for phase,n in [('pilot',12),('remainder',36)]:
        path=BULK/('dispatch_'+phase+'_v1')/'execution.json';execution=read(path)
        approval_path=DISPATCH/(phase.upper()+'_RUN_APPROVED.json');approval=read(approval_path)
        phase_cases=[r for r in new if ('pilot' if r['school_seed']==SEEDS[0] else 'remainder')==phase]
        actual_steps=sum(byname[r['case_name']]['native_steps'] for r in phase_cases)
        bridge=path.parent/'activated_frozen_runner_bridge.json'
        template=DISPATCH/'COMPATIBILITY_BRIDGE_TEMPLATE.json'
        if (binding['phase_execution_sha256'][phase]!=sha(path) or execution['status']!='complete'
                or len(execution['case_names'])!=n
                or set(execution['case_names'])!={r['case_name'] for r in phase_cases}
                or execution['native_steps']!=actual_steps
                or actual_steps>approval['maximum_native_steps']
                or execution['maximum_native_steps']!=approval['maximum_native_steps']
                or execution['phase_approval_sha256']!=sha(approval_path)
                or execution['dispatch_freeze_sha256']!=DISPATCH_SHA
                or approval['bridge_template_sha256']!=sha(template)
                or sha(bridge)!=sha(template)):
            raise ValueError('Completed phase execution receipt differs')
    pairs,summary=reconstruct_map(rows,read(SCIENCE/'analysis_plan.json'))
    compare_csv(FULL/'analysis_final/case_outcomes.csv',rows,('case_name',))
    compare_csv(FULL/'analysis_final/paired_school_changes.csv',pairs,('school_seed','herding_minimum_T','gannets'))
    compare_csv(FULL/'analysis_final/regime_summary.csv',summary,('herding_minimum_T','gannets'))
    if 'fish_sim.cmodel' in sys.modules:raise ValueError('Native simulation imported during verification')
    return dict(status='passed',new_cases=48,retained_cases=60,cells=108,paired_rows=72,map_cells=18,
        independent_previously_observed_schools=4,original_exact_replays=8,source_files=len(read(CLOSURE)) if CLOSURE else len(frozen['source_sha256']),
        all_raw_accounts_starts_dispatch_and_bootstrap_reconstructed=True,native_steps=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--readiness-only',action='store_true')
    args=parser.parse_args();gate=readiness()
    if args.readiness_only or gate['status']!='ready':print(json.dumps(gate,indent=2));return 0 if gate['status']=='ready' else 2
    print(json.dumps(verify_complete(),indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
