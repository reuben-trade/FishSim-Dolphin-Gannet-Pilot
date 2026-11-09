"""Additive, native-free one-rule regime-map analysis; historical v4 preserved."""
from __future__ import annotations
import csv
import importlib.util
from pathlib import Path

import notebook_support_v4 as historical
import regime_evidence_v5 as evidence

ROOT = Path(__file__).resolve().parent
VERSION = '2026-11-09_regime_v2'
SWEEP_NAME = 'pilot_regime_sweep_2026-11-09_v2'
SWEEP = ROOT/'data/research'/SWEEP_NAME
read,sha,print_table = evidence.read,evidence.sha,historical.print_table


def snapshot():
    """Created only after the complete v2 evidence is bundled and reviewed."""
    return read(ROOT/f'REGIME_SNAPSHOT_{VERSION}.json')


def verify_inputs():
    meta = snapshot()
    manifest = read(ROOT/meta['manifest'])
    for name,digest in manifest['files'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Protected input differs: '+name)
    for entry in read(ROOT/meta['source_closure']):
        if manifest['files'].get(entry['bundled_path'])!=entry['sha256']:
            raise ValueError('Source-closure file is absent from protected publication inputs')
    earlier = historical.verify_inputs()
    inventory = read(ROOT/meta['inventory'])
    if len(inventory['cases']) != 132 or inventory['case_count'] != 132:
        raise ValueError('Expected72historical plus60sweep execution records')
    fresh = [r for r in inventory['cases'] if r['study'] == SWEEP_NAME]
    if len(fresh) != 60 or sum(r['anchor_replay'] for r in fresh) != 8:
        raise ValueError('Require60v2executions, explicitly including8exactreplays')
    if any(r['study'] == 'pilot_regime_sweep_2026-11-09' for r in inventory['cases']):
        raise ValueError('Stopped v1attempt must remain supporting provenance only')
    expected = {r['case_name']:r for r in evidence.identities()}
    if {r['case'] for r in fresh} != set(expected):
        raise ValueError('Sweep inventory identities differ')
    for r in fresh:
        folder = ROOT/r['relative_path']
        if (sha(folder/'completion.json') != r['completion_sha256']
                or r['anchor_replay'] != expected[r['case']]['anchor_replay']):
            raise ValueError('Sweep execution inventory seal differs')
    result = evidence.verify_complete(SWEEP,closure=ROOT/meta['source_closure'],bundle_root=ROOT)
    runtime=verify_runtime_overlay()
    return dict(status='passed',snapshot=meta['version'],feeding_execution_records=132,
        preserved_historical_executions=earlier['feeding_encounters'],
        sweep_execution_records=60,exact_historical_replay_executions=8,
        additional_sweep_cells=52,sweep_independent_previously_observed_schools=4,
        earlier_independent_validation_schools=8,protected_inputs=len(manifest['files']),
        native_steps=0,full_map_audit=result,additive_runtime_files=runtime['files'],
        optional_runtime_scope=runtime['scope'])


def verify_runtime_overlay():
    manifest=read(ROOT/'ADDITIVE_RUNTIME_MANIFEST.json')
    base=manifest['required_existing_base_manifest']
    if sha(ROOT/base['path'])!=base['sha256'] or manifest['default_native_steps']!=0:
        raise ValueError('Runtime must preserve the exact historical base and native-free default')
    for name,digest in manifest['files'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Additive runtime input differs: '+name)
    return dict(status='passed',files=len(manifest['files']),scope=manifest['scope'],native_steps=0)


def sweep_case_rows():
    frozen = read(SWEEP/'frozen_sources.json')
    return [evidence.raw_row(SWEEP/'results/full_36T_v1/cases'/r['case_name'],r,frozen)
            for r in evidence.identities()]


def sweep_tables(rows=None):
    return evidence.reconstruct_map(sweep_case_rows() if rows is None else rows,
                                    read(SWEEP/'analysis_plan.json'))


def sweep_diagnostics(rows=None):
    source = {r['case_name']:r for r in (sweep_case_rows() if rows is None else rows)}
    result = evidence.diagnostic_rows(SWEEP)
    for r in result:
        raw = source[r['case_name']]
        for species,count in [('D',raw['dolphins']),('G',raw['gannets'])]:
            for name in ('captures','contacts','launches'):
                r[species+'_'+name] = raw[species+'_'+name]
                r[species+'_'+name+'_per_actor_per_T'] = raw[species+'_'+name]/(count*36) if count else None
        r['remaining_fish'] = raw['remaining_fish']
    return result


def original_shared_pairs():
    rows = historical.case_rows()
    return {group:[r for r in historical.paired_rows(rows,group) if r['policy'] == 'exposed']
            for group in ('development','replication')}


def whole_map_school_points(pairs):
    """All36school/setting contrasts, without selecting favourable outcomes."""
    return [dict(school_seed=r['school_seed'],herding_minimum_T=r['herding_minimum_T'],gannets=r['gannets'],
        D_change_per_dolphin_per36T=r['D_rate_change']*36,
        G_change_per_gannet_per36T=r['G_rate_change']*36,
        D_change_vs_best_tested_per_dolphin_per36T=r['D_rate_change_vs_best_tested_Donly']*36,
        both_positive=r['both_rate_changes_positive']) for r in pairs]


def reproduce_figures(output=None):
    output = ROOT/'outputs/regime_figures' if output is None else Path(output)
    spec = importlib.util.spec_from_file_location('_regime_figure_source',ROOT/'paper_figure_source_v5.py')
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.RESEARCH = ROOT/'data/research'
    module.DEVELOPMENT = module.RESEARCH/'simple_herd_strike_pilot_2026-11-08'
    module.REPLICATION = module.RESEARCH/'exposed_replication_2026-11-08'
    module.LONGER = module.RESEARCH/historical.COARSE
    module.FINE = module.RESEARCH/historical.FINE
    module.SWEEP = module.RESEARCH/SWEEP_NAME
    module.CLOSURE = ROOT/snapshot()['source_closure']
    module.BUNDLE_ROOT = ROOT
    module.OUT = output
    module.main()
    return output


def show_figure(name,output=None):
    return historical.show_figure(name,ROOT/'outputs/regime_figures' if output is None else output)


def export_regime_tables(rows,pairs,summary,diagnostics,output=None):
    output = ROOT/'outputs/regime_tables' if output is None else Path(output)
    output.mkdir(parents=True,exist_ok=True)
    datasets = {'sweep_case_outcomes':rows,'sweep_paired_school_changes':pairs,
        'sweep_regime_summary':summary,'sweep_state_contact_diagnostics':diagnostics,
        'sweep_all_school_points':whole_map_school_points(pairs)}
    for name,values in datasets.items():
        with (output/(name+'.csv')).open('w',newline='') as handle:
            writer = csv.DictWriter(handle,fieldnames=list(values[0]))
            writer.writeheader();writer.writerows(values)
    return [str((output/(name+'.csv')).relative_to(ROOT)) for name in datasets]
