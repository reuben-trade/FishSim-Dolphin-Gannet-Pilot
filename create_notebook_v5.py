"""Build an additive one-rule notebook only after the complete sweep is sealed.

--prepare-only writes an explicitly UNEXECUTED private scaffold. Normal execution
requires the versioned REGIME_SNAPSHOT metadata and all complete-map gates before
any new result.
Nothing here advances native simulation time.
"""
from __future__ import annotations
import argparse
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parent


def md(text):
    text=re.sub(r'(?<=\d)(?=[a-z])',' ',text)
    text=re.sub(r'(?<=\dT)(?=[a-z])',' ',text)
    text=re.sub(r'(?<=%)(?=[a-z])',' ',text)
    for old,new in [('preserves72','preserves 72'),('adds60','adds 60'),('all60','all 60'),
                    ('produced41','produced 41'),('and87','and 87'),('setting61001','setting 61001'),
                    ('from+1','from +1'),('to0','to 0'),('from+5','from +5'),('to+2','to +2'),
                    ('n=4and','n=4 and'),('four36','four 36')]:
        text=text.replace(old,new)
    return dict(cell_type='markdown',metadata={},source=text.strip().splitlines(True))
def code(text,figure=None):return dict(cell_type='code',metadata={} if figure is None else {'figure':figure},source=text.strip().splitlines(True),execution_count=None,outputs=[])


