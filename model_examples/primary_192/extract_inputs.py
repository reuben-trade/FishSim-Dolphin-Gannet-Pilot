"""Private native-free archive of frozen starts and ONLY accepted first-world food refs."""
from pathlib import Path
import json,shutil,sys
from primary_runtime import HERE,ORIGINAL,STUDY,SOURCE_FREEZE,ZERO_SHA,inventory,read,sha,write

def main():
    source=ORIGINAL/STUDY;bulk=Path('/home/venture/FishSim_Independent_Validation_2026-11-10')
    if (HERE/'references').exists():raise FileExistsError('Input references already exist')
    freeze=source/'frozen_sources.json'
    if sha(freeze)!=SOURCE_FREEZE or sha(source/'ACTUAL_ZERO_STEP.json')!=ZERO_SHA:raise RuntimeError('Frozen primary/zero source changed')
    sources=read(freeze)['source_sha256']
    if len(sources)!=2127:raise RuntimeError('Expected2127 frozen bindings')
    for p,h in sources.items():
        if str(bulk/'full_36T_v1') in p or str(bulk/'phases') in p:raise RuntimeError('Unaccepted feeding path in source map')
        if sha(p)!=h:raise RuntimeError('Frozen input changed:'+p)
    references=HERE/'references';references.mkdir()
    for name in ('ACTUAL_ZERO_STEP.json','PURE_PREFLIGHT.json'):shutil.copy2(source/name,references/name)
    old=bulk/'archived_preparation_first8';new=bulk/'new_preparation_v1'
    a,b=read(old/'manifest.json'),read(new/'manifest.json')
    if a['status']!=b['status'] or a['status']!='complete' or a['native']['sha256']!=b['native']['sha256']:raise RuntimeError('Completed16 preparations required')
    checkpoints={}
    for seed in range(39065501,39065517):
        folder=(old if seed<39065509 else new)/f's{seed}';summary=read(folder/'summary.json');cp=folder/'encounter.npz'
        if not summary['accepted'] or sha(cp)!=summary['checkpoint']['sha256']:raise RuntimeError('Frozen accepted raw20T input changed')
        checkpoints[str(seed)]=dict(path=str(cp),sha256=sha(cp),accepted=True,screen_status='passed')
    accepted=bulk/'independent_block1_review.json'
    if sha(accepted)!='1609c4dd6d131bd95232ec3600dc428deba69d6b959eb46099fe057c4cd9a59c':raise RuntimeError('Only accepted first48 review may supply feeding refs')
    review=read(accepted);rows=[r for phase in review['phases'].values() for r in phase['rows']]
    selected=[r for r in rows if r['school_seed']==39065501 and r['capture_seed']==71001]
    if len(selected)!=6 or {r['presence'] for r in selected}!={'D','G','DG'} or {r['grid'] for r in selected}!={'coarse','fine'}:raise RuntimeError('Exactly first-world six accepted cases required')
    shutil.copy2(accepted,references/'accepted_block1_review.json')
    cases=[]
    for row in selected:
        folder=bulk/'full_36T_v1/cases'/row['case_name'];seal=read(folder/'completion.json')
        if sha(folder/'completion.json')!=row['completion_sha256'] or seal['status']!='complete':raise RuntimeError('Accepted completion binding changed')
        target=references/'full36T'/row['case_name'];target.mkdir(parents=True)
        for filename,digest in seal['files'].items():
            p=(folder/filename).resolve()
            if not p.is_relative_to(folder.resolve()) or sha(p)!=digest:raise RuntimeError('Sealed accepted raw reference changed')
            shutil.copy2(p,target/filename)
        shutil.copy2(folder/'completion.json',target/'completion.json')
        cases.append(dict(case_name=row['case_name'],grid=row['grid'],presence=row['presence'],dt=row['dt'],
            completion_sha256=row['completion_sha256'],native_steps=row['native_steps'],actual_duration_T=row['actual_duration_T']))
    write(HERE/'MODEL_INPUTS.json',dict(schema='primary_model_inputs_v1',primary_sources=sources,source_freeze_sha256=SOURCE_FREEZE,
        zero_source_sha256=ZERO_SHA,portable_reader_sha256='3d08ad828a2bb64c93492a7181ba5351d66ae57d4118b4eee877c0126a7c95e3',
        portable_reader_future_install_path='validation_tools/portable_reader.py',production_reader_candidate_freeze_sha256='6968bc5a158f9a61b04c43e3bde654c848319b6ae5ef558c2b376d5bf95062c6',
        production_reader_handoff_sha256='ef3e23637630e2764bb508a22b8abce805612fbea4e677ea01ff1e65d3647ec7',
        production_reader_independent_review_sha256='f339d8d79117efc55c931c3f1fd544221ef4f6ee712282608db9c1bb846db1cc',
        public_reference_aliases={'references/accepted_block1_review.json':'validation_progress/primary_192_2026-11-10/prefix_48/evidence/independent_block1_review.json'},
        preparation=dict(old_directory=str(old),new_directory=str(new),manifest=dict(status='complete',native=a['native'],checkpoints=checkpoints)),
        identity_count=192,accepted_reference_cases=cases,accepted_feeding_review_sha256=sha(accepted),unaccepted_feeding_rows_read=0))
    write(HERE/'REFERENCE_MANIFEST.json',dict(schema='primary_model_references_v1',files={str(p.relative_to(HERE)):sha(p) for p in sorted(references.rglob('*')) if p.is_file()},
        initialization_cases=192,accepted_full_feeding_reference_cases=6,case_names=[r['case_name'] for r in cases],
        scope='Only previously accepted firstschool39065501/label71001 bothgrids/three arms; no unaccepted feeding data',input_spec_sha256=sha(HERE/'MODEL_INPUTS.json')))
    if any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules):raise RuntimeError('Unexpected model import')
    print('Archived2127 frozen inputs by identity/SHA,192 zero references and6accepted full36T feeding cases;native0')

if __name__=='__main__':main()
