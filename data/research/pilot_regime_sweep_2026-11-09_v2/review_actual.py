"""Read-only physical review adapted from the reviewed fine-grid audit."""
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import gzip,hashlib,json,math
import numpy as np
HERE=Path(__file__).resolve().parent
OUT=HERE/'results/integration_4T_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(p):
 with gzip.open(p,'rt') as f:return [json.loads(s) for s in f]
def generator(state):
 r=np.random.default_rng(0);r.bit_generator.state=deepcopy(state);return r
def validate_dolphin_cycle(event,config):
 assert config['dolphin_target_policy']=='exposed'
 assert event['pressure_elapsed']>=config['minimum_herding_duration']-1e-10
 assert event['selected_neighbor_count']==event['feasible_min_neighbor_count']
 assert abs(event['time']-event['pressure_started']-event['pressure_elapsed'])<1e-9
def audit_case(p):
 summary,seal=read(p/'summary.json'),read(p/'completion.json')
 config=read(p/'config.json')
 for who,controller in read(p/'initial_engine.json')['controllers'].items():
  if who.startswith('D'):
   assert controller['simple']['policy']=='exposed'
   assert controller['parameters']['pressure_minimum']==config['minimum_herding_duration']
   assert controller['simple']['herding_minimum']==config['minimum_herding_duration']
 assert summary['status']==seal['status']=='complete'
 for name,digest in seal['files'].items():assert sha(p/name)==digest,(p.name,name)
 for name,digest in read(p/'source_manifest.json').items():assert sha(Path(name))==digest,name
 assert read(p/'audit.json')['status']=='passed'
 duration=summary['planned_duration'];observed=summary['actual_duration'];steps=round(observed/.00125)
 monitor_times=np.arange(int(np.floor((observed+1e-8)/.1))+1)*.1
 frame_times=monitor_times if abs(monitor_times[-1]-observed)<1e-8 else np.r_[monitor_times,observed]
 samples=len(frame_times)
 assert summary['dt']==.00125 and summary['native_steps']==steps
 assert observed<=duration+1e-8
 if summary['native_absorbing_termination']:assert summary['final_count']==0
 else:assert abs(observed-duration)<1e-8
 initial,final=read(p/'initial_engine.json'),read(p/'final_engine.json')
 events,cycles=records(p/'events.jsonl.gz'),records(p/'opportunities.jsonl.gz')
 oral=[r for r in events if r['kind']=='oral'];removed=[];actors={}
 for who,policy in initial['actor_policy'].items():
  cfg,mouth=policy['config'],policy['mouth'];assert policy['capture_probability']==.7
  r=generator(initial['capture_rng'][who]);closed=set();caught=0
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
    assert e['closes_bout'] and e['bout_id'] not in closed;closed.add(e['bout_id'])
    assert r.random()==e['draw'] and (e['status']=='captured')==(e['draw']<.7)
    if e['status']=='captured':caught+=1;removed.append(e['prey_id'])
  assert r.bit_generator.state==final['capture_rng'][who]
  per=summary['per_actor'][who]
  assert (per['captures'],per['launches'],per['contacts'])==(caught,len(launch),len(closed))
  assert abs(sum(per['physical_mode_time'].values())-observed)<1e-8
  actors[who]=dict(status='passed',captures=caught,launches=len(launch),oral_contacts=len(closed),geometry='passed',capture_rng='passed',recovery='passed')
 assert len(removed)==len(set(removed))==summary['initial_count']-summary['final_count']
 assert set(removed)==set(final['ownership']['captured_ids'])
 with np.load(p/'initial_school.npz') as x,np.load(p/'final_school.npz') as y:
  assert int(x['step_index'])==16000 and int(y['step_index'])==16000+steps
  assert abs(float(x['time'])-20.)<1e-8 and abs(float(y['time'])-(20.+observed))<1e-8
  assert set(map(int,x['prey_ids']))-set(map(int,y['prey_ids']))==set(removed)
 with np.load(p/'trajectories.npz') as t:
  assert len(t['time'])==samples and np.allclose(t['time'],frame_times,rtol=0,atol=1e-8)
  alive=t['alive'];assert np.all(t['positions'][:,:,2][alive]<=1e-8)
  common=alive[:-1]&alive[1:];movement=np.linalg.norm(np.diff(t['positions'],axis=0),axis=2)
  assert np.all(movement[common]<=np.broadcast_to(3*np.diff(t['time'])[:,None],movement.shape)[common]+1e-8)
  for i,who in enumerate(t['actor_ids']):
   speed=6. if str(who).startswith('D') else 10.
   assert np.all(np.linalg.norm(np.diff(t['predator_positions'][:,i],axis=0),axis=1)<=speed*np.diff(t['time'])+1e-8)
 monitor=records(p/'monitor.jsonl.gz')
 for who in initial['actor_policy']:
  elapsed=[r['elapsed'] for r in monitor if r['actor_id']==who]
  assert len(elapsed)==len(monitor_times) and np.allclose(elapsed,monitor_times,rtol=0,atol=1e-8)
 dlo=[e for e in events if e['kind']=='transition' and e['reason']=='launch' and e['actor_id'].startswith('D')]
 clo=[e for e in cycles if e['kind']=='cycle_launch']
 key=lambda e:(e['actor_id'],e['bout_id'],e['time'],e['target_id'])
 assert {key(e) for e in dlo}=={key(e) for e in clo} and len(dlo)==len(clo)
 for e in clo:
  validate_dolphin_cycle(e,config)
 target={}
 for who in (who for who in initial['controllers'] if who.startswith('G')):
  rng=generator(initial['controllers'][who]['target_rng_state']);count=0
  for e in events:
   if e.get('reason')!='gannet_global_dense_target_selected' or e['actor_id']!=who:continue
   detail=e['targeting_diagnostics'];prob=detail['selection_probabilities']
   if prob:
    weights=np.asarray(detail['eligible_patch_accessible_counts'],float)
    assert np.allclose(weights/weights.sum(),prob,rtol=0,atol=1e-15)
    assert int(rng.choice(len(prob),p=prob))==detail['selected_patch'];count+=1
  assert rng.bit_generator.state==final['controllers'][who]['target_rng_state']
  target[who]=dict(status='passed',weighted_draws=count)
 tie=generator(initial['tie_rng']);calls=read(p/'tie_stream_calls.json')
 for e in calls:assert tie.permutation(e['n']).tolist()==e['result']
 assert tie.bit_generator.state==final['tie_rng']
 return dict(case=p.name,status='passed',native_steps=steps,actual_duration_T=summary['actual_duration'],saved_frames=samples,actor_monitor_samples_each=len(monitor_times),dolphin_cycle_launches=len(clo),actors=actors,gannet_target_rng=target,tie_rng='passed',source_and_case_seals='passed',completion_sha256=sha(p/'completion.json'))
def main():
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 output=args.output.resolve();status=read(output/'status.json');assert status['status']=='complete'
 cases=sorted((output/'cases').iterdir());receipts=[audit_case(p)for p in cases]
 assert len(receipts)==status['complete']==status['planned']
 result=dict(status='passed',at=datetime.now(ZoneInfo('Australia/Perth')).isoformat(),native_steps_executed_by_review=0,cases=receipts,review_source_sha256=sha(Path(__file__)),scope='Physical review using the previously reviewed fine-grid geometry/RNG/cadence helper; not independent biological validation')
 (output/'physical_review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