def cells():
    result=[
    md('''# FishSim: one shared hunting rule and conditional feeding benefits

**Run All** checks sealed evidence, reconstructs the complete declared parameter map and its uncertainty, rebuilds the four current report figures, and exports the result tables. Default execution imports no native simulator and runs zero native steps.

The inventory preserves72historical feeding executions and adds60corrected-v2 sweep executions. Eight sweep executions are exact replays of historical outcomes, not new independent samples. The sweep has four previously observed school units. Its discovery map is kept separate from the original pilots and the later eight-school replication. Numerical sensitivity remains unresolved.

The main comparison adds gannets while keeping the same dolphin herding rule and H. The stronger best-tested D-only H comparison is separately labelled. Original notebooks, manifests, source receipts and historical policy comparisons remain archived unchanged.
'''),
    code('''from pathlib import Path
import sys
ROOT=Path.cwd()
assert (ROOT/'notebook_support_v5.py').is_file(), "Open Jupyter in the repository folder."
sys.path.insert(0,str(ROOT))
import notebook_support_v5 as study
print("Default analysis: saved evidence only; zero native simulation steps.")'''),
    md('''## Verify the complete evidence before inspecting outcomes

This checks every previous protected file, all60current case seals, the exact eight-anchor replay, source closure, complete physical review and raw-event accounting. It independently reconstructs the frozen whole-school bootstrap and the best-H reselection within each draw. An incomplete map is rejected.
'''),
    code('''validation=study.verify_inputs()
study.print_table([validation])'''),
    md('''## One fixed dolphin rule and fair controls

After H of continuous near-prey pressure, a dolphin chooses a physically feasible target, preferring fewer radius-2 neighbours, and makes one bounded strike before ordinary recovery. H does not certify completed herding; the fish need not be moving outward. No bird count, dive cue or capture bonus enters the dolphin controller. Gannets affect dolphins through prey dynamics and competition.

The native C++ FishSim engine is inherited from [yangyushi/FishSim](https://github.com/yangyushi/FishSim); this project adds predator controllers, experiment harnesses and analysis. Contact success q=.7 is uncalibrated conditional eligible-contact success, not success per observed field attack.
'''),
    code('''parameters=study.historical.actual_parameter_table()+[
 {"parameter":"Sweep herding minima H (T)","value":"1, 2, 3"},
 {"parameter":"Sweep gannet counts","value":"0, 1, 3, 6; count-matched G-only controls"},
 {"parameter":"Sweep independent school units","value":"4 previously observed schools"},
 {"parameter":"Sweep encounter duration / dt (T)","value":"36 / 0.00125"}]
study.print_table(parameters)'''),
    md('''## Positive original pilots, kept distinct from later checks

The original exposed-prey rule produced41→48dolphin captures across two development schools and87→101across two fresh follow-up schools, each under two random settings. Four follow-up repetitions still represent two independent schools. The sweep replays only setting61001on these four schools; its anchors do not replace the original pilot totals.
'''),
    code('''shared=study.original_shared_pairs()
for cohort,values in shared.items():
 print(cohort)
 study.print_table(values,["school","capture_seed","D","DG","difference","change_percent"])'''),
    md('''## Independent eight-school replication and numerical sensitivity

The coarse36T primary analysis and fine36T check use the same eight schools. Only the coarse primary estimates have prespecified97.5%marginal bootstrap intervals. The coarse72T outcomes continue the same trajectories; there is no fine72T run. Neither a second grid nor a longer horizon creates independent schools.
'''),
    code('''new_horizons=study.historical.horizon_rows()
new_pairs=study.historical.longer_pairs(new_horizons)
stats=study.historical.primary_statistics(new_pairs)
study.print_table(stats)'''),
    code('''grid_cases=study.historical.grid_case_rows()
grid_effects=study.historical.grid_effect_rows(grid_cases)
study.print_table(grid_effects,["school_seed","coarse_D_partner_effect","fine_D_partner_effect","coarse_G_partner_effect","fine_G_partner_effect","D_effect_fine_minus_coarse","G_effect_fine_minus_coarse"])'''),
    code('''study.print_table(study.historical.grid_summary(grid_effects))
study.print_table(study.historical.secondary_increments(new_pairs))'''),
    md('''The fine grid changes the mean dolphin partner effect from+1to0captures per school and the gannet effect from+5.125to+2.5. The positive original cohorts were not rerun on the finer grid. Substantial numerical sensitivity prevents a convergence claim or a general dolphin-facilitation conclusion.

## Complete corrected-v2 parameter map

The exploratory map varies H={1,2,3}T and G={0,1,3,6}with12dolphins, plus G-only controls for each positive count. All60condition-school rows are retained. The stopped v1attempt remains immutable supporting provenance and contributes no case to this map. Its two summary-clock recording exports were corrected without changing physics, controllers or the strict anchor comparator.
'''),
    code('''sweep_rows=study.sweep_case_rows()
study.print_table(sweep_rows,["school_seed","herding_minimum_T","gannets","presence","anchor_replay","D_captures","G_captures","D_contacts","G_contacts","remaining_fish"])'''),
    code('''sweep_pairs,sweep_summary=study.sweep_tables(sweep_rows)
study.print_table(sweep_summary,["herding_minimum_T","gannets","D_mean_rate_change","D_pointwise95_low","D_pointwise95_high","G_mean_rate_change","G_pointwise95_low","G_pointwise95_high","both_positive_schools"])'''),
    code('''school_points=study.whole_map_school_points(sweep_pairs)
study.print_table(school_points)'''),
    md('''The primary dolphin effect compares mixed return against the SAME-H dolphin-only control. Gannet effects use per-bird returns against count-matched G-only controls, reused across H. One common whole-school bootstrap resamples all controls and responses together. The pointwise95%intervals have n=4and no multiplicity adjustment: selected positive cells do not establish a winning regime.

The stronger comparator below selects one D-only H across the entire discovery bank, with the smallest-H tie rule, and reselects H within every bootstrap draw. It is neither a per-school oracle nor an unrestricted optimal independent policy. Held-out validation, if later conducted, must keep its selection frozen.
'''),
    code('''study.print_table(sweep_summary,["herding_minimum_T","gannets","best_tested_Donly_H","best_tested_Donly_mean_rate","D_mixed_mean_rate","D_mean_rate_change_vs_best_tested_Donly","D_vs_best_tested_pointwise95_low","D_vs_best_tested_pointwise95_high"])'''),
    md('''## Collective fish state, contacts and food

These diagnostic summaries use every declared setting and school, without selecting successful post-dive windows. Live-school state is averaged over observed nonempty saved frames; contacts and food retain the full36Tdenominator. Survival, consumption and threshold-sensitive trajectories can change the summaries. These are descriptive associations, not demonstrated causal mediation or biological cooperation.
'''),
    code('''diagnostics=study.sweep_diagnostics(sweep_rows)
study.print_table(diagnostics,["school_seed","herding_minimum_T","gannets","presence","time_mean_r90","time_mean_outward_fraction","D_launches","D_contacts","D_captures","remaining_fish"])'''),
    md('''## Rebuild the four current paper figures

The source verifies sealed raw evidence before plotting. Historical depth/timing figures and policy alternatives remain in versioned snapshots; the current main report follows one shared dolphin rule. Figure2keeps positive pilots and eight-school numerical sensitivity in explicitly separate panels.
'''),
    code('''figure_folder=study.reproduce_figures()
print("Four current report figures rebuilt from sealed evidence:",figure_folder)'''),
    code('''study.show_figure("fig1_model",figure_folder)''','fig1_model'),
    code('''study.show_figure("fig2_cohorts",figure_folder)''','fig2_cohorts'),
    code('''study.show_figure("fig3_regime_map",figure_folder)''','fig3_regime_map'),
    code('''study.show_figure("fig4_diagnostics",figure_folder)''','fig4_diagnostics'),
    md('''## Export tables and retain earlier evidence

The14historical tables remain separate from five new sweep tables. Older table exports retain the archived development alternatives; they are not pooled into the current one-rule map or presented as the main policy comparison.
'''),
    code('''rows=study.historical.case_rows()
development=study.historical.paired_rows(rows,"development")
replication=study.historical.paired_rows(rows,"replication")
joint=study.historical.reciprocity_rows(rows)
depth=study.historical.depth_rows(rows)
study.historical.export_tables(rows,development,replication,joint,depth,new_horizons,new_pairs,stats,grid_cases,grid_effects)
print("New sweep tables:")
print("\\n".join(study.export_regime_tables(sweep_rows,sweep_pairs,sweep_summary,diagnostics)))'''),
    md('''## Reproduction scopes and optional new simulations

The unchanged historical `run_model.py` covers the original historical pair/eight encounters. The additive `run_current_model.py` executes the eight-school H=2coarse/fine replication rather than this H×G sweep. Its known-host binary requires the documented CPython3.12/Linux/glibc environment. The separately source-built Linux amd64 image passed bounded BuildKit checks; its host Docker bind-mount command and Windows/macOS execution remain untested. See `CURRENT_MODEL_SETUP.md` for setup, scope and validation receipts.

Running new simulations creates new output directories, costs time and does not add independent schools when the same starts are reused. The optional execution toggle below defaults to False; its plan command takes zero native steps. The analysis notebook is portable independently of the native binary.
'''),
    code('''assert "fish_sim.cmodel" not in sys.modules
print("Notebook complete: default native imports = 0; native simulation steps = 0.")''')]
    addon=read_optional_cells()
    result[-1:-1]=addon
    return result


