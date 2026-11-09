"""Focused native-free checks of clocks, baseline equivalence, matching and gates."""
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze
import build
import cases
import evidence
import preflight
import review_actual
from regime_controller import SimpleHerdStrikePlanner, ControllerState, ControllerParameters
from research.prey_mediated.predators import PredatorConfig, initial_predator, observe, apply_contact


def cfg():
    return replace(PredatorConfig(),miss_recovery_duration=.75)


def state(t=0.):
    return replace(initial_predator('D0',(0.,0.,-5.),(1.,0.,0.),cfg()),time=t)


def view(s,offsets=None,velocities=None,ids=None):
    offsets=np.asarray([[2.,-.1,0.],[2.,.1,0.],[2.2,-.1,0.],[2.2,.1,0.]] if offsets is None else offsets,float).reshape(-1,3)
    x=offsets+np.asarray(s.position)
    v=np.zeros_like(x) if velocities is None else np.asarray(velocities,float)
    return observe(s,x,v,np.arange(len(x)) if ids is None else np.asarray(ids),cfg())


def planner(h,ready=False):
    p=SimpleHerdStrikePlanner('exposed',parameters=replace(ControllerParameters(),pressure_minimum=h))
    if ready:p._memory=ControllerState(phase='maintain',phase_started=0.,maintenance_started=0.)
    return p


@pytest.mark.parametrize('h',(1.,2.,3.))
def test_launch_respects_exact_H_clock_inside_a_step(h):
    p=planner(h,True);s=state(h-.02)
    step=p(s,view(s),.05,cfg())
    launch=next(e for e in step.transitions if e.reason=='launch')
    assert launch.time==h
    assert not p.opportunity_events  # proposal is not an observed attack
    p.commit_step(step)
    assert len(p.opportunity_events)==1
    assert p.opportunity_events[0]['pressure_elapsed']==h
    again=p(step.state,view(step.state),.05,cfg())
    assert not any(e.reason=='launch' for e in again.transitions)


@pytest.mark.parametrize('h',(1.,2.,3.))
def test_lost_proximity_requires_new_H_clock(h):
    p=planner(h,True);s=state(h-.1)
    far=p(s,view(s,offsets=[[10.,0.,0.]]),.05,cfg());p.commit_step(far)
    assert p.controller_state.maintenance_started is None
    near=p(far.state,view(far.state),.05,cfg());p.commit_step(near)
    assert p.controller_state.maintenance_started==far.state.time
    assert not any(e.reason=='launch' for e in near.transitions)


@pytest.mark.parametrize('h',(1.,2.,3.))
def test_all_H_keep_exposed_feasible_selection_and_dense_fallback(h):
    s=state(h)
    x=[[1.,0.,0.],[1.1,.1,0.],[1.1,-.1,0.],[1.2,0.,0.],[4.,0.,0.]]
    p=planner(h,True)
    step=p(s,view(s,offsets=x),.05,cfg());p.commit_step(step)
    assert step.state.target_id==4
    q=planner(h,True);vel=np.zeros((5,3));vel[4]=[20.,0.,0.]
    other=q(s,view(s,offsets=x,velocities=vel),.05,cfg());q.commit_step(other)
    assert other.state.target_id!=4
    event=q.opportunity_events[0]
    assert event['selected_neighbor_count']==event['feasible_min_neighbor_count']==3


def test_H2_replays_original_proposals_actual_contacts_and_all_controller_memory():
    path=HERE.parent/'simple_herd_strike_pilot_2026-11-08/controllers.py'
    spec=importlib.util.spec_from_file_location('_original_herdstrike_for_regime_test',path)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    a=old.SimpleHerdStrikePlanner('exposed');b=planner(2.)
    s=state();contacts=0
    for i in range(220):
        offsets=[[10.,0.,0.]] if i in (11,12) else None
        obs=view(s,offsets=offsets)
        x=a(s,obs,.05,cfg());y=b(s,obs,.05,cfg())
        assert build.clean(asdict(x))==build.clean(asdict(y))
        if any(p.mode=='attack' for p in x.pieces) and contacts==0:
            piece=next(p for p in x.pieces if p.mode=='attack')
            t=(piece.body.start+piece.body.end)/2
            x=apply_contact(x,True,t,cfg());y=apply_contact(y,True,t,cfg());contacts+=1
        a.commit_step(x);b.commit_step(y)
        assert a.state_dict()==evidence.original_h2_labels(b.state_dict())
        s=x.state
    assert contacts==1


