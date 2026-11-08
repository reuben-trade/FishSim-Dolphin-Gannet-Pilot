"""Native-free evidence analysis and figure reproduction for the local notebook.

Nothing in this module imports the fish simulator or advances model time.
Optional simulation is launched explicitly through run_model.py in a subprocess.
"""
from __future__ import annotations

import ast
import csv
import gzip
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT/'data/research'
DEVELOPMENT = 'simple_herd_strike_pilot_2026-11-08'
REPLICATION = 'exposed_replication_2026-11-08'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_inputs():
    manifest = read(ROOT/'INPUT_MANIFEST.json')
    for name,digest in manifest['files'].items():
        path = ROOT/name
        if not path.is_file() or sha(path)!=digest:
            raise ValueError(f'Frozen input changed or is missing: {name}')
    inventory = read(ROOT/'DATASET.json')
    if len(inventory['cases'])!=16 or inventory['older_C_policy_cases_included']:
        raise ValueError('Expected exactly eight development and eight fresh-replication cases')
    for entry in inventory['cases']:
        folder = ROOT/entry['relative_path']
        seal = read(folder/'completion.json')
        if sha(folder/'completion.json')!=entry['completion_sha256'] or seal['status']!='complete':
            raise ValueError(f'Case seal differs: {entry["case"]}')
        for name,digest in seal['files'].items():
            if sha(folder/name)!=digest:
                raise ValueError(f'Case file differs: {entry["case"]}/{name}')
    return dict(status='passed',validated_cases=16,protected_files=len(manifest['files']),
                studies=['development: 8 cases','fresh replication: 8 cases'],native_steps=0)


