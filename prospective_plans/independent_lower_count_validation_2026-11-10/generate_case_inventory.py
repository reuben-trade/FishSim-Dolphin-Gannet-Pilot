"""Pure planned-case identities from byte-exact cases.py; no model/data loading."""
from pathlib import Path
import argparse,csv,hashlib,importlib.util,io,json,sys
HERE=Path(__file__).resolve().parent

def inventory():
    manifest=json.loads((HERE/'ARCHIVE_MANIFEST.json').read_text()) if (HERE/'ARCHIVE_MANIFEST.json').exists() else None
    path=HERE/'cases.py'
    if manifest and hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['frozen_files']['cases.py']:
        raise ValueError('Archived identity source changed')
    spec=importlib.util.spec_from_file_location('_frozen_validation_case_identities',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    rows=[case.asdict() for case in module.all_cases()]
    assert len(rows)==len({r['case_name'] for r in rows})==192
    assert len({r['school_seed'] for r in rows})==16
    assert len({(r['school_seed'],r['replicate_label']) for r in rows})==32
    assert {g:sum(r['grid']==g for r in rows) for g in module.GRIDS}=={'coarse':96,'fine':96}
    assert {p:sum(r['presence']==p for r in rows) for p in ('D','G','DG')}=={'D':64,'G':64,'DG':64}
    assert all(r['duration_T']==36 and r['replicate_label']==r['capture_seed']==r['capture_label'] for r in rows)
    assert all(r['gannets']==(12 if 'G' in r['presence'] else 0) and r['herding_minimum_T']==(2 if 'D' in r['presence'] else None) for r in rows)
    assert not any(k.endswith(('_captures','_contacts','_launches')) for r in rows for k in r)
    assert not any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules)
    text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return text.getvalue().encode()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path);args=p.parse_args();data=inventory()
    if args.check:
        assert data==(HERE/'case_inventory.csv').read_bytes(),'Planned inventory bytes changed'
    else:
        path=args.output or HERE/'case_inventory.csv'
        with path.open('xb') as stream:stream.write(data)
    print(json.dumps(dict(status='passed',planned_cases=192,independent_schools=16,nested_worlds=32,grids=2,arms=3,native_imports=0,native_steps=0,feeding_data_read=0,inventory_sha256=hashlib.sha256(data).hexdigest()),indent=2))
if __name__=='__main__':main()