@pytest.mark.parametrize('h',(0.,4.,float('nan')))
def test_undeclared_H_rejected(h):
    with pytest.raises(ValueError):planner(h)


def test_snapshot_cannot_load_a_different_H():
    with pytest.raises(ValueError,match='policy/version'):
        planner(3.).load_state_dict(planner(1.).state_dict())


def test_pure_60case_preflight_cannot_construct_native_fish(monkeypatch):
    from research.prey_mediated.scenario import TravellingSchool
    def prohibited(*args,**kwargs):raise AssertionError('Native construction is forbidden during pure preparation')
    monkeypatch.setattr(TravellingSchool,'__init__',prohibited)
    result=preflight.validate()
    assert result['pure_cases']==60 and result['anchor_initial_receipts']==8
    assert result['native_constructions']==result['native_steps']==0


def test_grid_and_control_reuse_are_exact():
    c=cases.all_cases();stages=cases.execution_stages()
    assert len(c)==len({x.name for x in c})==60
    assert [len(x) for _,x in stages]==[8,8,12,32]
    assert sum(not x.dolphins for x in c)==12
    assert sum(x.dolphins and x.gannets==0 for x in c)==12
    assert len(cases.smoke_cases())==3 and sum(4/cases.DT for _ in cases.smoke_cases())==9600


def synthetic_rows():
    rows=[]
    for c in cases.all_cases():
        base=10+cases.SEEDS.index(c.school_seed)
        d=base+(c.herding_minimum*c.gannets if c.dolphins else 0)
        g=base+(c.herding_minimum if c.dolphins else 0)
        row=c.asdict()
        row.update(D_captures=d if c.dolphins else 0,D_rate=d/(12*36) if c.dolphins else None,
            G_captures=g if c.gannets else 0,G_rate=g/(c.gannets*36) if c.gannets else None)
        rows.append(row)
    return rows


def test_bootstrap_uses_whole_school_vectors_and_fixed_controls():
    plan={'bootstrap':{'seed':88493009,'draws':10000,'quantiles':[.025,.975]}}
    paired,summary=analyze.paired_statistics(synthetic_rows(),plan)
    assert len(paired)==36 and len(summary)==9
    for row in summary:
        d=row['herding_minimum_T']*row['gannets']/(12*36)
        g=row['herding_minimum_T']/(row['gannets']*36)
        assert row['D_mean_rate_change']==pytest.approx(d)
        assert row['D_pointwise95_low']==pytest.approx(d)
        assert row['D_pointwise95_high']==pytest.approx(d)
        assert row['G_mean_rate_change']==pytest.approx(g)


def test_analysis_rejects_missing_duplicate_or_selected_cells():
    plan={'bootstrap':{'seed':88493009,'draws':10,'quantiles':[.025,.975]}}
    rows=synthetic_rows()
    with pytest.raises(ValueError,match='All60'):analyze.paired_statistics(rows[:-1],plan)
    with pytest.raises(ValueError,match='All60'):analyze.paired_statistics(rows[:-1]+[rows[0]],plan)


def test_same_H_gain_can_still_lose_against_best_tested_Donly():
    rows=synthetic_rows()
    for row in rows:
        if not row['dolphins']:continue
        h=row['herding_minimum_T']
        catches={1.:100,2.:40,3.:20}[h] if row['gannets']==0 else 30
        row['D_captures']=catches;row['D_rate']=catches/(12*36)
    _,summary=analyze.paired_statistics(rows,{'bootstrap':{'seed':88493009,'draws':1000,'quantiles':[.025,.975]}})
    row=next(r for r in summary if r['herding_minimum_T']==3. and r['gannets']==3)
    assert row['best_tested_Donly_H']==1.
    assert row['D_mean_rate_change']>0
    assert row['D_mean_rate_change_vs_best_tested_Donly']<0


