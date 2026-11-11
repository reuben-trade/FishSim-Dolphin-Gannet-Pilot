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
# Focused V2 source-only startup cases; no kernel is started.
py='/SYNTHETIC/venv/bin/python';parent=100;pid=101
spec={'argv':[py,'-B','-m','ipykernel_launcher','-f','{connection_file}']}
start={'pid':pid,'ppid':parent,'executable':py,'argv':['-m','-f','/SYNTHETIC/connection.json']}
assert m.kernel_startup(start,pid,parent,spec,py);n+=1
for key,value in [('pid',102),('ppid',999),('executable','/wrong/python'),('argv',['-m','unidentified']),('argv',['-m','-f','relative.json'])]:
    bad=copy.deepcopy(start);bad[key]=value;rejected(lambda:m.kernel_startup(bad,pid,parent,spec,py));n+=1
bad_spec=copy.deepcopy(spec);bad_spec['argv'][3]='unknown_launcher';rejected(lambda:m.kernel_startup(start,pid,parent,bad_spec,py));n+=1
with tempfile.TemporaryDirectory(prefix='SYNTHETIC_local_QA_analysis_') as td:
    package=Path(td);script=package/'discovery_profile/build_figures.py';script.parent.mkdir();script.write_text('# SYNTHETIC source only')
    realsha=m.sha
    m.sha=lambda p:m.ANALYSIS_BUILDER_SHA if Path(p)==script else realsha(p)
    try:
        observed={'argv':[str(script)],'isolated':0,'executable':py}
        assert m.analysis_startup(observed,package,py);n+=1
        bad=copy.deepcopy(observed);bad['argv'].append('--extra');rejected(lambda:m.analysis_startup(bad,package,py));n+=1
        bad=copy.deepcopy(observed);bad['isolated']=1;rejected(lambda:m.analysis_startup(bad,package,py));n+=1
        bad=copy.deepcopy(observed);bad['argv']=[str(package/'unknown.py')];rejected(lambda:m.analysis_startup(bad,package,py));n+=1
    finally:m.sha=realsha
m.no_model()
# V3 executes the two actual source-roster statements, not a mirrored validator.
import ast
parsed=ast.parse((HERE/'AUDIT.py').read_text());fn=next(x for x in parsed.body if isinstance(x,ast.FunctionDef) and x.name=='audit')
idx=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.For) and isinstance(x.iter,ast.Call) and ast.unparse(x.iter)=="a['source_files'].items()")
block=ast.Module(body=fn.body[idx:idx+2],type_ignores=[]);ast.fix_missing_locations(block)
validate=compile(block,str(HERE/'AUDIT.py'),'exec');expected=m.read(m.PLAN/'CANDIDATE_FREEZE.json')['files']
assert m.sha(m.PLAN/'CANDIDATE_FREEZE.json')==m.PLAN_SHA
check=lambda roster:exec(validate,{'a':{'source_files':roster},'sha':m.sha,'read':m.read,'PLAN':m.PLAN,'need':m.need})
check(dict(expected));n+=1
bad=dict(expected);bad.pop(next(iter(bad)));rejected(lambda:check(bad));n+=1
bad=dict(expected);bad['UNKNOWN_EXTRA.json']='0'*64
unknown=lambda:exec(validate,{'a':{'source_files':bad},'sha':lambda p:'0'*64 if Path(p).name=='UNKNOWN_EXTRA.json' else m.sha(p),'read':m.read,'PLAN':m.PLAN,'need':m.need})
rejected(unknown);n+=1
bad=dict(expected);bad[next(iter(bad))]='0'*64;rejected(lambda:check(bad));n+=1
rejected(lambda:check(m.read(m.PLAN/'QA_PLAN.json')['source_files']));n+=1
print(json.dumps({'status':'passed' ,'checks':n,'synthetic_only':True,'child_processes':0,'model_imports':0,'native_constructions':0,'native_steps':0,'leases':0}))
