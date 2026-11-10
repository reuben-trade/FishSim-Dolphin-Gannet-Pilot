"""Saved-data operational seal adapter; no author-study gates or native calls.

The original physical audit body is retained. Its one seal import resolves here,
where the complete runtime is reconstructed from accepted immutable inputs and
its actual request/dispatch chain, instead of recomputing an author-directory
preparation inventory in a relocated execution view.
"""
from __future__ import annotations
import hashlib,json,os
from contextlib import contextmanager
from pathlib import Path

CONTEXT=None

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()

def safe_member(folder,name):
    if not isinstance(name,str) or not name or Path(name).is_absolute():raise RuntimeError('Unsafe sealed member')
    target=(Path(folder)/name).resolve()
    if not target.is_relative_to(Path(folder).resolve()):raise RuntimeError('Sealed member escapes case')
    return target

@contextmanager
def request_environment(runtime,request,dispatch):
    values={'FISHSIM_PRIMARY_RUNTIME':str(runtime),'FISHSIM_PRIMARY_REQUEST':str(request),'FISHSIM_PRIMARY_DISPATCH':str(dispatch)}
    old={k:os.environ.get(k) for k in values};os.environ.update(values)
    try:yield
    finally:
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v

def reconstruct_runtime(pr,runtime,declaration):
    """Reconstruct every declared file hash from accepted portable source bytes."""
    package=Path(declaration['package']).resolve()
    saved=pr.load_accepted_snapshot(package,declaration['snapshot_manifest_file'])
    if declaration['source_mode']!='production_snapshot' or pr.sha(saved.path)!=declaration['snapshot_manifest_sha256']:raise RuntimeError('Accepted snapshot/declaration differs')
    if str(saved.path.parent)!=declaration['snapshot_root']:raise RuntimeError('Snapshot root differs')
    inputs=read(pr.HERE/'MODEL_INPUTS.json');refs=read(pr.HERE/'REFERENCE_MANIFEST.json')
    if inputs['source_freeze_sha256']!=pr.SOURCE_FREEZE or len(inputs['primary_sources'])!=2127:raise RuntimeError('Original source scope differs')
    if refs['input_spec_sha256']!=sha(pr.HERE/'MODEL_INPUTS.json'):raise RuntimeError('Reference source binding differs')
    frozen=read(package/'INPUT_MANIFEST_2026-11-10_D24.json')['files']
    expected={str(Path(p).relative_to('frozen_model')):h for p,h in frozen.items() if p.startswith('frozen_model/')}
    mapping={original:str(runtime/pr.relative(original)) for original in inputs['primary_sources']}
    native_original=str(pr.ORIGINAL/'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so')
    mapping[native_original]=str(runtime/'historical_reference/cmodel.cpython-312-x86_64-linux-gnu.so')
    for original,h in inputs['primary_sources'].items():
        if saved.manifest['sources'].get(original)!=h:raise RuntimeError('Accepted source crosswalk differs:'+original)
        source=saved.path_for(h);rel=str(pr.relative(original))
        if rel in pr.RELOCATED:expected[rel]=digest(pr.relocate(read(source),mapping))
        else:expected[rel]=h
    for p,h in refs['files'].items():
        expected[str(Path('reference_inputs')/Path(p).relative_to('references'))]=h
    native='lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so'
    expected[native]=declaration['active_native_sha256']
    expected['historical_reference/cmodel.cpython-312-x86_64-linux-gnu.so']=pr.HISTORICAL
    prep=pr.relocate(inputs['preparation'],mapping)
    prep['old_directory']=str(runtime/pr.relative(inputs['preparation']['old_directory']))
    prep['new_directory']=str(runtime/pr.relative(inputs['preparation']['new_directory']))
    expected['PREPARATION_INDEX.json']=digest(prep)
    if read(runtime/'PREPARATION_INDEX.json')!=prep:raise RuntimeError('Prepared-school index differs')
    for name in pr.INTERFACE:expected[str(pr.STUDY/name)]=sha(pr.HERE/name)
    builder,bproof=pr.derive_builder((runtime/pr.STUDY/'build.py').read_text())
    runner,rproof=pr.derive_runner((runtime/pr.STUDY/'physical_run.py').read_text())
    expected[str(pr.STUDY/'primary_build.py')]=hashlib.sha256(builder.encode()).hexdigest()
    expected[str(pr.STUDY/'primary_execution.py')]=hashlib.sha256(runner.encode()).hexdigest()
    if declaration['builder_proof']!=bproof or declaration['runner_proof']!=rproof:raise RuntimeError('Unchanged constructor/physical derivation differs')
    if declaration['runtime_files']!=expected:
        missing=set(expected)-set(declaration['runtime_files']);extra=set(declaration['runtime_files'])-set(expected)
        changed=[p for p in expected.keys()&declaration['runtime_files'].keys() if expected[p]!=declaration['runtime_files'][p]]
        raise RuntimeError('Runtime reconstruction differs:'+str(dict(missing=sorted(missing),extra=sorted(extra),changed=changed)))
    return dict(source_bindings=2127,runtime_files=len(expected),reference_files=len(refs['files']),snapshot_manifest_sha256=sha(saved.path),preparation_index_sha256=digest(prep),original_source_freeze_sha256=pr.SOURCE_FREEZE,builder_proof=bproof,runner_proof=rproof)

