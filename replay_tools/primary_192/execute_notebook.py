"""Headless saved analysis with logical preflight and fresh output receipts."""
from __future__ import annotations
import argparse,copy,hashlib,json,os,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--profile',default='FINAL_NOTEBOOK_PROFILE.json');parser.add_argument('--proof-deny-roots',type=Path);args=parser.parse_args();root=args.root.resolve()
    from .notebook_session import Session
    preflight=object.__new__(Session);preflight.root=root;preflight.verify_package()
    logical=preflight.logical_notebook_validation
    profile_path=(root/args.profile).resolve()
    if not profile_path.is_relative_to(root):raise RuntimeError('Profile escapes notebook package')
    if json.loads(profile_path.read_text())['validation']['kind']!='PRIMARY192_PRODUCTION':raise RuntimeError('This current-paper headless route accepts the completed production192 profile only; synthetic fixture tooling is separate')
    if logical['settings']['RUN_NATIVE']:raise RuntimeError('This headless driver runs saved analysis only; keep RUN_NATIVE=False. Use the separate certified GUI/CLI native workflow.')
    import nbformat
    from nbclient import NotebookClient
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',FISHSIM_NOTEBOOK_PROFILE=args.profile,IPYTHONDIR=str(root/'.headless/ipython'),JUPYTER_RUNTIME_DIR=str(root/'.headless/runtime'),MPLCONFIGDIR=str(root/'.headless/matplotlib'))
    os.environ.pop('PYTHONOPTIMIZE',None)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    kernel=root/'.headless/share/jupyter/kernels/fishsim_saved_analysis';kernel.mkdir(parents=True,exist_ok=True)
    (kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-B','-m','ipykernel_launcher','-f','{connection_file}'],display_name='Local saved-data analysis',language='python')))
    os.environ['JUPYTER_PATH']=str(root/'.headless/share/jupyter')
    book=nbformat.read(root/'main.ipynb',as_version=4);canonical_cells=len(book.cells)
    if args.proof_deny_roots:
        denied=json.loads(args.proof_deny_roots.read_text())
        guard='''import os,sys
from pathlib import Path
DENIED_ROOTS = '''+repr(denied)+'''
DENIED_READ_ATTEMPTS=[]
def deny_original_reads(event,args):
    if event not in ('open','os.listdir','os.scandir') or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
    try:target=Path(os.fsdecode(args[0])).resolve()
    except (OSError,ValueError):return
    if any(target==Path(base)or target.is_relative_to(Path(base))for base in DENIED_ROOTS):
        DENIED_READ_ATTEMPTS.append(str(target));raise RuntimeError('Proof forbids original author paths:'+str(target))
sys.addaudithook(deny_original_reads)
'''
        book.cells.insert(0,nbformat.v4.new_code_cell(guard));book.cells.append(nbformat.v4.new_code_cell("assert not DENIED_READ_ATTEMPTS\nprint('Zero original-author input reads.')"))
    started=time.perf_counter();NotebookClient(book,timeout=180,kernel_name='fishsim_saved_analysis',allow_errors=False,resources={'metadata':{'path':str(root)}}).execute()
    proof=root/'outputs'/('headless_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);proof.mkdir(parents=True,exist_ok=False)
    nbformat.write(book,proof/'EXECUTED_main.ipynb')
    receipt=dict(status='passed_saved_data',fresh_kernel=True,canonical_notebook_cells=canonical_cells,executed_cells=len(book.cells),synthetic=False,original_notebook_sha256=hashlib.sha256((root/'main.ipynb').read_bytes()).hexdigest(),logical_source_sha256=logical['logical_sha256'],seconds=time.perf_counter()-started,python=sys.executable,profile=args.profile,author_deny_guard_used=bool(args.proof_deny_roots),native_steps=0,new_bootstrap_draws=0,proof_directory=str(proof),historical_receipts_overwritten=False)
    (proof/'HEADLESS_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
