"""One reviewed engineering validation sequence; source/lease/budget guards only."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,fcntl,hashlib,json,os,signal,subprocess,sys,time

CANDIDATE=Path('/tmp/FishSim_Regime_Runtime_Example_Candidate_v4')
PACKAGE=Path('/home/venture/FishSim-Dolphin-Gannet-Pilot')
EXECUTION=Path('/tmp/FishSim_Headline_Model_Execution_2026-11-09')
LEASE=Path('/tmp/FishSim_Native_Execution_Lease_2026-11-09.lock')
FREEZE_SHA='143ae45ac98cb385cdba9567b6262e499d48859f06a19374eb0fbc2b5638b414'
PLAN=Path('/tmp/FishSim_Headline_Model_Validation_Plan_2026-11-09_v2.json')
PLAN_SHA='458c09932f8712005c450c0b09dd0547c7375cd993f14bc6181ceb540a43de8d'
RUNTIMES={
 'historical':Path('/tmp/FishSim_Paper_Model_v4_Historical_Work/model'),
 'source-built':Path('/tmp/FishSim Paper Model v4 Rebuilt/model')}
RUNTIME_SHA={
 'historical':'ddf9cf3ad67834eb066deca1199cd25fcaf17612de31f699fc7ff72acee40fc5',
 'source-built':'d6c78c5860ba0aaacfb8c8ff03d5dcf6f499028d9580281386a2bb9d826ebeca'}
NATIVES={
 'historical':'eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558',
 'source-built':'cc21f00f355e1d25e8ecb48bd6aa50a7c9b63f909d921f4864a96e91d9ef2d4b'}
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):
 p=Path(p);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');q.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def live_group(pgid):
 found=[]
 for path in Path('/proc').iterdir():
  if not path.name.isdigit():continue
  try:
   fields=(path/'stat').read_text().rsplit(')',1)[1].split()
   if int(fields[2])==pgid and fields[0] not in ('Z','X'):found.append(int(path.name))
  except (OSError,ValueError,IndexError):continue
 return found
def terminate_and_join(process):
 try:os.killpg(process.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:process.wait(timeout=5)
 except subprocess.TimeoutExpired:
  try:os.killpg(process.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  process.wait()
 # A direct child frontend can itself own a worker. Do not release the task
 # lease until every non-zombie member of this task-only group has stopped.
 deadline=time.monotonic()+5
 while live_group(process.pid):
  if time.monotonic()>deadline:
   try:os.killpg(process.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  time.sleep(.1)
def specification():
 entries=[]
 for kind in RUNTIMES:
  entries.append(dict(name=kind+'_zero108',kind=kind,mode='--check',setting=None,duration_T=0.,native_steps=0,native_zero_constructions=108,output=None))
 for kind in RUNTIMES:
  for setting,duration in (('headline',4.),('joint',2.)):
   name=kind+'_'+setting+'_'+str(duration).replace('.','p')+'T'
   entries.append(dict(name=name,kind=kind,mode='--quick',setting=setting,duration_T=duration,native_steps=round(duration/.00125)*2,native_zero_constructions=0,output=str(EXECUTION/name),role='headline_core'))
 entries.append(dict(name='source-built_frontend_reuse_0p5T',kind='source-built',mode='--quick',setting='headline',duration_T=.5,native_steps=800,native_zero_constructions=0,output=str(EXECUTION/'source-built_frontend_reuse_0p5T'),role='frontend_reuse_path'))
 return entries
def verify_sources(approval):
 assert sha(CANDIDATE/'CANDIDATE_FREEZE.json')==FREEZE_SHA
 freeze=read(CANDIDATE/'CANDIDATE_FREEZE.json')
 for name,digest in freeze['files'].items():assert sha(CANDIDATE/name)==digest,name
 assert sha(PLAN)==PLAN_SHA
 assert approval['approved'] is True and approval['scope']=='headline_model_engineering_validation_only'
 assert approval['source_freeze_sha256']==FREEZE_SHA and approval['plan_sha256']==PLAN_SHA
 assert approval['driver_sha256']==sha(__file__)
 assert approval['maximum_zero_constructions']==216 and approval['maximum_native_steps']==20000 and approval['workers']==1
 assert approval['execution_root']==str(EXECUTION) and approval['task_lease']==str(LEASE)
 assert approval['sequence']==specification()
 assert approval['interface_source_review_sha256']==sha(CANDIDATE/'INTERFACE_SOURCE_REVIEW.json')
 for kind,runtime in RUNTIMES.items():
  assert sha(runtime/'REGIME_RUNTIME_DECLARATION.json')==RUNTIME_SHA[kind]
  assert approval['runtime_declarations'][kind]==RUNTIME_SHA[kind]
  d=read(runtime/'REGIME_RUNTIME_DECLARATION.json');assert d['actual_native_sha256']==NATIVES[kind]
  for relative,digest in d['runtime_files'].items():assert sha(runtime/relative)==digest,(kind,relative)
def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',action='store_true');p.add_argument('--approval',type=Path);a=p.parse_args()
 if a.plan:
  print(json.dumps(dict(source_freeze_sha256=FREEZE_SHA,plan_sha256=PLAN_SHA,driver_sha256=sha(__file__),sequence=specification(),maximum_zero_constructions=216,maximum_native_steps=20000,execution_root=str(EXECUTION),task_lease=str(LEASE)),indent=2));return
 assert a.approval and not EXECUTION.exists(),'Fresh approved execution only'
 approved=read(a.approval);verify_sources(approved)
 # Acquire the task-level lease OUTERMOST, before any subprocess/import/native
 # entrypoint. Parent owns this FD across all children and joins them serially.
 with LEASE.open('a+') as lease:
  fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  for runtime in RUNTIMES.values():assert not (runtime.parent/'zero_check').exists(),'Preserve any earlier actual initialization attempt'
  EXECUTION.mkdir();(EXECUTION/'logs').mkdir()
  state=dict(status='running',started=now(),pid=os.getpid(),approval_path=str(a.approval.resolve()),approval_sha256=sha(a.approval),driver_sha256=sha(__file__),task_lease=str(LEASE),source_freeze_sha256=FREEZE_SHA,completed=[],zero_constructions_completed=0,native_steps_completed=0,active=None)
  write(EXECUTION/'execution.json',state)
  environment=os.environ.copy();environment['PYTHONDONTWRITEBYTECODE']='1';environment['PYTHONUNBUFFERED']='1';environment.pop('PYTHONOPTIMIZE',None)
  def interrupted(signum,frame):raise KeyboardInterrupt('Validation parent interrupted; stopping its own process group before releasing task lease')
  signal.signal(signal.SIGTERM,interrupted)
  for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):environment[name]='1'
  zero_hashes={}
  try:
   for stage in specification():
    kind=stage['kind'];runtime=RUNTIMES[kind]
    # All216 actual starts must finish before ANY integration stage.
    if stage['mode']=='--quick':assert state['zero_constructions_completed']==216
    command=[sys.executable,'-B',str(CANDIDATE/'run_v6_example.py'),stage['mode'],'--package-root',str(PACKAGE),'--runtime',str(runtime),'--native-kind',kind]
    if stage['mode']=='--quick':command+=['--setting',stage['setting'],'--duration',str(stage['duration_T']),'--output',stage['output']]
    state['active']=dict(**stage,started=now());write(EXECUTION/'execution.json',state)
    print('START '+stage['name'],flush=True)
    started=time.monotonic();log=EXECUTION/'logs'/(stage['name']+'.log')
    with log.open('w') as output:
     process=subprocess.Popen(command,cwd=CANDIDATE,env=environment,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
     try:
      while process.poll() is None:
       write(EXECUTION/'heartbeat.json',dict(at=now(),parent_pid=os.getpid(),child_pid=process.pid,stage=stage['name'],wall_seconds=time.monotonic()-started,completed_steps=state['native_steps_completed'],completed_zero_constructions=state['zero_constructions_completed']))
       time.sleep(2)
     except BaseException:
      terminate_and_join(process);raise
     if process.returncode:
      terminate_and_join(process);raise subprocess.CalledProcessError(process.returncode,command)
     if live_group(process.pid):
      terminate_and_join(process);raise RuntimeError('Frontend exited while its native worker group remained active')
    zero=runtime.parent/'zero_check/ACTUAL_ZERO_STEP_EXAMPLE.json';seal=runtime.parent/'zero_check/ZERO_CHECK_SEAL.json'
    if stage['mode']=='--check':
     z=read(zero);assert z['status']=='passed' and z['native_steps']==0 and z['native_constructions']==108 and len(z['cases'])==108
     assert z['actual_native_sha256']==NATIVES[kind]
     zero_hashes[kind]={str(x):sha(x) for x in (zero,seal,runtime.parent/'zero_check/execution_request.json')}
     state['zero_constructions_completed']+=108
    else:
     for filename,digest in zero_hashes[kind].items():assert sha(filename)==digest,'Zero check unexpectedly rerun/changed'
     z=read(Path(stage['output'])/'REGIME_EXAMPLE_EXECUTION.json');assert z['status']=='passed' and z['cases']==2 and z['native_steps']==stage['native_steps']
     assert z['actual_native_sha256']==NATIVES[kind]
     state['native_steps_completed']+=z['native_steps']
    state['completed'].append(dict(**stage,wall_seconds=time.monotonic()-started,log_sha256=sha(log),zero_receipt_sha256=sha(zero),zero_seal_sha256=sha(seal)))
    state['active']=None;write(EXECUTION/'execution.json',state);print('PASS '+stage['name'],flush=True)
   assert state['zero_constructions_completed']==216 and state['native_steps_completed']==20000
   verify_sources(approved)
   state.update(status='passed',finished=now(),historical_evidence_modified=False,feeding_inference=False)
   write(EXECUTION/'execution.json',state);print(json.dumps(dict(status='passed',zero_constructions=216,native_steps=20000,receipt=str(EXECUTION/'execution.json'))),flush=True)
  except BaseException as error:
   state.update(status='failed_preserved_no_retry',finished=now(),error=repr(error),remaining_native_work_not_started=True)
   write(EXECUTION/'execution.json',state);raise
if __name__=='__main__':main()
