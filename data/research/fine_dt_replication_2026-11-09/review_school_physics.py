"""Additional read-only sampled fish/actor kinematics across both full grids."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse,hashlib,json
import numpy as np
HERE=Path(__file__).resolve().parent
FINE=HERE/'results/full_36T_v1'
COARSE=HERE.parent/'longer_replication_2026-11-09/results/full_72T_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(case):
 seal=read(case/'completion.json');assert seal['status']=='complete'
 for name,digest in seal['files'].items():assert sha(case/name)==digest
 summary=read(case/'summary.json');initial=read(case/'initial_engine.json')
 with np.load(case/'trajectories.npz') as t,np.load(case/'final_school.npz') as f:
  time=t['time'];delta=np.diff(time);assert len(time)>1 and abs(time[0])<1e-9 and np.all(delta>0)
  assert np.max(delta)<=.1+1e-8 and np.allclose(delta[:-1],.1,rtol=0,atol=1e-8)
  assert abs(time[-1]-summary['actual_duration'])<1e-8
  alive=t['alive'];x=t['positions'];v=t['directions'];assert np.isfinite(x).all() and np.isfinite(v).all()
  assert np.all(x[:,:,2][alive]<=1e-9)
  assert np.max(abs(np.linalg.norm(v,axis=2)[alive]-1),initial=0)<1e-8
  common=alive[:-1]&alive[1:];moves=np.linalg.norm(np.diff(x,axis=0),axis=2)
  assert np.all(moves[common]<=np.broadcast_to(3*delta[:,None],moves.shape)[common]+1e-8)
  assert np.array_equal(t['prey_ids'][alive[-1]],f['prey_ids'])
  assert np.array_equal(x[-1,alive[-1]],f['positions']) and np.array_equal(v[-1,alive[-1]],f['directions'])
  assert set(map(str,t['actor_ids']))==set(initial['actor_policy'])
  for i,who in enumerate(map(str,t['actor_ids'])):
   cfg=initial['actor_policy'][who]['config'];p=t['predator_positions'][:,i];assert np.isfinite(p).all()
   speed=cfg['speed'] if who.startswith('D') else max(cfg['air_speed'],cfg['speed'])
   assert np.all(np.linalg.norm(np.diff(p,axis=0),axis=1)<=speed*delta+1e-8)
   if who.startswith('D'):assert np.all(p[:,2]<=cfg['surface_z']+1e-8)
   else:assert np.all(p[:,2]>=cfg['surface_z']-cfg['max_dive_depth']-1e-8)
  reflections=int(f['surface_reflections'])
 return dict(case=str(case),status='passed',saved_frames=len(time),actual_duration_T=summary['actual_duration'],fish_surface_reflections=reflections,finite_underwater_unit_school_and_speed_bounds='passed',sampled_actor_medium_speed_and_depth_bounds='passed',final_saved_frame_matches_state='passed',completion_sha256=sha(case/'completion.json'))
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',action='store_true');a=parser.parse_args()
 if a.plan:print(json.dumps(dict(status='plan_only',native_steps=0,required_complete_cases=48)));return
 receipts=[]
 for folder in (COARSE,FINE):
  s=read(folder/'status.json');assert s['status']=='complete' and s['complete']==24
  for seed in range(39064501,39064509):
   for presence in ('D','G','DG'):receipts.append(check(folder/'cases'/f's{seed}_exposed_{presence}_c61001'))
 out=FINE/'analysis_final/school_physics_review.json'
 value=dict(status='passed',at=datetime.now(ZoneInfo('Australia/Perth')).isoformat(),native_steps_executed_by_review=0,complete_cases=48,review_source_sha256=sha(Path(__file__)),scope='All retained full-run fish/actor frames; exact final frame/state identity. Contact geometry and private RNG audits are separate. Sampled bounds do not establish continuous-time convergence.',total_fish_surface_reflections=sum(r['fish_surface_reflections'] for r in receipts),cases=receipts)
 out.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({k:value[k] for k in ('status','complete_cases','native_steps_executed_by_review','total_fish_surface_reflections')}))
if __name__=='__main__':main()
