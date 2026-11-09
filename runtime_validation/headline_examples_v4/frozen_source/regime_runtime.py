"""Private derived runtime for the frozen four-school H×G model example.

This module only verifies and copies files. It neither imports the extension nor
constructs a school. Historical experiment gates and receipts are never reused
as runtime authorizations.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
INTERFACE_FILES = ('regime_runtime.py', 'regime_runtime_worker.py', 'run_regime_model.py', 'regime_example_gate.py', 'run_v6_example.py')
ORIGINAL = Path('/home/venture/uwa/complex-systems/FishSim-RL')
STUDY = Path('research/high_count_regime_extension_2026-11-09')
RETAINED_STUDY = Path('research/pilot_regime_sweep_2026-11-09_v2')
INPUT_MANIFEST = 'INPUT_MANIFEST_2026-11-09_high_counts.json'
CLOSURE = 'SOURCE_CLOSURE_2026-11-09_high_counts.json'
HISTORICAL_NATIVE = 'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so'
HISTORICAL_SHA = 'eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'
RELOCATED_JSON = (
    'research/herding_study_2026-11-07/v2_numeric_execution_v1.json',
    'research/exposed_replication_2026-11-08/checkpoints/manifest.json',
    'research/prey_mediated/BASELINE_V1.json',
    'research/prey_mediated/results/short_angular_physical_g3_v1/manifest.json',
    'research/prey_mediated/results/short_angular_physical_g3_v1/native.json',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def interface_hashes():
    return {name: sha(HERE / name) for name in INTERFACE_FILES}


def safe_output(path, package):
    path, package = Path(path).resolve(), Path(package).resolve()
    external_preparation = Path('/run/media/venture/DJ K4T/FishSim-herding-study-2026-11-06')
    for protected in (package, ORIGINAL, HERE, external_preparation):
        if path == protected or path.is_relative_to(protected) or protected.is_relative_to(path):
            raise ValueError('Runtime/output must be outside protected package, source and adapter: ' + str(path))
    return path


def verify_package(package):
    package = Path(package).resolve()
    pins = read(HERE / 'REGIME_RUNTIME_INPUTS.json')
    for name, expected in pins['package_manifests'].items():
        if sha(package / name) != expected:
            raise RuntimeError('Protected package manifest changed: ' + name)
    manifest = read(package / INPUT_MANIFEST)['files']
    expected_frozen = {p: h for p, h in manifest.items() if p.startswith('frozen_model/')}
    actual = {str(p.relative_to(package)) for p in (package / 'frozen_model').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if actual != set(expected_frozen):
        raise RuntimeError('Frozen-model file inventory changed')
    for relative, digest in expected_frozen.items():
        if sha(package / relative) != digest:
            raise RuntimeError('Frozen-model bytes changed: ' + relative)
    entries = read(package / CLOSURE)
    if len(entries) != 2100 or len({x['original_path'] for x in entries}) != 2100:
        raise RuntimeError('The complete2100-entry v6 source closure is required')
    for entry in entries:
        if sha(package / entry['bundled_path']) != entry['sha256']:
            raise RuntimeError('Frozen regime input changed: ' + entry['bundled_path'])
    if sha(package / 'frozen_model' / HISTORICAL_NATIVE) != HISTORICAL_SHA:
        raise RuntimeError('Historical pure-reference artifact changed')
    return entries, expected_frozen


def native_source_files(package):
    package = Path(package)
    paths = [package / 'frozen_model/CMakeLists.txt']
    for folder in ('src', 'extern'):
        paths += [p for p in (package / 'frozen_model' / folder).rglob('*') if p.is_file()
                  and '__pycache__' not in p.parts and p.suffix != '.pyc']
    return {str(p.relative_to(package / 'frozen_model')): sha(p) for p in sorted(paths)}


def destination_relative(original):
    original = Path(original)
    if not original.is_absolute():
        raise ValueError('The source closure must contain absolute original paths')
    try:
        return original.relative_to(ORIGINAL)
    except ValueError:
        return Path('external') / Path(*original.parts[1:])


def relocate(value, path_map):
    if isinstance(value, str):
        # Longest exact known prefix first; no arbitrary token/hash substitution.
        for old, new in sorted(path_map.items(), key=lambda pair: -len(pair[0])):
            if value == old or value.startswith(old + '/'):
                return new + value[len(old):]
        return value
    if isinstance(value, list):
        return [relocate(x, path_map) for x in value]
    if isinstance(value, dict):
        return {relocate(k, path_map): relocate(v, path_map) for k, v in value.items()}
    return value


def generate_execution(source):
    """Derive an explicit new harness; retain the full physical/accounting body.

    Only five run_case preamble statements enforcing historical operational
    gates/horizons are replaced. Every later run_case AST node is identical.
    Helpers/imports used by the body retain their exact AST. The old run.py
    itself remains byte-identical in the copied runtime.
    """
    tree = ast.parse(source)
    original = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_case')
    expected = [
        "require_approval('smoke' if duration == 4.0 else 'full')",
        "case = decode(seed, policy, presence)",
        "if duration not in (4.0, 36.0):\n    raise ValueError('Only declared smoke/full horizons are allowed')",
        "if duration == 4.0 and case not in smoke_cases():\n    raise ValueError('Unplanned smoke case')",
        "if case not in all_cases():\n    raise ValueError('Retained outcomes are reused; never rerun as new cells')",
    ]
    def normalized(text):
        return ast.dump(ast.parse(text).body[0], include_attributes=False)
    if [ast.dump(n, include_attributes=False) for n in original.body[1:6]] != [normalized(x) for x in expected]:
        raise RuntimeError('Frozen runner preamble differs from the reviewed extraction contract')
    new_case = copy.deepcopy(original)
    new_case.body[1:6] = ast.parse(
        'require_example_case(seed, policy, presence, capture_seed, duration, output)\n'
        'case = decode(seed, policy, presence)\n').body
    if ast.dump(ast.Module(body=original.body[6:], type_ignores=[]), include_attributes=False) != \
       ast.dump(ast.Module(body=new_case.body[3:], type_ignores=[]), include_attributes=False):
        raise RuntimeError('Physical/accounting body changed during extraction')
    chosen = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'evidence':
            chosen.extend(ast.parse('from regime_example_gate import require_example_case, example_source_manifest as source_manifest').body)
        elif isinstance(node, ast.FunctionDef):
            if node.name == 'run_case':
                chosen.append(new_case)
                break
            chosen.append(copy.deepcopy(node))
        else:
            chosen.append(copy.deepcopy(node))
    generated = '# New derived example harness; historical run.py is preserved separately.\n' + ast.unparse(ast.fix_missing_locations(ast.Module(body=chosen, type_ignores=[]))) + '\n'
    proof = dict(status='passed', historical_run_case_nodes=len(original.body),
                 unchanged_physical_accounting_nodes=len(original.body[6:]),
                 changed_preamble_only=True, historical_gate_receipts_reused=False,
                 historical_run_sha256=hashlib.sha256(source.encode()).hexdigest(),
                 full_body_ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=original.body[6:], type_ignores=[]), include_attributes=False).encode()).hexdigest(),
                 generated_full_body_ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=new_case.body[3:], type_ignores=[]), include_attributes=False).encode()).hexdigest(),
                 generated_sha256=hashlib.sha256(generated.encode()).hexdigest())
    return generated, proof


def generate_builder(source):
    """Replace only old artifact approval with a separately scoped example gate."""
    tree = ast.parse(source)
    original = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build')
    expected = ast.parse('from evidence import require_approval\nrequire_approval(stage)\n').body
    # The function docstring is retained at index0.
    if [ast.dump(n, include_attributes=False) for n in original.body[1:3]] != [ast.dump(n, include_attributes=False) for n in expected]:
        raise RuntimeError('Frozen high-count builder artifact gate differs')
    adapted = copy.deepcopy(original)
    adapted.body[1:3] = ast.parse('from regime_example_gate import require_example_build\n'
        'require_example_build(seed, policy, presence, capture_seed, stage)\n').body
    old_body = ast.dump(ast.Module(body=original.body[3:], type_ignores=[]), include_attributes=False)
    new_body = ast.dump(ast.Module(body=adapted.body[3:], type_ignores=[]), include_attributes=False)
    if old_body != new_body:
        raise RuntimeError('Pure preparation or physical constructor changed')
    for i, node in enumerate(tree.body):
        if node is original:
            tree.body[i] = adapted
    generated = '# New derived builder gate; archived build.py remains byte-identical.\n' + ast.unparse(ast.fix_missing_locations(tree)) + '\n'
    proof = dict(status='passed', historical_build_sha256=hashlib.sha256(source.encode()).hexdigest(),
        historical_constructor_body_ast_sha256=hashlib.sha256(old_body.encode()).hexdigest(),
        generated_constructor_body_ast_sha256=hashlib.sha256(new_body.encode()).hexdigest(),
        generated_sha256=hashlib.sha256(generated.encode()).hexdigest(),
        artifact_gate_only=True, historical_approval_receipts_reused=False)
    return generated, proof


def golden_case_folder(package, case):
    """Resolve the exact saved actual start for each retained/new v6 identity."""
    study = RETAINED_STUDY if case.retained else STUDY
    return Path(package) / 'data' / study / 'results/full_36T_v1/cases' / case.name


def prepare_runtime(package, work, candidate_native=None, candidate_record=None):
    package = Path(package).resolve()
    work = safe_output(work, package)
    entries, frozen = verify_package(package)
    if work.exists():
        raise ValueError('Use a fresh runtime folder; existing derived runtimes are preserved')
    binary = package / 'frozen_model' / HISTORICAL_NATIVE
    build_record = None
    native_kind = 'historical_pinned_binary'
    if candidate_native:
        if not candidate_record:
            raise ValueError('A separate rebuilt module needs its explicit native build record')
        binary = Path(candidate_native).resolve()
        build_record = read(candidate_record)
        if (build_record['binary_sha256'] != sha(binary)
                or build_record['model_source_sha256'] != native_source_files(package)
                or not build_record['python_version'].startswith('3.12.')):
            raise RuntimeError('Separate native build provenance does not match exact published C++ inputs')
        native_kind = 'explicit_separate_source_build'
    work.parent.mkdir(parents=True, exist_ok=True)
    staging = work.with_name(work.name + '.building_' + str(os.getpid()))
    if staging.exists():
        raise RuntimeError('Preserve incomplete staging; select a fresh work folder')
    shutil.copytree(package / 'frozen_model', staging, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    paths = {str(ORIGINAL): str(work)}
    original_copies = {}
    overlays = []
    for entry in entries:
        relative = destination_relative(entry['original_path'])
        destination = staging / relative
        if destination.exists() and sha(destination) != entry['sha256']:
            overlays.append(dict(path=str(relative), prior_sha256=sha(destination), required_sha256=entry['sha256']))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package / entry['bundled_path'], destination)
        original_copies[str(relative)] = entry['sha256']
        paths[entry['original_path']] = str(work / relative)
    historical_copy = staging / 'historical_native' / Path(HISTORICAL_NATIVE).name
    historical_copy.parent.mkdir()
    shutil.copy2(package / 'frozen_model' / HISTORICAL_NATIVE, historical_copy)
    shutil.copy2(binary, staging / HISTORICAL_NATIVE)
    relocations = []
    for relative in RELOCATED_JSON:
        path = staging / relative
        previous = read(path)
        current = relocate(previous, paths)
        if relative.endswith('/short_angular_physical_g3_v1/native.json'):
            if previous['sha256'] != HISTORICAL_SHA:
                raise RuntimeError('Historical pure-reference artifact pin differs')
            current['path'] = str(work / 'historical_native' / Path(HISTORICAL_NATIVE).name)
        elif relative.endswith('/v2_numeric_execution_v1.json') or relative.endswith('/checkpoints/manifest.json'):
            if current['native']['sha256'] != HISTORICAL_SHA:
                raise RuntimeError('Checkpoint preparation origin differs')
            current['native'] = dict(current['native'], path=str(work / HISTORICAL_NATIVE), sha256=sha(binary))
            if 'bytes' in current['native']:
                current['native']['bytes'] = binary.stat().st_size
        write(path, current)
        relocations.append(dict(path=relative, original_sha256=sha(package / 'frozen_model' / relative)
                                if relative not in original_copies else original_copies[relative],
                                derived_sha256=sha(path), original_native=previous.get('native'),
                                role='Derived path/active-native compatibility binding; historical input remains unchanged in package'))
    for relative, digest in original_copies.items():
        if relative not in RELOCATED_JSON and relative != HISTORICAL_NATIVE and sha(staging / relative) != digest:
            raise RuntimeError('Exact frozen regime code/array/evidence copy differs: ' + relative)
    generated, proof = generate_execution((staging / STUDY / 'run.py').read_text())
    (staging / STUDY / 'regime_example_execution.py').write_text(generated)
    generated_build, builder_proof = generate_builder((staging / STUDY / 'build.py').read_text())
    (staging / STUDY / 'regime_example_build.py').write_text(generated_build)
    shutil.copy2(HERE / 'regime_example_gate.py', staging / STUDY / 'regime_example_gate.py')
    runtime_files = {str(p.relative_to(staging)): sha(p) for p in sorted(staging.rglob('*'))
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    declaration = dict(schema='fishsim_regime_example_derived_runtime_v4', status='assembled_not_native_validated',
        package=str(package), runtime=str(work), scientific_study=str(STUDY),
        package_manifests=read(HERE / 'REGIME_RUNTIME_INPUTS.json')['package_manifests'],
        adapter_sha256=sha(__file__), worker_sha256=sha(HERE / 'regime_runtime_worker.py'),
        interface_sha256=sha(HERE / 'run_regime_model.py'), gate_sha256=sha(HERE / 'regime_example_gate.py'),
        request_generator_sha256=sha(HERE / 'run_v6_example.py'), interface_files=interface_hashes(),
        native_kind=native_kind, actual_native_sha256=sha(binary), historical_native_sha256=HISTORICAL_SHA,
        historical_actor_reference=dict(path=str(work / 'historical_native' / Path(HISTORICAL_NATIVE).name),
                                        sha256=HISTORICAL_SHA, executed=False),
        native_build_record=build_record, archived_scientific_python_and_checkpoint_bytes_modified=False,
        archive_receipts_are_not_runtime_authorizations=True,
        original_repository=str(ORIGINAL), original_path_to_runtime=paths,
        relocated_json=relocations, scientific_overlays=overlays, execution_body_proof=proof,
        builder_body_proof=builder_proof, actual_start_cases=108, independent_schools=4,
        runtime_files=runtime_files, native_imports=0, native_constructions=0, native_steps=0,
        scope='V6 four archived discovery schools;108 starts across H1/2/3 and G0/1/3/6/9/12/18 with matched D/G/DG arms. Coarse dt=.00125. Bounded examples H1/G9 andH2/G12 only; never a replacement for historical evidence.')
    write(staging / 'REGIME_RUNTIME_DECLARATION.json', declaration)
    staging.rename(work)
    return work


def verify_runtime(runtime):
    runtime = Path(runtime).resolve()
    declaration = read(runtime / 'REGIME_RUNTIME_DECLARATION.json')
    if declaration['runtime'] != str(runtime):
        raise RuntimeError('Derived runtime path differs from its declared bindings')
    if declaration.get('interface_files') != interface_hashes():
        raise RuntimeError('Derived runtime does not bind the exact complete v4 interface/request generator')
    for filename, field in (('regime_runtime.py', 'adapter_sha256'), ('regime_runtime_worker.py', 'worker_sha256'),
                            ('run_regime_model.py', 'interface_sha256'), ('regime_example_gate.py', 'gate_sha256')):
        if sha(HERE / filename) != declaration[field]:
            raise RuntimeError('Current example interface differs from its derived runtime declaration: ' + filename)
    for relative, expected in declaration['runtime_files'].items():
        if sha(runtime / relative) != expected:
            raise RuntimeError('Derived runtime input changed: ' + relative)
    return declaration
