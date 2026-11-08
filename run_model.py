"""Explicit optional execution of the actual frozen FishSim model.

No substitute simulator is used. Python model sources and the pinned binary are
copied unchanged into a private runtime tree. Only absolute JSON paths are
relocated, with original and relocated hashes recorded. The historical runner
then executes in a fresh subprocess to avoid short-module-name collisions.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relocate(value, old, new):
    if isinstance(value,str):return value.replace(old,new)
    if isinstance(value,list):return [relocate(item,old,new) for item in value]
    if isinstance(value,dict):return {relocate(key,old,new):relocate(item,old,new) for key,item in value.items()}
    return value


def prepare_runtime():
    from notebook_support import verify_inputs
    verify_inputs()
    dataset = json.loads((HERE/'DATASET.json').read_text())
    frozen = HERE/'frozen_model';runtime = HERE/'work/model_runtime'
    receipt = runtime/'NOTEBOOK_RELOCATION.json'
    frozen_files = {str(path.relative_to(frozen)):sha(path) for path in frozen.rglob('*') if path.is_file()}
    if runtime.exists():
        if not receipt.exists():raise RuntimeError('Incomplete runtime cache; remove only work/model_runtime and try again.')
        existing = json.loads(receipt.read_text())
        if existing['runtime_root']!=str(runtime.resolve()):
            raise RuntimeError('Notebook folder moved after runtime preparation. Remove work/model_runtime and retry; saved runs remain in outputs.')
        if existing['frozen_files']!=frozen_files:
            raise RuntimeError('Runtime was prepared from different frozen sources; use a fresh notebook folder.')
        for relative,digest in existing['runtime_files'].items():
            if sha(runtime/relative)!=digest:raise RuntimeError(f'Runtime input changed: {relative}')
        return runtime
    runtime.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(frozen,runtime)
    changes = []
    old_root = dataset['original_repository']
    for path in sorted(runtime.rglob('*.json')):
        before = path.read_bytes();value = json.loads(before)
        updated = relocate(value,old_root,str(runtime.resolve()))
        if updated!=value:
            path.write_text(json.dumps(updated,indent=2)+'\n')
            changes.append(dict(path=str(path.relative_to(runtime)),
                original_sha256=hashlib.sha256(before).hexdigest(),relocated_sha256=sha(path)))
    runtime_files = {str(path.relative_to(runtime)):sha(path) for path in runtime.rglob('*') if path.is_file()}
    for relative,digest in frozen_files.items():
        if Path(relative).suffix in ('.py','.so','.cpp','.hpp','.npz'):
            if runtime_files[relative]!=digest:raise RuntimeError(f'Non-JSON model artifact changed: {relative}')
    receipt.write_text(json.dumps(dict(runtime_root=str(runtime.resolve()),
        original_repository=old_root,relocation='absolute path text in copied JSON only; no code, parameter or checkpoint changes',
        frozen_files=frozen_files,runtime_files=runtime_files,relocated_json=changes),indent=2)+'\n')
    return runtime


def check_native(runtime):
    from notebook_support import native_environment
    report = native_environment()
    if not report['eligible_for_native_import_check']:
        raise RuntimeError('The shipped model binary requires CPython3.12, Linux x86-64 and glibc>=2.43. '
            'The analysis notebook still works. See NATIVE_SETUP.md for source/rebuild provenance; no rebuilt platform is silently accepted. '
            +json.dumps(report))
    # Import only; no school constructor or model stepping is invoked here.
    code = ('import hashlib,json,fish_sim.cmodel as native; '
            'p=native.__file__; print(json.dumps({"native_path":p,"sha256":hashlib.sha256(open(p,"rb").read()).hexdigest(),"native_steps":0}))')
    environment = os.environ.copy()
    environment['PYTHONPATH'] = os.pathsep.join([str(runtime/'lib'),str(runtime)])
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        environment[name] = '1'
    result = subprocess.run([sys.executable,'-c',code],cwd=runtime,env=environment,
                            text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError('Native import failed. Check the model dependency environment and C++/OpenMP runtime.\n'+result.stderr)
    loaded = json.loads(result.stdout.strip().splitlines()[-1])
    if loaded['sha256']!=report['binary_sha256']:
        raise RuntimeError('Imported extension is not the historical pinned binary')
    print(json.dumps(dict(status='native_import_passed',**loaded)),flush=True)
    return environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check',action='store_true',help='Native import test only; zero model steps')
    modes.add_argument('--quick',action='store_true',help='0.5T D plus 0.5T DG integration check; not feeding evidence')
    modes.add_argument('--full',action='store_true',help='36T matched D/DG pair')
    parser.add_argument('--school',type=int,choices=(39063501,39063502),default=39063501)
    parser.add_argument('--capture-seed',type=int,choices=(61001,61002),default=61001)
    parser.add_argument('--workers',type=int,choices=(1,2,3,4),default=1)
    parser.add_argument('--all-replication',action='store_true',help='With --full only: both schools and both capture seeds, eight cases')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.all_replication and not args.full:parser.error('--all-replication requires --full')
    runtime = prepare_runtime();environment = check_native(runtime)
    if args.check:return
    output = args.output or HERE/'outputs/model_runs'/datetime.now().strftime('%Y%m%d_%H%M%S')
    output = output.resolve()
    if output.exists():parser.error('Output must be fresh; previous results are preserved')
    output.parent.mkdir(parents=True,exist_ok=True)
    schools = [39063501,39063502] if args.all_replication else [args.school]
    captures = [61001,61002] if args.all_replication else [args.capture_seed]
    duration = .5 if args.quick else 36.
    command = [sys.executable,str(runtime/'research/exposed_replication_2026-11-08/run.py'),
        '--smoke' if args.quick else '--execute','--duration',str(duration),
        '--output',str(output),'--workers',str(args.workers),'--policies','exposed',
        '--schools',*map(str,schools),'--capture-seeds',*map(str,captures),'--presences','D','DG']
    log_path = output.with_name(output.name+'.log')
    print(f'Running the frozen model: {len(schools)*len(captures)*2} cases × {duration:g}T; output={output}',flush=True)
    started = time.monotonic()
    with log_path.open('w') as log:
        process = subprocess.Popen(command,cwd=runtime,env=environment,stdout=log,stderr=subprocess.STDOUT)
        while True:
            try:
                code = process.wait(timeout=15)
                break
            except subprocess.TimeoutExpired:
                progress = []
                for file in sorted((output/'cases').glob('*/progress.json')):
                    try:
                        row = json.loads(file.read_text())
                        progress.append(f'{file.parent.name}: {row["elapsed"]:.1f}/{duration:g}T')
                    except (ValueError,KeyError):pass
                print(' | '.join(progress) if progress else 'Preparing actual model inputs...',flush=True)
    if code:
        raise RuntimeError(f'Actual model run failed; output retained at {output}.\n'+log_path.read_text()[-5000:])
    status = json.loads((output/'status.json').read_text())
    if status['status']!='complete':raise RuntimeError('Runner did not complete its requested cases')
    for directory in (output/'cases').iterdir():
        audit = json.loads((directory/'audit.json').read_text())
        if audit['status']!='passed':raise RuntimeError(f'Run audit failed: {directory.name}')
        seal = json.loads((directory/'completion.json').read_text())
        for name,digest in seal['files'].items():
            if sha(directory/name)!=digest:raise RuntimeError(f'Run seal differs: {directory.name}/{name}')
    receipt = dict(status='passed',mode='quick_integration' if args.quick else 'full_encounter',
        actual_model=True,behavioral_code_modified=False,checkpoint_arrays_modified=False,
        duration_per_case_T=duration,cases=len(schools)*len(captures)*2,
        native_steps=round(duration/.00125)*len(schools)*len(captures)*2,
        wall_seconds=time.monotonic()-started,command=command,runtime_relocation=str(runtime/'NOTEBOOK_RELOCATION.json'),
        output=str(output),interpretation='Quick check is too short to test the 2T herding cycle or feeding benefit.' if args.quick else 'New matched runs under the frozen model assumptions; separate from bundled historical data.')
    (output/'notebook_execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
