"""Current-paper through-36 saved-output analysis; no model or new bootstrap draws."""
from __future__ import annotations
import csv, gzip, hashlib, html, json, math, os, subprocess, sys, time
from collections import Counter, defaultdict
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAVED = ROOT / 'saved_results'
DEP = ROOT / 'departure_evidence'
OUT = ROOT / 'outputs'
STUDY = SAVED / 'data/research/upper_count_regime_extension_2026-11-09/results/full_36T_v1/analysis_final'
SEEDS = (39061001, 39061002, 39063501, 39063502)
HS = (1., 2., 3.)
GS = (1, 3, 6, 9, 12, 18, 24, 36)
STARTED = time.perf_counter()

def read(path): return json.loads(Path(path).read_text())
def table(path):
    with Path(path).open(newline='') as f: return list(csv.DictReader(f))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def mean(xs):
    xs=list(xs)
    return sum(xs)/len(xs)
def truth(x): return x is True or str(x).lower() == 'true'
def same(a, b):
    assert math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-13), (a,b)
def sign(x): return (x>0)-(x<0)
def no_model():
    assert not any(n == 'fish_sim' or n.startswith('fish_sim.') or n == 'cmodel' for n in sys.modules)

def environment():
    return {'Python':sys.version, 'executable':sys.executable,
            'packages':{p:metadata.version(p) for p in ('numpy','matplotlib','IPython','ipykernel','nbclient','nbformat')}}

def verify_inputs():
    no_model()
    records=[]
    for rel, rec in read(SAVED/'provenance.json')['files'].items():
        p=SAVED/rel
        assert p.is_file() and sha(p)==rec['sha256'], str(p)
        records.append({'path':str(p.relative_to(ROOT)),'sha256':rec['sha256']})
    for rec in read(DEP/'provenance.json')['files']:
        p=DEP/rec['bundled_path']
        assert p.is_file() and sha(p)==rec['sha256'], str(p)
        records.append({'path':str(p.relative_to(ROOT)),'sha256':rec['sha256']})
    scientific_count=len(read(SAVED/'provenance.json')['files'])+13
    assert len(records)==scientific_count
    model_docs=ROOT/'model_reproduction'
    for rec in read(model_docs/'provenance.json')['files']:
        p=model_docs/rec['bundled_path']
        expected=rec.get('sha256',rec.get('stored_sha256'))
        assert p.is_file() and sha(p)==expected, str(p)
        if 'source_sha256' in rec:
            assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==rec['source_sha256']
        records.append({'path':str(p.relative_to(ROOT)),'sha256':expected})
    assert len(records)==scientific_count+17  # plus frozen model documentation/receipt files
    return records

def export(name, rows):
    OUT.mkdir(exist_ok=True)
    path=OUT/f'{name}.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return path

def html_table(rows, columns=None, limit=None):
    columns=columns or list(rows[0]); selected=rows if limit is None else rows[:limit]
    return '<table><thead><tr>'+''.join('<th>'+html.escape(str(c))+'</th>' for c in columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(row.get(c,'')))+'</td>' for c in columns)+'</tr>' for row in selected)+'</tbody></table>'

