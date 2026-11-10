"""Focused synthetic-only outer-label/receipt-lineage regressions; no new draws."""
import ast,copy,hashlib,json,shutil,tempfile,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import integration as app
V2=Path(__file__).resolve().parent
V1=Path('/home/venture/FishSim_Final_Paper_Integration_2026-11-11')
CACHE=Path('/home/venture/task-ownedtestcache/final_notebook_labels_v2_2026-11-11')
HANDOFF=app.read(V1/'HANDOFF.json')
CLONE=Path(HANDOFF['proof']['private_clone'])
RUN=next((CLONE/'outputs').glob('SYNTHETIC_TEST_OUTPUTS_*/SYNTHETIC_NOTEBOOK_RUN_RECEIPT.json')).parent
UPSTREAM=RUN/'SYNTHETIC_validation/rendered'

class SyntheticRendererLabels(unittest.TestCase):
    def setUp(self):
        CACHE.mkdir(parents=True,exist_ok=True);self.temp=tempfile.TemporaryDirectory(prefix='SYNTHETIC_label_check_',dir=CACHE);self.root=Path(self.temp.name)
        self.source=self.root/'frozen renderer original';shutil.copytree(UPSTREAM,self.source)
        self.before={p.name:app.sha(p) for p in self.source.iterdir() if p.is_file()}
    def tearDown(self):self.temp.cleanup()
    def derive(self):return app.derive_synthetic_renderer_outputs(self.source,self.root/'derived',self.root/'SYNTHETIC_ORIGINALS.zip')
    def test_both_auxiliary_csvs_individually_marked_with_numeric_text_unchanged(self):
        result=self.derive();self.assertEqual(len(result['csv_derivations']),2)
        files=list((self.root/'derived').glob('*.csv'));self.assertEqual({p.name for p in files},{'SYNTHETIC_paired_school_means.csv','SYNTHETIC_nested_world_effects.csv'})
        for path in files:
            derived=app.table(path);original=app.table(self.source/path.name.removeprefix('SYNTHETIC_'))
            for row in derived:self.assertEqual(row.pop('data_kind'),'SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS')
            self.assertEqual(derived,original)
    def test_original_outputs_and_complete_archived_members_remain_byte_exact(self):
        result=self.derive();self.assertEqual({p.name:app.sha(p) for p in self.source.iterdir() if p.is_file()},self.before)
        with zipfile.ZipFile(self.root/'SYNTHETIC_ORIGINALS.zip') as saved:
            self.assertEqual(set(saved.namelist()),set(self.before))
            for name,digest in self.before.items():self.assertEqual(hashlib.sha256(saved.read(name)).hexdigest(),digest)
            original=json.loads(saved.read('render_receipt.json'))
            for name,digest in original['files'].items():self.assertEqual(hashlib.sha256(saved.read(name)).hexdigest(),digest)
        self.assertEqual(result['upstream_lineage']['archive_member_sha256'],self.before)
        self.assertEqual(result['upstream_lineage']['original_receipt_sha256'],self.before['render_receipt.json'])
        self.assertEqual(result['upstream_lineage']['archive_sha256'],app.sha(self.root/'SYNTHETIC_ORIGINALS.zip'))
        self.assertEqual(((self.root/'derived')/result['upstream_lineage']['archive_path_relative_to_receipt']).resolve(),(self.root/'SYNTHETIC_ORIGINALS.zip').resolve())
    def test_current_receipt_hashes_current_derived_bytes_separately_from_upstream(self):
        result=self.derive();folder=self.root/'derived';self.assertEqual(set(result['files']),{p.name for p in folder.iterdir()}-{'render_receipt.json'})
        for name,digest in result['files'].items():self.assertEqual(app.sha(folder/name),digest)
        original=app.read(self.source/'render_receipt.json')
        for name in ('paired_school_means.csv','nested_world_effects.csv'):
            self.assertNotIn(name,result['files']);self.assertNotEqual(result['files']['SYNTHETIC_'+name],original['files'][name])
        self.assertEqual(result['renderer_sha256'],app.RENDER_SHA)
    def test_tampered_original_rejected_before_creating_derived_output_or_archive(self):
        p=self.source/'paired_school_means.csv';p.write_bytes(p.read_bytes()+b'TAMPER\n')
        with self.assertRaisesRegex(ValueError,'Original renderer receipt mismatch'):self.derive()
        self.assertFalse((self.root/'derived').exists());self.assertFalse((self.root/'SYNTHETIC_ORIGINALS.zip').exists())
    def test_production_and_unexpected_original_inventory_rejected(self):
        p=self.source/'render_receipt.json';original=p.read_bytes();r=app.read(p);r['synthetic']=False;app.write(p,r)
        with self.assertRaisesRegex(ValueError,'Only synthetic'):self.derive()
        p.write_bytes(original);(self.source/'unexpected.csv').write_text('extra\n')
        with self.assertRaisesRegex(ValueError,'Unexpected original renderer inventory'):self.derive()
    def test_repeat_does_not_overwrite_lineage(self):
        self.derive();archive=app.sha(self.root/'SYNTHETIC_ORIGINALS.zip')
        with self.assertRaisesRegex(ValueError,'Never overwrite'):self.derive()
        self.assertEqual(app.sha(self.root/'SYNTHETIC_ORIGINALS.zip'),archive)
    def test_synthetic_route_exposes_six_marked_csvs_and_preserves_original_archive(self):
        # Reuse the already-accepted synthetic cache; do not call an RNG or model.
        profile=app.read(CLONE/'SYNTHETIC_PROFILE.json');manifest=CLONE/profile['validation']['snapshot_manifest']
        reader=app.load('_labels_review_cached_reader',V2/'validation_tools/portable_reader.py')
        result=reader.analyse_snapshot(manifest,allow_synthetic=True)
        session=app.Session.__new__(app.Session);session.profile=profile;session.root=V2;session.output=self.root/'run';session.output.mkdir()
        session.validation_result=result;session.validation_exports=None;session.reader=reader
        def frozen_render_fixture(argv,**kwargs):
            target=Path(argv[argv.index('--output')+1]);self.assertFalse(target.exists());shutil.copytree(self.source,target)
            return SimpleNamespace(stdout='SYNTHETIC frozen4040 reference fixture; no new render/draw/model\n')
        with patch.object(app.subprocess,'run',side_effect=frozen_render_fixture):exports=session.export_validation()
        csvs=list(session.output.rglob('*.csv'));self.assertEqual(len(csvs),6)
        for path in csvs:
            self.assertTrue(path.name.startswith('SYNTHETIC_'));self.assertTrue(all(r['data_kind']=='SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS' for r in app.table(path)))
        self.assertEqual(list(session.output.rglob('SYNTHETIC_RENDER_STAGE_*')),[])
        archives=list(session.output.rglob('SYNTHETIC_UPSTREAM_RENDERER_ORIGINALS.zip'));self.assertEqual(len(archives),1)
        self.assertTrue(exports['figure4'].exists());self.assertIs(result['production_accepted'],False)
    def test_only_synthetic_wrapper_changed_and_production_statement_is_AST_exact(self):
        old=ast.parse((V1/'integration.py').read_text());new=ast.parse((V2/'integration.py').read_text())
        new.body=[n for n in new.body if not(isinstance(n,ast.FunctionDef) and n.name=='derive_synthetic_renderer_outputs')]
        oi=next(n for n in old.body if isinstance(n,ast.Import));ni=next(n for n in new.body if isinstance(n,ast.Import));ni.names=[n for n in ni.names if n.name not in ('shutil','tempfile','zipfile')]
        def export(tree):return next(n for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='Session' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='export_validation')
        oe,ne=export(old),export(new)
        original=next(n for n in oe.body if isinstance(n,ast.Assign) and ast.unparse(n).startswith('completed = subprocess.run'))
        idx=next(i for i,n in enumerate(ne.body) if isinstance(n,ast.If) and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='derive_synthetic_renderer_outputs' for c in ast.walk(n)))
        branch=ne.body[idx];self.assertEqual(ast.unparse(branch.test),'self.synthetic');self.assertEqual(len(branch.orelse),1)
        self.assertEqual(ast.dump(branch.orelse[0],include_attributes=False),ast.dump(original,include_attributes=False))
        ne.body[idx]=copy.deepcopy(original)
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))
        for rel in ('main.ipynb','FINAL_NOTEBOOK_PROFILE.json','render_verified.py','validation_tools/validation_reporting/render.py','validation_tools/portable_reader.py'):
            self.assertEqual(app.sha(V1/rel),app.sha(V2/rel),rel)
        archive=app.read('/home/venture/FishSim_Final_Paper_Integration_Archive_Receipt_2026-11-11_v1.json')
        for rel,digest in archive['files'].items():self.assertEqual(app.sha(Path(archive['archive'])/rel),digest);self.assertEqual(app.sha(V1/rel),digest)

if __name__=='__main__':unittest.main(verbosity=2)
