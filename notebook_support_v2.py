"""Native-free analysis of the explicitly versioned 9 November report snapshot.

The first-draft module, inventory, input manifest, raw case seals and optional
model runner remain unchanged. This module adds eight sealed G-only/depth cases.
"""
from __future__ import annotations
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import statistics

import numpy as np
import notebook_support as previous

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/research'
DEVELOPMENT=previous.DEVELOPMENT
REPLICATION=previous.REPLICATION
DEPTH='gannet_depth_study_2026-11-08'
SNAPSHOT='2026-11-09'
read=previous.read
sha=previous.sha
print_table=previous.print_table
source_excerpt=previous.source_excerpt
actual_parameter_table=previous.actual_parameter_table
native_environment=previous.native_environment
new_run_table=previous.new_run_table
paired_rows=previous.paired_rows
school_means=previous.school_means


def verify_inputs():
    manifest=read(ROOT/f'INPUT_MANIFEST_{SNAPSHOT}.json')
    for name,digest in manifest['files'].items():
        path=ROOT/name
        if not path.is_file() or sha(path)!=digest:
            raise ValueError(f'Current frozen input changed or is missing: {name}')
    prior=previous.verify_inputs()
    inventory=read(ROOT/f'DATASET_{SNAPSHOT}.json')
    if inventory['older_C_policy_cases_included']:
        raise ValueError('The earlier C-policy experiment is not part of this snapshot')
    seen=set()
    for entry in inventory['cases']:
        key=entry['relative_path']
        if key in seen:raise ValueError(f'Duplicate inventory entry: {key}')
        seen.add(key);folder=ROOT/key;seal=read(folder/'completion.json')
        if seal['status']!='complete' or sha(folder/'completion.json')!=entry['completion_sha256']:
            raise ValueError(f'Case seal differs: {entry["case"]}')
        for name,digest in seal['files'].items():
            if sha(folder/name)!=digest:raise ValueError(f'Case file differs: {entry["case"]}/{name}')
    if len(seen)!=inventory['case_count']:raise ValueError('Inventory case count differs')
    for entry in read(ROOT/'SOURCE_CLOSURE_2026-11-09.json'):
        if sha(ROOT/entry['bundled_path'])!=entry['sha256']:
            raise ValueError('Gannet-study source closure differs')
    verify_matching_starts()
    engineering=verify_engineering_support()
    return dict(status='passed',snapshot=SNAPSHOT,validated_cases=len(seen),
        protected_files=len(manifest['files']),first_draft_manifest_status=prior['status'],
        first_draft_cases_preserved=prior['validated_cases'],exact_start_matching='passed',
        engineering_checks_verified=engineering['cases'],engineering_checks_in_feeding_analysis=False,
        studies=['development:8','fresh replication:8','G-only/depth:8'],native_steps=0)


def verify_engineering_support():
    index=read(ROOT/'supporting_evidence/timing/INDEX.json')
    if index['engineering_case_count']!=3 or index['feeding_case_count']!=0:
        raise ValueError('Timing checks must remain separate from feeding evidence')
    feeding={entry['relative_path'] for entry in read(ROOT/f'DATASET_{SNAPSHOT}.json')['cases']}
    for entry in index['cases']:
        if entry['relative_path'] in feeding or entry['feeding_inventory_included']:
            raise ValueError('Engineering case leaked into the feeding inventory')
        folder=ROOT/entry['relative_path'];seal=read(folder/'completion.json')
        if seal['status']!='complete' or sha(folder/'completion.json')!=entry['completion_sha256']:
            raise ValueError('Engineering case seal differs')
        for name,digest in seal['files'].items():
            if sha(folder/name)!=digest:raise ValueError('Engineering case file differs: '+name)
        if read(folder/'audit.json')['status']!='passed':raise ValueError('Engineering physical audit failed')
    for entry in read(ROOT/'supporting_evidence/timing/SOURCE_CLOSURE.json'):
        if sha(ROOT/entry['bundled_path'])!=entry['sha256']:
            raise ValueError('Timing source closure differs')
    return dict(status='passed',cases=len(index['cases']),included_in_feeding_analysis=False,native_steps=0)


def _projection(receipt,species):
    return dict(actors=[a for a in receipt['actors'] if a['species']==species],
        actor_policy={k:v for k,v in receipt['actor_policy'].items() if k.startswith(species)},
        ownership=receipt['ownership'],capture_rng={k:v for k,v in receipt['capture_rng'].items() if k.startswith(species)},
        tie_rng=receipt['tie_rng'],controllers={k:v for k,v in receipt['controllers'].items() if k.startswith(species)})


