"""Predeclared6T engineering probe; default preparation never runs native work.

Execution needs a later root signal, completed source-bound release settlement,
geometry priority and the shared lease. No full feeding configuration is enabled.
"""
from __future__ import annotations

import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import argparse
from collections import Counter
import copy
from dataclasses import asdict
from datetime import datetime
import fcntl
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time
from zoneinfo import ZoneInfo

import numpy as np

HERE=Path(__file__).resolve().parent
C=HERE.parent
ROOT=HERE.parents[2]
E=Path('/run/media/venture/DJ K4T/FishSim-overnight-evidence-2026-11-08')
LABEL='corrected_v2_engineering_probe_6T_v1'
SCHOOLS=(39061001,39061002)
BRANCHES=('full_pressure_D','half_hunt_D','full_pressure_DG','half_hunt_DG')


class NotReady(Exception):
    """No native work: a prerequisite observation is pending or unverifiable."""


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.now(ZoneInfo('Australia/Perth')).isoformat()
def protocol():return read(HERE/'protocol.json')


def clean(value):
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,np.generic):return clean(value.item())
    return value


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as handle:
        json.dump(clean(value),handle,indent=2,allow_nan=False);handle.write('\n');handle.flush();os.fsync(handle.fileno())
    temporary.replace(path)


def require(condition,message):
    if not condition:raise NotReady(message)


def grid_time(value,maximum,dt=.00125):
    require(isinstance(value,(int,float)) and math.isfinite(value) and value>=0,'Invalid native duration')
    steps=round(value/dt)
    require(abs(value-steps*dt)<1e-7 and steps*dt<=maximum+1e-8,'Duration is not a bounded declared grid count')
    return steps*dt


def time_account(summary,duration,expected_ids):
    require(summary.get('remove_prey') is False,'Release accounting is not nonlethal')
    require(summary['initial_count']==summary['final_count']==160,'Release prey-count conservation missing')
    require(set(summary['per_actor'])==set(expected_ids),'Release actor coverage differs')
    for who,row in summary['per_actor'].items():
        for key in ('time','physical_mode_time'):
            require(all(math.isfinite(v) and v>=-1e-10 for v in row[key].values()),'Nonfinite/negative time accounting')
            require(abs(sum(row[key].values())-duration)<1e-7,'Actor time accounting does not bound native work: '+who)


def verify_seal(directory,required_files=()):
    completion=read(directory/'completion.json')
    require(completion.get('status')=='durably_complete','Branch is not durably sealed')
    require(set(required_files)<=set(completion['files']),'Completion seal omits a consumed required artifact')
    for name,digest in completion['files'].items():
        require((directory/name).is_file() and sha(directory/name)==digest,'Branch seal changed: '+name)
    require(not (directory/'failure.json').exists(),'Branch has a partial/failure receipt')
    return completion


def school_anchor(path):
    with np.load(path,allow_pickle=False) as saved:
        return dict(time=float(saved['time']),step_index=int(saved['step_index']),
            prey_ids=saved['prey_ids'].copy(),positions=saved['positions'].copy(),directions=saved['directions'].copy())


def branch_native_counter_check(initial,final,common):
    require(initial['step_index']==common['step_index'] and abs(initial['time']-common['time'])<1e-8,
        'Branch native starting counter/clock differs from common release')
    for key in ('prey_ids','positions','directions'):
        require(np.array_equal(initial[key],common[key]),'Branch initial native state differs from common release: '+key)
    require(final['step_index']-initial['step_index']==4800 and abs(final['time']-initial['time']-6.)<1e-7,
        'Branch native counter/clock does not prove4800steps/6T')
    require(np.array_equal(initial['prey_ids'],final['prey_ids']),'Nonlethal branch stable IDs differ')


