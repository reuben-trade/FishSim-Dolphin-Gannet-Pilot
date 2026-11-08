"""Four paper figures from sealed FishSim encounters; no simulation is run."""
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
DEPTH=RESEARCH/'gannet_depth_study_2026-11-08'
OUT=HERE/'figures'
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
        'native_steps':0,'uncertainty_intervals':'none'}
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
    labels=['Herd near prey\nfor 2T continuously',
            'Select feasible prey\nnearest / exposed',
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
    caption=('Model rules and one recorded encounter. (a) Both dolphin target policies use the same '
        '2T near-prey herding cycle, one feasible strike and normal handling/recovery. Gannets influence '
        'dolphins through prey dynamics, without a dolphin response to a bird cue. (b,c) Actual top and '
        'side views at 12T for development school 39061002, exposed targeting with gannets; lines show '
        'predator paths over 6–12T and crosses mark actual captures in that interval. Horizontal coordinates '
        'are relative to the surviving fish centroid at 12T; z=0 is the surface. Coordinates are model units. This snapshot illustrates '
        'the model, not successful whole-school containment.')
    save(fig,'fig1_model',caption,[directory/'trajectories.npz',directory/'events.jsonl.gz',
        directory/'initial_school.npz',directory/'completion.json',DEVELOPMENT/'controllers.py'],
        {'school_seed':39061002,'policy':'exposed','presence':'DG','frame_elapsed_T':float(trajectory['time'][index]),
         'path_interval_T':[6.,12.],'live_fish':len(live),'capture_count_in_path_interval':len(captures),
         'coordinate_reference_xyz':reference.tolist(),'trajectory_sampling_T':.1})


def development_figure():
    file=DEVELOPMENT/'results/analysis_final/paired_comparison.csv'
    rows=table(file)
    fig,axes=plt.subplots(1,2,figsize=(6.95,2.2),sharey=True)
    fig.subplots_adjust(left=.085,right=.995,wspace=.2,bottom=.23,top=.78)
    for ax,policy,title,letter in zip(axes,['nearest','exposed'],['Nearest feasible','Prefer exposed'],['a','b']):
        selected=sorted([r for r in rows if r['policy']==policy],key=lambda r:r['school_seed'])
        alone=[int(r['dolphin_food_alone']) for r in selected]
        mixed=[int(r['dolphin_food_with_gannets']) for r in selected]
        x=np.arange(2)
        for offset,values,color,label in [(-.18,alone,D,'Dolphins only'),(.18,mixed,DG,'With gannets')]:
            bars=ax.bar(x+offset,values,.32,color=color,label=label,zorder=3)
            ax.bar_label(bars,padding=2,fontsize=9)
        panel(ax,letter,title);ax.set_ylim(0,36);ax.set_yticks([0,10,20,30])
        ax.set_xticks(x,[f'School {i+1}\n{r["school_seed"]}' for i,r in enumerate(selected)])
    axes[0].set_ylabel('Dolphin captures / 36T')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.5,1.015))
    caption=('Development comparison of the two dolphin target-selection rules. Bars show actual '
        'dolphin captures in matched 36T encounters with 12 dolphins, with or without 3 gannets. '
        'Each policy was tested on the same two development schools with one random-stream setting. '
        'Nearest targeting changed from 55 to 53 captures in total; exposed targeting changed from '
        '41 to 48. The exposed policy was selected for follow-up on this development evidence. '
        'Individual school outcomes are shown without confidence intervals.')
    save(fig,'fig2_development',caption,[file,DEVELOPMENT/'results/analysis_final/analysis_audit.json'],rows)


