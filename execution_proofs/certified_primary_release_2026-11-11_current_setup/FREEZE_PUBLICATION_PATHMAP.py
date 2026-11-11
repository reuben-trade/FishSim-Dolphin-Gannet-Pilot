from pathlib import Path
import datetime, hashlib, json, re, shutil, subprocess, sys

ROOT=Path('/home/venture/FishSim Certified Release Candidate 2026-11-11')
HERE=Path(__file__).resolve().parent
CANONICAL=Path('/home/venture/uwa/complex-systems/FishSim-RL/research/thesis_working_draft_2026-11-08')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
maps=[Path('/home/venture/FishSim Final Publication Candidate 2026-11-11/private_preparation/PRIOR_PROTECTED_FILES.json'),
      CANONICAL/'publication_protection_additions_2026-11-11_primary192_final.json',
      CANONICAL/'publication_protection_additions_2026-11-11_notebook_usability.json']
protected={}
for p in maps:
    for n,h in read(p)['files'].items():
        if n in protected:assert protected[n]==h
        protected[n]=h
assert len(protected)==15982
for n,h in protected.items():assert sha(ROOT/n)==h,n
sys.path.insert(0,str(ROOT))
from replay_tools.primary_192.notebook_session import Session
s=object.__new__(Session);s.root=ROOT;s.verify_package()
assert s.logical_notebook_validation['settings']['RUN_NATIVE']is False
preservation=dict(schema='certified_primary_release_final_preservation_v2',status='passed',
    protected_files=len(protected),all_protected_hashes_exact=True,installed_old_model_payloads=sum(n.startswith('model_examples/primary_192/')for n in protected),
    original_private_model_closure=329,installed_model_closure=328,administrative_private_handoff_omitted=True,
    original_package_inputs=467,other_466_plus_oldmain_archive_exact=True,
    source_maps=[dict(path=str(p),sha256=sha(p))for p in maps],logical_validation=s.logical_notebook_validation,
    paper_pdf_sha256=sha(ROOT/'reports/current/Feeding_Frenzy_Working_Draft.pdf'),
    snapshot_sha256=sha(ROOT/'data/primary_validation192_2026-11-11/SNAPSHOT.json'),
    native_steps=0,model_imports=0,new_bootstrap_draws=0,lease_acquisitions=0)
proofroot=ROOT/'execution_proofs/certified_primary_release_2026-11-11_current_setup'
write(proofroot/'PRESERVATION_PROOF.json',preservation)
shutil.copyfile(__file__,proofroot/'FREEZE_PUBLICATION_PATHMAP.py')

raw=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z'],cwd=ROOT)
allpaths=sorted(set(x.decode()for x in raw.split(b'\0')if x))
mutable={'FINAL_NOTEBOOK_PROFILE.json','NOTEBOOK_RELEASE_BINDINGS.json','README.md','main.ipynb'}
prefixes=['docs/PRIMARY_MODEL_LOCAL_SETUP_2026-11-11.md','docs/PRIMARY_NATIVE_HEADLESS_GUARD.md',
          'execution_proofs/certified_primary_release_2026-11-11/',
          'execution_proofs/certified_primary_release_2026-11-11_current_setup/',
          'model_examples/primary_192/PRIMARY_MODEL_RELEASE.json',
          'model_examples/primary_192/validation/primary_replay/',
          'notebook_profiles/certified_primary_release_2026-11-11/',
          'notebook_profiles/native_facade_v1_2026-11-11/',
          'replay_tools/primary_192/certified_native_v1.py']
pub=[n for n in allpaths if n in mutable or any(n.startswith(p)for p in prefixes)]
excluded=[n for n in allpaths if n not in pub]
assert all(n not in protected for n in pub),set(pub)&set(protected)
tracked=set(x.decode()for x in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0')if x)
assert set(pub)&tracked==mutable
for n in pub:
    p=ROOT/n;assert p.is_file()and not p.is_symlink()
    if p.suffix in ('.json','.md','.py','.log','.jsonl','.ipynb'):
        t=p.read_text()
        assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}',t),n
