"""Execute main.ipynb headlessly in a fresh local analysis kernel."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
import nbformat
from nbclient import NotebookClient

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--profile',default='FINAL_NOTEBOOK_PROFILE.json');p.add_argument('--proof-deny-roots',type=Path);a=p.parse_args()
    root=a.root.resolve();assert (root/'main.ipynb').is_file()
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',FISHSIM_NOTEBOOK_PROFILE=a.profile,IPYTHONDIR=str(root/'.headless/ipython'),JUPYTER_RUNTIME_DIR=str(root/'.headless/runtime'),MPLCONFIGDIR=str(root/'.headless/matplotlib'))
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    kernel=root/'.headless/share/jupyter/kernels/fishsim_final_local';kernel.mkdir(parents=True,exist_ok=True)
    (kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-B','-m','ipykernel_launcher','-f','{connection_file}'],display_name='Local saved-data analysis',language='python')))
    os.environ['JUPYTER_PATH']=str(root/'.headless/share/jupyter')
    book=nbformat.read(root/'main.ipynb',as_version=4);canonical_cells=len(book.cells)
    if a.proof_deny_roots:
        denied=json.loads(a.proof_deny_roots.read_text())
        # Only the disposable notebook object gains this test-only guard cell.
        code='''import importlib.abc, os, sys
from pathlib import Path
DENIED_ROOTS = '''+repr(denied)+'''
DENIED_READ_ATTEMPTS = []
def deny_author_reads(event, args):
    if event not in ('open','os.listdir','os.scandir') or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    try:
        candidate = Path(os.fsdecode(args[0])).resolve()
    except (OSError, ValueError):
        return
    for value in DENIED_ROOTS:
        base = Path(value)
        if candidate == base or candidate.is_relative_to(base):
            DENIED_READ_ATTEMPTS.append(str(candidate))
            raise RuntimeError('PROOF: original author inputs unavailable: '+str(candidate))
sys.addaudithook(deny_author_reads)
'''
        book.cells.insert(0,nbformat.v4.new_code_cell(code))
        book.cells.append(nbformat.v4.new_code_cell("assert DENIED_READ_ATTEMPTS == [], DENIED_READ_ATTEMPTS\nprint('Fresh-kernel proof: zero author-input read attempts.')"))
    started=time.perf_counter();NotebookClient(book,timeout=180,kernel_name='fishsim_final_local',allow_errors=False,resources={'metadata':{'path':str(root)}}).execute()
    synthetic=a.profile=='SYNTHETIC_PROFILE.json';prefix='SYNTHETIC_' if synthetic else ''
    proof=root/'execution_proofs';proof.mkdir(exist_ok=True)
    nbformat.write(book,proof/(prefix+'EXECUTED_main.ipynb'))
    receipt=dict(status='SYNTHETIC_TEST_ONLY_NOT_RESULTS' if synthetic else 'passed_saved_data',fresh_kernel=True,canonical_notebook_cells=canonical_cells,executed_cells=len(book.cells),synthetic=synthetic,original_notebook_sha256=hashlib.sha256((root/'main.ipynb').read_bytes()).hexdigest(),seconds=time.perf_counter()-started,python=sys.executable,profile=a.profile,author_deny_guard_used=bool(a.proof_deny_roots),native_steps=0,new_bootstrap_draws=0)
    (proof/(prefix+'HEADLESS_RECEIPT.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
