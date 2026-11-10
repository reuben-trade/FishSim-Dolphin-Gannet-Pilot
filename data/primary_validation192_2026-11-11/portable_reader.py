"""Standalone stdlib-only primary192 reader. Source identities are opaque labels.

Only relative content-addressed objects are opened. No model, author workspace,
source executable, bootstrap RNG or native library is imported or invoked.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,io,json,math,sys
from decimal import Decimal
from pathlib import Path

SCHOOLS=tuple(range(39065501,39065517));LABELS=(71001,71002)
GRIDS={'coarse':.00125,'fine':.000625};ARMS=('D','G','DG')
FREEZE='253071467e55b4cdbe91f75ba1de3f1bb80d65344e9cba05aadb86bccb08da0b'
AUDITOR='8ff3eec0139784c175fcdfb1d5397478f91b0f23fa0d2b05501de22cd8d52cdf'
SIDECAR='5cc43e3391ebd48d165fd0b7dd808317ae0a0a4139cdfa0ae032607b905472c3'
SIDECAR_PEER='0d11e7efcb4c954a0384ce85e4ca6a79702ef7e7bc733698f8c50e0f4f5b6d9b'
REQUIREMENT='c26d15c929e80a0f294d08249f53200534cccbd18c7ea0bd6eabcd3440251466'
T_CRITICAL=2.4898797034798923
REPORTER_PINS={'gate.py':'efdf5392cc148ce4b14b7baeea2c5e718b299e64ae7de1b97fb2ae1aa9c55b02','render.py':'4040740e28a93cc2cea9bd2ec716506bf7086ad4fc6c245b3e571c3d822a4e7c','source_pins.json':'51a176741e38852deb60afffad7394d444b22f15b0275e920fe8d303ba4c5776'}
CONTRASTS=('fine_D','fine_G','coarse_D','coarse_G','fine_minus_coarse_D','fine_minus_coarse_G')
POINT_FIELDS={'case_id','school_seed','replicate_label','grid','dt','presence','dolphins','gannets','D_captures','G_captures','duration_T','actual_duration_T','native_steps','native_absorbing_termination','remaining_fish','D_captures_per_individual_36T','D_captures_per_individual_per_T','G_captures_per_individual_36T','G_captures_per_individual_per_T'}

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def integer(v):
    require(not isinstance(v,bool),'Boolean is not an integer')
    n=Decimal(str(v));require(n.is_finite() and n==n.to_integral_value(),'Integer count required');return int(n)
def number(v):
    require(not isinstance(v,bool),'Boolean is not numeric metadata');x=float(v);require(math.isfinite(x),'Finite number required');return x
def flag(v):
    require(type(v) is bool or v in ('True','False'),'Canonical boolean required');return v is True or v=='True'
def close(a,b,tol=1e-13):require(abs(number(a)-number(b))<=tol,'Numeric evidence mismatch')
def identity(s,label,grid,arm,synthetic=False):
    policy='Gonly36' if arm=='G' else ('H1_G36' if arm=='DG' else 'H1_G0')
    return ('SYNTHETIC_' if synthetic else '')+f's{s}_{grid}_{policy}_{arm}_c{label}'

class Snapshot:
    def __init__(self,path,allow_synthetic=False,expected_receipt_sha256=None):
        self.path=Path(path).resolve();self.root=self.path.parent
        receipt_path=self.root/'EXPORT_RECEIPT.json'
        if expected_receipt_sha256:require(sha(receipt_path)==expected_receipt_sha256,'Externally pinned export receipt changed')
        self.receipt=json.loads(receipt_path.read_text());self.manifest=json.loads(self.path.read_text())
        require(self.receipt['manifest_sha256']==sha(self.path),'Snapshot manifest changed')
        require(self.manifest['schema']=='fishsim_primary192_portable_snapshot_v1','Unknown portable schema')
        self.synthetic=self.manifest['kind']=='SYNTHETIC_TEMP_ONLY'
        require(self.manifest['kind'] in ('PRIMARY192_PRODUCTION','SYNTHETIC_TEMP_ONLY'),'Unknown snapshot kind')
        require(not self.synthetic or allow_synthetic,'Synthetic fixtures require explicit opt-in; not study results')
        require(self.manifest['production_accepted'] is (not self.synthetic),'Mislabelled production status')
        require(self.receipt['kind']==self.manifest['kind'],'Receipt kind differs')
        require(sha(Path(__file__))==self.manifest['reader_sha256']==self.receipt['reader_sha256'],'Reader bytes changed')
        for digest,item in self.manifest['objects'].items():
            require(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'Invalid object identity')
            target=(self.root/item['path']).resolve()
            require(target.is_relative_to(self.root) and target.is_file(),'Missing/outside-root object')
            require(target.stat().st_size==item['bytes'] and sha(target)==digest,'Portable object tampered')
        if not self.synthetic:require(self.manifest['reporter_assets']==REPORTER_PINS,'Frozen reporter assets changed')
        for name,digest in self.manifest['reporter_assets'].items():
            require(Path(name).name==name and sha(self.root/'analysis_source/validation_reporting'/name)==digest,'Copied reporter asset changed')
        require(not any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules),'Compiled model prohibited')
    def path_for(self,digest):
        require(digest in self.manifest['objects'],'Unmapped object')
        path=(self.root/self.manifest['objects'][digest]['path']).resolve();require(path.is_relative_to(self.root),'Object resolved outside snapshot');return path
    def json(self,digest):return json.loads(self.path_for(digest).read_text())
    def evidence(self,role):return self.json(self.manifest['evidence'][role])
    def sealed(self,item):
        seal=self.json(item['completion_sha256']);require(seal['status']=='complete','Unsealed case')
        require(item['files']==seal['files'],'Case file map differs from exact seal')
        for name,digest in item['files'].items():
            require(Path(name).name==name and digest in self.manifest['objects'],'Unsafe/missing sealed case member')
        return seal

def validate_evidence(s):
    m=s.manifest;e=m['evidence'];final=s.evidence('independent_final');meta=s.evidence('metadata_sidecar');owner=s.evidence('analysis_audit')
    freeze=s.evidence('source_freeze');expected_freeze=e['source_freeze']
    require(final.get('status')=='passed' and final.get('stage')=='final' and final.get('new_full_cases')==192 and final.get('independent_schools')==16,'Complete independent192 FINAL required')
    require(final.get('reused_discovery_cases_in_estimate')==0,'Discovery pooling prohibited')
    require(final.get('audit_source_sha256')==AUDITOR and final['freeze_sha256']==expected_freeze==final['bindings']['execution_freeze_sha256'],'Wrong original FINAL/source binding')
    require(final.get('native_constructions_by_review')==final.get('native_steps_by_review')==0,'Read-only FINAL required')
    require(final['analysis_audit_sha256']==e['analysis_audit'],'Owner analysis differs from independent FINAL')
    require(owner['status']=='passed' and owner['full_cases']==192 and owner['independent_schools']==16 and owner['replicate_labels']==2 and owner['primary_grid']=='fine','Wrong complete owner analysis')
    require(owner['source_freeze_sha256']==expected_freeze and owner['native_steps_executed_by_analysis']==0,'Wrong owner analysis source')
    for role in ('statistics.json','case_outcomes.csv'):require(owner['files'][role]==m['analysis'][role],'Accepted cached output differs')
    require(meta.get('status')=='passed' and meta.get('stage')=='final_publication_metadata_supplement' and meta.get('schema')=='fishsim_primary_final_metadata_supplement_v1','FINAL metadata supplement required')
    require(meta.get('sidecar_source_sha256')==SIDECAR and meta.get('original_auditor_sha256')==AUDITOR,'Unreviewed sidecar/auditor')
    require(meta['original_final_review_sha256']==e['independent_final'] and meta['analysis_audit_sha256']==e['analysis_audit'] and meta['execution_freeze_sha256']==expected_freeze,'Metadata acceptance chain differs')
    require(meta['statistics_sha256']==m['analysis']['statistics.json'] and meta['case_csv_sha256']==m['analysis']['case_outcomes.csv'],'Metadata pass binds different outputs')
    require(meta['cases']==192 and meta['independent_school_clusters']==16,'Metadata supplement is partial')
    require(meta['original_final_receipt_mandatory'] is True and meta['original_final_receipt_replaced'] is False and meta['scientific_effects_intervals_or_decision_recomputed'] is False and meta['scientific_success_required'] is False,'Metadata supplement changed scientific role')
    require(all(meta[k]==0 for k in ('native_imports','native_constructions','native_steps','native_leases')),'Metadata supplement performed model work')
    require(m['sources']==freeze['source_sha256'],'Exact source/input relocation map differs')
    if not s.synthetic:
        require(expected_freeze==FREEZE and e['publication_requirement']==REQUIREMENT,'Wrong frozen production requirement')
        require(len(m['sources'])==2127,'All2127 original source/input bindings required')
        requirement=s.evidence('publication_requirement')
        require(requirement['required_before_primary192_final_publication'] is True and requirement['all192_cases_required'] is True,'Missing mandatory final gate')
        require(e['sidecar_source']==SIDECAR and e['auditor_source']==AUDITOR,'Source proof bytes differ')
        require(e['sidecar_peer']==requirement['independent_peer']['sha256']==SIDECAR_PEER and requirement['sidecar']['sha256']==SIDECAR,'Independent metadata peer proof differs')
        require(requirement['scientific_execution_freeze_sha256']==expected_freeze and requirement['mandatory_original_final_auditor_sha256']==AUDITOR,'Root publication source requirement differs')
    for original,digest in m['sources'].items():
        require(isinstance(original,str) and digest in m['objects'],'Unmapped original source identity')
    return final,meta,owner

def read_counts(s,owner):
    cases=s.manifest['cases'];synthetic=s.synthetic
    expected={identity(i,l,g,a,synthetic) for i in SCHOOLS for l in LABELS for g in GRIDS for a in ARMS}
    require(len(cases)==192 and set(cases)==expected,'Exact192 sealed cases required; no partial-prefix inference')
    rows=[]
    for school in SCHOOLS:
        for label in LABELS:
            for grid,dt in GRIDS.items():
                for arm in ARMS:
                    name=identity(school,label,grid,arm,synthetic);item=cases[name];s.sealed(item)
                    require(owner['case_completion_sha256'][name]==item['completion_sha256'],'Accepted case seal differs')
                    config=s.json(item['files']['config.json']);summary=s.json(item['files']['summary.json'])
                    nd,ng=(12 if 'D' in arm else 0),(36 if 'G' in arm else 0)
                    values=dict(case_id=name,school_seed=school,replicate_label=label,grid=grid,dt=dt,presence=arm,dolphins=nd,gannets=ng)
                    for key,value in values.items():require(config[key]==value,'Wrong sealed case metadata:'+key)
                    require(config['case_name']==name and config['capture_seed']==config['capture_label']==label,'Wrong actor randomness identity')
                    require(config['duration']==summary['planned_duration']==36 and summary['dt']==dt and summary['initial_count']==160,'Wrong nominal encounter')
                    require(config['counts']==dict(fish=160,D=nd,G=ng),'Wrong source predator/prey counts')
                    source=s.json(item['files']['source_manifest.json']);require(source==s.manifest['sources'],'Case source manifest differs from relocated bytes')
                    with gzip.open(s.path_for(item['files']['events.jsonl.gz']),'rt') as f:events=[json.loads(line) for line in f]
                    oral=[e for e in events if e['kind']=='oral' and e['closes_bout']]
                    removed=[e['prey_id'] for e in oral if e['status']=='captured']
                    require(all(type(x) is int for x in removed) and len(removed)==len(set(removed))==160-summary['final_count'],'Unique raw removals differ')
                    for species,count in [('D',nd),('G',ng)]:
                        contact=[e for e in oral if e['actor_id'].startswith(species)]
                        captures=sum(e['status']=='captured' for e in contact)
                        launches=sum(e['kind']=='transition' and e['reason']=='launch' and e['actor_id'].startswith(species) for e in events)
                        for key,value in [('captures',captures),('contacts',len(contact)),('launches',launches)]:
                            require(integer(summary['species'][species][key])==value,'Raw event/summary count differs')
                            values[species+'_'+key]=value
                        require(0<=captures<=len(contact)<=launches and (count or launches==0),'Absent/impossible species counts')
                    actual=number(summary['actual_duration']);steps=integer(summary['native_steps']);absorbed=flag(summary['native_absorbing_termination']);remaining=integer(summary['final_count'])
                    require(type(summary['native_absorbing_termination']) is bool and 0<actual<=36+1e-7 and steps>0 and steps==round(actual/dt) and abs(actual-steps*dt)<=1e-7,'Incoherent observed clock')
                    require((remaining==0 and len(removed)==160) if absorbed else (abs(actual-36)<=1e-7 and steps==round(36/dt)),'Partial/incoherent depletion')
                    values.update(case_name=name,capture_seed=label,capture_label=label,herding_minimum_T=1. if nd else None,duration_T=36.,actual_duration_T=actual,native_steps=steps,native_absorbing_termination=absorbed,remaining_fish=remaining,initial_fish=160,completion_sha256=item['completion_sha256'])
                    rows.append(values)
    cached=list(csv.DictReader(io.StringIO(s.path_for(s.manifest['analysis']['case_outcomes.csv']).read_text())))
    indexed={r['case_name']:r for r in cached};require(len(cached)==len(indexed)==192 and set(indexed)==expected,'Cached case CSV missing/duplicate')
    for raw in rows:
        saved=indexed[raw['case_name']]
        for key in ('school_seed','replicate_label','capture_seed','capture_label','dolphins','gannets','D_captures','G_captures','D_contacts','G_contacts','D_launches','G_launches','remaining_fish','native_steps','initial_fish'):require(integer(saved[key])==raw[key],'Cached CSV integer differs:'+key)
        for key in ('case_name','case_id','grid','presence','completion_sha256'):require(saved[key]==raw[key],'Cached CSV identity differs')
        for key in ('dt','duration_T'):close(saved[key],raw[key])
        close(saved['actual_duration_T'],raw['actual_duration_T'],1e-7);require(flag(saved['native_absorbing_termination'])==raw['native_absorbing_termination'],'Cached CSV depletion differs')
    return rows

def validate_audit_closure(s,final,owner,rows):
    """Verify copied audit/engineering graph; physical replay stays with8ff."""
    phases=final['phases'];expected={'smoke',*(f'block{i}_{g}' for i in range(1,5) for g in GRIDS)}
    require(set(phases)==expected and set(s.manifest['phase_evidence'])==expected,'All nine audited phases required')
    accepted=[];full_steps=0
    for phase,proof in phases.items():
        mapped=s.manifest['phase_evidence'][phase]
        for key,name in [('status_sha256','status.json'),('execution_sha256','execution.json'),('physical_review_sha256','physical_review.json')]:
            require(mapped[name]==proof[key] and proof[key] in s.manifest['objects'],'Phase proof object missing/changed')
        status=s.json(mapped['status.json']);execution=s.json(mapped['execution.json']);physical=s.json(mapped['physical_review.json'])
        count=6 if phase=='smoke' else 24
        require(status['status']==execution['status']=='complete' and status['complete']==status['planned']==count,'Incomplete portable phase')
        require(physical['status']=='passed' and physical['status_sha256']==mapped['status.json'],'Unbound portable physical review')
        require(execution['freeze_sha256']==s.manifest['evidence']['source_freeze'] and execution['workers']==8,'Phase source/workers differ')
        require(status['total_native_steps']==execution['total_native_steps']==physical['native_steps']==proof['native_steps'],'Phase step totals differ')
        require(proof['native_steps']<=proof['phase_limit']==execution['maximum_native_steps'],'Phase budget differs')
        require(set(proof['control_barriers'])=={'D_only_controls','G_only_controls','mixed'},'Missing source control wave')
        for wave,binding in proof['control_barriers'].items():
            for key,suffix in [('barrier_sha256','_stage.json'),('dispatch_sha256','_dispatch.json')]:require(mapped[wave+suffix]==binding[key] and binding[key] in s.manifest['objects'],'Missing portable control barrier')
        require(mapped['phase_approval']==proof['phase_approval_sha256'] and mapped['phase_approval'] in s.manifest['objects'],'Unbound portable phase approval')
        if phase!='smoke':
            accepted.extend(proof['rows']);full_steps+=proof['native_steps']
            require(owner['phase_review_sha256'][phase]==mapped['physical_review.json'],'Owner phase audit differs')
    require(full_steps==final['full_native_steps']==owner['native_steps']<=8294400,'Wrong192 native step total')
    require(final['all_new_native_steps']<=8912000,'Original total step ceiling exceeded')
    accepted_by_name={r['case_name']:r for r in accepted}
    require(len(accepted)==len(accepted_by_name)==192,'Independent FINAL raw inventory incomplete')
    for row in rows:
        a=accepted_by_name[row['case_name']]
        for key in ('case_name','case_id','school_seed','replicate_label','capture_seed','capture_label','grid','dt','presence','dolphins','gannets','D_captures','G_captures','D_contacts','G_contacts','D_launches','G_launches','native_steps','remaining_fish','initial_fish','completion_sha256'):
            require(a[key]==row[key],'Independent FINAL raw row differs:'+key)
        close(a['actual_duration_T'],row['actual_duration_T'],1e-7);require(a['native_absorbing_termination']==row['native_absorbing_termination'],'Independent depletion differs')
    engineering=s.manifest['engineering_cases'];prefixes=final['prefixes']
    expected_smoke={identity(SCHOOLS[0],LABELS[0],g,a,s.synthetic) for g in GRIDS for a in ARMS}
    require(set(engineering)==expected_smoke and len(prefixes)==6 and {p['case'] for p in prefixes}==expected_smoke,'Six engineering prefix proofs required')
    for p in prefixes:
        s.sealed(engineering[p['case']]);require(p['status']=='passed' and abs(p['prefix_T']-4.)<=1e-7,'Unpassed4T prefix')
        require(p['smoke_completion_sha256']==engineering[p['case']]['completion_sha256'] and p['full_completion_sha256']==s.manifest['cases'][p['case']]['completion_sha256'],'Changed smoke/full binding')

def recompute(rows):
    index={(r['school_seed'],r['replicate_label'],r['grid'],r['presence']):r for r in rows}
    deltas={};worlds=[];school_counts=[];school_points=[]
    for school in SCHOOLS:
        for label in LABELS:
            for grid in GRIDS:
                mixed=index[school,label,grid,'DG'];da=index[school,label,grid,'D']['D_captures'];ga=index[school,label,grid,'G']['G_captures']
                dd,gd=mixed['D_captures']-da,mixed['G_captures']-ga;deltas[school,label,grid]=(dd,gd)
                worlds.append(dict(school_seed=school,replicate_label=label,grid=grid,D_control_group_captures=da,G_control_group_captures=ga,D_mixed_group_captures=mixed['D_captures'],G_mixed_group_captures=mixed['G_captures'],D_effect_per_individual_36T=dd/12,G_effect_per_individual_36T=gd/36))
        sums={g:[sum(deltas[school,l,g][j] for l in LABELS) for j in (0,1)] for g in GRIDS}
        vector=[*sums['fine'],*sums['coarse'],sums['fine'][0]-sums['coarse'][0],sums['fine'][1]-sums['coarse'][1]];school_counts.append(vector)
        school_points.append(dict(school_seed=school,**{k:v/d for k,v,d in zip(CONTRASTS,vector,(24,72,24,72,24,72))}))
    summaries={}
    for j,(name,denominator) in enumerate(zip(CONTRASTS,(24,72,24,72,24,72))):
        points=[v[j]/denominator for v in school_counts];mean=sum(v[j] for v in school_counts)/(16*denominator)
        sd=math.sqrt(sum((x-mean)**2 for x in points)/15);se=sd/4
        species=name[-1];count=12 if species=='D' else 36;labelled=[];difference=[]
        for school in SCHOOLS:
            values=[]
            for label in LABELS:
                sp=0 if species=='D' else 1
                value=deltas[school,label,'fine'][sp]-deltas[school,label,'coarse'][sp] if 'minus' in name else deltas[school,label,name.split('_')[0]][sp]
                values.append(value);labelled.append(value)
            difference.append((values[0]-values[1])/count)
        w=sum(x*x/2 for x in difference)/16
        sign=lambda values:dict(positive=sum(v>0 for v in values),zero=sum(v==0 for v in values),negative=sum(v<0 for v in values))
        summaries[name]=dict(mean=mean,school_sd=sd,se=se,df=15,n_schools=16,n_worlds=32,student_t_97_5_ci=[mean-T_CRITICAL*se,mean+T_CRITICAL*se],school_signs=sign([v[j] for v in school_counts]),world_signs=sign(labelled),within_school_variance_W=w,conditional_mcse=math.sqrt(w/32),mean_rate_change_per_individual_per_T=mean/36)
    joint=all(summaries['fine_'+sp]['student_t_97_5_ci'][0]>0 for sp in ('D','G'))
    return dict(estimates=summaries,school_points=school_points,world_points=worlds,primary_joint_criterion_met=joint)

def validate_cached(s,rows,result,final):
    cached=s.json(s.manifest['analysis']['statistics.json'])
    require(cached['status']=='complete_prespecified_analysis' and cached['case_count']==192 and cached['primary']['grid']=='fine','Wrong cached final statistics')
    require(cached['design']['schools']==list(SCHOOLS) and cached['design']['replicate_labels']==list(LABELS) and cached['design']['grids']==GRIDS and cached['design']['presence_arms']==list(ARMS),'Wrong cached design')
    for key,value in [('dolphins',12),('gannets',36),('fish',160),('duration_T',36)]:require(type(cached['design'][key]) in (int,float) and cached['design'][key]==value,'Wrong cached numeric design')
    require(type(cached['t_critical']) in (int,float) and math.isfinite(cached['t_critical']) and cached['t_critical']==T_CRITICAL,'Cached t critical value differs')
    coverage=cached['primary']['familywise_coverage_target']
    require(type(coverage) in (int,float) and math.isfinite(coverage) and coverage==.95,'Cached original familywise coverage target differs')
    require(cached['primary']['joint_criterion_met'] is result['primary_joint_criterion_met'],'Fine primary decision mismatch')
    b=cached['bootstrap'];require((b['draws'],b['seed'],b['generator'],b['quantiles'],b['unit'],b['common_draws_across_all_contrasts'])==(50000,8611030,'PCG64',[.0125,.9875],'whole matched school vector',True),'Changed cached bootstrap procedure')
    require(cached['uncertainty']['mcse_added_to_total_se'] is False,'Repeat MCSE double-counted')
    oracle=final['independent_statistics'];require(oracle['independent_schools']==16 and oracle['capture_repeats_per_school']==2 and oracle['encounter_rows']==192,'Wrong independent oracle scope')
    require((oracle['bootstrap']['draws'],oracle['bootstrap']['seed'],oracle['bootstrap']['quantiles'])==(50000,8611030,[.0125,.9875]),'Independent cache bootstrap procedure differs')
    for name,computed in result['estimates'].items():
        species=name[-1]
        saved=cached['secondary']['fine_minus_coarse'][species] if 'minus' in name else cached['primary']['species'][species] if name.startswith('fine') else cached['secondary']['coarse'][species]
        for field,value in (('df',15),('n_schools',16),('n_worlds',32)):
            require(type(saved.get(field)) is int and saved[field]==value,'Cached t endpoint scope differs:'+field)
        t_interval=saved.get('student_t_97_5_ci')
        require(type(t_interval) is list and len(t_interval)==2,'Cached t interval requires exactly two endpoints')
        require(all(type(value) in (int,float) and math.isfinite(value) for value in t_interval),'Cached t interval requires finite numeric endpoints')
        require(t_interval[0]<=t_interval[1],'Cached t interval endpoints are reversed')
        key=species+'_fine_minus_coarse' if 'minus' in name else species+'_'+name.split('_')[0];accepted=oracle['endpoints'][key]
        for field in ('mean','school_sd','se','within_school_variance_W','conditional_mcse','mean_rate_change_per_individual_per_T'):close(computed[field],saved[field])
        for a,z in zip(computed['student_t_97_5_ci'],t_interval):close(a,z)
        require(computed['school_signs']==saved['school_signs'] and computed['world_signs']==saved['world_signs'],'Cached signs differ')
        interval=saved['bootstrap_97_5_ci'];require(len(interval)==2 and number(interval[0])<=number(interval[1]),'Bad cached bootstrap endpoints')
        for a,z in zip(interval,[accepted['bootstrap_975_low'],accepted['bootstrap_975_high']]):close(a,z)
        computed['bootstrap_97_5_ci']=interval
    saved_school={r['school_seed']:r for r in cached['school_points']};require(len(cached['school_points'])==len(saved_school)==16,'Wrong cached school points')
    for row in result['school_points']:
        for name in CONTRASTS:close(row[name],saved_school[row['school_seed']][name])
    points={p['case_id']:p for p in cached['case_points']};require(len(cached['case_points'])==len(points)==192,'Wrong cached casepoint inventory')
    for row in rows:
        p=points[row['case_id']];require(set(p)==POINT_FIELDS,'Wrong canonical casepoint fields')
        for field in ('case_id','school_seed','replicate_label','grid','dt','presence','dolphins','gannets','D_captures','G_captures','duration_T','native_steps','remaining_fish'):require(p[field]==row[field],'Cached casepoint differs:'+field)
        for field in ('school_seed','replicate_label','dolphins','gannets','D_captures','G_captures','native_steps','remaining_fish'):require(type(p[field]) is int,'Cached casepoint integer type differs')
        require(type(p['duration_T']) in (int,float),'Invalid nominal casepoint clock type')
        require(type(p['native_absorbing_termination']) is bool and p['native_absorbing_termination']==row['native_absorbing_termination'],'Cached casepoint depletion differs')
        observed=number(p['actual_duration_T']);close(observed,row['actual_duration_T'],1e-7)
        require(0<observed<=36+1e-7 and abs(observed-p['native_steps']*p['dt'])<=1e-7,'Cached casepoint clock/step mismatch')
        for sp,count in [('D',row['dolphins']),('G',row['gannets'])]:
            for suffix,den in [('captures_per_individual_36T',count),('captures_per_individual_per_T',count*36)]:
                if count:close(p[sp+'_'+suffix],row[sp+'_captures']/den)
                else:require(p[sp+'_'+suffix] is None,'Absent species return is not null')
    return cached

def analyse_snapshot(path,allow_synthetic=False,expected_receipt_sha256=None):
    s=Snapshot(path,allow_synthetic,expected_receipt_sha256);final,meta,owner=validate_evidence(s)
    rows=read_counts(s,owner);validate_audit_closure(s,final,owner,rows);result=recompute(rows);cached=validate_cached(s,rows,result,final)
    result.update(status='SYNTHETIC_TEST_DATA_ONLY' if s.synthetic else 'verified_portable_primary192',synthetic=s.synthetic,production_accepted=not s.synthetic,case_count=192,independent_school_clusters=16,counts=rows,new_bootstrap_draws=0,native_model_imports=0,native_steps=0,bootstrap_verification='Cached50k endpoints agree with sealed owner outputs and original independent FINAL oracle; no draws generated',reporter_input=dict(stage='final',school_count=16,rows=rows,statistics=cached,synthetic=s.synthetic,proofs={'portable_manifest_sha256':sha(s.path)},source_pins_sha256=s.manifest.get('reporter_source_pins_sha256')))
    return result

def write_tables(result,destination):
    """Four additive tables; never touches the existing discovery profile."""
    destination=Path(destination);require(not destination.exists(),'Do not overwrite a prior table export');destination.mkdir(parents=True)
    estimates=[]
    for name,row in result['estimates'].items():
        value={key:row[key] for key in ('mean','school_sd','se','n_schools','n_worlds','within_school_variance_W','conditional_mcse','mean_rate_change_per_individual_per_T')}
        value.update(contrast=name,t_97_5_low=row['student_t_97_5_ci'][0],t_97_5_high=row['student_t_97_5_ci'][1],cached_bootstrap_97_5_low=row['bootstrap_97_5_ci'][0],cached_bootstrap_97_5_high=row['bootstrap_97_5_ci'][1])
        for scope in ('school','world'):
            for sign,count in row[scope+'_signs'].items():value[scope+'_'+sign]=count
        estimates.append(value)
    tables={'validation_case_counts.csv':result['counts'],'validation_school_effects.csv':result['school_points'],'validation_world_effects.csv':result['world_points'],'validation_estimates.csv':estimates}
    for name,rows in tables.items():
        with (destination/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    receipt=dict(status=result['status'],synthetic=result['synthetic'],production_accepted=result['production_accepted'],case_count=192,independent_school_clusters=16,new_bootstrap_draws=0,native_model_imports=0,files={name:sha(destination/name) for name in tables})
    (destination/'TABLE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--allow-synthetic',action='store_true');p.add_argument('--expected-receipt-sha256');p.add_argument('--output',type=Path);p.add_argument('--tables',type=Path);a=p.parse_args()
    r=analyse_snapshot(a.snapshot,a.allow_synthetic,a.expected_receipt_sha256)
    if a.output:
        require(not a.output.exists(),'Do not overwrite prior analysis');a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    if a.tables:write_tables(r,a.tables)
    print(json.dumps({k:r[k] for k in ('status','synthetic','production_accepted','case_count','independent_school_clusters','primary_joint_criterion_met','new_bootstrap_draws','native_model_imports','native_steps')},indent=2))
if __name__=='__main__':main()
