"""Native-free analysis of independently sealed 36T/72T horizon evidence."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import csv
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from horizons import species_projection
from review_actual import source_matches

HERE=Path(__file__).resolve().parent
SCHOOLS=tuple(range(39064501,39064509))


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def records(path):
    with gzip.open(path,'rt') as handle:return [json.loads(line) for line in handle]
def rng(state):
    result=np.random.default_rng(0);result.bit_generator.state=deepcopy(state);return result
def csv_file(path,rows):
    if not rows:Path(path).write_text('');return
    with Path(path).open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def load_horizon(directory,nominal):
    directory=Path(directory);prefix=f'checkpoint_{nominal:g}T'
    seal_path=directory/(prefix+'.seal.json')
    if not seal_path.exists():return None
    seal=read(seal_path)
    assert seal['status']=='complete' and seal['nominal_horizon_T']==nominal
    for name,digest in seal['files'].items():assert sha(directory/name)==digest,(directory.name,name)
    for path,digest in seal['source_sha256'].items():assert source_matches(path,digest,HERE),path
    match=re.fullmatch(r's(\d+)_exposed_(D|G|DG)_c61001',directory.name);assert match
    school,presence=int(match[1]),match[2];assert school in SCHOOLS
    value=read(directory/(prefix+'.json'));streams=read(directory/(prefix+'.streams.json'))
    events=records(directory/(prefix+'.events.jsonl.gz'))
    initial,final=streams['initial'],streams['final'];elapsed=value['observed_native_duration_T']
    assert value['nominal_horizon_T']==nominal and value['status']=='complete'
    assert value['physical_accounting_audit']['status']=='passed'
    assert value['native_steps']==round(elapsed/.00125)
    assert {a['species'] for a in initial['actors']}==set(presence)
    config=read(directory/'config.json')
    assert config['school_seed']==school and config['capture_seed']==61001 and config['presence']==presence
    preparation=read(config['preparation_manifest_path'])
    checkpoint=preparation['checkpoints'][str(school)]
    assert sha(checkpoint['path'])==checkpoint['sha256']==config['checkpoint_sha256']
    with np.load(checkpoint['path']) as original,np.load(directory/'initial_school.npz') as actual:
        assert np.array_equal(original['positions'],actual['positions'])
        assert np.array_equal(original['prey_ids'],actual['prey_ids'])
        assert np.allclose(original['directions'],actual['directions'],rtol=0,atol=1e-10)
    captures=[e for e in events if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
    removed={e['prey_id'] for e in captures};assert len(removed)==len(captures)
    assert len(removed)==value['initial_count']-value['final_count']
    origin=initial['ownership']['time']
    assert abs(final['ownership']['time']-origin-elapsed)<1e-8
    with np.load(directory/(prefix+'.school.npz')) as state:
        assert set(map(int,state['prey_ids']))==set(initial['ownership']['prey_ids'])-removed
        assert abs(float(state['time'])-origin-elapsed)<1e-8
        assert np.isfinite(state['positions']).all() and np.all(state['positions'][:,2]<=1e-9)
        assert np.max(abs(np.linalg.norm(state['directions'],axis=1)-1),initial=0)<1e-8
    if elapsed<nominal-1e-7:
        assert value['absorbing_no_food_continuation'] and value['final_count']==0 and len(removed)==160
    else:assert abs(elapsed-nominal)<1e-7
    launch_events={(e['actor_id'],e['bout_id']):e for e in events
        if e['kind']=='transition' and e.get('reason')=='launch' and e['actor_id'].startswith('D')}
    cycle_events=[e for e in events if e['kind']=='phase' and e.get('cycle_launch')]
    assert len(cycle_events)==len(launch_events)
    for event in cycle_events:
        launch=launch_events[(event['actor_id'],event['bout_id'])]
        assert event['pressure_elapsed']>=2.-1e-8
        assert abs(event['time']-event['pressure_started']-event['pressure_elapsed'])<1e-7
        assert event['selected_neighbor_count']==event['feasible_min_neighbor_count']
        assert event['target_id']==launch['target_id'] and abs(event['time']-launch['time'])<1e-8
    for who,state in initial['capture_rng'].items():
        generator=rng(state);contacts=caught=0
        for event in events:
            if event['kind']!='oral' or event['actor_id']!=who or event['draw'] is None:continue
            assert generator.random()==event['draw'] and event['closes_bout']
            assert (event['status']=='captured')==(event['draw']<.7)
            contacts+=1;caught+=event['status']=='captured'
        assert generator.bit_generator.state==final['capture_rng'][who]
        row=value['per_actor'][who]
        assert row['contacts']==contacts and row['captures']==caught
        assert abs(sum(row['time'].values())-elapsed)<1e-7
    generator=rng(initial['tie_rng'])
    for event in streams['tie_records']:assert generator.permutation(event['n']).tolist()==event['result']
    assert generator.bit_generator.state==final['tie_rng']
    target_draws=0
    for who in (k for k in initial['controllers'] if k.startswith('G')):
        generator=rng(initial['controllers'][who]['target_rng_state'])
        for event in events:
            if event.get('reason')!='gannet_global_dense_target_selected' or event['actor_id']!=who:continue
            detail=event['targeting_diagnostics'];probability=detail['selection_probabilities']
            if probability:
                weights=np.asarray(detail['eligible_patch_accessible_counts'],float)
                assert np.allclose(weights/weights.sum(),probability,rtol=0,atol=1e-15)
                assert int(generator.choice(len(probability),p=probability))==detail['selected_patch'];target_draws+=1
            else:assert detail['reason']=='fallback_densest_accessible_neighbourhood'
        assert generator.bit_generator.state==final['controllers'][who]['target_rng_state']
    for species in ('D','G'):
        assert value['species'][species]['captures']==sum(e['actor_id'].startswith(species) for e in captures)
    return dict(school=school,presence=presence,nominal=nominal,value=value,initial=initial,
        events=events,captures=captures,origin=origin,seal_sha256=sha(seal_path),directory=directory,
        audit=dict(status='passed',capture_and_tie_replay='passed',gannet_target_draws=target_draws,
            dolphin_cycle_launches=len(cycle_events),source_and_checkpoint_hashes='passed',
            unique_removals='passed',nominal_T=nominal,observed_T=elapsed))


def validate_continuation(primary,secondary):
    assert primary['initial']==secondary['initial']
    assert secondary['events'][:len(primary['events'])]==primary['events'],'36T events differ from72T prefix'
    directory=secondary['directory']
    if (directory/'completion.json').exists():
        seal=read(directory/'completion.json')
        assert seal['files']['trajectories.npz']==sha(directory/'trajectories.npz')
        with np.load(directory/'trajectories.npz') as trajectory,np.load(directory/'checkpoint_36T.school.npz') as state:
            elapsed=primary['value']['observed_native_duration_T']
            index=int(np.argmin(abs(trajectory['time']-elapsed)))
            assert abs(trajectory['time'][index]-elapsed)<1e-8
            alive=trajectory['alive'][index]
            assert np.array_equal(trajectory['positions'][index,alive],state['positions'])
            assert np.array_equal(trajectory['directions'][index,alive],state['directions'])
    return 'exact36T event prefix and retained physical frame passed'


def outcome_rows(cases):
    result=[]
    for case in cases:
        v=case['value'];structure=v['school_structure']
        for species in ('D','G'):
            row=v['species'][species]
            if row['count']==0:continue
            result.append(dict(school_seed=case['school'],presence=case['presence'],species=species,horizon_T=case['nominal'],
                captures=row['captures'],launches=row['launches'],contacts=row['contacts'],
                captures_per_launch=row['captures']/row['launches'] if row['launches'] else None,
                captures_per_contact=row['captures']/row['contacts'] if row['contacts'] else None,
                captures_per_actor_per_nominal_T=row['captures_per_actor_per_nominal_T'],
                observed_native_duration_T=v['observed_native_duration_T'],native_steps=v['native_steps'],
                absorbing_continuation=v['absorbing_no_food_continuation'],live_fish=v['final_count'],
                observed_actor_effort_T=row['observed_effort_T'],observed_distance=row['observed_distance'],
                largest_component_fraction=structure.get('largest_component_fraction'),
                envelope_retention=structure.get('envelope_retention'),mean_depth=structure.get('mean_depth'),
                horizon_seal_sha256=case['seal_sha256']))
    return result


def paired_rows(cases):
    by={(r['school'],r['presence'],r['nominal']):r for r in cases};pairs=[]
    for nominal in sorted({r['nominal'] for r in cases}):
        for school in SCHOOLS:
            if not all((school,p,nominal) in by for p in ('D','G','DG')):continue
            alone,birds,mixed=(by[(school,p,nominal)] for p in ('D','G','DG'))
            assert species_projection(alone['initial'],'D')==species_projection(mixed['initial'],'D')
            assert species_projection(birds['initial'],'G')==species_projection(mixed['initial'],'G')
            d,dg,g,gg=(r['value']['species'][s]['captures'] for r,s in ((alone,'D'),(mixed,'D'),(birds,'G'),(mixed,'G')))
            pairs.append(dict(school_seed=school,horizon_T=nominal,D_alone=d,D_with_gannets=dg,D_difference=dg-d,
                G_alone=g,G_with_dolphins=gg,G_difference=gg-g,joint_positive=dg>d and gg>g,
                D_percent_change=100*(dg-d)/d if d else None,G_percent_change=100*(gg-g)/g if g else None,
                D_live_fish=alone['value']['final_count'],G_live_fish=birds['value']['final_count'],DG_live_fish=mixed['value']['final_count']))
    return pairs


def bootstrap_primary(pairs,plan):
    rows=sorted((r for r in pairs if r['horizon_T']==36.),key=lambda r:r['school_seed'])
    if [r['school_seed'] for r in rows]!=list(SCHOOLS):
        return dict(status='pending',reason='All eight independent36Tschool triplets required',complete_schools=len(rows))
    vector=np.asarray([[r['D_difference'],r['G_difference']] for r in rows],float)
    config=plan['bootstrap'];generator=np.random.default_rng(config['seed'])
    draws=generator.integers(0,len(rows),size=(config['draws'],len(rows)))
    means=vector[draws].mean(axis=1);intervals=np.quantile(means,config['quantiles'],axis=0)
    return dict(status='complete',independent_schools=8,bootstrap_draws=config['draws'],analysis_seed=config['seed'],
        resampling_unit='whole paired school vectors, equal school weights',marginal_interval_coverage=.975,
        familywise_interpretation='approximate95% across two primary species; small-n percentile-bootstrap limits',
        D=dict(mean_difference=float(vector[:,0].mean()),interval=intervals[:,0].tolist()),
        G=dict(mean_difference=float(vector[:,1].mean()),interval=intervals[:,1].tolist()),
        joint_positive=sum(r['joint_positive'] for r in rows))


def comparison_plot(pairs,output):
    horizons=sorted({r['horizon_T'] for r in pairs})
    if not horizons:return False
    fig,axes=plt.subplots(2,len(horizons),figsize=(5*len(horizons),6),squeeze=False)
    for col,nominal in enumerate(horizons):
        rows=[r for r in pairs if r['horizon_T']==nominal]
        for row,species in enumerate(('D','G')):
            ax=axes[row,col];x=[r['school_seed']-39064500 for r in rows];y=[r[species+'_difference'] for r in rows]
            ax.axhline(0,color='#8e9ba4',lw=1)
            ax.scatter(x,y,c='#087f8c' if species=='D' else '#d98525',s=45)
            ax.set(xlim=(.5,8.5),xticks=range(1,9),xlabel='Independent starting school',ylabel='Mixed − alone captures',
                title=f'{"Dolphins" if species=="D" else "Gannets"}: {nominal:g}T ({len(rows)}/8 schools)')
    fig.tight_layout();fig.savefig(output/'paired_differences.png',dpi=180);plt.close(fig);return True


def table(rows,columns):
    if not rows:return '<p>No complete paired schools at this horizon yet.</p>'
    def fmt(v):
        if v is None:return '—'
        if isinstance(v,float):return f'{v:.4g}'
        return str(v)
    return '<table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in columns)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+html.escape(fmt(r[k]))+'</td>' for k in columns)+'</tr>' for r in rows)+'</tbody></table>'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--partial',action='store_true')
    args=parser.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    execution=read(args.input/'execution.json');plan=read(HERE/'analysis_plan.json')
    protocol=read(HERE/'protocol.json');assert sha(HERE/'analysis_plan.json')==protocol['analysis_plan_sha256']
    horizons=[36.,72.] if execution['duration']==72. else [execution['duration']]
    cases=[];pending=[];continuations=[]
    for declaration in execution['cases']:
        directory=args.input/'cases'/f"s{declaration['school_seed']}_exposed_{declaration['presence']}_c61001"
        loaded={}
        for nominal in horizons:
            case=load_horizon(directory,nominal)
            if case is None:pending.append(dict(case=directory.name,horizon_T=nominal))
            else:cases.append(case);loaded[nominal]=case
        if 36. in loaded and 72. in loaded:continuations.append(dict(case=directory.name,status=validate_continuation(loaded[36.],loaded[72.])))
    if pending and not args.partial:raise RuntimeError('Incomplete horizons; use--partial for explicitly labeled progress')
    outcomes=outcome_rows(cases);pairs=paired_rows(cases);primary=bootstrap_primary(pairs,plan)
    csv_file(output/'case_horizons.csv',outcomes);csv_file(output/'paired_horizons.csv',pairs)
    increments=[]
    by={(r['school_seed'],r['horizon_T']):r for r in pairs}
    for school in SCHOOLS:
        if (school,36.) in by and (school,72.) in by:
            a,b=by[(school,36.)],by[(school,72.)]
            increments.append(dict(school_seed=school,**{k:b[k]-a[k] for k in ('D_alone','D_with_gannets','D_difference','G_alone','G_with_dolphins','G_difference')}))
    csv_file(output/'interval_36_to_72.csv',increments);write(output/'primary_statistics.json',primary)
    audit=dict(status='passed',sealed_horizon_records=len(cases),pending=pending,
        physical_prefix_continuation=continuations,case_reviews=[dict(case=c['directory'].name,**c['audit']) for c in cases],
        analysis_plan_sha256=sha(HERE/'analysis_plan.json'),native_steps=0)
    write(output/'analysis_audit.json',audit)
    has_plot=comparison_plot(pairs,output)
    status='Partial: incomplete horizons are listed explicitly.' if pending else 'All prespecified horizons are sealed and validated.'
    body=f'''<!doctype html><meta charset="utf-8"><title>Longer FishSim replication</title>
<style>body{{font:16px system-ui;max-width:1150px;margin:40px auto;padding:0 20px;color:#243544}}table{{border-collapse:collapse;margin:18px 0;font-size:14px}}td,th{{border:1px solid #ccd5dd;padding:7px;text-align:right}}img{{max-width:100%}}code,pre{{white-space:pre-wrap}}</style>
<h1>Fresh eight-school replication: 36T primary, 72T secondary</h1><p>{status}</p>
<p>Fixed exposed-prey dolphin cycle, unchanged gannet policy and contact physics. Each of eight new starting schools has one matched D/G/DG triplet and one stochastic setting. The36T and72T records come from the same continuous trajectory. Historical development and two-school replication results are excluded.</p>
<p>Capture success remains0.7 conditional on an eligible physical oral contact. Units are uncalibrated. Dolphins use2T continuous nearby-prey pressure before a feasible strike; this does not certify school compaction or explicit waiting for a bird dive.</p>
'''
    for nominal in horizons:
        group=[r for r in pairs if r['horizon_T']==nominal]
        body+=f'<h2>{nominal:g}T: {len(group)} complete school triplets</h2>'+table(group,['school_seed','D_alone','D_with_gannets','D_difference','G_alone','G_with_dolphins','G_difference','joint_positive'])
    if has_plot:body+='<img src="paired_differences.png" alt="All observed school-paired effects">'
    body+='<h2>Primary uncertainty</h2><pre>'+html.escape(json.dumps(primary,indent=2))+'</pre>'
    body+='<p>Bootstrap resamples whole school-paired vectors with equal weights.97.5% marginal percentile intervals target approximate95% familywise coverage across the two primary species. With only eight schools, interval coverage and tails are uncertain. Secondary72T and36–72T comparisons are descriptive; horizons are not independent observations.</p>'
    body+='<h2>Finite prey and effort</h2><p>If all160 fish are physically captured, native stepping ends and subsequent capture totals remain exactly fixed. Rates retain the prespecified nominal36T/72T denominator. Native duration, steps and effort remain the actual observed values; no later movement, handling or energy expenditure is invented.</p>'
    body+='<h2>Files</h2><p><a href="case_horizons.csv">Species-level outcomes and effort</a> · <a href="paired_horizons.csv">Paired school outcomes</a> · <a href="interval_36_to_72.csv">36–72T increments</a> · <a href="analysis_audit.json">Evidence audit and pending cases</a> · <a href="primary_statistics.json">Primary statistics</a></p>'
    body+=f'<p>Analysis uses zero native simulation steps. Sealed horizon records:{len(cases)}; pending horizon records:{len(pending)}.</p>'
    (output/'report.html').write_text(body)
    print(json.dumps(dict(status='passed',sealed_horizons=len(cases),pending=len(pending),paired_schools_by_horizon={str(t):sum(r['horizon_T']==t for r in pairs) for t in horizons},report=str(output/'report.html'))))


if __name__=='__main__':main()
