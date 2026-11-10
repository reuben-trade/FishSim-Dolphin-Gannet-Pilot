"""Source-bound local replay permissions, closed until independent release."""
from __future__ import annotations
import os
from pathlib import Path
from primary_runtime import HERE,STUDY,SOURCE_FREEZE,ZERO_SHA,HISTORICAL,SOURCE_BUILT,interfaces,inventory,identity,read,sha,steps,verify_runtime,safe

def proof(entry,inside=None):
    path=Path(entry['path']);path=(inside/path).resolve() if inside else path.resolve()
    if inside and not path.is_relative_to(inside):raise RuntimeError('Release proof escapes interface')
    if sha(path)!=entry['sha256']:raise RuntimeError('Bound proof changed')
    return read(path)

def validate_release_artifact(kind,artifact,tests):
    if kind not in ('historical','source-built'):raise RuntimeError('Unknown artifact')
    expected=HISTORICAL if kind=='historical' else SOURCE_BUILT;digest=artifact.get('runtime_declaration_sha256')
    if artifact.get('active_native_sha256')!=expected or not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise RuntimeError('Release artifact/declaration differs')
    for name,p in tests.items():
        if p.get('status')!='passed' or p.get('interface_files')!=interfaces():raise RuntimeError('Release source review differs:'+name)
        if name!='source_review' and (p.get('active_native_sha256')!=expected or p.get('runtime_declaration_sha256')!=digest):raise RuntimeError('Cross-artifact or cross-declaration release proof')
    zero,short,full=(tests[k] for k in ('actual_zero_review','short4T_review','full36T_review'))
    if zero.get('native_constructions')!=192 or zero.get('native_steps')!=0 or zero.get('exact_case_names')!=[c['case_name'] for c in inventory()]:raise RuntimeError('Release needs all192 exact zero starts')
    expected_cases=[identity(39065501,71001,g,a)['case_name'] for g in ('coarse','fine') for a in ('D','G','DG')]
    for duration,p,cap in ((4,short,28800),(36,full,259200)):
        if p.get('exact_case_names')!=expected_cases or p.get('duration_T')!=duration or p.get('source_execution_native_steps')!=cap or p.get('exact_full_trajectory_and_event_replay') is not True:
            raise RuntimeError('Both grids/three arms need actual exact full-horizon engineering proof')

def validate_worker_binding(runtime_arg,output_arg,stage_arg,runtime,output,stage):
    if runtime_arg is not None and Path(runtime_arg).resolve()!=Path(runtime).resolve():raise RuntimeError('Worker runtime differs from authority')
    if output_arg is not None and Path(output_arg).resolve()!=Path(output).resolve():raise RuntimeError('Worker output differs from authority')
    if stage_arg is not None and stage_arg!=stage:raise RuntimeError('Worker stage differs from authority')

def validate_release(kind):
    path=HERE/'PRIMARY_MODEL_RELEASE.json'
    if not path.is_file():raise RuntimeError('PRIMARY native gate CLOSED; no artifact-specific full-horizon release')
    release=read(path);expected=HISTORICAL if kind=='historical' else SOURCE_BUILT
    if release.get('status')!='passed' or release.get('interface_files')!=interfaces() or release.get('source_freeze_sha256')!=SOURCE_FREEZE:
        raise RuntimeError('Full-model release source binding differs')
    artifact=release['artifacts'][kind]
    tests={name:proof(artifact[name],HERE) for name in ('source_review','actual_zero_review','short4T_review','full36T_review')}
    validate_release_artifact(kind,artifact,tests)
    return path,artifact

