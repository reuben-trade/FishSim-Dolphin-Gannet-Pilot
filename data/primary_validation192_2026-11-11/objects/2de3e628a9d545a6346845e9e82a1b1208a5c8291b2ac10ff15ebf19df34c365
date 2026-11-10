"""Additive V2 recording; adaptive choices never replace physical phases."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import sys
import numpy as np

OLD=Path(__file__).resolve().parents[1]/'overnight_workload_2026-11-08'
sys.path.insert(0,str(OLD))
from workload_common import clean,behaviour_category,audit_summary

CHOICE_PREFIXES=('adaptive_v1_','adaptive_v2_')

def window_time(window,low,high):
    return 0. if window is None else max(0.,min(high,window.close)-max(low,window.open))

def overlap_time(first,second,low,high):
    if first is None or second is None:return 0.
    return max(0.,min(high,first.close,second.close)-max(low,first.open,second.open))

class AccountingV2:
    def __init__(self,engine):
        self.per={a.state.actor_id:dict(time=Counter(),distance=Counter(),physical_mode_time=Counter(),
            phases=Counter(),exposure_time=Counter(),captures=0,virtual_successes=0,contacts=0,launches=0,reasons=Counter()) for a in engine.actors}
        self.events=[]

    def add(self,engine,result,phases_before):
        records=[]
        for step in result.predator_steps:
            who=step.before.actor_id;row=self.per[who];planner=engine.actor_planners.get(who)
            diagnostic={} if planner is None else (planner.last_diagnostics or {})
            changes=sorted(diagnostic.get('phase_events',[]),key=lambda e:e['time'])
            physical=[e for e in changes if not e.get('reason','').startswith(CHOICE_PREFIXES)]
            phase=phases_before.get(who,'not_dolphin')
            intent=diagnostic.get('adaptive_committed_mode',diagnostic.get('adaptive_mode'))
            for piece in step.pieces:
                low,high=piece.body.start,piece.body.end;assert high>=low
                water=window_time(getattr(piece,'water_window',None),low,high)
                bite=window_time(getattr(piece,'bite_window',None),low,high)
                wet_bite=overlap_time(getattr(piece,'water_window',None),getattr(piece,'bite_window',None),low,high)
                row['exposure_time']['water']+=water;row['exposure_time']['air']+=high-low-water
                row['exposure_time']['bite_window']+=bite;row['exposure_time']['underwater_bite_window']+=wet_bite
                row['exposure_time']['water_'+piece.mode]+=water;row['exposure_time']['air_'+piece.mode]+=high-low-water
                row['exposure_time']['underwater_bite_'+piece.mode]+=wet_bite
                cuts=sorted({low,high,*[e['time'] for e in physical if low<e['time']<high]})
                distance=float(np.linalg.norm(np.asarray(piece.body.after)-piece.body.before))
                for left,right in zip(cuts,cuts[1:]):
                    actual_phase=phase
                    for event in physical:
                        if event['time']<=left+1e-12:actual_phase=event['after']
                    dt=right-left;category=behaviour_category(actual_phase,piece.mode,intent)
                    row['time'][category]+=dt;row['distance'][category]+=distance*dt/(high-low)
                    row['physical_mode_time'][piece.mode]+=dt;row['phases'][actual_phase]+=dt
            for event in step.transitions:
                row['reasons'][event.reason]+=1;row['launches']+=event.reason=='launch'
                if event.reason!='habitat_boundary_hold':records.append(dict(kind='transition',actor_id=who,**asdict(event)))
            for event in changes:
                choice=event.get('reason','').startswith(CHOICE_PREFIXES)
                record=dict(kind='choice' if choice else 'phase',actor_id=who,**event)
                if choice:record.update(adaptive_metrics=diagnostic.get('adaptive_metrics'),
                    adaptive_stable_since=diagnostic.get('adaptive_stable_since'),adaptive_mode=intent,
                    adaptive_reason=diagnostic.get('adaptive_reason'))
                records.append(record)
        for outcome in result.contacts:
            if outcome.status=='bout_closed':continue
            proposal=outcome.proposal;row=self.per[proposal.actor_id]
            if outcome.closes_bout:
                row['contacts']+=1
                if outcome.status=='captured':row['captures' if engine.remove_prey else 'virtual_successes']+=1
            records.append(dict(kind='oral',actor_id=proposal.actor_id,bout_id=proposal.bout_id,prey_id=proposal.prey_id,
                status=outcome.status,closes_bout=outcome.closes_bout,draw=outcome.draw,contact=asdict(proposal.contact)))
        self.events.extend(records);return records

    def snapshot(self):return clean(self.per)
