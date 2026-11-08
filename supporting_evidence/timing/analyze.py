"""Read-only comparisons of timing feasibility outputs and frozen baselines."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'research/exposed_replication_2026-11-08'


def read(path):return json.loads(Path(path).read_text())
def records(path):
    with gzip.open(path,'rt') as handle:return [json.loads(line) for line in handle]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sealed(case):
    receipt=read(case/'completion.json')
    assert receipt['status']=='complete'
    for name,digest in receipt['files'].items():assert sha(case/name)==digest,(case.name,name)
    for path,digest in read(case/'source_manifest.json').items():assert sha(path)==digest,path
    assert read(case/'audit.json')['status']=='passed'


def exact_disabled(case,reference=None):
    """Exact all-frame/state/event/stream parity for equal-horizon native runs."""
    case=Path(case)
    reference=Path(reference or PRIOR/'results/integration_smoke_v1/cases/s39063501_exposed_DG_c61001')
    sealed(case);sealed(reference)
    for name in ('initial_engine.json','final_engine.json','tie_stream_calls.json'):
        assert read(case/name)==read(reference/name),name
    for name in ('initial_school.npz','final_school.npz','trajectories.npz'):
        with np.load(case/name) as a,np.load(reference/name) as b:
            assert set(a.files)==set(b.files),name
            for key in a.files:
                assert np.array_equal(a[key],b[key],equal_nan=True) if a[key].dtype.kind in 'fc' else np.array_equal(a[key],b[key]),(name,key)
    for name in ('events.jsonl.gz','opportunities.jsonl.gz','bird_events.jsonl.gz'):
        assert records(case/name)==records(reference/name),name
    return dict(status='passed',reference=str(reference),scope='All retained trajectories, initial/final school and engine, actual events, private capture/target/tie streams; identical4T horizon')


def enabled_feasibility(case,reference=None):
    """Audit actual imposed delay; descriptive fixed-prefix feeding comparison."""
    case=Path(case)
    reference=Path(reference or PRIOR/'results/full_36T_v1/cases/s39063501_exposed_DG_c61001')
    sealed(case);sealed(reference)
    summary=read(case/'summary.json');duration=summary['planned_duration']
    initial=read(case/'initial_engine.json');baseline_initial=read(reference/'initial_engine.json')
    assert initial==baseline_initial
    final=read(case/'final_engine.json')
    origin=initial['actors'][0]['time']
    rows=records(case/'timing_events.jsonl.gz')
    ordinary=records(case/'events.jsonl.gz')
    gates=[r for r in rows if r['kind']=='timing_gate']
    assert all(r['original_legal'] and r['original_mode']=='orient' and r['time']>=r['ready_at']-1e-10 for r in gates)
    for r in gates:
        if not r['allow']:
            t=r['timing'];cue=t['cue']
            assert r['qualification']=='qualified'
            assert r['peer_distance_3d']<=12. and r['target_region_distance_3d']<=4.
            assert -1e-10<=r['cue_age']<=2.+1e-10
            assert cue['published_at']<=r['time']+1e-10
            assert t['requested_release']==cue['time']+1.
            assert r['time']<t['requested_release']+1e-10
    launch_rows=[r for r in rows if r['kind']=='actual_gannet_launch']
    actual={(r['actor_id'],r['bout_id'],r['time']) for r in ordinary
            if r['kind']=='transition' and r['reason']=='launch' and r['actor_id'].startswith('G')}
    assert {(r['actor_id'],r['bout_id'],r['time']) for r in launch_rows}==actual
    delayed=[r for r in launch_rows if r['timing'] and r['timing']['ever_deferred']]
    for r in delayed:
        assert r['time']>r['timing']['first_eligible_at']
        if r['timing']['status']=='released':
            assert r['time']>=r['timing']['requested_release']-1e-10
    target_replay={}
    for who in (w for w in initial['controllers'] if w.startswith('G')):
        rng=np.random.default_rng(0)
        rng.bit_generator.state=deepcopy(initial['controllers'][who]['target_rng_state'])
        count=0
        for event in ordinary:
            if event.get('reason')!='gannet_global_dense_target_selected' or event['actor_id']!=who:continue
            detail=event['targeting_diagnostics'];p=detail['selection_probabilities']
            if p:
                weights=np.asarray(detail['eligible_patch_accessible_counts'],float)
                assert np.allclose(weights/weights.sum(),p,rtol=0,atol=1e-15)
                assert int(rng.choice(len(p),p=p))==detail['selected_patch']
                count+=1
            else:assert detail['reason']=='fallback_densest_accessible_neighbourhood'
        assert rng.bit_generator.state==final['controllers'][who]['target_rng_state']
        target_replay[who]=dict(status='passed',weighted_draws=count)
    cycle_launches=[e for e in records(case/'opportunities.jsonl.gz') if e['kind']=='cycle_launch']
    assert all(e['pressure_elapsed']>=2.-1e-10 for e in cycle_launches)
    base_events=[r for r in records(reference/'events.jsonl.gz')
                 if (r['time'] if 'time' in r else r['contact']['time'])<=origin+duration+1e-8]
    def food(events):return dict(Counter(r['actor_id'][0] for r in events
        if r['kind']=='oral' and r['status']=='captured' and r['closes_bout']))
    return dict(status='passed',actual_delayed_plunges=len(delayed),delayed_launches=delayed,
        timing_changed=bool(delayed),native_horizon_T=duration,
        gate_calls=len(gates),gate_reasons=dict(Counter(r['reason'] for r in gates)),
        unchanged_dense_target_rng_replay=target_replay,dolphin_2T_cycle_launches=len(cycle_launches),
        captures=food(ordinary),baseline_same_elapsed_prefix_captures=food(base_events),
        baseline_reference=str(reference),baseline_scope=f'Fixed first{duration:g}T of sealed36T encounter; no terminal-state claim for this prefix',
        interpretation='Engineering timing feasibility only. Changes in realised effort and waiting are part of policy effect; no mutual-benefit or timing-efficiency claim.')