def verify_release(release,expected_sources):
    """Conservative time proof from every establishment and planned branch."""
    release=Path(release)
    require((release/'status.json').is_file(),'Release has not terminated')
    status=read(release/'status.json');status_digest=sha(release/'status.json')
    require(status.get('status')=='complete' and status.get('schools')==2,'Release is pending/partial; no credit')
    manifest=read(release/'manifest.json');retained=read(release/'protocol.json')
    require(retained['school_seeds']==list(SCHOOLS) and retained['branch_duration']==6.,'Release inventory differs')
    require(retained['establishment']['maximum_duration']==12. and retained['remove_prey'] is False,'Release allowance differs')
    for path,digest in expected_sources.items():
        require(manifest['files'].get(path)==digest,'Release is not bound to predeclared reviewed source: '+path)
    preflights=[Path(name) for name in manifest['files'] if Path(name).name=='test_receipt.json' and Path(name).parent.name.startswith('release_preflight_')]
    require(len(preflights)==1,'Release pure preflight identity missing/ambiguous')
    preflight=read(preflights[0]);require(preflight.get('status')=='passed' and preflight.get('native_steps')==0,'Release pure preflight did not pass')
    for path,digest in expected_sources.items():
        require(preflight['source_sha256'].get(path)==digest,'Release preflight/source identity differs')
    external={row['source_path']:row for row in read(release/'external_input_archive.json')['files']}
    for name,digest in manifest['files'].items():
        source=Path(name)
        require(source.is_file() and sha(source)==digest,'Release live frozen binding differs: '+name)
        if source.is_relative_to(ROOT) and source.suffix in ('.py','.md','.json','.cpp','.hpp'):
            archive=release/'sources'/source.relative_to(ROOT)
            require(archive.is_file() and sha(archive)==digest,'Release source snapshot differs')
        elif not source.is_relative_to(ROOT):
            require(name in external,'Release external input closure absent')
            archive=release/external[name]['archive_path']
            require(external[name]['sha256']==digest and archive.is_file() and sha(archive)==digest,'Release external input changed')
    school_dirs={p.name for p in release.glob('school_*') if p.is_dir()}
    require(school_dirs=={f'school_{s}' for s in SCHOOLS},'Extra/missing release school attempts')
    index=read(release/'index.json')['schools']
    require(len(index)==2 and {row['seed'] for row in index}==set(SCHOOLS),'Release index duplicates/misses a school')
    indexed={row['seed']:row for row in index};rows=[];files={}
    for seed in SCHOOLS:
        directory=release/f'school_{seed}'
        require(not list(directory.rglob('failure.json')) and not list(directory.rglob('*.tmp')),'Incomplete release attempt exists')
        require(not any('attempt' in p.name.lower() for p in directory.rglob('*') if p.is_dir()),'Extra release attempt directory')
        establishment=read(directory/'establishment_summary.json');audit=read(directory/'establishment_audit.json')
        require(audit.get('status')=='passed' and not audit.get('errors'),'Establishment audit did not pass')
        elapsed=grid_time(establishment['actual_duration'],12.)
        require(abs(elapsed-establishment['elapsed'])<1e-7,'Establishment clocks disagree')
        time_account(establishment,elapsed,[f'D{i:02d}' for i in range(12)])
        initial_anchor=school_anchor(directory/'establishment_initial_school.npz')
        trace=read(directory/'establishment_trace.json')
        require(trace and abs(trace[0]['time'])<1e-8 and abs(trace[-1]['time']-elapsed)<1e-7,'Establishment trace not complete')
        require(all(b['time']>a['time'] for a,b in zip(trace,trace[1:])),'Establishment time order invalid')
        branch_dirs={p.name for p in (directory/'branches').iterdir() if p.is_dir()} if (directory/'branches').exists() else set()
        if not establishment['established']:
            require(elapsed==12. and not branch_dirs and not indexed[seed]['branches'],'Nonengaged release has unaccounted work')
            require(indexed[seed]['status']=='engaged_containment_not_established','Unexpected nonengagement terminal disposition')
            actual=elapsed
            clock_evidence='Full12T source-bound loop cap plus complete actor-time/trace accounting; no final native counter was logged for a nonengaged establishment'
        else:
            require(branch_dirs==set(BRANCHES),'Extra/missing branch attempts')
            school=read(directory/'school_summary.json')
            require(school['status']=='complete' and school['parent_unchanged_after_all_branches'] is True,'Common-parent fork closure missing')
            common=school['common_release_fingerprint']
            common_anchor=school_anchor(directory/'common_release_school.npz')
            ticks=common_anchor['step_index']-initial_anchor['step_index']
            require(0<=ticks<=9600 and abs(ticks*.00125-elapsed)<1e-7
                and abs(common_anchor['time']-initial_anchor['time']-elapsed)<1e-7,
                'Establishment native counter/clock disagrees with elapsed time')
            require(np.array_equal(initial_anchor['prey_ids'],common_anchor['prey_ids']),'Nonlethal establishment IDs changed')
            clock_evidence='Initial/common native counters, physical clocks and complete actor-time accounting'
            require(len(indexed[seed]['branches'])==4,'Release index lacks four completed branches')
            for branch in BRANCHES:
                path=directory/'branches'/branch
                seal=verify_seal(path,('summary.json','audit.json','trace.json','events.json','initial_school.npz',
                    'final_school.npz','initial_engine.json','final_engine.json','trajectory.npz','intervention.json'))
                summary=read(path/'summary.json');audit=read(path/'audit.json')
                require(seal['branch']==branch and summary['branch']['id']==branch,'Branch identity differs')
                require(summary['status']=='complete' and audit['status']=='passed' and not audit.get('errors'),'Branch accounting is not complete/valid')
                require(grid_time(summary['actual_duration'],6.)==6. and abs(seal['actual_duration']-6.)<1e-7,'Branch is not full6T')
                ids=[f'D{i:02d}' for i in range(12)]+([f'G{i}' for i in range(3)] if branch.endswith('DG') else [])
                time_account(summary,6.,ids)
                require(seal['common_release_fingerprint']==common,'Branch common-state binding differs')
                branch_native_counter_check(school_anchor(path/'initial_school.npz'),school_anchor(path/'final_school.npz'),common_anchor)
                frames=read(path/'trace.json')
                require(len(frames)==121 and abs(frames[0]['time'])<1e-8 and abs(frames[-1]['time']-6.)<1e-7,'Branch trace horizon differs')
                for name,digest in seal['files'].items():files[str(path/name)]=digest
                files[str(path/'completion.json')]=sha(path/'completion.json')
            actual=elapsed+24.
            require(abs(school['actual_model_time']-actual)<1e-7,'School total does not match native work')
        require(abs(indexed[seed]['actual_model_time']-actual)<1e-7,'Index total differs from complete native accounting')
        for path in directory.glob('*'):
            if path.is_file():files[str(path)]=sha(path)
        rows.append(dict(seed=seed,establishment_upper_T=elapsed,full_branches=4 if establishment['established'] else 0,
            actual_upper_T=actual,establishment_clock_evidence=clock_evidence))
    actual=sum(row['actual_upper_T'] for row in rows)
    require(actual<=72. and abs(status['actual_model_time']-actual)<1e-7,'Terminal total disagrees with reconstructed upper bound')
    require(read(release/'status.json')==status and sha(release/'status.json')==status_digest,'Release terminal status changed during observation')
    for name in ('status.json','manifest.json','protocol.json','index.json','external_input_archive.json','execution.json'):
        files[str(release/name)]=sha(release/name)
    return dict(status='source_bound_complete_release_time_verified',actual_upper_T=actual,
        reserved_T=72.,unused_credit_T=72.-actual,schools=rows,files=files,
        manifest_sha256=sha(release/'manifest.json'),terminal_status_sha256=sha(release/'status.json'))


