"""Additional read-only exact event-prefix and realized-effort review."""
from pathlib import Path
import importlib.util,json,math
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_timing_prefix_analysis',HERE/'analyze.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
case=HERE/'results/lag1_36T_demonstration_v1/cases/s39063501_lag1_DG_c61002'
base=A.PRIOR/'results/full_36T_v1/cases/s39063501_exposed_DG_c61002'
review=A.read(case.parent.parent/'demonstration_review.json')
cut=review['independent_review']['first_denied_gate_time']
if cut is None:cut=float('inf')
origin=A.read(case/'initial_engine.json')['actors'][0]['time']
step_cut=origin+math.floor((cut-origin)/.00125)*.00125 if cut!=float('inf') else cut
checks={}
for name in ('events.jsonl.gz','opportunities.jsonl.gz','bird_events.jsonl.gz'):
 def before(path):
  rows=A.records(path)
  return [r for r in rows if (r['time'] if 'time' in r else r['contact']['time'])<step_cut-1e-10]
 left,right=before(case/name),before(base/name)
 assert left==right,name
 checks[name]=dict(status='exact_equal_JSON_values',retained_records=len(left))
summary,reference=A.read(case/'summary.json'),A.read(base/'summary.json')
out=dict(status='passed',exact_event_prefix=checks,prefix_cutoff='Fully committed steps strictly before intervention step; target-selection diagnostics emitted after that step contain its resulting mode even when timestamped at its start.',intervention_step_start=None if cut==float('inf') else step_cut,first_intervention_time=None if cut==float('inf') else cut,first_intervention_elapsed=None if cut==float('inf') else cut-A.read(case/'initial_engine.json')['actors'][0]['time'],whole_horizon_comparison=dict(enabled=summary['species'],baseline=reference['species']),interpretation='One opportunity-selected post-hoc engineering demonstration. Whole-horizon captures include altered realised effort; no independent timing-benefit,optimal-lag or efficiency claim.')
(case.parent.parent/'event_prefix_and_effort_review.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
