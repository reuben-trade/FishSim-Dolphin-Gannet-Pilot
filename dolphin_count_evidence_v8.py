"""Native-free complete D24 acceptance; no partial-study or actor pseudoreplication."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
import upper_count_evidence_v7 as previous

ROOT=Path(__file__).resolve().parent
SCIENCE=ROOT/'data/research/dolphin_count_sensitivity_2026-11-09'
RESULTS=SCIENCE/'results'
FULL=RESULTS/'full_36T_v1'
CLOSURE=ROOT/'SOURCE_CLOSURE_2026-11-10_D24.json'
FREEZE='6b404be6af4760c04349c4d48f722fc2b9eff5242d5897ff45df9424d633592b'
REVIEW='5b804d899c7feca29323d22af4a15985b853b103ee5a3976ba699bb3194d1f67'
SELECTION='6b2974e3ddffabf68c98262d2b259b61d74a1f496a3ae0c36dc974bc825fe582'
SEEDS=previous.SEEDS
ENDPOINTS=('D12_partner_rate_change','D24_partner_rate_change','D24_minus_D12_partner_rate_change','D24_minus_D12_mixed_rate','G_with_D12_partner_rate_change','G_with_D24_partner_rate_change')
read,sha,compare_csv=previous.read,previous.sha,previous.compare_csv


def identities():
    return [dict(school_seed=s,herding_minimum_T=1.,gannets=g,dolphins=24,policy=f'D24_H1_G{g}',presence='DG' if g else 'D',capture_seed=61001,dt=.00125,duration_T=36.,case_name=f's{s}_D24_H1_G{g}_{"DG" if g else "D"}_c61001') for s in SEEDS for g in (0,36)]


def readiness():
    paths=[FULL/'status.json',FULL/'physical_review.json',FULL/'analysis_final/analysis_audit.json',RESULTS/'independent_complete_review.json']
    if not all(p.is_file() for p in paths):raise ValueError('All eight cases, full physical/analysis and independent final receipt required')
    status,physical,audit,review=map(read,paths)
    assert status['status']=='complete' and status['complete']==status['planned']==8
    assert physical['status']=='passed' and len(physical['cases'])==8
    assert audit['status']=='passed' and (audit['new_cases'],audit['reused_comparator_cases'],audit['selected_regimes'],audit['independent_schools'])==(8,12,1,4)
    assert sha(paths[3])==REVIEW and review['status']=='passed' and review['stage']=='final'
    assert (review['new_cases'],review['reused_comparator_cases'],review['paired_rows'],review['independent_schools'])==(8,12,4,4)
    for name,path in [('status_sha256',paths[0]),('physical_review_sha256',paths[1]),('analysis_audit_sha256',paths[2])]:assert review[name]==sha(path)
    return status,physical,audit,review


def source_checks(review):
    assert sha(SCIENCE/'frozen_sources.json')==FREEZE and sha(SCIENCE/'selected_regimes.json')==SELECTION
    frozen=read(SCIENCE/'frozen_sources.json');closure=read(CLOSURE)
    assert len(closure)==3597 and {r['original_path']:r['sha256'] for r in closure}==frozen['source_sha256']
    for row in closure:assert sha(ROOT/row['bundled_path'])==row['sha256'],row['bundled_path']
    assert sha(SCIENCE/'INPUT_FREEZE.json')==frozen['input_freeze_sha256']
    assert sha(SCIENCE/'ACTUAL_ZERO_STEP.json')==frozen['actual_zero_step_sha256']
    assert sha(SCIENCE/'PURE_PREFLIGHT.json')==read(SCIENCE/'INPUT_FREEZE.json')['pure_preflight_sha256']
    binding=review['bindings']
    for key,file in [('protocol_sha256','protocol.json'),('input_freeze_sha256','INPUT_FREEZE.json'),('execution_freeze_sha256','frozen_sources.json'),('actual_zero_step_sha256','ACTUAL_ZERO_STEP.json'),('selected_regimes_sha256','selected_regimes.json'),('candidate_selection_sha256','selection_candidate.json'),('independent_selection_review_sha256','INDEPENDENT_SELECTION_REVIEW.json'),('physical_review_source_sha256','review_actual.py')]:assert binding[key]==sha(SCIENCE/file),key
    for p in ['PURE_PREFLIGHT.json','ACTUAL_ZERO_STEP.json','INDEPENDENT_INITIALIZATION_REVIEW.json']:assert read(SCIENCE/p)['status']=='passed'
    return frozen


def check_selection(prior_rows):
    selection=read(SCIENCE/'selected_regimes.json')
    assert selection['status']=='reviewed_complete_map_selection' and selection['frozen_before_D24_outcomes'] is True
    assert selection['D24_native_constructions_before_selection']==selection['D24_native_steps_before_selection']==0
    assert selection['actual_full_cases']==8 and selection['actual_smoke_cases']==2 and selection['unused_budget_not_reassigned'] is True
    lookup={(r['school_seed'],r['herding_minimum_T'],r['gannets'],r['dolphins']):r for r in prior_rows}
    candidates=[]
    for h in previous.HS:
        for g in previous.GS[1:]:
            total=sum(lookup[s,h,g,12]['D_captures'] for s in SEEDS)
            both=sum(lookup[s,h,g,12]['D_captures']>lookup[s,h,0,12]['D_captures'] and lookup[s,h,g,12]['G_captures']>lookup[s,None,g,0]['G_captures'] for s in SEEDS)
            candidates.append((h,g,total,both))
    pick=lambda rs:max(rs,key=lambda r:(r[2],-r[1],-r[0]))
    a=pick(candidates);b=pick([r for r in candidates if r[3]==4]);assert a[:2]==b[:2]==(1.,36)
    assert [(r['herding_minimum_T'],r['gannets']) for r in selection['regimes']]==[(1.,36)]
    assert set(selection['regimes'][0]['selection_labels'])=={'A_maximum_D12_mixed_return','B_joint_positive_in_all_four_schools'}
    return lookup


def new_rows(frozen):
    rows=[]
    for expected in identities():
        row=previous.prior.raw_case(FULL/'cases'/expected['case_name'],expected,frozen,previous.prior.old)
        for name in ['initial_fish','water_entries','D_captures_per_contact','G_captures_per_contact']:row.pop(name)
        row['execution_origin']='new_D24_sensitivity';rows.append(row)
    return rows


def matching(new,old_lookup):
    byname={r['case_name']:r for r in new}
    for s in SEEDS:
        cases={r['gannets']:r for r in identities() if r['school_seed']==s};a=FULL/'cases'/cases[0]['case_name'];b=FULL/'cases'/cases[36]['case_name']
        previous.prior.same_start(a,b,'D')
        old_cases={r['gannets']:r for r in previous.identities() if r['school_seed']==s and r['herding_minimum_T']==1.}
        bird=next(r for r in previous.identities() if r['school_seed']==s and r['gannets']==36 and not r['dolphins'])
        previous.prior.same_start(b,previous.folder(bird),'G')
        for g,path in [(0,a),(36,b)]:
            current,original=read(path/'initial_engine.json'),read(previous.folder(old_cases[g])/'initial_engine.json')
            actors={r['actor_id']:r for r in current['actors']};base={r['actor_id']:r for r in original['actors']}
            ids={f'D{i:02d}' for i in range(12)}
            assert {k:v for k,v in actors.items() if k in ids}=={k:v for k,v in base.items() if k in ids}
            for field in ['actor_policy','capture_rng','controllers']:
                assert {k:v for k,v in current[field].items() if k in ids}=={k:v for k,v in original[field].items() if k in ids}
            assert current['tie_rng']==original['tie_rng']
            for i in range(12,24):
                who=f'D{i:02d}';parent=f'D{i%12:02d}';expected=dict(actors[parent],actor_id=who,ready_at=actors[who]['ready_at'])
                assert actors[who]==expected
                assert current['actor_policy'][who]==current['actor_policy'][parent]
                assert current['controllers'][who]==current['controllers'][parent]
                assert current['capture_rng'][who]!=current['capture_rng'][parent]
    return True


def statistics(new,old_lookup):
    lookup={(r['school_seed'],r['gannets']):r for r in new};pairs=[];numerators=[]
    denominators=np.array([432,864,864,864,1296,1296],float)
    for seed in SEEDS:
        m12,a12,gb=old_lookup[seed,1.,36,12],old_lookup[seed,1.,0,12],old_lookup[seed,None,36,0]
        m24,a24=lookup[seed,36],lookup[seed,0]
        d12=m12['D_captures']-a12['D_captures'];d24=m24['D_captures']-a24['D_captures']
        nums=[d12,d24,d24-2*d12,m24['D_captures']-2*m12['D_captures'],m12['G_captures']-gb['G_captures'],m24['G_captures']-gb['G_captures']]
        numerators.append(nums);values=np.array(nums)/denominators
        pairs.append(dict(school_seed=seed,herding_minimum_T=1.,gannets=36,**dict(zip(ENDPOINTS,map(float,values))),D12_group_captures_mixed=m12['D_captures'],D12_group_captures_alone=a12['D_captures'],D24_group_captures_mixed=m24['D_captures'],D24_group_captures_alone=a24['D_captures'],D12_partner_group_capture_change=d12,D24_partner_group_capture_change=d24))
    integers=np.array(numerators);values=integers/denominators
    plan=read(SCIENCE/'analysis_plan.json')['bootstrap'];assert (plan['draws'],plan['seed'],plan['quantiles'])==(10000,88493024,[.025,.975])
    indices=np.random.default_rng(88493024).integers(0,4,size=(10000,4));bounds=np.quantile(values[indices].mean(axis=1),[.025,.975],axis=0)
    summary=dict(herding_minimum_T=1.,gannets=36,independent_schools=4)
    for i,name in enumerate(ENDPOINTS):
        summary.update({name+'_mean':float(integers[:,i].sum()/(4*denominators[i])),name+'_sample_sd':float(values[:,i].std(ddof=1)),name+'_pointwise95_low':float(bounds[0,i]),name+'_pointwise95_high':float(bounds[1,i]),name+'_positive_schools':int((integers[:,i]>0).sum()),name+'_zero_schools':int((integers[:,i]==0).sum()),name+'_negative_schools':int((integers[:,i]<0).sum())})
    pooled=dict(D12_group_captures_mixed=sum(r['D12_group_captures_mixed'] for r in pairs),D12_group_captures_alone=sum(r['D12_group_captures_alone'] for r in pairs),D24_group_captures_mixed=sum(r['D24_group_captures_mixed'] for r in pairs),D24_group_captures_alone=sum(r['D24_group_captures_alone'] for r in pairs),G_alone_group_captures=sum(old_lookup[s,None,36,0]['G_captures'] for s in SEEDS),G_with_D12_group_captures=sum(old_lookup[s,1.,36,12]['G_captures'] for s in SEEDS),G_with_D24_group_captures=sum(lookup[s,36]['G_captures'] for s in SEEDS))
    return pairs,[summary],pooled


def verify_complete():
    if not __debug__:raise RuntimeError('Audit assertions require unoptimized Python')
    status,physical,audit,review=readiness();frozen=source_checks(review)
    prior=previous.verify_complete();assert prior['outcomes']==140
    old_rows=previous.all_rows();old_lookup=check_selection(old_rows);old_seals={r['case_name']:r['completion_sha256'] for r in old_rows}
    assert review['preserved_prior_case_completion_sha256']==old_seals
    rows=new_rows(frozen);newseals={r['case_name']:r['completion_sha256'] for r in rows}
    assert {p.name for p in (FULL/'cases').iterdir() if p.is_dir()}==set(newseals)
    assert newseals==audit['new_case_completion_sha256']==review['new_case_completion_sha256']=={r['case']:r['completion_sha256'] for r in physical['cases']}
    assert physical['review_source_sha256']==sha(SCIENCE/'review_actual.py')
    expected_refs=[r for r in old_rows if (r['herding_minimum_T']==1. and r['gannets'] in (0,36)) or (not r['dolphins'] and r['gannets']==36)]
    assert len(expected_refs)==12
    reused=[dict(r,execution_origin='reused_D12_map') for r in expected_refs];refseals={r['case_name']:r['completion_sha256'] for r in reused}
    assert refseals==audit['reused_case_completion_sha256']==review['reused_case_completion_sha256']
    assert audit['selected_regimes_sha256']==SELECTION and audit['source_freeze_sha256']==FREEZE
    for key,path in [('complete_D12_csv_sha256',previous.FULL/'analysis_final/case_outcomes.csv'),('complete_D12_analysis_audit_sha256',previous.FULL/'analysis_final/analysis_audit.json'),('complete_D12_independent_review_sha256',previous.RESULTS/'independent_complete_map_review.json')]:assert audit[key]==sha(path)
    for name,digest in audit['files'].items():assert sha(FULL/'analysis_final'/name)==digest,name
    matching(rows,old_lookup)
    for phase,n,steps in [('smoke',2,6400),('pilot',2,57600),('remainder',6,172800)]:
        record=RESULTS/(phase+'_phase_v1');pstatus=read(record/'status.json');execution=read(record/'execution.json');pphysical=read(record/'physical_review.json');approval=read(SCIENCE/(phase.upper()+'_APPROVED.json'));ind=review['phases'][phase]
        for key,path in [('phase_approval_sha256',SCIENCE/(phase.upper()+'_APPROVED.json')),('phase_status_sha256',record/'status.json'),('phase_execution_sha256',record/'execution.json'),('physical_review_sha256',record/'physical_review.json')]:assert ind[key]==sha(path)
        assert pstatus['status']=='complete' and pstatus['complete']==n and pphysical['status']=='passed'
        assert execution['status']=='complete' and execution['total_native_steps']==pstatus['total_native_steps']==ind['native_steps']==steps
        assert execution['maximum_native_steps']==approval['maximum_native_steps']==steps and approval['approved'] is True
        assert execution['frozen_sources_sha256']==FREEZE
        for label in ['dolphin_only_controls','mixed']:
            path=record/(label+'_stage.json');barrier=read(path);assert barrier['status']=='complete' and sha(path)==ind['barrier_sha256'][label]
        assert read(record/'dolphin_only_controls_stage.json')['at']<=read(record/'mixed_stage.json')['at']
        if phase!='smoke':
            assert status['phase_status_sha256'][phase]==sha(record/'status.json') and physical['phase_review_sha256'][phase]==sha(record/'physical_review.json')
        else:
            for smoke in pphysical['cases']:
                name=smoke['case'];folder=RESULTS/'smoke_4T_v1/cases'/name;seal=read(folder/'completion.json')
                for rel,digest in seal['files'].items():assert sha(folder/rel)==digest
                assert read(folder/'summary.json')['native_steps']==3200
                with np.load(folder/'trajectories.npz',allow_pickle=False) as a,np.load(FULL/'cases'/name/'trajectories.npz',allow_pickle=False) as b:
                    assert set(a.files)==set(b.files);frames=len(a['time'])
                    for field in a.files:assert np.array_equal(a[field],b[field] if field in ['actor_ids','prey_ids'] else b[field][:frames]),(name,field)
    pairs,summary,pooled=statistics(rows,old_lookup)
    for file,values,keys in [('case_outcomes.csv',rows,('case_name',)),('reused_case_outcomes.csv',reused,('case_name',)),('paired_school_changes.csv',pairs,('school_seed','herding_minimum_T','gannets')),('regime_summary.csv',summary,('herding_minimum_T','gannets'))]:compare_csv(FULL/'analysis_final'/file,values,keys)
    for k,v in summary[0].items():
        assert np.isclose(v,review['independent_summary'][0][k],rtol=1e-12,atol=1e-14),k
    assert pooled==review['independent_summary'][0]['pooled_group_captures']
    assert review['native_steps_all_phases']==236800 and review['native_steps_new_full']==230400
    assert not any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules)
    return dict(status='passed',new_cases=8,reused_comparators=12,paired_school_rows=4,selected_regimes=1,independent_schools=4,source_bindings=3597,new_full_native_steps=230400,separate_engineering_cases=2,separate_engineering_native_steps=6400,all_smoke_prefixes_exact=True,reader_native_steps=0,fixed_bootstrap_verification_draws_per_run=10000,new_case_completion_sha256=newseals,reused_case_completion_sha256=refseals,pooled_group_captures=pooled,paired_school_changes=pairs,regime_summary=summary,source_freeze_sha256=FREEZE,selection_sha256=SELECTION,independent_review_sha256=REVIEW,reader_source_sha256=sha(Path(__file__)))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args();r=verify_complete()
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ['new_case_completion_sha256','reused_case_completion_sha256','paired_school_changes','regime_summary']},indent=2))
if __name__=='__main__':main()
