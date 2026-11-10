"""New integration checks only; retained synthetic cache, zero new RNG draws."""
import copy,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import integration as app
HERE=Path(__file__).resolve().parent
CACHE=Path(os.environ.get('FISHSIM_INTEGRATION_TEST_CACHE','/home/venture/task-ownedtestcache/final_notebook_integration_2026-11-11'))
FIXTURE=Path(os.environ.get('FISHSIM_SYNTHETIC_SNAPSHOT','/home/venture/task-ownedtestcache/portable_peer_brief_audit_v2_2026-11-10/pytest_run/SYNTHETIC_primary192_portability0/snapshot with spaces'))

def copy_package(dest):
    def ignore(source,names):return [n for n in names if n in ('__pycache__','.ipynb_checkpoints') or (Path(source)==HERE and n in ('outputs','execution_proofs','.headless','proofs'))]
    shutil.copytree(HERE,dest,ignore=ignore)
def attach_synthetic(root):
    source=app.read(FIXTURE/'SNAPSHOT.json');assert source['kind']=='SYNTHETIC_TEMP_ONLY' and source['production_accepted'] is False
    target=root/'SYNTHETIC validation snapshot with spaces';shutil.copytree(FIXTURE,target)
    cfg=copy.deepcopy(app.read(root/'FINAL_NOTEBOOK_PROFILE.json'));cfg['not_study_results']=True
    cfg['validation'].update(kind='SYNTHETIC_TEMP_ONLY',test_only=True,snapshot_manifest=str((target/'SNAPSHOT.json').relative_to(root)),snapshot_manifest_sha256=app.sha(target/'SNAPSHOT.json'),export_receipt_sha256=app.sha(target/'EXPORT_RECEIPT.json'),independent_final_sha256=source['evidence']['independent_final'],metadata_sidecar_sha256=source['evidence']['metadata_sidecar'])
    app.write(root/'SYNTHETIC_PROFILE.json',cfg);return cfg,target

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        CACHE.mkdir(parents=True,exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(prefix='SYNTHETIC_final_integration_',dir=CACHE);cls.base=Path(cls.temp.name)
        cls.package=cls.base/'fresh checkout with spaces';copy_package(cls.package);cls.cfg,cls.snapshot=attach_synthetic(cls.package)
    @classmethod
    def tearDownClass(cls):
        # Retain the explicitly synthetic isolated proof pack after interpreter exit.
        cls.temp._finalizer.detach()
    def test_pending_rejects_configured_outcomes_before_any_snapshot_read(self):
        cfg=copy.deepcopy(self.cfg);cfg['validation']['kind']='PENDING';cfg['validation']['snapshot_manifest']='DO_NOT_READ_unaccepted_outcomes/SNAPSHOT.json'
        app.write(self.package/'BAD_PENDING_PROFILE.json',cfg)
        with self.assertRaisesRegex(ValueError,'Pending profile'):app.Session(self.package,'BAD_PENDING_PROFILE.json')
    def test_complete_synthetic_negative_primary_is_valid_not_a_success_filter(self):
        s=app.Session(self.package,'SYNTHETIC_PROFILE.json');r=s.validation_result
        self.assertIs(r['primary_joint_criterion_met'],False);self.assertFalse(r['production_accepted'])
        self.assertEqual((len(r['counts']),len(r['school_points']),len(r['world_points'])),(192,16,64))
        self.assertEqual(r['new_bootstrap_draws'],0)
        for row in s.validation_overview():self.assertEqual((row['n_schools'],row['n_worlds']),(16,32));self.assertEqual(row['SE'],r['estimates'][row['contrast']]['school_sd']/4)
    def test_partial96_rejected_before_analysis_or_exports(self):
        value=app.read(self.snapshot/'SNAPSHOT.json');partial=copy.deepcopy(value);partial['cases']=dict(list(partial['cases'].items())[:96])
        fake=self.package/'SYNTHETIC partial96';fake.mkdir();app.write(fake/'SNAPSHOT.json',partial)
        cfg=copy.deepcopy(self.cfg);cfg['validation']['snapshot_manifest']=str((fake/'SNAPSHOT.json').relative_to(self.package));cfg['validation']['snapshot_manifest_sha256']=app.sha(fake/'SNAPSHOT.json')
        old=self.package/'SYNTHETIC_PROFILE.json';original=old.read_bytes();app.write(old,cfg)
        try:
            with self.assertRaisesRegex(ValueError,'Exact192 required'):app.Session(self.package,'SYNTHETIC_PROFILE.json')
        finally:old.write_bytes(original)
    def test_missing_metadata_binding_and_synthetic_promotion_rejected(self):
        original=(self.package/'SYNTHETIC_PROFILE.json').read_bytes()
        for field,value,pattern in [('metadata_sidecar_sha256',None,'Missing final snapshot'),('kind','PRIMARY192_PRODUCTION','Synthetic/production profile mismatch')]:
            cfg=copy.deepcopy(self.cfg);cfg['validation'][field]=value;app.write(self.package/'SYNTHETIC_PROFILE.json',cfg)
            try:
                with self.assertRaisesRegex(ValueError,pattern):app.Session(self.package,'SYNTHETIC_PROFILE.json')
            finally:(self.package/'SYNTHETIC_PROFILE.json').write_bytes(original)
    def test_changed_reader_source_rejected(self):
        path=self.package/'validation_tools/portable_reader.py';saved=path.read_bytes();path.write_bytes(saved+b'\n# SYNTHETIC TAMPER\n')
        try:
            with self.assertRaisesRegex(ValueError,'Notebook input changed'):app.Session(self.package,'SYNTHETIC_PROFILE.json')
        finally:path.write_bytes(saved)
    def test_z_headless_isolated_main_with_original_author_reads_denied(self):
        source=app.read(self.snapshot/'SNAPSHOT.json');fixture_sources=[str(Path(p).parent) for p in source['sources']]
        roots=['/home/venture/FishSim-Dolphin-Gannet-Pilot','/home/venture/uwa/complex-systems/FishSim-RL',str(HERE),*sorted(set(fixture_sources))]
        denied=self.base/'DENIED_ORIGINAL_INPUT_ROOTS.json';app.write(denied,roots)
        env=dict(os.environ,TMPDIR=str(CACHE),PYTHONDONTWRITEBYTECODE='1')
        result=subprocess.run([sys.executable,'-I','-B',str(self.package/'execute_notebook.py'),'--root',str(self.package),'--profile','SYNTHETIC_PROFILE.json','--proof-deny-roots',str(denied)],cwd=self.base,env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        proof=app.read(self.package/'execution_proofs/SYNTHETIC_HEADLESS_RECEIPT.json');self.assertTrue(proof['fresh_kernel']);self.assertTrue(proof['author_deny_guard_used'])
        receipts=list((self.package/'outputs').glob('SYNTHETIC_TEST_OUTPUTS_*/SYNTHETIC_NOTEBOOK_RUN_RECEIPT.json'));self.assertTrue(receipts)
        run=app.read(receipts[-1]);self.assertEqual((run['discovery_tables'],run['validation_tables'],run['validation_cases'],run['validation_school_clusters']),(9,4,192,16));self.assertFalse(run['production_accepted']);self.assertFalse(run['primary_joint_criterion_met'])
        self.assertEqual((run['discovery_figures_reused'],run['discovery_figures_regenerated']),(1,2))
        out=receipts[-1].parent
        tables=list(out.glob('SYNTHETIC_validation/tables/*.csv'));self.assertEqual(len(tables),4)
        for path in tables:
            self.assertTrue(path.name.startswith('SYNTHETIC_'));self.assertTrue(all(r['data_kind']=='SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS' for r in app.table(path)))
        images=list(out.glob('SYNTHETIC_validation/rendered/SYNTHETIC_paired_grid_effects.*'));self.assertEqual({p.suffix for p in images},{'.png','.pdf'})
        rendered=app.read(out/'SYNTHETIC_validation/rendered/render_receipt.json');self.assertTrue(rendered['synthetic']);self.assertEqual(rendered['renderer_sha256'],app.RENDER_SHA)
        self.assertEqual((run['native_model_imports'],run['native_steps'],run['new_bootstrap_draws']),(0,0,0))
        app.write(CACHE/'LATEST_HEADLESS_PROOF.json',dict(package=str(self.package),execution_receipt=str(self.package/'execution_proofs/SYNTHETIC_HEADLESS_RECEIPT.json'),run_receipt=str(receipts[-1]),deny_roots=str(denied),synthetic_only=True,stdout=result.stdout,stderr=result.stderr))

if __name__=='__main__':unittest.main(verbosity=2)
