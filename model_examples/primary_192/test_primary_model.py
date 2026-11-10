"""Native-free inventory, source, binding and accepted-reference negative tests."""
import ast,copy,io,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from primary_runtime import HERE,STUDY,HISTORICAL,SOURCE_BUILT,identity,inventory,steps,interfaces,derive_builder,derive_runner,read
from primary_gate import validate_release_artifact,validate_worker_binding
from primary_worker import DenyNative
from run_primary_model import select
from check_primary_replay import compare

ROOT=Path('/home/venture/uwa/complex-systems/FishSim-RL')
PACKAGE=Path('/home/venture/FishSim-Dolphin-Gannet-Pilot')

def release_fixture(kind='historical'):
    native=HISTORICAL if kind=='historical' else SOURCE_BUILT
    artifact=dict(active_native_sha256=native,runtime_declaration_sha256='a'*64)
    shared=dict(status='passed',interface_files=interfaces(),active_native_sha256=native,runtime_declaration_sha256='a'*64)
    names=[identity(39065501,71001,g,a)['case_name'] for g in ('coarse','fine') for a in ('D','G','DG')]
    tests=dict(source_review=dict(shared),actual_zero_review=dict(shared,native_constructions=192,native_steps=0,exact_case_names=[c['case_name'] for c in inventory()]),
        short4T_review=dict(shared,duration_T=4,source_execution_native_steps=28800,exact_case_names=names,exact_full_trajectory_and_event_replay=True),
        full36T_review=dict(shared,duration_T=36,source_execution_native_steps=259200,exact_case_names=names,exact_full_trajectory_and_event_replay=True))
    return artifact,tests

