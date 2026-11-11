"""Closed saved-data auditor for one future local professor QA, never a launcher.

Reuses unchanged bb920 raw-case comparison; independently checks the distinct
local-request and guarded-process contract. No model import, lease or subprocess.
"""
from __future__ import annotations
import argparse,collections,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PLAN=Path('/home/venture/FishSim_Professor_Local_QA_Plan_2026-11-11')
PLAN_SHA='3db301fbd98768485dc35e1a89af43c617ed1232a6a46db8c767428ef1325469'
BB=Path('/tmp/FishSim_Primary_Replay_Independent_Review_2026-11-11.py')
BB_SHA='bb920d4fa7f29d70e31ea61f1f5757180b472ea887b4ce8a39ec94a78ecf4c22'
EB='eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'
FREEZE='253071467e55b4cdbe91f75ba1de3f1bb80d65344e9cba05aadb86bccb08da0b'
HELPERS={'replay_tools/primary_192/optional_native.py': 'e37de32618cbbdcfacc2e8dcecf8ac589ff4d1107e5b0b44c376a4c2cc82ece4', 'replay_tools/primary_192/check_primary_replay_v2.py': '55adee85ec494ac4125aaa3e051e5e73518876d7a8f6e9cf584e3600095fe7d4', 'replay_tools/primary_192/portable_seal_adapter.py': '37a93a74eb5fa9942a806ba3ce1153bc8a1ac5e9d4712404c2cb30e8b06a850d', 'replay_tools/primary_192/SOURCE_PINS.json': 'e058a0d8e79cb06630acd397741e975d86768f9a6e6e389a143b028aeeed9418', 'replay_tools/primary_192/certified_native_v1.py': '4cf4db76a5125349ecd78c7e04861535810e7a6a8c8ede15b0e330730bfb09d9', 'replay_tools/primary_192/notebook_session.py': '8e5e2d57cb04363fbafdfcd927ab8b68ba49db4f4f624692f33972f09c5c6417', 'replay_tools/primary_192/notebook_template.py': 'd86e724c68a2b5cf21694e852dde5ee9b36e8b078a631c21e574ffb478f19e9b'}
THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')
def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(e):
    need(isinstance(e,dict) and isinstance(e.get('path'),str) and isinstance(e.get('sha256'),str),'Missing actual proof')
    need(sha(e['path'])==e['sha256'],'Proof hash differs');return read(e['path'])
def no_model():need(not any(k=='cmodel' or k=='fish_sim' or k.startswith('fish_sim.') for k in sys.modules),'Model import forbidden')
def bb_load():
    need(sha(BB)==BB_SHA,'Original independent raw auditor changed')
    spec=importlib.util.spec_from_file_location('_local_qa_exact_bb920',BB);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def local_request(r,stage,runtime,output,interfaces,release,jobs,zero=None):
    need(r.get('schema')=='primary_local_opt_in_v1' and r.get('explicit_local_opt_in') is True and r.get('independent_review') is False and 'approved' not in r,'Actual local opt-in, not an authority, required')
    need(r.get('stage')==stage and r.get('interface_files')==interfaces and r.get('active_native_sha256')==EB and r.get('runtime_declaration_sha256')==sha(runtime/'PRIMARY_RUNTIME.json') and r.get('release_sha256')==release and Path(r['output']).resolve()==output,'Local request binding differs')
    need(r.get('jobs')==jobs and type(r.get('maximum_native_steps')) is int and r['maximum_native_steps']==(0 if stage=='zero' else 28800) and type(r.get('native_constructions')) is int and r['native_constructions']==(192 if stage=='zero' else 6),'Local finite queue differs')
    need(type(r.get('workers')) is int and r['workers']==(1 if stage=='zero' else 6),'Local worker count differs')
    if stage=='run':need(r.get('zero_receipt')=={'path':str(zero),'sha256':sha(zero)},'Run zero proof differs')

