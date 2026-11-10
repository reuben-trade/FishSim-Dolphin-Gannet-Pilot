"""Accept only sealed independently audited validation blocks; never import a model."""
from __future__ import annotations
import csv,hashlib,json,math
from decimal import Decimal
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCHOOLS=tuple(range(39065501,39065517)); LABELS=(71001,71002)
GRIDS={'coarse':.00125,'fine':.000625}; ARMS=('D','G','DG')

def read(path): return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def integer(v):
    require(not isinstance(v,bool),'Boolean is not a count')
    n=Decimal(str(v));require(n.is_finite() and n==n.to_integral_value(),'Noninteger count')
    return int(n)
def boolean(v):
    require(v is True or v is False or v in ('True','False'),'Noncanonical boolean')
    return v is True or v=='True'
def name(s,label,grid,arm,synthetic=False):
    policy=f'H1_G{36 if arm=="DG" else 0}' if arm!='G' else 'Gonly36'
    return ('SYNTHETIC_' if synthetic else '')+f's{s}_{grid}_{policy}_{arm}_c{label}'

def normalise(rows,n,synthetic=False):
    require(n in (4,8,12,16),'Only complete four-school prefixes or final16')
    index={};ids=set()
    for raw in rows:
        s=integer(raw['school_seed']); label=integer(raw['replicate_label']);grid=raw['grid'];arm=raw['presence']
        require(s in SCHOOLS[:n] and label in LABELS and grid in GRIDS and arm in ARMS,'Unexpected school/world/grid/arm; no discovery pooling')
        for alias in ('capture_seed','capture_label'):
            require(alias not in raw or integer(raw[alias])==label,'Conflicting randomness labels')
        require(float(raw['dt'])==GRIDS[grid] and float(raw['duration_T'])==36.,'Wrong encounter grid/duration')
        key=s,label,grid,arm;require(key not in index,'Duplicate design cell')
        who=raw['case_name'];require(who==name(s,label,grid,arm,synthetic) and raw.get('case_id',who)==who and who not in ids,'Case identity mismatch')
        nd=12 if 'D' in arm else 0;ng=36 if 'G' in arm else 0
        require(integer(raw['dolphins'])==nd and integer(raw['gannets'])==ng and integer(raw['initial_fish'])==160,'Wrong predator/prey counts')
        values={k:integer(raw[k]) for k in ('D_captures','G_captures','D_contacts','G_contacts','D_launches','G_launches','remaining_fish','native_steps')}
        require(values['remaining_fish']>=0 and values['D_captures']+values['G_captures']+values['remaining_fish']==160,'Removal accounting mismatch')
        for sp,count in [('D',nd),('G',ng)]:
            a,b,c=[values[sp+'_'+k] for k in ('captures','contacts','launches')]
            require(0<=a<=b<=c and (count or c==0),'Impossible counts/absent species')
        actual=float(raw['actual_duration_T']);absorbed=boolean(raw['native_absorbing_termination']);steps=values['native_steps'];dt=GRIDS[grid]
        require(math.isfinite(actual) and 0<actual<=36.+1e-7 and abs(actual-steps*dt)<=1e-7,'Incoherent actual duration')
        if absorbed:require(values['remaining_fish']==0,'Early termination requires absorbing depletion')
        else:require(abs(actual-36.)<=1e-7 and steps==round(36/dt),'Unfinished encounter cannot enter report')
        digest=str(raw['completion_sha256']);require(len(digest)==64 and all(x in '0123456789abcdef' for x in digest),'Bad completion hash')
        index[key]=dict(raw,**values,school_seed=s,replicate_label=label,dolphins=nd,gannets=ng);ids.add(who)
    expected={(s,l,g,a) for s in SCHOOLS[:n] for l in LABELS for g in GRIDS for a in ARMS}
    require(set(index)==expected,f'Exact {n*12}-case paired prefix required; no missing-cell imputation')
    return [index[k] for k in sorted(index)]

def _sources(pins):
    study=Path(pins['study_root']);bulk=Path(pins['bulk_root'])
    for rel,h in pins['sources'].items():require(sha(study/rel)==h,'Changed scientific source: '+rel)
    require(sha(pins['auditor_path'])==pins['auditor_sha256'],'Changed independent auditor source')
    require(sha(pins['oracle_path'])==pins['oracle_sha256'],'Changed independent statistics source')
    require(sha(bulk/'independent_preparation_outcome_review.json')==pins['preparation_review_sha256'],'Changed preparation provenance')
    freeze=read(study/'frozen_sources.json')
    for file,h in freeze['source_sha256'].items():require(sha(file)==h,'Frozen source/input changed: '+file)
    return study,bulk,freeze

