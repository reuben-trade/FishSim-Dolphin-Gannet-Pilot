"""Execute a new eight-school notebook while preserving both prior generators."""
from __future__ import annotations
import base64,contextlib,copy,hashlib,importlib.util,io,json,os,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_prior_notebook_generator',HERE/'create_notebook_current.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
cells=copy.deepcopy(prior.cells)
for cell in cells:
    text=''.join(cell['source'])
    text=text.replace('import notebook_support_v2 as study','import notebook_support_v3 as study')
    text=text.replace('verifies 24 completed feeding encounters and three separate timing engineering checks, regenerates the four figures in the 9 November report snapshot, and exports eight tables','verifies 48 completed feeding encounters and three separate timing checks, reconstructs 48 sealed horizons from the new eight-school cohort, regenerates the four current figures, and exports twelve tables')
    if text.startswith('# FishSim dolphin'):
        a=text.index('This snapshot contains');b=text.index('\n\nStart with',a)
        text=text[:a]+'''This snapshot preserves the earlier24 encounters and adds a separate **eight-school cohort with24 D/G/DG encounters**. Each new encounter has sealed36T primary and72T secondary records. These are48 encounters in total, not72 independent samples. Earlier two-school repetitions are not pooled with the eight new schools. Original inventories and seals remain intact; the finer-timestep study is pending and excluded.

**Primary finding:** the new cohort gives a mean dolphin change of+1 capture per school, with a97.5% marginal interval from−2.375 to+5. Gannets gain+5.125 captures, interval2.75 to7. Dolphin benefit remains unresolved; a general mutual advantage is not established.''' +text[b:]
    text=text.replace('## Recalculate the outcomes from the sealed evidence','## Earlier exploratory evidence: kept separate')
    text=text.replace('All cases are 36T, with 28,800 native steps each.','These earlier24 cases are36T, with28,800 steps each. New-cohort results are reconstructed separately below from their sealed horizon prefixes.')
    text=text.replace('These match the 9 November report snapshot, including its replacement Figure 4. The original first-draft figure source and references remain unchanged. Later 72T results are not mixed into this snapshot.','These match the eight-school report snapshot. Figure3 shows the eight new schools; Figure4 retains the earlier two-school controls and initial-depth pilot. Earlier source/reference sets remain intact. The finer-timestep follow-up is excluded.')
    text=text.replace('Figure 3. Fresh exposed-policy replication: four paired stochastic runs nested within two independent starting schools. Every paired difference is positive here; this remains a small descriptive pilot.','Figure3. Eight-school partner effects at primary36T and secondary72T. The primary dolphin interval crosses zero; the gannet interval is positive. Earlier two-school results are excluded.')
    text=text.replace('study.export_tables(rows, development, replication, joint, depth)','study.export_tables(rows, development, replication, joint, depth, new_horizons, new_pairs, stats)')
    text=text.replace('under `outputs/current_figures/`','under `outputs/eight_school_figures/`')
    cell['source']=text.splitlines(True)

def markdown(text):return dict(cell_type='markdown',metadata={},source=text.splitlines(True))
def code(text):return dict(cell_type='code',metadata={},source=text.splitlines(True),execution_count=None,outputs=[])
for index,cell in enumerate(cells):
    text=''.join(cell['source'])
    if '## Rebuild all four current paper figures' in text:
        before,after=text.split('## Rebuild all four current paper figures',1)
        new=[markdown(before),markdown('''## Eight independent new schools: primary36T, secondary72T

One matched D/G/DG triplet represents each new school. Each horizon is reconstructed from its separately sealed event prefix. The72T record continues the same encounter; it is not an additional independent observation. Complete depletion would freeze later food counts while ending physical effort at depletion; none occurred here.
'''),code('''new_horizons = study.horizon_rows()
new_pairs = study.longer_pairs(new_horizons)
study.print_table(new_pairs)
'''),markdown('''The frozen primary analysis uses10,000 draws of entire paired school vectors with shared resampling indices for both species. Two97.5% marginal percentile intervals target approximate95% familywise coverage, with unstable coverage/tails possible at n=8. No historical cases enter these statistics.
'''),code('''stats = study.primary_statistics(new_pairs)
study.print_table(stats)
primary = [r for r in new_pairs if r["horizon_T"] == 36.]
secondary = [r for r in new_pairs if r["horizon_T"] == 72.]
print("Primary 36T joint positive:", sum(r["joint_positive"] for r in primary), "of8 schools.")
print("Secondary 72T joint positive:", sum(r["joint_positive"] for r in secondary), "of8; descriptive, same trajectories.")
study.print_table(study.secondary_increments(new_pairs))
'''),markdown('''At36T, dolphin captures total168 alone and176 mixed; gannet captures total35 alone and76 mixed. At72T the totals are352→380 for dolphins and85→149 for gannets. The dolphin primary interval spans negative and positive effects, leaving its benefit unresolved. The72T comparison is secondary and cannot replace the primary horizon because its effect is larger.

## Rebuild all four current paper figures'''+after)]
        cells[index:index+1]=new;break
for index,cell in enumerate(cells):
    if cell['cell_type']=='markdown':
        cell['source']=re.sub(r'(?<=[a-zA-Z])(?=\d)',' ',''.join(cell['source'])).splitlines(True)
    cell['id']=f'v3-cell-{index:02d}'
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
            path=HERE/'outputs/eight_school_figures'/(cell['metadata']['figure']+'.png')
            cell['outputs'].append(dict(output_type='display_data',data={'image/png':base64.b64encode(path.read_bytes()).decode(),'text/plain':[cell['metadata']['figure']]},metadata={}))
    assert 'fish_sim.cmodel' not in sys.modules
    import numpy as np
    import matplotlib.image as mpimg
    figures={}
    for name in ('fig1_model','fig2_development','fig3_replication','fig4_mechanism'):
        output=HERE/'outputs/eight_school_figures'/(name+'.png');reference=HERE/'reference_figures_v3'/(name+'.png')
        assert np.array_equal(mpimg.imread(output),mpimg.imread(reference)),name
        figures[name]=dict(pixels_identical_to_reference=True,sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    notebook=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Python3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},cells=cells)
    path=HERE/'FishSim_Professor_Notebook.ipynb';path.write_text(json.dumps(notebook,indent=1)+'\n')
    receipt=dict(status='passed',snapshot='2026-11-09_0231',feeding_encounters=48,new_sealed_horizons=48,new_independent_schools=8,
        code_cells_executed=count,native_steps=0,native_module_imported=False,figures=figures,
        notebook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),wall_seconds=time.monotonic()-started)
    (HERE/'validation/eight_school_notebook_2026-11-09_0231.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