def budget_projection(ledger,proof):
    require(ledger['cap_model_time']==288.,'Hard overnight cap differs')
    require(proof.get('status')=='source_bound_complete_release_time_verified','No verified release-time proof')
    require(not ledger.get('settlements'),'An existing settlement requires separate review; no automatic second credit')
    rows=ledger['reservations'];labels=[row['label'] for row in rows]
    require(len(labels)==len(set(labels)) and LABEL not in labels,'Duplicate/existing probe reservation')
    require(all(math.isfinite(row['reserved_model_time']) and row['reserved_model_time']>=0 for row in rows),'Invalid reservation amount')
    gross=sum(row['reserved_model_time'] for row in rows)
    require(abs(gross-ledger['reserved_model_time'])<1e-8 and gross<=288.+1e-8,'Ledger outstanding total is not conservative/consistent')
    release=[r for r in rows if r['label']=='release_experiment_v1']
    require(len(release)==1 and release[0]['reserved_model_time']==72.,'Original72T release reservation absent/different')
    expected={f's{s}_{c}' for s in SCHOOLS for c in ('adaptive_D','fixed_D','adaptive_DG')}
    full=[r for r in rows if r['label'] in expected]
    require({r['label'] for r in full}==expected and all(r['reserved_model_time']==36. for r in full),'Original216T V1 reservations differ')
    actual=proof['actual_upper_T'];require(0<=actual<=72.,'Verified actual time outside release allowance')
    credit=72.-actual;effective_before=gross-credit;effective_after=effective_before+6.
    require(effective_after<=288.+1e-8,'Less than6T verified headroom; no probe')
    return dict(original_gross_reserved_T=gross,release_actual_upper_T=actual,verified_credit_T=credit,
        effective_before_probe_T=effective_before,probe_reserved_T=6.,effective_after_probe_T=effective_after,
        gross_after_probe_T=gross+6.,hard_cap_T=288.)


def geometry_ready():
    path=E/'geometry_continuation_v1/geometry_completion_status.json'
    require(path.is_file(),'Geometry retains priority; no audited12-case closure yet')
    state=read(path)
    require(state.get('status')=='audited_complete' and state.get('complete_cases')==12,'Geometry retains priority')
    return dict(path=str(path),sha256=sha(path),status=state)


def source_guard(manifest):
    for path,digest in manifest['source_sha256'].items():
        require(Path(path).is_file() and sha(path)==digest,'Probe frozen source/input changed: '+path)
    for name,digest in manifest['artifact_sha256'].items():
        path=Path(manifest['preflight_directory'])/name
        require(path.is_file() and sha(path)==digest,'Probe preflight artifact changed: '+name)


