"""Relocatable paper notebook: frozen discovery + separately accepted primary192."""
from __future__ import annotations
import csv,hashlib,html,importlib.abc,importlib.util,json,os,shutil,subprocess,sys,tempfile,uuid,zipfile
from datetime import datetime,timezone
from pathlib import Path

READER_SHA='3d08ad828a2bb64c93492a7181ba5351d66ae57d4118b4eee877c0126a7c95e3'
EXPORTER_SHA='eea690d7f064396c78dbca7a7883c27c5e667ed7bab5025413c8476759369a3f'
RENDER_SHA='4040740e28a93cc2cea9bd2ec716506bf7086ad4fc6c245b3e571c3d822a4e7c'
GATE_SHA='efdf5392cc148ce4b14b7baeea2c5e718b299e64ae7de1b97fb2ae1aa9c55b02'
PINS_SHA='51a176741e38852deb60afffad7394d444b22f15b0275e920fe8d303ba4c5776'
KINDS=('PENDING','PRIMARY192_PRODUCTION','SYNTHETIC_TEMP_ONLY')

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def relative(root,path):
    p=Path(path);require(not p.is_absolute(),'Use a relative bundled path')
    resolved=(root/p).resolve();require(resolved.is_relative_to(root),'Path escapes notebook package');return resolved
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='fish_sim' or fullname.startswith('fish_sim.') or fullname=='cmodel':raise RuntimeError('This saved-data notebook cannot import the simulation model')
def no_model():require(not any(n=='fish_sim' or n.startswith('fish_sim.') or n=='cmodel' for n in sys.modules),'Unexpected model import')
def table(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))
def html_table(rows,columns=None,limit=None):
    if not rows:return '<p>No rows.</p>'
    columns=columns or list(rows[0]);shown=rows if limit is None else rows[:limit]
    return '<table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(format(r.get(k),' .6g').strip() if type(r.get(k)) is float else str(r.get(k,'')))+'</td>' for k in columns)+'</tr>' for r in shown)+'</tbody></table>'

def derive_synthetic_renderer_outputs(upstream,destination,archive):
    """Expose marked CSVs; preserve exact frozen-renderer lineage in a ZIP.

    This wrapper is synthetic-only. The original renderer bytes and receipts
    remain unchanged archive members; the derived receipt hashes derived files.
    """
    upstream=Path(upstream);destination=Path(destination);archive=Path(archive)
    require(not destination.exists() and not archive.exists(),'Never overwrite renderer lineage')
    original=read(upstream/'render_receipt.json')
    require(original.get('synthetic') is True and original.get('status')=='SYNTHETIC_LAYOUT_ONLY','Only synthetic renderer output can be derived')
    require(original.get('renderer_sha256')==RENDER_SHA and original.get('gate_sha256')==GATE_SHA,'Upstream renderer source differs')
    names=set(original['files'])|{'render_receipt.json'}
    require({p.name for p in upstream.iterdir() if p.is_file()}==names,'Unexpected original renderer inventory')
    for name,digest in original['files'].items():
        require(Path(name).name==name and sha(upstream/name)==digest,'Original renderer receipt mismatch:'+name)
    originals={name:sha(upstream/name) for name in sorted(names)}
    archive.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as saved:
        for name in sorted(names):saved.write(upstream/name,arcname=name)
    with zipfile.ZipFile(archive) as saved:
        require(set(saved.namelist())==names,'Archive inventory mismatch')
        for name,digest in originals.items():require(hashlib.sha256(saved.read(name)).hexdigest()==digest,'Archived original bytes differ:'+name)
    destination.mkdir(parents=True)
    derivations={}
    for name in sorted(original['files']):
        source=upstream/name
        if source.suffix=='.csv':
            rows=table(source);require(bool(rows),'Empty synthetic renderer table')
            fields=list(rows[0]);require('data_kind' not in fields,'Unexpected original CSV watermark')
            for row in rows:row['data_kind']='SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS'
            target=destination/('SYNTHETIC_'+name)
            with target.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=[*fields,'data_kind']);writer.writeheader();writer.writerows(rows)
            derivations[target.name]=dict(original_archive_member=name,original_sha256=originals[name],transformation='Original numeric text retained; append data_kind and prefix filename')
        else:shutil.copy2(source,destination/name)
    # A derived receipt describes current derived bytes. The original receipt
    # applies ONLY to original members inside the explicitly synthetic archive.
    derived=dict(original,status='SYNTHETIC_DERIVED_RENDERER_OUTPUT_NOT_STUDY_RESULTS',
        files={p.name:sha(p) for p in sorted(destination.iterdir()) if p.is_file()},
        upstream_lineage=dict(kind='SYNTHETIC_ORIGINAL_RENDERER_ARCHIVE_NOT_USABLE_CSV_EXPORTS',archive_file=archive.name,archive_path_relative_to_receipt=os.path.relpath(archive,destination),archive_sha256=sha(archive),original_receipt_member='render_receipt.json',original_receipt_sha256=originals['render_receipt.json'],archive_member_sha256=originals),
        csv_derivations=derivations,derivation_wrapper_sha256=sha(__file__))
    write(destination/'render_receipt.json',derived)
    for name,digest in originals.items():require(sha(upstream/name)==digest,'Original renderer output was mutated')
    return derived