class ModelInterfaceTests(unittest.TestCase):
    def test_exact192_design_and_full_step_count(self):
        cases=inventory();self.assertEqual(len(cases),192);self.assertEqual(len({c['case_name'] for c in cases}),192)
        self.assertEqual(steps([dict(c,duration_T=36) for c in cases]),8294400)
        self.assertEqual({c['grid'] for c in cases},{'coarse','fine'})
    def test_both_artifact_engineering_ceiling_is576000(self):
        first=[c for c in inventory() if c['school_seed']==39065501 and c['capture_seed']==71001]
        short=steps([dict(c,duration_T=4) for c in first]);full=steps([dict(c,duration_T=36) for c in first])
        self.assertEqual((2*short,2*full,2*(short+full)),(57600,518400,576000))
    def test_invalid_or_silently_defaulted_worlds_rejected(self):
        args=SimpleNamespace(all_ensemble=False,school=0,label=71001,grid='fine',arms=None,duration=36)
        with self.assertRaises(ValueError):select(args)
        args.school=39065501;args.label=0
        with self.assertRaises(ValueError):select(args)
        args.label=71001;args.arms=''
        with self.assertRaises(ValueError):select(args)
    def test_entire_physical_tail_and_constructor_are_preserved(self):
        source=(ROOT/STUDY/'physical_run.py').read_text();generated,proof=derive_runner(source)
        self.assertTrue(proof['physical_tail_unchanged'])
        b,proof=derive_builder((ROOT/STUDY/'build.py').read_text());self.assertTrue(proof['pure_assembly_unchanged'])
        def functions(text):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(text).body if isinstance(x,ast.FunctionDef)}
        old,new=functions((ROOT/STUDY/'build.py').read_text()),functions(b)
        for f in ('prepare_from_initial','initial_private_streams','_seed_words','prepare_case'):self.assertEqual(old[f],new[f])
    def test_unknown_parent_preamble_is_rejected(self):
        text=(ROOT/STUDY/'physical_run.py').read_text().replace('Undeclared smoke case','Modified gate')
        with self.assertRaises(RuntimeError):derive_runner(text)
    def test_default_plan_rejects_native_imports(self):
        code='''import sys
from primary_worker import DenyNative
b=DenyNative();sys.meta_path.insert(0,b)
from run_primary_model import main
main(['--package-root',sys.argv[1],'--plan'])
assert not b.attempts
'''
        r=subprocess.run([sys.executable,'-B','-c',code,str(PACKAGE)],cwd=HERE,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);d=json.loads(r.stdout);self.assertEqual(d['cases'],3);self.assertEqual(d['selected_duration_T'],36);self.assertEqual(d['native_steps'],0)
    def test_actual_run_closed_before_runtime_or_lease(self):
        r=subprocess.run([sys.executable,'-B',str(HERE/'run_primary_model.py'),'--package-root',str(PACKAGE),'--run','--runtime','/nonexistent/not_runtime','--output','/tmp/FishSim_Primary_Uncreated_Run_Fixture'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('native gate CLOSED',r.stderr);self.assertNotIn('PRIMARY_RUNTIME.json',r.stderr)
    def test_no_default_approval_or_certificate_is_created(self):
        self.assertFalse((HERE/'PRIMARY_MODEL_RELEASE.json').exists())
    def test_worker_runtime_output_stage_bind_for_both_modes(self):
        for stage in ('zero','run'):
            validate_worker_binding('/tmp/A','/tmp/outA',stage,'/tmp/A','/tmp/outA',stage)
            for runtime,output,mode in [('/tmp/B','/tmp/outA',stage),('/tmp/A','/tmp/outB',stage),('/tmp/A','/tmp/outA','run' if stage=='zero' else 'zero')]:
                with self.assertRaises(RuntimeError):validate_worker_binding(runtime,output,mode,'/tmp/A','/tmp/outA',stage)
    def test_coherent_release_requires192zeros_and_actual4_and36_bothgrids(self):
        for kind in ('historical','source-built'):validate_release_artifact(kind,*release_fixture(kind))
    def test_short_proof_does_not_authorize36T(self):
        artifact,tests=release_fixture();tests['full36T_review']=copy.deepcopy(tests['short4T_review'])
        with self.assertRaises(RuntimeError):validate_release_artifact('historical',artifact,tests)
    def test_fine_only36_proof_does_not_authorize_bothgrids(self):
        artifact,tests=release_fixture();tests['full36T_review']['exact_case_names']=tests['full36T_review']['exact_case_names'][3:]
        with self.assertRaises(RuntimeError):validate_release_artifact('historical',artifact,tests)
    def test_cross_artifact_and_cross_declaration_proofs_rejected(self):
        for name in ('actual_zero_review','short4T_review','full36T_review'):
            for key,value in [('active_native_sha256',SOURCE_BUILT),('runtime_declaration_sha256','b'*64)]:
                artifact,tests=release_fixture();tests[name][key]=value
                with self.assertRaises(RuntimeError):validate_release_artifact('historical',artifact,tests)
    def test_incomplete_zero_or_wrong_full_budget_rejected(self):
        for name,key,value in [('actual_zero_review','native_constructions',191),('full36T_review','source_execution_native_steps',172800)]:
            artifact,tests=release_fixture();tests[name][key]=value
            with self.assertRaises(RuntimeError):validate_release_artifact('historical',artifact,tests)
    def test_native_entry_requires_lease_and_authority_before_import(self):
        t=ast.parse((HERE/'primary_worker.py').read_text());functions={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
        configure=ast.unparse(functions['configure']);self.assertLess(configure.index('authorize('),configure.index('import fish_sim.cmodel'))
        self.assertLess(configure.index('_LEASE_STATE'),configure.index('import fish_sim.cmodel'))
        main=ast.unparse(functions['main']);self.assertLess(main.index('authorize('),main.index('import fcntl'))
    def test_accepted_real_reference_streams_4T_and36T(self):
        for duration,group in [(4,'smoke4T'),(36,'full36T')]:
            folder=HERE/'references'/group/identity(39065501,71001,'fine','DG')['case_name']
            compare(folder,folder,duration)
    def test_changed_reference_trajectory_or_terminal_stream_is_rejected(self):
        source=HERE/'references/smoke4T'/identity(39065501,71001,'coarse','D')['case_name']
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_primary_replay_negative_') as temp:
            clone=Path(temp)/'mutated';shutil.copytree(source,clone)
            state=read(clone/'final_engine.json');state['tie_rng']['state']['state']+=1
            (clone/'final_engine.json').write_text(json.dumps(state))
            with self.assertRaisesRegex(AssertionError,'terminal'):compare(clone,source,4)
            shutil.copy2(source/'final_engine.json',clone/'final_engine.json')
            with np.load(clone/'trajectories.npz',allow_pickle=False) as saved:arrays={k:saved[k].copy() for k in saved.files}
            arrays['positions'][0,0,0]+=1e-9
            np.savez_compressed(clone/'trajectories.npz',**arrays)
            with self.assertRaisesRegex(AssertionError,'trajectory'):compare(clone,source,4)
    def test_author_path_guard_is_process_local_and_denies_original_open(self):
        code='''from primary_worker import install_author_path_guard
b=install_author_path_guard()
try:
    open('/home/venture/uwa/complex-systems/FishSim-RL/research/independent_validation_2026-11-10/cases.py').read()
except RuntimeError:
    assert len(b)==1
else:raise AssertionError('author path was not blocked')
'''
        r=subprocess.run([sys.executable,'-B','-c',code],cwd=HERE,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
