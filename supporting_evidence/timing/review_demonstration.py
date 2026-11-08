"""Independent read-only review of the sealed post-hoc36T timing demonstration."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip, importlib.util, json, math
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_timing_frozen_analysis',HERE/'analyze.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
case=HERE/'results/lag1_36T_demonstration_v1/cases/s39063501_lag1_DG_c61002'
base=A.PRIOR/'results/full_36T_v1/cases/s39063501_exposed_DG_c61002'
result=A.enabled_feasibility(case,base)
rows=A.records(case/'timing_events.jsonl.gz');events=A.records(case/'events.jsonl.gz')
initial=A.read(case/'initial_engine.json');final=A.read(case/'final_engine.json')
summary=A.read(case/'summary.json')
gates=[r for r in rows if r['kind']=='timing_gate']
blocked=[r for r in gates if not r['allow']]
cues={(r['actor_id'],r['bout_id'],r['time']):r for r in rows if r['kind']=='committed_dolphin_cue'}
launches={(r['actor_id'],r['bout_id'],r['time']) for r in events if r['kind']=='transition' and r['reason']=='launch' and r['actor_id'].startswith('D')}
assert set(cues)==launches
for r in gates:
 cfg=initial['actor_policy'][r['actor_id']]['config']
 assert np.linalg.norm(np.asarray(r['position'])[:2]-np.asarray(r['target_position'])[:2])<=cfg['plunge_horizontal_radius']+1e-10
 assert r['position'][2]>=cfg['surface_z']-1e-10
 if 'timing' not in r:continue
 cue=r['timing']['cue'];key=(cue['actor_id'],cue['bout_id'],cue['time'])
 assert key in cues
 for key2 in ('position','target_id','target_position','published_at'):assert cue[key2]==cues[key][key2]
 assert cue['time']<=cue['published_at']<=r['time']+1e-10

# Verify every physical/capture stream against resolved oral contacts.
contacts=[r for r in events if r['kind']=='oral'];removed=[]
for who,policy in initial['actor_policy'].items():
 cfg,mouth=policy['config'],policy['mouth'];rng=np.random.default_rng(0)
 rng.bit_generator.state=deepcopy(initial['capture_rng'][who]);closed=set();caught=0
 actor=[r for r in events if r['kind']=='transition' and r['actor_id']==who]
 times={r['bout_id']:r['time'] for r in actor if r['reason']=='launch'}
 ready=next(r for r in initial['actors'] if r['actor_id']==who)['ready_at']
 for r in actor:
  if r['reason']=='launch':assert r['time']>=ready-1e-8
  elif r['reason']=='capture':ready=r['time']+cfg['handling_duration']
  elif r['reason'] in ('contact_miss','timeout','target_not_visible','ascent_depth_margin','uncommitted_water_entry'):ready=r['time']+cfg['miss_recovery_duration']
 for r in (r for r in contacts if r['actor_id']==who):
  c=r['contact'];mouthpoint=np.asarray(c['mouth_position']);prey=np.asarray(c['prey_position']);body=np.asarray(c['body_position']);heading=np.asarray(c['heading'])
  assert np.linalg.norm(mouthpoint-prey)<=mouth['radius']+1e-8
  assert abs(np.linalg.norm(heading)-1)<1e-8 and np.dot(prey-body,heading)>=-1e-8
  bound=mouth['forward_offset']*(1-math.cos(cfg['turn_rate']*(c['segment_end']-c['segment_start'])/2))
  assert np.linalg.norm(mouthpoint-body-mouth['forward_offset']*heading)<=bound+1e-9
  assert max(body[2],mouthpoint[2])<=cfg['surface_z']+1e-8
  assert times[r['bout_id']]-1e-9<=c['time']<=times[r['bout_id']]+cfg['bout_duration']+1e-9
  if r['draw'] is not None:
   assert r['closes_bout'] and r['bout_id'] not in closed;closed.add(r['bout_id'])
   assert rng.random()==r['draw'] and (r['status']=='captured')==(r['draw']<.7)
   if r['status']=='captured':caught+=1;removed.append(r['prey_id'])
 assert rng.bit_generator.state==final['capture_rng'][who]
 assert caught==summary['per_actor'][who]['captures']
 assert len(closed)==summary['per_actor'][who]['contacts']
assert len(removed)==len(set(removed))==summary['initial_count']-summary['final_count']
assert set(removed)==set(final['ownership']['captured_ids'])

# The enabled policy must reproduce the same physics until its first actual gate.
cut=min((r['time'] for r in blocked),default=float('inf'))
with np.load(case/'trajectories.npz') as x,np.load(base/'trajectories.npz') as y:
 origin=initial['actors'][0]['time'];keep=origin+x['time']<cut-1e-10
 n=int(keep.sum());assert np.array_equal(x['time'][:n],y['time'][:n])
 for key in ('prey_ids','actor_ids'):assert np.array_equal(x[key],y[key])
 for key in ('positions','directions','alive','predator_positions','predator_modes','target_ids','dolphin_phases'):
  assert np.array_equal(x[key][:n],y[key][:n],equal_nan=True) if x[key].dtype.kind in 'fc' else np.array_equal(x[key][:n],y[key][:n]),key
result['independent_review']=dict(status='passed',actual_committed_D_cues=len(cues),legal_horizontal_plunge_gates=len(gates),denied_gate_records=len(blocked),first_denied_gate_time=None if not blocked else cut,exact_preintervention_frames=n,oral_geometry_capture_rng_recovery_and_unique_removals='passed',G_launches=sum(r['kind']=='actual_gannet_launch' for r in rows),G_water_entries=sum(r['kind']=='actual_gannet_water_entry' for r in rows),completion_sha256=A.sha(case/'completion.json'))
result['demonstration_native_budget']=dict(previous_feasibility_T=12,posthoc_single_demonstration_T=36,additional_native_steps=28800,total_native_steps=38400,full_timing_study=False)
result['posthoc_interpretation']='Selected after baseline opportunity screening; engineering demonstration only,not independent timing-benefit confirmation.'
out=HERE/'results/lag1_36T_demonstration_v1/demonstration_review.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
