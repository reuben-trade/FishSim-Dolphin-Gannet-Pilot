"""Focused, explicitly synthetic snapshot-file/directory contract regressions.

Uses the real byte-pinned portable reader. Creates no feeding rows, bootstrap
draws, native constructors or production evidence. Existing v1 model/pure-state
proofs are reused; this suite tests only the corrected operational interface.
"""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, shutil, sys, tempfile, unittest
import primary_runtime as runtime

READER = Path('/home/venture/uwa/complex-systems/FishSim-RL/research/validation_portable_export_2026-11-10/portable_reader.py')
READER_SHA = '3d08ad828a2bb64c93492a7181ba5351d66ae57d4118b4eee877c0126a7c95e3'
V1 = Path('/home/venture/FishSim_Primary_Model_Candidate_2026-11-10')

def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    return path

def real_reader():
    if runtime.sha(READER) != READER_SHA:
        raise AssertionError('Actual reviewed portable reader changed')
    spec=importlib.util.spec_from_file_location('_real_pinned_reader_contract_test',READER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def make_synthetic_manifest(root):
    """Small API-only fixture; not a production snapshot or model outcome."""
    root.mkdir(parents=True)
    reader=real_reader();objects={}
    def obj(value):
        raw=(json.dumps(value,sort_keys=True)+'\n').encode();digest=hashlib.sha256(raw).hexdigest()
        path=root/'objects'/digest;path.parent.mkdir(exist_ok=True);path.write_bytes(raw)
        objects[digest]=dict(path=str(path.relative_to(root)),bytes=len(raw))
        return digest
    source=obj(dict(marker='SYNTHETIC API SOURCE ONLY'))
    sources={'SYNTHETIC opaque source identity':source}
    freeze=obj(dict(source_sha256=sources))
    stats=obj(dict(marker='SYNTHETIC NO EFFECTS OR DRAWS'))
    table=obj(dict(marker='SYNTHETIC NO FEEDING ROWS'))
    owner=obj(dict(status='passed',full_cases=192,independent_schools=16,
        replicate_labels=2,primary_grid='fine',source_freeze_sha256=freeze,
        native_steps_executed_by_analysis=0,files={'statistics.json':stats,'case_outcomes.csv':table}))
    final=obj(dict(status='passed',stage='final',new_full_cases=192,
        independent_schools=16,reused_discovery_cases_in_estimate=0,
        audit_source_sha256=reader.AUDITOR,freeze_sha256=freeze,
        bindings=dict(execution_freeze_sha256=freeze),native_constructions_by_review=0,
        native_steps_by_review=0,analysis_audit_sha256=owner))
    meta=obj(dict(status='passed',stage='final_publication_metadata_supplement',
        schema='fishsim_primary_final_metadata_supplement_v1',
        sidecar_source_sha256=reader.SIDECAR,original_auditor_sha256=reader.AUDITOR,
        original_final_review_sha256=final,analysis_audit_sha256=owner,
        execution_freeze_sha256=freeze,statistics_sha256=stats,case_csv_sha256=table,
        cases=192,independent_school_clusters=16,original_final_receipt_mandatory=True,
        original_final_receipt_replaced=False,scientific_effects_intervals_or_decision_recomputed=False,
        scientific_success_required=False,native_imports=0,native_constructions=0,native_steps=0,native_leases=0))
    manifest=put(root/'SNAPSHOT.json',dict(schema='fishsim_primary192_portable_snapshot_v1',
        kind='SYNTHETIC_TEMP_ONLY',production_accepted=False,reader_sha256=READER_SHA,
        objects=objects,sources=sources,reporter_assets={},
        analysis={'statistics.json':stats,'case_outcomes.csv':table},
        evidence=dict(independent_final=final,metadata_sidecar=meta,analysis_audit=owner,source_freeze=freeze)))
    put(root/'EXPORT_RECEIPT.json',dict(kind='SYNTHETIC_TEMP_ONLY',
        manifest_sha256=runtime.sha(manifest),reader_sha256=READER_SHA))
    return manifest

class SnapshotContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='FishSim SYNTHETIC snapshot contract ',dir='/home/venture')
        self.base=Path(self.temp.name)
        self.file=make_synthetic_manifest(self.base/'snapshot directory with spaces')
        self.package=self.base/'package with spaces';(self.package/'validation_tools').mkdir(parents=True)
        shutil.copy2(READER,self.package/'validation_tools/portable_reader.py')
    def tearDown(self):
        self.temp.cleanup()
    def test_file_and_directory_use_real_pinned_api_and_same_declaration_hash(self):
        reader=real_reader();expected=self.file.resolve();results=[]
        for argument in (self.file,self.file.parent,str(self.file),str(self.file.parent)):
            normalized=runtime.snapshot_manifest_file(argument)
            self.assertEqual(normalized,expected)
            saved=reader.Snapshot(normalized,allow_synthetic=True)
            reader.validate_evidence(saved)
            self.assertTrue(saved.synthetic);self.assertFalse(saved.manifest['production_accepted'])
            provenance=runtime.snapshot_provenance(saved);results.append(provenance)
            self.assertEqual(provenance,dict(snapshot_manifest_sha256=runtime.sha(expected),
                snapshot_manifest_file=str(expected),snapshot_root=str(expected.parent)))
        self.assertTrue(all(row==results[0] for row in results))
    def test_production_prepare_rejects_synthetic_same_way_for_both_forms(self):
        for i,argument in enumerate((self.file,self.file.parent)):
            output=self.base/f'never prepared runtime {i}'
            with self.assertRaisesRegex(ValueError,'Synthetic fixtures require explicit opt-in'):
                runtime.prepare(self.package,output,'historical',argument)
            self.assertFalse(output.exists())
    def test_missing_wrong_named_and_nonpath_inputs_fail_before_reader(self):
        empty=self.base/'empty directory';empty.mkdir()
        for argument in (empty,self.base/'missing directory'/'SNAPSHOT.json'):
            with self.assertRaises(FileNotFoundError):runtime.snapshot_manifest_file(argument)
        wrong=put(self.base/'other.json',{})
        for argument in (wrong,self.base/'not_a_manifest',None,123):
            with self.assertRaises((ValueError,TypeError)):runtime.snapshot_manifest_file(argument)
    def test_missing_and_changed_reader_fail_closed(self):
        path=self.package/'validation_tools/portable_reader.py'
        path.unlink()
        with self.assertRaisesRegex(RuntimeError,'not yet installed'):
            runtime.load_accepted_snapshot(self.package,self.file.parent)
        path.write_text('# changed reader\n')
        with self.assertRaisesRegex(RuntimeError,'differs from pinned'):
            runtime.load_accepted_snapshot(self.package,self.file)
    def test_symlink_directory_normalizes_to_one_exact_manifest(self):
        alias=self.base/'directory alias with spaces';alias.symlink_to(self.file.parent,target_is_directory=True)
        self.assertEqual(runtime.snapshot_manifest_file(alias),self.file.resolve())
        link=self.base/'SNAPSHOT.json';link.symlink_to(self.file)
        self.assertEqual(runtime.snapshot_manifest_file(link),self.file.resolve())
    def test_real_reader_evidence_gate_remains_before_source_object_resolution(self):
        tree=ast.parse((runtime.HERE/'primary_runtime.py').read_text())
        functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        loader=ast.unparse(functions['load_accepted_snapshot'])
        self.assertLess(loader.index('module.Snapshot(manifest)'),loader.index('module.validate_evidence(saved)'))
        self.assertLess(loader.index('module.validate_evidence(saved)'),loader.index('return saved'))
        lookup=ast.unparse(functions['input_paths'])
        self.assertLess(lookup.index('load_accepted_snapshot('),lookup.index('saved.path_for('))
        self.assertNotIn('allow_synthetic',loader)
        reader=real_reader();saved=reader.Snapshot(self.file,allow_synthetic=True)
        del saved.manifest['evidence']['metadata_sidecar']
        with self.assertRaises(KeyError):reader.validate_evidence(saved)
    def test_only_snapshot_operational_functions_changed_and_v1_is_exact(self):
        original=runtime.read(V1/'HANDOFF_FROZEN.json')
        self.assertEqual(runtime.sha(V1/'HANDOFF_FROZEN.json'),'b6ed64c8f6df737e83912ab68a58462770f9496ea4d2b0e293d66d7a86ffb6ef')
        for name,digest in original['files'].items():self.assertEqual(runtime.sha(V1/name),digest,name)
        for name in ('primary_gate.py','primary_worker.py','run_primary_model.py','MODEL_INPUTS.json','REFERENCE_MANIFEST.json','test_primary_model.py'):
            self.assertEqual(runtime.sha(V1/name),runtime.sha(runtime.HERE/name),name)
        def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
        old,new=functions(V1/'primary_runtime.py'),functions(runtime.HERE/'primary_runtime.py')
        self.assertEqual(set(new)-set(old),{'snapshot_manifest_file','load_accepted_snapshot','snapshot_provenance'})
        for name in set(old)-{'input_paths','prepare'}:self.assertEqual(old[name],new[name],name)
        self.assertFalse((runtime.HERE/'PRIMARY_MODEL_RELEASE.json').exists())
        self.assertFalse(any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules))
    def test_prepare_uses_tested_manifest_provenance_and_other_operations_are_exact(self):
        def nodes(path):return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
        old,new=nodes(V1/'primary_runtime.py'),nodes(runtime.HERE/'primary_runtime.py')
        call=next(n for n in ast.walk(new['prepare']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='snapshot_provenance')
        self.assertEqual(ast.unparse(call),'snapshot_provenance(saved)')
        before=next(n for n in ast.walk(old['prepare']) if isinstance(n,ast.Call) and any(k.arg=='snapshot_manifest_sha256' for k in n.keywords))
        after=next(n for n in ast.walk(new['prepare']) if isinstance(n,ast.Call) and any(k.arg is None for k in n.keywords))
        prior_keyword=next(k for k in before.keywords if k.arg=='snapshot_manifest_sha256')
        after.keywords=[copy.deepcopy(prior_keyword) if k.arg is None else k for k in after.keywords]
        self.assertEqual(ast.dump(old['prepare'],include_attributes=False),ast.dump(new['prepare'],include_attributes=False))
        before_if=next(n for n in old['input_paths'].body if isinstance(n,ast.If))
        after_if=next(n for n in new['input_paths'].body if isinstance(n,ast.If))
        self.assertEqual(ast.dump(ast.Module(body=before_if.orelse,type_ignores=[]),include_attributes=False),
            ast.dump(ast.Module(body=after_if.orelse,type_ignores=[]),include_attributes=False))
        self.assertEqual(ast.dump(ast.Module(body=before_if.body[-2:],type_ignores=[]),include_attributes=False),
            ast.dump(ast.Module(body=after_if.body[-2:],type_ignores=[]),include_attributes=False))
        after_if.body=copy.deepcopy(before_if.body)
        self.assertEqual(ast.dump(old['input_paths'],include_attributes=False),ast.dump(new['input_paths'],include_attributes=False))

if __name__=='__main__':unittest.main()
