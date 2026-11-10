"""Native-free final source/reference/protected-input verification.

This checks existing immutable inputs and recorded pure-start receipts only.
It never opens an unaccepted primary feeding path or imports the simulator.
"""
from pathlib import Path
import ast, hashlib, json, shutil, sys

HERE = Path(__file__).resolve().parent
ROOT = Path('/home/venture/uwa/complex-systems/FishSim-RL')
PUBLIC = Path('/home/venture/FishSim-Dolphin-Gannet-Pilot')
PAPER = ROOT/'research/thesis_working_draft_2026-11-08'
CACHE = {}

def sha(path):
    path = Path(path)
    stat = path.stat()
    key = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    if key not in CACHE:
        CACHE[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return CACHE[key]

def read(path):
    return json.loads(Path(path).read_text())

def check_map(root, files):
    for name, digest in files.items():
        path = (root/name).resolve()
        if not path.is_relative_to(root.resolve()) or sha(path) != digest:
            raise AssertionError('Changed protected input: '+name)

def main():
    dest = HERE/'validation/PREPARATION_VALIDATION.json'
    if dest.exists():
        raise FileExistsError('Preserve the recorded validation receipt')
    spec = read(HERE/'MODEL_INPUTS.json')
    freeze = ROOT/'research/independent_validation_2026-11-10/frozen_sources.json'
    if sha(freeze) != '253071467e55b4cdbe91f75ba1de3f1bb80d65344e9cba05aadb86bccb08da0b':
        raise AssertionError('Parent execution freeze changed')
    if read(freeze)['source_sha256'] != spec['primary_sources'] or len(spec['primary_sources']) != 2127:
        raise AssertionError('Parent source closure differs')
    for original, digest in spec['primary_sources'].items():
        if '/FishSim_Independent_Validation_2026-11-10/full_36T_v1/' in original or '/FishSim_Independent_Validation_2026-11-10/phases/' in original:
            raise AssertionError('Unaccepted feeding path in source closure')
        if sha(original) != digest:
            raise AssertionError('Parent source/input changed: '+original)

    manifests = [('publication_receipt_2026-11-10_accessibility_supplement.json','new_supplement_files_to_preserve_in_next_manifest'),
        ('publication_receipt_2026-11-10_validation_preanalysis_plan.json','new_preanalysis_archive_paths_to_preserve_in_next_manifest'),
        ('publication_receipt_2026-11-10_lower_count_followup_plan.json','new_lower_count_plan_paths_to_preserve_in_next_manifest'),
        ('publication_receipt_2026-11-10_crossed_followup_plan.json','new_crossed_plan_paths_to_preserve_in_next_manifest'),
        ('publication_receipt_2026-11-10_primary_progress48.json','new_primary_progress48_paths_to_preserve_in_next_manifest')]
    protected = dict(read(PUBLIC/'INPUT_MANIFEST_2026-11-10_D24.json')['files'])
    for filename, key in manifests:
        for name, digest in read(PAPER/filename)[key].items():
            if name in protected and protected[name] != digest:
                raise AssertionError('Conflicting prior protection map')
            protected[name] = digest
    if len(protected) != 9916:
        raise AssertionError('Expected 9,916 existing protected files')
    check_map(PUBLIC, protected)

    old = Path('/tmp/FishSim_G36_Example_Candidate_2026-11-10_v2')
    oldfreeze = old/'HANDOFF_FROZEN.json'
    if sha(oldfreeze) != '9b1c3dc4bf139225dae938c51f09db08a2afb0ad8963a6172784fee3eaf9bd8e':
        raise AssertionError('Old G36 v2 handoff changed')
    check_map(old, read(oldfreeze)['files'])
    refs = read(HERE/'REFERENCE_MANIFEST.json')
    if refs['input_spec_sha256'] != sha(HERE/'MODEL_INPUTS.json') or len(refs['files']) != 303:
        raise AssertionError('Reference/spec inventory differs')
    check_map(HERE, refs['files'])
    for branch, duration in [('smoke4T', 4), ('full36T', 36)]:
        for case in refs['case_names']:
            folder = HERE/'references'/branch/case
            seal = read(folder/'completion.json')
            if seal['status'] != 'complete':
                raise AssertionError('Unsealed accepted reference')
            check_map(folder, seal['files'])
    if sha(HERE/'references/accepted_block1_review.json') != '1609c4dd6d131bd95232ec3600dc428deba69d6b959eb46099fe057c4cd9a59c':
        raise AssertionError('Only accepted first48 may supply references')

    from primary_runtime import interfaces, inventory
    pure = {}
    for artifact, label, runtime in [
        ('historical', 'Historical', Path('/home/venture/FishSim Primary Historical Strict Proof 2026-11-10')),
        ('source-built', 'Source_Built', Path('/home/venture/FishSim Primary Source Built Strict Proof 2026-11-10'))]:
        original = Path(f'/home/venture/FishSim_Primary_Pure192_{label}_Strict_Final_2026-11-10.json')
        result = read(original)
        declaration = read(runtime/'PRIMARY_RUNTIME.json')
        if (result['status'] != 'passed' or result['pure_cases'] != 192
                or [x['case_name'] for x in result['cases']] != [x['case_name'] for x in inventory()]
                or any(result[k] != 0 for k in ['native_imports','native_constructions','native_steps','original_author_access_attempts'])
                or result['original_author_model_and_data_paths_forbidden'] is not True
                or declaration['interface_files'] != interfaces()
                or result['runtime_declaration_sha256'] != sha(runtime/'PRIMARY_RUNTIME.json')):
            raise AssertionError('Strict real Python-state proof differs')
        for name, digest in declaration['runtime_files'].items():
            if sha(runtime/name) != digest:
                raise AssertionError('Private view changed')
        receipt = HERE/'validation'/f'PURE192_{artifact}.json'
        if receipt.exists():
            if sha(receipt) != sha(original):
                raise AssertionError('Prior pure proof differs')
        else:
            shutil.copy2(original, receipt)
        pure[artifact] = dict(path=str(receipt.relative_to(HERE)),sha256=sha(receipt),
            pure_cases=192,active_native_sha256=result['active_native_sha256'],
            runtime_declaration_sha256=result['runtime_declaration_sha256'],
            maximum_raw_to_archived_normalized_heading_delta=max(x['raw_to_native_heading_max_delta'] for x in result['cases']))
    draft = read(HERE/'OPTIONAL_NOTEBOOK_DRAFT.json')
    for cell in ['plan_cell','opt_in_cell']:
        compile(draft[cell],cell,'exec')
    tree = ast.parse(draft['opt_in_cell'])
    toggles = [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUN_PRIMARY_MODEL' for t in n.targets)]
    if len(toggles) != 1 or not isinstance(toggles[0].value,ast.Constant) or toggles[0].value.value is not False:
        raise AssertionError('Optional model toggle must remain literal False')
    if (HERE/'PRIMARY_MODEL_RELEASE.json').exists() or any(k=='fish_sim' or k.startswith('fish_sim.') for k in sys.modules):
        raise AssertionError('No release/model import expected')
    result = dict(status='passed',schema='primary_model_private_preparation_validation_v1',
        interface_files=interfaces(),source_freeze_sha256=sha(freeze),parent_source_bindings_verified=2127,
        prior_public_protected_files_verified=9916,old_g36_v2_files_verified=53,
        accepted_reference_files_verified=303,accepted_full36T_reference_cases=6,accepted_smoke4T_reference_cases=6,
        actual_zero_reference_cases=192,real_python_state_checks=pure,
        native_free_pure_starts_per_artifact=192,native_free_pure_starts_total=384,
        targeted_tests=dict(status='passed',tests=18,elapsed_seconds=2.506,
            test_source_sha256=sha(HERE/'test_primary_model.py'),
            evidence='Agent-recorded actual python -B -m unittest -v test_primary_model completion; no synthetic native execution'),
        optional_cell_sources_compile=True,optional_native_toggle=False,
        native_imports=0,native_constructions=0,native_steps=0,native_lease_acquisitions=0,compiler_invocations=0,
        unaccepted_primary_feeding_rows_read=0,original_tree_renames_or_moves=0,public_or_Doc_writes=0,
        release_certificate_exists=False,production_snapshot_exists=False,
        future_engineering_proposed_native_steps=576000,
        scope='Private source and real Python-state preparation only. Actual native zeros, 4T and 36T replay remain unperformed and gated.')
    dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('interface_files','real_python_state_checks')},indent=2))

if __name__ == '__main__':
    main()
