"""Portable standard-library inspection of the saved prospective identities.

Reads no simulator or feeding outcomes and executes no authoring harness.
"""
from pathlib import Path
import csv
import hashlib
import json

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def rows(path):
    with Path(path).open(newline='') as handle:return list(csv.DictReader(handle))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inspect():
    manifest=json.loads((HERE/'ARCHIVE_MANIFEST.json').read_text())
    for name,digest in manifest['files'].items():
        path=(HERE/name).resolve()
        if not path.is_relative_to(HERE) or sha(path)!=digest:raise AssertionError('Archive changed: '+name)
    new=rows(HERE/'new_mixed_cases.csv')
    smoke=rows(HERE/'engineering_smokes.csv')
    mapping=rows(HERE/'new_case_control_map.csv')
    paired=rows(HERE/'paired_control_map.csv')
    assert (len(new),len(smoke),len(mapping),len(paired))==(128,4,128,64)
    primary=rows(REPO/'prospective_plans/independent_validation_2026-11-10/case_inventory.csv')
    lower=rows(REPO/'prospective_plans/independent_lower_count_validation_2026-11-10/case_inventory.csv')
    def identity(row):return row.get('case_name',row.get('case_id'))
    old={identity(row) for row in primary+lower}
    assert len(primary)==len(lower)==192 and len(old)==384
    names={row['case_id'] for row in new}
    assert len(names)==128 and not names & old and len(names|old)==512
    expected={(str(seed),str(label),grid,str(h),str(g)) for seed in range(39065501,39065517)
        for label in (71001,71002) for grid in ('coarse','fine') for h,g in ((1,12),(2,36))}
    actual=set()
    for row in new:
        seed,label,grid,h,g=(row[k] for k in ('school_seed','capture_label','grid','herding_minimum_T','gannets'))
        assert row['replicate_label']==label==row['capture_seed']
        assert row['case_id']==row['case_name']==f's{seed}_{grid}_H{h}_G{g}_DG_c{label}'
        assert row['presence']=='DG' and int(row['dolphins'])==12 and int(row['initial_fish'])==160
        assert float(row['duration_T'])==36. and row['execution_status']=='PLANNED_NOT_AUTHORISED'
        assert float(row['dt'])==(.00125 if grid=='coarse' else .000625)
        assert int(row['maximum_native_steps'])==round(36./float(row['dt']))
        actual.add((seed,label,grid,h,g))
    assert actual==expected
    assert {row['mixed_case_id'] for row in mapping}==names
    new_by_id={row['case_id']:row for row in new}
    controls=set()
    for row in mapping:
        case=new_by_id[row['mixed_case_id']]
        for key in ('school_seed','replicate_label','capture_label','grid','dt','herding_minimum_T','gannets'):
            assert row[key]==case[key]
        seed,label,grid,h,g=(row[k] for k in ('school_seed','capture_label','grid','herding_minimum_T','gannets'))
        wanted_D=f's{seed}_{grid}_H{h}_G0_D_c{label}'
        wanted_G=f's{seed}_{grid}_Gonly{g}_G_c{label}'
        assert row['D_source_case_id']==wanted_D and row['G_source_case_id']==wanted_G
        assert wanted_D in old and wanted_G in old
        for species in ('D','G'):
            assert row[f'{species}_source_completion_sha256']==''
            assert row[f'{species}_reuse_status']=='PENDING_BOTH_COMPLETE_INDEPENDENT_FINAL_AUDITS'
        controls.update((wanted_D,wanted_G))
    assert len(controls)==256
    keys={(row['school_seed'],row['replicate_label'],row['grid']) for row in paired}
    assert len(keys)==64
    all_paired_ids=set()
    for row in paired:
        ids={v for k,v in row.items() if k.endswith('_case_id')}
        assert len(ids)==8 and ids<=(old|names)
        all_paired_ids.update(ids)
    assert len(all_paired_ids)==512
    assert len({row['case_id'] for row in smoke})==4
    assert {row['case_id'] for row in smoke}<=names
    assert all(float(row['duration_T'])==4. and row['included_in_estimation']=='False' for row in smoke)
    assert sum(int(row['maximum_native_steps']) for row in new)==5529600
    assert sum(int(row['maximum_native_steps']) for row in smoke)==19200
    return dict(status='passed',new_full_cases=128,engineering_cases=4,paired_control_rows=64,
        old_unique_cases=384,total_unique_full_cases=512,unique_reused_controls=256,
        independent_schools=16,nested_labels=2,worlds=32,world_grid_rows=64,
        full_maximum_steps=5529600,engineering_maximum_steps=19200,total_proposed_step_ceiling=5548800,
        native_steps_authorized=0,model_imports=0,feeding_outcome_reads=0)

if __name__=='__main__':print(json.dumps(inspect(),indent=2))