def map_analysis():
    rows=table(STUDY/'case_outcomes.csv');pairs=table(STUDY/'paired_school_changes.csv');summary=table(STUDY/'regime_summary.csv')
    assert len(rows)==140 and len(pairs)==96 and len(summary)==24
    assert {int(r['school_seed']) for r in rows} == set(SEEDS)
    assert sum(truth(r['anchor_replay']) for r in rows)==8
    assert read(STUDY/'analysis_audit.json')['status']=='passed'
    dcontrols={(int(r['school_seed']),float(r['herding_minimum_T'])):r for r in rows if r['presence']=='D'}
    gcontrols={(int(r['school_seed']),int(r['gannets'])):r for r in rows if r['presence']=='G'}
    mixed={(int(r['school_seed']),float(r['herding_minimum_T']),int(r['gannets'])):r for r in rows if r['presence']=='DG'}
    pindex={(int(r['school_seed']),float(r['herding_minimum_T']),int(r['gannets'])):r for r in pairs}
    assert len(dcontrols)==12 and len(gcontrols)==32 and len(mixed)==96
    for r in rows:
        assert float(r['duration_T'])==36 and float(r['dt'])==.00125 and int(r['initial_fish'])==160
        assert int(r['gannets']) in (0,*GS) and int(r['capture_seed'])==61001
        for species,key in [('D','dolphins'),('G','gannets')]:
            n=int(r[key])
            if n: same(r[species+'_rate'],int(r[species+'_captures'])/(n*36))
    best_h=min(HS,key=lambda h:(-mean([int(dcontrols[s,h]['D_captures'])/12/36 for s in SEEDS]),h))
    reconstructed=[]
    for (school,h,g),r in sorted(mixed.items()):
        saved=pindex[school,h,g];dc=dcontrols[school,h];gc=gcontrols[school,g]
        calc={'school_seed':school,'herding_minimum_T':h,'gannets':g}
        for species,control,n in [('D',dc,12),('G',gc,g)]:
            alone=int(control[species+'_captures']);both=int(r[species+'_captures'])
            for key,value in [('rate_alone',alone/n/36),('rate_mixed',both/n/36),('rate_change',(both-alone)/n/36),('capture_change',both-alone)]:
                same(saved[species+'_'+key],value)
            calc[species+'_capture_change']=both-alone
            calc[species+'_change_per_individual']=(both-alone)/n
        best_change=(int(r['D_captures'])-int(dcontrols[school,best_h]['D_captures']))/12/36
        same(saved['D_rate_change_vs_best_tested_Donly'],best_change)
        assert truth(saved['both_rate_changes_positive']) == (calc['D_capture_change']>0 and calc['G_capture_change']>0)
        reconstructed.append(calc)
    archived=read(SAVED/'reports/high_count_2026-11-09/figures/figure_receipts.json')
    archived_map={(float(r['herding_minimum_T']),int(r['gannets'])):r for r in archived['fig3_regime_map']['plotted_data']}
    upper_review=read(SAVED/'data/research/upper_count_regime_extension_2026-11-09/independent_complete_map_review.json')
    assert upper_review['status']=='passed' and upper_review['total_cases']==140
    assert upper_review['analysis_audit_sha256']==sha(STUDY/'analysis_audit.json')
    independent_map={(float(r['H']),int(r['G'])):r for r in upper_review['complete_raw_table']}
    audit_root=SAVED/'data/research/upper_count_regime_extension_2026-11-09'
    binding=read(audit_root/'raw_acceptance_binding.json')
    acceptance=read(audit_root/'raw_acceptance.json')
    assert binding['status']=='passed' and acceptance['status']=='passed'
    assert binding['raw_acceptance_sha256']==sha(audit_root/'raw_acceptance.json')
    assert binding['summary_sha256']==sha(STUDY/'independently_reconstructed_summary.csv')
    assert binding['diagnostics_sha256']==sha(STUDY/'state_contact_diagnostics.csv')
    assert binding['maximum_raw_r90_frame_error']==0 and binding['native_steps']==0
    assert acceptance['D_mean_signs_positive_zero_negative']==[18,2,4]
    assert acceptance['G_mean_signs_positive_zero_negative']==[20,2,2]
    endpoint_check={(float(r['herding_minimum_T']),int(r['gannets'])):r for r in table(STUDY/'independently_reconstructed_summary.csv')}
    diagnostics=table(STUDY/'state_contact_diagnostics.csv')
    assert len(diagnostics)==140 and sum(r['presence']!='G' for r in diagnostics)==108
    outcomes={r['case_name']:r for r in rows}
    for diagnostic in diagnostics:
        raw=outcomes[diagnostic['case_name']]
        for species in ('D','G'):
            for metric in ('captures','contacts','launches'):
                assert int(diagnostic[species+'_'+metric])==int(raw[species+'_'+metric])
    cells=[];opportunities=[]
    for h in HS:
        for g in GS:
            sr=next(r for r in summary if float(r['herding_minimum_T'])==h and int(r['gannets'])==g)
            if g<=18:
                ar=archived_map[h,g]
                # This archived receipt covers only the retained eighteen-setting subset.
                for key,value in sr.items(): same(value,ar[key])
            for key,value in sr.items(): same(value,endpoint_check[h,g][key])
            ir=independent_map[h,g]
            rs=[r for r in reconstructed if r['herding_minimum_T']==h and r['gannets']==g]
            cell={'H_T':h,'gannets':g,'D_alone_per_individual':mean([int(dcontrols[s,h]['D_captures'])/12 for s in SEEDS]),
                  'D_mixed_per_individual':mean([int(mixed[s,h,g]['D_captures'])/12 for s in SEEDS]),
                  'G_alone_per_individual':mean([int(gcontrols[s,g]['G_captures'])/g for s in SEEDS]),
                  'G_mixed_per_individual':mean([int(mixed[s,h,g]['G_captures'])/g for s in SEEDS])}
            for species in ('D','G'):
                values=[r[species+'_change_per_individual'] for r in rs]
                same(mean(values)/36,sr[species+'_mean_rate_change'])
                for name,test in [('positive',lambda x:x>0),('zero',lambda x:x==0),('negative',lambda x:x<0)]:
                    assert sum(test(x) for x in values)==int(sr[species+'_'+name+'_schools'])
                low,high=[float(sr[species+'_pointwise95_'+end])*36 for end in ('low','high')]
                assert math.isfinite(low) and low<=high and math.isfinite(high)
                # Sum integer capture changes before division, so an exact aggregate tie
                # is not classified by floating-point cancellation of per-school ratios.
                norm=12 if species=='D' else g
                exact_mean=sum(r[species+'_capture_change'] for r in rs)/(len(rs)*norm)
                cell.update({species+'_mean_change':exact_mean,species+'_95_low':low,species+'_95_high':high})
            assert sum(int(mixed[s,h,g]['D_captures']) for s in SEEDS)==ir['D_mixed']
            assert sum(int(mixed[s,h,g]['G_captures']) for s in SEEDS)==ir['G_mixed']
            assert [r['D_capture_change'] for r in rs]==ir['D_school_changes']
            assert [r['G_capture_change'] for r in rs]==ir['G_school_changes']
            cell['both_gain_schools']=sum(r['D_capture_change']>0 and r['G_capture_change']>0 for r in rs)
            assert cell['both_gain_schools']==int(sr['both_positive_schools'])
            same(best_h,sr['best_tested_Donly_H'])
            same(mean((int(mixed[s,h,g]['D_captures'])-int(dcontrols[s,best_h]['D_captures']))/12/36 for s in SEEDS),sr['D_mean_rate_change_vs_best_tested_Donly'])
            cells.append(cell)
        for g in (0,*GS):
            cases=[dcontrols[s,h] if g==0 else mixed[s,h,g] for s in SEEDS]
            launches=sum(int(r['D_launches']) for r in cases); contacts=sum(int(r['D_contacts']) for r in cases)
            opportunities.append({'H_T':h,'gannets':g,'pooled_D_launches':launches,'pooled_D_contacts':contacts,
                                  'pooled_contacts_per_launch':contacts/launches,'launches_per_dolphin':launches/48,
                                  'contacts_per_dolphin':contacts/48,'D_captures':sum(int(r['D_captures']) for r in cases),
                                  'G_captures':sum(int(r['G_captures']) for r in cases)})
    assert sum(c['D_mean_change']>0 for c in cells)==18
    assert sum(c['D_mean_change']==0 for c in cells)==2
    assert sum(c['D_mean_change']<0 for c in cells)==4
    assert sum(c['G_mean_change']>0 for c in cells)==20
    assert sum(c['G_mean_change']==0 for c in cells)==2
    selected=next(c for c in cells if c['H_T']==1 and c['gannets']==36)
    for key,value in [('D_mean_change',41/48),('D_95_low',32/48),('D_95_high',50/48),('G_95_low',67/144),('G_95_high',91/144)]:same(selected[key],value)
    assert [r['D_capture_change'] for r in reconstructed if r['herding_minimum_T']==1 and r['gannets']==36]==[13,12,8,8]
    mutual=next(c for c in cells if c['H_T']==2 and c['gannets']==12)
    assert mutual['both_gain_schools']==4
    for h in HS:
        a=[c['G_mixed_per_individual'] for c in cells if c['H_T']==h]
        assert a[0]>a[-1]  # endpoint decline; full eight-count trend is not monotonic
    export('reconstructed_school_effects',reconstructed);export('reconstructed_response_means',cells);export('opportunity_decomposition',opportunities)
    return {'cases':140,'schools':4,'anchor_replays':8,'paired_effects_checked':96,'cells':cells,'opportunities':opportunities,'best_tested_Donly_H':best_h,
            'interval_policy':'All24 pointwise endpoints retained and checked against the hash-bound independent raw-reader reconstruction. Original eighteen-setting endpoints also checked against their archived plot receipt. The upstream acceptance reader verified the frozen10,000-draw procedure; this compact notebook generates zero bootstrap draws.'}

