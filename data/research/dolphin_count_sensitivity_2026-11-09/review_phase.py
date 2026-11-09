"""Read-only fixed-phase wrapper around the unchanged physical auditor."""
import argparse
from common import HERE, read, write, sha, stamp
from cases import all_cases, phase_cases, phase_output, phase_record, phase_limit, execution_stages
from evidence import validate_candidate_seal, verify_source_freeze
from review_actual import audit_case


def review(stage):
    verify_source_freeze(); record, output = phase_record(stage), phase_output(stage)
    status, cases = read(record/'status.json'), phase_cases(stage)
    expected = {c.name for c in cases}
    if (status.get('status') != 'complete' or status.get('complete') != len(cases)
            or status.get('planned') != len(cases) or len(status['cases']) != len(cases)
            or {x['case']['case_name'] for x in status['cases']} != expected):
        raise RuntimeError('Complete exact phase inventory required')
    permitted = expected | ({c.name for c in phase_cases('pilot')} if stage == 'remainder' else set())
    if {p.name for p in (output/'cases').iterdir()} != permitted:
        raise RuntimeError('Unexpected or partial phase case folders')
    for name, cells in execution_stages(stage):
        barrier = read(record/(name+'_stage.json'))
        if barrier.get('status') != 'complete' or barrier.get('cases') != [c.name for c in cells]:
            raise RuntimeError('Complete control-before-mixed stage barrier required')
    receipts = []
    for case in cases:
        folder = output/'cases'/case.name
        validate_candidate_seal(folder, duration=4. if stage == 'smoke' else 36.)
        receipts.append(audit_case(folder))
    steps = sum(r['native_steps'] for r in receipts)
    if steps != status['total_native_steps'] or steps > phase_limit(stage):
        raise RuntimeError('Phase step accounting/ceiling differs')
    path = record/'physical_review.json'
    if path.exists():
        raise RuntimeError('Preserve phase physical review')
    result = dict(status='passed', stage=stage, at=stamp(), native_steps_executed_by_review=0, cases=receipts,
        review_source_sha256=sha(HERE/'review_actual.py'), wrapper_source_sha256=sha(__file__),
        status_sha256=sha(record/'status.json'),
        scope='Unchanged H clock, exposed target, oral contact/recovery/private streams/cadence/removal; new D24-only controls before mixed')
    write(path, result)
    return result


def combine():
    verify_source_freeze(); output = phase_output('remainder')
    if (output/'status.json').exists() or (output/'physical_review.json').exists():
        raise RuntimeError('Final combined gate is one-shot')
    statuses = [read(phase_record(s)/'status.json') for s in ('pilot','remainder')]
    physical = [read(phase_record(s)/'physical_review.json') for s in ('pilot','remainder')]
    if any(s['status'] != 'complete' for s in statuses) or any(p['status'] != 'passed' for p in physical):
        raise RuntimeError('Both completed phase reviews required')
    rows = sum((p['cases'] for p in physical), []); cells = sum((s['cases'] for s in statuses), [])
    expected = {c.name for c in all_cases()}
    if (len(rows) != len(expected) or len(cells) != len(expected)
            or {r['case'] for r in rows} != expected or {r['case']['case_name'] for r in cells} != expected):
        raise RuntimeError('All selected unique scientific outcomes required regardless sign')
    for case in all_cases():
        validate_candidate_seal(output/'cases'/case.name)
    total = sum(s['total_native_steps'] for s in statuses)
    if total > len(expected)*28800 or total > 460800:
        raise RuntimeError('Full-study step ceiling exceeded')
    write(output/'status.json', dict(status='complete', at=stamp(), complete=len(expected), planned=len(expected),
        cases=cells, total_native_steps=total,
        phase_status_sha256={s:sha(phase_record(s)/'status.json') for s in ('pilot','remainder')}))
    write(output/'physical_review.json', dict(status='passed', at=stamp(), native_steps_executed_by_review=0,
        cases=rows, review_source_sha256=sha(HERE/'review_actual.py'),
        phase_review_sha256={s:sha(phase_record(s)/'physical_review.json') for s in ('pilot','remainder')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--stage', choices=('smoke','pilot','remainder'), required=True)
    args = parser.parse_args(); result = review(args.stage)
    if args.stage == 'remainder':
        combine()
    print(dict(status='passed', stage=args.stage, cases=len(result['cases'])))