def verify_matching_starts():
    base=DATA/DEPTH/'results/full_36T_v1/cases'
    prior=DATA/REPLICATION/'results/full_36T_v1/cases'
    for school in (39063501,39063502):
        for stream in (61001,61002):
            g=base/f's{school}_baseline_G_c{stream}'
            dg=prior/f's{school}_exposed_DG_c{stream}'
            if _projection(read(g/'initial_engine.json'),'G')!=_projection(read(dg/'initial_engine.json'),'G'):
                raise ValueError('G-only and mixed initial states/streams differ')
            with np.load(g/'initial_school.npz') as a,np.load(dg/'initial_school.npz') as b:
                if set(a.files)!=set(b.files) or not all(np.array_equal(a[k],b[k]) for k in a.files):
                    raise ValueError('Unshifted G-only and mixed initial fish differ')
        with np.load(base/f's{school}_baseline_G_c61001/initial_school.npz') as a:
            reference={k:a[k].copy() for k in a.files}
        for treatment,mean in [('depth8',8.),('depth11',11.)]:
            folder=base/f's{school}_{treatment}_G_c61001'
            with np.load(folder/'initial_school.npz') as a:
                if not np.array_equal(a['positions'][:,:2],reference['positions'][:,:2]):
                    raise ValueError('Depth treatment changed horizontal geometry')
                shift=a['positions'][:,2]-reference['positions'][:,2]
                if not np.allclose(shift,shift[0],rtol=0,atol=1e-12) or abs(-a['positions'][:,2].mean()-mean)>1e-10:
                    raise ValueError('Depth treatment is not the declared vertical translation')
                if not all(np.array_equal(a[k],reference[k]) for k in a.files if k!='positions'):
                    raise ValueError('Depth treatment changed headings, IDs or clocks')
    return True