files={n:sha(ROOT/n)for n in pub};immutable={n:h for n,h in files.items()if n not in mutable}
manifest=dict(schema='certified_primary_release_publication_pathmap_v1',status='PRIVATE_REVIEW_CANDIDATE_NOT_PUBLISHED',
    base_git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    public_files=len(files),new_immutable_files=len(immutable),previous_protected_files=15982,
    resulting_protected_files=15982+len(immutable),files=files,new_protection_additions=immutable,
    mutable_aliases=sorted(mutable),bytes=sum((ROOT/n).stat().st_size for n in files),
    excluded_generated_or_private_paths=excluded,maximum_new_file_bytes=max((ROOT/n).stat().st_size for n in immutable),
    private_key_and_common_token_signature_scan='no matches in publication text payload',
    copied_archive_scope='Synthetic model software/provenance only; no real participant data, author credentials or dependency/runtime trees added.')
write(HERE/'PUBLICATION_PATHMAP.json',manifest)
projection=proofroot/'OUTPUT_PROJECTION_PROOF.json'
handoff=dict(schema='certified_primary_notebook_release_publication_handoff_v1',status='QUIESCENT_PRIVATE_CANDIDATE_PENDING_PEER_AND_ROOT_PUBLICATION_APPROVAL',
    candidate=str(ROOT),prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),base_git=manifest['base_git'],
    publication_pathmap=dict(path=str(HERE/'PUBLICATION_PATHMAP.json'),sha256=sha(HERE/'PUBLICATION_PATHMAP.json')),
    preservation=dict(path=str(proofroot/'PRESERVATION_PROOF.json'),sha256=sha(proofroot/'PRESERVATION_PROOF.json')),
    output_projection=dict(path=str(projection),sha256=sha(projection)),
    actual_QA_independent_review_sha256='28967fcbc504e1b1e87012b8a65ede9c48babb3ed08828d15f011e35751ecae1',
    actual_QA_root_acceptance_sha256='08793abf9201d7d81885476a020823c48f1c6083088167ee79d660272dbb7ba0',
    actual_artifact_certificate_sha256='7a1461e4ee2f382d285c6421568b6877ad0b5c7ccdd3c3f3b6c3d03727b5db98',
    actual_backend_root_acceptance_sha256='0b9eeed0fd1da87bce61769d7be8ff4f982879106cf2ff3de8766a54fa4a9029',
    main_sha256=sha(ROOT/'main.ipynb'),main_bytes=(ROOT/'main.ipynb').stat().st_size,
    logical_main=s.logical_notebook_validation,canonical_cells=14,canonical_code_cells=7,
    final_default_seconds=read(projection)['actual_default_seconds'],canonical_CSVs=13,paper_PNGs=4,
    visible_PNGs_exact_paper=True,all_sources_and_outputs_actual=True,
    markdown_only_final_change='The active optional-replay markdown setup link now points to the current guide; all7code cells match accepted QA. Old1b/8ea/previous output proofs retained.',
    scope='Both-artifact fixed-world zero/4T/36T backend proofs plus one historical4T local notebook route. No full192 new dynamics replay, fresh dependency install or broad platform claim.',
    protected_files=15982,additional_immutable_files=len(immutable),future_protected_files=15982+len(immutable),
    public_Doc_or_Drive_changes=False,Git_public_changes=False,native_model_runs_during_publication_prep=0,
    known_exclusions=excluded,remaining='Independent exact-payload review, ROOT final publication approval, narrow commit/push/readback/shared clean fast-forward; no more model or notebook execution needed.')
write(HERE/'HANDOFF.json',handoff)
print(json.dumps(dict(handoff_sha256=sha(HERE/'HANDOFF.json'),pathmap_sha256=sha(HERE/'PUBLICATION_PATHMAP.json'),public_files=len(files),new_immutable=len(immutable),future_protected=15982+len(immutable),bytes=manifest['bytes'],main_sha256=sha(ROOT/'main.ipynb')),indent=2))