def context(runtime_arg=None,output_arg=None,stage_arg=None):
    authority_path=Path(os.environ.get('FISHSIM_PRIMARY_REQUEST','/nonexistent/PRIMARY_MODEL_CLOSED'))
    if not authority_path.is_file():raise RuntimeError('PRIMARY native gate CLOSED; no bounded request')
    request=read(authority_path);runtime=Path(os.environ['FISHSIM_PRIMARY_RUNTIME']).resolve();declaration=verify_runtime(runtime)
    if request.get('schema') not in ('primary_future_engineering_authority_v1','primary_local_opt_in_v1'):raise RuntimeError('Unknown execution request')
    engineering=request['schema']=='primary_future_engineering_authority_v1'
    if request.get('interface_files')!=interfaces() or request.get('runtime_declaration_sha256')!=sha(runtime/'PRIMARY_RUNTIME.json'):raise RuntimeError('Request runtime/interface differs')
    if request.get('active_native_sha256')!=declaration['active_native_sha256']:raise RuntimeError('Request active artifact differs')
    if engineering:
        if request.get('approved') is not True or request.get('primary192_complete_lease_released') is not True:raise RuntimeError('Future owner authority required')
        final=proof(request['primary_final_review']);metadata=proof(request['primary_metadata_review'])
        if (final.get('status')!='passed' or final.get('stage')!='final' or final.get('new_full_cases')!=192
                or final.get('independent_schools')!=16 or final.get('reused_discovery_cases_in_estimate')!=0
                or final.get('audit_source_sha256')!='8ff3eec0139784c175fcdfb1d5397478f91b0f23fa0d2b05501de22cd8d52cdf'
                or final.get('native_steps_by_review')!=0 or final.get('freeze_sha256')!=SOURCE_FREEZE):raise RuntimeError('Original full192 independentFINAL required')
        if (metadata.get('status')!='passed' or metadata.get('cases')!=192 or metadata.get('independent_school_clusters')!=16
                or metadata.get('sidecar_source_sha256')!='5cc43e3391ebd48d165fd0b7dd808317ae0a0a4139cdfa0ae032607b905472c3'
                or metadata.get('original_final_review_sha256')!=request['primary_final_review']['sha256']
                or metadata.get('execution_freeze_sha256')!=SOURCE_FREEZE):raise RuntimeError('Additional full192 metadata proof required')
        review=proof(request['independent_source_review'])
        if review.get('status')!='passed' or review.get('interface_files')!=interfaces():raise RuntimeError('Fresh independent source review required')
    else:
        release,_=validate_release(declaration['native_kind'])
        if (request.get('explicit_local_opt_in') is not True or request.get('independent_review') is not False or 'approved' in request
                or request.get('release_sha256')!=sha(release) or declaration['source_mode']!='production_snapshot'):
            raise RuntimeError('Local request needs certified production snapshot and explicit opt-in')
    stage=request.get('stage');output=Path(request['output']).resolve()
    if stage not in ('zero','run'):raise RuntimeError('Unknown native stage')
    validate_worker_binding(runtime_arg,output_arg,stage_arg,runtime,output,stage)
    safe(output,declaration['package'])
    if output==runtime or output.is_relative_to(runtime) or runtime.is_relative_to(output):raise RuntimeError('Runtime/output overlap')
    if stage=='zero':
        if request.get('maximum_native_steps')!=0 or request.get('native_constructions')!=192:raise RuntimeError('Zero gate requires exactly192 starts/zero steps')
    else:
        jobs=request['jobs'];keys={(j['case_name'],j['duration_T']) for j in jobs}
        if len(jobs)!=len(keys) or steps(jobs)!=request.get('maximum_native_steps') or len(jobs)>384:raise RuntimeError('Invalid finite run queue')
        if type(request.get('workers'))is not int or request['workers'] not in range(1,9):raise RuntimeError('Global worker count must be1..8')
        zero=proof(request['zero_receipt'])
        if zero.get('status')!='passed' or zero.get('native_constructions')!=192 or zero.get('native_steps')!=0 or zero.get('runtime_declaration_sha256')!=request['runtime_declaration_sha256'] or zero.get('active_native_sha256')!=declaration['active_native_sha256']:
            raise RuntimeError('Run needs this exact artifact/runtime’s separately completed192 zero starts')
        if engineering and any(j['duration_T']==36 for j in jobs):
            short=proof(request['short_replay_review'])
            if (short.get('status')!='passed' or short.get('interface_files')!=interfaces() or short.get('duration_T')!=4
                    or short.get('source_execution_native_steps')!=28800
                    or short.get('active_native_sha256')!=declaration['active_native_sha256']
                    or short.get('runtime_declaration_sha256')!=request['runtime_declaration_sha256']
                    or short.get('exact_full_trajectory_and_event_replay') is not True):raise RuntimeError('Full engineering needs prior actual both-grid4T replay acceptance')
    return runtime,declaration,authority_path,request

def runtime_root():return Path(os.environ['FISHSIM_PRIMARY_RUNTIME']).resolve()
def preparation_manifest():return read(runtime_root()/'PREPARATION_INDEX.json')['manifest']
# These are file-view paths only; no native constructor or authority is loaded.
if 'FISHSIM_PRIMARY_RUNTIME' in os.environ:
    _index=read(runtime_root()/'PREPARATION_INDEX.json')
    OLD_PREP=Path(_index['old_directory']);PREP_OUTPUT=Path(_index['new_directory'])

def require_approval(stage):
    _,_,_,request=context()
    expected='initialization' if request['stage']=='zero' else None
    if expected and stage!=expected:raise RuntimeError('Constructor stage differs')
    if not expected and stage not in ('smoke','feeding'):raise RuntimeError('Run constructor stage differs')
def require_case_permission(case,stage,output=None):
    runtime,_,_,request=context()
    exact=identity(case.school_seed,case.capture_seed,case.grid,case.presence)
    if exact['case_name']!=case.name:raise RuntimeError('Foreign case')
    if request['stage']=='zero':
        if stage!='initialization':raise RuntimeError('Zero constructor stage differs')
        return
    matching=[j for j in request['jobs'] if j['case_name']==case.name and ('smoke' if j['duration_T']==4 else 'feeding')==stage]
    if len(matching)!=1:raise RuntimeError('Constructor job not uniquely authorized')
    if output is not None and Path(output).resolve()!=Path(request['output']).resolve()/f"{matching[0]['duration_T']:g}T":raise RuntimeError('Physical output directory differs')
def require_run(case,duration,output):
    _,_,_,request=context()
    if request['stage']!='run' or not any(j['case_name']==case.name and j['duration_T']==duration for j in request['jobs']):raise RuntimeError('Exact case/horizon not authorized')
    require_case_permission(case,'smoke' if duration==4 else 'feeding',output)
def source_manifest():
    runtime,d,path,request=context();files={str(runtime/p):h for p,h in d['runtime_files'].items()};files[str(runtime/'PRIMARY_RUNTIME.json')]=sha(runtime/'PRIMARY_RUNTIME.json');files[str(path)]=sha(path)
    for name in ('zero_receipt','primary_final_review','primary_metadata_review','independent_source_review','short_replay_review'):
        if name in request:files[request[name]['path']]=request[name]['sha256']
    dispatch=os.environ.get('FISHSIM_PRIMARY_DISPATCH')
    if dispatch:files[dispatch]=sha(dispatch)
    return files