def completed_outcome_chronology(prior,outcomes):
    """Do not confuse an absent status file with an unstarted release."""
    frozen=datetime.fromisoformat(prior['created_at']).timestamp()
    require(bool(outcomes),'Completed-outcome chronology has not been documented')
    for row in outcomes:
        require(frozen<row['modification_epoch'],'Protocol was not fixed before a completed establishment outcome')
    return dict(scope='Before completed establishment outcomes only; not before release start, live progress or V1 results',
        predeclaration_epoch=frozen)


def prepare(output):
    output=Path(output);require(not output.exists(),'Fresh preflight directory required')
    p=protocol();predecl=E/'v2_engineering_probe_protocol_predeclaration_v1'
    prior=read(predecl/'receipt.json')
    require(prior['protocol_sha256']==sha(HERE/'protocol.json')==sha(predecl/'protocol.json'),'Protocol differs from pre-outcome declaration')
    chronology=read(predecl/'chronology_clarification.json')
    completed_outcome_chronology(prior,chronology['completed_establishment_outcomes'])
    require({row['school_seed'] for row in chronology['completed_establishment_outcomes']}==set(SCHOOLS),'Chronology must disclose both completed schools')
    for row in chronology['completed_establishment_outcomes']:
        path=Path(row['path'])
        require(sha(path)==row['sha256'] and abs(path.stat().st_mtime-row['modification_epoch'])<1e-6,
            'Completed-outcome timestamp/source identity differs from chronology clarification')
    future_path=C/'corrected_v2_future_config.json';future=read(future_path)
    require(future['execution']==dict(enabled=False,queued=False,native_steps_performed=0),'Full future feeding config must stay disabled')
    require(sha(future_path)==sha(E/'corrected_controller_v2_implementation_v1/corrected_v2_future_config.json'),
        'Full future construction configuration differs from reviewed frozen V2')
    validation=read(HERE/'pure_preflight_receipt.json')
    require(validation.get('status')=='passed' and validation.get('native_steps')==0,'Pure engineering preflight has not passed')
    for path,digest in validation['source_sha256'].items():require(sha(path)==digest,'Probe source changed after pure preflight')
    bindings=dict(future['source_sha256'])
    for path in [future_path,*HERE.glob('*.py'),HERE/'protocol.json',HERE/'PROBE_PROTOCOL.md',HERE/'pure_preflight_receipt.json',predecl/'receipt.json',predecl/'protocol.json',predecl/'chronology_clarification.json',C/'release_experiment.py',C/'release_protocol.json']:
        require(path.is_file(),'Probe preflight source missing: '+str(path));bindings[str(path)]=sha(path)
    for path,digest in bindings.items():require(sha(path)==digest,'Existing V2 frozen input changed')
    configuration=dict(purpose=p['purpose'],controller_version=future['controller_version'],
        school_seed=39061001,condition='adaptive_DG',capture_seed=61001,dt=.00125,planned_duration=6.,planned_steps=4800,
        reference_geometry='point',capture_probabilities={'D':.7,'G':.7},remove_prey=True,
        adaptive_parameters=future['adaptive_parameters'],original_declaration=future['original_declaration'],
        original_declaration_sha256=bindings[future['original_declaration']],
        native=future['native'],execution_scope='single engineering probe; disabled until separate root signal',
        full_future_feeding_config_path=str(future_path),full_future_feeding_config_sha256=sha(future_path),
        full_future_feeding_config_enabled=False,feeding_outcome_measured=False)
    output.mkdir(parents=True)
    write(output/'actual_construction_configuration.json',configuration);shutil.copy2(HERE/'protocol.json',output/'protocol.json')
    for path,digest in bindings.items():
        source=Path(path);relative=source.relative_to(ROOT) if source.is_relative_to(ROOT) else Path('external_inputs')/digest/source.name
        target=output/'sources'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        require(sha(target)==digest,'Probe source copy failed')
    manifest=dict(status='prepared_not_queued',created_at=stamp(),native_steps=0,preflight_directory=str(output.resolve()),
        protocol_sha256=sha(HERE/'protocol.json'),source_sha256=bindings,
        expected_release_sources={str(C/name):bindings[str(C/name)] for name in ('release_experiment.py','release_protocol.json')},
        artifact_sha256={str(path.relative_to(output)):sha(path) for path in output.rglob('*') if path.is_file()})
    write(output/'preflight_manifest.json',manifest)
    return manifest