def numerical_check():
    rows=table(SAVED/'data/research/fine_dt_replication_2026-11-09/results/full_36T_v1/analysis_final/paired_effect_grid_differences.csv')
    stats=read(SAVED/'data/research/longer_replication_2026-11-09/results/analysis_final/primary_statistics.json')
    assert len(rows)==8 and len({r['school_seed'] for r in rows})==8
    results=[]
    for species in ('D','G'):
        for grid in ('coarse','fine'):
            effects=[];alone=[];mixed=[]
            for r in rows:
                a=int(r[f'{grid}_{species}_alone']);m=int(r[f'{grid}_{species}_mixed']);effect=m-a
                same(effect,r[f'{grid}_{species}_partner_effect']);effects.append(effect);alone.append(a);mixed.append(m)
            rec={'species':species,'timestep':grid,'alone_total':sum(alone),'mixed_total':sum(mixed),'mean_change_per_school':mean(effects),
                 'positive_schools':sum(v>0 for v in effects),'zero_schools':sum(v==0 for v in effects),'negative_schools':sum(v<0 for v in effects)}
            if grid=='coarse':
                same(mean(effects),stats[species]['mean_difference']);rec['original_marginal_97_5_interval']=stats[species]['interval']
            else:rec['original_marginal_97_5_interval']='not provided for fine check'
            results.append(rec)
        for r in rows:
            a=int(r[f'coarse_{species}_partner_effect']);b=int(r[f'fine_{species}_partner_effect'])
            same(b-a,r[species+'_effect_fine_minus_coarse'])
            assert truth(r[species+'_effect_same_sign']) == (sign(a)==sign(b))
    expected={('D','coarse'):(168,176),('D','fine'):(179,179),('G','coarse'):(35,76),('G','fine'):(49,69)}
    for r in results:assert (r['alone_total'],r['mixed_total'])==expected[r['species'],r['timestep']]
    export('numerical_sensitivity',results)
    return {'schools':8,'rows':results,'scope':'Same eight H2/G3 schools on two grids; not refinement of selected H1/G36 or H2/G12 settings.'}