def case_rows():
    """Derive feeding outcomes from actual oral events and sealed summaries."""
    rows = []
    for entry in read(ROOT/'DATASET.json')['cases']:
        folder = ROOT/entry['relative_path'];summary = read(folder/'summary.json')
        config = read(folder/'config.json');audit = read(folder/'audit.json')
        if summary['status']!='complete' or audit['status']!='passed':
            raise ValueError(f'Unvalidated case: {entry["case"]}')
        if abs(summary['actual_duration']-36.)>1e-7 or summary['native_steps']!=28800:
            raise ValueError('A bundled paper case is not a full 36T encounter')
        with gzip.open(folder/'events.jsonl.gz','rt') as handle:
            events = [json.loads(line) for line in handle]
        captured = [e for e in events if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
        if len({e['prey_id'] for e in captured})!=len(captured):
            raise ValueError('A prey was captured twice')
        counts = {species:sum(e['actor_id'].startswith(species) for e in captured) for species in 'DG'}
        for species in 'DG':
            if counts[species]!=summary['species'][species]['captures']:
                raise ValueError('Recorded captures differ from case summary')
        d = summary['species']['D']
        rows.append(dict(study='development' if entry['study']==DEVELOPMENT else 'replication',
            school=summary['school_seed'],capture_seed=summary['capture_seed'],policy=summary['policy'],
            presence=config['presence'],dolphin_captures=counts['D'],gannet_captures=counts['G'],
            dolphin_launches=d['launches'],dolphin_contacts=d['contacts'],
            captures_per_launch=d['captures']/d['launches'] if d['launches'] else None,
            captures_per_dolphin_per_T=d['captures']/(12*summary['actual_duration']),
            final_live_fish=summary['final_count'],duration_T=summary['actual_duration'],
            folder=str(folder.relative_to(ROOT))))
    return sorted(rows,key=lambda r:(r['study'],r['school'],r['capture_seed'],r['policy'],r['presence']))


def paired_rows(rows, study):
    selected = [r for r in rows if r['study']==study]
    keys = sorted({(r['school'],r['capture_seed'],r['policy']) for r in selected})
    by = {(r['school'],r['capture_seed'],r['policy'],r['presence']):r for r in selected}
    result = []
    for school,capture,policy in keys:
        alone,mixed = (by[(school,capture,policy,p)] for p in ('D','DG'))
        a,b = alone['dolphin_captures'],mixed['dolphin_captures']
        result.append(dict(school=school,capture_seed=capture,policy=policy,D=a,DG=b,
            difference=b-a,change_percent=100*(b-a)/a if a else None,
            launches_D=alone['dolphin_launches'],launches_DG=mixed['dolphin_launches'],
            yield_D=alone['captures_per_launch'],yield_DG=mixed['captures_per_launch']))
    # The paper's preserved CSV is independently checked against raw events.
    name = DEVELOPMENT if study=='development' else REPLICATION
    with (DATA/name/'results/analysis_final/paired_comparison.csv').open(newline='') as handle:
        recorded = list(csv.DictReader(handle))
    if len(recorded)!=len(result):
        raise ValueError('Stored paper table has the wrong pair count')
    for expected in result:
        matches = [r for r in recorded if int(r['school_seed'])==expected['school']
            and r['policy']==expected['policy']
            and int(r.get('capture_seed',61001))==expected['capture_seed']]
        if len(matches)!=1 or int(matches[0]['dolphin_food_alone'])!=expected['D'] \
                or int(matches[0]['dolphin_food_with_gannets'])!=expected['DG']:
            raise ValueError('Paper table differs from the sealed raw outcomes')
    return result


def school_means(replication_pairs):
    result = []
    for school in sorted({r['school'] for r in replication_pairs}):
        group = [r for r in replication_pairs if r['school']==school]
        if {r['capture_seed'] for r in group}!={61001,61002}:
            raise ValueError('Both repeated capture seeds are required for a school mean')
        result.append(dict(school=school,repeated_streams=2,
            mean_D=statistics.mean(r['D'] for r in group),mean_DG=statistics.mean(r['DG'] for r in group),
            mean_difference=statistics.mean(r['difference'] for r in group),
            positive_repetitions=sum(r['difference']>0 for r in group)))
    return result


def print_table(rows, columns=None):
    """HTML in Jupyter; a readable text table in a plain Python execution."""
    if not rows:
        print('No rows.');return
    columns = columns or list(rows[0])
    def formatted(value):
        if value is None:return '—'
        if isinstance(value,float):return f'{value:.4g}'
        return str(value)
    values = [[formatted(row.get(k)) for k in columns] for row in rows]
    try:
        from IPython import get_ipython
        from IPython.display import HTML, display
        if get_ipython() is None:raise ImportError
    except ImportError:
        widths = [max(len(str(k)),*(len(row[i]) for row in values)) for i,k in enumerate(columns)]
        print(' | '.join(str(k).ljust(w) for k,w in zip(columns,widths)))
        print('-+-'.join('-'*w for w in widths))
        for row in values:print(' | '.join(v.ljust(w) for v,w in zip(row,widths)))
    else:
        heading = '<tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in columns)+'</tr>'
        body = ''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in values)
        display(HTML('<table>'+heading+body+'</table>'))


def reproduce_figures(output=None):
    """Execute the exact paper plotting code against the bundled case data."""
    output = ROOT/'outputs/figures' if output is None else Path(output)
    spec = importlib.util.spec_from_file_location('_bundled_paper_figures',ROOT/'paper_figure_source.py')
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.DEVELOPMENT = DATA/DEVELOPMENT
    module.REPLICATION = DATA/REPLICATION
    module.OUT = output
    for function in (module.model_figure,module.development_figure,module.replication_figure,module.mechanism_figure):
        function()
    receipts = read(output/'figure_receipts.json')
    if set(receipts)!={'fig1_model','fig2_development','fig3_replication','fig4_mechanism'}:
        raise ValueError('Not all four figures were generated')
    return output


