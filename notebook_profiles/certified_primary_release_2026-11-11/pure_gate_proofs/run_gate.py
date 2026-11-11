import argparse,hashlib,importlib.abc,json,os,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--deny-source-candidate',action='store_true');a=p.parse_args();root=a.root.resolve()
class DeniedProcess(RuntimeError):pass
class DenyModel(importlib.abc.MetaPathFinder):
 def __init__(self):self.attempts=[]
 def find_spec(self,fullname,path=None,target=None):
  if fullname=='fish_sim'or fullname.startswith('fish_sim.')or fullname=='cmodel':self.attempts.append(fullname);raise RuntimeError('Model import denied in actual-certificate gate test')
blocked=DenyModel();sys.meta_path.insert(0,blocked);reads=[];commands=[]
deny=[Path(v)for v in ['/home/venture/uwa/complex-systems/FishSim-RL','/home/venture/FishSim_Independent_Validation_2026-11-10','/home/venture/FishSim-Dolphin-Gannet-Pilot','/home/venture/FishSim Final Publication Candidate 2026-11-11','/home/venture/FishSim_Primary_Replay_Engineering_2026-11-11','/home/venture/FishSim_Native_Facade_Draft_2026-11-11']]
if a.deny_source_candidate:deny.append(Path('/home/venture/FishSim Certified Release Candidate 2026-11-11'))
def guard(event,args):
 if event=='subprocess.Popen':commands.append(args[1]);raise DeniedProcess('Pure actual-release test prohibits child execution')
 if event not in ('open','os.listdir','os.scandir')or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
 path=Path(os.fsdecode(args[0])).resolve()
 if any(path==base or path.is_relative_to(base)for base in deny):reads.append(str(path));raise RuntimeError('Original author/source read denied:'+str(path))
sys.addaudithook(guard);sys.path.insert(0,str(root))
from replay_tools.primary_192 import certified_native_v1 as facade
from replay_tools.primary_192 import optional_native
from replay_tools.primary_192.notebook_template import verify
b=json.loads((root/'NOTEBOOK_RELEASE_BINDINGS.json').read_text());t=b['notebook_template'];logical=verify(root/'main.ipynb',root/t['path'],t['configuration_cell_id'],t['logical_sha256']);assert logical['settings']['RUN_NATIVE']is False
for key in ('IPYTHONDIR','JUPYTER_RUNTIME_DIR','JUPYTER_PATH'):os.environ.pop(key,None)
cert=root/'model_examples/primary_192/PRIMARY_MODEL_RELEASE.json';before=hashlib.sha256(cert.read_bytes()).hexdigest();assert before=='7a1461e4ee2f382d285c6421568b6877ad0b5c7ccdd3c3f3b6c3d03727b5db98'
proofs={kind:facade.validate_release(root,kind)for kind in ('historical','source-built')}
plans={}
for kind in proofs:
 for duration in [4,36]:
  plan=facade.argument_plan(root,kind=kind,duration=duration,work_root=Path(__file__).parent/('not_created_'+kind+str(duration)))
  assert plan['cases']==6 and plan['maximum_native_steps']==(28800 if duration==4 else 259200)
  assert all('--authority'not in row and'--all-ensemble'not in row for row in plan['commands'])
  plans[kind+'_'+str(duration)]=plan
# The real positive source path must reach its ordinary finite first command,
# which the audit hook rejects BEFORE process creation. No fake certificate.
try:facade.run(root,work_root=Path(__file__).parent/('no_run_'+root.name.replace(' ','_')))
except DeniedProcess:pass
else:raise AssertionError('Native route did not stop at denied process boundary')
assert len(commands)==1 and '--prepare'in commands[0]
# Actual-certificate positive state must not open the legacy headless route.
os.environ['IPYTHONDIR']=str(root/'.headless/ipython')
try:facade.run(root)
except RuntimeError as error:assert 'saved-analysis headless context'in str(error)
else:raise AssertionError('Legacy headless route accepted with actual certificate')
assert len(commands)==1;os.environ.pop('IPYTHONDIR')
assert not reads and not blocked.attempts and not any(n=='fish_sim'or n.startswith('fish_sim.')or n=='cmodel'for n in sys.modules)
assert hashlib.sha256(cert.read_bytes()).hexdigest()==before
result=dict(status='passed_actual_certificate_pure_gate_only',root=str(root),actual_certificate_sha256=before,actual_both_artifacts_validated=proofs,structural_plans=plans,normal_actual_native_path_first_command_denied=commands,legacy_actual_positive_context_denied=True,space_path=True,source_candidate_denied=a.deny_source_candidate,original_author_source_reads=reads,model_import_attempts=blocked.attempts,kernel_starts=0,subprocesses_started=0,native_constructions=0,native_steps=0,leases=0,compilers=0,certificate_and_proofs_unchanged=True,scope='Actual accepted certificate and copiedrelativeproofs; bothgate/plans pass. No model subprocess was started. This is not actual professor local notebook QA.')
a.receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],root=str(root),plans=4,actual_positive_process_boundary_denied=True,model_steps=0,original_reads=0)))
