"""Read-only48-case/36T-prefix gate; never edits or publishes a paper."""
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse,csv,gzip,hashlib,json,math
import numpy as np
HERE=Path(__file__).resolve().parent
FINE=HERE/'results/full_36T_v1'
COARSE=HERE.parent/'longer_replication_2026-11-09/results/full_72T_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with gzip.open(p,'rt') as f:return [json.loads(s) for s in f]
def generator(state):
 r=np.random.default_rng(0);r.bit_generator.state=deepcopy(state);return r
def projection(s,species):
 return dict(actors=[a for a in s['actors'] if a['species']==species],actor_policy={k:v for k,v in s['actor_policy'].items() if k.startswith(species)},ownership=s['ownership'],capture_rng={k:v for k,v in s['capture_rng'].items() if k.startswith(species)},tie_rng=s['tie_rng'],controllers={k:v for k,v in s['controllers'].items() if k.startswith(species)})
def audit_case(folder,seed,presence,dt):
 p=folder/'cases'/f's{seed}_exposed_{presence}_c61001'
 complete=read(p/'completion.json');assert complete['status']=='complete'
 for name,digest in complete['files'].items():assert sha(p/name)==digest
 seal=read(p/'checkpoint_36T.seal.json');assert seal['status']=='complete' and seal['nominal_horizon_T']==36.
 for name,digest in seal['files'].items():assert sha(p/name)==digest
 for name,digest in seal['source_sha256'].items():assert sha(Path(name))==digest
 h=read(p/'checkpoint_36T.json');streams=read(p/'checkpoint_36T.streams.json')
 initial,final=streams['initial'],streams['final'];events=rows(p/'checkpoint_36T.events.jsonl.gz')
 assert h['status']=='complete' and h['nominal_horizon_T']==36. and h['physical_accounting_audit']['status']=='passed'
 assert initial==read(p/'initial_engine.json')
 observed=h['observed_native_duration_T'];assert h['native_steps']==round(observed/dt)
 assert abs(final['ownership']['time']-initial['ownership']['time']-observed)<1e-8
 if observed<36.-1e-7:assert h['absorbing_no_food_continuation'] and h['final_count']==0
 else:assert abs(observed-36.)<1e-7
 assert {a['species'] for a in initial['actors']}==set(presence)
 oral=[e for e in events if e['kind']=='oral'];removed=[];physical_contacts=0
 for who,policy in initial['actor_policy'].items():
  assert policy['capture_probability']==.7;cfg,mouth=policy['config'],policy['mouth']
  rng=generator(initial['capture_rng'][who]);closed=set();caught=0
  actor=[e for e in events if e['kind']=='transition' and e['actor_id']==who]
  launch={e['bout_id']:e['time'] for e in actor if e['reason']=='launch'}
  assert len(launch)==sum(e['reason']=='launch' for e in actor)
  ready=next(a for a in initial['actors'] if a['actor_id']==who)['ready_at']
  for e in actor:
   if e['reason']=='launch':assert e['time']>=ready-1e-8
   elif e['reason']=='capture':ready=e['time']+cfg['handling_duration']
   elif e['reason'] in ('contact_miss','timeout','target_not_visible','ascent_depth_margin','uncommitted_water_entry'):ready=e['time']+cfg['miss_recovery_duration']
  for e in (e for e in oral if e['actor_id']==who):
   c=e['contact'];body=np.asarray(c['body_position']);prey=np.asarray(c['prey_position']);mp=np.asarray(c['mouth_position']);heading=np.asarray(c['heading'])
   assert c['segment_start']-1e-10<=c['time']<=c['segment_end']+1e-10
   assert abs(c['time']-c['segment_start']-c['fraction']*(c['segment_end']-c['segment_start']))<1e-9
   assert np.linalg.norm(mp-prey)<=mouth['radius']+1e-8
   bound=mouth['forward_offset']*(1-math.cos(cfg['turn_rate']*(c['segment_end']-c['segment_start'])/2))
   assert np.linalg.norm(mp-body-mouth['forward_offset']*heading)<=bound+1e-9
   assert abs(np.linalg.norm(heading)-1)<1e-8 and np.dot(prey-body,heading)>=-1e-8
   assert max(body[2],mp[2])<=cfg['surface_z']+1e-8
   assert launch[e['bout_id']]-1e-9<=c['time']<=launch[e['bout_id']]+cfg['bout_duration']+1e-9
   if e['draw'] is not None:
    assert e['closes_bout'] and e['bout_id'] not in closed;closed.add(e['bout_id']);physical_contacts+=1
    assert rng.random()==e['draw'] and (e['status']=='captured')==(e['draw']<.7)
    if e['status']=='captured':caught+=1;removed.append(e['prey_id'])
  assert rng.bit_generator.state==final['capture_rng'][who]
  assert h['per_actor'][who]['captures']==caught and h['per_actor'][who]['contacts']==len(closed)
  assert h['per_actor'][who]['launches']==len(launch)
  assert abs(sum(h['per_actor'][who]['physical_mode_time'].values())-observed)<1e-7
 assert len(removed)==len(set(removed))==h['initial_count']-h['final_count']
 assert set(removed)==set(final['ownership']['captured_ids'])
 with np.load(p/'checkpoint_36T.school.npz') as state:
  assert set(map(int,state['prey_ids']))==set(initial['ownership']['prey_ids'])-set(removed)
  assert abs(float(state['time'])-initial['ownership']['time']-observed)<1e-8
 target_draws=0
 for who in (k for k in initial['controllers'] if k.startswith('G')):
  rng=generator(initial['controllers'][who]['target_rng_state'])
  for e in events:
   if e.get('reason')!='gannet_global_dense_target_selected' or e['actor_id']!=who:continue
   detail=e['targeting_diagnostics'];prob=detail['selection_probabilities']
   if prob:
    weights=np.asarray(detail['eligible_patch_accessible_counts'],float)
    assert np.allclose(weights/weights.sum(),prob,rtol=0,atol=1e-15)
    assert int(rng.choice(len(prob),p=prob))==detail['selected_patch'];target_draws+=1
  assert rng.bit_generator.state==final['controllers'][who]['target_rng_state']
 tie=generator(initial['tie_rng'])
 for e in streams['tie_records']:assert tie.permutation(e['n']).tolist()==e['result']
 assert tie.bit_generator.state==final['tie_rng']
 launches={(e['actor_id'],e['bout_id']):e for e in events if e['kind']=='transition' and e['reason']=='launch' and e['actor_id'].startswith('D')}
 cycles=[e for e in events if e['kind']=='phase' and e.get('cycle_launch')]
 assert len(cycles)==len(launches)
 for e in cycles:
  q=launches[(e['actor_id'],e['bout_id'])]
  assert e['pressure_elapsed']>=2.-1e-8 and abs(e['time']-e['pressure_started']-e['pressure_elapsed'])<1e-7
  assert e['selected_neighbor_count']==e['feasible_min_neighbor_count'] and e['target_id']==q['target_id'] and e['time']==q['time']
 return h,initial,dict(status='passed',case=str(p),completion_sha256=sha(p/'completion.json'),horizon_seal_sha256=sha(p/'checkpoint_36T.seal.json'),native_dt=dt,nominal_T=36,observed_T=observed,physical_contacts=physical_contacts,target_draws=target_draws,unique_captures=len(removed),private_streams='capture/target/tieexactreplaypassed',geometry_recovery_cycle='passed')
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',action='store_true');args=parser.parse_args()
 if args.plan:print(json.dumps(dict(status='plan_only',native_steps=0,required_complete_cases=48)));return
 for folder in (COARSE,FINE):
  status=read(folder/'status.json');assert status['status']=='complete' and status['complete']==status['planned']==24
 for name,digest in read(HERE/'frozen_sources.json')['source_sha256'].items():assert sha(Path(name))==digest
 audit=read(FINE/'analysis_final/analysis_audit.json');assert audit['status']=='complete' and audit['schools']==audit['independent_schools']==8 and audit['grids']==2 and len(audit['evidence'])==48
 values={};starts={};evidence=[]
 for grid,dt,folder in (('coarse',.00125,COARSE),('fine',.000625,FINE)):
  for seed in range(39064501,39064509):
   for presence in ('D','G','DG'):
    h,s,receipt=audit_case(folder,seed,presence,dt);values[(grid,seed,presence)]=h;starts[(grid,seed,presence)]=s;evidence.append(receipt)
  for seed in range(39064501,39064509):
   for species in ('D','G'):assert projection(starts[(grid,seed,species)],species)==projection(starts[(grid,seed,'DG')],species)
 for seed in range(39064501,39064509):
  for presence in ('D','G','DG'):
   assert starts[('coarse',seed,presence)]==starts[('fine',seed,presence)]
   with np.load(COARSE/'cases'/f's{seed}_exposed_{presence}_c61001/initial_school.npz') as a,np.load(FINE/'cases'/f's{seed}_exposed_{presence}_c61001/initial_school.npz') as b:
    assert set(a.files)==set(b.files) and all(np.array_equal(a[k],b[k]) for k in a.files)
 with (FINE/'analysis_final/case_grid_comparison.csv').open() as f:table=list(csv.DictReader(f))
 assert len(table)==64
 for r in table:
  h=values[(r['grid'],int(r['school_seed']),r['presence'])]
  for key in ('captures','launches','contacts'):assert int(r[key])==h['species'][r['species']][key]
 with (FINE/'analysis_final/paired_effect_grid_differences.csv').open() as f:pairs=list(csv.DictReader(f))
 assert len(pairs)==8 and {int(r['school_seed']) for r in pairs}==set(range(39064501,39064509))
 for r in pairs:
  seed=int(r['school_seed'])
  for grid in ('coarse','fine'):
   for species in ('D','G'):
    alone=values[(grid,seed,species)]['species'][species]['captures'];mixed=values[(grid,seed,'DG')]['species'][species]['captures']
    assert int(r[f'{grid}_{species}_partner_effect'])==mixed-alone
  for species in ('D','G'):assert int(r[f'{species}_effect_fine_minus_coarse'])==int(r[f'fine_{species}_partner_effect'])-int(r[f'coarse_{species}_partner_effect'])
 files=[FINE/'analysis_final'/n for n in ('REPORT.md','case_grid_comparison.csv','paired_effect_grid_differences.csv','analysis_audit.json')]
 result=dict(status='passed',at=datetime.now(ZoneInfo('Australia/Perth')).isoformat(),stage='analysis ready for publisher; paper publication not performed',analysis_ready_for_publisher=True,paper_publication_performed=False,native_steps_executed_by_validator=0,complete_case_count=48,independent_schools=8,paired_grids=2,fine_analysis_source_sha256=sha(HERE/'analyze.py'),validator_source_sha256=sha(Path(__file__)),frozen_full_sources_sha256=sha(HERE/'frozen_sources.json'),physical_and_private_stream_review=evidence,exact_initial_matching='all24cross-gridcasesandall16speciespresenceprojections passed',table_rows=dict(case_grid_comparison=64,paired_effect_grid_differences=8),analysis_files={str(p):sha(p) for p in files},interpretation='Two-grid numerical sensitivity; no convergence/timestep-independence claim and no extra independent schools')
 (HERE/'paper_update_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status='passed',path=str(HERE/'paper_update_validation.json'),complete_case_count=48,paper_publication_performed=False)))
if __name__=='__main__':main()
