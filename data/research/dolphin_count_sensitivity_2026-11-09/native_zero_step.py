"""Fresh approved initialization with every model-step entrypoint prohibited."""
from dataclasses import asdict
from unittest.mock import patch
import gc
import numpy as np
from common import HERE,read,sha,write
from cases import SEEDS,all_cases,TASK_LEASE,ROOT
from reference import reference_path
from evidence import require_approval
from build import build,prepare_case
from preflight import state_digest
from physical_run import snapshot

def validate():
    require_approval('initialization')
    from research.prey_mediated.encounter import Encounter
    from research.prey_mediated.scenario import TravellingSchool
    from research.prey_mediated.surface_safe_school import SurfaceSafeSchool
    def prohibited(*args,**kwargs):raise RuntimeError('Stepping forbidden during actual initialization checks')
    states={};rows=[]
    with patch.object(Encounter,'step',prohibited),patch.object(TravellingSchool,'step',prohibited),patch.object(SurfaceSafeSchool,'step',prohibited):
        for case in all_cases():
            pure=prepare_case(case)
            engine,metadata=build(case.school_seed,case.policy,presence=case.presence,stage='initialization')
            actual=engine.school.state()
            if snapshot(engine)!=pure.receipt():raise RuntimeError('Actual private/actor/controller receipt differs from pure state')
            archived=reference_path(case.school_seed, case.herding_minimum, case.gannets, 12)
            with np.load(archived/'initial_school.npz',allow_pickle=False) as saved:
                if not all(np.array_equal(np.asarray(value),saved[name]) for name,value in asdict(actual).items()):
                    raise RuntimeError('Actual native fish initialization must replay archived arrays exactly, including normalized headings')
            if actual.step_index!=16000 or len(actual.prey_ids)!=160 or abs(actual.time-20)>1e-8:
                raise RuntimeError('Actual fish clock/count differs')
            states[case.name]=state_digest(actual)
            rows.append(dict(**case.asdict(),actual_initial_school_sha256=states[case.name]))
            del engine;gc.collect()
    for seed in SEEDS:
        if len({states[c.name] for c in all_cases() if c.school_seed==seed})!=1:
            raise RuntimeError('Count/H changes actual fish initialization')
    import fish_sim.cmodel as native
    if sha(native.__file__)!='eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558':
        raise RuntimeError('Pinned native binary differs')
    return dict(status='passed',actual_cases=len(all_cases()),native_constructions=len(all_cases()),native_steps=0,
        input_freeze_sha256=sha(HERE/'INPUT_FREEZE.json'),native_sha256=sha(native.__file__),
        step_guard='Encounter,TravellingSchool,SurfaceSafeSchool.step all replaced by exceptions',rows=rows)

if __name__=='__main__':
    path=HERE/'ACTUAL_ZERO_STEP.json'
    if path.exists():raise RuntimeError('Never overwrite actual initialization receipt')
    import fcntl
    with TASK_LEASE.open('a+') as task, (ROOT/'research/herding_gannet_paired_pilot_2026-11-08/native.lock').open('a+') as legacy:
        fcntl.flock(task.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(legacy.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=validate();write(path,result);print({k:v for k,v in result.items() if k!='rows'})
