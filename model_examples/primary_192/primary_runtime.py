"""Native-free source/input view for the exact H1/G36 primary192 model.

Only operational imports, constructor permissions and output gates are derived.
Pure assembly, constructor operations and the physical/accounting tail keep the
parent AST. Original files and hashes are immutable provenance.
"""
from __future__ import annotations
import ast,copy,hashlib,json,os,shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGINAL=Path('/home/venture/uwa/complex-systems/FishSim-RL')
STUDY=Path('research/independent_validation_2026-11-10')
SCHOOLS=tuple(range(39065501,39065517));LABELS=(71001,71002)
GRIDS={'coarse':.00125,'fine':.000625};ARMS=('D','G','DG')
HISTORICAL='eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'
SOURCE_BUILT='cc21f00f355e1d25e8ecb48bd6aa50a7c9b63f909d921f4864a96e91d9ef2d4b'
SOURCE_FREEZE='253071467e55b4cdbe91f75ba1de3f1bb80d65344e9cba05aadb86bccb08da0b'
ZERO_SHA='ed402b01c1984af14d205db6386607f72b634bbd14ab8226ae187310533470ea'
INTERFACE=('primary_runtime.py','primary_gate.py','primary_worker.py','run_primary_model.py','MODEL_INPUTS.json','REFERENCE_MANIFEST.json')
RELOCATED=('research/herding_study_2026-11-07/v2_numeric_execution_v1.json',
 'research/exposed_replication_2026-11-08/checkpoints/manifest.json','research/prey_mediated/BASELINE_V1.json',
 'research/prey_mediated/results/short_angular_physical_g3_v1/manifest.json',
 'research/prey_mediated/results/short_angular_physical_g3_v1/native.json')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def interfaces():return {p:sha(HERE/p) for p in INTERFACE}
def identity(school,label,grid,arm):
    if type(school)is not int or school not in SCHOOLS or type(label)is not int or label not in LABELS or grid not in GRIDS or arm not in ARMS:
        raise ValueError('Only the exact192 primary identities are allowed')
    policy='Gonly36' if arm=='G' else 'H1_G36' if arm=='DG' else 'H1_G0'
    return dict(case_name=f's{school}_{grid}_{policy}_{arm}_c{label}',school_seed=school,capture_seed=label,grid=grid,presence=arm,dt=GRIDS[grid])
def inventory():return [identity(s,l,g,a) for s in SCHOOLS for l in LABELS for g in GRIDS for a in ARMS]
def steps(jobs):
    total=0
    for job in jobs:
        if type(job['duration_T']) not in (int,float) or job['duration_T'] not in (4.,36.):raise ValueError('Only4T or36T')
        case=identity(job['school_seed'],job['capture_seed'],job['grid'],job['presence'])
        if job['case_name']!=case['case_name']:raise ValueError('Case identifier differs')
        total+=round(job['duration_T']/case['dt'])
    return total
def safe(path,package):
    path=Path(path).resolve();package=Path(package).resolve()
    for base in (package,ORIGINAL,HERE):
        if path==base or path.is_relative_to(base) or base.is_relative_to(path):raise ValueError('Protected path overlap:'+str(path))
    return path
def relative(original):
    original=Path(original)
    try:return original.relative_to(ORIGINAL)
    except ValueError:return Path('external',*original.parts[1:])
def relocate(value,mapping):
    if isinstance(value,str):
        for old,new in sorted(mapping.items(),key=lambda p:-len(p[0])):
            if value==old or value.startswith(old+'/'):return new+value[len(old):]
        return value
    if isinstance(value,list):return [relocate(x,mapping) for x in value]
    if isinstance(value,dict):return {relocate(k,mapping):relocate(v,mapping) for k,v in value.items()}
    return value
def link(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if sha(source)!=sha(target):raise RuntimeError('Input collision:'+str(target))
        return
    try:os.link(source,target)
    except OSError:shutil.copy2(source,target)
def ast_text(nodes):return ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False)

def derive_builder(source):
    tree=ast.parse(source);original=copy.deepcopy(tree)
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom) and n.module=='evidence':n.module='primary_gate'
    original_build=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='build')
    new_build=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build')
    # Operational imports change; every operation following prepare_case is exact.
    i=next(i for i,n in enumerate(original_build.body) if isinstance(n,ast.Assign) and ast.unparse(n).startswith('prepared = prepare_case'))
    if ast_text(original_build.body[i:])!=ast_text(new_build.body[i:]):raise RuntimeError('Constructor AST changed')
    return ast.unparse(ast.fix_missing_locations(tree))+'\n',dict(constructor_ast_sha256=hashlib.sha256(ast_text(original_build.body[i:]).encode()).hexdigest(),pure_assembly_unchanged=True)