def replication_figure():
    base=REPLICATION/'results/full_36T_v1/cases';pairs=[];inputs=[]
    expected=[base/f's{s}_exposed_{g}_c{c}' for s in (39063501,39063502)
              for c in (61001,61002) for g in ('D','DG')]
    if not all((p/'completion.json').exists() for p in expected):
        print('fig3_replication: pending sealed 36T pairs; no placeholder generated',flush=True)
        return False
    for seed in (39063501,39063502):
        for capture in (61001,61002):
            summaries={}
            for presence in ('D','DG'):
                directory=base/f's{seed}_exposed_{presence}_c{capture}'
                require_sealed(directory,['summary.json','audit.json'])
                summary=read(directory/'summary.json')
                assert summary['status']=='complete' and abs(summary['actual_duration']-36.)<1e-7
                assert read(directory/'audit.json')['status']=='passed'
                summaries[presence]=summary;inputs.extend([directory/'summary.json',directory/'completion.json'])
            a=summaries['D']['species']['D']['captures'];b=summaries['DG']['species']['D']['captures']
            pairs.append({'school_seed':seed,'capture_seed':capture,'D':a,'DG':b,'difference':b-a})
    fig,axes=plt.subplots(1,2,figsize=(7.05,2.4),gridspec_kw={'width_ratios':[1.45,1]})
    fig.subplots_adjust(left=.075,right=.995,wspace=.58,bottom=.29,top=.77)
    x=np.array([0.,.9,2.25,3.15])
    for offset,key,color,label in [(-.16,'D',D,'Dolphins only'),(.16,'DG',DG,'With gannets')]:
        bars=axes[0].bar(x+offset,[p[key] for p in pairs],.29,color=color,label=label,zorder=3)
        axes[0].bar_label(bars,padding=2,fontsize=8.5)
    panel(axes[0],'a','Fresh-school captures')
    axes[0].set_ylabel('Dolphin captures / 36T')
    axes[0].set_ylim(0,max(max(p['D'],p['DG']) for p in pairs)+7)
    axes[0].set_xticks(x,[str(p['capture_seed']) for p in pairs])
    axes[0].text(.45,-.34,'School 39063501',ha='center',transform=axes[0].get_xaxis_transform(),fontsize=8.5)
    axes[0].text(2.7,-.34,'School 39063502',ha='center',transform=axes[0].get_xaxis_transform(),fontsize=8.5)
    axes[0].axvline(1.575,color='#D5DEE5',lw=.7)
    panel(axes[1],'b','Paired change')
    values=[p['difference'] for p in pairs];y=np.arange(4)[::-1]
    axes[1].axvline(0,color='#74828E',lw=.8)
    for yy,p in zip(y,pairs):
        axes[1].plot([0,p['difference']],[yy,yy],color=D,lw=1.2)
        axes[1].scatter([p['difference']],[yy],s=35,color=D,zorder=3)
        axes[1].annotate(f'{p["difference"]:+d}',(p['difference'],yy),xytext=(5,5),
                         textcoords='offset points',fontsize=8.5)
    axes[1].set_yticks(y,[f'S{i//2+1} / {p["capture_seed"]}' for i,p in enumerate(pairs)])
    axes[1].set_xlabel('Capture difference (DG − D)')
    axes[1].set_xlim(min(0,min(values))-2,max(0,max(values))+3)
    axes[1].set_ylim(-.6,3.7);axes[1].grid(False)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.5,1.015))
    caption=('Fresh-school replication of the frozen exposed-target policy. (a) Actual dolphin '
        'captures with and without gannets for two fresh schools crossed with two random-stream '
        'settings; labels 61001 and 61002 identify those settings. (b) The within-pair capture '
        'difference; S1 and S2 denote schools 39063501 and 39063502. All encounters last 36T and retain identical dolphin rules and starting '
        'conditions within each pair. Four stochastic comparisons represent two independent '
        'school configurations, not four independent schools. No confidence intervals are shown.')
    save(fig,'fig3_replication',caption,inputs,pairs)
    return True