def validate_signal(signal_path,preflight):
    require(signal_path is not None and Path(signal_path).is_file(),'No later explicit root launch signal; preparation only')
    signal=read(signal_path);manifest=read(preflight/'preflight_manifest.json')
    require(signal.get('authorize_native_engineering_probe_once') is True,'Launch signal does not authorize the engineering probe')
    require(signal.get('feeding_estimator_allowed') is False,'Launch signal must exclude feeding estimation')
    require(signal.get('preflight_manifest_sha256')==sha(preflight/'preflight_manifest.json'),'Launch signal names a different source freeze')
    require(signal.get('protocol_sha256')==manifest['protocol_sha256'],'Launch signal names a different protocol')
    require(signal.get('probe_label')==LABEL and signal.get('duration')==6. and signal.get('school_seed')==39061001
        and signal.get('condition')=='adaptive_DG','Launch signal scope differs')
    return signal


def prerequisites(preflight):
    """Called again under the shared lock immediately before any settlement."""
    manifest=read(preflight/'preflight_manifest.json');source_guard(manifest)
    construction=read(preflight/'actual_construction_configuration.json')
    future=read(construction['full_future_feeding_config_path'])
    require(future['execution']==dict(enabled=False,queued=False,native_steps_performed=0),'Full future feeding config was enabled')
    geometry=geometry_ready()
    pilot=E/'adaptive_pilot_v1';status=read(pilot/'status.json')
    require(status.get('status')=='simulation_complete' and status.get('completed_new_cases')==6,'Original full V1 matrix is not complete')
    index=read(pilot/'summaryindex.json')['cases']
    expected={(s,c) for s in SCHOOLS for c in ('adaptive_D','fixed_D','adaptive_DG')}
    require(len(index)==6 and {(r['school_seed'],r['condition']) for r in index}==expected,'Original V1 full inventory differs')
    rates=[]
    for row in index:
        directory=pilot/'cases'/f"s{row['school_seed']}_{row['condition']}"
        seal=verify_seal(directory,('summary.json','audit.json','initial_school.npz','final_school.npz',
            'initial_engine.json','final_engine.json','config.json','events.jsonl.gz','trajectories.npz'))
        summary=read(directory/'summary.json')
        require(abs(summary['actual_duration']-36.)<1e-7 and read(directory/'audit.json')['status']=='passed','Original V1 case is not full/accounting-valid')
        rates.append(summary['wall_seconds']/36.)
    require(all(math.isfinite(rate) and rate>0 for rate in rates),'Completed-case benchmark rate is invalid')
    release=verify_release(E/'release_experiment_v1',manifest['expected_release_sources'])
    ledger=read(E/'behavior_budget.json');projection=budget_projection(ledger,release)
    p=read(preflight/'protocol.json');cutoff=datetime.fromisoformat(p['native_cutoff']).timestamp()
    forecast=max(rates)*6.*p['forecast']['safety_multiplier']+p['forecast']['overhead_seconds']
    require(time.time()+forecast<cutoff,'Measured engineering forecast does not fit before05:50')
    require(E.is_dir() and os.path.ismount(E.parent),'Verified external mount absent')
    require(shutil.disk_usage(E).free>=4*2**30+64*2**20,'External free-space floor reached')
    memory={r.split(':')[0]:int(r.split()[1]) for r in Path('/proc/meminfo').read_text().splitlines()}
    require(memory['MemAvailable']*1024>=8*2**30,'Available RAM floor reached')
    return dict(manifest=manifest,construction=construction,geometry=geometry,release=release,
        ledger=ledger,ledger_sha256=sha(E/'behavior_budget.json'),projection=projection,
        forecast_seconds=forecast,cutoff_epoch=cutoff)


def settle_and_reserve(output,ready):
    """Only under overnight_native.lock. Original reservation rows are retained."""
    require(sha(E/'behavior_budget.json')==ready['ledger_sha256'],'Budget changed since locked verification')
    proof=ready['release'];projection=ready['projection']
    write(output/'release_time_settlement_proof.json',proof)
    proof_path=output/'release_time_settlement_proof.json'
    ledger=copy.deepcopy(ready['ledger'])
    ledger['settlements']=[dict(label='release_experiment_v1',original_reserved_model_time=72.,
        verified_actual_upper_model_time=proof['actual_upper_T'],released_verified_model_time=projection['verified_credit_T'],
        proof_path=str(proof_path),proof_sha256=sha(proof_path),at=stamp())]
    ledger['reservations'].append(dict(label=LABEL,reserved_model_time=6.,at=stamp(),pid=os.getpid(),
        purpose='engineering integration only; no feeding estimator',partial_attempt_keeps_full_charge=True))
    ledger['gross_reserved_model_time']=projection['gross_after_probe_T']
    ledger['released_verified_model_time']=projection['verified_credit_T']
    ledger['effective_reserved_model_time']=projection['effective_after_probe_T']
    ledger['reserved_model_time']=projection['effective_after_probe_T']
    ledger['ledger_schema']='verified_release_settlement_v2'
    write(output/'budget_before.json',ready['ledger']);write(E/'behavior_budget.json',ledger)
    write(output/'budget_after_reservation.json',ledger)
    return ledger