def test_physical_cycle_audit_uses_H_and_exposed_policy_not_cell_name():
    event=dict(pressure_elapsed=1.,time=2.,pressure_started=1.,selected_neighbor_count=0,feasible_min_neighbor_count=0)
    config=dict(policy='H1_G3',dolphin_target_policy='exposed',minimum_herding_duration=1.)
    review_actual.validate_dolphin_cycle(event,config)
    with pytest.raises(AssertionError):review_actual.validate_dolphin_cycle(event,{**config,'minimum_herding_duration':3.})
    with pytest.raises(AssertionError):review_actual.validate_dolphin_cycle({**event,'selected_neighbor_count':2},config)


def test_root_approval_is_required_and_bound_to_exact_freeze(tmp_path,monkeypatch):
    monkeypatch.setattr(evidence,'HERE',tmp_path)
    monkeypatch.setattr(evidence,'verify_source_freeze',lambda:{'source_sha256':{}})
    (tmp_path/'protocol.json').write_text('{}')
    (tmp_path/'frozen_sources.json').write_text('{}')
    with pytest.raises(RuntimeError,match='Root approval'):evidence.require_approval('smoke')
    (tmp_path/'SMOKE_RUN_APPROVED.json').write_text(json.dumps(dict(approved=True,stage='smoke',
        protocol_sha256='wrong',frozen_sources_sha256='wrong')))
    with pytest.raises(RuntimeError,match='does not bind'):evidence.require_approval('smoke')


def test_additional_cells_cannot_start_without_all_eight_anchor_replays(tmp_path):
    with pytest.raises(RuntimeError,match='Eight full original anchors'):evidence.require_anchor_stage(tmp_path)


def test_version_normalization_does_not_erase_scientific_differences():
    a=dict(simple=dict(version='test',herding_minimum=3.),memory=dict(maintenance_started=1.))
    with pytest.raises(ValueError):evidence.original_h2_labels(a)
    a['simple']['herding_minimum']=2.
    assert evidence.original_h2_labels(a)['memory']==dict(maintenance_started=1.)


def test_cadence_is_point_one_T_at_original_timestep():
    import cadence
    assert cadence.DT==.00125 and cadence.SAMPLE_STEPS==80 and cadence.PROGRESS_STEPS==800


@pytest.mark.parametrize('observed,recent,exposure,depleted,expected',[
    (35.99999999996726,0.,0.,False,(36.,36.)),
    (35.99999999996726,24.4,7.5,False,(36.-24.4,36.-7.5)),
    (35.99999999996726,36.00000000001,36.00000000002,False,(36.-36.00000000001,36.-36.00000000002)),
    (9.2,4.,2.,True,(9.2-4.,9.2-2.)),
    (9.2,10.,9.20000000001,True,(0.,0.)),
])
def test_actual_summary_block_preserves_legacy_nominal_clock_and_depleted_effort(observed,recent,exposure,depleted,expected):
    # Execute the actual post-loop summary block, never a duplicate helper or
    # model step. These inputs reproduce the replay failure and its edge cases.
    import ast
    tree=ast.parse((HERE/'run.py').read_text())
    blocks=[node for node in ast.walk(tree) if isinstance(node,ast.For)
        and isinstance(node.target,ast.Tuple)
        and [getattr(n,'id',None) for n in node.target.elts]==['who','row']
        and isinstance(node.iter,ast.Call) and isinstance(node.iter.func,ast.Attribute)
        and isinstance(node.iter.func.value,ast.Name) and node.iter.func.value.id=='per']
    assert len(blocks)==1
    code=compile(ast.fix_missing_locations(ast.Module(body=blocks,type_ignores=[])),'actual_recorded_summary_block','exec')
    env=dict(per={'D00':{}},duration=36.,observed_duration=observed,
        depletion_elapsed=observed if depleted else None,semantic_time={'D00':{}},
        available={'D00':0.},exposure={'D00':exposure},with_recent_event={'D00':recent})
    exec(code,env)
    row=env['per']['D00']
    assert (row['sampled_no_recent_gannet_event_T'],row['sampled_no_opportunity_T'])==expected