class Session:
    def __init__(self,root,profile='FINAL_NOTEBOOK_PROFILE.json'):
        self.root=Path(root).resolve();self.profile_path=relative(self.root,profile);self.profile=read(self.profile_path)
        require(self.profile.get('schema')=='fishsim_final_paper_notebook_profile_v1','Unknown notebook profile')
        no_model();self.guard=NoModel();sys.meta_path.insert(0,self.guard)
        self.verify_package();self.validation_result=None;self.validation_exports=None;self.discovery_result=None
        self._load_backend()  # All configured validation gates precede any result export.
        mark='SYNTHETIC_TEST_OUTPUTS_' if self.synthetic else 'run_'
        self.output=self.root/'outputs'/(mark+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
        self.output.mkdir(parents=True,exist_ok=False)
    @property
    def synthetic(self):return self.profile['validation']['kind']=='SYNTHETIC_TEMP_ONLY'
    def verify_package(self):
        manifest=read(self.root/'PACKAGE_INPUTS.json');require(manifest['schema']=='fishsim_final_notebook_immutable_inputs_v1','Unknown package manifest')
        for p,digest in manifest['files'].items():require(sha(relative(self.root,p))==digest,'Notebook input changed:'+p)
        require(sha(self.root/'validation_tools/portable_reader.py')==READER_SHA,'Pinned portable reader changed')
        for name,digest in [('render.py',RENDER_SHA),('gate.py',GATE_SHA),('source_pins.json',PINS_SHA)]:require(sha(self.root/'validation_tools/validation_reporting'/name)==digest,'Frozen reporter changed:'+name)
        self.input_files=len(manifest['files']);return self.input_files
    def _load_backend(self):
        cfg=self.profile['validation'];kind=cfg.get('kind');require(kind in KINDS,'Only PENDING or exact final192 backend is supported; partial prefixes are not final evidence')
        fields=('snapshot_manifest','snapshot_manifest_sha256','export_receipt_sha256','independent_final_sha256','metadata_sidecar_sha256','root_activation','root_activation_sha256')
        if kind=='PENDING':
            require(all(cfg.get(k) is None for k in fields),'Pending profile cannot silently accept configured results')
            self.backend_status='PENDING: final192 + original independent FINAL + metadata PASS + root activation';return
        for key in fields[:5]:require(isinstance(cfg.get(key),str) and bool(cfg[key]),'Missing final snapshot binding:'+key)
        path=relative(self.root,cfg['snapshot_manifest']);require(path.name=='SNAPSHOT.json','Expected portable SNAPSHOT.json file')
        require(sha(path)==cfg['snapshot_manifest_sha256'],'Snapshot manifest binding differs')
        manifest=read(path);require(manifest['kind']==kind,'Synthetic/production profile mismatch')
        require(len(manifest['cases'])==192,'Exact192 required; partial96/144 cannot enter the final paper')
        require(manifest['evidence']['independent_final']==cfg['independent_final_sha256'] and manifest['evidence']['metadata_sidecar']==cfg['metadata_sidecar_sha256'],'Final/metadata profile bindings differ')
        if kind=='PRIMARY192_PRODUCTION':
            require(isinstance(cfg.get('root_activation'),str) and isinstance(cfg.get('root_activation_sha256'),str),'Root export activation is still pending')
            activation=relative(self.root,cfg['root_activation']);require(sha(activation)==cfg['root_activation_sha256'],'Root activation changed')
            approval=read(activation)
            require(approval.get('approved') is True and approval.get('recorded_by')=='/root' and approval.get('scope')=='primary192_private_portable_export','Root production activation required')
            require(approval.get('reader_sha256')==READER_SHA and approval.get('exporter_sha256')==EXPORTER_SHA,'Activation source differs')
            require(approval.get('final_review_sha256')==cfg['independent_final_sha256'] and approval.get('metadata_review_sha256')==cfg['metadata_sidecar_sha256'],'Activation final/metadata differs')
        else:
            require(self.profile_path.name=='SYNTHETIC_PROFILE.json' and cfg.get('test_only') is True and self.profile.get('not_study_results') is True,'Synthetic data require an explicit testing-only profile')
            require(cfg.get('root_activation') is None and cfg.get('root_activation_sha256') is None,'Synthetic fixtures cannot carry production activation')
        self.reader=load('_final_paper_portable_reader',self.root/'validation_tools/portable_reader.py')
        result=self.reader.analyse_snapshot(path,allow_synthetic=self.synthetic,expected_receipt_sha256=cfg['export_receipt_sha256'])
        require(result['case_count']==192 and result['independent_school_clusters']==16,'Wrong final sample scope')
        require(result['synthetic'] is self.synthetic and result['production_accepted'] is (not self.synthetic),'Mislabelled data kind')
        self.validation_result=result;self.backend_status=result['status'];no_model()
    def discovery(self):
        if self.discovery_result is not None:return self.discovery_result
        root=relative(self.root,self.profile['discovery']['root'])
        analysis=load('_final_paper_discovery_analysis',root/'analysis_support.py')
        target=self.output/'discovery';target.mkdir();analysis.OUT=target
        inputs=analysis.verify_inputs();mapped=analysis.map_analysis();population=analysis.population_check();numerical=analysis.numerical_check();departure=analysis.departure_check()
        archived=self.profile['discovery']['tables'];require(len(archived)==9,'Nine discovery tables required')
        for name,digest in archived.items():require(sha(target/name)==digest,'Discovery table differs:'+name)
        require(len(list(target.glob('*.csv')))==9,'Unexpected discovery table export')
        figures=[]
        for name in ('fig1_model','fig2_returns','fig3_opportunities'):
            for ext in ('png','pdf'):require(sha(root/'figures'/f'{name}.{ext}')==self.profile['discovery']['figures'][f'{name}.{ext}'],'Discovery figure changed')
            figures.append(root/'figures'/f'{name}.png')
        rebuilt=analysis.render_figures()
        rebuilt_root=Path(rebuilt['path'])
        figures=[root/'figures/fig1_model.png',rebuilt_root/'fig2_returns.png',rebuilt_root/'fig3_opportunities.png']
        self.discovery_result=dict(mapped=mapped,population=population,numerical=numerical,departure=departure,figures=figures,table_root=target,verified_inputs=len(inputs))
        return self.discovery_result
    def validation_overview(self):
        if self.validation_result is None:return []
        rows=[]
        for contrast,value in self.validation_result['estimates'].items():
            rows.append(dict(contrast=contrast,mean=value['mean'],school_SD=value['school_sd'],SE=value['se'],t_97_5_low=value['student_t_97_5_ci'][0],t_97_5_high=value['student_t_97_5_ci'][1],n_schools=value['n_schools'],n_worlds=value['n_worlds'],W=value['within_school_variance_W'],conditional_MCSE=value['conditional_mcse'],school_signs=value['school_signs'],cached_bootstrap_97_5=value['bootstrap_97_5_ci']))
        return rows
    def export_validation(self):
        if self.validation_result is None:return None
        if self.validation_exports is not None:return self.validation_exports
        prefix='SYNTHETIC_' if self.synthetic else ''
        root=self.output/(prefix+'validation');root.mkdir();tables=root/'tables'
        receipt=self.reader.write_tables(self.validation_result,tables)
        if self.synthetic:
            marked={}
            for name in receipt['files']:
                path=tables/name;rows=table(path)
                for row in rows:row['data_kind']='SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS'
                new=path.with_name('SYNTHETIC_'+name)
                with new.open('w',newline='') as f:
                    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
                path.unlink();marked[new.name]=sha(new)
            (tables/'TABLE_RECEIPT.json').unlink()
            write(tables/'SYNTHETIC_TABLE_RECEIPT.json',dict(status='SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS',synthetic=True,production_accepted=False,files=marked,upstream_receipt_before_explicit_watermark=receipt,new_bootstrap_draws=0))
        data=root/(prefix+'verified_reporter_input.json');write(data,self.validation_result['reporter_input'])
        report=root/'rendered';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(self.output/'.matplotlib'))
        for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[k]='1'
        if self.synthetic:
            with tempfile.TemporaryDirectory(prefix='SYNTHETIC_RENDER_STAGE_',dir=root) as staging:
                upstream=Path(staging)/'original'
                completed=subprocess.run([sys.executable,'-I','-B',str(self.root/'render_verified.py'),'--data',str(data),'--data-sha256',sha(data),'--output',str(upstream)],capture_output=True,text=True,check=True,env=env,cwd=self.root)
                derive_synthetic_renderer_outputs(upstream,report,root/'SYNTHETIC_UPSTREAM_RENDERER_ORIGINALS.zip')
        else:
            completed=subprocess.run([sys.executable,'-I','-B',str(self.root/'render_verified.py'),'--data',str(data),'--data-sha256',sha(data),'--output',str(report)],capture_output=True,text=True,check=True,env=env,cwd=self.root)
        receipt=read(report/'render_receipt.json');require(receipt['renderer_sha256']==RENDER_SHA and receipt['gate_sha256']==GATE_SHA,'Renderer source differs')
        require(receipt['synthetic'] is self.synthetic and receipt['cases']==192 and receipt['schools']==16,'Wrong validation figure scope')
        figure=report/(prefix+'paired_grid_effects.png');require(figure.is_file(),'Figure4 missing')
        self.validation_exports=dict(root=root,tables=tables,figure4=figure,figure4_pdf=figure.with_suffix('.pdf'),renderer_receipt=report/'render_receipt.json',renderer_stdout=completed.stdout)
        return self.validation_exports
    def finish(self):
        self.verify_package();no_model()
        result=dict(status='SYNTHETIC_TEST_ONLY_NOT_STUDY_RESULTS' if self.synthetic else ('completed_saved_data_with_validation_PENDING' if self.validation_result is None else 'completed_verified_primary192_saved_data'),validation_backend=self.backend_status,discovery_tables=9,discovery_figures_reused=1,discovery_figures_regenerated=2,validation_tables=4 if self.validation_exports else 0,validation_cases=192 if self.validation_result else 0,validation_school_clusters=16 if self.validation_result else 0,new_bootstrap_draws=0,native_model_imports=0,native_steps=0,raw_tables_accessible=True,figure4_generated=self.validation_exports is not None,synthetic=self.synthetic,production_accepted=bool(self.validation_result and not self.synthetic),primary_joint_criterion_met=self.validation_result['primary_joint_criterion_met'] if self.validation_result else None,input_files_verified=self.input_files,profile_sha256=sha(self.profile_path))
        prefix='SYNTHETIC_' if self.synthetic else '';write(self.output/(prefix+'NOTEBOOK_RUN_RECEIPT.json'),result);return result