def derive_runner(source):
    tree=ast.parse(source);original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_case')
    marker=next(i for i,n in enumerate(original.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(a,ast.Name) and a.id=='seed' for a in t.elts) for t in n.targets))
    expected='''from build import build
if not isinstance(case,Case):raise TypeError('A frozen held-out Case is required')
stage='smoke' if duration==4. else 'feeding'
require_approval(stage)
from evidence import require_case_permission
require_case_permission(case,stage,output)
if duration not in (4.,36.):raise ValueError('Only declared4T/36T horizons')
from cases import phase_output
if Path(output).resolve()!=phase_output('smoke' if stage=='smoke' else 'block1_coarse').resolve():raise ValueError('Exact declared output required')
if stage=='smoke' and case not in smoke_cases():raise ValueError('Undeclared smoke case')
'''
    if ast_text(original.body[:marker])!=ast_text(ast.parse(expected).body):raise RuntimeError('Unexpected parent operational preamble')
    new=copy.deepcopy(original)
    new.body[:marker]=ast.parse('from primary_build import build\nif not isinstance(case,Case):raise TypeError("A frozen primary Case is required")\nstage="smoke" if duration==4. else "feeding"\nrequire_run(case,duration,output)').body
    tail=ast_text(original.body[marker:])
    if tail!=ast_text(new.body[4:]):raise RuntimeError('Physical/accounting AST changed')
    chosen=[]
    for n in tree.body:
        if isinstance(n,ast.ImportFrom) and n.module=='evidence':chosen+=ast.parse('from primary_gate import source_manifest,require_approval,require_run').body
        elif isinstance(n,ast.FunctionDef) and n.name=='run_case':chosen.append(new);break
        else:chosen.append(n)
    return ast.unparse(ast.fix_missing_locations(ast.Module(body=chosen,type_ignores=[])))+'\n',dict(physical_ast_sha256=hashlib.sha256(tail.encode()).hexdigest(),physical_tail_unchanged=True)

def snapshot_manifest_file(snapshot):
    """One canonical manifest-file contract; a directory is convenience only."""
    path=Path(snapshot).expanduser().resolve()
    if path.is_dir():path=(path/'SNAPSHOT.json').resolve()
    if path.name!='SNAPSHOT.json':raise ValueError('Snapshot must name SNAPSHOT.json or its containing directory')
    if not path.is_file():raise FileNotFoundError('Snapshot manifest is missing:'+str(path))
    return path

