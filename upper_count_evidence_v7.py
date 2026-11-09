"""Read-only reconstruction of the complete140-outcome,24-setting upper bank.

Native-free acceptance audit; the compact paper notebook retains saved interval
endpoints instead of running this separate10,000-draw verification on Run All.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
import high_count_evidence_v6 as prior

ROOT=Path(__file__).resolve().parent
SCIENCE=ROOT/'data/research/upper_count_regime_extension_2026-11-09'
RESULTS=SCIENCE/'results'
FULL=RESULTS/'full_36T_v1'
CLOSURE=ROOT/'SOURCE_CLOSURE_2026-11-10_upper_counts.json'
FREEZE='f37d767a57a14b44fe2c32cbb921471b07df3f98a9211a37f6f70db256f64738'
REVIEW='54331dbc2430a6f6660cea3aedbf37c45bb7a224c8303ff5bebf03647b9c20d3'
GS=(0,1,3,6,9,12,18,24,36)
NEW_GS=(24,36)
SEEDS,HS=prior.SEEDS,prior.HS
read,sha,compare_csv=prior.read,prior.sha,prior.compare_csv

def identities(counts=GS):return prior.identities(counts)
def folder(case):return FULL/'cases'/case['case_name'] if case['gannets'] in NEW_GS else prior.folder(case)

def readiness():
    paths=[FULL/'status.json',FULL/'physical_review.json',FULL/'analysis_final/analysis_audit.json',RESULTS/'independent_complete_map_review.json']
    if not all(p.is_file() for p in paths):raise ValueError('Complete32-case and independent final gates required')
    s,p,a,r=map(read,paths)
    assert s['status']=='complete' and s['complete']==s['planned']==32
    assert p['status']=='passed' and len(p['cases'])==32 and all(c['status']=='passed' for c in p['cases'])
    assert a['status']=='passed' and (a['new_cases'],a['retained_cases'],a['cells'],a['mixed_map_cells'],a['independent_schools'])==(32,108,140,24,4)
    assert sha(paths[3])==REVIEW and r['status']=='passed'
    for k,pth in [('source_freeze_sha256',SCIENCE/'frozen_sources.json'),('status_sha256',paths[0]),('physical_review_sha256',paths[1]),('analysis_audit_sha256',paths[2])]:assert r[k]==sha(pth),k
    return s,p,a,r

def sources():
    assert sha(SCIENCE/'frozen_sources.json')==FREEZE
    frozen=read(SCIENCE/'frozen_sources.json');closure=read(CLOSURE)
    assert len(closure)==3336 and {r['original_path']:r['sha256'] for r in closure}==frozen['source_sha256']
    for r in closure:assert sha(ROOT/r['bundled_path'])==r['sha256'],r['bundled_path']
    assert sha(SCIENCE/'INPUT_FREEZE.json')==frozen['input_freeze_sha256']
    assert sha(SCIENCE/'ACTUAL_ZERO_STEP.json')==frozen['actual_zero_step_sha256']
    inputs=read(SCIENCE/'INPUT_FREEZE.json');assert sha(SCIENCE/'PURE_PREFLIGHT.json')==inputs['pure_preflight_sha256']
    assert read(SCIENCE/'PURE_PREFLIGHT.json')['status']=='passed' and read(SCIENCE/'ACTUAL_ZERO_STEP.json')['status']=='passed'
    return frozen

def all_rows():
    frozen=read(SCIENCE/'frozen_sources.json');rows=prior.all_rows()
    for r in rows:r['execution_origin']='retained_discovery' if r['gannets']<=6 else 'retained_high_count_extension'
    for case in identities(NEW_GS):
        r=prior.raw_case(folder(case),case,frozen,prior.old);r['execution_origin']='new_upper_count_extension';rows.append(r)
    return rows

def reconstruct(rows):
    lookup={(r['school_seed'],r['herding_minimum_T'],r['gannets'],bool(r['dolphins'])):r for r in rows}
    assert len(rows)==len(lookup)==140
    settings=[(h,g) for h in HS for g in GS[1:]]
    control=np.array([[lookup[s,h,0,True]['D_captures']/432 for h in HS] for s in SEEDS])
    totals=[sum(lookup[s,h,0,True]['D_captures'] for s in SEEDS) for h in HS]
    best_index=max(range(3),key=lambda i:(totals[i],-HS[i]));best_h=HS[best_index]
    values=[];mixed=[];pairs=[];integer_deltas=[]
    for seed in SEEDS:
        vector=[];absolute=[];ints=[]
        for h,g in settings:
            d0,dg,g0=lookup[seed,h,0,True],lookup[seed,h,g,True],lookup[seed,None,g,False]
            dc=dg['D_captures']-d0['D_captures'];gc=dg['G_captures']-g0['G_captures'];d=dc/432;b=gc/(g*36)
            vector.append([d,b]);absolute.append(dg['D_rate']);ints.append([dc,gc])
            pairs.append(dict(school_seed=seed,herding_minimum_T=h,gannets=g,D_rate_alone=d0['D_rate'],D_rate_mixed=dg['D_rate'],D_rate_change=d,G_rate_alone=g0['G_rate'],G_rate_mixed=dg['G_rate'],G_rate_change=b,D_capture_change=dc,G_capture_change=gc,best_tested_Donly_H=best_h,D_rate_change_vs_best_tested_Donly=(dg['D_captures']-lookup[seed,best_h,0,True]['D_captures'])/432,both_rate_changes_positive=dc>0 and gc>0))
        values.append(vector);mixed.append(absolute);integer_deltas.append(ints)
    values=np.array(values);mixed=np.array(mixed);integer_deltas=np.array(integer_deltas)
    plan=read(SCIENCE/'analysis_plan.json')['bootstrap'];assert (plan['draws'],plan['seed'],plan['quantiles'])==(10000,88493009,[.025,.975])
    indices=np.random.default_rng(plan['seed']).integers(0,4,size=(10000,4))
    bounds=np.quantile(values[indices].mean(axis=1),[.025,.975],axis=0)
    bestbounds=np.quantile(mixed[indices].mean(axis=1)-control[indices].mean(axis=1).max(axis=1)[:,None],[.025,.975],axis=0)
    summary=[]
    for j,(h,g) in enumerate(settings):
        row=dict(herding_minimum_T=h,gannets=g,independent_schools=4)
        for k,species,n in [(0,'D',12),(1,'G',g)]:
            exact=int(integer_deltas[:,j,k].sum())/(4*n*36)
            row.update({species+'_mean_rate_change':exact,species+'_pointwise95_low':float(bounds[0,j,k]),species+'_pointwise95_high':float(bounds[1,j,k]),species+'_positive_schools':int((integer_deltas[:,j,k]>0).sum()),species+'_zero_schools':int((integer_deltas[:,j,k]==0).sum()),species+'_negative_schools':int((integer_deltas[:,j,k]<0).sum())})
        row.update(both_positive_schools=int(((integer_deltas[:,j,0]>0)&(integer_deltas[:,j,1]>0)).sum()),best_tested_Donly_H=best_h,best_tested_Donly_mean_rate=float(control[:,best_index].mean()),D_mixed_mean_rate=float(mixed[:,j].mean()),D_mean_rate_change_vs_best_tested_Donly=(sum(lookup[s,h,g,True]['D_captures'] for s in SEEDS)-totals[best_index])/(4*432),D_vs_best_tested_pointwise95_low=float(bestbounds[0,j]),D_vs_best_tested_pointwise95_high=float(bestbounds[1,j]))
        summary.append(row)
    return pairs,summary

def diagnostics(rows):
    out=[];largest_error=0.
    for case in identities():
        path=folder(case);states=[r for r in read(path/'school_metrics.json') if r['n_live']>0];t=np.array([r['elapsed'] for r in states]);assert len(t)>1 and (np.diff(t)>0).all()
        row=dict(case_name=case['case_name'],school_seed=case['school_seed'],herding_minimum_T=case['herding_minimum_T'],gannets=case['gannets'],dolphins=case['dolphins'],presence=case['presence'],state_duration_T=float(t[-1]-t[0]),state_frames=len(t))
        for field in ['r90','outward_fraction','largest_component_fraction','mean_depth']:
            v=np.array([r[field] for r in states]);assert np.isfinite(v).all();row['time_mean_'+field]=float(np.sum((v[1:]+v[:-1])/2*np.diff(t))/(t[-1]-t[0]))
        # Independent reconstruction from recorded live-fish positions, not saved radius values.
        with np.load(path/'trajectories.npz',allow_pickle=False) as trace:
            assert len(trace['time'])==len(states)
            raw=[]
            for positions,alive in zip(trace['positions'],trace['alive']):
                p=positions[alive];raw.append(float(np.quantile(np.linalg.norm(p-p.mean(axis=0),axis=1),.9)))
        saved=np.array([r['r90'] for r in states]);err=float(np.max(np.abs(np.array(raw)-saved)));largest_error=max(largest_error,err)
        if not np.allclose(raw,saved,rtol=1e-11,atol=1e-11):raise ValueError('Raw radius differs: '+case['case_name'])
        original=next(r for r in rows if r['case_name']==case['case_name'])
        for s in ['D','G']:
            for field in ['captures','contacts','launches']:row[s+'_'+field]=original[s+'_'+field]
        out.append(row)
    return out,largest_error

def verify_complete(with_diagnostics=False):
    status,physical,audit,independent=readiness();frozen=sources()
    inherited=prior.verify_complete();assert inherited['cells']==108
    rows=all_rows();byname={r['case_name']:r for r in rows};new=identities(NEW_GS);seals={r['case_name']:r['completion_sha256'] for r in rows};newseals={c['case_name']:seals[c['case_name']] for c in new}
    assert {p.name for p in (FULL/'cases').iterdir() if p.is_dir()}==set(newseals)
    assert {r['case']:r['completion_sha256'] for r in physical['cases']}==newseals
    assert physical['review_source_sha256']==sha(SCIENCE/'review_actual.py')
    assert audit['case_completion_sha256']==independent['case_completion_sha256']==seals
    assert audit['new_case_completion_sha256']==newseals
    for n,d in audit['files'].items():assert sha(FULL/'analysis_final'/n)==d,n
    for case in new:
        if case['dolphins']:
            control=next(c for c in identities() if c['school_seed']==case['school_seed'] and c['herding_minimum_T']==case['herding_minimum_T'] and c['gannets']==0)
            birds=next(c for c in new if c['school_seed']==case['school_seed'] and c['gannets']==case['gannets'] and not c['dolphins'])
            prior.same_start(folder(case),folder(control),'D');prior.same_start(folder(case),folder(birds),'G')
    for phase,n,steps in [('pilot',8,230400),('remainder',24,691200)]:
        record=RESULTS/(phase+'_phase_v1');execution=read(record/'execution.json');pstatus=read(record/'status.json');review=read(record/'physical_review.json');approval=read(SCIENCE/(phase.upper()+'_RUN_APPROVED.json'))
        names={c['case_name'] for c in new if (c['school_seed']==SEEDS[0])==(phase=='pilot')}
        assert execution['status']=='complete' and pstatus['status']=='complete' and review['status']=='passed'
        assert set(approval['case_names'])==names and len(names)==n and pstatus['complete']==n
        assert execution['total_native_steps']==pstatus['total_native_steps']==sum(byname[x]['native_steps'] for x in names)==steps
        assert execution['maximum_native_steps']==approval['maximum_native_steps']==steps and approval['approved'] is True
        assert execution['frozen_sources_sha256']==approval['freeze_sha256']==FREEZE
        assert execution['protocol_sha256']==approval['protocol_sha256']==sha(SCIENCE/'protocol.json')
        assert physical['phase_review_sha256'][phase]==sha(record/'physical_review.json') and status['phase_status_sha256'][phase]==sha(record/'status.json')
        assert review['status_sha256']==sha(record/'status.json') and review['wrapper_source_sha256']==sha(SCIENCE/'review_phase.py')
        assert independent['phases'][phase]['native_steps']==steps
        for key,path in [('phase_approval_sha256',SCIENCE/(phase.upper()+'_RUN_APPROVED.json')),('phase_execution_sha256',record/'execution.json'),('phase_status_sha256',record/'status.json'),('phase_physical_sha256',record/'physical_review.json')]:assert independent['phases'][phase][key]==sha(path),key
    # Five separately recorded4T engineering checks; exact prefixes, never feeding rows.
    smoke_approval=read(SCIENCE/'SMOKE_RUN_APPROVED.json');smoke_execution=read(RESULTS/'smoke_phase_v1/execution.json');smoke_physical=read(RESULTS/'smoke_phase_v1/physical_review.json')
    assert smoke_execution['status']=='complete' and smoke_execution['total_native_steps']==smoke_approval['maximum_native_steps']==16000
    assert smoke_physical['status']=='passed' and len(smoke_physical['cases'])==5
    assert smoke_approval['freeze_sha256']==smoke_execution['frozen_sources_sha256']==FREEZE
    assert smoke_physical['review_source_sha256']==sha(SCIENCE/'review_actual.py')
    assert smoke_physical['wrapper_source_sha256']==sha(SCIENCE/'review_phase.py')
    smoke_folder=RESULTS/'smoke_4T_v1/cases'
    assert {p.name for p in smoke_folder.iterdir()}==set(smoke_approval['case_names'])
    for name in smoke_approval['case_names']:
        smoke=smoke_folder/name;seal=read(smoke/'completion.json');summary=read(smoke/'summary.json');config=read(smoke/'config.json')
        assert seal['status']=='complete' and summary['native_steps']==3200 and summary['planned_duration']==4. and summary['dt']==.00125
        for rel,digest in seal['files'].items():assert not Path(rel).is_absolute() and '..' not in Path(rel).parts and sha(smoke/rel)==digest
        assert read(smoke/'source_manifest.json')==frozen['source_sha256']
        case=next(c for c in new if c['case_name']==name)
        assert config['counts']==dict(fish=160,D=case['dolphins'],G=case['gannets']) and config['capture_probability']==.7
        for species in (['D','G'] if case['dolphins'] else ['G']):prior.same_start(smoke,folder(case),species)
        with np.load(smoke/'trajectories.npz',allow_pickle=False) as a,np.load(folder(case)/'trajectories.npz',allow_pickle=False) as b:
            assert set(a.files)==set(b.files);frames=len(a['time'])
            for key in a.files:
                actual=a[key];expected=b[key] if key in ['actor_ids','prey_ids'] else b[key][:frames]
                assert actual.dtype==expected.dtype and np.array_equal(actual,expected),(name,key)
    pairs,summary=reconstruct(rows)
    compare_csv(FULL/'analysis_final/case_outcomes.csv',rows,('case_name',))
    compare_csv(FULL/'analysis_final/paired_school_changes.csv',pairs,('school_seed','herding_minimum_T','gannets'))
    compare_csv(FULL/'analysis_final/regime_summary.csv',summary,('herding_minimum_T','gannets'))
    dsigns=[sum(r['D_mean_rate_change']>0 for r in summary),sum(r['D_mean_rate_change']==0 for r in summary),sum(r['D_mean_rate_change']<0 for r in summary)];assert dsigns==[18,2,4]
    gsigns=[sum(r['G_mean_rate_change']>0 for r in summary),sum(r['G_mean_rate_change']==0 for r in summary),sum(r['G_mean_rate_change']<0 for r in summary)];assert gsigns==[20,2,2]
    assert not any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules)
    result=dict(status='passed',outcomes=140,new_cases=32,retained_cases=108,paired_rows=96,mixed_cells=24,independent_schools=4,source_bindings=3336,new_full_native_steps=921600,separate_engineering_smokes=5,separate_engineering_native_steps=16000,all_five_smoke_prefixes_exact=True,native_steps_by_reader=0,bootstrap_verification_draws=10000,D_mean_signs_positive_zero_negative=dsigns,G_mean_signs_positive_zero_negative=gsigns,case_completion_sha256=seals,analysis_summary=summary,source_freeze_sha256=FREEZE,independent_review_sha256=REVIEW)
    if with_diagnostics:
        result['diagnostics'],result['maximum_raw_r90_frame_error']=diagnostics(rows)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--diagnostics',action='store_true');a=p.parse_args();result=verify_complete(a.diagnostics)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['case_completion_sha256','analysis_summary','diagnostics']},indent=2))
if __name__=='__main__':main()