class PermutationRecorder:
    """Transparent tie-stream logging: no additional model RNG operation."""
    def __init__(self,rng):self.rng=rng;self.records=[]
    @property
    def bit_generator(self):return self.rng.bit_generator
    def permutation(self,n):
        answer=self.rng.permutation(n);self.records.append(dict(n=int(n),result=answer.tolist()))
        return answer


def replay_streams(initial,final,oral,tie_records):
    for who,state in initial['capture_rng'].items():
        replay=np.random.default_rng(0);replay.bit_generator.state=copy.deepcopy(state)
        for row in oral:
            if row['actor_id']!=who:continue
            if row['draw'] is None:
                require(not row['closes_bout'],'A closed oral contact has no private draw')
                continue
            require(row['closes_bout'] and replay.random()==row['draw'],'Private capture-stream draw mismatch')
            require((row['status']=='captured')==(row['draw']<.7),'Original fixed oral rule differs')
        require(clean(replay.bit_generator.state)==final['capture_rng'][who],'Private capture-stream terminal state differs')
    tie=np.random.default_rng(0);tie.bit_generator.state=copy.deepcopy(initial['tie_rng'])
    for row in tie_records:require(tie.permutation(row['n']).tolist()==row['result'],'Tie permutation replay differs')
    require(clean(tie.bit_generator.state)==final['tie_rng'],'Tie-stream terminal state differs')


def build_probe(construction):
    """Called only after signal, lease, time proof and conservative reservation."""
    sys.path[:0]=[str(C),str(ROOT/'research/herding_study_2026-11-07'),str(ROOT),str(ROOT/'lib')]
    import setup_v2 as setup
    from corrected_v2_setup import install_corrected_planners
    declaration=read(construction['original_declaration']);checkpoint=declaration['checkpoints']['39061001']
    require(sha(checkpoint['path'])==checkpoint['sha256'],'Original checkpoint changed')
    initial=setup._legacy_setup().read_school(checkpoint['path'])
    parameters=setup.ControllerParameters.from_dict(declaration['controller_parameters'])
    original,metadata=setup.build(initial,school_seed=39061001,capture_seed=61001,
        condition='herding_DG',dt=.00125,parameters=parameters)
    engine,metadata=install_corrected_planners(original._engine,metadata,parameters)
    require(sum(a.state.species=='D' for a in engine.actors)==12 and sum(a.state.species=='G' for a in engine.actors)==3,
        'Actual engineering actor inventory differs')
    require(all(asdict(p.adaptive_parameters)==construction['adaptive_parameters'] for p in engine.actor_planners.values()),
        'Actual V2 decision parameters differ from construction freeze')
    metadata.update(engineering_probe=True,planned_duration=6.,planned_steps=4800,
        feeding_outcome_measured=False,reference_geometry='point',capture_probabilities={'D':.7,'G':.7})
    return engine,metadata,setup


def snapshot(engine,setup):
    value=setup._legacy_setup().load_legacy().engine_snapshot(engine)
    value['controllers']=setup.controller_snapshot(engine)
    return clean(value)


def high_failure(metrics,parameters):
    return (metrics['local_radius90']>parameters['radius_exit']
        or metrics['outward_speed90']>parameters['outward_speed_exit']
        or metrics['outward_escape_fraction']>parameters['escape_fraction_exit']
        or metrics['local_reference_retained']<parameters['retention_exit']
        or metrics['lateral_bulk_drift']>parameters['lateral_drift_exit'])


