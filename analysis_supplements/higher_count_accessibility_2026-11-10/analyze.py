"""Descriptive access diagnostics from the sealed through-36 discovery bank.

No simulation, controller decisions, random draws or new bootstrap samples.
The old48-encounter departure outputs remain immutable. This separate analysis
extends their deterministic new-target geometry to all128 bird-bearing cases.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
UPPER = Path('/tmp/FishSim_Upper_Count_Extension_2026-11-09/full_36T_v1')
HIGH = Path('/tmp/FishSim_High_Count_Extension_2026-11-09/full_36T_v1')
OLD = REPO/'research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1'
LEGACY = REPO/'research/gannet_departure_timecourse_2026-11-09'
OUT = HERE/'outputs'
SEEDS = (39061001, 39061002, 39063501, 39063502)
COUNTS = (1, 3, 6, 9, 12, 18, 24, 36)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def table(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_geometry():
    path = LEGACY/'diagnostics.py'
    spec = importlib.util.spec_from_file_location('_saved_gannet_geometry_only', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def location(row):
    base = OLD if int(row['gannets']) <= 6 else HIGH if int(row['gannets']) <= 18 else UPPER
    return base/'cases'/row['case_name']


def analyze_case(row, geometry):
    folder = location(row)
    seal = read(folder/'completion.json')
    if sha(folder/'completion.json') != row['completion_sha256'] or seal['status'] != 'complete':
        raise ValueError('Case identity/completion mismatch: '+row['case_name'])
    inputs = {str(folder/'completion.json'): sha(folder/'completion.json')}
    for name in ('config.json', 'summary.json', 'trajectories.npz', 'events.jsonl.gz'):
        actual = sha(folder/name)
        if actual != seal['files'].get(name):
            raise ValueError('Sealed input changed: '+str(folder/name))
        inputs[str(folder/name)] = actual
    config = read(folder/'config.json')
    summary = read(folder/'summary.json')
    actual_h = config['herding_minimum_T']
    expected_h = float(row['herding_minimum_T']) if row['herding_minimum_T'] else None
    if (config['case_name'] != row['case_name'] or actual_h != expected_h
            or config['dt'] != .00125 or config['dolphins'] != int(row['dolphins'])
            or config['presence'] != row['presence'] or config['gannets'] != int(row['gannets'])
            or config['school_seed'] != int(row['school_seed']) or config['capture_probability'] != .7
            or config['contact_model'] != 'point' or float(config['duration_T']) != 36.):
        raise ValueError('Unexpected physical case configuration')
    birds = {a['state']['actor_id']: a['config'] for a in config['actors'] if a['state']['species'] == 'G'}
    with gzip.open(folder/'events.jsonl.gz', 'rt') as stream:
        events = [json.loads(line) for line in stream]
    captures = [e for e in events if e.get('kind') == 'oral' and e.get('status') == 'captured']
    if len({e['prey_id'] for e in captures}) != len(captures):
        raise ValueError('Duplicate prey removal')
    if len(captures) != int(row['initial_fish'])-int(row['remaining_fish']):
        raise ValueError('Removal conservation failure')
    bird_events = [e for e in events if e.get('actor_id') in birds]
    launches = geometry.event_times(bird_events, 'launch')
    bird_catches = geometry.event_times(bird_events, 'capture')
    if len(launches) != int(row['G_launches']) or len(bird_catches) != int(row['G_captures']):
        raise ValueError('Saved event totals mismatch')
    for species in ('D', 'G'):
        if summary['species'][species]['captures'] != int(row[species+'_captures']):
            raise ValueError('Saved species total mismatch')
    with np.load(folder/'trajectories.npz', allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
        times = np.asarray(data['time'], float)
        if abs(times[0]) > 1e-7 or abs(times[-1]-36.) > 1e-7 or np.any(np.diff(times) <= 0):
            raise ValueError('Diagnostics require a complete ordered36T trajectory')
        columns = [(i, str(actor)) for i, actor in enumerate(data['actor_ids']) if str(actor) in birds]
        if len(columns) != int(row['gannets']):
            raise ValueError('Saved roster mismatch')
        if len({json.dumps(cfg, sort_keys=True) for cfg in birds.values()}) != 1:
            raise ValueError('This summary assumes identical bird physical configs')
        cfg = next(iter(birds.values()))
        cap = cfg['max_dive_depth']-cfg['speed']/cfg['turn_rate']-cfg['ascent_margin']
        frames = []
        for i, time in enumerate(times):
            fish = data['positions'][i][data['alive'][i].astype(bool)]
            depth = cfg['surface_z']-fish[:, 2]
            eligible_depth = (depth >= 0) & (depth <= cfg['detection_depth']) & (depth <= cap)
            accessible = 0
            searches = 0
            for column, actor in columns:
                check = geometry.new_target_eligibility(fish, data['predator_positions'][i, column], birds[actor])
                accessible += bool(np.any(check['eligible']))
                searches += str(data['predator_modes'][i, column]) == 'search'
            frames.append(dict(case_name=row['case_name'], time_T=float(time), live_fish=len(fish),
                depth_eligible_fish=int(eligible_depth.sum()),
                depth_eligible_fraction=float(eligible_depth.mean()) if len(fish) else 0.,
                median_live_depth=float(np.median(depth)) if len(fish) else 0.,
                birds_with_new_target=accessible, birds_searching=searches,
                any_new_target=bool(accessible),
                depth_blackout=bool(len(fish) and not eligible_depth.any()),
                all_search_no_target=bool(len(fish) and searches == len(columns) and not accessible),
                shallow_but_unreachable=bool(eligible_depth.any() and not accessible)))
    durations = np.diff(times)
    horizon = float(times[-1]-times[0])
    result = dict(case_name=row['case_name'], school_seed=int(row['school_seed']),
        H_T=float(row['herding_minimum_T']) if row['herding_minimum_T'] else '',
        gannets=int(row['gannets']), presence=row['presence'],
        D_captures=int(row['D_captures']), G_captures=int(row['G_captures']),
        G_contacts=int(row['G_contacts']), G_launches=len(launches),
        G_contact_yield=int(row['G_contacts'])/len(launches) if launches else 0.,
        G_captures_per_bird=int(row['G_captures'])/int(row['gannets']),
        last_gannet_launch_T=geometry.last(launches),
        no_launch_final_6T=not any(t >= 30.-1e-8 for t in launches),
        all_birds_final_search=frames[-1]['birds_searching'] == len(columns),
        all_birds_final_no_accessible_targets=not frames[-1]['any_new_target'],
        terminal_contact_loss=frames[-1]['all_search_no_target'],
        effective_target_depth_cap=cap)
    for field in ('depth_eligible_fraction', 'median_live_depth'):
        values = np.asarray([f[field] for f in frames], float)
        result['time_mean_'+field] = float(np.sum(durations*(values[:-1]+values[1:])/2)/horizon)
    for field in ('any_new_target', 'depth_blackout', 'all_search_no_target', 'shallow_but_unreachable'):
        result['sampled_'+field+'_T'] = float(np.dot(durations, [f[field] for f in frames[:-1]]))
    return result, frames, inputs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = UPPER/'analysis_final/case_outcomes.csv'
    bank_audit_path = UPPER/'analysis_final/analysis_audit.json'
    bank_audit = read(bank_audit_path)
    if (bank_audit['status'] != 'passed' or bank_audit['files']['case_outcomes.csv'] != sha(source)
            or len(bank_audit['case_completion_sha256']) != 140):
        raise ValueError('Passed completed-map audit and exact master table required')
    inventory = table(source)
    if len(inventory) != 140 or len({r['case_name'] for r in inventory}) != 140:
        raise ValueError('Exactly140 complete condition-school outcomes required')
    rows = [r for r in inventory if int(r['gannets'])]
    expected = {(s, p, h, g) for s in SEEDS for g in COUNTS for p, h in [('G', ''), ('DG', '1.0'), ('DG', '2.0'), ('DG', '3.0')]}
    observed = {(int(r['school_seed']), r['presence'], r['herding_minimum_T'], int(r['gannets'])) for r in rows}
    if len(rows) != 128 or observed != expected:
        raise ValueError('Complete128-case bird-bearing inventory required')
    if any(bank_audit['case_completion_sha256'][r['case_name']] != r['completion_sha256'] for r in inventory):
        raise ValueError('Master table and completed-map case bindings disagree')
    geometry = load_geometry()
    old_table = LEGACY/'outputs/cessation_summary.csv'
    results, frames, inputs = [], [], {str(p): sha(p) for p in
        (source, bank_audit_path, LEGACY/'diagnostics.py', old_table)}
    for index, row in enumerate(rows, 1):
        result, trace, signatures = analyze_case(row, geometry)
        results.append(result)
        frames.extend(trace)
        inputs.update(signatures)
        if index % 16 == 0:
            print(f'Checked {index}/128 sealed trajectories', flush=True)
    # Reconcile the original48 exported facts without changing those files.
    prior = table(old_table)
    lookup = {r['case_name']: r for r in results}
    for old in prior:
        new = lookup[old['id']]
        for key in ('no_launch_final_6T', 'all_birds_final_search', 'all_birds_final_no_accessible_targets'):
            if new[key] != (old[key] == 'True'):
                raise ValueError('Old48 diagnostic discrepancy: '+key)
        if abs(new['last_gannet_launch_T']-float(old['last_gannet_launch_T'])) > 1e-8:
            raise ValueError('Old48 event-time discrepancy')
    paired = []
    fields = ('G_captures_per_bird', 'G_contact_yield', 'time_mean_depth_eligible_fraction',
        'time_mean_median_live_depth', 'sampled_any_new_target_T', 'sampled_depth_blackout_T',
        'sampled_all_search_no_target_T', 'sampled_shallow_but_unreachable_T')
    for mixed in (r for r in results if r['presence'] == 'DG'):
        alone = next(r for r in results if r['presence'] == 'G' and r['school_seed'] == mixed['school_seed'] and r['gannets'] == mixed['gannets'])
        paired.append(dict(school_seed=mixed['school_seed'], H_T=mixed['H_T'], gannets=mixed['gannets'],
            **{key+'_change': mixed[key]-alone[key] for key in fields},
            terminal_loss_alone=alone['terminal_contact_loss'], terminal_loss_mixed=mixed['terminal_contact_loss']))
    group = []
    for h in (1., 2., 3.):
        for g in COUNTS:
            values = [r for r in paired if r['H_T'] == h and r['gannets'] == g]
            group.append(dict(H_T=h, gannets=g, previously_examined_schools=4,
                **{key+'_mean_change': float(np.mean([r[key+'_change'] for r in values])) for key in fields},
                terminal_losses_Gonly=sum(r['terminal_loss_alone'] for r in values),
                terminal_losses_mixed=sum(r['terminal_loss_mixed'] for r in values)))
    write_csv(OUT/'case_accessibility.csv', results)
    write_csv(OUT/'sampled_accessibility.csv', frames)
    write_csv(OUT/'paired_accessibility.csv', paired)
    write_csv(OUT/'regime_accessibility.csv', group)
    if any(name.startswith('fish_sim') or name.endswith('.cmodel') for name in sys.modules):
        raise RuntimeError('Unexpected simulation-module import')
    receipt = dict(status='passed', at_utc=datetime.now(timezone.utc).isoformat(),
        analysis_source_sha256=sha(__file__), completed_cases=140, bird_bearing_cases=128,
        mixed_cases=96, bird_only_cases=32, previously_examined_schools=4,
        original48_reconciled=len(prior), paired_rows=len(paired), regime_rows=len(group),
        native_steps=0, simulation_module_imports=0, new_bootstrap_draws=0,
        inputs=inputs, outputs={p.name: sha(p) for p in OUT.glob('*.csv')},
        limitations=['Descriptive discovery reanalysis; no new independent schools.',
            'Depth/accessibility summaries concern surviving prey and are affected by removal.',
            'New-target eligibility is not a controller decision or a committed target test.',
            'Boolean durations use left-constant0.1T samples; boundaries uncertain by one sample.',
            'Terminal contact loss describes the36T boundary, not permanent abandonment.',
            'Dolphin presence changes access, disturbance, removal and trajectories together; these contrasts do not isolate causation.'])
    (OUT/'analysis_audit.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('inputs', 'outputs', 'limitations')}, indent=2))


if __name__ == '__main__':
    main()
