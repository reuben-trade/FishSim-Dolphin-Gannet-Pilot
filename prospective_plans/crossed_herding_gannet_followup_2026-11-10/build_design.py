"""Native-free prospective inventory only; no model imports or execution code."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIMARY = ROOT/'research/independent_validation_2026-11-10'
LOWER = ROOT/'research/independent_lower_count_validation_2026-11-10'
BULK = Path('/home/venture/FishSim_Crossed_Followup_2026-11-10')
PRIMARY_BULK = Path('/home/venture/FishSim_Independent_Validation_2026-11-10')
LOWER_BULK = Path('/home/venture/FishSim_Lower_Count_Validation_2026-11-10')
SEEDS = tuple(range(39065501, 39065517))
LABELS = (71001, 71002)
GRIDS = dict(coarse=.00125, fine=.000625)
NEW_CELLS = ((1, 12), (2, 36))


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(name, value):
    path = HERE/name
    with path.open('x') as handle: handle.write(json.dumps(value, indent=2)+'\n')
    return path
def table(name, rows):
    path = HERE/name
    with path.open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return path


def identity(school, label, grid, presence, h=None, g=0):
    policy = f'H{h}_G{g}' if 'D' in presence else f'Gonly{g}'
    return f's{school}_{grid}_{policy}_{presence}_c{label}'


def existing_reference(school, label, grid, presence, h=None, g=0):
    primary = (presence == 'D' and h == 1) or (presence == 'G' and g == 36) or (presence == 'DG' and (h, g) == (1, 36))
    lower = (presence == 'D' and h == 2) or (presence == 'G' and g == 12) or (presence == 'DG' and (h, g) == (2, 12))
    assert primary != lower
    source, bulk = (PRIMARY, PRIMARY_BULK) if primary else (LOWER, LOWER_BULK)
    name = identity(school, label, grid, presence, h, g)
    return dict(source_study=source.name, source_case_id=name,
                source_case_path=str(bulk/'full_36T_v1/cases'/name),
                source_execution_freeze_sha256='253071467e55b4cdbe91f75ba1de3f1bb80d65344e9cba05aadb86bccb08da0b' if primary else '',
                source_completion_sha256='', reuse_status='PENDING_BOTH_COMPLETE_INDEPENDENT_FINAL_AUDITS')


def build():
    # These are sealed input descriptors, not feeding outcomes.
    parent_path = PRIMARY/'PURE_PREFLIGHT.json'; lower_path = LOWER/'case_inventory.csv'
    assert sha(parent_path) == '9bed5786175bbbf16a8fe6a875fefa8090538f2e4c7f8d1e42d63e95f7ab0798'
    assert sha(lower_path) == '30226fd37072324e32eb60b1c512f7d71eb01ae34cf08f21b944dbda89233d27'
    primary_plans = {r['case_name']: r for r in read(parent_path)['rows']}
    with lower_path.open(newline='') as handle: lower_plans = {r['case_name']: r for r in csv.DictReader(handle)}
    plans = {PRIMARY.name: primary_plans, LOWER.name: lower_plans}
    new, controls, paired, unique_controls, unique_bank = [], [], [], set(), set()
    for school in SEEDS:
        for label in LABELS:
            for grid, dt in GRIDS.items():
                common = dict(school_seed=school, replicate_label=label, capture_label=label, grid=grid, dt=dt)
                mapping = dict(common)
                for h in (1, 2):
                    ref = existing_reference(school, label, grid, 'D', h, 0)
                    planned = plans[ref['source_study']][ref['source_case_id']]
                    assert int(planned['school_seed']) == school and int(planned['capture_seed']) == label
                    assert planned['presence'] == 'D' and float(planned['herding_minimum_T']) == h
                    assert float(planned['dt']) == dt and int(planned['dolphins']) == 12 and int(planned['gannets']) == 0
                    mapping[f'D_only_H{h}_study'] = ref['source_study']
                    mapping[f'D_only_H{h}_case_id'] = ref['source_case_id']
                    mapping[f'D_only_H{h}_path'] = ref['source_case_path']
                    unique_controls.add((ref['source_study'], ref['source_case_id'])); unique_bank.add((ref['source_study'], ref['source_case_id']))
                for g in (12, 36):
                    ref = existing_reference(school, label, grid, 'G', None, g)
                    planned = plans[ref['source_study']][ref['source_case_id']]
                    assert int(planned['school_seed']) == school and int(planned['capture_seed']) == label
                    assert planned['presence'] == 'G' and float(planned['dt']) == dt
                    assert int(planned['dolphins']) == 0 and int(planned['gannets']) == g
                    mapping[f'G_only_G{g}_study'] = ref['source_study']
                    mapping[f'G_only_G{g}_case_id'] = ref['source_case_id']
                    mapping[f'G_only_G{g}_path'] = ref['source_case_path']
                    unique_controls.add((ref['source_study'], ref['source_case_id'])); unique_bank.add((ref['source_study'], ref['source_case_id']))
                for h in (1, 2):
                    for g in (12, 36):
                        name = identity(school, label, grid, 'DG', h, g)
                        if (h, g) in NEW_CELLS:
                            study, path = HERE.name, str(BULK/'full_36T_v1/cases'/name)
                            row = dict(common, case_name=name, case_id=name, capture_seed=label,
                                       presence='DG', herding_minimum_T=h, dolphins=12, gannets=g, initial_fish=160,
                                       duration_T=36, maximum_native_steps=round(36/dt),
                                       block=(school-SEEDS[0])//4+1, proposed_case_path=path,
                                       execution_status='PLANNED_NOT_AUTHORISED')
                            new.append(row)
                            d = existing_reference(school, label, grid, 'D', h, 0)
                            bird = existing_reference(school, label, grid, 'G', None, g)
                            controls.append(dict(common, mixed_case_id=name, herding_minimum_T=h, gannets=g,
                                                 **{'D_'+k: v for k, v in d.items()}, **{'G_'+k: v for k, v in bird.items()}))
                        else:
                            ref = existing_reference(school, label, grid, 'DG', h, g)
                            planned = plans[ref['source_study']][ref['source_case_id']]
                            assert float(planned['herding_minimum_T']) == h and int(planned['gannets']) == g
                            assert float(planned['dt']) == dt
                            study, path = ref['source_study'], ref['source_case_path']
                        mapping[f'DG_H{h}_G{g}_study'] = study
                        mapping[f'DG_H{h}_G{g}_case_id'] = name
                        mapping[f'DG_H{h}_G{g}_path'] = path
                        unique_bank.add((study, name))
                paired.append(mapping)
    assert len(new) == len({r['case_name'] for r in new}) == 128
    assert len(controls) == 128 and len(paired) == 64
    assert len(unique_controls) == 256 and len(unique_bank) == 512
    assert sum(r['maximum_native_steps'] for r in new) == 5529600
    smokes = [dict(row, duration_T=4, maximum_native_steps=round(4/row['dt']),
                   proposed_case_path=str(BULK/'smoke_4T_v1/cases'/row['case_name']),
                   included_in_estimation=False)
              for row in new if row['school_seed'] == SEEDS[0] and row['capture_label'] == LABELS[0]]
    assert len(smokes) == 4 and sum(r['maximum_native_steps'] for r in smokes) == 19200
    table('new_mixed_cases.csv', new); table('new_case_control_map.csv', controls)
    table('paired_control_map.csv', paired); table('engineering_smokes.csv', smokes)
    at = datetime.now(ZoneInfo('Australia/Perth')).isoformat()
    write('protocol.json', dict(status='prospective_native_free_design_only', created_at=at,
        authorised_scope='Case/reference tables and analysis design only; no native harness or execution',
        chronology='Designed after primary control runs began and before first complete paired feeding effects were inspected, as stated by root; designer has inspected no feeding outcomes.',
        conditions=dict(H=[1, 2], G=[12, 36], D=12, fish=160, q_eligible_contact=.7),
        new_mixed_cells=[dict(H=h, G=g) for h, g in NEW_CELLS],
        existing_mixed_cells=[dict(H=1, G=36, study=PRIMARY.name), dict(H=2, G=12, study=LOWER.name)],
        schools=list(SEEDS), labels=list(LABELS), grids=GRIDS, duration_T=36,
        new_full_cases=128, new_full_step_ceiling=5529600, engineering_smokes=4,
        smoke_duration_T=4, smoke_step_ceiling=19200, new_preparation_steps=0, total_new_step_ceiling=5548800,
        independent_school_clusters=16, stochastic_worlds=32, world_grid_pairs=64,
        existing_unique_full_cases=384, final_unique_full_case_bank=512, unique_control_cases=256,
        aliases='D-only reused across bird counts withinH; G-only reused acrossH within bird count. References are not new runs or independent samples.',
        initialisation='Exact same16 accepted20T schools and original school/label/stable-ID private streams. G0-G11 nested withinG0-G35 at the same3 launch sites; four versus twelve point birds/site. No added coverage/spacing/timing parameter.',
        unchanged_model='Original committed physical/contact/controller/gannet helpers, q.7 and per-dolphin herd-strike rule; only declaredH/G inputs vary.',
        queued_order='Only after BOTH192-case studies pass complete independent FINAL evidence audits, regardless of effect signs. Fresh finite root authority, source/input/actual-start/engineering/feeding gates required.',
        control_binding='Future harness must bind exact source_case_id, grid/label/H/G metadata, source execution freeze, completion seal and independent FINAL receipt. Empty completion/future-lower-freeze fields are pending, never fabricated.',
        selection_rule='All128 new full cases mandatory; no dropping, replacements, early success or outcome-selected settings.',
        scheduling_proposal='Four fixed four-school blocks, both labels, coarse then fine, fixedH1/G12 thenH2/G36 waves; at most8 workers and one numerical thread each.',
        future_bulk=str(BULK), future_execution_authority=None, native_imports_authorised=0,
        native_constructions_authorised=0, native_steps_authorised=0, native_lease_authorised=False,
        compiler_invocations_authorised=0, publication_authorised=False))
    write('analysis_plan.json', dict(status='prospective_secondary_estimation_design',
        fine_analysis_grid=.000625, coarse_sensitivity_grid=.00125,
        independent_unit='School: average both labels within each of16 shared schools before any SE or interval; never pool into32schools.',
        units='Fish captured per individual over nominal36T; D denominator12; G denominator12or36; rates divide by36 separately.',
        cell_effect_D='(mixed_D(H,G)-D_only(H))/12',
        cell_effect_G='(mixed_G(H,G)-G_only(G))/G',
        school_cell_effect='Average the two matched labelled-world cell effects within school.',
        count_contrast='E(H,36)-E(H,12), separately atH1 andH2, within school.',
        herding_contrast='E(2,G)-E(1,G), separately atG12 andG36, within school.',
        interaction='E(2,36)-E(2,12)-E(1,36)+E(1,12), within school.',
        integer_arithmetic='Use common world denominator36: D numerator3*(mixed-control), G numerator(36/G)*(mixed-control); sum2labels gives school denominator72. Form all contrasts on integer numerators before division, preserving exact zeros/control cancellations.',
        summary='Mean16 school contrasts; sampleSD(ddof1); SE=SD/4;95% pointwise Student-tCI mean+-2.131449545559776*SE(df15).',
        confidence=.95, df=15, t_critical=2.131449545559776,
        interval_role='Descriptive pointwise estimates; no simultaneous coverage or new confirmatory family.',
        endpoint_vector='For each species:4cell effects+2count contrasts+2herding contrasts+1interaction=9. Full18-vector atfine/coarse and school-paired fine-minus-coarse.',
        automated_success_decision=None, bootstrap=None,
        existing_inference='Retain original H1/G36 primary97.5% criterion and predeclared four-endpoint programme98.75% analysis unchanged. New cells cannot rescue/replace either.',
        raw_reporting='All school/world points and signs; separate group totals, per-individual food and nominal-time rates. No zero imputation for missing cases; coherent absorbing depletion retains nominal36T.',
        interpretation='Separates modelH and bird-count effects at these two tested levels, including interaction. Bird count changes local multiplicity at3fixed sites; no biological causal validation, spatial-coverage claim or global optimum.'))
    return dict(new_full_cases=128, control_map_rows=128, paired_map_rows=64, unique_controls=256,
                final_unique_full_case_bank=512, new_full_steps=5529600, smoke_steps=19200, total_new_steps=5548800)


if __name__ == '__main__': print(json.dumps(build(), indent=2))
