"""New runtime checks and bounded integration; not executed during preparation."""
from __future__ import annotations

import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'

import argparse
from dataclasses import asdict
import importlib.util
from pathlib import Path
import platform
import sys
import tempfile
from unittest.mock import patch

import numpy as np

from regime_runtime import HERE, STUDY, INPUT_MANIFEST, read, write, sha, verify_runtime, verify_package, golden_case_folder


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def configure(runtime, approval, stage):
    if sys.flags.optimize or sys.version_info[:2] != (3, 12) or platform.system() != 'Linux':
        raise RuntimeError('Actual model checking requires unoptimized CPython3.12 on Linux; platform portability is not asserted')
    declaration = verify_runtime(runtime)
    verify_package(Path(declaration['package']))
    os.environ['FISHSIM_REGIME_EXAMPLE_RUNTIME'] = str(runtime)
    os.environ['FISHSIM_REGIME_EXAMPLE_REQUEST'] = str(approval)
    from regime_example_gate import _context
    _, _, _, reviewed = _context()
    if reviewed.get('stage') != stage:
        raise RuntimeError('The fresh execution review does not authorize this stage')
    sys.path[:0] = [str(runtime / STUDY), str(runtime / 'lib'), str(runtime)]
    import fish_sim.cmodel as native
    if sha(native.__file__) != declaration['actual_native_sha256']:
        raise RuntimeError('Imported extension differs from the explicit active-native declaration')
    return declaration, reviewed


def pure_prepare(runtime):
    """Construct only Python state, with the extension/native boundaries blocked."""
    runtime = Path(runtime).resolve()
    declaration = verify_runtime(runtime)
    sys.path[:0] = [str(runtime / STUDY), str(runtime), str(runtime / 'lib')]
    builder = load('build', runtime / STUDY / 'regime_example_build.py')
    from research.prey_mediated import scenario
    from research.prey_mediated.encounter import Encounter
    from cases import combined_cases
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError('Native import/construction/stepping is forbidden in pure preparation')
    class NativeImportBlocker:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'fish_sim.cmodel' or fullname.startswith('fish_sim.cmodel.'):
                forbidden()
            return None
    blocker = NativeImportBlocker()
    sys.meta_path.insert(0, blocker)
    rows = []
    try:
        with patch.object(scenario, '_native_school', forbidden), patch.object(Encounter, '__init__', forbidden), patch.object(Encounter, 'step', forbidden):
            for case in combined_cases():
                prepared = builder.prepare_case(case)
                if len(prepared.initial.prey_ids) != 160 or prepared.scenario.dt != .00125:
                    raise AssertionError('Saved school count/coarse grid differs')
                receipt = prepared.receipt()
                rows.append(dict(case=case.asdict(), checkpoint_sha256=prepared.metadata['checkpoint_sha256'],
                    initial_receipt=receipt, fish=builder.clean(asdict(prepared.initial))))
    finally:
        sys.meta_path.remove(blocker)
    if calls or 'fish_sim.cmodel' in sys.modules:
        raise AssertionError('Pure preparation unexpectedly imported/constructed native code')
    return dict(status='passed', cases=rows, pure_cases=len(rows), native_imports=0,
                native_constructions=0, native_steps=0, runtime_declaration_sha256=sha(runtime / 'REGIME_RUNTIME_DECLARATION.json'),
                scope='Pure states/planners/private streams only; native loading, normalization and integration are unvalidated')


def prepare_receipt_output(output):
    """Check the fresh destination before doing any native construction."""
    output = Path(output)
    if output.exists():
        raise RuntimeError('Actual initialization receipt must be a fresh file')
    output.parent.mkdir(parents=True, exist_ok=True)
    # An actual create/open catches permission, ACL and invalid-parent failures
    # before all108 initializations; no receipt or model data is written here.
    with tempfile.TemporaryFile(dir=output.parent):
        pass


