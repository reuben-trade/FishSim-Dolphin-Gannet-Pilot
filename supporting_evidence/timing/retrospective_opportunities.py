"""Read-only motion-bound screening of sealed ordinary36T DG launches.

Saved positions do not resolve launch instants. Endpoint speed-ball
intersections certify qualifications when their complete interval lies inside12/4.
No simulator import, model construction, or native execution occurs.
"""
from pathlib import Path
from collections import Counter
import csv, gzip, hashlib, json
import numpy as np

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'exposed_replication_2026-11-08/results/full_36T_v1/cases'
DT=.00125

def read(p):return json.loads(p.read_text())
def records(p):
 with gzip.open(p,'rt') as f:return [json.loads(x) for x in f]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

rows=[];cases=[]
for seed in (39063501,39063502):
 for cap in (61001,61002):
  p=PRIOR/f's{seed}_exposed_DG_c{cap}'
  seal=read(p/'completion.json');assert seal['status']=='complete'
  for name,digest in seal['files'].items():assert sha(p/name)==digest
  for path,digest in read(p/'source_manifest.json').items():assert sha(Path(path))==digest
  e=records(p/'events.jsonl.gz')
  dl=[r for r in e if r['kind']=='transition' and r['reason']=='launch' and r['actor_id'].startswith('D')]
  gl=[r for r in e if r['kind']=='transition' and r['reason']=='launch' and r['actor_id'].startswith('G')]
  with np.load(p/'trajectories.npz') as t:
   origin=float(read(p/'initial_engine.json')['actors'][0]['time']);time=origin+t['time'];ids=list(map(int,t['prey_ids']));actors=list(map(str,t['actor_ids']))
   def body(who,when,speed):
    # Actual position lies in both endpoint speed balls. Bound the complete
    # intersection around the linear chord point; no curvature assumption.
    j=min(len(time)-1,int(np.searchsorted(time,when,side='left')));i=max(0,j-1)
    p0=t['predator_positions'][i,actors.index(who)];p1=t['predator_positions'][j,actors.index(who)]
    if abs(time[j]-when)<1e-9:return p1,1e-8,[float(time[j]),float(time[j])]
    assert time[i]<=when<=time[j]
    r0=speed*(when-time[i])+1e-8;r1=speed*(time[j]-when)+1e-8
    distance=float(np.linalg.norm(p1-p0));alpha=(when-time[i])/(time[j]-time[i])
    point=(1-alpha)*p0+alpha*p1
    assert distance<=r0+r1+1e-7
    if distance<1e-12:return point,min(r0,r1),[float(time[i]),float(time[j])]
    centre=alpha*distance
    lower=max(-r0,distance-r1);upper=min(r0,distance+r1)
    crossing=(r0*r0-r1*r1+distance*distance)/(2*distance)
    coordinate=float(np.clip(crossing,lower,upper))
    squared=min(r0*r0+centre*centre-2*coordinate*centre,
        r1*r1-distance*distance+centre*centre+2*coordinate*(distance-centre))
    return point,float(np.sqrt(max(0.,squared))+1e-8),[float(time[i]),float(time[j])]
   def fish(who,when):
    j=ids.index(int(who));possible=np.flatnonzero(t['alive'][:,j])
    assert len(possible)
    i=int(possible[np.argmin(abs(time[possible]-when))])
    # The prospective cue/observation uses constant-velocity within one dt.
    # Its deviation from the actual fish path is at most2*speed*dt.
    return t['positions'][i,j],float(3*abs(time[i]-when)+6*DT+1e-8),float(time[i])
   for g in gl:
    relevant=[d for d in dl if 2*DT+1e-9<=g['time']-d['time']<=2.-1e-9]
    for d in relevant:
     gp,ge,gt=body(g['actor_id'],g['time'],10.)
     dp,de,dt=body(d['actor_id'],d['time'],6.)
     gf,gfe,gft=fish(g['target_id'],g['time'])
     df,dfe,dft=fish(d['target_id'],d['time'])
     peer=float(np.linalg.norm(gp-dp));region=float(np.linalg.norm(gf-df))
     plo,phi=max(0.,peer-ge-de),peer+ge+de
     rlo,rhi=max(0.,region-gfe-dfe),region+gfe+dfe
     certain=phi<=12. and rhi<=4.
     possible=plo<=12. and rlo<=4.
     age=float(g['time']-d['time'])
     row=dict(case=p.name,school_seed=seed,capture_seed=cap,G_actor=g['actor_id'],G_bout=g['bout_id'],G_target=g['target_id'],G_time=g['time'],G_elapsed=g['time']-origin,D_actor=d['actor_id'],D_bout=d['bout_id'],D_target=d['target_id'],D_time=d['time'],cue_age_T=age,peer_distance_estimate=peer,peer_distance_lower=plo,peer_distance_upper=phi,target_region_distance_estimate=region,target_region_distance_lower=rlo,target_region_distance_upper=rhi,robust_local_qualification=certain,possible_local_qualification=possible,lag1_release_still_future=age<1.-1e-9,robust_lag1_deferral_opportunity=certain and age<1.-1e-9,G_body_snapshot_time=gt,D_body_snapshot_time=dt,G_target_snapshot_time=gft,D_target_snapshot_time=dft)
     rows.append(row)
  mine=[r for r in rows if r['case']==p.name]
  qualified={(r['G_actor'],r['G_bout']) for r in mine if r['robust_local_qualification']}
  deferrable={(r['G_actor'],r['G_bout']) for r in mine if r['robust_lag1_deferral_opportunity']}
  later=[r for r in mine if r['robust_lag1_deferral_opportunity'] and r['G_elapsed']>8.+1e-8]
  first=min(later,key=lambda r:r['G_time'],default=None)
  cases.append(dict(case=p.name,source_completion_sha256=sha(p/'completion.json'),G_launches=len(gl),D_launches=len(dl),recent_committed_time_candidates=len(mine),robust_qualifying_G_launches=len(qualified),possible_qualifying_pairs=sum(r['possible_local_qualification'] for r in mine),possible_lag1_deferral_pairs=sum(r['possible_local_qualification'] and r['lag1_release_still_future'] for r in mine),robust_lag1_deferrable_G_launches=len(deferrable),first_robust_lag1_after8T=first))

out=HERE/'results/retrospective_36T';out.mkdir(parents=True,exist_ok=True)
with (out/'candidate_launch_pairs.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
result=dict(status='complete',native_steps=0,method='Conservative speed-bound intervals: predator position lies in intersection of speed balls from both bracketing snapshot endpoints, enclosed around the chord point; fish uses closest alive snapshot. Exact sealed event times/target IDs. Max speeds D6,G10,fish3; target predictions include2*3*dt extra uncertainty each. Require cue age>=2dt to guarantee prior-step publication. Robust qualifies only if both distance upper bounds lie within unchanged12/4 thresholds.',limitation='This is a retrospective screening of the unmodified baseline. It certifies distance margins without exact event-position reconstruction, and does not predict the altered trajectory after any first deferral. Borderline intervals remain unresolved. Exact target-selection behavior and flight response still require an enabled native run.',cases=cases,all_G_launches=sum(r['G_launches'] for r in cases),robust_qualifying_G_launches=sum(r['robust_qualifying_G_launches'] for r in cases),robust_lag1_deferrable_G_launches=sum(r['robust_lag1_deferrable_G_launches'] for r in cases),robust_lag1_after8T_pairs=sum(r['robust_lag1_deferral_opportunity'] and r['G_elapsed']>8.+1e-8 for r in rows))
(out/'screening.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