def normal_argv(v):
    need(isinstance(v,list) and all(isinstance(x,str) for x in v),'Recorded argv required')
    if v and ('python' in Path(v[0]).name):v=v[1:]
    return [x for x in v if x=='-I' or x!='-B']

def guards(logdir,config_path,guard_file,kernel_parent,interface,runtime,work):
    cfg=read(config_path);expected_guard=sha(PLAN/'qa_startup_guard.py');need(sha(guard_file)==expected_guard,'Copied guard differs')
    template=read(PLAN/'GUARD_CONFIG.TEMPLATE.json')
    for k in ('schema','deny_author_roots','allow_dependency_roots','append_dependency_sites','blocked_probe_path'):need(cfg.get(k)==template[k],'Guard configuration scope differs:'+k)
    need(cfg.get('enabled') is True and Path(cfg['audit_directory']).resolve()==logdir,'Guard not actually enabled')
    logs={};startup={}
    for p in logdir.glob('*.jsonl'):
        rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()];need(rows,'Empty guard log')
        need(all(type(x.get('pid')) is int and x['pid']==int(p.stem) for x in rows),'Guard PID/file identity differs')
        starts=[x for x in rows if x.get('event')=='guard_loaded'];need(len(starts)==1,'One startup per guarded PID required')
        s=starts[0];need(s.get('guard_sha256')==expected_guard and s.get('config_sha256')==sha(config_path) and s.get('isolated')==0 and s.get('optimize')==0,'Guard startup source/config/flags differ')
        logs[s['pid']]=rows;startup[s['pid']]=s
    need(len(startup)==12,'Exactly twelve guarded Python startups required')
    roles=collections.Counter();native_pids=[];kernel=None
    for pid,s in startup.items():
        a=s['argv'];text=' '.join(a)
        if 'ipykernel_launcher' in text:role='kernel';kernel=pid;need(s['ppid']==kernel_parent,'Kernel coordinator PPID differs')
        elif Path(a[0]).name=='run_primary_model.py':role='cli';need(Path(a[0]).resolve()==interface/'run_primary_model.py','Foreign CLI')
        elif Path(a[0]).name=='primary_worker.py':
            need(Path(a[0]).resolve()==interface/'primary_worker.py','Foreign worker');need('--mode' in a,'Worker mode missing');mode=a[a.index('--mode')+1];need(mode in ('zero','run'),'Unexpected native worker mode');role='zero' if mode=='zero' else 'integration';native_pids.append(pid)
        elif Path(a[0]).name=='check_primary_replay_v2.py':role='checker';need(Path(a[0]).resolve()==interface.parents[1]/'replay_tools/primary_192/check_primary_replay_v2.py','Foreign owner checker')
        else:raise ValueError('Unexpected guarded role:'+text)
        roles[role]+=1
    def arg(a,k):
        need(a.count(k)==1 and a.index(k)+1<len(a),'Missing or duplicated argv field:'+k);return a[a.index(k)+1]
    modes=[];indices=[]
    for pid,s in startup.items():
        a=s['argv'];name=Path(a[0]).name
        if name in ('run_primary_model.py','primary_worker.py','check_primary_replay_v2.py'):
            need(Path(arg(a,'--runtime')).resolve()==runtime,'Recorded worker/CLI runtime differs')
            need('--authority' not in a and '--all-ensemble' not in a,'Nonlocal or expanded model route')
        if name=='run_primary_model.py':
            need(Path(arg(a,'--package-root')).resolve()==interface.parents[1] and arg(a,'--native-kind')=='historical','Recorded CLI package/artifact differs')
            selected=[k for k in ('--prepare','--check','--run') if k in a];need(len(selected)==1,'Exactly one CLI stage required');modes+=selected
        if name=='primary_worker.py':
            mode=arg(a,'--mode');out=work/'zero192.json' if mode=='zero' else work/'first-world-4T'
            need(Path(arg(a,'--output')).resolve()==out and '--lease-fd' in a,'Recorded native output/lease binding differs')
            if mode=='run':indices.append(int(arg(a,'--job-index')))
    need(sorted(modes)==['--check','--prepare','--run'] and sorted(indices)==list(range(6)),'One CLI per stage and six unique worker jobs required')
    need(roles=={'kernel':1,'cli':3,'zero':1,'integration':6,'checker':1},'Guarded role inventory differs')
    requests=[];isolated=[];denials=[];probes=[];measured=[]
    for pid,rows in logs.items():
        for e in rows:
            if e.get('event')=='python_child_request':
                if '-I' in e['argv']:isolated.append(e)
                else:requests.append(e)
            elif e.get('event')=='denied_author_read':denials.append(e)
            elif e.get('event')=='blocked_probe_passed':probes.append(e)
            elif e.get('event')=='denied_model_import':raise ValueError('Denied model import')
            elif e.get('event')=='model_import':
                need(pid in native_pids,'Model import outside seven native workers')
                if e.get('path') is not None:
                    p=Path(e['path']).resolve();need(p.is_relative_to(runtime/'lib'),'Model import escapes fresh runtime')
                    if e.get('module') in ('fish_sim.cmodel','cmodel'):
                        need(p==runtime/'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so' and sha(p)==EB,'Measured native artifact differs');measured.append(pid)
    need(len(isolated)==2,'Exactly two explicitly excluded renderer -I children expected')
    need(len(requests)==11,'Exactly eleven guarded child dispatches required')
    available=set(startup)-{kernel}
    for e in requests:
        matches=[pid for pid in available if startup[pid]['ppid']==e['pid'] and normal_argv(startup[pid]['argv'])==normal_argv(e['argv'])]
        need(len(matches)==1,'Popen/startup PPID/argv must match uniquely');available.remove(matches[0])
        need('--authority' not in e['argv'],'Model path received an authority argument')
    need(not available,'Unreconciled child startup')
    need(len(denials)==len(probes)==1 and denials[0]['pid']==probes[0]['pid']==kernel and denials[0].get('expected_probe') is True and denials[0].get('path')==probes[0].get('path')==cfg['blocked_probe_path'],'One intentional kernel probe only; no other denied reads')
    need(probes[0]['monotonic']<min(startup[p]['monotonic'] for p in native_pids),'Probe must precede native worker startup')
    need(set(measured)==set(native_pids),'Every native worker needs a non-null measured cmodel path; None is not measurement')
    return {'guarded_processes':12,'roles':dict(roles),'reconciled_child_dispatches':11,'excluded_renderer_children':2,'intentional_denials':1,'unexpected_denials':0,'measured_cmodel_worker_pids':sorted(set(measured)),'guard_log_sha256':{p.name:sha(p) for p in sorted(logdir.glob('*.jsonl'))}}