def _binding(receipt,pins):
    require(receipt['status']=='passed' and receipt['freeze_sha256']==pins['sources']['frozen_sources.json'],'Independent review not passed/current')
    require(receipt['audit_source_sha256']==pins['auditor_sha256'],'Unpinned independent auditor')
    require(receipt['native_constructions_by_review']==receipt['native_steps_by_review']==0,'Review performed model work')
    wanted={'input_freeze_sha256':pins['sources']['INPUT_FREEZE.json'],'execution_freeze_sha256':pins['sources']['frozen_sources.json'],'actual_zero_sha256':pins['sources']['ACTUAL_ZERO_STEP.json'],'protocol_sha256':pins['sources']['protocol.json'],'preparation_outcome_review_sha256':pins['preparation_review_sha256']}
    require(receipt['bindings']==wanted,'Review provenance bindings changed')

def _phase(item,study,bulk,pins):
    phase=item['phase'];smoke=phase=='smoke';record=bulk/'phases'/phase
    files={'status_sha256':'status.json','execution_sha256':'execution.json','physical_review_sha256':'physical_review.json'}
    for k,f in files.items():require(sha(record/f)==item[k],'Phase receipt changed: '+phase+'/'+f)
    approval=study/('SMOKE_APPROVED.json' if smoke else 'FEEDING_APPROVED.json')
    require(sha(approval)==item['phase_approval_sha256'],'Phase approval changed')
    status,execution,physical=[read(record/f) for f in ('status.json','execution.json','physical_review.json')]
    expected_count=6 if smoke else 24
    require(status['status']==execution['status']=='complete' and status['planned']==status['complete']==expected_count,'Incomplete phase')
    require(physical['status']=='passed' and physical['status_sha256']==item['status_sha256'],'Unbound phase physical audit')
    require(physical['review_source_sha256']==pins['sources']['review_actual.py'] and physical['wrapper_source_sha256']==pins['sources']['review_phase.py'],'Changed physical audit code')
    require(physical['cases']==item['physical_cases'],'Independent physical cases differ')
    require(execution['freeze_sha256']==pins['sources']['frozen_sources.json'],'Execution source freeze changed')
    require(status['total_native_steps']==execution['total_native_steps']==physical['native_steps']==item['native_steps'],'Phase step mismatch')
    require(item['native_steps']<=item['phase_limit']==execution['maximum_native_steps'],'Phase budget mismatch')
    for wave,binding in item['control_barriers'].items():
        require(sha(record/(wave+'_stage.json'))==binding['barrier_sha256'] and sha(record/(wave+'_dispatch.json'))==binding['dispatch_sha256'],'Control barrier/dispatch changed')
    require(set(item['control_barriers'])=={'D_only_controls','G_only_controls','mixed'},'Missing matched-control wave')
    for row in item['rows']:
        folder=bulk/('smoke_4T_v1' if smoke else 'full_36T_v1')/'cases'/row['case_name']
        require(sha(folder/'completion.json')==row['completion_sha256'],'Case completion changed')
        seal=read(folder/'completion.json');require(seal['status']=='complete','Unsealed case')
        for rel,h in seal['files'].items():
            path=(folder/rel).resolve();require(path.is_relative_to(folder.resolve()) and sha(path)==h,'Sealed case file changed')
    if not smoke:
        desc=read(record/'descriptive.json');require(desc['status']=='complete_prespecified_block_descriptive_only' and desc['decision'] is None,'Phase description claimed inference')
        require(sha(record/'case_outcomes.csv')==desc['table_sha256'],'Descriptive table changed')
        with (record/'case_outcomes.csv').open(newline='') as f:saved=list(csv.DictReader(f))
        serial=lambda r:{k:'' if v is None else str(v) for k,v in r.items()}
        expected={r['case_name']:serial(r) for r in item['rows']}
        require(len(saved)==24 and {r['case_name']:r for r in saved}==expected,'Owner export differs from independently audited rows')
    return item['rows']

