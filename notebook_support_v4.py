"""Final native-free report snapshot with paired-grid numerical sensitivity."""
from __future__ import annotations
import csv,gzip,importlib.util,json
from pathlib import Path
import numpy as np
import notebook_support_v3 as previous

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/research'
FINE='fine_dt_replication_2026-11-09'
COARSE=previous.LONGER
VERSION='2026-11-09_0433'
read=previous.read
sha=previous.sha
print_table=previous.print_table
source_excerpt=previous.source_excerpt
native_environment=previous.native_environment
new_run_table=previous.new_run_table
case_rows=previous.case_rows
paired_rows=previous.paired_rows
school_means=previous.school_means
reciprocity_rows=previous.reciprocity_rows
reciprocity_school_means=previous.reciprocity_school_means
feeding_rate_summary=previous.feeding_rate_summary
depth_rows=previous.depth_rows
horizon_rows=previous.horizon_rows
longer_pairs=previous.longer_pairs
primary_statistics=previous.primary_statistics
secondary_increments=previous.secondary_increments


def actual_parameter_table():
    return previous.actual_parameter_table()+[dict(parameter='Sensitivity timestep T',value=.000625),dict(parameter='Sensitivity duration T',value=36.),dict(parameter='Sensitivity sample interval T',value=.1)]


def verify_inputs():
    manifest=read(ROOT/f'INPUT_MANIFEST_{VERSION}.json')
    for name,digest in manifest['files'].items():
        if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:raise ValueError('Frozen input differs: '+name)
    prior=previous.verify_inputs();inventory=read(ROOT/f'DATASET_{VERSION}.json');known=set();fine_count=0
    for entry in inventory['cases']:
        relative=entry['relative_path']
        if relative in known:raise ValueError('Duplicate encounter inventory')
        known.add(relative)
        if entry['study']!=FINE:continue
        folder=ROOT/relative;seal=read(folder/'completion.json')
        if seal['status']!='complete' or sha(folder/'completion.json')!=entry['completion_sha256']:raise ValueError('Fine case seal differs')
        for name,digest in seal['files'].items():
            if sha(folder/name)!=digest:raise ValueError('Fine case file differs: '+name)
        previous.sealed_horizon(folder,36);fine_count+=1
    if len(known)!=72 or fine_count!=24:raise ValueError('Require all72encounters including24fine cases')
    for entry in read(ROOT/'SOURCE_CLOSURE_2026-11-09_0433.json'):
        if sha(ROOT/entry['bundled_path'])!=entry['sha256']:raise ValueError('Fine source closure differs')
    gate=read(DATA/FINE/'paper_update_validation.json')
    if gate['status']!='passed' or not gate['analysis_ready_for_publisher'] or gate['complete_case_count']!=48:
        raise ValueError('Complete paired-grid audit gate has not passed')
    if len(gate['physical_and_private_stream_review'])!=48 or not all(row['status']=='passed' for row in gate['physical_and_private_stream_review']):raise ValueError('Incomplete physical review')
    physics=read(DATA/FINE/'results/full_36T_v1/analysis_final/school_physics_review.json')
    if physics['status']!='passed' or physics['complete_cases']!=48 or physics['total_fish_surface_reflections']!=0:
        raise ValueError('Full-frame school-physics review failed')
    if sha(DATA/FINE/'review_school_physics.py')!=physics['review_source_sha256']:
        raise ValueError('School-physics review source differs')
    if sha(DATA/FINE/'analyze.py')!=gate['fine_analysis_source_sha256']:
        raise ValueError('Fine analysis source differs')
    verify_cross_grid_initials()
    return dict(status='passed',snapshot=VERSION,feeding_encounters=72,earlier_encounters_preserved=prior['feeding_encounters'],
        new_fine_encounters=24,new_study_horizon_records=72,paired_independent_schools=8,numerical_grids=2,
        protected_inputs=len(manifest['files']),engineering_checks=prior['supporting_engineering_checks'],native_steps=0,
        interpretation='Two-grid sensitivity, not convergence or16 independent schools')


def verify_cross_grid_initials():
    coarse=DATA/COARSE/'results/full_72T_v1/cases';fine=DATA/FINE/'results/full_36T_v1/cases'
    for school in range(39064501,39064509):
        for presence in ('D','G','DG'):
            name=f's{school}_exposed_{presence}_c61001';a=read(coarse/name/'initial_engine.json');b=read(fine/name/'initial_engine.json')
            if a!=b:raise ValueError('Cross-grid initial actor/controller/private RNG states differ')
            with np.load(coarse/name/'initial_school.npz') as x,np.load(fine/name/'initial_school.npz') as y:
                if set(x.files)!=set(y.files) or not all(np.array_equal(x[k],y[k]) for k in x.files):raise ValueError('Cross-grid physical fish state differs')
    return True


