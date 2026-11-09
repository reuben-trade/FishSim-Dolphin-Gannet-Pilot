"""Full-map exploratory paired analysis from sealed outputs; zero native steps."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from cases import all_cases, SEEDS, HERDING_MINIMA, GANNET_COUNTS, DURATION
from evidence import validate_candidate_seal, require_anchor_stage, verify_source_freeze

HERE = Path(__file__).resolve().parent
POSITIVE_COUNTS = tuple(g for g in GANNET_COUNTS if g)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_events(path):
    with gzip.open(path, 'rt') as handle:
        return [json.loads(line) for line in handle]


def case_row(path, case):
    seal = validate_candidate_seal(path)
    summary = json.loads((path/'summary.json').read_text())
    config = json.loads((path/'config.json').read_text())
    if (config['policy'] != case.policy or config['presence'] != case.presence
            or config['counts'] != dict(fish=160, D=12 if case.dolphins else 0, G=case.gannets)):
        raise ValueError('Case/config identity mismatch')
    if config['dolphin_target_policy'] != 'exposed' or config['minimum_herding_duration'] != case.herding_minimum:
        raise ValueError('Wrong target policy or H')
    events = read_events(path/'events.jsonl.gz')
    row = case.asdict()
    row.update(remaining_fish=summary['final_count'], initial_fish=summary['initial_count'],
        native_steps=summary['native_steps'], water_entries=summary['water_entries'],
        completion_sha256=sha(path/'completion.json'))
    captured = []
    for species, count in (('D', 12 if case.dolphins else 0), ('G', case.gannets)):
        oral = [e for e in events if e['kind'] == 'oral' and e['actor_id'].startswith(species) and e['closes_bout']]
        catches = [e for e in oral if e['status'] == 'captured']
        launches = [e for e in events if e['kind'] == 'transition' and e['reason'] == 'launch' and e['actor_id'].startswith(species)]
        expected = summary['species'][species]
        if (len(catches), len(oral), len(launches), count) != (expected['captures'], expected['contacts'], expected['launches'], expected['count']):
            raise ValueError('Raw event and species accounts disagree')
        captured.extend(e['prey_id'] for e in catches)
        row.update({species+'_captures': len(catches), species+'_contacts': len(oral), species+'_launches': len(launches),
            species+'_rate': len(catches)/(count*DURATION) if count else None,
            species+'_captures_per_contact': len(catches)/len(oral) if oral else None})
    if len(captured) != len(set(captured)) or len(captured) != summary['initial_count']-summary['final_count']:
        raise ValueError('Unique prey-removal conservation failed')
    return row


def paired_statistics(rows, plan):
    expected = {(c.school_seed, c.herding_minimum, c.gannets, c.dolphins) for c in all_cases()}
    lookup = {(r['school_seed'], r['herding_minimum_T'], r['gannets'], bool(r['dolphins'])): r for r in rows}
    if len(rows) != 60 or len(lookup) != 60 or set(lookup) != expected:
        raise ValueError('All60 cells exactly once are required; no positive-cell selection')
    controls = np.asarray([[lookup[seed, h, 0, True]['D_rate'] for h in HERDING_MINIMA] for seed in SEEDS])
    best_index = int(np.argmax(controls.mean(axis=0)))  # sorted H gives smallest-H tie rule
    best_h = HERDING_MINIMA[best_index]
    mixed_returns = []
    paired = []
    vectors = []
    for seed in SEEDS:
        vector = []
        mixed_vector = []
        for h in HERDING_MINIMA:
            alone = lookup[seed, h, 0, True]
            for g in POSITIVE_COUNTS:
                mixed = lookup[seed, h, g, True]
                birds = lookup[seed, None, g, False]
                d = mixed['D_rate']-alone['D_rate']
                b = mixed['G_rate']-birds['G_rate']
                paired.append(dict(school_seed=seed, herding_minimum_T=h, gannets=g,
                    D_rate_alone=alone['D_rate'], D_rate_mixed=mixed['D_rate'], D_rate_change=d,
                    G_rate_alone=birds['G_rate'], G_rate_mixed=mixed['G_rate'], G_rate_change=b,
                    D_capture_change=mixed['D_captures']-alone['D_captures'],
                    G_capture_change=mixed['G_captures']-birds['G_captures'],
                    best_tested_Donly_H=best_h,
                    D_rate_change_vs_best_tested_Donly=mixed['D_rate']-lookup[seed, best_h, 0, True]['D_rate'],
                    both_rate_changes_positive=d > 0 and b > 0))
                vector.append((d, b))
                mixed_vector.append(mixed['D_rate'])
        vectors.append(vector)
        mixed_returns.append(mixed_vector)
    values = np.asarray(vectors, float)  # school × all9cells × two species
    settings = plan['bootstrap']
    indices = np.random.default_rng(settings['seed']).integers(0, len(SEEDS), size=(settings['draws'], len(SEEDS)))
    draws = values[indices].mean(axis=1)
    bounds = np.quantile(draws, settings['quantiles'], axis=0)
    means = values.mean(axis=0)
    mixed_returns = np.asarray(mixed_returns)
    # The discovery comparison selects the best D-only H within each whole-
    # school bootstrap resample. It remains exploratory; the observed H* must
    # be frozen before any future independent validation.
    best_draws = mixed_returns[indices].mean(axis=1)-controls[indices].mean(axis=1).max(axis=1)[:, None]
    best_bounds = np.quantile(best_draws, settings['quantiles'], axis=0)
    summary = []
    for j, (h, g) in enumerate((h, g) for h in HERDING_MINIMA for g in POSITIVE_COUNTS):
        r = dict(herding_minimum_T=h, gannets=g, independent_schools=4)
        for k, species in enumerate(('D', 'G')):
            r.update({species+'_mean_rate_change': float(means[j, k]),
                species+'_pointwise95_low': float(bounds[0, j, k]),
                species+'_pointwise95_high': float(bounds[1, j, k]),
                species+'_positive_schools': int(np.count_nonzero(values[:, j, k] > 0)),
                species+'_zero_schools': int(np.count_nonzero(values[:, j, k] == 0)),
                species+'_negative_schools': int(np.count_nonzero(values[:, j, k] < 0))})
        r['both_positive_schools'] = int(np.count_nonzero((values[:, j, 0] > 0) & (values[:, j, 1] > 0)))
        r.update(best_tested_Donly_H=best_h, best_tested_Donly_mean_rate=float(controls[:, best_index].mean()),
            D_mixed_mean_rate=float(mixed_returns[:, j].mean()),
            D_mean_rate_change_vs_best_tested_Donly=float(mixed_returns[:, j].mean()-controls[:, best_index].mean()),
            D_vs_best_tested_pointwise95_low=float(best_bounds[0, j]),
            D_vs_best_tested_pointwise95_high=float(best_bounds[1, j]))
        summary.append(r)
    return paired, summary


def write_csv(path, rows):
    with open(path, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_map(summary, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    values = [np.asarray([r[key] for r in summary]).reshape(3, 3) for key in (
        'D_mean_rate_change', 'G_mean_rate_change', 'D_mean_rate_change_vs_best_tested_Donly')]
    bound = max(float(np.max(abs(a))) for a in values) or 1e-6
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8), constrained_layout=True)
    for ax, data, species in zip(axes, values, ('Dolphins: mixed − same-H alone', 'Gannets: mixed − G-only', 'Dolphins: mixed − best tested alone')):
        im = ax.imshow(data, origin='lower', cmap='RdBu_r', norm=TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound))
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f'{data[i,j]:+.4f}', ha='center', va='center', fontsize=9)
        ax.set(xticks=range(3), xticklabels=POSITIVE_COUNTS, yticks=range(3), yticklabels=HERDING_MINIMA,
            xlabel='Gannets in mixed group', ylabel='Continuous local herding minimum (T)', title=species)
    fig.colorbar(im, ax=axes, label='Capture-rate change per animal per T', shrink=.8)
    fig.suptitle('Exploratory map: four previously observed schools, dt=0.00125, 36T', fontsize=11)
    for ext in ('png', 'pdf'):
        fig.savefig(output/f'regime_map.{ext}', dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE/'results/full_36T_v1')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    verify_source_freeze()
    status = json.loads((args.input/'status.json').read_text())
    physical = json.loads((args.input/'physical_review.json').read_text())
    if status.get('status') != 'complete' or status.get('complete') != 60 or physical.get('status') != 'passed':
        parser.error('All60 cells plus physical review are required; partial maps are not final analysis')
    anchor = require_anchor_stage(args.input)
    rows = [case_row(args.input/'cases'/case.name, case) for case in all_cases()]
    paired, summary = paired_statistics(rows, json.loads((HERE/'analysis_plan.json').read_text()))
    output = args.output or args.input/'analysis_final'
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output/'case_outcomes.csv', rows)
    write_csv(output/'paired_school_changes.csv', paired)
    write_csv(output/'regime_summary.csv', summary)
    best = dict(selected_H=summary[0]['best_tested_Donly_H'],
        selection='Highest across-four-school mean D-only per-animal36T return among H1/2/3; ties choose smallest H',
        independent_schools=4, capture_seed=61001, scope='Best tested on this discovery bank, not a global optimum',
        validation='Freeze this H before any held-out validation; do not reselect on held-out outcomes',
        source_case_completion_sha256={r['case_name']: r['completion_sha256'] for r in rows if r['gannets']==0})
    (output/'best_tested_Donly.json').write_text(json.dumps(best, indent=2)+'\n')
    plot_map(summary, output)
    caption = ('All nine mixed-group combinations, including positive, zero and negative changes. '
        'Four existing school geometries, one capture-stream label, original coarse timestep, 36T. '
        'Colour shows paired per-animal feeding-rate change against H-matched D-only or count-matched G-only controls. '
        'G0-only and G0–G2 rosters retain original launch locations; G3–G5 duplicate those locations. '
        'Intervals in the accompanying table resample whole four-school vectors and are exploratory pointwise95%, '
        'with no multiplicity adjustment, independent validation or optimal-regime claim. '
        'A separate comparison uses the best-tested D-only H, selected on this discovery bank; its bootstrap reselects H within each resample. '
        'The eight anchor replays are existing outcomes, not eight new independent samples.')
    (output/'caption.txt').write_text(caption+'\n')
    audit = dict(status='passed', native_steps_executed_by_analysis=0, cells=60,
        independent_schools=4, previously_observed_anchor_cells=8, additional_cells=52,
        bootstrap=json.loads((HERE/'analysis_plan.json').read_text())['bootstrap'],
        anchor_replay=anchor, case_completion_sha256={r['case_name']: r['completion_sha256'] for r in rows},
        limitations=caption, files={p.name: sha(p) for p in output.iterdir() if p.is_file()})
    (output/'analysis_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(dict(status='passed', output=str(output), cells=60, independent_schools=4)))


if __name__ == '__main__':
    main()
