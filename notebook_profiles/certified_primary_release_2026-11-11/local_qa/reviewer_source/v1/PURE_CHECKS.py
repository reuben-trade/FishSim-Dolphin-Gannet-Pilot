"""Small synthetic-only negative contract checks. No child process or model."""
import copy,hashlib,importlib.util,json,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('qa_audit_pure',HERE/'AUDIT.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def rejected(f):
    try:f()
    except ValueError:return True
    raise AssertionError('Corruption unexpectedly accepted')
with tempfile.TemporaryDirectory(prefix='SYNTHETIC_local_QA_reviewer_') as td:
    runtime=Path(td);(runtime/'PRIMARY_RUNTIME.json').write_text('{}')
    r=dict(schema='primary_local_opt_in_v1',explicit_local_opt_in=True,independent_review=False,interface_files={'x':'y'},active_native_sha256=m.EB,runtime_declaration_sha256=m.sha(runtime/'PRIMARY_RUNTIME.json'),release_sha256='SYNTHETIC',stage='zero',output=str(runtime/'zero.json'),jobs=[],workers=1,maximum_native_steps=0,native_constructions=192)
    check=lambda v:m.local_request(v,'zero',runtime,runtime/'zero.json',{'x':'y'},'SYNTHETIC',[])
    check(r);n=1
    for key,value in [('approved',True),('schema','primary_future_engineering_authority_v1'),('independent_review',True),('explicit_local_opt_in',False),('workers',True),('maximum_native_steps',True),('native_constructions',191),('active_native_sha256','wrong'),('runtime_declaration_sha256','wrong'),('release_sha256','wrong'),('jobs',[{}]),('output',str(runtime/'different'))]:
        bad=copy.deepcopy(r);bad[key]=value;rejected(lambda:check(bad));n+=1
    m.bb_load();n+=1
    assert m.normal_argv(['/venv/bin/python','-B','/copy/run_primary_model.py','--check'])==m.normal_argv(['/copy/run_primary_model.py','--check']);n+=1
    assert m.normal_argv(['/venv/bin/python','-I','renderer.py'])!=m.normal_argv(['/venv/bin/python','renderer.py']);n+=1
    rejected(lambda:m.normal_argv(['script',7]));n+=1
    m.no_model()
print(json.dumps({'status':'passed','checks':n,'synthetic_only':True,'child_processes':0,'model_imports':0,'native_constructions':0,'native_steps':0,'leases':0}))
