"""Prepare an additive runtime for the published eight-school experiments.

Historical package files are read, verified, and copied. Scientific Python/C++
sources and checkpoint arrays are never edited. Derived JSON declarations record
path relocation and, when explicitly selected, a separately built native binary.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
STUDIES = {'coarse': 'longer_replication_2026-11-09',
           'fine': 'fine_dt_replication_2026-11-09'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def relocate(value, original, destination, old_binary_hash, new_binary_hash):
    if isinstance(value, str):
        if value == old_binary_hash:
            return new_binary_hash
        return value.replace(original, destination)
    if isinstance(value, list):
        return [relocate(x, original, destination, old_binary_hash, new_binary_hash) for x in value]
    if isinstance(value, dict):
        return {relocate(k, original, destination, old_binary_hash, new_binary_hash):
                relocate(v, original, destination, old_binary_hash, new_binary_hash)
                for k, v in value.items()}
    return value


def native_source_files(package):
    verify_frozen_source(package)
    frozen = Path(package) / 'frozen_model'
    files = [frozen / 'CMakeLists.txt']
    for directory in ('src', 'extern'):
        files.extend(p for p in (frozen / directory).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {str(p.relative_to(frozen)): sha(p) for p in sorted(files)}


def reject_source_destination(destination, sources):
    destination = Path(destination).resolve()
    for source in sources:
        if destination.is_relative_to(Path(source).resolve()):
            raise ValueError('Output/work must be outside protected source trees: ' + str(destination))


def verify_frozen_source(package):
    package = Path(package).resolve()
    declaration = read(HERE / 'CURRENT_RUNTIME_INPUTS.json')
    manifest = declaration['published_input_manifest']
    path = package / manifest['path']
    if sha(path) != manifest['sha256']:
        raise RuntimeError('The published input manifest changed.')
    files = read(path)['files']
    expected = {name: digest for name, digest in files.items() if name.startswith('frozen_model/')}
    actual = {str(p.relative_to(package)) for p in (package / 'frozen_model').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if actual != set(expected):
        raise RuntimeError('The complete frozen source file inventory changed.')
    for relative, digest in expected.items():
        if sha(package / relative) != digest:
            raise RuntimeError('A protected frozen source changed: ' + relative)
    return expected


def verify_inputs(package):
    package = Path(package).resolve()
    verify_frozen_source(package)
    declaration = read(HERE / 'CURRENT_RUNTIME_INPUTS.json')
    for entry in declaration['package_source_manifest_entries']:
        if sha(package / entry['bundled_path']) != entry['sha256']:
            raise RuntimeError('Current source differs: ' + entry['bundled_path'])
    for entry in declaration['extra_checkpoints']:
        if sha(HERE / entry['bundled_path']) != entry['sha256']:
            raise RuntimeError('Prepared checkpoint differs: ' + entry['bundled_path'])
    if sha(package / 'frozen_model' / declaration['historical_native_relative']) != declaration['historical_native_sha256']:
        raise RuntimeError('Historical binary differs; originals must remain unchanged.')
    return declaration


def prepare_runtime(package, work, candidate_native=None, candidate_record=None):
    """Copy and relocate inputs only; import no native module and take no steps."""
    package, work = Path(package).resolve(), Path(work).resolve()
    reject_source_destination(work, [package / 'frozen_model', package / 'data',
        package / 'study_sources', HERE / 'current_model_inputs'])
    inputs = verify_inputs(package)
    binary = package / 'frozen_model' / inputs['historical_native_relative']
    native_kind = 'historical_pinned_binary'
    build_record = None
    if candidate_native is not None:
        if candidate_record is None:
            raise ValueError('A rebuilt binary requires an explicit native build record.')
        binary = Path(candidate_native).resolve()
        build_record = read(candidate_record)
        if build_record['binary_sha256'] != sha(binary):
            raise RuntimeError('Candidate binary hash differs from its build record.')
        if build_record['model_source_sha256'] != native_source_files(package):
            raise RuntimeError('Candidate build sources differ from the published sources.')
        if not build_record['python_version'].startswith('3.12.'):
            raise RuntimeError('This current model runtime requires a CPython 3.12 build.')
        native_kind = 'explicit_separate_source_build'
    signature = dict(package=str(package), work=str(work),
                     inputs_sha256=sha(HERE / 'CURRENT_RUNTIME_INPUTS.json'),
                     adapter_sha256=sha(__file__),
                     worker_sha256=sha(HERE / 'current_runtime_worker.py'),
                     python=sys.version,
                     packages={name: importlib.metadata.version(name) for name in
                               ('numpy', 'scipy', 'matplotlib', 'networkx', 'numba')},
                     container_image_id=os.environ.get('FISHSIM_RUNTIME_IMAGE_ID'),
                     native_sha256=sha(binary),
                     native_kind=native_kind)
    key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()[:20]
    runtime = work / ('current_model_' + key)
    receipt = runtime / 'CURRENT_MODEL_DECLARATION.json'
    if runtime.exists():
        retained = receipt if receipt.exists() else runtime / 'RUNTIME_COPY_RECEIPT.json'
        if not retained.exists():
            raise RuntimeError('Incomplete private runtime: use a fresh --work folder. ' + str(runtime))
        existing = read(retained)
        if existing['signature'] != signature:
            raise RuntimeError('Private runtime signature changed.')
        for relative, digest in existing['runtime_files'].items():
            if sha(runtime / relative) != digest:
                raise RuntimeError('Private runtime input changed: ' + relative)
        return runtime
    runtime.parent.mkdir(parents=True, exist_ok=True)
    staging = runtime.with_name(runtime.name + '.building_' + str(os.getpid()))
    shutil.copytree(package / 'frozen_model', staging,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    overrides = []
    original_root = Path(inputs['original_repository'])
    for entry in inputs['package_source_manifest_entries']:
        relative = Path(entry['original_path']).relative_to(original_root)
        destination = staging / relative
        if destination.exists() and sha(destination) != entry['sha256']:
            overrides.append(dict(path=str(relative), prior_sha256=sha(destination),
                                  required_current_sha256=entry['sha256']))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package / entry['bundled_path'], destination)
    for entry in inputs['extra_checkpoints']:
        relative = Path(entry['original_path']).relative_to(original_root)
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / entry['bundled_path'], destination)
    # Additional readiness declarations are data, not scientific Python source.
    for study in STUDIES.values():
        for name in ('frozen_sources.json',):
            source = package / 'data/research' / study / name
            destination = staging / 'research' / study / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    shutil.copy2(binary, staging / inputs['historical_native_relative'])
    relocations = []
    for path in sorted(staging.rglob('*.json')):
        previous = read(path)
        current = relocate(previous, str(original_root), str(runtime),
                           inputs['historical_native_sha256'], sha(binary))
        if previous != current:
            if isinstance(previous, dict) and path.name == 'manifest.json' and 'checkpoints' in previous and 'native' in previous:
                current['historical_preparation_native'] = previous['native']
                current['derived_execution_native'] = current['native']
                current['checkpoint_arrays_reused_without_preparation'] = True
                current['native_binding_interpretation'] = 'The native field is a derived execution compatibility binding; historical_preparation_native retains checkpoint origin.'
            before = sha(path)
            write(path, current)
            relocations.append(dict(path=str(path.relative_to(staging)),
                                    original_sha256=before, derived_sha256=sha(path)))
    # Every declared scientific source and saved array is still exact.
    for entry in inputs['package_source_manifest_entries'] + inputs['extra_checkpoints']:
        relative = Path(entry['original_path']).relative_to(original_root)
        if relative.suffix != '.json' and sha(staging / relative) != entry['sha256']:
            raise RuntimeError('Scientific code/checkpoint changed: ' + str(relative))
    copied_files = {str(p.relative_to(staging)): sha(p) for p in staging.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    write(staging / 'RUNTIME_COPY_RECEIPT.json', dict(
        status='copied_not_execution_validated', signature=signature,
        original_repository=str(original_root), runtime_root=str(runtime),
        native_kind=native_kind, native_build_record=build_record,
        historical_native_sha256=inputs['historical_native_sha256'],
        actual_native_sha256=sha(binary), current_source_overlays=overrides,
        relocated_json=relocations, runtime_files=copied_files, native_steps=0,
        scope='Exact current source/checkpoint copy; JSON paths and explicit native declaration only.'))
    staging.rename(runtime)
    return runtime


def require_python():
    if sys.flags.optimize:
        raise RuntimeError('Run actual model validation without Python -O or PYTHONOPTIMIZE.')
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Actual current-model execution uses CPython 3.12. The analysis notebook remains independent.')
