"""Native-free reader for the COMPLETE declared regime map; no external writes.

This private scaffold refuses incomplete data. It independently reconstructs
raw food/contact/launch counts, the paired map and its frozen bootstrap instead
of importing the simulation or trusting a selected favourable table row.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

SEEDS = (39061001, 39061002, 39063501, 39063502)
HS = (1., 2., 3.)
GS = (0, 1, 3, 6)
DT = .00125
DURATION = 36.


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identities():
    out = []
    for seed in SEEDS:
        for h in HS:
            for g in GS:
                policy = f'H{h:g}_G{g}'
                presence = 'DG' if g else 'D'
                out.append(dict(school_seed=seed, herding_minimum_T=h, gannets=g,
                    dolphins=12, policy=policy, presence=presence, capture_seed=61001,
                    dt=DT, duration_T=DURATION, anchor_replay=h == 2 and g in (0, 3),
                    case_name=f's{seed}_{policy}_{presence}_c61001'))
        for g in GS[1:]:
            policy = f'Gonly{g}'
            out.append(dict(school_seed=seed, herding_minimum_T=None, gannets=g,
                dolphins=0, policy=policy, presence='G', capture_seed=61001,
                dt=DT, duration_T=DURATION, anchor_replay=False,
                case_name=f's{seed}_{policy}_G_c61001'))
    return out


def readiness(study):
    """Check only global completion, before reading any partial outcome table."""
    base = Path(study)/'results/full_36T_v1'
    names = ('status.json', 'anchor_replay.json', 'physical_review.json',
             'analysis_final/analysis_audit.json')
    missing = [name for name in names if not (base/name).is_file()]
    if missing:
        return dict(status='not_ready', reason='Complete-map receipts unavailable',
                    missing=missing, native_steps=0, publication_performed=False)
    status, anchor, physical, analysis = [read(base/name) for name in names]
    passed = (status.get('status') == 'complete' and status.get('complete') == 60
        and anchor.get('status') == 'passed' and anchor.get('anchor_cells') == 8
        and physical.get('status') == 'passed' and len(physical.get('cases', [])) == 60
        and all(r.get('status') == 'passed' for r in physical['cases'])
        and analysis.get('status') == 'passed' and analysis.get('cells') == 60
        and analysis.get('independent_schools') == 4)
    return dict(status='ready' if passed else 'not_ready',
                reason='All declared completion receipts pass' if passed else 'Complete-map gate has not passed',
                native_steps=0, publication_performed=False)


def verify_sources(study, *, closure=None, bundle_root=None):
    study = Path(study)
    frozen = read(study/'frozen_sources.json')
    if closure is None:
        mapping = {name: Path(name) for name in frozen['source_sha256']}
    else:
        records = read(closure)
        mapping = {r['original_path']: Path(bundle_root)/r['bundled_path'] for r in records}
        if set(mapping) != set(frozen['source_sha256']):
            raise ValueError('Incomplete or extra source-closure identities')
        if {r['original_path']: r['sha256'] for r in records} != frozen['source_sha256']:
            raise ValueError('Source-closure digests differ from frozen declaration')
    for name, digest in frozen['source_sha256'].items():
        if sha(mapping[name]) != digest:
            raise ValueError('Frozen source/input changed: '+name)
    for file, key in [('preflight.json', 'preflight_sha256'),
                      ('native_zero_step.json', 'native_zero_step_sha256')]:
        if sha(study/file) != frozen[key]:
            raise ValueError('Frozen preparation receipt changed: '+file)
    pre = read(study/'preflight.json')
    zero = read(study/'native_zero_step.json')
    if pre.get('status') != 'passed' or pre.get('pure_cases') != 60 or pre.get('native_constructions') != 0:
        raise ValueError('Pure preparation gate failed')
    if (zero.get('status') != 'passed' or zero.get('actual_cases') != 60
            or zero.get('native_steps') != 0 or zero.get('actual_initial_anchor_matches') != 8):
        raise ValueError('Actual zero-step matching gate failed')
    protocol_digest, frozen_digest = sha(study/'protocol.json'), sha(study/'frozen_sources.json')
    for name, stage in [('SMOKE_RUN_APPROVED.json', 'smoke'), ('FULL_RUN_APPROVED.json', 'full')]:
        approval = read(study/name)
        if (approval.get('approved') is not True or approval.get('stage') != stage
                or approval.get('protocol_sha256') != protocol_digest
                or approval.get('frozen_sources_sha256') != frozen_digest):
            raise ValueError('Execution approval source binding differs')
    return frozen


def verify_seal(folder, expected, frozen):
    seal = read(folder/'completion.json')
    if seal.get('status') != 'complete':
        raise ValueError('Incomplete case')
    for name, digest in seal['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Seal path leaves case directory')
        if sha(folder/name) != digest:
            raise ValueError('Case sealed file changed: '+str(folder/name))
    config = read(folder/'config.json')
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError('Case/config identity differs: '+key)
    if (config['minimum_herding_duration'] != expected['herding_minimum_T']
            or config['dolphin_target_policy'] != 'exposed'
            or config['capture_probability'] != .7 or config['duration'] != DURATION
            or config['counts'] != dict(fish=160, D=expected['dolphins'], G=expected['gannets'])):
        raise ValueError('Shared-model condition differs')
    if read(folder/'source_manifest.json') != frozen['source_sha256']:
        raise ValueError('Case source freeze differs')
    summary = read(folder/'summary.json')
    audit = read(folder/'audit.json')
    if summary.get('status') != 'complete' or audit.get('status') != 'passed' or audit.get('errors'):
        raise ValueError('Physical/accounting case audit failed')
    actual = summary['actual_duration']
    depleted = summary.get('native_absorbing_termination') is True
    if (summary['dt'] != DT or summary['planned_duration'] != DURATION
            or summary['native_steps'] != round(actual/DT) or not 0 < actual <= DURATION+1e-7
            or (not depleted and abs(actual-DURATION) > 1e-7)
            or (depleted and summary['final_count'] != 0)):
        raise ValueError('Incomplete nominal horizon or incorrect depletion semantics')
    return summary


def raw_row(folder, expected, frozen):
    summary = verify_seal(folder, expected, frozen)
    with gzip.open(folder/'events.jsonl.gz', 'rt') as handle:
        events = [json.loads(line) for line in handle]
    if any(e.get('elapsed', 0) > DURATION+1e-7 for e in events):
        raise ValueError('Post-horizon event')
    row = dict(expected, remaining_fish=summary['final_count'], initial_fish=summary['initial_count'],
        native_steps=summary['native_steps'], water_entries=summary['water_entries'],
        completion_sha256=sha(folder/'completion.json'))
    prey = []
    for species, count in [('D', expected['dolphins']), ('G', expected['gannets'])]:
        contacts = [e for e in events if e['kind'] == 'oral' and e['actor_id'].startswith(species) and e['closes_bout']]
        catches = [e for e in contacts if e['status'] == 'captured']
        launches = [e for e in events if e['kind'] == 'transition' and e['actor_id'].startswith(species) and e['reason'] == 'launch']
        totals = summary['species'][species]
        if (len(catches), len(contacts), len(launches), count) != (
                totals['captures'], totals['contacts'], totals['launches'], totals['count']):
            raise ValueError('Raw event and species account differ')
        prey.extend(e['prey_id'] for e in catches)
        row.update({species+'_captures':len(catches), species+'_contacts':len(contacts),
            species+'_launches':len(launches), species+'_rate':len(catches)/(count*DURATION) if count else None,
            species+'_captures_per_contact':len(catches)/len(contacts) if contacts else None})
    if len(prey) != len(set(prey)) or len(prey) != row['initial_fish']-row['remaining_fish']:
        raise ValueError('Unique prey removal conservation failed')
    return row


def reconstruct_map(rows, plan):
    """One common four-school bootstrap including selection within every draw."""
    lookup = {(r['school_seed'],r['herding_minimum_T'],r['gannets'],bool(r['dolphins'])):r for r in rows}
    if len(lookup) != 60 or len(rows) != 60:
        raise ValueError('Complete unique 60-cell map required')
    settings = [(h,g) for h in HS for g in GS[1:]]
    control = np.array([[lookup[s,h,0,True]['D_rate'] for h in HS] for s in SEEDS])
    best_index = int(np.argmax(control.mean(axis=0)))
    control_totals = [sum(lookup[s,h,0,True]['D_captures'] for s in SEEDS) for h in HS]
    if best_index != int(np.argmax(control_totals)):
        raise ValueError('Best-tested H must use exact capture-total ties, choosing smaller H')
    best_h = HS[best_index]
    vectors, mixed, pairs = [], [], []
    for seed in SEEDS:
        vector, returns = [], []
        for h,g in settings:
            d0, dg, g0 = lookup[seed,h,0,True], lookup[seed,h,g,True], lookup[seed,None,g,False]
            d, b = dg['D_rate']-d0['D_rate'], dg['G_rate']-g0['G_rate']
            vector.append([d,b]); returns.append(dg['D_rate'])
            pairs.append(dict(school_seed=seed,herding_minimum_T=h,gannets=g,
                D_rate_alone=d0['D_rate'],D_rate_mixed=dg['D_rate'],D_rate_change=d,
                G_rate_alone=g0['G_rate'],G_rate_mixed=dg['G_rate'],G_rate_change=b,
                D_capture_change=dg['D_captures']-d0['D_captures'],
                G_capture_change=dg['G_captures']-g0['G_captures'],best_tested_Donly_H=best_h,
                D_rate_change_vs_best_tested_Donly=dg['D_rate']-lookup[seed,best_h,0,True]['D_rate'],
                both_rate_changes_positive=d>0 and b>0))
        vectors.append(vector);mixed.append(returns)
    values, mixed = np.array(vectors), np.array(mixed)
    boot = plan['bootstrap']
    if (boot['draws'],boot['seed'],boot['quantiles']) != (10000,88493009,[.025,.975]):
        raise ValueError('Declared bootstrap changed')
    indices = np.random.default_rng(boot['seed']).integers(0,4,size=(boot['draws'],4))
    bounds = np.quantile(values[indices].mean(axis=1),boot['quantiles'],axis=0)
    means = values.mean(axis=0)
    best_bounds = np.quantile(mixed[indices].mean(axis=1)-control[indices].mean(axis=1).max(axis=1)[:,None],
                              boot['quantiles'],axis=0)
    summary = []
    for j,(h,g) in enumerate(settings):
        r = dict(herding_minimum_T=h,gannets=g,independent_schools=4)
        for k,species in enumerate(('D','G')):
            r.update({species+'_mean_rate_change':float(means[j,k]),
                species+'_pointwise95_low':float(bounds[0,j,k]),species+'_pointwise95_high':float(bounds[1,j,k]),
                species+'_positive_schools':int((values[:,j,k]>0).sum()),
                species+'_zero_schools':int((values[:,j,k]==0).sum()),
                species+'_negative_schools':int((values[:,j,k]<0).sum())})
        r.update(both_positive_schools=int(((values[:,j,0]>0)&(values[:,j,1]>0)).sum()),
            best_tested_Donly_H=best_h,best_tested_Donly_mean_rate=float(control[:,best_index].mean()),
            D_mixed_mean_rate=float(mixed[:,j].mean()),
            D_mean_rate_change_vs_best_tested_Donly=float(mixed[:,j].mean()-control[:,best_index].mean()),
            D_vs_best_tested_pointwise95_low=float(best_bounds[0,j]),D_vs_best_tested_pointwise95_high=float(best_bounds[1,j]))
        summary.append(r)
    return pairs,summary


def compare_csv(path, rows, key):
    with open(path,newline='') as handle:
        stored = list(csv.DictReader(handle))
    actual = {tuple(r[k] for k in key):r for r in rows}
    if len(stored) != len(rows):
        raise ValueError('Table row count differs: '+str(path))
    seen = set()
    for old in stored:
        # Match identities after string normalisation; CSV retains None as ''.
        identity = tuple(old[k] for k in key)
        matches = [r for k,r in actual.items() if tuple('' if v is None else str(v) for v in k)==identity]
        if len(matches) != 1 or identity in seen:
            raise ValueError('Table identities differ: '+str(path))
        seen.add(identity);new = matches[0]
        for name,value in new.items():
            if value is None:
                equal = old[name] == ''
            elif isinstance(value,bool):
                equal = old[name] == str(value)
            elif isinstance(value,(float,int)):
                equal = np.isclose(float(old[name]),value,rtol=1e-12,atol=1e-14)
            else:
                equal = old[name] == value
            if not equal:
                raise ValueError(f'Table value differs: {path.name} {identity} {name}')


def diagnostic_rows(study):
    """Prespecified descriptive time means, retaining all H/G settings."""
    rows = []
    for case in identities():
        folder = Path(study)/'results/full_36T_v1/cases'/case['case_name']
        state = [r for r in read(folder/'school_metrics.json') if r['n_live'] > 0]
        if len(state)<2:
            raise ValueError('Insufficient observed nonempty school-state frames')
        times = np.array([r['elapsed'] for r in state])
        if not (np.diff(times)>0).all() or times[-1]>DURATION+1e-7:
            raise ValueError('School-state cadence differs')
        row = dict(case_name=case['case_name'],school_seed=case['school_seed'],
            herding_minimum_T=case['herding_minimum_T'],gannets=case['gannets'],presence=case['presence'],
            state_duration_T=float(times[-1]-times[0]),state_frames=len(state),
            state_condition='Observed live-school frames; survivor-conditional, not causal mediation')
        for field in ('r90','outward_fraction','largest_component_fraction','mean_depth'):
            v = np.array([r[field] for r in state],float)
            if not np.isfinite(v).all():
                raise ValueError('Nonfinite school-state diagnostic')
            row['time_mean_'+field] = float(np.sum((v[1:]+v[:-1])/2*np.diff(times))/(times[-1]-times[0]))
        rows.append(row)
    return rows


def verify_complete(study, *, closure=None, bundle_root=None):
    gate = readiness(study)
    if gate['status'] != 'ready':
        raise ValueError(gate['reason'])
    study = Path(study);base = study/'results/full_36T_v1'
    frozen = verify_sources(study,closure=closure,bundle_root=bundle_root)
    expected = identities();names = {r['case_name'] for r in expected}
    if {p.name for p in (base/'cases').iterdir() if p.is_dir()} != names:
        raise ValueError('Declared full case matrix differs')
    rows = [raw_row(base/'cases'/r['case_name'],r,frozen) for r in expected]
    seals = {r['case_name']:r['completion_sha256'] for r in rows}
    physical = read(base/'physical_review.json')
    if {r['case']:r['completion_sha256'] for r in physical['cases']} != seals:
        raise ValueError('Physical review does not bind all current seals')
    if sha(study/'review_actual.py') != physical['review_source_sha256']:
        raise ValueError('Physical review source differs')
    anchor = read(base/'anchor_replay.json')
    if (anchor.get('protocol_sha256') != sha(study/'protocol.json')
            or anchor.get('frozen_sources_sha256') != sha(study/'frozen_sources.json')
            or anchor.get('replay_is_not_new_independent_evidence') is not True):
        raise ValueError('Exact-anchor source binding differs')
    checks = anchor.get('checks',[])
    if {r['case']['case_name'] for r in checks} != {r['case_name'] for r in expected if r['anchor_replay']}:
        raise ValueError('Require all eight exact historical anchors')
    for row in checks:
        if (row['status'] != 'passed' or not all(row['checks'].values())
                or row['candidate_completion_sha256'] != seals[row['case']['case_name']]
                or row['prior_completion_sha256'] not in frozen['source_sha256'].values()):
            raise ValueError('Anchor replay receipt differs')
    audit = read(base/'analysis_final/analysis_audit.json')
    if audit['case_completion_sha256'] != seals:
        raise ValueError('Analysis does not bind current full case matrix')
    for name,digest in audit['files'].items():
        if sha(base/'analysis_final'/name) != digest:
            raise ValueError('Stored analysis output changed')
    pairs,summary = reconstruct_map(rows,read(study/'analysis_plan.json'))
    compare_csv(base/'analysis_final/case_outcomes.csv',rows,('case_name',))
    compare_csv(base/'analysis_final/paired_school_changes.csv',pairs,('school_seed','herding_minimum_T','gannets'))
    compare_csv(base/'analysis_final/regime_summary.csv',summary,('herding_minimum_T','gannets'))
    best = read(base/'analysis_final/best_tested_Donly.json')
    if best['selected_H'] != summary[0]['best_tested_Donly_H']:
        raise ValueError('Frozen best-tested H differs')
    diagnostics = diagnostic_rows(study)
    if 'fish_sim.cmodel' in sys.modules:
        raise ValueError('Native module imported during evidence review')
    return dict(status='passed',cells=60,paired_rows=len(pairs),map_cells=len(summary),
        diagnostic_rows=len(diagnostics),independent_schools=4,anchor_replay_executions=8,
        additional_cells=52,source_files=len(frozen['source_sha256']),
        all_raw_accounts_and_bootstrap_tables_reconstructed=True,
        native_steps=0,publication_performed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--readiness-only',action='store_true')
    parser.add_argument('--closure',type=Path)
    parser.add_argument('--bundle-root',type=Path)
    args = parser.parse_args()
    gate = readiness(args.study)
    if args.readiness_only or gate['status'] != 'ready':
        print(json.dumps(gate,indent=2));return 0 if gate['status']=='ready' else 2
    print(json.dumps(verify_complete(args.study,closure=args.closure,bundle_root=args.bundle_root),indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