def read_optional_cells():
    proposal=json.loads((ROOT/'CURRENT_MODEL_NOTEBOOK_SECTION.json').read_text())
    if proposal['default_native_steps']!=0:raise ValueError('Native-free default is required')
    addon=proposal['cells']
    for cell in addon:
        if cell['cell_type']!='code':continue
        source=''.join(cell['source'])
        if '"--plan"' in source:
            source=source.replace('subprocess.run([','plan_result = subprocess.run([')
            source=source.replace('], check=True)','], check=True, cwd=ROOT, capture_output=True, text=True)')
            source+='\nprint(plan_result.stdout)\n'
        else:
            source=source.replace('subprocess.run(command, check=True)','subprocess.run(command, check=True, cwd=ROOT)')
        compile(source,'<optional current-model cell>','exec')
        cell['source']=source.splitlines(True)
    return addon


def build(*,prepare_only=False):
    notebook_cells=cells()
    for i,cell in enumerate(notebook_cells):cell['id']=f'v5-cell-{i:02d}'
    if not prepare_only:
        os.chdir(ROOT);sys.path.insert(0,str(ROOT));namespace={'__name__':'__main__'}
        started=time.monotonic();count=0
        for cell in notebook_cells:
            if cell['cell_type']!='code':continue
            count+=1;capture=io.StringIO()
            with contextlib.redirect_stdout(capture):exec(compile(''.join(cell['source']),f'<v5cell{count}>','exec'),namespace)
            cell['execution_count']=count
            if capture.getvalue():cell['outputs'].append(dict(output_type='stream',name='stdout',text=capture.getvalue().splitlines(True)))
            if cell['metadata'].get('figure'):
                p=ROOT/'outputs/regime_figures'/(cell['metadata']['figure']+'.png')
                cell['outputs'].append(dict(output_type='display_data',data={'image/png':base64.b64encode(p.read_bytes()).decode(),'text/plain':[cell['metadata']['figure']]},metadata={}))
        assert 'fish_sim.cmodel' not in sys.modules
        import numpy as np
        import matplotlib.image as mpimg
        figures={}
        for name in ['fig1_model','fig2_cohorts','fig3_regime_map','fig4_diagnostics']:
            generated=ROOT/'outputs/regime_figures'/(name+'.png');reference=ROOT/'reference_figures_v5'/(name+'.png')
            if not np.array_equal(mpimg.imread(generated),mpimg.imread(reference)):raise ValueError('Paper figure pixels differ: '+name)
            figures[name]=dict(pixels_identical_to_report=True,sha256=hashlib.sha256(generated.read_bytes()).hexdigest())
    notebook=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Python3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},cells=notebook_cells)
    path=ROOT/('FishSim_Regime_Candidate_UNEXECUTED.ipynb' if prepare_only else 'FishSim_Professor_Notebook.ipynb')
    path.write_text(json.dumps(notebook,indent=1)+'\n')
    if prepare_only:
        print(json.dumps(dict(stage='unexecuted_private_scaffold',file=path.name,code_cells=sum(c['cell_type']=='code' for c in notebook_cells),native_steps=0,publication_performed=False)))
    else:
        receipt=dict(status='passed',snapshot=namespace['study'].snapshot()['version'],feeding_execution_records=132,
            sweep_cells=60,exact_historical_replay_executions=8,sweep_independent_known_schools=4,
            code_cells_executed=count,exported_csv_tables=19,native_steps=0,native_module_imported=False,
            figures=figures,notebook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),wall_seconds=time.monotonic()-started)
        (ROOT/'validation').mkdir(exist_ok=True)
        (ROOT/'validation'/f"regime_notebook_{receipt['snapshot']}.json").write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true')
    build(prepare_only=parser.parse_args().prepare_only)