def grid_case_rows():
    """Reconstruct both grids from exact36T event prefixes, not72T totals."""
    rows=[]
    for grid,study,path,dt in [('coarse',COARSE,'full_72T_v1',.00125),('fine',FINE,'full_36T_v1',.000625)]:
        base=DATA/study/'results'/path/'cases'
        for school in range(39064501,39064509):
            for presence in ('D','G','DG'):
                folder=base/f's{school}_exposed_{presence}_c61001';record=previous.sealed_horizon(folder,36.)
                config=read(folder/'config.json')
                if config['dt']!=dt:raise ValueError('Grid timestep differs')
                with gzip.open(folder/'checkpoint_36T.events.jsonl.gz','rt') as handle:
                    events=[json.loads(line) for line in handle]
                caught=[e for e in events if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
                if len({e['prey_id'] for e in caught})!=len(caught):raise ValueError('Duplicate grid food')
                for e in events:
                    if e.get('elapsed',0)>36.+1e-7:raise ValueError('Post-horizon event used')
                if len(caught)!=160-record['final_count']:raise ValueError('Grid removal accounting differs')
                for species in ('D','G'):
                    values=record['species'][species]
                    if not values['count']:continue
                    count=sum(e['actor_id'].startswith(species) for e in caught)
                    if count!=values['captures']:raise ValueError('Grid raw events differ from horizon record')
                    structure=record['school_structure']
                    rows.append(dict(grid=grid,dt=dt,school_seed=school,presence=presence,species=species,
                        captures=count,launches=values['launches'],contacts=values['contacts'],
                        captures_per_actor_per_nominal_T=count/(values['count']*36.),
                        observed_effort_T=values['observed_effort_T'],observed_distance=values['observed_distance'],
                        observed_native_duration_T=record['observed_native_duration_T'],native_steps=record['native_steps'],
                        final_live_fish=record['final_count'],school_mean_depth=structure['mean_depth'],school_r90=structure['r90']))
    with (DATA/FINE/'results/full_36T_v1/analysis_final/case_grid_comparison.csv').open(newline='') as handle:stored=list(csv.DictReader(handle))
    indexed={(r['grid'],int(r['school_seed']),r['presence'],r['species']):r for r in stored}
    if len(rows)!=64 or len(indexed)!=64:raise ValueError('Require all64active species/grid rows')
    for row in rows:
        old=indexed[(row['grid'],row['school_seed'],row['presence'],row['species'])]
        for field,value in row.items():
            if isinstance(value,(int,float)):
                if abs(float(old[field])-value)>1e-9:raise ValueError('Stored grid table differs: '+field)
            elif str(value)!=old[field]:raise ValueError('Stored grid label differs')
    return rows


def grid_effect_rows(rows):
    by={(r['grid'],r['school_seed'],r['presence'],r['species']):r['captures'] for r in rows};result=[]
    for school in range(39064501,39064509):
        row={'school_seed':school}
        for grid in ('coarse','fine'):
            d,md,g,mg=(by[(grid,school,p,s)] for p,s in [('D','D'),('DG','D'),('G','G'),('DG','G')])
            row.update({grid+'_D_alone':d,grid+'_D_mixed':md,grid+'_D_partner_effect':md-d,
                grid+'_G_alone':g,grid+'_G_mixed':mg,grid+'_G_partner_effect':mg-g,grid+'_joint_positive':md>d and mg>g})
        for species in ('D','G'):
            a,b=row['coarse_'+species+'_partner_effect'],row['fine_'+species+'_partner_effect']
            row[species+'_effect_fine_minus_coarse']=b-a;row[species+'_effect_same_sign']=bool(np.sign(a)==np.sign(b))
        result.append(row)
    with (DATA/FINE/'results/full_36T_v1/analysis_final/paired_effect_grid_differences.csv').open(newline='') as handle:stored=list(csv.DictReader(handle))
    if len(stored)!=8:raise ValueError('Need8paired grid-effect rows')
    indexed={int(r['school_seed']):r for r in stored}
    for row in result:
        old=indexed[row['school_seed']]
        for field,value in row.items():
            if isinstance(value,bool):
                if str(value)!=old[field]:raise ValueError('Stored grid Boolean differs')
            elif int(old[field])!=value:raise ValueError('Stored grid effect differs')
    return result


def grid_summary(rows):
    result=[]
    for species in ('D','G'):
        a=[r['coarse_'+species+'_partner_effect'] for r in rows];b=[r['fine_'+species+'_partner_effect'] for r in rows]
        changes=np.asarray(b)-a
        result.append(dict(species=species,paired_schools=8,coarse_mean=float(np.mean(a)),fine_mean=float(np.mean(b)),
            same_sign_schools=sum(r[species+'_effect_same_sign'] for r in rows),
            grid_difference_min=int(changes.min()),grid_difference_max=int(changes.max())))
    return result


def reproduce_figures(output=None):
    output=ROOT/'outputs/final_figures' if output is None else Path(output)
    spec=importlib.util.spec_from_file_location('_final_report_figures',ROOT/'paper_figure_source_v4.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.DEVELOPMENT=DATA/previous.earlier.DEVELOPMENT;module.REPLICATION=DATA/previous.earlier.REPLICATION
    module.DEPTH=DATA/previous.earlier.DEPTH;module.LONGER=DATA/COARSE;module.FINE=DATA/FINE;module.RESEARCH=DATA;module.OUT=output
    for function in (module.model_figure,module.development_figure,module.replication_figure,module.mechanism_figure):function()
    return output


def show_figure(name,output=None):return previous.show_figure(name,ROOT/'outputs/final_figures' if output is None else output)


def export_tables(rows,development,replication,joint,depth,new_horizons,new_pairs,stats,grid_cases,grid_effects):
    previous.export_tables(rows,development,replication,joint,depth,new_horizons,new_pairs,stats)
    folder=ROOT/'outputs/final_grid_tables';folder.mkdir(parents=True,exist_ok=True)
    for name,values in [('case_grid_comparison',grid_cases),('paired_effect_grid_differences',grid_effects)]:
        with (folder/(name+'.csv')).open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    print('Two paired-grid tables exported;14tables total, no historical/grid pooling.')
