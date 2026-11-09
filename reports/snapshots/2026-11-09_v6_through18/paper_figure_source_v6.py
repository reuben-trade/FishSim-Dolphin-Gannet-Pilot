"""One shared hunting rule: pilot evidence, complete regime map and diagnostics."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import numpy as np

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent
DEVELOPMENT=RESEARCH/'simple_herd_strike_pilot_2026-11-08'
REPLICATION=RESEARCH/'exposed_replication_2026-11-08'
LONGER=RESEARCH/'longer_replication_2026-11-09'
FINE=RESEARCH/'fine_dt_replication_2026-11-09'
DEPTH=RESEARCH/'gannet_depth_study_2026-11-08'
SWEEP=RESEARCH/'high_count_regime_extension_2026-11-09'
CLOSURE=None
BUNDLE_ROOT=None
OUT=HERE/'figures'
import high_count_evidence_v6 as evidence
D='#087F8C'
DG='#D98525'
FISH='#8099AB'
INK='#263746'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,
    'axes.labelsize':9.5,'axes.titlesize':10,'xtick.labelsize':8.5,
    'ytick.labelsize':8.5,'legend.fontsize':8.5,'axes.spines.top':False,
    'axes.spines.right':False,'axes.edgecolor':'#657582',
    'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,
    'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})


def read(path):return json.loads(path.read_text())

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def table(path):
    with path.open(newline='') as handle:return list(csv.DictReader(handle))

def source(path):return {'path':str(path.resolve()),'sha256':sha(path)}

def require_sealed(directory, filenames):
    seal=read(directory/'completion.json')
    assert seal['status']=='complete'
    for name in filenames:assert seal['files'][name]==sha(directory/name),(directory,name)

def save(fig, name, caption, inputs, data):
    OUT.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.035)
    fig.savefig(OUT/(name+'.png'),dpi=230,bbox_inches='tight',pad_inches=.035)
    plt.close(fig)
    receipt_path=OUT/'figure_receipts.json'
    receipts=read(receipt_path) if receipt_path.exists() else {}
    receipts[name]={'caption':caption,'sources':[source(p) for p in inputs],
        'plotted_data':data,'created_at':datetime.now(ZoneInfo('Australia/Perth')).isoformat(),
        'outputs':{ext:source(OUT/(name+'.'+ext)) for ext in ('pdf','png')},
        'native_steps':0,'uncertainty_intervals':(
            'Pointwise95% paired whole-school bootstrap, n=4;10000draws seed88493009; no multiplicity correction'
            if name=='fig3_regime_map' else
            'Prespecified97.5% marginal intervals for coarse36T eight-school effects; other cohorts descriptive'
            if name=='fig2_cohorts' else 'none')}
    receipt_path.write_text(json.dumps(receipts,indent=2,allow_nan=False)+'\n')
    (OUT/'captions.txt').write_text('\n\n'.join(f'{key}: {receipts[key]["caption"]}' for key in sorted(receipts))+'\n')
    print(name,flush=True)

def panel(ax, letter, title):
    ax.set_title(f'({letter})  {title}',loc='left',pad=8)
    ax.set_axisbelow(True)
    ax.grid(axis='y',color='#E2E8ED',linewidth=.6)

def model_figure():
    directory=DEVELOPMENT/'results/full_36T_v1/cases/s39061002_exposed_DG'
    require_sealed(directory,['trajectories.npz','events.jsonl.gz','initial_school.npz'])
    with np.load(directory/'trajectories.npz') as archive:
        trajectory={k:archive[k].copy() for k in archive.files}
    with np.load(directory/'initial_school.npz') as archive:origin=float(archive['time'])
    index=int(np.argmin(abs(trajectory['time']-12.)))
    assert abs(float(trajectory['time'][index])-12.)<1e-7
    start=int(np.argmin(abs(trajectory['time']-6.)))
    live=trajectory['positions'][index,trajectory['alive'][index]]
    reference=live.mean(axis=0);reference[2]=0.
    fish=live-reference
    predators=trajectory['predator_positions'][index]-reference
    paths=trajectory['predator_positions'][start:index+1]-reference
    actors=trajectory['actor_ids']
    dolphins=np.array([a.startswith('D') for a in actors]);birds=~dolphins
    captures=[]
    with gzip.open(directory/'events.jsonl.gz','rt') as handle:
        for line in handle:
            event=json.loads(line)
            if event['kind']=='oral' and event['status']=='captured' and event['closes_bout']:
                elapsed=event['contact']['time']-origin
                if 6.-1e-8<=elapsed<=12.+1e-8:
                    captures.append((np.asarray(event['contact']['prey_position'])-reference).tolist())
    captures=np.asarray(captures,float).reshape(-1,3)
    fig=plt.figure(figsize=(7.05,2.55))
    fig.subplots_adjust(left=.025,right=.99,bottom=.24,top=.85)
    gs=fig.add_gridspec(1,3,width_ratios=[1.25,1.1,1.1],wspace=.45)
    diagram=fig.add_subplot(gs[0]);diagram.set_axis_off()
    diagram.set_title('(a)  Shared dolphin cycle',loc='left',pad=8)
    labels=['Near prey for H\ncontinuously',
            'Select feasible prey\nfewest neighbours',
            'One bounded strike\nshared capture rule',
            'Handle or recover\nrestart herding']
    ys=[.84,.61,.38,.15]
    for y,label in zip(ys,labels):
        box=FancyBboxPatch((.13,y-.075),.83,.15,boxstyle='round,pad=.015',
            facecolor='#EEF6F7',edgecolor=D,linewidth=.8,transform=diagram.transAxes)
        diagram.add_patch(box)
        diagram.text(.545,y,label,ha='center',va='center',fontsize=8.5,transform=diagram.transAxes)
    for y,z in zip(ys,ys[1:]):
        diagram.annotate('',xy=(.545,z+.095),xytext=(.545,y-.095),
            xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':INK,'lw':.9})
    diagram.plot([.12,.035,.035,.12],[.15,.15,.84,.84],transform=diagram.transAxes,color=INK,lw=.8)
    diagram.annotate('',xy=(.13,.84),xytext=(.035,.84),xycoords='axes fraction',
        arrowprops={'arrowstyle':'->','color':INK,'lw':.8})
    diagram.text(.5,-.12,'Gannets affect prey;\nthe dolphin rule stays fixed.',
        ha='center',va='top',fontsize=8.1,transform=diagram.transAxes)
    axes=[fig.add_subplot(gs[1]),fig.add_subplot(gs[2])]
    for ax,vertical,title,letter in zip(axes,[1,2],['Top view, 12T','Side view, 12T'],['b','c']):
        for j in range(len(actors)):
            ax.plot(paths[:,j,0],paths[:,j,vertical],color=D if dolphins[j] else DG,
                linewidth=.65,alpha=.35,zorder=1)
        ax.scatter(fish[:,0],fish[:,vertical],s=6,color=FISH,alpha=.8,linewidths=0,zorder=2)
        ax.scatter(predators[dolphins,0],predators[dolphins,vertical],s=28,marker='^',
                   color=D,edgecolors='white',linewidths=.35,zorder=4)
        ax.scatter(predators[birds,0],predators[birds,vertical],s=35,marker='v',
                   color=DG,edgecolors='white',linewidths=.35,zorder=4)
        if len(captures):ax.scatter(captures[:,0],captures[:,vertical],s=18,marker='x',color=INK,lw=.8,zorder=5)
        if vertical==2:
            ax.axhline(0,color='#A5BCC8',lw=1,ls='--',zorder=0)
            ax.set_ylabel('z')
        else:ax.set_ylabel('Relative y')
        ax.set_xlabel('Relative x')
        ax.set_title(f'({letter})  {title}',loc='left',pad=8)
        ax.set_aspect('equal',adjustable='box')
        ax.locator_params(axis='both',nbins=4)
    handles=[Line2D([],[],marker='o',color=FISH,lw=0,markersize=3,label='Fish'),
             Line2D([],[],marker='^',color=D,lw=0,markersize=5,label='Dolphin'),
             Line2D([],[],marker='v',color=DG,lw=0,markersize=5,label='Gannet'),
             Line2D([],[],marker='x',color=INK,lw=0,markersize=4,label='Capture, 6–12T')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.67,.005),ncol=4,
               frameon=False,columnspacing=.65,handletextpad=.3,fontsize=8)
    caption=('One shared dolphin rule and one recorded encounter. (a) Continuous near-prey pressure for H, '
        'a physically feasible strike preferring prey with fewer neighbours, then ordinary recovery. '
        'The dolphin rule is unchanged by gannet presence. H does not certify completed herding; the target need not move outward. '
        '(b,c) Recorded top and side views at12T for original development school39061002, with paths/captures over6–12T. '
        'The fish centroid defines horizontal coordinates; z=0 is the surface, in model units. '
        'This historical snapshot was fixed before the sweep and does not demonstrate whole-school containment or a causal mechanism.')
    save(fig,'fig1_model',caption,[directory/'trajectories.npz',directory/'events.jsonl.gz',
        directory/'initial_school.npz',directory/'completion.json',DEVELOPMENT/'controllers.py'],
        {'school_seed':39061002,'policy':'exposed','presence':'DG','frame_elapsed_T':float(trajectory['time'][index]),
         'path_interval_T':[6.,12.],'live_fish':len(live),'capture_count_in_path_interval':len(captures),
         'coordinate_reference_xyz':reference.tolist(),'trajectory_sampling_T':.1})

def verified_replication():
    analysis=LONGER/'results/analysis_final'
    audit=read(analysis/'analysis_audit.json')
    assert audit['status']=='passed' and audit['sealed_horizon_records']==48 and not audit['pending']
    pairs=table(analysis/'paired_horizons.csv');statistics=read(analysis/'primary_statistics.json')
    plan=read(LONGER/'analysis_plan.json')
    assert statistics['status']=='complete' and statistics['independent_schools']==8 and len(pairs)==16
    inputs=[analysis/'paired_horizons.csv',analysis/'primary_statistics.json',analysis/'analysis_audit.json',LONGER/'analysis_plan.json',Path(__file__)]
    by={(int(r['school_seed']),float(r['horizon_T'])):r for r in pairs}
    for school in range(39064501,39064509):
        for horizon in (36.,72.):
            states={}
            for presence in ('D','G','DG'):
                directory=LONGER/'results/full_72T_v1/cases'/f's{school}_exposed_{presence}_c61001'
                seal_path=directory/f'checkpoint_{horizon:g}T.seal.json';seal=read(seal_path)
                assert seal['status']=='complete'
                for name,digest in seal['files'].items():assert sha(directory/name)==digest
                data_path=directory/f'checkpoint_{horizon:g}T.json'
                states[presence]=read(data_path);inputs.extend([seal_path,data_path])
            row=by[(school,horizon)]
            for field,presence,species in (('D_alone','D','D'),('D_with_gannets','DG','D'),('G_alone','G','G'),('G_with_dolphins','DG','G')):
                assert int(row[field])==states[presence]['species'][species]['captures']
            assert int(row['D_difference'])==int(row['D_with_gannets'])-int(row['D_alone'])
            assert int(row['G_difference'])==int(row['G_with_dolphins'])-int(row['G_alone'])
    vectors=np.asarray([[float(by[(s,36.)]['D_difference']),float(by[(s,36.)]['G_difference'])] for s in range(39064501,39064509)])
    generator=np.random.default_rng(plan['bootstrap']['seed'])
    draws=generator.integers(0,8,size=(plan['bootstrap']['draws'],8))
    intervals=np.quantile(vectors[draws].mean(axis=1),plan['bootstrap']['quantiles'],axis=0)
    for index,species in enumerate(('D','G')):
        assert statistics[species]['mean_difference']==float(vectors[:,index].mean())
        assert np.array_equal(np.asarray(statistics[species]['interval']),intervals[:,index])
    fine_analysis=FINE/'results/full_36T_v1/analysis_final'
    fine_audit=read(fine_analysis/'analysis_audit.json')
    assert fine_audit['status']=='complete' and fine_audit['independent_schools']==8 and fine_audit['grids']==2
    fine_table=table(fine_analysis/'paired_effect_grid_differences.csv')
    assert len(fine_table)==8
    inputs.extend([fine_analysis/'analysis_audit.json',fine_analysis/'paired_effect_grid_differences.csv',
                   FINE/'paper_update_validation.json'])
    assert read(FINE/'paper_update_validation.json')['status']=='passed'
    fine_pairs=[]
    assert sorted(int(r['school_seed']) for r in fine_table)==list(range(39064501,39064509))
    for row in sorted(fine_table,key=lambda r:int(r['school_seed'])):
        school=int(row['school_seed']);states={}
        for presence in ('D','G','DG'):
            directory=FINE/'results/full_36T_v1/cases'/f's{school}_exposed_{presence}_c61001'
            seal_path=directory/'checkpoint_36T.seal.json';seal=read(seal_path)
            assert seal['status']=='complete'
            for name,digest in seal['files'].items():assert sha(directory/name)==digest
            data_path=directory/'checkpoint_36T.json';states[presence]=read(data_path)
            assert states[presence]['native_steps']==57600
            inputs.extend([seal_path,data_path])
        fine_row=dict(school_seed=school,horizon_T=36.)
        for species,alone in [('D','D'),('G','G')]:
            a=states[alone]['species'][species]['captures'];m=states['DG']['species'][species]['captures']
            assert int(row[f'fine_{species}_alone'])==a and int(row[f'fine_{species}_mixed'])==m
            assert int(row[f'fine_{species}_partner_effect'])==m-a
            assert int(row[f'coarse_{species}_partner_effect'])==int(by[(school,36.)][species+'_difference'])
            coarse=by[(school,36.)]
            assert int(row[f'coarse_{species}_alone'])==int(coarse[species+'_alone'])
            assert int(row[f'coarse_{species}_mixed'])==int(coarse['D_with_gannets' if species=='D' else 'G_with_dolphins'])
            assert int(row[f'{species}_effect_fine_minus_coarse'])==m-a-int(by[(school,36.)][species+'_difference'])
            fine_row[species+'_difference']=m-a
            fine_row[species+'_alone']=a;fine_row[species+'_mixed']=m
        fine_pairs.append(fine_row)
    return pairs,statistics,fine_pairs,inputs


def pilot_pairs(study):
    """Read only the fixed exposed rule from original sealed oral events."""
    records={};inputs=[]
    for folder in sorted((study/'results/full_36T_v1/cases').iterdir()):
        config=read(folder/'config.json')
        summary=read(folder/'summary.json')
        if summary['policy']!='exposed':continue
        require_sealed(folder,['config.json','events.jsonl.gz','summary.json'])
        assert summary['status']=='complete' and abs(summary['actual_duration']-36)<1e-7
        with gzip.open(folder/'events.jsonl.gz','rt') as handle:
            catches=[e for e in map(json.loads,handle) if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
        assert len(catches)==len({e['prey_id'] for e in catches})
        d=sum(e['actor_id'].startswith('D') for e in catches)
        assert d==summary['species']['D']['captures']
        key=(summary['school_seed'],summary['capture_seed'],config['presence'])
        assert key not in records
        records[key]=d
        inputs.extend(folder/name for name in ('config.json','events.jsonl.gz','summary.json','completion.json'))
    pairs=[]
    for school,stream in sorted({k[:2] for k in records}):
        pairs.append(dict(school_seed=school,capture_seed=stream,D=records[school,stream,'D'],DG=records[school,stream,'DG']))
    return pairs,inputs


def cohort_figure():
    development,di=pilot_pairs(DEVELOPMENT);followup,fi=pilot_pairs(REPLICATION)
    assert len(development)==2 and len(followup)==4
    assert (sum(r['D'] for r in development),sum(r['DG'] for r in development))==(41,48)
    assert (sum(r['D'] for r in followup),sum(r['DG'] for r in followup))==(87,101)
    pairs,statistics,fine,ri=verified_replication()
    coarse=sorted([r for r in pairs if float(r['horizon_T'])==36],key=lambda r:int(r['school_seed']))
    fine=sorted(fine,key=lambda r:int(r['school_seed']))
    fig,axes=plt.subplots(1,4,figsize=(7.05,2.45))
    fig.subplots_adjust(left=.075,right=.99,bottom=.25,top=.74,wspace=.55)
    colours=['#087F8C','#D98525']
    for ax,group,letter,title in [(axes[0],development,'a','Pilot: 2 schools\n41 → 48 (+17.1%)'),
                                  (axes[1],followup,'b','Follow-up: 2 schools\n87 → 101 (+16.1%)')]:
        schools=sorted({r['school_seed'] for r in group})
        for row in group:
            color=colours[schools.index(row['school_seed'])]
            marker='o' if row['capture_seed']==61001 else 's'
            ax.plot([0,1],[row['D'],row['DG']],color=color,lw=.9,marker=marker,ms=3.5,alpha=.85)
        ax.set_xticks([0,1],['D only','Mixed']);ax.set_xlim(-.2,1.2)
        ax.set_ylabel('Dolphin captures',fontsize=8)
        ax.set_title(f'({letter}) {title}',loc='left',fontsize=8.5,pad=8)
        ax.grid(axis='y',color='#E2E8ED',lw=.6);ax.locator_params(axis='y',nbins=4)
    values={}
    for ax,species,letter in [(axes[2],'D','c'),(axes[3],'G','d')]:
        a=np.array([int(r[species+'_difference']) for r in coarse]);b=np.array([r[species+'_difference'] for r in fine])
        for j,(x,y) in enumerate(zip(a,b)):
            ax.plot([0,1],[x,y],color='#8396A3',lw=.7,marker='o',ms=2.5,alpha=.65)
        means=[float(a.mean()),float(b.mean())]
        ax.scatter([0,1],means,color=INK,marker='D',s=22,zorder=5)
        ci=statistics[species]['interval']
        ax.errorbar(0,means[0],yerr=[[means[0]-ci[0]],[ci[1]-means[0]]],color=INK,lw=1.1,capsize=3,zorder=6)
        ax.axhline(0,color='#566D7D',lw=.8,ls='--');ax.set_xticks([0,1],['Coarse','Fine']);ax.set_xlim(-.2,1.2)
        ax.set_ylabel('Partner effect\n(captures)',fontsize=8)
        ax.set_title(f'({letter}) New 8 schools: {species}\ncoarse → fine (36T)',loc='left',fontsize=8.5,pad=8)
        ax.grid(axis='y',color='#E2E8ED',lw=.6);ax.locator_params(axis='y',nbins=5)
        values[species]=dict(coarse=a.tolist(),fine=b.tolist(),coarse_interval=ci,mean=means)
    caption=('Distinct cohorts under the same exposed-prey dolphin rule. (a) Two development schools, one capture-stream setting; '
        '(b) two fresh follow-up schools, each under two stream settings (circles/squares), not four independent schools. '
        'Colour identifies school within each two-school panel; circles/squares identify stream settings61001/61002. '
        'Lines join D-only and mixed outcomes for each repetition; the headline totals are not additional samples. '
        '(c,d) Partner effects on eight further schools at36T, with each school joined across coarse/fine grids. '
        'Diamonds mark means; only coarse-primary means have97.5% marginal school-vector bootstrap intervals. '
        'The fine check reused these eight schools, not the earlier positive cohorts. No convergence or universal dolphin benefit is established.')
    save(fig,'fig2_cohorts',caption,di+fi+ri,
         dict(development=development,followup=followup,eight_school_sensitivity=values))


def complete_regime():
    receipt=evidence.verify_complete()
    rows=evidence.all_rows()
    pairs,summary=evidence.reconstruct_map(rows,read(SWEEP/'analysis_plan.json'))
    return rows,pairs,summary,evidence.diagnostic_rows(),receipt


def regime_figure(summary):
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.ticker import MaxNLocator
    fields=[('D_mean_rate_change','D_pointwise95_low','D_pointwise95_high','Dolphins: mixed − same-H alone'),
            ('G_mean_rate_change','G_pointwise95_low','G_pointwise95_high','Gannets: mixed − same-count alone')]
    fig,axes=plt.subplots(2,1,figsize=(7.05,3.05))
    fig.subplots_adjust(left=.075,right=.925,bottom=.13,top=.89,hspace=.54)
    counts=evidence.GS[1:]
    for ax,(field,lower,upper,title),letter in zip(axes,fields,'ab'):
        values=np.array([r[field]*36 for r in summary]).reshape(3,6)
        bound=max(float(abs(values).max()),1e-8)
        im=ax.imshow(values,origin='lower',cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound),aspect='auto')
        for i in range(3):
            for j in range(6):
                row=summary[i*6+j]
                compact=lambda x:f'{0. if abs(x)<5e-12 else x:+.2f}'
                ax.text(j,i,f'{compact(row[field]*36)}\n[{compact(row[lower]*36)}, {compact(row[upper]*36)}]',
                        ha='center',va='center',fontsize=7.6,color='white' if abs(values[i,j])>.68*bound else INK)
        ax.set_xticks(range(6),counts);ax.set_yticks(range(3),[1,2,3]);ax.set_ylabel('H (T)',fontsize=8)
        ax.set_title(f'({letter}) {title}',loc='left',fontsize=9,pad=6)
        bar=fig.colorbar(im,ax=ax,orientation='vertical',fraction=.02,pad=.02,aspect=12)
        bar.ax.tick_params(labelsize=7);bar.locator=MaxNLocator(3);bar.update_ticks()
    axes[1].set_xlabel('Gannets in mixed group',fontsize=8,labelpad=3)
    caption=('Complete balanced H×G response map: all18mixed settings, paired within the same four previously observed schools. '
        'Cell numbers are mean capture changes per predator over36T; brackets are pointwise95% whole-school bootstrap intervals. '
        '(a) Same-H dolphin-only controls; (b) count-matched gannet-only controls shared across H. Colour scales differ. '
        'All72school contrasts, absolute returns and separate best-tested-D-only comparisons are in the notebook. '
        'The108condition-school outcomes include60retained and48new encounters, not108independent schools. '
        'Intervals are exploratory, without multiplicity adjustment; no winning group size or convergence is established.')
    base=evidence.FULL
    inputs=[SWEEP/'protocol.json',SWEEP/'analysis_plan.json',SWEEP/'frozen_sources.json',
            evidence.DISPATCH/'DISPATCH_FREEZE.json',base/'status.json',base/'physical_review.json',
            base/'dispatch_analysis_binding.json',base/'analysis_final/analysis_audit.json',base/'analysis_final/regime_summary.csv']
    save(fig,'fig3_regime_map',caption,inputs,summary)


def diagnostic_figure(rows,diagnostics):
    counts={r['case_name']:r for r in rows}
    records=[]
    for r in diagnostics:
        raw=counts[r['case_name']]
        if not raw['dolphins']:continue
        records.append(dict(r,D_contacts_per_dolphin_per36T=raw['D_contacts']/12,
            D_captures_per_dolphin_per36T=raw['D_captures']/12))
    assert len(records)==84
    fields=[('time_mean_r90','Live-school radius r90'),('time_mean_outward_fraction','Outward-moving live-fish fraction'),
        ('D_contacts_per_dolphin_per36T','Eligible contacts / dolphin / 36T'),
        ('D_captures_per_dolphin_per36T','Captures / dolphin / 36T')]
    fig,axes=plt.subplots(2,2,figsize=(7.05,2.8))
    fig.subplots_adjust(left=.075,right=.99,bottom=.19,top=.83,wspace=.35,hspace=.65)
    colours=['#087F8C','#D98525','#7B5E9C']
    for ax,(field,label),letter in zip(axes.flat,fields,'abcd'):
        for h,color,marker in zip(evidence.HS,colours,['o','s','^']):
            means=[]
            for x,g in enumerate(evidence.GS):
                chosen=sorted([r for r in records if r['herding_minimum_T']==h and r['gannets']==g],key=lambda r:r['school_seed'])
                assert len(chosen)==4
                y=[r[field] for r in chosen];means.append(float(np.mean(y)))
                ax.scatter(np.array([-.08,-.025,.025,.08])+x,y,s=7,marker=marker,color=color,alpha=.35,linewidths=0)
            ax.plot(range(len(evidence.GS)),means,color=color,marker=marker,ms=3,lw=.9,label=f'H={h:g}T')
        ax.set_xticks(range(len(evidence.GS)),list(evidence.GS))
        if letter in 'cd':ax.set_xlabel('Gannets',fontsize=8)
        ax.set_title(f'({letter}) {label}',loc='left',fontsize=8,pad=5)
        ax.grid(axis='y',color='#E2E8ED',lw=.6);ax.locator_params(axis='y',nbins=4)
    fig.legend(*axes.flat[0].get_legend_handles_labels(),loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.5,1),fontsize=8)
    caption=('Descriptive collective-state and feeding diagnostics across every dolphin-bearing H×G setting, '
        'including G=0. Faint points are all four previously observed schools; lines join equal-school means. '
        'Saved live-fish r90 and outward fraction are time-averaged over the full observed nonempty trajectory, '
        'without selected post-dive windows. Contacts and food come from complete raw events with the full36T denominator. '
        'Prey consumption and survivor selection can change school-state summaries. These associations do not demonstrate '
        'causal mediation, completed herding, biological calibration or deliberate cooperation.')
    inputs=[]
    for r in records:
        folder=evidence.folder(counts[r['case_name']])
        inputs.extend(folder/name for name in ('completion.json','school_metrics.json','events.jsonl.gz','summary.json'))
    save(fig,'fig4_diagnostics',caption,inputs,records)


def main(historical_preview=False):
    if not historical_preview:
        rows,pairs,summary,diagnostics,receipt=complete_regime()
    model_figure();cohort_figure()
    if not historical_preview:
        regime_figure(summary);diagnostic_figure(rows,diagnostics)
    assert 'fish_sim.cmodel' not in __import__('sys').modules
    return dict(native_steps=0,complete_sweep=not historical_preview)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-preview',action='store_true',help='Only existing cohorts; no sweep effects')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.output:OUT=args.output
    main(historical_preview=args.historical_preview)

