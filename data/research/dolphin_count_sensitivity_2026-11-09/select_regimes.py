"""Select from the complete D12 map only; never read D24 outcomes."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from cases import SEEDS, HERDING_MINIMA, GANNET_COUNTS, DURATION, CAPTURE_SEED, DT


def key(row):
    return (int(row['school_seed']), None if row['herding_minimum_T'] in ('', None) else float(row['herding_minimum_T']),
            int(row['gannets']), int(row['dolphins']))


def validate_complete_rows(rows):
    counts = tuple(g for g in GANNET_COUNTS if g)
    expected = {(s, h, g, 12) for s in SEEDS for h in HERDING_MINIMA for g in GANNET_COUNTS}
    expected |= {(s, None, g, 0) for s in SEEDS for g in counts}
    lookup = {key(r): r for r in rows}
    if len(rows) != 140 or len(lookup) != 140 or set(lookup) != expected:
        raise ValueError('Complete 140-row D12 upper map required exactly once; no outcome filtering')
    for k, r in lookup.items():
        if int(r['capture_seed']) != CAPTURE_SEED or float(r['dt']) != DT or float(r['duration_T']) != DURATION:
            raise ValueError('Only the prescribed capture stream, grid and horizon are permitted')
        if float(r['D_captures'])+float(r['G_captures']) > 160:
            raise ValueError('Group catches exceed initial unique prey')
        for species, count in (('D', k[3]), ('G', k[2])):
            raw = r[species+'_captures']
            if isinstance(raw, bool) or float(raw) != int(float(raw)) or not 0 <= int(float(raw)) <= 160:
                raise ValueError('Invalid integer unique capture total')
            rate = r[species+'_rate']
            expected_rate = int(float(raw))/(count*DURATION) if count else None
            if count and (not math.isfinite(float(rate)) or abs(float(rate)-expected_rate) > 1e-14):
                raise ValueError('Per-animal nominal-horizon normalization changed')
            if not count and (int(float(raw)) != 0 or rate not in (None, '')):
                raise ValueError('Absent species has captures or a feeding rate')
    return lookup


def select(rows):
    lookup = validate_complete_rows(rows)
    candidates = []
    for h in HERDING_MINIMA:
        for g in GANNET_COUNTS[1:]:
            school = []
            for s in SEEDS:
                mixed, alone, birds = lookup[s, h, g, 12], lookup[s, h, 0, 12], lookup[s, None, g, 0]
                school.append(dict(school_seed=s,
                    D_capture_change=int(float(mixed['D_captures']))-int(float(alone['D_captures'])),
                    G_capture_change=int(float(mixed['G_captures']))-int(float(birds['G_captures']))))
            candidates.append(dict(herding_minimum_T=h, gannets=g,
                D_mixed_captures=sum(int(float(lookup[s, h, g, 12]['D_captures'])) for s in SEEDS),
                joint_positive_schools=sum(r['D_capture_change'] > 0 and r['G_capture_change'] > 0 for r in school),
                school_changes=school))
    order = lambda r: (-r['D_mixed_captures'], r['gannets'], r['herding_minimum_T'])
    a = min(candidates, key=order)
    eligible = [r for r in candidates if r['joint_positive_schools'] == len(SEEDS)]
    b = min(eligible, key=order) if eligible else None
    selected = [dict(a, selection_labels=['A_maximum_D12_mixed_return'])]
    if b is not None:
        if (a['herding_minimum_T'], a['gannets']) == (b['herding_minimum_T'], b['gannets']):
            selected[0]['selection_labels'].append('B_joint_positive_in_all_four_schools')
        else:
            selected.append(dict(b, selection_labels=['B_joint_positive_in_all_four_schools']))
    return dict(status='candidate_selection_requires_independent_review',
        based_only_on='complete D12 map; no D24 outcomes', independent_schools=4,
        tie_rule='maximum pooled mixed dolphin captures; then fewer gannets; then lower H',
        B_eligible=bool(eligible), regimes=selected, all_24_candidates=candidates)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', type=Path, required=True)
    p.add_argument('--analysis-audit', type=Path, required=True)
    p.add_argument('--independent-map-review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    audit = json.loads(args.analysis_audit.read_text())
    digest = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    if audit.get('status') != 'passed' or audit.get('files', {}).get(args.csv.name) != digest:
        p.error('Passed complete-map analysis audit must SHA-bind the input CSV')
    review = json.loads(args.independent_map_review.read_text())
    audit_sha = hashlib.sha256(args.analysis_audit.read_bytes()).hexdigest()
    if (review.get('status') != 'passed' or review.get('total_cases') != 140
            or review.get('analysis_audit_sha256') != audit_sha
            or review.get('case_completion_sha256') != audit.get('case_completion_sha256')):
        p.error('Complete independently reviewed map must precede candidate selection')
    with args.csv.open(newline='') as f:
        result = select(list(csv.DictReader(f)))
    result['input_bindings'] = dict(case_outcomes_csv=str(args.csv.resolve()), csv_sha256=digest,
        analysis_audit=str(args.analysis_audit.resolve()),
        analysis_audit_sha256=audit_sha, independent_map_review=str(args.independent_map_review.resolve()),
        independent_map_review_sha256=hashlib.sha256(args.independent_map_review.read_bytes()).hexdigest())
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(status=result['status'], regimes=result['regimes'])))


if __name__ == '__main__':
    main()
