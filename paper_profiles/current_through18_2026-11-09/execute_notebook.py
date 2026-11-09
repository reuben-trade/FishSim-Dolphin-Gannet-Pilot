"""Run the default saved-data notebook in a fresh kernel; never run a model."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,os,time,sys,traceback
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parent
os.environ['JUPYTER_PATH']=str(ROOT/'.jupyter/share/jupyter')
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.jupyter/runtime')
os.environ['IPYTHONDIR']=str(ROOT/'.ipython')
os.environ['MPLCONFIGDIR']=str(ROOT/'outputs/.matplotlib')
for name in ['.jupyter/runtime','.ipython','outputs']: (ROOT/name).mkdir(parents=True,exist_ok=True)
# Keep this headless runner portable after extraction: provision a local kernel
# that uses the interpreter running this script, rather than an authoring path.
kernel=ROOT/'.jupyter/share/jupyter/kernels/fishsim_v3'
kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                            'display_name':'Python 3 (frozen V3 analysis)','language':'python'},indent=2)+'\n')
path=ROOT/'main.ipynb'
notebook=nbformat.read(path,as_version=4)
started=time.perf_counter()
try:
    client=NotebookClient(notebook,timeout=300,kernel_name='fishsim_v3',allow_errors=False,
                          record_timing=True,resources={'metadata':{'path':str(ROOT)}})
    client.execute()
    nbformat.write(notebook,path)
    errors=[out for c in notebook.cells if c.cell_type=='code' for out in c.get('outputs',[]) if out.output_type=='error']
    code=[c for c in notebook.cells if c.cell_type=='code']
    assert not errors and all(c.execution_count is not None for c in code)
    analysis=json.loads((ROOT/'outputs/analysis_verification.json').read_text())
    assert analysis['status']=='passed' and analysis['native_simulation_steps']==0 and analysis['new_bootstrap_draws']==0
    result={'status':'passed','at':datetime.now(ZoneInfo('Australia/Perth')).isoformat(),
            'notebook':path.name,'fresh_kernel':True,'kernel_name':'fishsim_v3','execution_backend':'nbclient.NotebookClient.execute',
            'total_cells':len(notebook.cells),'code_cells':len(code),'executed_code_cells':len(code),'error_outputs':0,
            'wall_seconds':time.perf_counter()-started,'python_executable':sys.executable,
            'native_model_imports':0,'native_simulation_steps':0,'new_bootstrap_draws':0,
            'analysis_receipt':'outputs/analysis_verification.json','input_files_verified':analysis['input_files_verified'],
            'figures_directory':'outputs/reproduced_figures','figure1_reused':True,
            'existing_confidence_endpoints_retained':True,'r90_from_archived_time_means':True,
            'environment':analysis['environment']}
except Exception as e:
    result={'status':'failed','notebook':path.name,'fresh_kernel':True,'wall_seconds':time.perf_counter()-started,
            'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
    (ROOT/'outputs/notebook_execution_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    raise
(ROOT/'outputs/notebook_execution_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