def run_native(output,ready):
    sys.path.insert(0,str(C));import adaptive_runner
    coverage=Counter();mode_time={};oral=[];removed=set();samples=[];checks=Counter();started=time.monotonic()
    deadline=min(ready['cutoff_epoch'],time.time()+900.)
    engine,metadata,setup=build_probe(ready['construction'])
    origin=engine.school.time;initial=snapshot(engine,setup);initial_school=engine.school.state()
    write(output/'actual_initial_engine.json',initial);write(output/'actual_actor_configuration.json',metadata)
    np.savez_compressed(output/'initial_school.npz',**asdict(initial_school))
    tie=PermutationRecorder(engine.tie_rng);engine._engine.tie_rng=tie
    mode_time={a.state.actor_id:Counter() for a in engine.actors}
    configs={a.state.actor_id:a.config for a in engine.actors}
    try:
        with adaptive_runner.logging_context(),gzip.open(output/'events.jsonl.gz','wt') as events:
            for index in range(4801):
                if index%200==0:
                    if time.time()>=deadline:raise TimeoutError('Engineering native wall/deadline budget reached')
                    if shutil.disk_usage(E).free<4*2**30:raise RuntimeError('Engineering external reserve reached')
                    memory={row.split(':')[0]:int(row.split()[1]) for row in Path('/proc/meminfo').read_text().splitlines()}
                    if memory['MemAvailable']*1024<8*2**30:raise RuntimeError('Engineering available RAM floor reached')
                    if sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>64*2**20:raise RuntimeError('Engineering artifact cap reached')
                    write(output/'progress.json',dict(status='running_engineering_probe',native_steps=index,
                        actual_duration=engine.school.time-origin,planned_duration=6.,feeding_outcome_measured=False,
                        wall_seconds=time.monotonic()-started,updated_at=stamp()))
                    samples.append(dict(native_step=index,physical_time=engine.school.time,snapshot=snapshot(engine,setup)))
                if index==4800:break
                before={who:dict(state=actor.state,choice=engine.actor_planners[who].adaptive_state.mode,
                    needs_free=engine.actor_planners[who]._needs_free_reassessment)
                    for actor in engine.actors if (who:=actor.state.actor_id) in engine.actor_planners}
                result=engine.step()
                for step in result.predator_steps:
                    who=step.before.actor_id
                    for piece in step.pieces:
                        dt=piece.body.end-piece.body.start;require(dt>=0,'Negative physical-mode interval')
                        mode_time[who][piece.mode]+=dt
                        if step.before.species=='D':
                            distance=np.linalg.norm(np.asarray(piece.body.after)-piece.body.before)
                            angle=np.arccos(np.clip(np.asarray(piece.heading_before)@piece.heading_after,-1.,1.))
                            require(distance<=configs[who].speed*dt+1e-8 and angle<=configs[who].turn_rate*dt+1e-8,'Dolphin movement capability violated')
                            require(piece.mode=='attack' or piece.bite_window is None,'New nonattack bite capability introduced')
                            checks['dolphin_piece_capability']+=1
                    for transition in step.transitions:
                        events.write(json.dumps(clean(dict(kind='choice_transition' if transition.reason.startswith('adaptive_v2_') else 'physical_transition',actor_id=who,**asdict(transition))),allow_nan=False)+'\n')
                    if who not in before:continue
                    planner=engine.actor_planners[who];diag=planner.last_diagnostics;old=before[who]
                    require(planner._pending is None and planner._adaptive_pending is None and planner._v2_pending_context is None,'Native/committed proposal was not acknowledged')
                    require(planner._committed==step.state,'Committed controller actor differs from resolved native actor')
                    require(diag['adaptive_committed_mode']==planner.adaptive_state.mode,'Committed intent differs from diagnostics')
                    checks['native_committed_acknowledgement']+=1
                    if step.contact_resolved and diag.get('adaptive_mode')=='hunt':
                        require(planner.adaptive_state.mode=='hunt','Hunt intent lost on actual contact');coverage['contact_hunt_intent_carry']+=1
                    busy=old['state'].mode=='attack' or (old['state'].mode=='recovery' and old['state'].time<old['state'].ready_at-1e-12)
                    metrics=diag.get('adaptive_metrics') or {}
                    if not busy and old['needs_free']:
                        require(diag['adaptive_observation_reassessed'],'First free native observation was not reassessed')
                        coverage['fresh_free_reassessment']+=1
                        if metrics.get('valid'):
                            require(abs(metrics['observation_time']-old['state'].time)<1e-8,'First free observation is stale')
                            if old['choice']=='hunt':
                                high=high_failure(metrics,ready['construction']['adaptive_parameters'])
                                require(diag['adaptive_mode']==('contain' if high else 'hunt'),'Native upper-threshold reassessment differs')
                                coverage['high_exit' if high else 'carried_hunt_free_hold']+=1
                        else:
                            require(diag['adaptive_mode']=='contain','Missing free view was treated as containment success');coverage['missing_free_view']+=1
                    for event in diag.get('phase_events',[]):
                        events.write(json.dumps(clean(dict(kind='controller_choice' if event['reason'].startswith('adaptive_v2_') else 'controller_phase',actor_id=who,**event)),allow_nan=False)+'\n')
                        coverage['stable_hunt_entry']+=event.get('after')=='hunt' and event['reason']=='adaptive_v2_observed_stability'
                for outcome in result.contacts:
                    row=dict(kind='oral_accounting',actor_id=outcome.proposal.actor_id,bout_id=outcome.proposal.bout_id,
                        prey_id=outcome.proposal.prey_id,status=outcome.status,draw=outcome.draw,
                        closes_bout=outcome.closes_bout,contact=asdict(outcome.proposal.contact))
                    oral.append(row);events.write(json.dumps(clean(row),allow_nan=False)+'\n')
                    if outcome.status=='captured':
                        require(row['prey_id'] not in removed,'Stable prey ID removed twice');removed.add(row['prey_id'])
                require(engine.school.n>0,'School exhausted; fixed6T engineering horizon cannot be completed')
        final=snapshot(engine,setup);duration=engine.school.time-origin
        require(abs(duration-6.)<1e-7,'Engineering horizon is not exact6T')
        for who,total in mode_time.items():require(abs(sum(total.values())-duration)<1e-7,'Physical-mode time conservation differs: '+who)
        final_school=engine.school.state()
        require(set(map(int,final_school.prey_ids))==set(map(int,initial_school.prey_ids))-removed,'Exact stable-ID removal conservation differs')
        replay_streams(initial,final,oral,tie.records)
        write(output/'final_engine.json',final);np.savez_compressed(output/'final_school.npz',**asdict(final_school))
        with gzip.open(output/'controller_samples.json.gz','wt') as handle:json.dump(clean(samples),handle,allow_nan=False)
        write(output/'tie_stream_calls.json',tie.records)
        write(output/'validation.json',dict(status='passed_bounded_native_integration_checks',native_steps=4800,
            planned_duration=6.,actual_duration=duration,feeding_outcome_measured=False,
            physical_mode_time=mode_time,performed_checks=checks,observed_coverage=coverage,
            unobserved_coverage=[name for name in ('stable_hunt_entry','contact_hunt_intent_carry','fresh_free_reassessment','high_exit','missing_free_view') if not coverage[name]],
            coverage_limit='Absent events are unobserved in the fixed6T window, not failures and never grounds for extension.',
            stream_scope='All actual private draws and tie permutations independently replay to exact final states; oral outcomes only support conservation, not intake estimation.'))
        return dict(status='complete_bounded_engineering_probe',planned_duration=6.,actual_duration=duration,
            native_steps=4800,feeding_outcome_measured=False,wall_seconds=time.monotonic()-started,
            observed_coverage=coverage,native_feeding_comparison=False,numerical_agreement='not_established')
    except BaseException as error:
        write(output/'partial_engine.json',snapshot(engine,setup))
        write(output/'failure.json',dict(status='partial_engineering_probe',error=repr(error),
            actual_duration=engine.school.time-origin,planned_duration=6.,feeding_outcome_measured=False,
            full6T_reservation_retained=True,no_retry_or_extension=True))
        raise