def audit(runtime, approval, output):
    declaration, reviewed = configure(runtime, approval, 'zero_step_initialization')
    if output != Path(reviewed['output']).resolve() or output.exists():
        raise RuntimeError('Zero-step output must be the fresh one-shot reviewed destination')
    if reviewed.get('maximum_native_steps') != 0 or reviewed.get('native_constructions') != 108:
        raise RuntimeError('Zero-step review must explicitly cover exactly108 starts and zero steps')
    prepare_receipt_output(output)
    builder = load('build', runtime / STUDY / 'regime_example_build.py')
    runner = load('_regime_example_execution', runtime / STUDY / 'regime_example_execution.py')
    from cases import combined_cases
    from research.prey_mediated.encounter import Encounter
    from research.prey_mediated.scenario import TravellingSchool
    from research.prey_mediated.surface_safe_school import SurfaceSafeSchool
    snapshots, schools, rows = {}, {}, []
    package = Path(declaration['package'])
    golden_manifest = read(package / INPUT_MANIFEST)['files']
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError('Zero-step initialization audit must not step the model')
    with patch.object(Encounter, 'step', forbidden), patch.object(TravellingSchool, 'step', forbidden), patch.object(SurfaceSafeSchool, 'step', forbidden):
        for case in combined_cases():
            engine, metadata = builder.build(case.school_seed, case.policy, 61001, case.presence)
            fish = asdict(engine.school.state())
            snap = runner.snapshot(engine)
            golden = golden_case_folder(package, case)
            for filename in ('initial_engine.json', 'initial_school.npz'):
                relative = str((golden / filename).relative_to(package))
                if sha(golden / filename) != golden_manifest[relative]:
                    raise AssertionError('Protected historical actual-initial-state input changed')
            if snap != read(golden / 'initial_engine.json'):
                raise AssertionError('Actual actor/controller/private state differs from the archived actual start')
            with np.load(golden / 'initial_school.npz', allow_pickle=False) as archived:
                if set(archived.files) != set(fish) or any(not np.array_equal(np.asarray(fish[k]), archived[k]) for k in archived.files):
                    raise AssertionError('Actual native fish arrays differ from the exact archived actual start')
            snapshots[case.name], schools[case.name] = snap, fish
            pure = builder.prepare_case(case)
            if snap != pure.receipt():
                raise AssertionError('Actual initialized actor/controller/private state differs from pure preparation')
            if not np.array_equal(fish['positions'], pure.initial.positions) or not np.array_equal(fish['prey_ids'], pure.initial.prey_ids):
                raise AssertionError('Native constructor changed saved fish positions or IDs')
            # The unchanged C++ loader normalizes headings; verify the documented
            # roundoff bound against raw saved checkpoint, never silently rewrite it.
            if np.max(abs(fish['directions'] - pure.initial.directions), initial=0.) > 1e-12:
                raise AssertionError('Checkpoint heading normalization exceeds recorded native loading bound')
            expected = next((schools[name] for name in schools if name != case.name and name.startswith('s' + str(case.school_seed) + '_')), None)
            if expected is not None and (set(expected) != set(fish) or any(not np.array_equal(np.asarray(expected[k]), np.asarray(fish[k])) for k in fish)):
                raise AssertionError('Actual native fish arrays differ across H/count/presence starts')
            rows.append(dict(case=case.asdict(), checkpoint_sha256=metadata['checkpoint_sha256'],
                             archived_actual_engine_sha256=sha(golden / 'initial_engine.json'),
                             archived_actual_school_sha256=sha(golden / 'initial_school.npz'),
                             native_constructions=1, native_steps=0))
    # Common species have the same stable-ID readiness, physical and capture
    # streams across presence/count/H. Dolphin controller H differs by design.
    for a in rows:
        ca = a['case']
        for b in rows:
            cb = b['case']
            if ca['school_seed'] != cb['school_seed']:
                continue
            x, y = snapshots[ca['case_name']], snapshots[cb['case_name']]
            common = set(x['capture_rng']) & set(y['capture_rng'])
            for who in common:
                xa = next(v for v in x['actors'] if v['actor_id'] == who)
                ya = next(v for v in y['actors'] if v['actor_id'] == who)
                if xa != ya or x['actor_policy'][who] != y['actor_policy'][who] or x['capture_rng'][who] != y['capture_rng'][who]:
                    raise AssertionError('Common stable-ID physical/readiness/capture initialization differs')
                if who.startswith('G') or ca['herding_minimum_T'] == cb['herding_minimum_T']:
                    if x['controllers'][who] != y['controllers'][who]:
                        raise AssertionError('Shared-controller start differs unexpectedly')
            if x['tie_rng'] != y['tie_rng']:
                raise AssertionError('Private tie stream differs across matched starts')
    if calls:
        raise AssertionError('Zero-step check attempted native integration')
    receipt = dict(status='passed', schema='fishsim_regime_example_zero_v1', native_steps=0,
        native_constructions=108, cases=rows, independent_schools=4, actual_native_sha256=declaration['actual_native_sha256'],
        native_kind=declaration['native_kind'], runtime_declaration_sha256=sha(runtime / 'REGIME_RUNTIME_DECLARATION.json'),
        execution_request_sha256=sha(approval), independent_execution_review_claimed=False,
        interface_source_review_sha256=sha(HERE / 'INTERFACE_SOURCE_REVIEW.json'), historical_anchor_replay=False,
        archived_input_manifest_sha256=sha(package / INPUT_MANIFEST),
        scope='Actual initialization only; exact archived actual fish/actor/controller/private starts and exact cross-arm starts; no feeding/integration claim')
    write(output, receipt)