def mechanism_figure():
    """Updated Figure 4: joint controls and the initial-depth transient."""
    depth_base=DEPTH/'results/full_36T_v1/cases'
    prior_base=REPLICATION/'results/full_36T_v1/cases'
    inputs=[];records={};pairs=[]
    for seed in (39063501,39063502):
        for treatment,cap in [('baseline',61001),('baseline',61002),('depth8',61001),('depth11',61001)]:
            directory=depth_base/f's{seed}_{treatment}_G_c{cap}'
            require_sealed(directory,['summary.json','audit.json','school_metrics.json'])
            summary=read(directory/'summary.json');metrics=read(directory/'school_metrics.json')
            assert read(directory/'audit.json')['status']=='passed'
            assert summary['status']=='complete' and abs(summary['actual_duration']-36.)<1e-7
            assert summary['species']['D']['count']==0 and summary['species']['G']['count']==3
            records[(seed,treatment,cap)]={'summary':summary,'metrics':metrics}
            inputs.extend(directory/name for name in ('summary.json','school_metrics.json','completion.json'))
        for cap in (61001,61002):
            summaries={}
            for presence in ('D','DG'):
                directory=prior_base/f's{seed}_exposed_{presence}_c{cap}'
                require_sealed(directory,['summary.json','audit.json'])
                summary=read(directory/'summary.json')
                assert summary['status']=='complete' and abs(summary['actual_duration']-36.)<1e-7
                assert read(directory/'audit.json')['status']=='passed'
                summaries[presence]=summary
                inputs.extend(directory/name for name in ('summary.json','completion.json'))
            d=summaries['D']['species']['D']['captures']
            md=summaries['DG']['species']['D']['captures']
            g=records[(seed,'baseline',cap)]['summary']['species']['G']['captures']
            mg=summaries['DG']['species']['G']['captures']
            pairs.append({'school_seed':seed,'capture_seed':cap,'D_alone':d,'D_mixed':md,
                          'G_alone':g,'G_mixed':mg,'D_difference':md-d,'G_difference':mg-g})
    assert [p['D_difference'] for p in pairs]==[1,4,1,8]
    assert [p['G_difference'] for p in pairs]==[-1,1,-1,7]
    fig,axes=plt.subplots(1,3,figsize=(7.1,2.55),gridspec_kw={'width_ratios':[1.12,1.,1.12]})
    fig.subplots_adjust(left=.065,right=.995,wspace=.58,bottom=.255,top=.84)
    y=np.arange(4)[::-1]
    axes[0].axvline(0,color='#74828E',lw=.8)
    for key,offset,color,label,marker in [('D_difference',.11,D,'Dolphins','o'),
                                         ('G_difference',-.11,DG,'Gannets','s')]:
        for j,(yy,pair) in enumerate(zip(y,pairs)):
            value=pair[key]
            axes[0].plot([0,value],[yy+offset]*2,color=color,lw=1.1)
            axes[0].scatter(value,yy+offset,color=color,marker=marker,s=22,zorder=3,
                            label=label if j==0 else None)
    panel(axes[0],'a','Paired joint changes')
    axes[0].grid(False)
    axes[0].set(yticks=y,yticklabels=['S1 / 1','S1 / 2','S2 / 1','S2 / 2'],
                xlabel='Capture change / 36T',xlim=(-2,10),ylim=(-.5,4.35),xticks=[-2,0,4,8])
    axes[0].legend(loc='upper left',frameon=False,fontsize=7.1,ncol=2,
                   columnspacing=.55,handlelength=.7,handletextpad=.35,borderaxespad=0.)
    depth_data=[]
    for j,seed in enumerate((39063501,39063502)):
        selected=[records[(seed,t,61001)] for t in ('baseline','depth8','depth11')]
        x=[r['metrics'][0]['depth_mean'] for r in selected]
        counts=[r['summary']['species']['G']['captures'] for r in selected]
        axes[1].plot(x,counts,marker=['o','s'][j],ls=['-','--'][j],color=[D,INK][j],
                     markersize=4,lw=1.,label=f'School {j+1}')
        depth_data.append({'school_seed':seed,'capture_seed':61001,
                           'initial_mean_depth':x,'gannet_captures':counts})
    panel(axes[1],'b','Initial-depth feeding')
    axes[1].set(xlabel='Initial mean depth',ylabel='Gannet captures / 36T',
                xlim=(5.,11.7),ylim=(0,12.7),xticks=[5.57,8,11],yticks=[0,4,8,12])
    axes[1].set_xticklabels(['5.57','8','11'])
    axes[1].legend(loc='upper right',frameon=False,fontsize=7.2,handlelength=1.5,borderaxespad=.1)
    curves=[]
    colors={'baseline':D,'depth8':DG,'depth11':'#8C539A'}
    labels={'baseline':'5.57','depth8':'8','depth11':'11'}
    for treatment in ('baseline','depth8','depth11'):
        for j,seed in enumerate((39063501,39063502)):
            metrics=records[(seed,treatment,61001)]['metrics']
            times=[r['elapsed'] for r in metrics]
            fractions=[r['reference_accessible_fraction'] for r in metrics]
            axes[2].plot(times,fractions,color=colors[treatment],ls=['-','--'][j],lw=.9,
                         alpha=.85,label=labels[treatment] if j==0 else None)
            curves.append({'school_seed':seed,'treatment':treatment,'capture_seed':61001,
                           'elapsed_T':times,'reference_accessible_fraction':fractions})
    panel(axes[2],'c','Realised accessibility')
    axes[2].set(xlabel='Elapsed time (T)',ylabel='Fraction at depth ≤7.93',
                xlim=(0,36),ylim=(-.03,1.28),xticks=[0,12,24,36],yticks=[0,.5,1.])
    axes[2].legend(loc='upper right',title='Initial depth',title_fontsize=7.,fontsize=7.1,
                   ncol=3,frameon=False,columnspacing=.4,handlelength=1.1,handletextpad=.3,
                   borderaxespad=.05)
    caption=('Matching gannet-only controls and initial-depth results. (a) Dolphin capture change '
        '(DG minus D) and gannet change (DG minus G) for the same four fresh-school comparisons. '
        'S1=39063501 and S2=39063502; repetitions 1 and 2 identify settings 61001 and 61002. '
        'Both species improve in two repetitions; four comparisons represent two independent schools. '
        '(b) Gannet-only captures over 36T across initial vertical translations, using setting 61001; '
        'lines join the same school, not fitted response curves. (c) Fraction of surviving fish within '
        'the reference target-depth envelope 7.93028, with colour identifying initial mean depth and '
        'solid/dashed lines identifying schools 1/2. This is a geometric eligibility reference, '
        'not guaranteed interception. Initial depth is not maintained; movement and selective removal '
        'can alter the survivor fraction. No uncertainty intervals are shown.')
    save(fig,'fig4_mechanism',caption,inputs+[DEPTH/'protocol.json',
        DEPTH/'results/full_36T_v1/analysis_final/analysis_audit.json'],
        {'paired_changes':pairs,'depth_captures':depth_data,'accessibility_curves':curves,
         'independent_schools':2,'joint_positive_pairs':2,'total_pairs':4,
         'reference_depth_envelope':7.93028,'initial_depth_is_maintained':False})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',choices=['all','model','development','replication','mechanism'],default='all')
    args=parser.parse_args()
    for name,fn in [('model',model_figure),('development',development_figure),
                    ('replication',replication_figure),('mechanism',mechanism_figure)]:
        if args.only in ('all',name):fn()


if __name__=='__main__':main()
