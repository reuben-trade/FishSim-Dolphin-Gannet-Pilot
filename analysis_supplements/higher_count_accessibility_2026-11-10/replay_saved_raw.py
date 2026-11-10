"""Replay the archived accessibility analysis from mapped sealed public files.

No native simulator or controller is imported. This replays saved-data geometry,
not a feeding simulation. The archived author's source remains byte-identical.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUTHOR_SHA = '838ded0738594d3551ecfea17a491f4d3eaf3ac21d599cafd4ad63133c04d22f'
AUDIT_SHA = '28da54606449783e65d39106150e8269eabc99636be6621a5bb479d3aa6ce169'

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def safe_file(relative):
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'Unsafe mapped path')
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT), 'Mapped file escaped repository')
    return path

def verified_inputs():
    require(sha(HERE/'analyze.py') == AUTHOR_SHA, 'Archived analysis source changed')
    require(sha(HERE/'outputs/analysis_audit.json') == AUDIT_SHA, 'Frozen audit changed')
    mapping = json.loads((HERE/'INPUT_MAP.json').read_text())
    audit = json.loads((HERE/'outputs/analysis_audit.json').read_text())
    require(mapping['analysis_source_sha256'] == AUTHOR_SHA and mapping['analysis_audit_sha256'] == AUDIT_SHA, 'Input-map source binding mismatch')
    rows = mapping['inputs']
    require(mapping['input_count'] == len(rows) == 644, 'Expected all644 inputs')
    require({r['author_path']:r['sha256'] for r in rows} == audit['inputs'], 'Input map differs from archived audit')
    require(len({r['view_relative_path'] for r in rows}) == 644, 'Duplicate view paths')
    for row in rows:
        require(sha(safe_file(row['bundled_path'])) == row['sha256'], 'Changed input: '+row['bundled_path'])
        view = Path(row['view_relative_path'])
        require(not view.is_absolute() and '..' not in view.parts and view.parts[0] in {'old','high','upper','legacy'}, 'Unsafe temporary view path')
    for name,digest in audit['outputs'].items():
        require(Path(name).name == name and sha(HERE/'outputs'/name) == digest, 'Frozen CSV changed: '+name)
    return rows, audit

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New output directory; existing paths are never overwritten')
    parser.add_argument('--verify-only', action='store_true', help='Check644 input hashes and frozen outputs without replay')
    args = parser.parse_args()
    started = time.monotonic()
    sys.dont_write_bytecode = True
    rows, frozen = verified_inputs()
    if args.verify_only:
        print(json.dumps(dict(status='passed',inputs=644,native_steps=0,replayed=False),indent=2))
        return
    destination = args.output or ROOT/'outputs/higher_count_accessibility'/datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    destination = destination.resolve()
    require(not destination.exists(), 'Choose a new output directory; existing paths are preserved')
    destination.mkdir(parents=True, exist_ok=False)
    scratch = ROOT/'outputs'
    scratch.mkdir(exist_ok=True)
    links = copies = 0
    with tempfile.TemporaryDirectory(prefix='accessibility_view_',dir=scratch) as name:
        view = Path(name)
        for row in rows:
            source = safe_file(row['bundled_path'])
            target = view/row['view_relative_path']
            target.parent.mkdir(parents=True,exist_ok=True)
            try:
                os.link(source,target)
                links += 1
            except OSError:
                shutil.copyfile(source,target)
                copies += 1
        spec = importlib.util.spec_from_file_location('_archived_accessibility_analysis',HERE/'analyze.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.OLD, module.HIGH, module.UPPER, module.LEGACY = (view/'old',view/'high',view/'upper',view/'legacy')
        module.OUT = destination
        module.main()
        actual = json.loads((destination/'analysis_audit.json').read_text())
        require(actual['status']=='passed' and actual['analysis_source_sha256']==AUTHOR_SHA,'Reproduced audit failed')
        require((actual['bird_bearing_cases'],actual['paired_rows'],actual['regime_rows'],actual['original48_reconciled'])==(128,96,24,48),'Reproduced scope changed')
        require(actual['native_steps']==actual['simulation_module_imports']==actual['new_bootstrap_draws']==0,'Unexpected native or random work')
        expected_inputs = {str(view/r['view_relative_path']):r['sha256'] for r in rows}
        require(actual['inputs']==expected_inputs,'Replayed input view differs')
        for filename,digest in frozen['outputs'].items():
            require(sha(destination/filename)==digest,'Replayed CSV differs: '+filename)
        verified_inputs() # Check all source bytes again after the archived code ran.
    require(not any(n=='fish_sim' or n.startswith('fish_sim.') or n.endswith('.cmodel') for n in sys.modules),'Unexpected simulator module import')
    receipt = dict(status='passed',analysis_source_sha256=AUTHOR_SHA,frozen_audit_sha256=AUDIT_SHA,
        input_map_sha256=sha(HERE/'INPUT_MAP.json'),replayer_sha256=sha(__file__),input_files_verified=644,
        bird_bearing_cases=128,sampled_frames=46208,paired_rows=96,conditions=24,independent_previously_observed_schools=4,
        original48_reconciled=48,csv_files_byte_identical=frozen['outputs'],native_steps=0,native_simulator_imports=0,new_bootstrap_draws=0,
        hardlinks=links,copy_fallbacks=copies,temporary_view_removed=True,protected_source_bytes_unchanged=True,
        generated_audit_note='Its input paths name the deleted temporary view; INPUT_MAP.json maps each to durable bundled files by SHA256.',
        python=sys.version.split()[0],platform=sys.platform,seconds=time.monotonic()-started)
    (destination/'replay_validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__ == '__main__':
    main()
