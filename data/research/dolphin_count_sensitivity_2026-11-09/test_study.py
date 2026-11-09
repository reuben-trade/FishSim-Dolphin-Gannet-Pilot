"""Native-free tests for changed population, selection and analysis behavior."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT), str(ROOT/'lib')]
from cases import Case, SEEDS, FIXTURES, GANNET_COUNTS, HERDING_MINIMA, DT, cases_for


@pytest.fixture(autouse=True)
def prohibit_native_construction_and_stepping(monkeypatch):
    from research.prey_mediated.encounter import Encounter
    from research.prey_mediated.scenario import TravellingSchool
    from research.prey_mediated.surface_safe_school import SurfaceSafeSchool
    def forbidden(*args, **kwargs):
        raise AssertionError('Native construction/stepping is forbidden in candidate software tests')
    for cls in (Encounter, TravellingSchool, SurfaceSafeSchool):
        monkeypatch.setattr(cls, '__init__', forbidden)
        monkeypatch.setattr(cls, 'step', forbidden)


def synthetic_old_rows():
    rows = []
    cases = [Case(s, h, g, 12) for s in SEEDS for h in HERDING_MINIMA for g in GANNET_COUNTS]
    cases += [Case(s, None, g, 0) for s in SEEDS for g in GANNET_COUNTS[1:]]
    for c in cases:
        d = 10 if c.dolphins else 0
        b = 3 if c.gannets else 0
        if c.dolphins and c.gannets:
            d = 9
        if (c.herding_minimum, c.gannets) in FIXTURES:
            d, b = 30, 5
        if (c.herding_minimum, c.gannets) == (3., 36):
            d, b = 50, 2
        rows.append(dict(c.asdict(), D_captures=d, G_captures=b,
            D_rate=d/(c.dolphin_count*36) if c.dolphins else None,
            G_rate=b/(c.gannets*36) if c.gannets else None))
    return rows


def synthetic_new_rows(regimes=FIXTURES):
    rows = []
    for c in cases_for(regimes):
        school_index = SEEDS.index(c.school_seed)
        d = 20 + (school_index-1 if c.gannets else 0)
        b = 2+school_index if c.gannets else 0
        rows.append(dict(c.asdict(), D_captures=d, G_captures=b,
            D_rate=d/(24*36), G_rate=b/(c.gannets*36) if c.gannets else None))
    return rows


def test_no_actual_selection_or_native_authority():
    from cases import all_cases
    from evidence import require_approval
    with pytest.raises(RuntimeError, match='Final regimes unset'):
        all_cases()
    with pytest.raises(RuntimeError, match='not authorized'):
        require_approval('initialization')


def test_population_case_type_and_deduplicated_controls():
    for count in (True, False, 6, 18, 24.):
        with pytest.raises(ValueError):
            Case(SEEDS[0], 1., 9, count)
    assert len(cases_for(FIXTURES)) == 16
    assert len(cases_for(((1.,9), (1.,12)))) == 12
    assert len(cases_for(((1.,9), (1.,9)))) == 8
    assert 16*round(36/DT) == 460800
    assert 4*round(4/DT) == 12800
    assert 460800+12800 == 473600
    with pytest.raises(ValueError):
        cases_for(((1., 0),))


def test_complete_map_selection_retains_negative_cells_and_tie_rules():
    from select_regimes import select
    result = select(synthetic_old_rows())
    assert len(result['all_24_candidates']) == 24
    a, b = result['regimes']
    assert (a['herding_minimum_T'], a['gannets']) == (3.,36)
    assert (b['herding_minimum_T'], b['gannets']) == (1.,9)
    assert a['joint_positive_schools'] == 0 and b['joint_positive_schools'] == 4


def test_no_B_eligible_and_A_B_deduplication():
    from select_regimes import select
    rows = synthetic_old_rows()
    for row in rows:
        if row['dolphins'] and row['gannets']:
            row['G_captures'] = 3
            row['G_rate'] = 3/(row['gannets']*36)
    result = select(rows)
    assert not result['B_eligible'] and len(result['regimes']) == 1
    rows = synthetic_old_rows()
    for row in rows:
        if row['herding_minimum_T'] == 3. and row['gannets'] == 36:
            row['G_captures'] = 4
            row['G_rate'] = 4/(36*36)
    result = select(rows)
    assert result['B_eligible'] and len(result['regimes']) == 1
    assert len(result['regimes'][0]['selection_labels']) == 2


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'wrong_rate'])
def test_selection_rejects_incomplete_or_inconsistent_map(change):
    from select_regimes import select
    rows = synthetic_old_rows()
    if change == 'missing':
        rows.pop()
    elif change == 'duplicate':
        rows[-1] = rows[0]
    else:
        rows[0]['D_rate'] = 1.
    with pytest.raises(ValueError):
        select(rows)


def test_whole_school_bootstrap_and_difference_in_partner_effect():
    from analyze import paired_statistics, BOOTSTRAP_SEED
    paired, summary = paired_statistics(synthetic_new_rows(), synthetic_old_rows(), FIXTURES)
    assert len(paired) == 8 and len(summary) == 2
    names = ('D12_partner_rate_change', 'D24_partner_rate_change', 'D24_minus_D12_partner_rate_change',
        'D24_minus_D12_mixed_rate', 'G_with_D12_partner_rate_change', 'G_with_D24_partner_rate_change')
    vectors = np.asarray([[[r[name] for name in names] for r in paired if r['school_seed'] == s] for s in SEEDS])
    indices = np.random.default_rng(BOOTSTRAP_SEED).integers(0,4,size=(10000,4))
    weights = np.column_stack([(indices == i).sum(axis=1) for i in range(4)])
    expected = np.quantile(np.einsum('bi,ijk->bjk',weights,vectors)/4,[.025,.975],axis=0)
    for j, row in enumerate(summary):
        assert row['independent_schools'] == 4
        for k, name in enumerate(names):
            assert row[name+'_mean'] == pytest.approx(vectors[:,j,k].mean(),abs=1e-15)
            assert [row[name+'_pointwise95_low'],row[name+'_pointwise95_high']] == pytest.approx(expected[:,j,k],abs=1e-15)
    for r in paired:
        assert r['D24_minus_D12_partner_rate_change'] == pytest.approx(r['D24_partner_rate_change']-r['D12_partner_rate_change'])
    assert summary[0]['D24_partner_rate_change_negative_schools'] > 0


def test_new_population_needs_its_own_alone_controls_and_denominator():
    from analyze import paired_statistics
    rows = synthetic_new_rows()
    with pytest.raises(ValueError):
        paired_statistics([r for r in rows if r['gannets']], synthetic_old_rows(), FIXTURES)
    rows[0]['D_rate'] *= 2
    with pytest.raises(ValueError):
        paired_statistics(rows, synthetic_old_rows(), FIXTURES)


def test_integer_first_exact_zero_population_interaction_all_schools_and_bootstrap():
    from analyze import paired_statistics
    old, new = synthetic_old_rows(), synthetic_new_rows()
    for row in old:
        if row['dolphins']:
            row['D_captures'] = 10 if row['gannets'] else 9
            row['D_rate'] = row['D_captures']/(12*36)
    for row in new:
        row['D_captures'] = 15 if row['gannets'] else 13
        row['D_rate'] = row['D_captures']/(24*36)
    paired, summary = paired_statistics(new, old, FIXTURES)
    assert all(r['D24_minus_D12_partner_rate_change'] == 0. for r in paired)
    for row in summary:
        name = 'D24_minus_D12_partner_rate_change'
        assert row[name+'_mean'] == row[name+'_sample_sd'] == 0.
        assert row[name+'_pointwise95_low'] == row[name+'_pointwise95_high'] == 0.
        assert row[name+'_zero_schools'] == 4
        assert row[name+'_positive_schools'] == row[name+'_negative_schools'] == 0


def test_pure_preflight_original_starts_roles_and_physical_source():
    from preflight import validate
    result = validate()
    assert result['native_constructions'] == result['native_steps'] == result['native_constructor_attempts'] == 0
    assert result['exact_archived_D12_receipts'] == result['pure_D24_fixture_states'] == 16
    assert result['same_physical_input_identity_attack_probes'] == 48
    assert len(result['unchanged_runner_functions']) == 15
    assert result['physical_runner_tail_exact_after_constructor'] is True


def test_native_build_denied_before_preparation(monkeypatch):
    import build
    monkeypatch.setattr(build, 'prepare_case', lambda c: pytest.fail('Native preparation before permission'))
    with pytest.raises(RuntimeError, match='not authorized'):
        build.build(SEEDS[0], 'D24_H1_G9')


def test_candidate_compiles():
    for p in HERE.glob('*.py'):
        compile(p.read_text(), str(p), 'exec')


@pytest.mark.parametrize('regimes,phase_counts', [(((1.,9),),(2,2,6)),
    (((1.,9),(1.,12)),(3,3,9)), (FIXTURES,(4,4,12))])
def test_phase_inventory_control_first_and_budget(regimes, phase_counts):
    from cases import phase_cases, execution_stages
    groups = [phase_cases(stage, regimes) for stage in ('smoke','pilot','remainder')]
    assert tuple(map(len,groups)) == phase_counts
    assert {c.name for c in groups[1]}.isdisjoint({c.name for c in groups[2]})
    assert {c.name for c in groups[1]+groups[2]} == {c.name for c in cases_for(regimes)}
    for stage in ('smoke','pilot','remainder'):
        (label, controls), (mixed_label, mixed) = execution_stages(stage, regimes)
        assert label == 'dolphin_only_controls' and mixed_label == 'mixed'
        assert all(c.gannets == 0 for c in controls) and all(c.gannets > 0 for c in mixed)
        assert len(controls)+len(mixed) == len(phase_cases(stage,regimes))
    assert len(groups[0])*3200 + (len(groups[1])+len(groups[2]))*28800 <= 473600


def test_scheduler_has_pool_completion_barrier_and_outer_shared_lease():
    import ast
    tree = ast.parse((HERE/'run.py').read_text())
    wave = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == '_execute_wave')
    assert any(isinstance(n,ast.With) and 'ProcessPoolExecutor' in ast.unparse(n.items[0].context_expr)
        for n in ast.walk(wave))
    main = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == 'main')
    loops = [n for n in ast.walk(main) if isinstance(n,ast.For) and ast.unparse(n.iter) == 'execution_stages(stage)']
    assert len(loops) == 1
    assert isinstance(loops[0].body[0], ast.Expr) and loops[0].body[0].value.func.id == '_execute_wave'
    locks = [n for n in ast.walk(main) if isinstance(n,ast.With) and 'TASK_LEASE.open' in ast.unparse(n.items[0].context_expr)]
    assert len(locks) == 1
    assert 'task.fileno()' in ast.unparse(locks[0].body[0])
    assert 'legacy.fileno()' in ast.unparse(locks[0].body[1])


def test_all_native_phases_remain_closed_without_real_selection():
    import evidence
    for stage in ('initialization','smoke','pilot','remainder'):
        with pytest.raises(RuntimeError, match='not authorized'):
            evidence.require_approval(stage)


def test_fixture_preflight_cannot_create_input_freeze(monkeypatch):
    import freeze
    monkeypatch.setattr(freeze,'read',lambda p: dict(status='passed',fixture_only=True,
        actual_regimes_selected=False,native_steps=0,native_constructions=0))
    monkeypatch.setattr(freeze,'write',lambda *a: pytest.fail('Fixture receipt produced a freeze'))
    with pytest.raises(RuntimeError, match='Selected-regime'):
        freeze.create('inputs')


def test_absorbing_depletion_retains_nominal_per_animal_feeding_denominator():
    from horizons import horizon_record
    actors = {f'D{i:02d}':dict(captures=1 if i < 8 else 0,launches=1,contacts=1,distance={}) for i in range(24)}
    record = horizon_record(nominal_T=36.,observed_T=2.,initial_count=8,final_count=0,
        per_actor=actors,native_steps=1600,structure={},terminal=True)
    assert record['species']['D']['captures_per_actor_per_nominal_T'] == 8/(24*36)
    assert record['species']['D']['observed_effort_T'] == 48.
    assert record['native_steps'] == 1600 and record['absorbing_no_food_continuation']


def test_reused_raw_case_parser_reconciles_a_real_completed_fixture_without_native_work():
    import csv
    from analyze import case_row
    from reference import reference_path
    path = Path('/tmp/FishSim_High_Count_Extension_2026-11-09/full_36T_v1/analysis_final/case_outcomes.csv')
    with path.open(newline='') as handle:
        expected = next(r for r in csv.DictReader(handle)
            if r['school_seed'] == str(SEEDS[0]) and r['herding_minimum_T'] == '1.0' and r['gannets'] == '9')
    row = case_row(reference_path(SEEDS[0],1.,9,12), expected, reference=True)
    assert row['D_captures'] == int(expected['D_captures'])
    assert row['G_captures'] == int(expected['G_captures'])
    assert row['D_rate'] == row['D_captures']/(12*36)
    assert row['G_rate'] == row['G_captures']/(9*36)


@pytest.mark.parametrize('mismatch',['phase','output'])
def test_case_phase_and_output_guard_precedes_output_creation_and_constructor(monkeypatch,tmp_path,mismatch):
    import build
    import physical_run
    case = Case(SEEDS[0],1.,9)
    approved = tmp_path/'approved'
    output = tmp_path/'wrong' if mismatch == 'output' else approved
    monkeypatch.setattr(physical_run,'require_approval',lambda stage:None)
    monkeypatch.setattr(physical_run,'decode',lambda *args:case)
    monkeypatch.setattr(physical_run,'phase_cases',lambda stage:() if mismatch == 'phase' else (case,))
    monkeypatch.setattr(physical_run,'phase_output',lambda stage:approved)
    monkeypatch.setattr(physical_run,'all_cases',lambda:(case,))
    monkeypatch.setattr(build,'build',lambda *args,**kwargs:pytest.fail('Native boundary crossed before exact phase/path guard'))
    with pytest.raises(ValueError,match='phase'):
        physical_run.run_case(case.school_seed,case.policy,output,presence=case.presence)
    assert not output.exists()
