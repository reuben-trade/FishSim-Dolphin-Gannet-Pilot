"""Meaningful native-free regression gates for the count-only extension."""
import ast,csv,json,sys
from pathlib import Path
import numpy as np
import pytest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT),str(ROOT/'lib')]
from cases import (Case,SEEDS,all_cases,retained_cases,combined_cases,smoke_cases,execution_stages,DT,DISCOVERY)

@pytest.fixture(autouse=True)
def prohibit_native_construction(monkeypatch):
    from research.prey_mediated.scenario import TravellingSchool
    def forbidden(*a,**k):raise AssertionError('Native construction forbidden in pure tests')
    monkeypatch.setattr(TravellingSchool,'__init__',forbidden)

def test_fixed_balanced_grid_and_unique_new_vs_retained_execution_inventory():
    assert len(all_cases())==48 and len(retained_cases())==60 and len(combined_cases())==108
    assert len({c.name for c in combined_cases()})==108
    assert {c.name for c in all_cases()}.isdisjoint({c.name for c in retained_cases()})
    assert [len(c) for _,c in execution_stages()]==[4,12,4,12,4,12]
    assert [name for name,_ in execution_stages()]==['G9_controls','G9_mixed','G12_controls','G12_mixed','G18_controls','G18_mixed']
    for n in (9,12,18):
        cells=[c for c in all_cases() if c.gannets==n]
        assert len(cells)==16 and {c.school_seed for c in cells}==set(SEEDS)
        assert sum(not c.dolphins for c in cells)==4
        assert [sum(i%3==site for i in range(n)) for site in range(3)]==[n//3]*3

@pytest.mark.parametrize('args',[(39065501,1.,9),(39061001,1.,8),(39061001,4.,9),
    (39061001,None,0,False),(39061001,1.,18,False),(39061001,True,9)])
def test_unprespecified_cells_rejected(args):
    with pytest.raises(ValueError):Case(*args)

def test_exact_five_smokes_and_total_budget():
    assert len(smoke_cases())==5
    assert {(c.herding_minimum,c.gannets,c.presence) for c in smoke_cases()}=={
        (None,9,'G'),(None,18,'G'),(1.,9,'DG'),(2.,12,'DG'),(3.,18,'DG')}
    assert sum(round(36/DT) for _ in all_cases())==1382400
    assert sum(round(4/DT) for _ in smoke_cases())==16000
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['all_stage_maximum_native_steps']==1382400+16000==1398400

def test_exact_sixty_old_receipts_and_nested_states_all_new_counts_native_free():
    import preflight
    result=preflight.validate()
    assert result['pure_new_cases']==48 and result['exact_retained_initial_receipts']==60
    assert result['native_steps']==result['native_constructions']==0
    assert result['pure_to_archived_native_heading_max_abs_roundoff']<=1e-12
    assert result['actual_native_heading_comparison'].startswith('Exact')

def test_physical_controller_cadence_and_review_sources_remain_byte_identical():
    for name in ('regime_controller.py','gannet.py','horizons.py','cadence.py','review_actual.py'):
        assert (HERE/name).read_bytes()==(DISCOVERY/name).read_bytes()

def actual_step_loop(path):
    tree=ast.parse(path.read_text())
    return next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='number')

class NormalizeStorageGuard(ast.NodeTransformer):
    def visit_Assert(self,node):
        return ast.Pass() if 'disk_usage' in ast.unparse(node.test) else self.generic_visit(node)
    def visit_Expr(self,node):
        return ast.Pass() if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='reserve' else self.generic_visit(node)

def test_resolved_motion_sampling_accounting_loop_is_exact_except_storage_guard():
    old=NormalizeStorageGuard().visit(actual_step_loop(DISCOVERY/'run.py'))
    new=NormalizeStorageGuard().visit(actual_step_loop(HERE/'run.py'))
    assert ast.dump(old)==ast.dump(new)

def synthetic_rows():
    rows=[]
    for c in combined_cases():
        i=SEEDS.index(c.school_seed)
        d=20+i-int(c.herding_minimum or 0)+(c.gannets//3 if c.dolphins else 0)
        g=4+i+c.gannets//3+(int(c.herding_minimum or 0) if c.dolphins else 0)
        rows.append(dict(c.asdict(),D_captures=d if c.dolphins else 0,G_captures=g if c.gannets else 0,
            D_rate=d/432 if c.dolphins else None,G_rate=g/(c.gannets*36) if c.gannets else None))
    return rows

def test_whole_four_school_bootstrap_uses_shared_controls_and_per_bird_rates():
    from analyze import paired_statistics
    plan=json.loads((HERE/'analysis_plan.json').read_text());pairs,summary=paired_statistics(synthetic_rows(),plan)
    assert len(pairs)==72 and len(summary)==18 and all(r['independent_schools']==4 for r in summary)
    values=np.asarray([[[p['D_rate_change'],p['G_rate_change']] for p in pairs if p['school_seed']==seed] for seed in SEEDS])
    index=np.random.default_rng(88493009).integers(0,4,size=(10000,4));weights=np.column_stack([(index==i).sum(axis=1) for i in range(4)])
    expected=np.quantile(np.einsum('bi,ijk->bjk',weights,values)/4,[.025,.975],axis=0)
    for j,row in enumerate(summary):
        for k,species in enumerate(('D','G')):
            assert row[species+'_mean_rate_change']==pytest.approx(values[:,j,k].mean(),abs=1e-15)
            assert [row[species+'_pointwise95_low'],row[species+'_pointwise95_high']]==pytest.approx(expected[:,j,k],abs=1e-15)

@pytest.mark.parametrize('change',['missing','duplicate'])
def test_final_analysis_refuses_partial_or_duplicate_inventory(change):
    from analyze import paired_statistics
    rows=synthetic_rows()
    if change=='missing':rows.pop()
    else:rows[-1]=rows[0]
    with pytest.raises(ValueError):paired_statistics(rows,json.loads((HERE/'analysis_plan.json').read_text()))

def test_native_builder_checks_fresh_approval_before_preparing(monkeypatch):
    import evidence,build
    def denied(stage):raise RuntimeError('No fresh stage approval')
    monkeypatch.setattr(evidence,'require_approval',denied)
    monkeypatch.setattr(build,'prepare_case',lambda c:pytest.fail('Crossed native boundary before approval'))
    c=all_cases()[0]
    with pytest.raises(RuntimeError,match='fresh'):build.build(c.school_seed,c.policy,presence=c.presence)

def test_all_candidate_python_compiles():
    for p in HERE.glob('*.py'):compile(p.read_text(),str(p),'exec')
