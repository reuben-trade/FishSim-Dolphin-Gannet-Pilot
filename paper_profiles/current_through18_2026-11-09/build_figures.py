"""Replot completed FishSim records; never imports or executes the simulator.

Uncertainty endpoints are read from the saved analysis, without resampling.
Run with the existing FishSim-RL .venv Python (Matplotlib and NumPy).
"""
from pathlib import Path
import csv
import hashlib
import json
import os
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get('FISHSIM_FIGURE_OUTPUT', ROOT / 'outputs/reproduced_figures'))
BUNDLE = ROOT / '_no_repository_fallback'
SAVED = ROOT / 'saved_results'
PROVENANCE = json.loads((SAVED / 'provenance.json').read_text())['files'] if (SAVED / 'provenance.json').is_file() else {}
STUDY = BUNDLE / 'data/research/high_count_regime_extension_2026-11-09'
ANALYSIS = STUDY / 'results/full_36T_v1/analysis_final'
H = (1., 2., 3.)
G = (1, 3, 6, 9, 12, 18)
COLORS = ('#007C83', '#CA7C18', '#7957A0')
MARKERS = ('o', 's', '^')
INK = '#263746'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.labelsize': 8.5, 'axes.titlesize': 9.2,
    'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'legend.fontsize': 8, 'axes.spines.top': False,
    'axes.spines.right': False, 'pdf.fonttype': 42,
    'savefig.facecolor': 'white',
})
OUT.mkdir(exist_ok=True, parents=True)
inputs = set()
manifest = {'native_steps': 0, 'bootstrap_draws_generated': 0, 'figures': {}}


def localize(path):
    """Require the exact bundled summary; never read a mutable repository."""
    relative = path.relative_to(BUNDLE)
    bundled = SAVED / relative
    if not bundled.is_file():
        raise FileNotFoundError(f'Frozen V3 input is missing: {bundled}')
    return bundled


def read(path):
    inputs.add(path)
    return json.loads(localize(path).read_text())