def audit(authority_path,terminal_path):
    no_model();need(sha(PLAN/'CANDIDATE_FREEZE.json')==PLAN_SHA,'QA source plan changed')
    for n,h in read(PLAN/'CANDIDATE_FREEZE.json')['files'].items():need(sha(PLAN/n)==h,'QA plan member changed')
    a=read(authority_path);need(a.get('schema')=='professor_local_notebook_qa_authority_v1' and a.get('approved') is True and a.get('recorded_by')=='/root' and a.get('separate_from_576000_engineering') is True,'Fresh separate ROOT QA authority required')
    need((a.get('maximum_native_constructions'),a.get('maximum_native_steps'),a.get('native_cases'),a.get('workers'))==(198,28800,6,6),'QA finite scope differs')
    need(a.get('both_artifact_full36_independent_passed') is True and a.get('all_prior_native_terminal_and_lease_released') is True,'Prerequisites not passed')
    for n,h in a['source_files'].items():need(sha(PLAN/n)==h,'Actual QA source binding differs')
    need(set(a['source_files'])==set(read(PLAN/'QA_PLAN.json')['source_files']),'QA source list differs')
    for entry in a['prerequisite_files'].values():bound(entry)
    bound(a['copied_package_receipt']);cfg=bound(a['guard_config'])
    package=Path(a['relocated_package']).resolve();control=Path(a['control_directory']).resolve();guard=Path(a['guard_directory']).resolve();interface=package/'model_examples/primary_192'
    owner=read(control/'OWNER_QA_RECEIPT.json');need(owner.get('status')=='owner_complete_pending_independent_guard_and_scope_review' and owner.get('independent_claim') is False and owner.get('authority_sha256')==sha(authority_path) and owner.get('native_constructions')==198 and owner.get('native_steps')==28800,'Actual owner completion required')
    terminal=read(terminal_path);need(terminal.get('schema')=='professor_local_qa_terminal_witness_v1' and terminal.get('status')=='complete' and terminal.get('same_session_terminal_observed') is True and type(terminal.get('owner_tool_session_id')) is int and terminal['owner_tool_session_id']>0 and type(terminal.get('exit_code')) is int and terminal['exit_code']==0 and terminal.get('all_children_joined') is True and terminal.get('canonical_lease_released') is True,'Actual SAME terminal/joined/lease-free proof required')
    need(terminal.get('authority_sha256')==sha(authority_path) and terminal.get('owner_receipt_sha256')==sha(control/'OWNER_QA_RECEIPT.json') and terminal.get('native_constructions')==198 and terminal.get('native_steps')==28800 and terminal.get('recorded_by') in ('/root','/root/sweep_design','/root/paper_update'),'Terminal bindings differ')
    need(all(terminal.get('numeric_environment',{}).get(k)=='1' for k in THREADS) and terminal.get('PYTHONOPTIMIZE_unset') is True,'Actual numeric environment proof required')
    need(terminal.get('argv')==[a['analysis_python'],'-B',str(PLAN/'run_notebook_once.py'),'--execute','--authority',str(authority_path)],'Actual coordinator argv differs')
    work=Path(owner['local_work']).resolve();runtime=work/'runtime';output=work/'first-world-4T';zero=work/'zero192.json';dispatch=work/'first-world-4T.dispatch.json';request_path=work/'first-world-4T.local_request.json';d=read(runtime/'PRIMARY_RUNTIME.json');bb=bb_load()
    interfaces=read(interface/'SOURCE_PINS.json')['interface_files'] if (interface/'SOURCE_PINS.json').exists() else read(package/'replay_tools/primary_192/SOURCE_PINS.json')['interface_files']
    for n,h in interfaces.items():need(sha(interface/n)==h,'e6 interface changed')
    for rel,h in HELPERS.items():need(sha(package/rel)==h,'Reviewed helper source changed:'+rel)
    book=read(control/'EXECUTED_LOCAL_QA.ipynb');codes=[c for c in book['cells'] if c.get('cell_type')=='code'];canonical=[c for c in read(package/'main.ipynb')['cells'] if c.get('cell_type')=='code']
    text=lambda c: ''.join(c['source']) if isinstance(c['source'],list) else c['source']
    need(len(codes)==8 and len(canonical)==7 and [text(c) for c in codes[1:]]==[text(c) for c in canonical] and [c.get('execution_count') for c in codes]==list(range(1,9)),'Exactly one probe plus seven canonical executed code cells required')
    need('blocked_read_probe' in text(codes[0]) and not any(o.get('output_type')=='error' for c in codes for o in c.get('outputs',[])),'Actual notebook probe/errors differ')
    need(interfaces==read(bb.PLAN/'SOURCE_AND_BUDGET_BINDINGS.json')['interface_files'],'Original accepted e6 interface required')
    for rel,h in d['runtime_files'].items():need(sha(bb.inside(runtime,rel))==h,'Runtime source changed')
    need(d.get('interface_files')==interfaces and d.get('active_native_sha256')==EB and d.get('native_kind')=='historical' and d.get('source_mode')=='production_snapshot' and d.get('source_freeze_sha256')==FREEZE and Path(d['package']).resolve()==package,'Actual runtime/artifact/source scope differs')
    need(sha(runtime/'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so')==EB,'Active binary differs')
    refs=read(interface/'REFERENCE_MANIFEST.json');need(len(refs['files'])==303 and d.get('reference_manifest_sha256')==sha(interface/'REFERENCE_MANIFEST.json'),'Golden closure differs')
    for rel,h in refs['files'].items():
        need(rel.startswith('references/'),'Unknown reference path');need(sha(bb.inside(runtime/'reference_inputs',rel.removeprefix('references/')))==h,'Golden reference changed')
    need([x['case_name'] for x in read(runtime/'reference_inputs/ACTUAL_ZERO_STEP.json')['rows']]==[x['case_name'] for x in bb.identities()],'Exact192 golden identities required')
    cert=interface/'PRIMARY_MODEL_RELEASE.json';need(sha(cert)==a['actual_certificate_sha256'] and owner.get('actual_certificate_sha256')==sha(cert),'Certificate binding differs')
    release=read(cert);need(release.get('status')=='passed' and release.get('interface_files')==interfaces and release.get('source_freeze_sha256')==FREEZE,'Actual release source differs')
    for kind,record in release['artifacts'].items():
        need(kind in bb.ARTIFACTS and record['active_native_sha256']==bb.ARTIFACTS[kind],'Certificate artifact differs')
        for name in ('source_review','actual_zero_review','short4T_review','full36T_review'):
            entry=record[name];p=bb.inside(interface,entry['path']);need(sha(p)==entry['sha256'],'Release proof changed');v=read(p);need(v.get('status')=='passed' and v.get('interface_files')==interfaces,'Release proof not passed')
            if name!='source_review':need(v.get('review_source_sha256')==BB_SHA and v.get('active_native_sha256')==bb.ARTIFACTS[kind] and v.get('runtime_declaration_sha256')==record['runtime_declaration_sha256'],'Release independent artifact binding differs')
            if name=='actual_zero_review':need(v.get('stage')=='zero' and v.get('native_constructions')==192 and type(v.get('native_steps')) is int and v['native_steps']==0 and v.get('exact_case_names')==[x['case_name'] for x in bb.identities()],'Release actual192-zero proof differs')
            if name=='short4T_review':bb.check_short_acceptance(v,kind,interfaces,record['runtime_declaration_sha256'])
            if name=='full36T_review':need(v.get('schema')=='primary_replay_independent_saved_data_review_v1' and v.get('stage')=='replay' and v.get('duration_T')==36 and v.get('source_execution_native_steps')==259200 and v.get('independent_review_claimed') is True and v.get('exact_full_trajectory_and_event_replay') is True and v.get('exact_case_names')==[x['case_name'] for x in bb.first_world()],'Release actual full36 proof differs')
    need(set(release['artifacts'])==set(bb.ARTIFACTS),'Both artifacts required')
    binding=read(package/'NOTEBOOK_RELEASE_BINDINGS.json')['native_release'];need(binding.get('status')=='ACTUAL_BOTH_ARTIFACTS_RELEASE_ACCEPTED' and binding.get('certificate_sha256')==sha(cert),'Notebook release binding differs')
    accepted=read(package/binding['root_release_acceptance_path']);need(sha(package/binding['root_release_acceptance_path'])==binding['root_release_acceptance_sha256'] and binding['acceptance_contract'].get('status')=='passed' and all(accepted.get(k)==v for k,v in binding['acceptance_contract'].items()),'Root release acceptance differs')
    r=read(request_path);zrequest=read(work/'zero192.json.local_request.json');jobs=[dict(x,duration_T=4.) for x in bb.first_world()]
    local_request(zrequest,'zero',runtime,zero,interfaces,sha(cert),[]);local_request(r,'run',runtime,output,interfaces,sha(cert),jobs,zero)
    z=read(zero);need(z.get('schema')=='primary_model_actual_zero192_v1' and z.get('status')=='passed' and z.get('exact_case_names')==[x['case_name'] for x in bb.identities()] and z.get('native_constructions')==192 and type(z.get('native_steps')) is int and z['native_steps']==0 and z.get('active_native_sha256')==EB and z.get('runtime_declaration_sha256')==sha(runtime/'PRIMARY_RUNTIME.json'),'Actual local192 assertion-success receipt differs')
    execution=read(output/'execution.json');need(execution.get('status')=='complete_pending_independent_replay_review' and (execution.get('jobs'),execution.get('workers'),execution.get('native_steps'),execution.get('maximum_native_steps'))==(6,6,28800,28800) and execution.get('request_sha256')==sha(request_path) and execution.get('dispatch_sha256')==sha(dispatch) and execution.get('active_native_sha256')==EB and execution.get('runtime_declaration_sha256')==sha(runtime/'PRIMARY_RUNTIME.json'),'Local execution differs')
    review=object.__new__(bb.Review);review.runtime=runtime;review.duration=4;review.request=r;review.request_path=request_path;review.declaration=d;review.kind='historical'
    folder=output/'4T/cases';need({p.name for p in folder.iterdir()}=={x['case_name'] for x in bb.first_world()},'Exact six local cases required')
    cases=[review.case(folder/x['case_name'],x,dispatch) for x in bb.first_world()]
    need(sum(x['native_steps'] for x in cases)==28800 and execution['case_completion_sha256']=={'4T/'+x['case']:x['completion_sha256'] for x in cases},'Independent local raw/native accounting differs')
    local=read(work/'LOCAL_REPLAY_RECEIPT.json');need(local.get('status')=='completed_explicit_professor_local_replay' and (local.get('cases'),local.get('duration_T'),local.get('zero_constructions'),local.get('integration_constructions'),local.get('model_steps'))==(6,4,192,6,28800) and local.get('source_execution_sha256')==sha(output/'execution.json') and local.get('active_native_sha256')==EB,'Local facade completion differs')
    checked=read(work/'owner-4T.json');need(sha(work/'owner-4T.json')==local.get('owner_receipt_sha256') and checked.get('status')=='passed' and checked.get('independent_review_claimed') is False and checked.get('owner_checker_sha256')==sha(package/'replay_tools/primary_192/check_primary_replay_v2.py'),'Versioned owner check missing')
    need(local.get('certificate_sha256')==sha(cert) and owner.get('local_receipt_sha256')==sha(work/'LOCAL_REPLAY_RECEIPT.json') and checked.get('interface_files')==interfaces and checked.get('exact_case_names')==[x['case_name'] for x in bb.first_world()] and checked.get('duration_T')==4 and checked.get('source_execution_native_steps')==28800 and checked.get('runtime_declaration_sha256')==sha(runtime/'PRIMARY_RUNTIME.json') and checked.get('active_native_sha256')==EB and checked.get('operational_adapter_version')==2,'Owner/local artifact/source/horizon proof differs')
    process=guards(Path(cfg['audit_directory']).resolve(),Path(a['guard_config']['path']),guard/'sitecustomize.py',terminal['coordinator_pid'],interface,runtime,work)
    no_model();return dict(status='passed',schema='professor_local_QA_independent_saved_data_review_v1',audit_source_sha256=sha(__file__),bb920_sha256=BB_SHA,authority_sha256=sha(authority_path),terminal_sha256=sha(terminal_path),owner_QA_sha256=sha(control/'OWNER_QA_RECEIPT.json'),certificate_sha256=sha(cert),runtime_declaration_sha256=sha(runtime/'PRIMARY_RUNTIME.json'),native_constructions=198,native_steps=28800,native_steps_by_review=0,model_imports_by_review=0,lease_acquisitions_by_review=0,exact_six_case_raw_reviews=cases,guard_review=process,zero_scope='Pinned verifier internal exact assertions witnessed by actual local receipt, guarded execution and terminal; not a second independent array measurement',new_scientific_inference=False)

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--authority',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();need(not a.receipt.exists(),'Preserve existing review');v=audit(a.authority.resolve(),a.terminal.resolve());a.receipt.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');print(json.dumps({'status':'passed','receipt_sha256':sha(a.receipt)}))
if __name__=='__main__':main()