def departure_check():
    rows=table(DEP/'cessation_summary.csv');full=read(DEP/'cessation_summary.json');windows=table(DEP/'before_after.csv')
    assert len(rows)==48 and len(full['cases'])==48
    byid={r['id']:r for r in rows};losses=[];resumed=[];silent=[]
    for case in full['cases']:
        r=byid[case['id']]
        for key in ('all_birds_final_search','all_birds_final_no_accessible_targets','no_launch_final_6T','final_shallow_but_out_of_reach'):
            assert truth(r[key]) == case[key]
        launches=case['launch_times_T'];assert len(launches)==int(r['gannet_launches'])
        same(launches[-1],r['last_gannet_launch_T'])
        gaps=[(a,b) for a,b in zip(launches,launches[1:]) if b-a>=6-1e-9]
        if gaps:resumed.append(case['id'])
        isloss=case['all_birds_final_search'] and case['all_birds_final_no_accessible_targets']
        if isloss:
            assert case['final_depth_eligible_fish_count']>0 and case['final_shallow_but_out_of_reach']
            assert case['depth_blackout_longest_sampled_T']>0
            losses.append(case['id'])
        if truth(r['no_launch_final_6T']):silent.append(case['id'])
    assert len(resumed)==20 and len(losses)==2 and len(silent)==4
    assert sum(byid[c]['presence']=='DG' for c in losses)==1 and sum(byid[c]['presence']=='G' for c in losses)==1
    complete=[w for w in windows if w['anchor']=='last_gannet_active_end_T' and w['species']=='D' and truth(w['full_windows'])]
    reasons=Counter(w['unavailable_reason'] for w in windows if w['anchor']=='last_gannet_active_end_T' and w['species']=='D' and not truth(w['full_windows']))
    assert len(complete)==1 and reasons=={'gannet_activity_right_censored':24,'insufficient_post_history':11}
    w=complete[0];assert w['case_id']=='s39061001_H1_G6_DG_c61001'
    assert tuple(int(w[k]) for k in ['before_mixed_captures','before_control_captures','after_mixed_captures','after_control_captures'])==(5,4,9,7)
    # Verify final prefix counts, and percentage/rate arithmetic, from existing timecourse exports.
    finals={}
    for r in table(DEP/'benefit_by_time.csv'):
        for species in ('D','G'):
            n=int(r[species+'_predators']);a=int(r[species+'_captures']);b=int(r[species+'_control_captures'])
            same((a-b)/n,r[species+'_capture_advantage_per_predator'])
            if r[species+'_percent_gain']:
                assert b>0;same(100*(a-b)/b,r[species+'_percent_gain'])
            else:assert b==0
        if math.isclose(float(r['time_T']),36,abs_tol=1e-7):finals[r['case_id']]=r
    assert len(finals)==36
    default=finals[w['case_id']]
    assert tuple(int(default[k]) for k in ['D_captures','D_control_captures','G_captures','G_control_captures'])==(27,23,2,7)
    default_record={k:default[k] for k in ['case_id','last_gannet_launch_T','last_gannet_active_end_T','D_captures','D_control_captures','D_percent_gain','G_captures','G_control_captures','G_percent_gain']}
    result={'bird_bearing_runs':48,'mixed_runs':36,'bird_only_runs':12,'schools':4,'whole_flock_loss_ids':losses,'terminal_no_launch_final_6T_ids':silent,
            'resumed_after_6T_gap_count':len(resumed),'resumed_ids':resumed,'full_final_attack_end_windows':1,'unavailable_reasons':dict(reasons),'default':default_record,
            'scope':'Older G1/3/6 subset: 48 bird-bearing encounters. The expanded map has 128 bird-bearing encounters; its higher counts are not included in this departure diagnostic. Depth/travel diagnostics are retained, not new controller decisions or a cessation intervention.'}
    export('terminal_contact_loss',[byid[c] for c in losses]);export('complete_default_before_after_windows',[w]);
    return result

