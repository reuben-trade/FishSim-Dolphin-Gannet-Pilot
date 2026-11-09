"""Paired per-animal count sensitivity; native-free, all signs retained."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import numpy as np
from cases import HERE, SEEDS, DURATION, DT, CAPTURE_SEED, cases_for, all_cases, selected_regimes, phase_output
from select_regimes import key, validate_complete_rows

BOOTSTRAP_SEED = 88493024


def paired_statistics(new_rows, complete_D12_rows, regimes, draws=10000):
    """Rows must already have passed raw/physical audits and SHA bindings.

    One bootstrap resamples four entire school vectors, sharing each school
    across every regime, dolphin population and species endpoint.
    """
    regimes = tuple(dict.fromkeys(regimes))
    old = validate_complete_rows(complete_D12_rows)
    expected = {(c.school_seed, c.herding_minimum, c.gannets, 24) for c in cases_for(regimes)}
    new = {key(r): r for r in new_rows}
    if len(new_rows) != len(expected) or len(new) != len(expected) or set(new) != expected:
        raise ValueError('Every selected D24 mixed case and same-H D24 control is required exactly once')
    for k, row in new.items():
        if int(row['capture_seed']) != CAPTURE_SEED or float(row['dt']) != DT or float(row['duration_T']) != DURATION:
            raise ValueError('Only the prescribed capture stream, grid and horizon are permitted')
        if float(row['D_captures'])+float(row['G_captures']) > 160:
            raise ValueError('Group catches exceed initial unique prey')
        for species, count in (('D', 24), ('G', k[2])):
            if isinstance(row[species+'_captures'], bool):
                raise ValueError('Boolean is not a capture total')
            captures = int(row[species+'_captures'])
            if float(row[species+'_captures']) != captures or not 0 <= captures <= 160:
                raise ValueError('Invalid integer capture total')
            rate = row[species+'_rate']
            if count and not np.isclose(float(rate), captures/(count*DURATION), rtol=0, atol=1e-14):
                raise ValueError('D24 count-aware per-animal rate required')
            if not count and (captures or rate not in (None, '')):
                raise ValueError('Absent birds have no rate/captures')
    paired, vectors = [], []
    endpoint_names = ('D12_partner_rate_change', 'D24_partner_rate_change',
        'D24_minus_D12_partner_rate_change', 'D24_minus_D12_mixed_rate',
        'G_with_D12_partner_rate_change', 'G_with_D24_partner_rate_change')
    for school in SEEDS:
        school_vector = []
        for h, g in regimes:
            m12, a12 = old[school, h, g, 12], old[school, h, 0, 12]
            m24, a24, birds = new[school, h, g, 24], new[school, h, 0, 24], old[school, None, g, 0]
            # Compute integer contrasts before division so mathematical zero
            # remains exactly zero, including sign counts and bootstrap draws.
            m12d, a12d, m24d, a24d = (int(r['D_captures']) for r in (m12, a12, m24, a24))
            delta12, delta24 = m12d-a12d, m24d-a24d
            vector = (delta12/(12*DURATION), delta24/(24*DURATION),
                (delta24-2*delta12)/(24*DURATION), (m24d-2*m12d)/(24*DURATION),
                (int(m12['G_captures'])-int(birds['G_captures']))/(g*DURATION),
                (int(m24['G_captures'])-int(birds['G_captures']))/(g*DURATION))
            row = dict(school_seed=school, herding_minimum_T=h, gannets=g,
                **dict(zip(endpoint_names, vector)),
                D12_group_captures_mixed=m12d, D12_group_captures_alone=a12d,
                D24_group_captures_mixed=m24d, D24_group_captures_alone=a24d,
                D12_partner_group_capture_change=delta12, D24_partner_group_capture_change=delta24)
            paired.append(row)
            school_vector.append(vector)
        vectors.append(school_vector)
    values = np.asarray(vectors, dtype=float)
    indices = np.random.default_rng(BOOTSTRAP_SEED).integers(0, 4, size=(draws, 4))
    bounds = np.quantile(values[indices].mean(axis=1), [.025, .975], axis=0)
    summary = []
    for j, (h, g) in enumerate(regimes):
        row = dict(herding_minimum_T=h, gannets=g, independent_schools=4)
        for k, name in enumerate(endpoint_names):
            v = values[:, j, k]
            row.update({name+'_mean': float(v.mean()), name+'_sample_sd': float(v.std(ddof=1)),
                name+'_pointwise95_low': float(bounds[0, j, k]), name+'_pointwise95_high': float(bounds[1, j, k]),
                name+'_positive_schools': int((v > 0).sum()), name+'_zero_schools': int((v == 0).sum()),
                name+'_negative_schools': int((v < 0).sum())})
        summary.append(row)
    return paired, summary


def case_row(folder, expected, reference=False):
    """Reconcile each counted capture/launch/contact against the sealed raw log."""
    from common import read, sha
    from evidence import validate_candidate_seal, validate_reference
    folder = Path(folder)
    (validate_reference(folder, expected['completion_sha256']) if reference else validate_candidate_seal(folder))
    config, summary = read(folder/'config.json'), read(folder/'summary.json')
    row = dict(expected)
    for field in ('school_seed','gannets','dolphins','capture_seed'):
        row[field] = int(row[field])
    row['herding_minimum_T'] = None if row['herding_minimum_T'] in (None,'') else float(row['herding_minimum_T'])
    row['dt'], row['duration_T'] = DT, DURATION
    if (config['school_seed'] != row['school_seed'] or config['capture_seed'] != CAPTURE_SEED
            or config['policy'] != row['policy'] or config['presence'] != row['presence']
            or config['counts'] != dict(fish=160, D=row['dolphins'], G=row['gannets'])
            or config['dolphin_target_policy'] != 'exposed'
            or config['minimum_herding_duration'] != row['herding_minimum_T']):
        raise ValueError('Sealed raw case/config identity differs from selected comparison')
    with gzip.open(folder/'events.jsonl.gz','rt') as handle:
        events = [json.loads(line) for line in handle]
    captured = []
    for species, count in (('D', row['dolphins']), ('G', row['gannets'])):
        oral = [e for e in events if e['kind'] == 'oral' and e['actor_id'].startswith(species) and e['closes_bout']]
        catches = [e for e in oral if e['status'] == 'captured']
        launches = [e for e in events if e['kind'] == 'transition' and e['reason'] == 'launch' and e['actor_id'].startswith(species)]
        account = summary['species'][species]
        if (len(catches),len(oral),len(launches),count) != (account['captures'],account['contacts'],account['launches'],account['count']):
            raise ValueError('Raw contacts/captures/launches differ from species accounts')
        captured.extend(e['prey_id'] for e in catches)
        row.update({species+'_captures':len(catches), species+'_contacts':len(oral), species+'_launches':len(launches),
            species+'_rate':len(catches)/(count*DURATION) if count else None})
        if reference and (len(catches) != int(expected[species+'_captures'])
                or (count and abs(row[species+'_rate']-float(expected[species+'_rate'])) > 1e-14)):
            raise ValueError('Reused raw outcomes differ from complete selected D12 map')
    if (len(captured) != len(set(captured)) or len(captured) != summary['initial_count']-summary['final_count']
            or summary['initial_count'] != 160):
        raise ValueError('Unique prey-removal conservation differs')
    row.update(completion_sha256=sha(folder/'completion.json'), native_steps=summary['native_steps'],
        remaining_fish=summary['final_count'], execution_origin='reused_D12_map' if reference else 'new_D24_sensitivity')
    return row


def write_csv(path, rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader(); writer.writerows(rows)


def main():
    from common import read, sha, write
    from evidence import verify_source_freeze, validate_selection
    from reference import reference_path, MAP, MAP_AUDIT, MAP_REVIEW
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=phase_output('remainder'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(); verify_source_freeze()
    if args.input.resolve() != phase_output('remainder').resolve():
        parser.error('Exact selected-study output required')
    rows12 = validate_selection(); lookup = validate_complete_rows(rows12)
    status, physical = read(args.input/'status.json'), read(args.input/'physical_review.json')
    if (status.get('status') != 'complete' or status.get('complete') != len(all_cases())
            or physical.get('status') != 'passed' or len(physical['cases']) != len(all_cases())):
        parser.error('Every selected D24 case and full physical review required')
    new = [case_row(args.input/'cases'/c.name, c.asdict()) for c in all_cases()]
    if ({r['case_name']:r['completion_sha256'] for r in new}
            != {r['case']:r['completion_sha256'] for r in physical['cases']}):
        raise RuntimeError('Physical review must bind every new D24 case exactly')
    regimes = selected_regimes()
    needed = {(s,h,g,12) for s in SEEDS for h,g in regimes}
    needed |= {(s,h,0,12) for s in SEEDS for h,_ in regimes}
    needed |= {(s,None,g,0) for s in SEEDS for _,g in regimes}
    reused = [case_row(reference_path(*k), lookup[k], reference=True) for k in sorted(needed, key=str)]
    paired, summary = paired_statistics(new, rows12, regimes)
    output = args.output or args.input/'analysis_final'; output.mkdir(parents=True, exist_ok=False)
    write_csv(output/'case_outcomes.csv',new); write_csv(output/'reused_case_outcomes.csv',reused)
    write_csv(output/'paired_school_changes.csv',paired); write_csv(output/'regime_summary.csv',summary)
    caption = ('D24 versus D12 at regimes selected from the complete prior D12 map before D24 outcomes. '
        'Each population has its own same-H dolphin-only baseline; count-matched gannet-only outcomes are reused. '
        'Primary effects are captures per dolphin per nominal36T with gannets minus without, and their D24−D12 interaction. '
        'Integer count contrasts precede division: mathematical zeros retain exact zero signs. '
        'All four previously observed school vectors are jointly resampled for pointwise95% intervals; n4, one capture setting, exploratory selection, no independent validation or numerical-convergence claim. '
        'D24 places two point dolphins at each original12slot, without avoidance/collision or increased spatial coverage. Group catches are distinct from per-animal benefit; every sign remains visible.')
    (output/'caption.txt').write_text(caption+'\n')
    write(output/'analysis_audit.json', dict(status='passed', native_steps_executed_by_analysis=0,
        new_cases=len(new), reused_comparator_cases=len(reused), selected_regimes=len(regimes), independent_schools=4,
        selected_regimes_sha256=sha(HERE/'selected_regimes.json'), source_freeze_sha256=sha(HERE/'frozen_sources.json'),
        complete_D12_csv_sha256=sha(MAP), complete_D12_analysis_audit_sha256=sha(MAP_AUDIT),
        complete_D12_independent_review_sha256=sha(MAP_REVIEW),
        new_case_completion_sha256={r['case_name']:r['completion_sha256'] for r in new},
        reused_case_completion_sha256={r['case_name']:r['completion_sha256'] for r in reused},
        bootstrap=dict(seed=BOOTSTRAP_SEED, draws=10000, unit='whole paired school vector', quantiles=[.025,.975]),
        limitations=caption, files={p.name:sha(p) for p in output.iterdir() if p.is_file()}))
    print(json.dumps(dict(status='passed', new_cases=len(new), reused_cases=len(reused), independent_schools=4)))


if __name__ == '__main__':
    main()
