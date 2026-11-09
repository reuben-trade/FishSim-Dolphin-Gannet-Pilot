"""All selected first-school D24 outcomes, descriptive only, with no ranking."""
from common import HERE, read, sha, write
from cases import phase_cases, phase_record, phase_output, SEEDS
from evidence import verify_source_freeze


def main():
    verify_source_freeze()
    physical = read(phase_record('pilot')/'physical_review.json')
    status = read(phase_record('pilot')/'status.json')
    if physical.get('status') != 'passed' or status.get('status') != 'complete':
        raise RuntimeError('Complete physically audited fixed-school pilot required')
    rows = []
    for case in phase_cases('pilot'):
        folder = phase_output('pilot')/'cases'/case.name
        summary = read(folder/'summary.json')
        rows.append(dict(**case.asdict(), species=summary['species'],
            completion_sha256=sha(folder/'completion.json')))
    path = phase_record('pilot')/'description.json'
    if path.exists():
        raise RuntimeError('Preserve pilot description')
    write(path, dict(status='complete_descriptive_pilot', school_seed=SEEDS[0], independent_schools=1,
        cases=rows, physical_review_sha256=sha(phase_record('pilot')/'physical_review.json'),
        interpretation='All fixed selected settings and same-H D24-only controls; n1, no confidence intervals, ranking or validation; remainder remains mandatory'))


if __name__ == '__main__':
    main()
