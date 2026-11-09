"""All six fixed-school pilot contrasts; n=1 descriptive, no ranking or interval."""
import csv
from common import read,write,sha,stamp
from cases import Case,SEEDS,HERDING_MINIMA,NEW_COUNTS,phase_output,phase_record,prior_case
from evidence import validate_candidate_seal,validate_retained_case
from analyze import case_row

def describe():
    record=phase_record('pilot');output=phase_output('pilot');status=read(record/'status.json');physical=read(record/'physical_review.json')
    if status['status']!='complete' or status['complete']!=8 or physical['status']!='passed':
        raise RuntimeError('All eight pilot outcomes and physical review required')
    rows=[]
    for h in HERDING_MINIMA:
        alone=Case(SEEDS[0],h,0);d=case_row(prior_case(alone),alone)
        for n in NEW_COUNTS:
            c=Case(SEEDS[0],h,n);g=Case(SEEDS[0],None,n,False)
            m=case_row(output/'cases'/c.name,c);b=case_row(output/'cases'/g.name,g)
            rows.append(dict(school_seed=SEEDS[0],herding_minimum_T=h,gannets=n,independent_schools=1,
                D_alone_captures=d['D_captures'],D_mixed_captures=m['D_captures'],D_capture_change=m['D_captures']-d['D_captures'],
                D_relative_percent_change=100*(m['D_captures']/d['D_captures']-1) if d['D_captures'] else None,
                G_alone_captures=b['G_captures'],G_mixed_captures=m['G_captures'],G_capture_change=m['G_captures']-b['G_captures'],
                G_alone_per_bird=b['G_captures']/n,G_mixed_per_bird=m['G_captures']/n))
    path=record/'pilot_all_settings.csv'
    if path.exists():raise RuntimeError('Do not overwrite pilot description')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write(record/'descriptive_receipt.json',dict(status='passed',at=stamp(),schools=1,mixed_cells=6,full_cases=8,
        csv_sha256=sha(path),physical_review_sha256=sha(record/'physical_review.json'),
        interpretation='Fixed first school, n1 preliminary descriptive result only; no interval, ranking or robustness inference. All remaining24 conditions run regardless signs.'))
    return rows
if __name__=='__main__':
    print(describe())
