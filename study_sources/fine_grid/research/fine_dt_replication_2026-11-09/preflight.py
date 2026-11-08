"""Zero-step construction comparison for all24 paired numerical-grid cases."""
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
import hashlib,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
COARSE=HERE.parent/'longer_replication_2026-11-09'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def changes(a,b,path=''):
 if isinstance(a,np.ndarray) or isinstance(b,np.ndarray):return [] if np.array_equal(a,b) else [path]
 if isinstance(a,dict) and isinstance(b,dict):
  if set(a)!=set(b):return [path+'/<keys>']
  return [v for key in a for v in changes(a[key],b[key],path+'/'+str(key))]
 if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):
  if len(a)!=len(b):return [path+'/<length>']
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in changes(x,y,path+'/'+str(i))]
 return [] if a==b else [path]
def main():
 coarse=load('_fine_preflight_coarse_build',COARSE/'build.py')
 fine=load('_fine_preflight_fine_build',HERE/'build.py')
 r=load('_fine_preflight_coarse_runner',COARSE/'run.py')
 from research.prey_mediated.encounter import Encounter
 from research.prey_mediated.scenario import TravellingSchool
 calls=[]
 def forbidden(*a,**k):calls.append(1);raise AssertionError('Preflight must not step any model')
 before={str(p):sha(p) for p in [COARSE/n for n in ('run.py','build.py','controllers.py','gannet.py','protocol.json','frozen_sources.json','checkpoints/manifest.json')]}
 receipts=[]
 with patch.object(Encounter,'step',forbidden),patch.object(TravellingSchool,'step',forbidden):
  for seed in range(39064501,39064509):
   for presence in ('D','G','DG'):
    a,ma=coarse.build(seed,'exposed',61001,presence);b,mb=fine.build(seed,'exposed',61001,presence)
    state_changes=changes(asdict(a.school.state()),asdict(b.school.state()))
    assert not state_changes,state_changes
    assert not changes(r.snapshot(a),r.snapshot(b))
    scenario_changes=changes(asdict(a.scenario),asdict(b.scenario))
    assert scenario_changes==['/dt'],scenario_changes
    assert a.scenario.dt==.00125 and b.scenario.dt==.000625
    assert a.school.state().step_index==b.school.state().step_index==16000
    assert abs(a.school.state().time-20.)<1e-8 and a.school.state().time==b.school.state().time
    diff=changes(ma,mb)
    allowed={'/study','/duration','/dt','/numerical_convergence','/preparation_manifest_path'}
    assert set(diff)<=allowed,diff
    assert ma['capture_probability']==mb['capture_probability']==.7
    assert ma['checkpoint_sha256']==mb['checkpoint_sha256']
    assert ma['preparation_manifest_sha256']==mb['preparation_manifest_sha256']
    assert ma['controller_initial_state']==mb['controller_initial_state']
    receipts.append(dict(school_seed=seed,presence=presence,status='passed',school_initial_state='bitwise identical arrays and exact metadata',predator_and_private_stream_snapshot='exactly identical',scenario_changed_paths=scenario_changes,metadata_changed_paths=diff,checkpoint_sha256=ma['checkpoint_sha256'],native_steps=0))
    del a,b
 assert not calls
 assert all(sha(Path(path))==digest for path,digest in before.items())
 result=dict(status='passed',at=datetime.now(ZoneInfo('Australia/Perth')).isoformat(),native_steps=0,cases=receipts,total_cases=len(receipts),coarse_source_hashes_unchanged=before,scope='samepreparedgeometry+time+stepindex,actorstates/configs/mouths,controllerparameters/state,capture/target/tieRNG; onlyscenariodt differs; metadata labels/horizon/path expresslylisted')
 (HERE/'preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