def _prefix_proofs(proofs,bulk,rows):
    expected={name(SCHOOLS[0],LABELS[0],g,a) for g in GRIDS for a in ARMS}
    require(len(proofs)==6 and {r['case'] for r in proofs}==expected,'Six exact engineering prefix identities required')
    full={r['case_name']:r['completion_sha256'] for r in rows}
    for proof in proofs:
        require(proof['status']=='passed' and abs(proof['prefix_T']-4.)<1e-7,'Unpassed/incomplete engineering prefix')
        require(proof['full_completion_sha256']==full[proof['case']],'Prefix/full case binding changed')
        small=bulk/'smoke_4T_v1/cases'/proof['case']
        require(sha(small/'completion.json')==proof['smoke_completion_sha256'],'Engineering prefix seal changed')
        seal=read(small/'completion.json');require(seal['status']=='complete','Engineering prefix unsealed')
        for rel,h in seal['files'].items():
            file=(small/rel).resolve();require(file.is_relative_to(small.resolve()) and sha(file)==h,'Engineering prefix input changed')

def accept(stage,through_block=1,pins_path=HERE/'source_pins.json'):
    pins=read(pins_path);bulk=Path(pins['bulk_root'])
    if stage=='prefix':
        require(through_block in (1,2,3),'Prefixes are4/8/12schools; final192 has a separate gate')
        paths=[bulk/f'independent_block{i}_review.json' for i in range(1,through_block+1)]
    elif stage=='final':paths=[bulk/'independent_complete_map_review.json']
    else:raise ValueError('Unknown reporting stage')
    # Check complete receipt chain before touching outcome rows or any live phase.
    require(all(p.is_file() for p in paths),'Await every complete audited paired block; no live partial data accepted')
    study,bulk,freeze=_sources(pins);rows=[];proofs={};statistics=None
    for i,path in enumerate(paths,1):
        receipt=read(path);_binding(receipt,pins);proofs[str(path)]=sha(path)
        if stage=='prefix':
            require(receipt['stage']==f'block{i}' and receipt['completed_full_cases']==48 and receipt['independent_schools']==4,'Noncontiguous block receipt')
            require(set(receipt['phases'])==set(GRIDS),'Both grids required')
            for grid,item in receipt['phases'].items():
                require(item['phase']==f'block{i}_{grid}','Wrong phase/block label')
                rows.extend(_phase(item,study,bulk,pins))
            if i==1:_prefix_proofs(receipt['prefixes'],bulk,rows)
        else:
            require(receipt['stage']=='final' and receipt['new_full_cases']==192 and receipt['independent_schools']==16 and receipt['reused_discovery_cases_in_estimate']==0,'Complete independent192 required')
            phases=receipt['phases'];require(set(phases)=={'smoke',*(f'block{i}_{g}' for i in range(1,5) for g in GRIDS)},'All eight complete feeding phases required')
            for phase,item in phases.items():
                got=_phase(item,study,bulk,pins)
                if phase!='smoke':rows.extend(got)
            out=bulk/'analysis_final';require(sha(out/'analysis_audit.json')==receipt['analysis_audit_sha256'],'Final audit changed')
            audit=read(out/'analysis_audit.json');require(audit['status']=='passed' and audit['full_cases']==192 and audit['independent_schools']==16 and audit['replicate_labels']==2 and audit['primary_grid']=='fine','Wrong final audit scope')
            require(audit['source_freeze_sha256']==pins['sources']['frozen_sources.json'] and audit['protocol_sha256']==pins['sources']['protocol.json'],'Final source binding changed')
            for file,h in audit['files'].items():require(Path(file).name==file and sha(out/file)==h,'Final export changed')
            require(audit['case_completion_sha256']=={r['case_name']:r['completion_sha256'] for r in rows},'Final case seal inventory changed')
            require(audit['phase_review_sha256']=={p:v['physical_review_sha256'] for p,v in phases.items() if p!='smoke'},'Final physical audit inventory changed')
            require(audit['native_steps']==receipt['full_native_steps']==sum(r['native_steps'] for r in rows),'Final step total mismatch')
            statistics=read(out/'statistics.json');require(statistics['status']=='complete_prespecified_analysis' and statistics['case_count']==192 and statistics['primary']['grid']=='fine','Wrong saved final statistics')
            require(receipt['full_native_steps']<=8294400 and receipt['all_new_native_steps']<=8912000,'Study budget exceeded')
            _prefix_proofs(receipt['prefixes'],bulk,rows)
            proofs[str(out/'statistics.json')]=sha(out/'statistics.json')
    n=through_block*4 if stage=='prefix' else 16
    rows=normalise(rows,n)
    require(not any(k=='fish_sim' or k.startswith('fish_sim.') for k in __import__('sys').modules),'No simulator imports')
    return dict(stage=stage,school_count=n,rows=rows,statistics=statistics,synthetic=False,proofs=proofs,source_pins_sha256=sha(pins_path),frozen_source_bindings=len(freeze['source_sha256']))
