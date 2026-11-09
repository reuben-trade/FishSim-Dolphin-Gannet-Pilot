"""Bounded container integration gate; never a scientific ensemble."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/validation')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    expected = read(ROOT/'EXPECTED_COMPILED_NATIVE.json')
    native = Path('/opt/fishsim-native')
    build = read(native/'NATIVE_BUILD.json')
    for filename, digest in expected['native_files'].items():
        if sha(native/filename) != digest:
            raise RuntimeError('Compiled runtime differs from reviewed OCI: '+filename)
    manifest = read(ROOT/'VALIDATION_INPUTS.json')
    for relative, digest in manifest['files'].items():
        if sha(ROOT/relative) != digest:
            raise RuntimeError('Validation input changed: '+relative)
    work, outputs, exported = (ROOT/name for name in ('work','outputs','export'))
    if any(path.exists() for path in (work,outputs,exported)):
        raise RuntimeError('Fresh validation outputs required; no retries')
    exported.mkdir()
    common = [sys.executable,str(ROOT/'runner/run_current_model.py'),
              '--backend','native','--package-root',str(ROOT/'package'),
              '--work',str(work),'--candidate-native',str(native/build['binary_filename']),
              '--candidate-record',str(native/'NATIVE_BUILD.json'),
              '--workers','1','--school','39064501','--presences','D','DG']
    environment = os.environ.copy()
    environment.pop('PYTHONOPTIMIZE',None)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        environment[key] = '1'
    jobs = [
        ('initialization',common+['--check']),
        ('coarse_quick',common+['--quick','--grid','coarse','--output',str(outputs/'coarse_quick')]),
        ('fine_quick',common+['--quick','--grid','fine','--output',str(outputs/'fine_quick')]),
        ('fine_4T',common+['--run','--duration','4','--grid','fine','--output',str(outputs/'fine_4T')]),
    ]
    operations=[]
    for name,command in jobs:
        print(json.dumps(dict(stage=name,command=command)),flush=True)
        with (exported/(name+'.log')).open('x') as log:
            subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT,check=True)
        operations.append(dict(stage=name,command=command,log_sha256=sha(exported/(name+'.log'))))
    cases=[];total=0
    for name,expected_steps,duration,dt in [('coarse_quick',400,.5,.00125),
                                             ('fine_quick',800,.5,.000625),
                                             ('fine_4T',6400,4.,.000625)]:
        folder=outputs/name
        receipt=read(folder/'current_model_execution.json')
        if (receipt['status']!='passed' or receipt['native_steps']!=2*expected_steps
                or receipt['actual_native_sha256']!=build['binary_sha256']
                or receipt['native_kind']!='explicit_separate_source_build'
                or receipt['dt']!=dt or receipt['duration_per_case_T']!=duration
                or {r['presence'] for r in receipt['cases']}!={'D','DG'}):
            raise RuntimeError('Unexpected bounded execution receipt: '+name)
        total+=receipt['native_steps']
        for case in receipt['cases']:
            path=folder/'cases'/f"s39064501_exposed_{case['presence']}_c61001"
            seal=read(path/'completion.json');audit=read(path/'audit.json');summary=read(path/'summary.json')
            if sha(path/'completion.json')!=case['completion_sha256']:
                raise RuntimeError('Case completion digest changed')
            for relative,digest in seal['files'].items():
                if sha(path/relative)!=digest:
                    raise RuntimeError('Case sealed file changed: '+relative)
            if (audit['status']!='passed' or audit['errors']
                    or audit['private_capture_and_tie_stream_replay']!='passed'
                    or summary['native_steps']!=expected_steps):
                raise RuntimeError('Case accounting or stream audit failed')
            cases.append(dict(stage=name,presence=case['presence'],native_steps=expected_steps,
                              completion_sha256=sha(path/'completion.json'),audit=audit,
                              species=summary['species']))
    if total!=15200 or len(cases)!=6:
        raise RuntimeError('Bounded validation budget or roster differs')
    declarations=list(work.glob('current_model_*/CURRENT_MODEL_DECLARATION.json'))
    if len(declarations)!=1:
        raise RuntimeError('One explicitly declared source-built runtime required')
    declaration=read(declarations[0])
    if (declaration['status']!='passed' or declaration['native_steps']!=0
            or declaration['zero_step_cases']!=24 or declaration['paired_grids']!=2
            or declaration['actual_native_sha256']!=build['binary_sha256']):
        raise RuntimeError('Cross-grid initial-state audit failed')
    historical_reference=declaration['historical_actor_reference_native']
    if (historical_reference['sha256']!=expected['historical_native_sha256']
            or sha(historical_reference['path'])!=expected['historical_native_sha256']):
        raise RuntimeError('Retained historical actor-reference pin changed')
    for relative,digest in declaration['runtime_files'].items():
        if sha(declarations[0].parent/relative)!=digest:
            raise RuntimeError('Derived runtime source changed: '+relative)
    shutil.copy2(declarations[0],exported/'CURRENT_MODEL_DECLARATION.json')
    shutil.copytree(outputs,exported/'outputs')
    report=dict(status='container_model_initialization_and_bounded_integration_passed',
        at=datetime.now(timezone.utc).isoformat(),native_steps=total,maximum_authorized_steps=15200,
        zero_step_constructions=48,feeding_ensembles_run=0,workers=1,school_seed=39064501,
        capture_seed=61001,operations=operations,cases=cases,
        actual_native_sha256=build['binary_sha256'],native_kind='explicit_separate_source_build',
        historical_native_sha256=expected['historical_native_sha256'],
        historical_actor_reference_native=historical_reference,
        native_field_roles=declaration['native_field_roles'],
        compiler=build['compiler'],python=build['python_version'],
        model_source_sha256=build['model_source_sha256'],
        installed_packages_sha256=sha(native/'INSTALLED_PACKAGES.txt'),
        reviewed_oci_sha256=expected['reviewed_oci_sha256'],
        original_checkpoints_and_scientific_code_modified=False,
        current_model_scope='Existing eight-school H2 coarse/fine replication, not H×G regime sweep',
        execution_scope='Linuxamd64 BuildKit validation target; packaged --backend docker bind-mount CLI not end-to-end tested',
        interpretation='Engineering initialization/integration checks only; no feeding-effect inference, full replication, convergence or historical-binary identity claim')
    (exported/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','model_source_sha256','operations')}),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException as error:
        # Complete the export transport so failed/partial evidence survives.
        # The outside executor requires VALIDATION.status to be passed and
        # fails the gate on this receipt; this is never a scientific pass.
        exported=ROOT/'export';exported.mkdir(exist_ok=True)
        outputs=ROOT/'outputs'
        if outputs.exists() and not (exported/'outputs').exists():
            shutil.copytree(outputs,exported/'outputs')
        retained=exported/'runtime_receipts';retained.mkdir(exist_ok=True)
        for name in ('RUNTIME_COPY_RECEIPT.json','CURRENT_MODEL_DECLARATION.json'):
            for path in (ROOT/'work').glob('current_model_*/'+name):
                shutil.copy2(path,retained/(path.parent.name+'_'+name))
        report=dict(status='failed_validation_evidence_retained',
            at=datetime.now(timezone.utc).isoformat(),error=repr(error),
            maximum_authorized_steps=15200,
            native_steps='See retained case summaries/failure/progress; no completed gate asserted',
            interpretation='Failed engineering check; partial evidence retained; no automatic retry')
        (exported/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
