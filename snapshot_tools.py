"""Append evidence snapshots without replacing prior sealed inputs; zero model steps.

Maintainer utility, not part of a professor's Run All workflow. Case inventories
and input manifests are explicitly versioned. Existing evidence must match its
old hashes before any additive snapshot can be produced.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_new(path,value):
    path=Path(path)
    if path.exists():raise FileExistsError(f'Preserve existing snapshot: {path.name}')
    path.write_text(json.dumps(value,indent=2)+'\n')


def verify_case(folder):
    folder=Path(folder);seal=read(folder/'completion.json')
    if seal['status']!='complete':raise ValueError(f'Incomplete case: {folder.name}')
    for name,digest in seal['files'].items():
        if sha(folder/name)!=digest:raise ValueError(f'Changed case file: {folder.name}/{name}')
    if read(folder/'summary.json')['status']!='complete' or read(folder/'audit.json')['status']!='passed':
        raise ValueError(f'Case status/audit failed: {folder.name}')
    return seal


def append_study(*,source_study,previous_inventory,version,expected_cases,case_subdir="results/full_36T_v1/cases"):
    """Copy complete case directories additively; never rewrite sealed files."""
    source_study=Path(source_study).resolve()
    relative_cases=Path(case_subdir)
    if relative_cases.is_absolute() or '..' in relative_cases.parts:raise ValueError('case_subdir must stay within the selected study')
    cases=sorted((source_study/relative_cases).glob('*'))
    cases=[p for p in cases if p.is_dir()]
    if len(cases)!=expected_cases:raise ValueError('Require the complete declared case matrix')
    for folder in cases:verify_case(folder)
    inventory=read(ROOT/previous_inventory)
    inventory.update(schema=2,version=version,previous_dataset=previous_inventory)
    entries=list(inventory['cases']);known={e['relative_path'] for e in entries}
    for folder in cases:
        destination=ROOT/'data/research'/source_study.name/relative_cases/folder.name
        if destination.exists():
            verify_case(destination)
            if sha(destination/'completion.json')!=sha(folder/'completion.json'):
                raise ValueError('Existing case has a different seal; use a separately named study')
        else:
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(folder,destination)
        relative=str(destination.relative_to(ROOT))
        if relative in known:continue
        entry=dict(study=source_study.name,case=folder.name,relative_path=relative,
            completion_sha256=sha(destination/'completion.json'))
        horizon_seals=sorted(destination.glob('checkpoint_*T.seal.json'))
        if horizon_seals:entry['horizon_seals']={p.name:sha(p) for p in horizon_seals}
        entries.append(entry);known.add(relative)
    inventory['cases']=entries;inventory['case_count']=len(entries)
    output=ROOT/f'DATASET_{version}.json';write_new(output,inventory);return output


def create_manifest(*,previous_manifest,inventory,version,extras):
    previous=read(ROOT/previous_manifest)
    for name,digest in previous['files'].items():
        if sha(ROOT/name)!=digest:raise ValueError(f'Prior protected input changed: {name}')
    paths=set(previous['files'])|{previous_manifest,inventory}
    for relative in extras:
        path=ROOT/relative
        if not path.exists():raise FileNotFoundError(relative)
        selected=path.rglob('*') if path.is_dir() else [path]
        for item in selected:
            if not item.is_file() or '__pycache__' in item.parts or item.suffix=='.pyc':continue
            paths.add(str(item.relative_to(ROOT)))
    manifest=dict(schema=2,version=version,previous_manifest=previous_manifest,inventory=inventory,
        note='Additive evidence snapshot; original case files/manifests remain byte-identical. Generated outputs are mutable.',
        files={name:sha(ROOT/name) for name in sorted(paths)})
    output=ROOT/f'INPUT_MANIFEST_{version}.json';write_new(output,manifest);return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--previous-inventory',default='DATASET.json')
    parser.add_argument('--source-study',type=Path)
    parser.add_argument('--expected-cases',type=int)
    parser.add_argument('--case-subdir',default='results/full_36T_v1/cases')
    parser.add_argument('--previous-manifest',default='INPUT_MANIFEST.json')
    parser.add_argument('--inventory')
    parser.add_argument('--extra',nargs='*',default=[])
    args=parser.parse_args()
    if args.source_study:
        if args.expected_cases is None:parser.error('--source-study requires --expected-cases')
        inventory=append_study(source_study=args.source_study,previous_inventory=args.previous_inventory,
            version=args.version,expected_cases=args.expected_cases,case_subdir=args.case_subdir)
        print(inventory.name)
    else:
        if not args.inventory:parser.error('Manifest creation requires --inventory')
        print(create_manifest(previous_manifest=args.previous_manifest,inventory=args.inventory,
            version=args.version,extras=args.extra).name)

if __name__=='__main__':main()