def show_figure(name, output=None):
    folder = ROOT/'outputs/figures' if output is None else Path(output)
    path = folder/(name+'.png')
    if not path.is_file():raise FileNotFoundError(path)
    try:
        from IPython import get_ipython
        from IPython.display import Image, display
        if get_ipython() is None:raise ImportError
    except ImportError:
        print(f'Figure written: {path.relative_to(ROOT)}')
    else:
        display(Image(filename=str(path)))


def source_excerpt(relative_path, qualified_name):
    path = ROOT/'frozen_model'/relative_path
    source = path.read_text();nodes = ast.parse(source).body
    node = None
    for name in qualified_name.split('.'):
        node = next((candidate for candidate in nodes if getattr(candidate,'name',None)==name),None)
        if node is None:raise ValueError(f'Source definition not found: {qualified_name}')
        nodes = getattr(node,'body',[])
    return '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])


def actual_parameter_table():
    case = DATA/REPLICATION/'results/full_36T_v1/cases/s39063501_exposed_DG_c61001'
    config = read(case/'config.json');actors = config['actors']
    d = next(a for a in actors if a['state']['species']=='D')
    g = next(a for a in actors if a['state']['species']=='G')
    settings = [('Initial fish',config['counts']['fish']),('Dolphins',config['counts']['D']),
        ('Gannets in DG',config['counts']['G']),('Native timestep T',config['dt']),
        ('Encounter duration T',config['duration']),('Continuous proximity requirement T',2.),
        ('Fish proximity radius',4.5),('Exposed neighbor radius',config['exposure_neighbour_radius']),
        ('Dolphin speed',d['config']['speed']),('Dolphin sensing radius',d['config']['sense_radius']),
        ('Maximum strike duration T',d['config']['bout_duration']),
        ('Successful handling T',d['config']['handling_duration']),
        ('Miss recovery T',d['config']['miss_recovery_duration']),
        ('Gannet detection depth',g['config']['detection_depth']),
        ('Gannet sensing radius (global approximation)',g['config']['sense_radius']),
        ('Conditional oral-contact success',d['capture_probability'])]
    return [dict(parameter=k,value=v) for k,v in settings]


def native_environment():
    """Static compatibility report; does not load the extension."""
    record = read(ROOT/'DATASET.json')['native_binary']
    libc_name,libc_version = platform.libc_ver()
    try:glibc = tuple(int(v) for v in libc_version.split('.')[:2])
    except ValueError:glibc = ()
    eligible = (sys.implementation.name=='cpython' and sys.version_info[:2]==(3,12)
        and sys.platform.startswith('linux') and platform.machine().lower() in ('x86_64','amd64')
        and libc_name=='glibc' and glibc>=(2,43))
    return dict(python=platform.python_version(),system=platform.system(),machine=platform.machine(),
        libc=f'{libc_name} {libc_version}',eligible_for_native_import_check=eligible,
        native_loaded=False,native_steps=0,binary_sha256=record['sha256'],
        note='An explicit optional run also checks the actual native import and dependent libraries. Analysis and figures do not need this binary.')


def export_tables(rows, development_pairs, replication_pairs):
    folder = ROOT/'outputs/tables';folder.mkdir(parents=True,exist_ok=True)
    for name,values in (('case_outcomes',rows),('development_pairs',development_pairs),
                        ('replication_pairs',replication_pairs),('replication_school_means',school_means(replication_pairs))):
        with (folder/(name+'.csv')).open('w',newline='') as handle:
            writer = csv.DictWriter(handle,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    print(f'Four tables exported to {folder.relative_to(ROOT)}')


def new_run_table(folder):
    rows = []
    for path in sorted((Path(folder)/'cases').glob('*/summary.json')):
        summary = read(path);config = read(path.with_name('config.json'))
        rows.append(dict(school=summary['school_seed'],capture_seed=summary['capture_seed'],
            presence=config['presence'],duration_T=summary['actual_duration'],
            D_captures=summary['species']['D']['captures'],G_captures=summary['species']['G']['captures'],
            native_steps=summary['native_steps']))
    return rows