def render_figures():
    OUT.mkdir(exist_ok=True);destination=OUT/'reproduced_figures'
    env=dict(os.environ,FISHSIM_FIGURE_OUTPUT=str(destination),FISHSIM_REPO=str(ROOT/'_unavailable_repository'),MPLCONFIGDIR=str(OUT/'.matplotlib'))
    result=subprocess.run([sys.executable,str(ROOT/'build_figures.py')],cwd=ROOT,env=env,capture_output=True,text=True,check=True)
    (OUT/'figure_build.log').write_text(result.stdout+result.stderr)
    manifest=read(destination/'figure_manifest.json')
    assert manifest['native_steps']==0 and manifest['bootstrap_draws_generated']==0
    assert len(manifest['sources'])==10 and all(s['read_from']=='bundled' for s in manifest['sources'])
    expected=['fig1_model','fig2_returns','fig3_opportunities','fig4_sensitivity']
    assert list(manifest['figures'])==expected
    for name in expected:
        for ext in ('png','pdf'):assert (destination/f'{name}.{ext}').is_file()
    no_model()
    return {'path':str(destination),'figures':expected,'sources':10,'all_sources_bundled':True,'figure1_scope':'Illustrative archived model image reused unchanged.',
            'r90_scope':'Saved per-school time means retained from the independent140-case diagnostic table, whose raw-trajectory frame check had zero maximum r90 error. This compact notebook does not recompute raw trajectories.'}

def finish(inputs, mapped, numerical, departure, figures):
    assert verify_inputs()==inputs;no_model()
    result={'status':'passed','environment':environment(),'input_files_verified':len(inputs),'input_hashes':inputs,
            'map_cases':mapped['cases'],'map_schools':mapped['schools'],'paired_effects_checked':mapped['paired_effects_checked'],
            'numerical_check_schools':numerical['schools'],'departure_runs':departure['bird_bearing_runs'],
            'four_report_figures_prepared':True,'figures_2_to_4_redrawn':True,'figure1_reused':True,'r90_from_archived_time_means':True,
            'scientific_input_files_verified':len(read(SAVED/'provenance.json')['files'])+13,'frozen_model_documentation_files_verified':17,
            'existing_confidence_endpoints_retained':True,'new_bootstrap_draws':0,'native_model_imports':0,'native_simulation_steps':0,
            'seconds_in_kernel':time.perf_counter()-STARTED,'figures':figures,
            'source_sha256':{n:sha(ROOT/n) for n in ['analysis_support.py','build_figures.py']}}
    OUT.mkdir(exist_ok=True);(OUT/'analysis_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'analysis_results.json').write_text(json.dumps({'map':mapped,'numerical':numerical,'departure':departure},indent=2)+'\n')
    return result
