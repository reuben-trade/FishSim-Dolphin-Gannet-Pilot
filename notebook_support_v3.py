"""Native-free eight-school report snapshot; earlier evidence remains separate."""
from __future__ import annotations
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import numpy as np
import notebook_support_v2 as earlier

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/research'
LONGER='longer_replication_2026-11-09'
VERSION='2026-11-09_0231'
read=earlier.read
sha=earlier.sha
print_table=earlier.print_table
source_excerpt=earlier.source_excerpt
def actual_parameter_table():
    rows=earlier.actual_parameter_table()
    for row in rows:
        if row['parameter']=='Encounter duration T':row['parameter']='Earlier encounter duration T'
    return rows+[dict(parameter='New-cohort primary horizon T',value=36.),dict(parameter='New-cohort secondary horizon T',value=72.)]

native_environment=earlier.native_environment
new_run_table=earlier.new_run_table
case_rows=earlier.case_rows
paired_rows=earlier.paired_rows
school_means=earlier.school_means
reciprocity_rows=earlier.reciprocity_rows
reciprocity_school_means=earlier.reciprocity_school_means
feeding_rate_summary=earlier.feeding_rate_summary
depth_rows=earlier.depth_rows


def verify_inputs():
    manifest=read(ROOT/f'INPUT_MANIFEST_{VERSION}.json')
    for name,digest in manifest['files'].items():
        path=ROOT/name
        if not path.is_file() or sha(path)!=digest:raise ValueError('Frozen input differs: '+name)
    old=earlier.verify_inputs();inventory=read(ROOT/f'DATASET_{VERSION}.json')
    entries=inventory['cases'];known=set();horizons=0
    for entry in entries:
        folder=ROOT/entry['relative_path']
        if entry['relative_path'] in known:raise ValueError('Duplicate encounter inventory entry')
        known.add(entry['relative_path']);seal=read(folder/'completion.json')
        if seal['status']!='complete' or sha(folder/'completion.json')!=entry['completion_sha256']:
            raise ValueError('Case seal differs: '+entry['case'])
        for name,digest in seal['files'].items():
            if sha(folder/name)!=digest:raise ValueError('Case file differs: '+entry['case']+'/'+name)
        if entry['study']==LONGER:
            for horizon in (36,72):
                sealed_horizon(folder,horizon);horizons+=1
    if len(known)!=48 or horizons!=48:raise ValueError('Require all48encounters and48newhorizons')
    for entry in read(ROOT/'SOURCE_CLOSURE_2026-11-09_0231.json'):
        if sha(ROOT/entry['bundled_path'])!=entry['sha256']:raise ValueError('Longer-study source closure differs')
    verify_new_initial_matching()
    audit=read(DATA/LONGER/'results/analysis_final/analysis_audit.json')
    if audit['status']!='passed' or audit['pending'] or audit['sealed_horizon_records']!=48:
        raise ValueError('Complete eight-school analysis gate has not passed')
    return dict(status='passed',snapshot=VERSION,feeding_encounters=48,earlier_encounters_preserved=old['validated_cases'],
        new_encounters=24,new_sealed_horizons=48,new_independent_schools=8,
        protected_files=len(manifest['files']),supporting_engineering_checks=old['engineering_checks_verified'],
        engineering_pooled=False,native_steps=0)


def sealed_horizon(folder,horizon):
    folder=Path(folder);prefix=f'checkpoint_{horizon:g}T';seal=read(folder/(prefix+'.seal.json'))
    if seal['status']!='complete' or seal['nominal_horizon_T']!=horizon:raise ValueError('Horizon seal differs')
    for name,digest in seal['files'].items():
        if sha(folder/name)!=digest:raise ValueError('Horizon input changed: '+name)
    record=read(folder/(prefix+'.json'))
    if record['status']!='complete' or record['nominal_horizon_T']!=horizon:raise ValueError('Incomplete horizon')
    if record['observed_native_duration_T']>horizon+1e-7:raise ValueError('Later state used for earlier horizon')
    if record['absorbing_no_food_continuation'] and record['final_count']!=0:raise ValueError('Invalid absorbing claim')
    return record