def resolve_bound_record(manifest,digest_value,kind):
    candidates=[]
    for name,h in manifest.items():
        if h!=digest_value:continue
        p=Path(name)
        if sha(p)!=h:raise RuntimeError('Bound '+kind+' changed')
        value=read(p)
        if kind=='request' and value.get('schema') in ('primary_future_engineering_authority_v1','primary_local_opt_in_v1'):candidates.append(p)
        if kind=='dispatch' and {'runtime','output','request_sha256','parent_pid'}<=value.keys():candidates.append(p)
    if len(candidates)!=1:raise RuntimeError('Exactly one bound '+kind+' required')
    return candidates[0]

def configure(pr,gate,runtime,output,execution,cases,duration):
    global CONTEXT
    if CONTEXT is not None:raise RuntimeError('One operational audit context per process')
    declaration=pr.verify_runtime(runtime)
    reconstruction=reconstruct_runtime(pr,runtime,declaration)
    first=output/f'{duration:g}T'/'cases'/cases[0]['case_name'];manifest=read(first/'source_manifest.json')
    request=resolve_bound_record(manifest,execution['request_sha256'],'request')
    dispatch=resolve_bound_record(manifest,execution['dispatch_sha256'],'dispatch')
    dispatch_value=read(dispatch)
    if (Path(dispatch_value['runtime']).resolve()!=runtime or Path(dispatch_value['output']).resolve()!=output or dispatch_value['request_sha256']!=sha(request)
            or type(dispatch_value['parent_pid']) is not int or dispatch_value['parent_pid']<=0):raise RuntimeError('Dispatch runtime/output/request differs')
    with request_environment(runtime,request,dispatch):
        _,_,_,authority=gate.context(runtime,output,'run')
        expected=gate.source_manifest()
    jobs=[dict(c, duration_T=duration) for c in cases]
    # Native worker jobs contain precisely these identity fields and horizon.
    if authority['jobs']!=jobs:raise RuntimeError('Exact six-case request roster differs')
    if authority['maximum_native_steps']!=execution['native_steps'] or execution['maximum_native_steps']!=execution['native_steps']:raise RuntimeError('Finite native budget differs')
    if execution['runtime_declaration_sha256']!=sha(runtime/'PRIMARY_RUNTIME.json') or execution['active_native_sha256']!=declaration['active_native_sha256']:raise RuntimeError('Execution artifact/runtime differs')
    if manifest!=expected:raise RuntimeError('Portable source/authority/dispatch closure differs')
    CONTEXT=dict(runtime=runtime,output=output,execution=execution,cases=cases,duration=duration,source_manifest=expected,reconstruction=reconstruction,request=request,dispatch=dispatch)
    return CONTEXT

def validate_candidate_seal(folder,duration=36.):
    """Original horizon/seal semantics plus actual portable source closure."""
    if CONTEXT is None:raise RuntimeError('Unconfigured portable seal context')
    folder=Path(folder).resolve();summary=read(folder/'summary.json');seal=read(folder/'completion.json')
    expected_dirs={CONTEXT['output']/f"{CONTEXT['duration']:g}T"/'cases'/c['case_name'] for c in CONTEXT['cases']}
    if folder not in expected_dirs or duration!=CONTEXT['duration']:raise RuntimeError('Foreign case/horizon')
    if seal.get('status')!='complete':raise RuntimeError('Incomplete replay case')
    for name,h in seal['files'].items():
        if sha(safe_member(folder,name))!=h:raise RuntimeError('Sealed replay bytes changed:'+name)
    key=f"{CONTEXT['duration']:g}T/"+folder.name
    if CONTEXT['execution']['case_completion_sha256'].get(key)!=sha(folder/'completion.json'):raise RuntimeError('Execution/completion binding differs')
    observed=summary['actual_duration']
    if summary['planned_duration']!=duration or summary['dt'] not in (.00125,.000625) or observed<=0 or observed>duration+1e-7 or summary['native_steps']!=round(observed/summary['dt']):raise RuntimeError('Bad physical horizon')
    if summary['native_absorbing_termination']:
        if summary['final_count']!=0:raise RuntimeError('Invalid depletion')
    elif abs(observed-duration)>1e-7:raise RuntimeError('Incomplete horizon')
    if read(folder/'source_manifest.json')!=CONTEXT['source_manifest'] or read(folder/'audit.json')['status']!='passed':raise RuntimeError('Portable source/physical audit mismatch')
    return seal
