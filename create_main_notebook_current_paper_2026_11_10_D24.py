"""Generate repository-root main.ipynb from the frozen current-paper profile."""
from pathlib import Path
import copy,json
R=Path(__file__).resolve().parent
P=R/'paper_profiles/current_through36_D24_2026-11-10'
b=json.loads((P/'analysis_only.ipynb').read_text())
for c in b['cells']:
 if c['cell_type']=='code':c['outputs']=[];c['execution_count']=None
 else:
  s=''.join(c['source']).replace('from this analysis-profile folder','from the repository root').replace('`python -m pip install -r requirements-analysis.lock`','`python -m pip install -r requirements-analysis.txt`')
  s=s.replace('There is no executable model cell here. This default notebook is the fast saved-output reproduction path and cannot start simulations.','The saved-output analysis above cannot start simulations. Separately validated short examples below remain disabled by default.')
  s=s.replace('**`MODEL_REPRODUCTION.txt`**','**`paper_profiles/current_through36_D24_2026-11-10/MODEL_REPRODUCTION.txt`**').replace('in `model_reproduction/`','in `paper_profiles/current_through36_D24_2026-11-10/model_reproduction/`')
  c['source']=s.splitlines(True)
first=b['cells'][1]
first['source']='''from pathlib import Path
import hashlib, json, sys
from IPython.display import display, HTML, Image, Markdown

PROJECT_ROOT = Path.cwd().resolve()
assert (PROJECT_ROOT / "MAIN_NOTEBOOK_PROFILE.json").is_file(), "Open main.ipynb from the repository root."
ROOT = PROJECT_ROOT / "paper_profiles/current_through36_D24_2026-11-10"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(ROOT))
protected = json.loads((PROJECT_ROOT / "INPUT_MANIFEST_2026-11-10_D24.json").read_text())["files"]
for relative, digest in protected.items():
    assert hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest() == digest, relative
print(f"Verified {len(protected)} preserved and current-profile inputs.")
import analysis_support as analysis
print(json.dumps(analysis.environment(), indent=2))
print("Default analysis takes zero native steps and generates no bootstrap draws.")
'''.splitlines(True)
optional=json.loads((R/'OPTIONAL_V6_NOTEBOOK_CELLS_2026-11-09.json').read_text())
for c in optional:
 c=copy.deepcopy(c)
 if c['cell_type']=='code':
  c['source']=''.join(c['source']).replace('ROOT','PROJECT_ROOT').splitlines(True);c['outputs']=[];c['execution_count']=None
 else:c['source']=('Earlier validated through18 examples only: `headline` = H1/G9 and `joint` = H2/G12. These do not execute H1/G36, D24 or the full24-setting map.\n\n'+''.join(c['source']).replace('analysis above reconstructs saved 36T evidence','analysis above reconstructs the current paper from saved evidence')).splitlines(True)
 b['cells'].append(c)
b['metadata']['kernelspec']={'display_name':'Python 3','language':'python','name':'python3'}
(R/'main.ipynb').write_text(json.dumps(b,indent=1)+'\n')
print('Wrote root main.ipynb:',len(b['cells']),'cells,',sum(c['cell_type']=='code' for c in b['cells']),'code cells; optional native execution disabled.')
