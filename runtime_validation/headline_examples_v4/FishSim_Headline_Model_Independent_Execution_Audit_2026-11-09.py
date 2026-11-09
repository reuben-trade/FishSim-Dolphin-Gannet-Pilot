"""Native-free review of new bounded model examples, never a feeding-effect analysis."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, gzip, hashlib, importlib.util, json, sys
import numpy as np

HISTORICAL='eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558'
REBUILT='cc21f00f355e1d25e8ecb48bd6aa50a7c9b63f909d921f4864a96e91d9ef2d4b'
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def records(p):
    with gzip.open(p,'rt') as f:return [json.loads(line) for line in f]
def sealed(p):
    s=read(p/'completion.json');assert s['status']=='complete'
    for name,digest in s['files'].items():assert sha(p/name)==digest,(p,name)
    return sha(p/'completion.json')
def arrays(a,b,prefix=False,exact=True):
    with np.load(a,allow_pickle=False) as x,np.load(b,allow_pickle=False) as y:
        assert set(x.files)==set(y.files)
        n=len(x['time']) if prefix else None
        diff={}
        for key in x.files:
            other=y[key][:n] if prefix and key not in ('prey_ids','actor_ids') else y[key]
            assert x[key].shape==other.shape and x[key].dtype==other.dtype,key
            if a.name=='initial_school.npz' and np.issubdtype(x[key].dtype,np.number):
                assert np.isfinite(x[key]).all() and np.isfinite(other).all(),(a,key,'nonfinite initial')
            if exact and a.name=='initial_school.npz':
                # Preserve the frozen actual-start comparator exactly; the
                # preceding finite check rules out NaNs in actual initial arrays.
                assert np.array_equal(x[key],other),(a,key)
            elif exact:
                # Byte equality retains NaN payload/sign/placement if any occur
                # in a trajectory; finite initial arrays remain strict as above.
                assert x[key].tobytes(order='C')==other.tobytes(order='C'),(a,key)
            elif np.issubdtype(x[key].dtype,np.number):
                finite=np.isfinite(x[key])&np.isfinite(other)
                with np.errstate(invalid='ignore',over='ignore'):
                    delta=np.abs(x[key][finite].astype(float)-other[finite].astype(float))
                valid=delta[np.isfinite(delta)]
                diff[key]=dict(maximum_finite_absolute_difference=float(np.max(valid,initial=0.)),
                    finite_pairs=int(np.count_nonzero(finite)),nonfinite_difference_results=int(np.count_nonzero(~np.isfinite(delta))),
                    differing_nan_patterns=int(np.count_nonzero(np.isnan(x[key])!=np.isnan(other))),
                    differing_positive_infinity_patterns=int(np.count_nonzero(np.isposinf(x[key])!=np.isposinf(other))),
                    differing_negative_infinity_patterns=int(np.count_nonzero(np.isneginf(x[key])!=np.isneginf(other))))
            elif np.issubdtype(x[key].dtype,np.bool_):diff[key+'_differing_entries']=int(np.count_nonzero(x[key]!=other))
            elif key in ('actor_ids','prey_ids'):assert np.array_equal(x[key],other)
            else:diff[key+'_differing_entries']=int(np.count_nonzero(x[key]!=other))
        return dict(fields=list(x.files),descriptive_differences=diff)
def audit(spec):
    package=Path(spec['package']).resolve()
    manifest=read(package/'INPUT_MANIFEST_2026-11-09_high_counts.json')['files']
    review=Path(spec['physical_review_source']).resolve()
    loader=importlib.util.spec_from_file_location('_headline_read_only_physical',review)
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    assert 'fish_sim.cmodel' not in sys.modules
    result=[];total=0
    for item in spec['examples']:
        folder=Path(item['case_folder']).resolve();name=folder.name
        summary=read(folder/'summary.json');config=read(folder/'config.json')
        artifact=item['actual_native_sha256'];assert artifact in (HISTORICAL,REBUILT)
        expected=round(item['duration_T']/.00125)
        assert summary['native_steps']==expected and summary['planned_duration']==item['duration_T']
        assert config['native_sha256']==artifact
        completion=sealed(folder)
        physical=module.audit_case(folder)
        assert physical['status']=='passed' and physical['native_steps']==expected
        # Golden starts come from the exact same frozen Case identity. Retained
        # D-only rows live in the discovery bank; high-count rows in the extension.
        study='pilot_regime_sweep_2026-11-09_v2' if '_G0_' in name else 'high_count_regime_extension_2026-11-09'
        gold=package/'data/research'/study/'results/full_36T_v1/cases'/name
        for filename in ('initial_engine.json','initial_shared.json','initial_school.npz','trajectories.npz','school_metrics.json','tie_stream_calls.json','events.jsonl.gz','monitor.jsonl.gz','opportunities.jsonl.gz','bird_events.jsonl.gz','responses.jsonl.gz'):
            relative=str((gold/filename).relative_to(package));assert sha(gold/filename)==manifest[relative]
        for filename in ('initial_engine.json','initial_shared.json'):assert read(folder/filename)==read(gold/filename),filename
        arrays(folder/'initial_school.npz',gold/'initial_school.npz',exact=True)
        prefix=arrays(folder/'trajectories.npz',gold/'trajectories.npz',prefix=True,exact=artifact==HISTORICAL)
        strict=artifact==HISTORICAL
        m=read(folder/'school_metrics.json')
        stream_matches={'school_metrics.json':m==read(gold/'school_metrics.json')[:len(m)]}
        for filename in ('events.jsonl.gz','monitor.jsonl.gz','opportunities.jsonl.gz','bird_events.jsonl.gz','responses.jsonl.gz'):
            a,b=records(folder/filename),records(gold/filename)
            if filename=='opportunities.jsonl.gz':
                # The frozen simple controller always keeps active_opportunity
                # None; no encounter-end diagnostic exclusion is permissible.
                assert not any(e.get('reason')=='encounter_end' for e in a)
                assert not any(e.get('reason')=='encounter_end' for e in b[:len(a)])
            stream_matches[filename]=a==b[:len(a)]
        a,b=read(folder/'tie_stream_calls.json'),read(gold/'tie_stream_calls.json')
        stream_matches['tie_stream_calls.json']=a==b[:len(a)]
        if strict:assert all(stream_matches.values()),stream_matches
        total+=expected
        result.append(dict(case=name,role=item.get('role','headline_core'),actual_native_sha256=artifact,duration_T=item['duration_T'],native_steps=expected,completion_sha256=completion,physical=physical,exact_archived_initial_states=True,exact_historical_trajectory_event_prefix_required=strict,trajectory_comparison=prefix,decoded_prefix_matches=stream_matches))
    assert len(result)==10 and total==20000
    assert sum(x['actual_native_sha256']==HISTORICAL for x in result)==4
    assert sum(x['actual_native_sha256']==REBUILT for x in result)==6
    core=[x for x in result if x['role']=='headline_core']
    front=[x for x in result if x['role']=='frontend_reuse_path']
    assert len(core)==8 and sum(x['native_steps'] for x in core)==19200
    assert len(front)==2 and sum(x['native_steps'] for x in front)==800
    assert all(x['actual_native_sha256']==REBUILT and x['duration_T']==.5 for x in front)
    assert 'fish_sim.cmodel' not in sys.modules
    return dict(status='passed',at=datetime.now(timezone.utc).isoformat(),native_steps_executed_by_review=0,examples=result,total_engineering_native_steps_reviewed=total,physical_review_source_sha256=sha(review),audit_source_sha256=sha(__file__),interpretation='Bounded engineering validation and exact historical-artifact prefix checks. The rebuilt artifact is separately declared; these short outputs do not estimate partner benefit or reproduce the full36T ensemble.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    assert not a.output.exists(),'Preserve earlier receipts'
    answer=audit(read(a.spec));a.output.write_text(json.dumps(answer,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(status=answer['status'],receipt=str(a.output),sha256=sha(a.output),native_steps_executed_by_review=0,total_engineering_native_steps_reviewed=answer['total_engineering_native_steps_reviewed'])))
