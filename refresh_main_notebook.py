"""Validate the active main.ipynb against its explicit report profile in a fresh kernel."""
from __future__ import annotations
import argparse,hashlib,json,os,sys,tempfile,time
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_default_code(book,profile):
    code=[''.join(c['source']) for c in book['cells'] if c['cell_type']=='code']
    digest=hashlib.sha256(json.dumps(code,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    if digest!=profile['code_source_sha256']:
        raise RuntimeError('main.ipynb code differs from the reviewed native-free defaults. Restore the default code cells before validation. Run optional native examples separately after explicitly opting in.')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--save',action='store_true');ap.add_argument('--receipt',type=Path,default=Path('validation/main_notebook_validation.json'));a=ap.parse_args()
    root=Path(__file__).resolve().parent;profile=json.loads((root/'MAIN_NOTEBOOK_PROFILE.json').read_text());book=json.loads((root/profile['notebook']).read_text())
    check_default_code(book,profile) # Before kernel creation or any cell/subprocess execution.
    assert profile['native_steps']==0 and sha(root/profile['report'])==profile['report_sha256']
    protected={}
    for name in profile['protected_manifests']:
        for relative,digest in json.loads((root/name).read_text())['files'].items():
            assert relative not in protected or protected[relative]==digest
            assert sha(root/relative)==digest,relative;protected[relative]=digest
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='fishsim_analysis_kernel_') as tmp:
        tmp=Path(tmp);kernel=tmp/'kernels/fishsim_current_paper';kernel.mkdir(parents=True)
        (kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Python 3 (validation)',language='python'))+'\n')
        os.environ['JUPYTER_PATH']=str(tmp);os.environ['JUPYTER_RUNTIME_DIR']=str(tmp/'runtime');os.environ['IPYTHONDIR']=str(tmp/'ipython');os.environ['MPLCONFIGDIR']=str(tmp/'matplotlib')
        import nbformat
        from nbclient import NotebookClient
        notebook=nbformat.read(root/profile["notebook"],as_version=4)
        NotebookClient(notebook,timeout=300,kernel_name='fishsim_current_paper',allow_errors=False,resources={'metadata':{'path':str(root)}}).execute()
    cells=[c for c in notebook.cells if c.cell_type=='code'];assert len(cells)==profile['code_cells']
    assert all(c.execution_count is not None for c in cells)
    assert not any(o.output_type=='error' for c in cells for o in c.get('outputs',[]))
    for relative,digest in protected.items():assert sha(root/relative)==digest,relative
    for relative,digest in profile['csv_tables'].items():assert sha(root/relative)==digest,relative
    import numpy as np
    import matplotlib.image as mpimg
    figures={}
    for name in profile['figure_names']:
        p=root/profile['figure_output']/(name+'.png');ref=root/profile['report_figure_reference']/(name+'.png')
        assert np.array_equal(mpimg.imread(p),mpimg.imread(ref)),name
        figures[name]=dict(sha256=sha(p),pixels_identical_to_report=True)
    analysis=json.loads((root/profile['analysis_root']/'outputs/analysis_verification.json').read_text())
    assert analysis['status']=='passed' and analysis['native_simulation_steps']==analysis['native_model_imports']==analysis['new_bootstrap_draws']==0
    if a.save:nbformat.write(notebook,root/profile['notebook'])
    receipt=dict(status='passed',profile=profile['profile'],notebook=profile['notebook'],notebook_sha256=sha(root/profile['notebook']),report_sha256=profile['report_sha256'],total_cells=len(notebook.cells),code_cells=len(cells),csv_tables=len(profile['csv_tables']),all_csv_bytes_identical=True,figures=figures,protected_inputs_unchanged=len(protected),profile_input_files=analysis['input_files_verified'],map_outcomes=analysis['map_cases'],map_schools=analysis['map_schools'],paired_school_effects=analysis['paired_effects_checked'],departure_subset_runs=analysis['departure_runs'],fresh_kernel=True,native_steps=0,native_imported=False,new_bootstrap_draws=0,code_preflight_passed=True,source_root=str(root),python=sys.version.split()[0],seconds=time.monotonic()-started)
    dest=a.receipt if a.receipt.is_absolute() else root/a.receipt;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
