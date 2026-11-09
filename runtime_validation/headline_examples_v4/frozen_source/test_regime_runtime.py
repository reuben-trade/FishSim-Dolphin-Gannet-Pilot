"""Native-free contract tests for the separately declared regime example."""
from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io

import numpy as np

from regime_runtime import (HERE, STUDY, CLOSURE, INPUT_MANIFEST, HISTORICAL_SHA, destination_relative,
                            RETAINED_STUDY, generate_execution, generate_builder, read, relocate, safe_output, sha,
                            verify_package, verify_runtime)
from run_regime_model import parse, plan

PACKAGE = Path(os.environ.get('FISHSIM_EXAMPLE_TEST_PACKAGE', '/home/venture/FishSim-Dolphin-Gannet-Pilot'))
RUNTIME = Path(os.environ.get('FISHSIM_EXAMPLE_TEST_RUNTIME', '/tmp/FishSim_Paper_Model_v4_Historical_Work/model'))
PURE = RUNTIME.parent / 'PURE_PREPARATION.json'


class NativeFreeContract(unittest.TestCase):
    def test_frontend_defaults_to_plan_and_public_source_built_artifact(self):
        import run_v6_example as frontend
        _, args = frontend.parse(['--package-root', str(PACKAGE)])
        self.assertTrue(args.plan)
        self.assertFalse(args.check or args.quick)
        self.assertEqual(args.native_kind, 'source-built')
        with patch.object(frontend, 'ensure_zero', side_effect=AssertionError('Plan must not initialize')), \
             patch.object(frontend, 'worker', side_effect=AssertionError('Plan must not execute')), \
             patch.object(frontend, 'prepare_runtime', side_effect=AssertionError('Plan must not copy runtime')):
            stream = io.StringIO()
            with redirect_stdout(stream):
                frontend.main(['--package-root', str(PACKAGE)])
        report = json.loads(stream.getvalue())
        self.assertFalse(report['default_native_execution'])
        self.assertEqual(report['selected_native_sha256'], 'cc21f00f355e1d25e8ecb48bd6aa50a7c9b63f909d921f4864a96e91d9ef2d4b')

    def test_local_request_is_durable_source_bound_and_not_reviewer_approval(self):
        import run_v6_example as frontend
        from regime_runtime import interface_hashes
        folder = Path('/tmp/FishSim_v4_Pure_Frontend_Fixtures') / ('request_' + RUNTIME.parent.name)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'execution_request.json'
        payload = frontend.request_payload(RUNTIME, 'zero_step_initialization', folder / 'not_executed_zero.json')
        self.assertEqual(payload['schema'], frontend.REQUEST_SCHEMA)
        self.assertTrue(payload['explicit_local_opt_in'])
        self.assertFalse(payload['independent_review'])
        self.assertNotIn('approved', payload)
        self.assertEqual(payload['interface_files'], interface_hashes())
        self.assertEqual(payload['request_generator_sha256'], sha(HERE / 'run_v6_example.py'))
        self.assertEqual(payload['maximum_native_steps'], 0)
        if not path.exists():
            frontend.write_request(path, payload)
        self.assertTrue(path.is_file())
        with self.assertRaises(ValueError):
            frontend.write_request(path, payload)

    def test_bad_explicit_pair_output_fails_before_zero_check_or_worker(self):
        import run_v6_example as frontend
        with patch.object(frontend, 'ensure_zero', side_effect=AssertionError('Invalid output must not initialize')), \
             patch.object(frontend, 'worker', side_effect=AssertionError('Invalid output must not execute')):
            with self.assertRaises(ValueError), redirect_stdout(io.StringIO()):
                frontend.main(['--quick', '--native-kind', 'historical' if verify_runtime(RUNTIME)['native_kind'] == 'historical_pinned_binary' else 'source-built',
                               '--package-root', str(PACKAGE), '--runtime', str(RUNTIME), '--output', str(PACKAGE / 'data/new')])

    def test_bad_request_path_or_parent_is_rejected_before_initialization(self):
        import run_v6_example as frontend
        with tempfile.TemporaryDirectory(prefix='fishsim_v4_output_test_') as name:
            folder = Path(name)
            output = folder / 'pair'
            request = folder / 'pair_execution_request.json'
            request.write_text('{"unit_fixture_only":true}\n')
            with self.assertRaises(ValueError):
                frontend.preflight_pair_output(output, RUNTIME, PACKAGE)
            collision = folder / 'file_parent'
            collision.write_text('file\n')
            with self.assertRaises(OSError):
                frontend.preflight_pair_output(collision / 'pair', RUNTIME, PACKAGE)

    def test_existing_zero_uses_validator_and_never_constructs_again(self):
        import run_v6_example as frontend
        with tempfile.TemporaryDirectory(prefix='fishsim_v4_reuse_test_') as name:
            runtime = Path(name) / 'model'
            zero = runtime.parent / 'zero_check'
            zero.mkdir()
            for filename in ('ACTUAL_ZERO_STEP_EXAMPLE.json', 'ZERO_CHECK_SEAL.json'):
                (zero / filename).write_text('{"unit_fixture_only":true}\n')
            with patch.object(frontend, 'validate_zero', return_value={'unit_fixture_only':True}) as validator, \
                 patch.object(frontend, 'worker', side_effect=AssertionError('Reuse must not initialize again')):
                receipt, seal, reused = frontend.ensure_zero(runtime)
            self.assertTrue(reused)
            validator.assert_called_once_with(runtime, receipt, seal)

    def test_request_generator_is_part_of_immutable_runtime_interface(self):
        declaration = verify_runtime(RUNTIME)
        self.assertEqual(len(declaration['interface_files']), 5)
        self.assertEqual(declaration['request_generator_sha256'], sha(HERE / 'run_v6_example.py'))
        gate = (HERE / 'regime_example_gate.py').read_text()
        self.assertIn('fishsim_regime_example_execution_request_v1', gate)
        self.assertNotIn('fishsim_regime_example_execution_review_v1', gate)
        if (HERE / 'INTERFACE_SOURCE_REVIEW.json').exists():
            review = read(HERE / 'INTERFACE_SOURCE_REVIEW.json')
            self.assertEqual(review['schema'], 'fishsim_regime_example_interface_source_review_v1')
            self.assertEqual(review['review_kind'], 'independent_source_review')

    def test_zero_check_blocks_all_native_step_entrypoints_before_loop(self):
        tree = ast.parse((HERE / 'regime_runtime_worker.py').read_text())
        audit = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'audit')
        guarded = set()
        for node in ast.walk(audit):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'patch'
                    and node.func.attr == 'object' and len(node.args) >= 2
                    and isinstance(node.args[0], ast.Name) and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value == 'step'):
                guarded.add(node.args[0].id)
        self.assertEqual(guarded, {'Encounter', 'TravellingSchool', 'SurfaceSafeSchool'})
        precheck = next(n for n in ast.walk(audit) if isinstance(n, ast.Call)
                        and isinstance(n.func, ast.Name) and n.func.id == 'prepare_receipt_output')
        constructions = [n for n in ast.walk(audit) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute) and n.func.attr == 'build']
        self.assertTrue(constructions)
        self.assertLess(precheck.lineno, min(n.lineno for n in constructions))

    def test_zero_receipt_parent_is_created_and_checked_without_native_work(self):
        from regime_runtime_worker import prepare_receipt_output
        with tempfile.TemporaryDirectory(prefix='fishsim_regime_output_test_') as folder:
            root = Path(folder)
            output = root / 'newdir' / 'check.json'
            prepare_receipt_output(output)
            self.assertTrue(output.parent.is_dir())
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.iterdir()), [])
            output.write_text('{}\n')
            with self.assertRaises(RuntimeError):
                prepare_receipt_output(output)
            collision = root / 'file_parent'
            collision.write_text('file\n')
            with self.assertRaises(OSError):
                prepare_receipt_output(collision / 'check.json')

    def test_complete_package_and_exact_runtime_inventory(self):
        entries, frozen = verify_package(PACKAGE)
        self.assertEqual(len(entries), 2100)
        self.assertEqual(len(frozen), 2117)
        declaration = verify_runtime(RUNTIME)
        self.assertEqual(declaration['native_steps'], 0)
        self.assertEqual(declaration['native_constructions'], 0)
        self.assertTrue(declaration['archive_receipts_are_not_runtime_authorizations'])

    def test_all108_pure_preparations_match_published_actual_actor_states(self):
        pure = read(PURE)
        protected = read(PACKAGE / INPUT_MANIFEST)['files']
        self.assertEqual((pure['status'], pure['pure_cases'], pure['native_imports'], pure['native_constructions'], pure['native_steps']),
                         ('passed', 108, 0, 0, 0))
        for row in pure['cases']:
            with self.subTest(case=row['case']['case_name']):
                study = RETAINED_STUDY if row['case']['gannets'] in (0, 1, 3, 6) else STUDY
                folder = PACKAGE / 'data' / study / 'results/full_36T_v1/cases' / row['case']['case_name']
                for filename in ('initial_engine.json', 'initial_school.npz'):
                    relative = str((folder / filename).relative_to(PACKAGE))
                    self.assertEqual(sha(folder / filename), protected[relative])
                self.assertEqual(row['initial_receipt'], read(folder / 'initial_engine.json'))
                with np.load(folder / 'initial_school.npz', allow_pickle=False) as actual:
                    self.assertEqual(set(actual.files), set(row['fish']))
                    for key in actual.files:
                        saved = np.asarray(row['fish'][key])
                        if key == 'directions':
                            self.assertLessEqual(np.max(abs(actual[key] - saved), initial=0.), 1e-12)
                        else:
                            self.assertTrue(np.array_equal(actual[key], saved), key)

    def test_every_scientific_source_and_checkpoint_copy_is_byte_identical(self):
        for entry in read(PACKAGE / CLOSURE):
            relative = destination_relative(entry['original_path'])
            if relative.suffix in ('.py', '.npz'):
                self.assertEqual(sha(RUNTIME / relative), entry['sha256'], str(relative))

    def test_entire_execution_body_and_all_helpers_have_identical_ast(self):
        source = (RUNTIME / STUDY / 'run.py').read_text()
        generated, proof = generate_execution(source)
        self.assertEqual(generated, (RUNTIME / STUDY / 'regime_example_execution.py').read_text())
        self.assertEqual(proof['full_body_ast_sha256'], proof['generated_full_body_ast_sha256'])
        self.assertEqual(proof['unchanged_physical_accounting_nodes'], 40)
        old, new = ast.parse(source), ast.parse(generated)
        a = {x.name: x for x in old.body if isinstance(x, ast.FunctionDef)}
        b = {x.name: x for x in new.body if isinstance(x, ast.FunctionDef)}
        for name, node in b.items():
            if name != 'run_case':
                self.assertEqual(ast.dump(a[name]), ast.dump(node), name)
        self.assertEqual(ast.dump(ast.Module(body=a['run_case'].body[6:], type_ignores=[])),
                         ast.dump(ast.Module(body=b['run_case'].body[3:], type_ignores=[])))
        compile(generated, '<derived regime example>', 'exec')

    def test_generated_builder_changes_only_historical_artifact_gate(self):
        source = (RUNTIME / STUDY / 'build.py').read_text()
        generated, proof = generate_builder(source)
        self.assertEqual(generated, (RUNTIME / STUDY / 'regime_example_build.py').read_text())
        self.assertEqual(proof['historical_constructor_body_ast_sha256'], proof['generated_constructor_body_ast_sha256'])
        old, new = ast.parse(source), ast.parse(generated)
        a = {x.name: x for x in old.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}
        b = {x.name: x for x in new.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))}
        self.assertEqual(set(a), set(b))
        for name in a:
            if name != 'build':
                self.assertEqual(ast.dump(a[name]), ast.dump(b[name]), name)
        self.assertEqual(ast.dump(ast.Module(body=a['build'].body[3:], type_ignores=[])),
                         ast.dump(ast.Module(body=b['build'].body[3:], type_ignores=[])))
        self.assertNotIn('from evidence import', generated)
        compile(generated, '<derived high-count builder>', 'exec')

    def test_changed_historical_gate_contract_fails_closed(self):
        source = (RUNTIME / STUDY / 'run.py').read_text()
        with self.assertRaises(RuntimeError):
            generate_execution(source.replace("require_approval('smoke' if duration==4. else 'full')", "require_approval('full')", 1))

    def test_exact_external_checkpoint_paths_are_relocated_without_hash_rewriting(self):
        old = '/run/media/venture/DJ K4T/FishSim-herding-study-2026-11-06/study/results/development_fine_v1/inputs/s39061001.npz'
        mapped = destination_relative(old)
        self.assertEqual(mapped.parts[:3], ('external', 'run', 'media'))
        value = dict(path=old, sha256=HISTORICAL_SHA)
        after = relocate(value, {old: str(RUNTIME / mapped)})
        self.assertEqual(after, dict(path=str(RUNTIME / mapped), sha256=HISTORICAL_SHA))
        self.assertEqual(relocate(old + '_different', {old: 'new'}), old + '_different')

    def test_default_headline_and_joint_alternate_boundaries(self):
        _, args = parse(['--quick', '--package-root', str(PACKAGE)])
        proposed = plan(args)
        self.assertEqual(proposed['planned_integration_native_steps'], 6400)
        self.assertEqual([x['policy'] for x in proposed['example_cases']], ['H1_G0', 'H1_G9'])
        self.assertEqual(proposed['actual_zero_step_check_cases'], 108)
        _, joint = parse(['--quick', '--setting', 'joint', '--package-root', str(PACKAGE)])
        alternate = plan(joint)
        self.assertEqual([x['policy'] for x in alternate['example_cases']], ['H2_G0', 'H2_G12'])
        self.assertEqual(alternate['planned_integration_native_steps'], 3200)
        _, short = parse(['--integration', '--package-root', str(PACKAGE)])
        self.assertEqual(plan(short)['planned_integration_native_steps'], 800)
        self.assertEqual(proposed['native_steps'], 0)

    def test_two_binary_validation_budget_and_pair_order_are_exact(self):
        proposed_steps = 0
        for setting, expected in (('headline', 6400), ('joint', 3200)):
            _, args = parse(['--quick', '--setting', setting, '--package-root', str(PACKAGE)])
            value = plan(args)
            self.assertEqual([x['presence'] for x in value['example_cases']], ['D', 'DG'])
            self.assertEqual(value['planned_integration_native_steps'], expected)
            self.assertTrue(all(x['capture_seed'] == 61001 for x in value['example_cases']))
            proposed_steps += expected
        self.assertEqual(2 * proposed_steps, 19200)
        self.assertEqual(2 * 108, 216)

    def test_actual_archived_arrays_remain_exact_and_binary_roles_are_separate(self):
        worker = ast.parse((HERE / 'regime_runtime_worker.py').read_text())
        audit = next(n for n in worker.body if isinstance(n, ast.FunctionDef) and n.name == 'audit')
        calls = [n for n in ast.walk(audit) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertFalse(any(n.func.attr == 'allclose' for n in calls))
        archived_exact = [n for n in calls if n.func.attr == 'array_equal' and len(n.args) == 2
                          and isinstance(n.args[1], ast.Subscript) and isinstance(n.args[1].value, ast.Name)
                          and n.args[1].value.id == 'archived']
        self.assertEqual(len(archived_exact), 1)
        declaration = verify_runtime(RUNTIME)
        reference = declaration['historical_actor_reference']
        self.assertEqual(reference['sha256'], HISTORICAL_SHA)
        self.assertFalse(reference['executed'])
        self.assertEqual(sha(reference['path']), HISTORICAL_SHA)
        active = RUNTIME / 'lib/fish_sim/cmodel.cpython-312-x86_64-linux-gnu.so'
        self.assertEqual(sha(active), declaration['actual_native_sha256'])
        native_reference = read(RUNTIME / 'research/prey_mediated/results/short_angular_physical_g3_v1/native.json')
        self.assertEqual(native_reference['path'], reference['path'])
        self.assertEqual(native_reference['sha256'], HISTORICAL_SHA)

    def test_full_ensemble_and_unbounded_horizons_are_not_silently_exposed(self):
        with self.assertRaises(SystemExit):
            parse(['--quick', '--package-root', str(PACKAGE), '--duration', '36'])
        pins = read(HERE / 'REGIME_RUNTIME_INPUTS.json')
        self.assertTrue(pins['G9_G12_G18_model_initialization_scope'])
        self.assertEqual(pins['proposed_validation_max_native_steps'], 19200)

    def test_protected_sources_cannot_be_selected_as_output(self):
        for path in (PACKAGE, PACKAGE / 'data/new', HERE / 'new',
                     Path('/home/venture/uwa/complex-systems/FishSim-RL/research/new'),
                     Path('/run/media/venture/DJ K4T/FishSim-herding-study-2026-11-06/new'),
                     Path('/tmp')):
            with self.assertRaises(ValueError):
                safe_output(path, PACKAGE)

    def test_actual_modes_without_fresh_review_fail_before_native_worker(self):
        environment = os.environ.copy()
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        for mode in ('--check', '--quick'):
            result = subprocess.run([sys.executable, '-B', str(HERE / 'run_regime_model.py'), mode,
                                     '--package-root', str(PACKAGE), '--runtime', str(RUNTIME)],
                                    env=environment, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('not been authorized', result.stderr)
        self.assertFalse((RUNTIME.parent / 'ACTUAL_ZERO_STEP_EXAMPLE.json').exists())
        self.assertFalse((RUNTIME.parent / 'headline_example_4T').exists())

    def test_no_historical_gate_import_or_scientific_global_assignment(self):
        generated = ast.parse((RUNTIME / STUDY / 'regime_example_execution.py').read_text())
        imports = [x.module for x in generated.body if isinstance(x, ast.ImportFrom)]
        self.assertNotIn('evidence', imports)
        calls = {x.func.id for x in ast.walk(generated) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)}
        self.assertFalse({'require_anchor_stage', 'require_approval', 'verify_source_freeze'} & calls)
        gate = ast.parse((HERE / 'regime_example_gate.py').read_text())
        assigned_attributes = [x for x in ast.walk(gate) if isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Store)]
        self.assertFalse(assigned_attributes)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeFreeContract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = dict(status='passed' if result.wasSuccessful() else 'failed', tests=result.testsRun,
                  failures=len(result.failures), errors=len(result.errors),
                  native_imports=0, native_constructions=0, native_steps=0,
                  runtime=str(RUNTIME), pure_preparation_sha256=sha(PURE),
                  runtime_declaration_sha256=sha(RUNTIME / 'REGIME_RUNTIME_DECLARATION.json'),
                  test_sha256=sha(__file__), scientific_code_unchanged=True,
                  independent_review_status='pending', actual_initialization='not_run', actual_integration='not_run')
    (HERE / 'PURE_VALIDATION.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
