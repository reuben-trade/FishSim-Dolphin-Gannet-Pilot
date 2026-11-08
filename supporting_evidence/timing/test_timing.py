"""Pure predator fixtures: no native fish model is imported or constructed."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1])]
import timing as T
from research.prey_mediated import predators as P


def fixture(time=1.):
    cfg=P.PredatorConfig(species='G',sense_radius=1e9)
    state=P.initial_predator('G0',(0.,0.,3.),(1.,0.,0.),cfg,time=time)
    state=replace(state,mode='orient',target_id=0)
    x=np.array([(1.+i*.1,0.,-2.) for i in range(4)])
    obs=P.observe(state,x,np.zeros_like(x),np.arange(4),cfg)
    cue=T.Cue('D00',1,time,(0.,0.,-2.),0,(1.,0.,-2.),time)
    return state,obs,cfg,cue


def dense(seed=91):
    spec=importlib.util.spec_from_file_location('_timing_test_dense',T.DENSE_PATH)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module.DensePatchGannetPlanner(seed=seed)


def bus_fixture(enabled=True,lag=1.,cue=None):
    bus=T.TimingBus(None,enabled=enabled,lag=lag)
    bus.in_step=True;bus.step_start=1.
    bus.staged={};bus.histories={};bus.cues=[] if cue is None else [cue]
    return bus


def test_disabled_wrapper_exact_motion_events_and_target_rng():
    state,obs,cfg,cue=fixture()
    reference=dense();wrapped=T.TimedGannet(dense(),bus_fixture(False,cue=cue))
    for _ in range(30):
        expected=reference(state,obs,.00125,cfg)
        actual=wrapped(state,obs,.00125,cfg)
        assert actual==expected
        reference.commit_step(expected);wrapped.commit_step(actual)
        assert wrapped.state_dict()==reference.state_dict()
        state=actual.state;obs=replace(obs,time=state.time)
        wrapped.bus.step_start=state.time


@pytest.mark.parametrize('mode',['orient','search','recovery','plunge','pursuit','ascent'])
def test_allow_hook_exact_original_integrator(mode):
    state,obs,cfg,_=fixture()
    active=mode in ('plunge','pursuit')
    state=replace(state,mode=mode,ready_at=state.time+.0005 if mode=='recovery' else state.time,
        bout_start=state.time if active else None,bout_deadline=state.time+6. if active else None)
    assert T.advance_with_gate(state,obs,.00125,cfg,lambda *_:True)==P.advance(state,obs,.00125,cfg)


def test_lag_zero_has_identical_dense_motion_and_rng():
    state,obs,cfg,cue=fixture()
    ref=dense();wrapped=T.TimedGannet(dense(),bus_fixture(True,0.,cue))
    expected=ref(state,obs,.00125,cfg);actual=wrapped(state,obs,.00125,cfg)
    assert expected==actual
    ref.commit_step(expected);wrapped.commit_step(actual)
    assert ref.state_dict()==wrapped.state_dict()
    assert not wrapped.proposed['ever_deferred']


@pytest.mark.parametrize('lag',[1.,2.])
def test_positive_lag_defers_only_until_release_and_keeps_air_movement(lag):
    state,obs,cfg,cue=fixture()
    bus=bus_fixture(True,lag,cue);wrapped=T.TimedGannet(dense(),bus)
    before_ready=state.ready_at
    plan=wrapped(state,obs,.00125,cfg)
    assert not any(e.reason=='launch' for e in plan.transitions)
    assert plan.state.mode=='orient' and plan.state.ready_at==before_ready
    assert np.linalg.norm(np.asarray(plan.state.position)-state.position)==pytest.approx(cfg.air_speed*.00125)
    assert plan.pieces==P.advance(state,obs,.00125,replace(cfg,plunge_horizontal_radius=.01)).pieces
    assert bus.memories=={}  # proposal has not changed the committed bus
    wrapped.commit_step(plan)
    assert bus.staged['G0']['ever_deferred']
    memory=bus.staged['G0']
    later=replace(state,time=cue.time+lag)
    allow,memory,row=T.decide(later,replace(obs,time=later.time),[cue],memory,
        lag=lag,step_start=later.time)
    assert allow and memory['status']=='released'
    assert row['timing']['requested_release']==cue.time+lag


@pytest.mark.parametrize('change,reason',[
    ({'position':(0.,0.,-10.)},'peer_outside_12'),
    ({'target_position':(10.,0.,-2.)},'target_region_outside_4'),
    ({'time':-2.},'cue_expired'),
    ({'time':2.},'uncommitted_or_future_cue'),
    ({'published_at':2.},'uncommitted_or_future_cue')])
def test_ineligible_cue_does_not_delay_original_launch(change,reason):
    state,obs,_,cue=fixture();cue=replace(cue,**change)
    okay,detail=T.qualification(state,np.array(obs.positions[0]),cue,1.)
    assert not okay and detail['qualification']==reason
    allow,memory,row=T.decide(state,obs,[cue],None,lag=1.,step_start=1.)
    assert allow and memory is None


def test_bound_cue_loss_cancels_without_rebinding_or_new_attempt():
    state,obs,_,cue=fixture()
    allow,memory,_=T.decide(state,obs,[cue],None,lag=1.,step_start=1.)
    assert not allow
    moved=replace(state,time=1.2,position=(30.,0.,3.))
    newer=replace(cue,actor_id='D01',time=1.1,published_at=1.1,position=(30.,0.,-2.))
    allow,after,row=T.decide(moved,replace(obs,time=1.2),[cue,newer],memory,lag=1.,step_start=1.2)
    assert allow and after['status']=='cancelled'
    assert after['cue']['actor_id']=='D00' and row['reason']=='cancelled_peer_outside_12'
    assert after['requested_release']==2.


def test_latest_qualifying_cue_ties_are_stable_and_expiry_is_retained():
    state,obs,_,cue=fixture()
    earlier=replace(cue,actor_id='D01',time=.9)
    same=replace(cue,actor_id='D02')
    _,memory,_=T.decide(state,obs,[same,earlier,cue],None,lag=2.,step_start=1.)
    assert memory['cue']['actor_id']=='D00'
    late=replace(state,time=3.1)
    allow,after,row=T.decide(late,replace(obs,time=3.1),[],memory,lag=2.,step_start=3.1)
    assert allow and row['reason']=='cancelled_cue_expired'


def test_recovery_boundary_retry_commits_one_gate_and_one_target_draw():
    state,obs,cfg,cue=fixture()
    state=replace(state,mode='recovery',target_id=None,ready_at=1.0005)
    bus=bus_fixture(True,1.,cue);wrapped=T.TimedGannet(dense(),bus)
    before_rng=wrapped.state_dict()['target_rng_state']
    plan=wrapped(state,obs,.00125,cfg)
    assert all(piece.mode=='recovery' for piece in plan.pieces if piece.body.start<state.ready_at)
    assert plan.state.ready_at==state.ready_at
    assert not any(e.reason=='launch' for e in plan.transitions)
    assert wrapped.state_dict()['target_rng_state']==before_rng
    assert wrapped.proposed['first_eligible_at']==state.ready_at
    wrapped.commit_step(plan)
    assert wrapped.state_dict()['target_rng_state']!=before_rng
    assert all(item['time']>=state.ready_at for item in bus.histories['G0'])


def test_gate_state_commits_only_through_resolved_contact_cutoff():
    state,obs,cfg,cue=fixture()
    bus=bus_fixture(True,cue=cue)
    actual=SimpleNamespace(before=state,state=replace(state,time=1.01),contact_resolved=True,
        transitions=(P.Transition(1.005,'plunge','ascent','capture',1,0),))
    memory={'base':True}
    history=[(1.001,{'committed':True},{'time':1.001}),
             (1.007,{'phantom':True},{'time':1.007})]
    bus.stage_actor(actual,memory,history)
    assert bus.staged['G0']=={'committed':True}
    assert bus.histories['G0']==[{'time':1.001}]


def test_actual_dolphin_launch_is_published_only_after_step_commit():
    state,obs,cfg,_=fixture()
    fish=SimpleNamespace(time=1.,prey_ids=np.arange(4),positions=np.asarray(obs.positions),
        directions=np.zeros((4,3)))
    raw=SimpleNamespace(school=SimpleNamespace(state=lambda:fish),scenario=SimpleNamespace(speed=3.))
    bus=T.TimingBus(raw,enabled=True,lag=1.);bus.begin_step()
    dcfg=P.PredatorConfig(species='D')
    dolphin=P.initial_predator('D00',(0.,0.,-2.),(1.,0.,0.),dcfg,time=1.)
    fake=SimpleNamespace(before=dolphin,state=replace(dolphin,time=1.00125),pieces=(),
        transitions=(P.Transition(1.,'position','attack','launch',1,0),))
    result=SimpleNamespace(before=fish,after=SimpleNamespace(time=1.00125),predator_steps=(fake,))
    assert bus.cues==[]
    bus.finalize(result)
    assert len(bus.cues)==1 and bus.cues[0].published_at==1.00125
    okay,_=T.qualification(state,np.asarray(obs.positions[0]),bus.cues[0],1.)
    assert not okay
    assert bus.state_dict()['version']==T.VERSION


def test_disabled_integrator_hook_changes_no_global_function_binding():
    state,obs,cfg,_=fixture()
    before=(P.advance,P._resolve_mode,P._launch)
    T.advance_with_gate(state,obs,.00125,cfg,lambda *_:False)
    assert before==(P.advance,P._resolve_mode,P._launch)


def test_invalid_gate_and_lag_rejected():
    state,obs,cfg,cue=fixture()
    with pytest.raises(ValueError):T.TimingBus(None,lag=.5)
    with pytest.raises(ValueError):T.decide(replace(state,mode='recovery'),obs,[cue],None,lag=1.,step_start=1.)

