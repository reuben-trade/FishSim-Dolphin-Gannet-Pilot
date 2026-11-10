"""Add only six exact engineering records accepted by the block1 prefix audit."""
from pathlib import Path
import shutil
from primary_runtime import HERE,read,sha,write

def main():
    root=Path('/home/venture/FishSim_Independent_Validation_2026-11-10')
    accepted=read(HERE/'references/accepted_block1_review.json')
    if sha(HERE/'references/accepted_block1_review.json')!='1609c4dd6d131bd95232ec3600dc428deba69d6b959eb46099fe057c4cd9a59c':raise RuntimeError('Exact accepted prefix audit required')
    rows=[]
    for binding in accepted['prefixes']:
        name=binding['case'];folder=root/'smoke_4T_v1/cases'/name;seal=read(folder/'completion.json')
        if sha(folder/'completion.json')!=binding['smoke_completion_sha256'] or seal['status']!='complete':raise RuntimeError('Accepted engineering completion changed')
        if binding['full_completion_sha256']!=sha(HERE/'references/full36T'/name/'completion.json'):raise RuntimeError('Accepted4T→36T prefix binding differs')
        target=HERE/'references/smoke4T'/name;target.mkdir(parents=True,exist_ok=True)
        for file,digest in seal['files'].items():
            source=(folder/file).resolve()
            if not source.is_relative_to(folder.resolve()) or sha(source)!=digest:raise RuntimeError('Engineering sealed reference changed')
            if (target/file).exists():
                if sha(target/file)!=digest:raise RuntimeError('Existing engineering extraction differs')
            else:shutil.copy2(source,target/file)
        if not (target/'completion.json').exists():shutil.copy2(folder/'completion.json',target/'completion.json')
        elif sha(target/'completion.json')!=binding['smoke_completion_sha256']:raise RuntimeError('Existing engineering completion differs')
        rows.append(binding)
    if len(rows)!=6:raise RuntimeError('Exactly six accepted engineering records required')
    spec=read(HERE/'MODEL_INPUTS.json');spec.update(accepted_engineering_cases=rows,
        accepted_engineering_prefix_audit_sha256=sha(HERE/'references/accepted_block1_review.json'))
    write(HERE/'MODEL_INPUTS.json',spec)
    manifest=read(HERE/'REFERENCE_MANIFEST.json');manifest.update(files={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'references').rglob('*')) if p.is_file()},
        accepted_engineering_reference_cases=6,input_spec_sha256=sha(HERE/'MODEL_INPUTS.json'),scope='Six accepted4Tengineering plus six accepted36Tfirst-world cases and192 actualzero; no unacceptedfeeding')
    write(HERE/'REFERENCE_MANIFEST.json',manifest);print('Added6accepted4Tengineering refs/terminalstreams;native0')

if __name__=='__main__':main()
