"""Execute final paired-grid notebook; preserve all earlier evidence snapshots."""
from __future__ import annotations
import base64,contextlib,copy,hashlib,importlib.util,io,json,os,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_coarse_notebook_generator',HERE/'create_notebook_v3.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
cells=copy.deepcopy(prior.cells)
for cell in cells:
    text=''.join(cell['source'])
    text=text.replace('import notebook_support_v3 as study','import notebook_support_v4 as study')
    if text.startswith('# FishSim dolphin'):
        text="""# FishSim dolphin–gannet pilot: final overnight evidence

**Run All** verifies 72 completed feeding encounters and three separate timing checks, reconstructs 72 sealed new-study horizon records, regenerates all four report figures, and exports fourteen tables. Default execution takes zero native simulation steps.

The inventory preserves 24 earlier encounters, 24 coarse-grid encounters across eight new schools, and 24 fine-grid encounters on those **same eight schools**. The grids are paired numerical treatments, not sixteen independent schools. Every earlier snapshot, input manifest and case seal remains intact.

**Main finding:** refining the timestep changes the mean dolphin partner effect from +1 to 0 captures per school, and the gannet effect from +5.125 to +2.5. School-level signs also change. These are numerically sensitive model outcomes; stable dolphin facilitation and convergence are not established.

Use [README.md](README.md) for local Jupyter setup. The default notebook reconstructs the current report from sealed evidence. The optional native runner at the end remains limited to the documented historical pair/eight encounters; it does not rerun the later ensembles.
"""
    text=text.replace('The finer-timestep study is pending and excluded.','The finer-timestep check is included below as a paired sensitivity.')
    text=text.replace('The finer-timestep follow-up is excluded.','The completed finer-grid sensitivity is included; earlier evidence remains separate.')
    text=text.replace('The dolphin primary interval spans negative and positive effects, leaving its benefit unresolved.','On the coarse grid, the dolphin primary interval spans negative and positive effects, leaving its benefit unresolved. The finer-grid point effects below are a sensitivity comparison without new inferential intervals.')
    text=text.replace('study.export_tables(rows, development, replication, joint, depth, new_horizons, new_pairs, stats)','study.export_tables(rows, development, replication, joint, depth, new_horizons, new_pairs, stats, grid_cases, grid_effects)')
    if text.startswith('Figure3.') or text.startswith('Figure 3.'):
        text='Figure 3. Paired coarse/fine 36T effects on the same eight schools, with the coarse 72T continuation shown separately. Thin lines join each school across grids; intervals belong only to the prespecified coarse primary analysis. The grid comparison diagnoses sensitivity, not convergence.\n'
    cell['source']=text.splitlines(True)

def markdown(text):return dict(cell_type='markdown',metadata={},source=text.splitlines(True))
def code(text):return dict(cell_type='code',metadata={},source=text.splitlines(True),execution_count=None,outputs=[])
for index,cell in enumerate(cells):
    text=''.join(cell['source'])
    if '## Rebuild all four current paper figures' in text:
        before,after=text.split('## Rebuild all four current paper figures',1)
        new=[markdown(before),markdown("""## Numerical sensitivity: same eight schools, two timesteps

The finer runs start from the exact same 20T physical checkpoints, predator states, readiness and private random streams. Only numerical dt changes from 0.00125T to 0.000625T. Monitoring remains every 0.1T. No schools, policies or capture probabilities were adjusted to obtain agreement. Both grids use the same 36T horizon; the fine grid has no 72T continuation.
"""),code("""grid_cases = study.grid_case_rows()
grid_effects = study.grid_effect_rows(grid_cases)
study.print_table(grid_effects, ["school_seed", "coarse_D_partner_effect", "fine_D_partner_effect", "coarse_G_partner_effect", "fine_G_partner_effect", "D_effect_fine_minus_coarse", "G_effect_fine_minus_coarse"])
"""),markdown("""The fine grid gives dolphin captures 179→179 and gannet captures 49→69. Mean effects change from +1 to 0 for dolphins and from +5.125 to +2.5 for gannets. The two-grid results do not establish numerical convergence or timestep independence. An unchanged native model with valid contact accounting can still have sensitive threshold decisions, trajectories and subsequent random-draw histories.
"""),code("""study.print_table(study.grid_summary(grid_effects))
print("Joint-positive schools, coarse:", sum(r["coarse_joint_positive"] for r in grid_effects), "fine:", sum(r["fine_joint_positive"] for r in grid_effects))
print("Joint-positive on both grids:", sum(r["coarse_joint_positive"] and r["fine_joint_positive"] for r in grid_effects), "of 8 paired schools.")
"""),markdown("""Dolphin effect signs agree in only 3/8 schools and gannet signs in 6/8. Fine-minus-coarse effect differences span −13 to +9 fish for dolphins and −9 to +5 for gannets. Each grid has three jointly positive schools, but only two are positive on both grids. These are the same eight schools, not sixteen independent observations. No finer-grid confidence interval or convergence claim is added.

## Rebuild all four current paper figures"""+after)]
        cells[index:index+1]=new;break
for index,cell in enumerate(cells):
    cell['id']=f'v4-cell-{index:02d}'
    if cell['cell_type']=='code':cell['execution_count']=None;cell['outputs']=[]

def main():
    os.chdir(HERE);sys.path.insert(0,str(HERE));namespace={'__name__':'__main__'};started=time.monotonic();count=0
    for cell in cells:
        if cell['cell_type']!='code':continue
        count+=1;captured=io.StringIO()
        with contextlib.redirect_stdout(captured):exec(compile(''.join(cell['source']),f'<v3 cell{count}>','exec'),namespace)
        cell['execution_count']=count
        if captured.getvalue():cell['outputs'].append(dict(output_type='stream',name='stdout',text=captured.getvalue().splitlines(True)))
        if cell['metadata'].get('figure'):
            path=HERE/'outputs/final_figures'/(cell['metadata']['figure']+'.png')
            cell['outputs'].append(dict(output_type='display_data',data={'image/png':base64.b64encode(path.read_bytes()).decode(),'text/plain':[cell['metadata']['figure']]},metadata={}))
    assert 'fish_sim.cmodel' not in sys.modules
    import numpy as np
    import matplotlib.image as mpimg
    figures={}
    for name in ('fig1_model','fig2_development','fig3_replication','fig4_mechanism'):
        output=HERE/'outputs/final_figures'/(name+'.png');reference=HERE/'reference_figures_v4'/(name+'.png')
        assert np.array_equal(mpimg.imread(output),mpimg.imread(reference)),name
        figures[name]=dict(pixels_identical_to_reference=True,sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    notebook=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Python3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},cells=cells)
    path=HERE/'FishSim_Professor_Notebook.ipynb';path.write_text(json.dumps(notebook,indent=1)+'\n')
    receipt=dict(status='passed',snapshot='2026-11-09_0433',feeding_encounters=72,new_sealed_horizons=72,new_independent_schools=8,numerical_grids=2,
        code_cells_executed=count,native_steps=0,native_module_imported=False,figures=figures,
        notebook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),wall_seconds=time.monotonic()-started)
    (HERE/'validation/final_notebook_2026-11-09_0433.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