def load_accepted_snapshot(package,snapshot):
    manifest=snapshot_manifest_file(snapshot)
    spec=read(HERE/'MODEL_INPUTS.json');reader_path=Path(package)/'validation_tools/portable_reader.py'
    if not reader_path.is_file():raise RuntimeError('Validated production portable_reader is not yet installed')
    if sha(reader_path)!=spec['portable_reader_sha256']:raise RuntimeError('Production snapshot reader differs from pinned source')
    import importlib.util
    module_spec=importlib.util.spec_from_file_location('primary_saved_snapshot_reader',reader_path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    saved=module.Snapshot(manifest)
    module.validate_evidence(saved)
    return saved

def snapshot_provenance(saved):
    if saved is None:return dict(snapshot_manifest_sha256=None,snapshot_manifest_file=None,snapshot_root=None)
    # Snapshot.path is the exact normalized file passed to the pinned reader.
    manifest=saved.path
    return dict(snapshot_manifest_sha256=sha(manifest),snapshot_manifest_file=str(manifest),snapshot_root=str(manifest.parent))

def input_paths(package,snapshot=None):
    """Resolve opaque identities via validated snapshot or private source spec.

    Private author mode is for current pure checks only; local native release
    requires a production snapshot accepted by the separate portable reader.
    """
    spec=read(HERE/'MODEL_INPUTS.json');resolved={};saved=None
    if snapshot is not None:
        saved=load_accepted_snapshot(package,snapshot)
        for original,digest in spec['primary_sources'].items():
            if saved.manifest['sources'].get(original)!=digest:raise RuntimeError('Snapshot source crosswalk differs')
            resolved[original]=saved.path_for(digest)
        mode='production_snapshot'
    else:
        for original,digest in spec['primary_sources'].items():
            if '/FishSim_Independent_Validation_2026-11-10/full_36T_v1/' in original or '/FishSim_Independent_Validation_2026-11-10/phases/' in original:raise RuntimeError('Unaccepted feeding path in source closure')
            resolved[original]=Path(original)
        mode='private_author_inputs_pure_only'
    for original,path in resolved.items():
        if sha(path)!=spec['primary_sources'][original]:raise RuntimeError('Input source differs:'+original)
    return resolved,mode,saved

def prepare(package,runtime,native_kind,snapshot=None):
    package=Path(package).resolve();runtime=safe(runtime,package)
    if runtime.exists():raise FileExistsError('Never overwrite a runtime')
    spec=read(HERE/'MODEL_INPUTS.json');sources,mode,saved=input_paths(package,snapshot)
    refs=read(HERE/'REFERENCE_MANIFEST.json')
    if refs['input_spec_sha256']!=sha(HERE/'MODEL_INPUTS.json'):raise RuntimeError('Reference/input-spec binding differs')
    reference_paths={}
    for p,h in refs['files'].items():
        if saved is None:source=HERE/p
        elif h in saved.manifest['objects']:source=saved.path_for(h)
        else:
            alias=spec.get('public_reference_aliases',{}).get(p)
            if alias is None:raise RuntimeError('Snapshot lacks required accepted reference:'+p)
            source=(package/alias).resolve()
            if not source.is_relative_to(package):raise RuntimeError('Public reference alias escapes package')
        if sha(source)!=h:raise RuntimeError('Reference changed:'+p)
        reference_paths[p]=source
    frozen=read(package/'INPUT_MANIFEST_2026-11-10_D24.json')['files']
    runtime.mkdir(parents=True)
    for p,h in frozen.items():
        if p.startswith('frozen_model/'):
            if sha(package/p)!=h:raise RuntimeError('Inherited model input changed')
            link(package/p,runtime/Path(p).relative_to('frozen_model'))
    mapping={}
    for original,path in sources.items():
        target=runtime/relative(original);link(path,target);mapping[original]=str(target)
    # Existing snapshot objects serve the reference paths too. No original
    # author path or duplicate new raw-data bundle is needed after export.
    for p,source in reference_paths.items():link(source,runtime/'reference_inputs'/Path(p).relative_to('references'))
    native=runtime/'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so'
    historical=runtime/'historical_reference/cmodel.cpython-312-x86_64-linux-gnu.so'
    link(package/'frozen_model/lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so',historical)
    if native_kind=='source-built':
        native.unlink();link(package/'runtime_validation/source_build_linux_amd64/cmodel.cpython-312-x86_64-linux-gnu.so',native)
    elif native_kind!='historical':raise ValueError('Unknown native kind')
    if sha(native)!=(HISTORICAL if native_kind=='historical' else SOURCE_BUILT):raise RuntimeError('Wrong active artifact')
    mapping[str(ORIGINAL/'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so')]=str(historical)
    for p in RELOCATED:
        target=runtime/p;value=relocate(read(target),mapping);target.unlink();write(target,value)
    prep=relocate(spec['preparation'],mapping)
    # Directory identities are not individual source-file keys; relocate them
    # explicitly so metadata hashing cannot fall back to the live author bank.
    prep['old_directory']=str(runtime/relative(spec['preparation']['old_directory']))
    prep['new_directory']=str(runtime/relative(spec['preparation']['new_directory']))
    write(runtime/'PREPARATION_INDEX.json',prep)
    for name in INTERFACE:shutil.copy2(HERE/name,runtime/STUDY/name)
    builder,bproof=derive_builder((runtime/STUDY/'build.py').read_text())
    runner,rproof=derive_runner((runtime/STUDY/'physical_run.py').read_text())
    (runtime/STUDY/'primary_build.py').write_text(builder);(runtime/STUDY/'primary_execution.py').write_text(runner)
    files={str(p.relative_to(runtime)):sha(p) for p in sorted(runtime.rglob('*')) if p.is_file()}
    declaration=dict(schema='fishsim_primary_model_runtime_v1',package=str(package),source_mode=mode,
        **snapshot_provenance(saved),native_kind=native_kind,
        active_native_sha256=sha(native),historical_reference_sha256=sha(historical),interface_files=interfaces(),
        source_freeze_sha256=SOURCE_FREEZE,reference_manifest_sha256=sha(HERE/'REFERENCE_MANIFEST.json'),
        builder_proof=bproof,runner_proof=rproof,runtime_files=files,native_imports=0,native_constructions=0,native_steps=0)
    write(runtime/'PRIMARY_RUNTIME.json',declaration);return declaration

def verify_runtime(runtime):
    runtime=Path(runtime).resolve();d=read(runtime/'PRIMARY_RUNTIME.json')
    if d['schema']!='fishsim_primary_model_runtime_v1' or d['interface_files']!=interfaces():raise RuntimeError('Runtime/interface differs')
    expected=HISTORICAL if d['native_kind']=='historical' else SOURCE_BUILT
    if d['active_native_sha256']!=expected or d['historical_reference_sha256']!=HISTORICAL:raise RuntimeError('Native artifact binding differs')
    actual={str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}
    if actual!=set(d['runtime_files'])|{'PRIMARY_RUNTIME.json'}:raise RuntimeError('Runtime inventory changed')
    for p,h in d['runtime_files'].items():
        target=(runtime/p).resolve()
        if not target.is_relative_to(runtime) or sha(target)!=h:raise RuntimeError('Runtime bytes changed:'+p)
    return d
