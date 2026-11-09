"""Optional complete-count descriptive table; never rank or select partial cells."""
import argparse
from pathlib import Path
from common import read,sha,write,stamp
from cases import BULK,NEW_COUNTS,all_cases,retained_cases,prior_case,SEEDS,HERDING_MINIMA
from evidence import verify_source_freeze
from review_actual import audit_case
from analyze import case_row,write_csv

def describe(count,output):
    if count not in NEW_COUNTS:raise ValueError('Only a declared new count')
    verify_source_freeze();cells=[c for c in all_cases() if c.gannets==count]
    if len(cells)!=16:raise RuntimeError('Complete16-case count block required')
    receipts=[audit_case(output/'cases'/c.name) for c in cells]
    rows=[case_row(output/'cases'/c.name,c) for c in cells]
    if {r['case_name']:r['completion_sha256'] for r in rows}!={r['case']:r['completion_sha256'] for r in receipts}:
        raise RuntimeError('Current physical audits must bind all16 cases')
    old={c.name:case_row(prior_case(c),c) for c in retained_cases() if c.gannets==0}
    lookup={(r['school_seed'],r['herding_minimum_T'],bool(r['dolphins'])):r for r in rows}
    contrasts=[]
    for seed in SEEDS:
        birds=lookup[seed,None,False]
        for h in HERDING_MINIMA:
            mixed=lookup[seed,h,True]
            alone=next(r for r in old.values() if r['school_seed']==seed and r['herding_minimum_T']==h)
            contrasts.append(dict(school_seed=seed,herding_minimum_T=h,gannets=count,
                D_alone=alone['D_captures'],D_mixed=mixed['D_captures'],D_change=mixed['D_captures']-alone['D_captures'],
                G_alone=birds['G_captures'],G_mixed=mixed['G_captures'],G_change=mixed['G_captures']-birds['G_captures']))
    dest=output/f'complete_count_G{count}_description';dest.mkdir(exist_ok=False)
    write_csv(dest/'all16_case_outcomes.csv',rows);write_csv(dest/'all12_paired_school_contrasts.csv',contrasts)
    write(dest/'descriptive_receipt.json',dict(status='complete_count_descriptive_only',at=stamp(),count=count,cases=16,
        independent_schools=4,selection=False,full48_still_required=True,physical=receipts,
        note='All4schools at all3H included; no winner ranking,pointwise inference or new parameter selection before complete48',
        files={p.name:sha(p) for p in dest.iterdir() if p.is_file()}))
    return dest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--count',type=int,choices=NEW_COUNTS,required=True)
    parser.add_argument('--input',type=Path,default=BULK/'full_36T_v1');args=parser.parse_args()
    print(describe(args.count,args.input))