def execute(preflight,output,signal_path):
    """Not invoked by preparation/tests. Caller must explicitly signal later."""
    preflight,output=Path(preflight),Path(output)
    try:
        signal=validate_signal(signal_path,preflight)
        require(not output.exists(),'A fresh single engineering attempt is required')
        with (E/'overnight_native.lock').open('a') as lease:
            try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise NotReady('Shared slot occupied; geometry/release retains priority')
            ready=prerequisites(preflight)  # terminal state is reread AFTER lock.
            output.mkdir(parents=True)
            write(output/'launch_signal.json',signal);write(output/'actual_construction_configuration.json',ready['construction'])
            write(output/'preflight_identity.json',dict(path=str(preflight),manifest_sha256=sha(preflight/'preflight_manifest.json')))
            settle_and_reserve(output,ready)
            try:
                summary=run_native(output,ready);source_guard(ready['manifest'])
                write(output/'status.json',dict(summary,completed_at=stamp()))
                write(output/'completion.json',dict(status='durably_complete_engineering_probe',
                    feeding_outcome_measured=False,planned_duration=6.,native_steps=4800,
                    files={p.name:sha(p) for p in output.iterdir() if p.is_file()}))
                return summary
            except BaseException as error:
                write(output/'status.json',dict(status='partial_engineering_probe',error=repr(error),
                    feeding_outcome_measured=False,planned_duration=6.,full6T_reservation_retained=True))
                return read(output/'status.json')
    except (NotReady,KeyError,ValueError,OSError) as error:
        return dict(status='not_launched_prerequisite_pending_or_unverified',reason=str(error),
            native_steps=0,feeding_outcome_measured=False,observation_failure_is_job_failure=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',type=Path)
    parser.add_argument('--preflight',type=Path);parser.add_argument('--output',type=Path)
    parser.add_argument('--launch-signal',type=Path);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.prepare:
        if args.execute:parser.error('Preparation cannot execute native work')
        result=prepare(args.prepare)
    elif args.execute:
        if args.preflight is None or args.output is None:parser.error('Explicit execution requires preflight and a fresh output')
        result=execute(args.preflight,args.output,args.launch_signal)
    else:
        result=dict(status='preparation_only_not_queued',native_steps=0,
            execution_authorized_now=False,protocol_sha256=sha(HERE/'protocol.json'))
    print(json.dumps(clean({k:v for k,v in result.items() if k not in ('source_sha256','artifact_sha256')}),allow_nan=False))


if __name__=='__main__':main()