def table(path):
    inputs.add(path)
    with localize(path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_record(path):
    relative = path.relative_to(BUNDLE).as_posix()
    actual = localize(path)
    digest = sha(actual)
    record = PROVENANCE.get(relative, {})
    if record:
        assert record['sha256'] == digest, f'Bundled source changed: {relative}'
    return {'path': record.get('original_path', str(path)), 'sha256': digest,
            'bundled_path': 'saved_results/' + relative if (SAVED / relative).is_file() else None,
            'read_from': 'bundled' if actual != path else 'repository'}


def save(fig, name, caption, data):
    for ext in ('png', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=260, bbox_inches='tight', pad_inches=.04)
    plt.close(fig)
    manifest['figures'][name] = {'caption': caption, 'plotted_data': data}


def style(ax, letter, title, ylabel):
    ax.set_title(f'({letter})  {title}', loc='left', pad=7)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', color='#E2E8ED', linewidth=.6)
    ax.set_axisbelow(True)
    ax.locator_params(axis='y', nbins=4)


rows = table(ANALYSIS / 'case_outcomes.csv')
pairs = table(ANALYSIS / 'paired_school_changes.csv')
summary = table(ANALYSIS / 'regime_summary.csv')
assert len(rows) == 108 and len(pairs) == 72 and len(summary) == 18
assert read(ANALYSIS / 'analysis_audit.json')['status'] == 'passed'
for row in rows:
    assert int(row['gannets']) in (0, *G)
    assert float(row['duration_T']) == 36.
    assert float(row['dt']) == .00125

# The pre-existing model illustration is already based on a fixed historical frame.
old = BUNDLE / 'reports/current/figures'
old_receipts = read(BUNDLE / 'reports/high_count_2026-11-09/figures/figure_receipts.json')
for ext in ('png', 'pdf'):
    source = old / f'fig1_model.{ext}'
    inputs.add(source)
    shutil.copy2(localize(source), OUT / source.name)
manifest['figures']['fig1_model'] = {
    'caption': ('The shared dolphin cycle and an illustrative encounter. Dolphins maintain near-prey '
                'pressure for H, select feasible prey with few neighbours, strike once, then recover. '
                'Top and side views show school 39061002 at 12T, with paths and captures over 6–12T. '
                'Horizontal coordinates are relative to the live-fish centroid; z=0 is the surface. '
                'The historical frame is illustrative, not evidence of completed herding or causal mediation.'),
    'plotted_data': old_receipts['fig1_model']['plotted_data'],
    'reused_without_change': True,
}


def chosen(h, g, presence=None):
    subset = [r for r in rows if int(r['gannets']) == g
              and (presence == 'G' and r['presence'] == 'G'
                   or presence != 'G' and r['presence'] != 'G'
                   and float(r['herding_minimum_T']) == h)]
    assert len(subset) == 4
    return sorted(subset, key=lambda r: int(r['school_seed']))


def paired(h, g):
    subset = [r for r in pairs if float(r['herding_minimum_T']) == h and int(r['gannets']) == g]
    assert len(subset) == 4
    return sorted(subset, key=lambda r: int(r['school_seed']))


def cell(h, g):
    return next(r for r in summary if float(r['herding_minimum_T']) == h and int(r['gannets']) == g)


# Figure 2: absolute individual food and the corresponding partner effects.
fig, axes = plt.subplots(2, 2, figsize=(7.05, 3.9))
fig.subplots_adjust(left=.085, right=.99, bottom=.115, top=.84, wspace=.30, hspace=.60)
plotted = []
for h, color, marker in zip(H, COLORS, MARKERS):
    dmeans = [np.mean([int(r['D_captures']) / 12 for r in chosen(h, g)]) for g in G]
    gmeans = [np.mean([int(r['G_captures']) / g for r in chosen(h, g)]) for g in G]
    baseline = np.mean([int(r['D_captures']) / 12 for r in chosen(h, 0)])
    axes[0, 0].plot(G, dmeans, color=color, marker=marker, ms=4, lw=1.2)
    axes[0, 0].axhline(baseline, color=color, lw=.95, ls='--', alpha=.85)
    axes[0, 1].plot(G, gmeans, color=color, marker=marker, ms=4, lw=1.2)
    for ax, species in zip(axes[1], ('D', 'G')):
        means = [float(cell(h, g)[species + '_mean_rate_change']) * 36 for g in G]
        lows = [float(cell(h, g)[species + '_pointwise95_low']) * 36 for g in G]
        highs = [float(cell(h, g)[species + '_pointwise95_high']) * 36 for g in G]
        ax.fill_between(G, lows, highs, color=color, alpha=.10, linewidth=0)
        ax.plot(G, means, color=color, marker=marker, ms=4, lw=1.2)
        ax.errorbar(G, means, yerr=[np.array(means)-lows, np.array(highs)-means],
                    fmt='none', ecolor=color, lw=.7, capsize=2, alpha=.65)
        for g in G:
            raw = [float(r[species + '_rate_change']) * 36 for r in paired(h, g)]
            x = np.full(4, g) + np.array([-.08, -.025, .025, .08])
            ax.scatter(x, raw, color=color, marker=marker, s=9, alpha=.55, linewidth=0, zorder=1)
    plotted.append({'H': h, 'gannets': list(G), 'D_mixed_per_dolphin': dmeans,
                    'D_alone_per_dolphin': baseline, 'G_mixed_per_gannet': gmeans,
                    'saved_interval_rows': [cell(h, g) for g in G]})
galone = [np.mean([int(r['G_captures']) / g for r in chosen(None, g, 'G')]) for g in G]
axes[0, 1].plot(G, galone, color=INK, marker='D', ms=3.5, lw=1.1, ls='--')
for ax in axes.flat:
    ax.set_xticks(G)
    ax.set_xlim(.4, 18.6)
    ax.set_xlabel('Number of gannets')
for ax in axes[1]:
    ax.axhline(0, color=INK, lw=.7, ls='--')
style(axes[0, 0], 'a', 'Absolute dolphin return', 'Captures per dolphin / 36T')
style(axes[0, 1], 'b', 'Absolute gannet return', 'Captures per gannet / 36T')
style(axes[1, 0], 'c', 'Dolphin partner effect', 'Change per dolphin / 36T')
style(axes[1, 1], 'd', 'Gannet partner effect', 'Change per gannet / 36T')
handles = [Line2D([], [], color=c, marker=m, lw=1.2, label=f'H={h:g}T')
           for h, c, m in zip(H, COLORS, MARKERS)]
handles += [Line2D([], [], color=INK, lw=1.1, label='Mixed'),
            Line2D([], [], color=INK, lw=1.1, ls='--', label='Species alone')]
fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.53, 1), ncol=5,
           frameon=False, columnspacing=1.1, handletextpad=.4)