def verify_new_initial_matching():
    base=DATA/LONGER/'results/full_72T_v1/cases'
    for school in range(39064501,39064509):
        folders={p:base/f's{school}_exposed_{p}_c61001' for p in ('D','G','DG')}
        for species in ('D','G'):
            if earlier._projection(read(folders[species]/'initial_engine.json'),species)!=earlier._projection(read(folders['DG']/'initial_engine.json'),species):
                raise ValueError('New cohort species states/private streams differ')
        with np.load(folders['DG']/'initial_school.npz') as a:reference={k:a[k].copy() for k in a.files}
        for presence in ('D','G'):
            with np.load(folders[presence]/'initial_school.npz') as a:
                if set(a.files)!=set(reference) or not all(np.array_equal(a[k],reference[k]) for k in a.files):
                    raise ValueError('New cohort initial fish differ')
    return True


def horizon_rows():
    """Count actual oral captures in each independently sealed event prefix."""
    result=[]
    for entry in read(ROOT/f'DATASET_{VERSION}.json')['cases']:
        if entry['study']!=LONGER:continue
        folder=ROOT/entry['relative_path'];config=read(folder/'config.json')
        for horizon in (36.,72.):
            record=sealed_horizon(folder,horizon)
            with gzip.open(folder/f'checkpoint_{horizon:g}T.events.jsonl.gz','rt') as handle:
                events=[json.loads(line) for line in handle]
            caught=[e for e in events if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
            if len({e['prey_id'] for e in caught})!=len(caught):raise ValueError('Duplicate horizon food')
            for e in events:
                elapsed=e.get('elapsed')
                if elapsed is not None and elapsed>horizon+1e-7:raise ValueError('Event after nominal horizon')
            counts={s:sum(e['actor_id'].startswith(s) for e in caught) for s in 'DG'}
            for s in 'DG':
                if counts[s]!=record['species'][s]['captures']:raise ValueError('Horizon event count differs')
            with np.load(folder/f'checkpoint_{horizon:g}T.school.npz') as state:
                if len(state['prey_ids'])!=record['final_count']:raise ValueError('Horizon survival differs')
            if sum(counts.values())!=record['initial_count']-record['final_count']:raise ValueError('Horizon removal conservation differs')
            result.append(dict(school=config['school_seed'],presence=config['presence'],horizon_T=horizon,
                D_captures=counts['D'],G_captures=counts['G'],D_launches=record['species']['D']['launches'],
                G_launches=record['species']['G']['launches'],D_contacts=record['species']['D']['contacts'],
                G_contacts=record['species']['G']['contacts'],D_rate=record['species']['D']['captures_per_actor_per_nominal_T'],
                G_rate=record['species']['G']['captures_per_actor_per_nominal_T'],live_fish=record['final_count'],
                observed_T=record['observed_native_duration_T'],absorbing=record['absorbing_no_food_continuation']))
    return sorted(result,key=lambda r:(r['horizon_T'],r['school'],r['presence']))


def longer_pairs(rows):
    by={(r['school'],r['presence'],r['horizon_T']):r for r in rows};result=[]
    for horizon in (36.,72.):
        for school in range(39064501,39064509):
            d,g,dg=(by[(school,p,horizon)] for p in ('D','G','DG'))
            dd=dg['D_captures']-d['D_captures'];gd=dg['G_captures']-g['G_captures']
            result.append(dict(school=school,horizon_T=horizon,D_alone=d['D_captures'],D_with_gannets=dg['D_captures'],
                D_difference=dd,G_alone=g['G_captures'],G_with_dolphins=dg['G_captures'],G_difference=gd,joint_positive=dd>0 and gd>0,
                D_rate_difference=dd/(12*horizon),G_rate_difference=gd/(3*horizon)))
    with (DATA/LONGER/'results/analysis_final/paired_horizons.csv').open(newline='') as handle:stored=list(csv.DictReader(handle))
    if len(stored)!=len(result):raise ValueError('Paired table length differs')
    indexed={(int(r['school_seed']),float(r['horizon_T'])):r for r in stored}
    for row in result:
        old=indexed[(row['school'],row['horizon_T'])]
        for key in ('D_alone','D_with_gannets','D_difference','G_alone','G_with_dolphins','G_difference'):
            if row[key]!=int(old[key]):raise ValueError('Stored paired table differs from raw prefixes')
    return result


def primary_statistics(pairs):
    plan=read(DATA/LONGER/'analysis_plan.json');recorded=read(DATA/LONGER/'results/analysis_final/primary_statistics.json')
    primary=sorted([r for r in pairs if r['horizon_T']==36.],key=lambda r:r['school'])
    if len(primary)!=8:raise ValueError('Need eight complete paired school vectors')
    vectors=np.asarray([[r['D_difference'],r['G_difference']] for r in primary],float)
    rng=np.random.default_rng(plan['bootstrap']['seed']);draws=rng.integers(0,8,size=(plan['bootstrap']['draws'],8))
    intervals=np.quantile(vectors[draws].mean(axis=1),plan['bootstrap']['quantiles'],axis=0)
    result=[]
    for index,species in enumerate(('D','G')):
        mean=float(vectors[:,index].mean());bounds=intervals[:,index]
        if mean!=recorded[species]['mean_difference'] or not np.array_equal(bounds,np.asarray(recorded[species]['interval'])):
            raise ValueError('Recomputed fixed-plan primary statistics differ')
        result.append(dict(species=species,independent_schools=8,horizon_T=36.,mean_capture_difference=mean,
            marginal_97_5_lower=float(bounds[0]),marginal_97_5_upper=float(bounds[1]),
            bootstrap_draws=plan['bootstrap']['draws'],analysis_seed=plan['bootstrap']['seed']))
    return result


def secondary_increments(pairs):
    lookup={(r['school'],r['horizon_T']):r for r in pairs}
    return [dict(school=s,interval_T='36–72',D_alone=lookup[(s,72.)]['D_alone']-lookup[(s,36.)]['D_alone'],
        D_mixed=lookup[(s,72.)]['D_with_gannets']-lookup[(s,36.)]['D_with_gannets'],
        G_alone=lookup[(s,72.)]['G_alone']-lookup[(s,36.)]['G_alone'],
        G_mixed=lookup[(s,72.)]['G_with_dolphins']-lookup[(s,36.)]['G_with_dolphins']) for s in range(39064501,39064509)]


def reproduce_figures(output=None):
    output=ROOT/'outputs/eight_school_figures' if output is None else Path(output)
    spec=importlib.util.spec_from_file_location('_eight_school_figures',ROOT/'paper_figure_source_v3.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.DEVELOPMENT=DATA/earlier.DEVELOPMENT;module.REPLICATION=DATA/earlier.REPLICATION;module.DEPTH=DATA/earlier.DEPTH
    module.LONGER=DATA/LONGER;module.RESEARCH=DATA;module.OUT=output
    for function in (module.model_figure,module.development_figure,module.replication_figure,module.mechanism_figure):function()
    return output


def show_figure(name,output=None):
    return earlier.show_figure(name,ROOT/'outputs/eight_school_figures' if output is None else output)


def export_tables(rows,development,replication,joint,depth,new_horizons,new_pairs,stats):
    # Earlier eight tables remain separate and unchanged in meaning.
    earlier.export_tables(rows,development,replication,joint,depth)
    folder=ROOT/'outputs/eight_school_tables';folder.mkdir(parents=True,exist_ok=True)
    tables={'case_horizons':new_horizons,'paired_horizons':new_pairs,'primary_statistics':stats,'secondary_36_72_increments':secondary_increments(new_pairs)}
    for name,values in tables.items():
        with (folder/(name+'.csv')).open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    print('Four new-cohort tables exported; earlier eight tables remain in outputs/current_tables.')