def integrate(runtime, approval, output):
    declaration, reviewed = configure(runtime, approval, 'bounded_example_integration')
    if output != Path(reviewed['output']).resolve():
        raise RuntimeError('Integration output differs from the one-shot reviewed destination')
    from run_v6_example import validate_zero
    validate_zero(runtime, Path(reviewed['zero_step_receipt']['path']), Path(reviewed['zero_step_seal']['path']))
    zero = read(Path(reviewed['zero_step_receipt']['path']))
    if (sha(reviewed['zero_step_receipt']['path']) != reviewed['zero_step_receipt']['sha256']
            or zero.get('status') != 'passed' or zero.get('native_steps') != 0
            or zero.get('native_constructions') != 108 or len(zero.get('cases', [])) != 108
            or zero.get('actual_native_sha256') != declaration['actual_native_sha256']
            or zero.get('runtime_declaration_sha256') != sha(runtime / 'REGIME_RUNTIME_DECLARATION.json')):
        raise RuntimeError('Integration requires a distinct completed source-bound zero-step check')
    load('build', runtime / STUDY / 'regime_example_build.py')
    runner = load('_regime_example_execution', runtime / STUDY / 'regime_example_execution.py')
    results = []
    for case in reviewed['cases']:
        result = runner.run_case(case['school_seed'], case['policy'], str(output), case['duration_T'],
                                 case['capture_seed'], True, case['presence'])
        results.append(result)
    receipt = dict(status='passed', schema='fishsim_regime_example_integration_v1',
        cases=len(results), native_steps=sum(x['native_steps'] for x in results),
        maximum_native_steps=reviewed['maximum_native_steps'], actual_native_sha256=declaration['actual_native_sha256'],
        native_kind=declaration['native_kind'], runtime_declaration_sha256=sha(runtime / 'REGIME_RUNTIME_DECLARATION.json'),
        execution_request_sha256=sha(approval), independent_execution_review_claimed=False,
        interface_source_review_sha256=sha(HERE / 'INTERFACE_SOURCE_REVIEW.json'), historical_anchor_replay=False,
        interpretation='A short new model integration example; not a partner-benefit estimate or a replacement for the saved36T map')
    if receipt['native_steps'] > receipt['maximum_native_steps']:
        raise AssertionError('Integration exceeded its reviewed native-step budget')
    write(output / 'REGIME_EXAMPLE_EXECUTION.json', receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--request', type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pure', action='store_true')
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--integrate', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    runtime, output = args.runtime.resolve(), args.output.resolve()
    if args.pure:
        write(output, pure_prepare(runtime))
    elif args.request is None:
        parser.error('Actual initialization/integration needs an explicit local execution request and reviewed interface')
    elif args.check:
        audit(runtime, args.request.resolve(), output)
    else:
        if output.exists():
            parser.error('New integration needs a fresh output directory')
        output.mkdir(parents=True)
        integrate(runtime, args.request.resolve(), output)


if __name__ == '__main__':
    main()