save(fig, 'fig2_returns',
     'Absolute returns (a,b) and matched partner effects (c,d) over complete 36T encounters, '
     'with equal weights for four previously observed schools. Solid lines join means at actual '
     'numeric bird counts. Dashed baselines are same-H dolphin-only returns (a) and count-matched '
     'gannet-only returns (b). Partner effects compare mixed with these controls; faint points are '
     'the four paired school effects and ribbons/whiskers are the existing 95% pointwise whole-school '
     'bootstrap intervals. Points have slight horizontal jitter. Absolute food per bird declines '
     'generally as counts grow, while some adjacent counts rise; partner benefits can remain positive. '
     'The intervals are exploratory and do not correct selection or multiplicity.',
     {'settings': plotted, 'G_alone_per_gannet': galone})

# Figure 3: opportunity decomposition and one prey-state diagnostic.
diagnostics = {r['case_name']: r for r in old_receipts['fig4_diagnostics']['plotted_data']}
fig, axes = plt.subplots(2, 2, figsize=(7.05, 3.6))
fig.subplots_adjust(left=.085, right=.99, bottom=.13, top=.84, wspace=.30, hspace=.60)
plotted = []
for h, color, marker in zip(H, COLORS, MARKERS):
    series = [[] for _ in range(4)]
    for g in (0, *G):
        group = chosen(h, g)
        launches = [int(r['D_launches']) / 12 for r in group]
        contacts = [int(r['D_contacts']) / 12 for r in group]
        ratios = [int(r['D_contacts']) / int(r['D_launches']) for r in group]
        r90 = [float(diagnostics[r['case_name']]['time_mean_r90']) for r in group]
        means = [np.mean(launches), sum(int(r['D_contacts']) for r in group) / sum(int(r['D_launches']) for r in group),
                 np.mean(contacts), np.mean(r90)]
        for i, (values, mean) in enumerate(zip((launches, ratios, contacts, r90), means)):
            series[i].append(float(mean))
            axes.flat[i].scatter(np.array([-.09,-.03,.03,.09])+g, values, s=9,
                                 color=color, marker=marker, alpha=.32, linewidth=0)
        plotted.append({'H': h, 'gannets': g, 'D_launches': sum(int(r['D_launches']) for r in group),
                        'D_contacts': sum(int(r['D_contacts']) for r in group),
                        'means': [float(v) for v in means], 'school_r90_time_means': r90})
    for ax, y in zip(axes.flat, series):
        ax.plot((0, *G), y, color=color, marker=marker, ms=3.5, lw=1.1)
for ax in axes.flat:
    ax.set_xticks((0, *G)); ax.set_xlim(-.5, 18.6)
    ax.set_xlabel('Number of gannets')
style(axes[0, 0], 'a', 'Strike opportunities', 'Launches per dolphin\n/ 36T')
style(axes[0, 1], 'b', 'Contact yield per launch', 'Eligible contacts / launch')
style(axes[1, 0], 'c', 'Total contact opportunity', 'Eligible contacts per dolphin\n/ 36T')
style(axes[1, 1], 'd', 'Live-fish school radius', 'Time-mean r90\n(model units)')
fig.legend(handles=handles[:3], loc='upper center', bbox_to_anchor=(.52, 1), ncol=3, frameon=False)
save(fig, 'fig3_opportunities',
     'Descriptive opportunity and prey-state diagnostics at every dolphin-bearing setting. '
     'Faint points show all four schools. Lines join equal-school means except in (b), where the '
     'line is pooled eligible contacts divided by pooled launches; faint points remain individual '
     'school ratios. Launches and contacts include the full 36T encounter; a launch near its end '
     'can remain incomplete. The saved r90 measure is the 90th percentile of distances of living fish '
     'from their current three-dimensional centroid, trapezoid-time-averaged over observed nonempty frames. '
     'Consumption and survivor selection affect this measure. The plots describe associations, '
     'not a causal separation of herding, disturbance and competition.', plotted)

