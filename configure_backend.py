"""Future publisher utility: bind only an accepted activated production snapshot.

No production data are read by --plan. This source is not export activation.
"""
import argparse,copy,json
from pathlib import Path
from integration import Session,read,relative,require,sha,write

def proposed_profile(root,snapshot,activation):
    root=Path(root).resolve();path=Path(snapshot).resolve()
    if path.is_dir():path=(path/'SNAPSHOT.json').resolve()
    require(path.name=='SNAPSHOT.json' and path.is_relative_to(root),'Bundle the actual snapshot under this package before binding')
    manifest=read(path);require(manifest['kind']=='PRIMARY192_PRODUCTION' and manifest['production_accepted'] is True,'Only a real accepted production snapshot may bind this profile')
    require(len(manifest['cases'])==192,'Partial validation cannot bind the final-paper profile')
    approval=Path(activation).resolve();require(approval.is_relative_to(root),'Bundle the root export activation as provenance')
    profile=copy.deepcopy(read(root/'FINAL_NOTEBOOK_PROFILE.json'))
    profile['status']='PRODUCTION_DATA_BOUND_PENDING_PUBLICATION_REVIEW'
    profile['validation'].update(kind='PRIMARY192_PRODUCTION',snapshot_manifest=str(path.relative_to(root)),snapshot_manifest_sha256=sha(path),export_receipt_sha256=sha(path.parent/'EXPORT_RECEIPT.json'),independent_final_sha256=manifest['evidence']['independent_final'],metadata_sidecar_sha256=manifest['evidence']['metadata_sidecar'],root_activation=str(approval.relative_to(root)),root_activation_sha256=sha(approval))
    return profile

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--plan',action='store_true');p.add_argument('--snapshot',type=Path);p.add_argument('--root-activation',type=Path);p.add_argument('--bind',action='store_true');a=p.parse_args()
    if not a.bind:
        print(json.dumps(dict(status='PRODUCTION_BINDING_CLOSED',required=['exact sealed192 portable production snapshot','original8ff FINAL','5cc metadata PASS','root-approved export activation','publisher integration peer review'],logical_notebook_cells_change=False,simulation_steps=0),indent=2));return
    require(a.snapshot is not None and a.root_activation is not None,'Binding needs actual final snapshot and root activation')
    root=a.root.resolve();profile=proposed_profile(root,a.snapshot,a.root_activation)
    # Use a temporary relative profile; Session applies the real pinned reader,
    # original FINAL/metadata chain and root approval, independent of effect sign.
    trial=root/'PROPOSED_PRODUCTION_PROFILE.json';require(not trial.exists(),'Preserve an earlier proposed profile')
    write(trial,profile)
    try:
        session=Session(root,trial.name)
        require(session.validation_result['production_accepted'] is True,'Production reader acceptance required')
        write(root/'FINAL_NOTEBOOK_PROFILE.json',profile)
        print(json.dumps(dict(status='bound_private_profile_not_published',profile_sha256=sha(root/'FINAL_NOTEBOOK_PROFILE.json'),case_count=192,independent_schools=16,native_steps=0,new_bootstrap_draws=0)))
    finally:trial.unlink()
if __name__=='__main__':main()