def case_rows():
    rows=[]
    for entry in read(ROOT/f'DATASET_{SNAPSHOT}.json')['cases']:
        folder=ROOT/entry['relative_path'];summary=read(folder/'summary.json');config=read(folder/'config.json')
        if summary['status']!='complete' or read(folder/'audit.json')['status']!='passed':
            raise ValueError(f'Unvalidated case: {entry["case"]}')
        if abs(summary['actual_duration']-36.)>1e-7 or summary['native_steps']!=28800:
            raise ValueError('This report snapshot requires full36T cases')
        with gzip.open(folder/'events.jsonl.gz','rt') as handle:
            captured=[e for e in map(json.loads,handle) if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
        if len({e['prey_id'] for e in captured})!=len(captured):raise ValueError('Duplicate prey capture')
        counts={s:sum(e['actor_id'].startswith(s) for e in captured) for s in 'DG'}
        for s in 'DG':
            if counts[s]!=summary['species'][s]['captures']:raise ValueError('Events differ from summary')
        d,g=(summary['species'][s] for s in 'DG');duration=summary['actual_duration']
        study={DEVELOPMENT:'development',REPLICATION:'replication',DEPTH:'gannet_depth'}[entry['study']]
        rows.append(dict(study=study,school=summary['school_seed'],capture_seed=summary['capture_seed'],
            policy=summary['policy'],presence=config['presence'],dolphin_captures=counts['D'],gannet_captures=counts['G'],
            dolphin_launches=d['launches'],dolphin_contacts=d['contacts'],
            gannet_launches=g['launches'],gannet_contacts=g['contacts'],
            captures_per_launch=d['captures']/d['launches'] if d['launches'] else None,
            captures_per_dolphin_per_T=d['captures']/(d['count']*duration) if d['count'] else None,
            captures_per_gannet_per_T=g['captures']/(g['count']*duration) if g['count'] else None,
            final_live_fish=summary['final_count'],duration_T=duration,folder=str(folder.relative_to(ROOT))))
    return sorted(rows,key=lambda r:(r['study'],r['school'],r['capture_seed'],r['policy'],r['presence']))


def reciprocity_rows(rows):
    lookup={(r['study'],r['school'],r['capture_seed'],r['policy'],r['presence']):r for r in rows}
    results=[]
    for school in (39063501,39063502):
        for stream in (61001,61002):
            d=lookup[('replication',school,stream,'exposed','D')]
            dg=lookup[('replication',school,stream,'exposed','DG')]
            g=lookup[('gannet_depth',school,stream,'baseline','G')]
            dd=dg['dolphin_captures']-d['dolphin_captures'];gd=dg['gannet_captures']-g['gannet_captures']
            results.append(dict(school=school,capture_seed=stream,D=d['dolphin_captures'],DG_D=dg['dolphin_captures'],
                D_difference=dd,G=g['gannet_captures'],DG_G=dg['gannet_captures'],G_difference=gd,
                D_rate_difference=dd/(12*36),G_rate_difference=gd/(3*36),both_gain=dd>0 and gd>0))
    with (DATA/DEPTH/'results/full_36T_v1/analysis_final/reciprocity_pairs.csv').open(newline='') as handle:
        stored=list(csv.DictReader(handle))
    for row,old in zip(results,stored):
        if (row['school'],row['capture_seed'],row['D_difference'],row['G_difference'])!=tuple(int(old[k]) for k in ('school_seed','capture_seed','D_difference','G_difference')):
            raise ValueError('Stored reciprocity table differs from raw reconstructed captures')
    if len(results)!=len(stored):raise ValueError('Reciprocity table length differs')
    return results


def reciprocity_school_means(rows):
    return [dict(school=s,repetitions=len(group),D_mean_difference=statistics.mean(r['D_difference'] for r in group),
        G_mean_difference=statistics.mean(r['G_difference'] for r in group),joint_positive_repetitions=sum(r['both_gain'] for r in group))
        for s in sorted({r['school'] for r in rows}) if (group:=[r for r in rows if r['school']==s])]


def depth_rows(rows):
    result=[]
    for row in rows:
        if row['study']!='gannet_depth' or row['capture_seed']!=61001:continue
        folder=ROOT/row['folder'];metrics=read(folder/'school_metrics.json')
        result.append(dict(school=row['school'],treatment=row['policy'],capture_seed=row['capture_seed'],
            G_captures=row['gannet_captures'],G_launches=row['gannet_launches'],G_contacts=row['gannet_contacts'],
            captures_per_gannet_per_T=row['gannet_captures']/108.,initial_mean_depth=metrics[0]['depth_mean'],
            initial_accessible_fraction=metrics[0]['reference_accessible_fraction'],
            final_accessible_fraction=metrics[-1]['reference_accessible_fraction']))
    return sorted(result,key=lambda r:(r['school'],r['initial_mean_depth']))


def feeding_rate_summary(joint):
    return [dict(species=s,alone_captures=sum(r[a] for r in joint),mixed_captures=sum(r[b] for r in joint),
        alone_per_predator_per_T=sum(r[a] for r in joint)/(len(joint)*n*36),
        mixed_per_predator_per_T=sum(r[b] for r in joint)/(len(joint)*n*36))
        for s,a,b,n in [('Dolphin','D','DG_D',12),('Gannet','G','DG_G',3)]]


def reproduce_figures(output=None):
    output=ROOT/'outputs/current_figures' if output is None else Path(output)
    spec=importlib.util.spec_from_file_location('_current_paper_figures',ROOT/'paper_figure_source_current.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.DEVELOPMENT=DATA/DEVELOPMENT;module.REPLICATION=DATA/REPLICATION;module.DEPTH=DATA/DEPTH
    module.RESEARCH=DATA;module.OUT=output
    for function in (module.model_figure,module.development_figure,module.replication_figure,module.mechanism_figure):function()
    if set(read(output/'figure_receipts.json'))!={'fig1_model','fig2_development','fig3_replication','fig4_mechanism'}:
        raise ValueError('Expected exactly four current paper figures')
    return output


def show_figure(name,output=None):
    return previous.show_figure(name,ROOT/'outputs/current_figures' if output is None else output)


def export_tables(rows,development,replication,joint,depth):
    folder=ROOT/'outputs/current_tables';folder.mkdir(parents=True,exist_ok=True)
    tables={'case_outcomes':rows,'development_pairs':development,'replication_pairs':replication,
        'replication_school_means':school_means(replication),'reciprocity_pairs':joint,
        'reciprocity_school_means':reciprocity_school_means(joint),'depth_outcomes':depth,
        'feeding_rate_summary':feeding_rate_summary(joint)}
    for name,values in tables.items():
        with (folder/(name+'.csv')).open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    print(f'{len(tables)} tables exported to {folder.relative_to(ROOT)}')