# Figure 4: four-school outcomes and the distinct eight-school numerical check.
grid_path = BUNDLE / 'data/research/fine_dt_replication_2026-11-09/results/full_36T_v1/analysis_final/paired_effect_grid_differences.csv'
grid = sorted(table(grid_path), key=lambda r: int(r['school_seed']))
stats = read(BUNDLE / 'data/research/longer_replication_2026-11-09/results/analysis_final/primary_statistics.json')
assert len(grid) == 8 and stats['independent_schools'] == 8
fig, axes = plt.subplots(2, 2, figsize=(7.05, 3.6))
fig.subplots_adjust(left=.085, right=.99, bottom=.13, top=.91, wspace=.32, hspace=.68)
school_colors = ('#007C83', '#CA7C18', '#7957A0', '#4F6A34')
current_data = {}
grid_data = {}
for j, species in enumerate(('D', 'G')):
    ax = axes[0, j]
    norm_a = 12 if species == 'D' else 9
    norm_b = 12
    a = [int(r[species + '_capture_change']) / norm_a for r in paired(1., 9)]
    b = [int(r[species + '_capture_change']) / norm_b for r in paired(2., 12)]
    for i, (u, v, color) in enumerate(zip(a, b, school_colors)):
        offset = [-.075,-.025,.025,.075][i]
        ax.plot([offset, 1+offset], [u, v], color=color, marker='o', ms=4, lw=.8, alpha=.8)
    means = [float(np.mean(a)), float(np.mean(b))]
    ci = [[float(cell(h, g)[species + '_pointwise95_' + end]) * 36 for end in ('low', 'high')] for h, g in ((1., 9), (2., 12))]
    ax.errorbar([0,1], means, yerr=[[means[k]-ci[k][0] for k in range(2)],
                                  [ci[k][1]-means[k] for k in range(2)]],
                color=INK, markersize=4, fmt='D', lw=1, capsize=3, zorder=5)
    ax.axhline(0, color=INK, lw=.7, ls='--')
    ax.set_xticks([0,1], ['H=1T, G=9', 'H=2T, G=12']); ax.set_xlim(-.25,1.25)
    style(ax, 'ab'[j], f'Current four schools: {species}', 'Change in captures\nper predator / 36T')
    current_data[species] = {'H1_G9': a, 'H2_G12': b, 'saved95_intervals': ci}
    ax = axes[1, j]
    norm = 12 if species == 'D' else 3
    a = [int(r['coarse_' + species + '_partner_effect']) / norm for r in grid]
    b = [int(r['fine_' + species + '_partner_effect']) / norm for r in grid]
    for u, v in zip(a, b):
        ax.plot([0,1], [u,v], color='#8B9AA4', marker='o', ms=3.2, lw=.8, alpha=.70)
    means = [float(np.mean(a)), float(np.mean(b))]
    ci = np.asarray(stats[species]['interval']) / norm
    ax.scatter([0,1], means, color=INK, marker='D', s=22, zorder=5)
    ax.errorbar([0], [means[0]], yerr=[[means[0]-ci[0]], [ci[1]-means[0]]],
                color=INK, capsize=3, lw=1.1, fmt='none', zorder=5)
    ax.axhline(0, color=INK, lw=.7, ls='--')
    ax.set_xticks([0,1], ['Coarse dt', 'Half dt']); ax.set_xlim(-.25,1.25)
    style(ax, 'cd'[j], f'Eight-school grid check: {species}', 'Change in captures\nper predator / 36T')
    grid_data[species] = {'coarse': a, 'fine': b, 'saved_coarse975_interval': ci.tolist()}
save(fig, 'fig4_sensitivity',
     'Raw school effects and numerical sensitivity, with D denoting dolphins and G gannets. '
     '(a,b) H1/nine-bird and H2/twelve-bird discovery settings: colours connect the same four schools, diamonds are means, '
     'and whiskers are saved 95% pointwise whole-school bootstrap intervals. Dolphin effects use '
     'same-H D-only controls; gannet effects use count-matched G-only controls. (c,d) A distinct eight-school '
     'H=2T, three-bird comparison, with schools connected across dt=0.00125T and dt=0.000625T. '
     'Diamonds are means; only coarse primary means have the saved 97.5% marginal intervals, '
     'chosen for the two-species primary comparison. All axes show captures per individual predator '
     'over 36T (12 dolphins; nine/twelve birds above and three below). These eight schools do not validate '
     'the selected discovery settings; repeating a school on a numerical grid does not add a school.',
     {'current': current_data, 'independent_grid_check': grid_data})

manifest['sources'] = [source_record(p) for p in sorted(inputs)]
for name, item in manifest['figures'].items():
    item['outputs'] = {ext: {'path': str(OUT / f'{name}.{ext}'), 'sha256': sha(OUT / f'{name}.{ext}')}
                       for ext in ('png', 'pdf')}
(OUT / 'figure_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(OUT / 'captions.txt').write_text('\n\n'.join(f'{name}: {item["caption"]}' for name, item in manifest['figures'].items()) + '\n')
shutil.copy2(OUT / 'captions.txt', ROOT / 'captions.txt')
print(json.dumps({'figures': list(manifest['figures']), 'native_steps': 0,
                  'bootstrap_draws_generated': 0, 'source_files': len(inputs)}, indent=2))
