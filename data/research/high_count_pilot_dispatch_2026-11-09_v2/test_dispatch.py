"""Focused scheduling/permission/compatibility tests; no model constructions."""
import fcntl,json,sys
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import dispatch as d

def test_exact_disjoint_subset_and_unchanged48_case_budget():
    pilot=d.phase_cases('pilot');rest=d.phase_cases('remainder')
    assert len(pilot)==12 and len(rest)==36
    assert {c.school_seed for c in pilot}=={39061001}
    assert {c.name for c in pilot}.isdisjoint({c.name for c in rest})
    assert {c.name for c in pilot+rest}=={c.name for c in d.identities.all_cases()}
    assert sum(round(36/d.identities.DT) for _ in pilot)==d.LIMITS['pilot']==345600
    assert sum(round(36/d.identities.DT) for _ in rest)==d.LIMITS['remainder']==1036800

def test_efficient_pilot_control_first_and_every_count_all_h():
    stages=d.stages('pilot')
    assert [len(c) for _,c in stages]==[3,9]
    assert d.MAX_WORKERS==8
    assert {c.gannets for c in stages[0][1]}=={9,12,18} and all(not c.dolphins for c in stages[0][1])
    mixed=stages[1][1]
    assert [c.gannets for c in mixed]==[9,9,9,12,12,12,18,18,18]
    for n in (9,12,18):
        assert {c.herding_minimum for c in mixed if c.gannets==n}=={1.,2.,3.}
    assert [len(c) for _,c in d.stages('remainder')]==[9,27]

@pytest.mark.parametrize('failure',[False,True])
def test_compatibility_flag_exists_only_inside_exclusive_lease_and_is_archived(tmp_path,monkeypatch,failure):
    here=tmp_path/'adapter';here.mkdir();frozen=tmp_path/'frozen';frozen.mkdir()
    lock=tmp_path/'research/herding_gannet_paired_pilot_2026-11-08/native.lock';lock.parent.mkdir(parents=True);lock.touch()
    phase=tmp_path/'pilot';phase.mkdir();template=here/'COMPATIBILITY_BRIDGE_TEMPLATE.json';template.write_text('{"bridge":true}\n')
    monkeypatch.setattr(d,'HERE',here);monkeypatch.setattr(d,'ROOT',tmp_path);monkeypatch.setattr(d,'FROZEN',frozen)
    monkeypatch.setattr(d,'phase_dir',lambda p:phase)
    monkeypatch.setattr(d.scientific_evidence,'require_approval',lambda stage:None)
    def run():
        with d.protected_compatibility_bridge('pilot'):
            assert (frozen/'FULL_RUN_APPROVED.json').read_bytes()==template.read_bytes()
            with lock.open('a') as other:
                with pytest.raises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if failure:raise ValueError('Deliberate pure bridge cleanup probe')
    if failure:
        with pytest.raises(ValueError):run()
    else:run()
    assert not (frozen/'FULL_RUN_APPROVED.json').exists()
    assert (phase/'activated_frozen_runner_bridge.json').read_bytes()==template.read_bytes()

def test_phase_permission_has_exact_step_and_source_binding(monkeypatch,tmp_path):
    monkeypatch.setattr(d,'HERE',tmp_path);monkeypatch.setattr(d,'verify_freeze',lambda:None)
    for name in ('DISPATCH_FREEZE.json','amendment.json','COMPATIBILITY_BRIDGE_TEMPLATE.json'):(tmp_path/name).write_text('{}\n')
    record=dict(approved=True,phase='pilot',dispatch_freeze_sha256=d.sha(tmp_path/'DISPATCH_FREEZE.json'),
        amendment_sha256=d.sha(tmp_path/'amendment.json'),maximum_native_steps=345600,
        bridge_template_sha256=d.sha(tmp_path/'COMPATIBILITY_BRIDGE_TEMPLATE.json'))
    d.write(tmp_path/'PILOT_RUN_APPROVED.json',record)
    assert d.require_phase('pilot')['maximum_native_steps']==345600
    record['maximum_native_steps']=1382400;d.write(tmp_path/'PILOT_RUN_APPROVED.json',record)
    with pytest.raises(RuntimeError):d.require_phase('pilot')

def test_remainder_refuses_pilot_without_complete_review(monkeypatch,tmp_path):
    monkeypatch.setattr(d,'HERE',tmp_path);monkeypatch.setattr(d,'verify_freeze',lambda:None)
    for name in ('DISPATCH_FREEZE.json','amendment.json','COMPATIBILITY_BRIDGE_TEMPLATE.json'):(tmp_path/name).write_text('{}\n')
    pilot=tmp_path/'pilot';pilot.mkdir();d.write(pilot/'pilot_review.json',dict(status='partial',cases=11))
    monkeypatch.setattr(d,'phase_dir',lambda phase:pilot)
    record=dict(approved=True,phase='remainder',dispatch_freeze_sha256=d.sha(tmp_path/'DISPATCH_FREEZE.json'),
        amendment_sha256=d.sha(tmp_path/'amendment.json'),maximum_native_steps=1036800,
        bridge_template_sha256=d.sha(tmp_path/'COMPATIBILITY_BRIDGE_TEMPLATE.json'),pilot_review_sha256=d.sha(pilot/'pilot_review.json'))
    d.write(tmp_path/'REMAINDER_RUN_APPROVED.json',record)
    with pytest.raises(RuntimeError,match='Completed pilot audit'):d.require_phase('remainder')

def test_adapter_does_not_assign_or_monkeypatch_scientific_globals():
    import ast
    tree=ast.parse((HERE/'dispatch.py').read_text())
    for n in ast.walk(tree):
        targets=n.targets if isinstance(n,ast.Assign) else [n.target] if isinstance(n,(ast.AnnAssign,ast.AugAssign)) else []
        assert not any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name)
            and t.value.id in ('scientific_runner','identities','scientific_evidence') for t in targets)

def test_resource_observer_is_read_only_and_best_effort():
    import os
    current=d.process_resources(os.getpid())
    assert current['pid']==os.getpid() and current['VmRSS']>0 and current['Threads']>=1
    assert current['user_CPU_s']>=0 and current['system_CPU_s']>=0 and d.available_memory()>0
    assert d.process_resources(None)==dict(pid=None)
