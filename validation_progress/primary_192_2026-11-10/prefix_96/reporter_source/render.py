"""Private native-free templates; real data require audited complete paired blocks."""
from __future__ import annotations
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np
from gate import HERE,SCHOOLS,LABELS,GRIDS,normalise,accept,require,sha,read
T_CRITICAL=2.4898797034798923
UNIT='fish captured per individual over the nominal 36T encounter'

def summaries(data):
    n=data['school_count'];index={(r['school_seed'],r['replicate_label'],r['grid'],r['presence']):r for r in data['rows']}
    worlds=[];schools=[];estimates=[]
    for species,count in [('D',12),('G',36)]:
        for grid in GRIDS:
            for school in SCHOOLS[:n]:
                alone=mixed=0
                for label in LABELS:
                    a=index[school,label,grid,species][species+'_captures'];m=index[school,label,grid,'DG'][species+'_captures'];alone+=a;mixed+=m
                    worlds.append(dict(school_seed=school,replicate_label=label,grid=grid,species=species,control_group_captures=a,mixed_group_captures=m,integer_capture_change=m-a,control_food=a/count,mixed_food=m/count,partner_gain=(m-a)/count))
                schools.append(dict(school_seed=school,grid=grid,species=species,labels_averaged=2,control_count_sum=alone,mixed_count_sum=mixed,integer_change_sum=mixed-alone,control_food=alone/(2*count),mixed_food=mixed/(2*count),partner_gain=(mixed-alone)/(2*count)))
            points=[r for r in schools if r['species']==species and r['grid']==grid];mean=sum(r['integer_change_sum'] for r in points)/(n*2*count);control=sum(r['control_count_sum'] for r in points)/(n*2*count);mixed=sum(r['mixed_count_sum'] for r in points)/(n*2*count)
            row=dict(grid=grid,species=species,independent_schools=n,nested_labels_per_school=2,unit=UNIT,control_food=control,mixed_food=mixed,partner_gain_mean=mean,school_sd=float(np.std([r['partner_gain'] for r in points],ddof=1)),relative_percent_ratio_of_matched_means=100*mean/control if control else None)
            if data['stage']=='final':
                if data['synthetic']:
                    se=row['school_sd']/math.sqrt(n);row['se']=se;row['student_t_97_5_ci']=[mean-T_CRITICAL*se,mean+T_CRITICAL*se];row['bootstrap_97_5_ci']=None
                else:
                    owner=data['statistics']['primary']['species'][species] if grid=='fine' else data['statistics']['secondary']['coarse'][species]
                    require(abs(owner['mean']-mean)<1e-13 and abs(owner['school_sd']-row['school_sd'])<1e-13,'Saved stats disagree with label-averaged school effects')
                    require(owner['n_schools']==16 and owner['n_worlds']==32 and owner['df']==15,'Incorrect final independent unit')
                    se=row['school_sd']/4;require(abs(owner['se']-se)<1e-13,'Saved school-mean SE differs');expected=[mean-T_CRITICAL*se,mean+T_CRITICAL*se]
                    require(np.allclose(owner['student_t_97_5_ci'],expected,rtol=0,atol=1e-13),'Saved t interval differs')
                    row.update(se=owner['se'],student_t_97_5_ci=owner['student_t_97_5_ci'],bootstrap_97_5_ci=owner['bootstrap_97_5_ci'],within_school_variance_W=owner['within_school_variance_W'],conditional_mcse=owner['conditional_mcse'])
            estimates.append(row)
    if data['stage']=='final' and not data['synthetic']:
        saved={r['school_seed']:r for r in data['statistics']['school_points']};require(set(saved)==set(SCHOOLS),'All16 final school points required')
        for row in schools:require(abs(saved[row['school_seed']][row['grid']+'_'+row['species']]-row['partner_gain'])<1e-13,'Final school-vector mismatch')
        require(data['statistics']['t_critical']==T_CRITICAL,'Different final interval constant')
        require((data['statistics']['bootstrap']['draws'],data['statistics']['bootstrap']['seed'])==(50000,8611030),'Changed prespecified sensitivity procedure')
        joint=all(r['student_t_97_5_ci'][0]>0 for r in estimates if r['grid']=='fine')
        require(joint==data['statistics']['primary']['joint_criterion_met'],'Final fine-grid criterion mismatch')
    else:joint=None
    return dict(stage=data['stage'],synthetic=data['synthetic'],independent_schools=n,case_count=len(data['rows']),nested_labels=2,unit=UNIT,school_points=schools,world_points=worlds,estimates=estimates,primary_joint_criterion_met=joint,interval_scope='Final 192 only: saved 97.5% marginal school-mean t intervals; fine is primary' if data['stage']=='final' else 'Descriptive only: no confidence intervals or primary decision',new_bootstrap_draws=0,native_model_imports=0,native_steps=0)

def figures(summary,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    synthetic=summary['synthetic'];stage=summary['stage'];n=summary['independent_schools'];species_all=('D','G')
    def gain(ax,species):
        for school in SCHOOLS[:n]:
            points=[next(r for r in summary['school_points'] if r['school_seed']==school and r['grid']==g and r['species']==species)['partner_gain'] for g in GRIDS]
            ax.plot([0,1],points,'o-',color='#788d9b',lw=.7,ms=3,alpha=.55)
        for r in summary['world_points']:
            if r['species']==species:ax.scatter(list(GRIDS).index(r['grid'])+(-.035 if r['replicate_label']==71001 else .035),r['partner_gain'],s=8,color='#778b9d',alpha=.17)
        for x,g in enumerate(GRIDS):
            row=next(r for r in summary['estimates'] if r['species']==species and r['grid']==g);m=row['partner_gain_mean']
            if stage=='final':
                lo,hi=row['student_t_97_5_ci'];ax.errorbar(x,m,yerr=[[m-lo],[hi-m]],fmt='D',ms=6,capsize=3,color='#092f46' if g=='fine' else '#ac6915',zorder=5)
            else:ax.plot(x,m,'D',color='#092f46',ms=6,zorder=5)
        ax.axhline(0,color='#68757e',lw=.8,ls='--');ax.set_xticks([0,1],['Coarse\n0.00125T','Fine\n0.000625T']);ax.set_xlim(-.18,1.18);ax.set_ylabel(('Change in fish per dolphin' if species=='D' else 'Change in fish per gannet')+'\nover 36T');ax.set_title(('Dolphins' if species=='D' else 'Gannets')+' — partner gain')
    def absolute(ax,species):
        for r in summary['world_points']:
            if r['species']!=species:continue
            base=0 if r['grid']=='coarse' else 2;j=-.035 if r['replicate_label']==71001 else .035
            ax.scatter([base+j,base+1+j],[r['control_food'],r['mixed_food']],s=8,color='#778b9d',alpha=.17)
        for school in SCHOOLS[:n]:
            for base,g in [(0,'coarse'),(2,'fine')]:
                r=next(r for r in summary['school_points'] if r['school_seed']==school and r['grid']==g and r['species']==species)
                ax.plot([base,base+1],[r['control_food'],r['mixed_food']],'o-',color='#788d9b',lw=.7,ms=3,alpha=.5)
        for base,g in [(0,'coarse'),(2,'fine')]:
            r=next(r for r in summary['estimates'] if r['grid']==g and r['species']==species);ax.plot([base,base+1],[r['control_food'],r['mixed_food']],'D',ms=6,color='#092f46')
        ax.set_xticks(range(4),['Alone\ncoarse','Mixed\ncoarse','Alone\nfine','Mixed\nfine']);ax.set_ylabel(('Fish per dolphin' if species=='D' else 'Fish per gannet')+'\nover 36T');ax.set_title(('Dolphins' if species=='D' else 'Gannets')+' — absolute return')
    def finish(fig,name):
        if stage=='final':
            title=(f'Synthetic final-layout — {n} schools × 2 nested worlds; H1/G36' if synthetic else f'192 complete cases — {n} validation schools × 2 nested worlds; H1/G36')
        else:title=f'{n} validation schools × 2 nested worlds; H1/G36 — descriptive only'
        caption='Faint points: nested world labels; lines: school means; diamonds: equal-school means.\n'
        caption+=('Bars: final 97.5% school-mean t intervals; fine is primary, coarse secondary.' if stage=='final' else 'No confidence intervals or primary decision before all 192 complete cases.')
        fig.suptitle(title,fontsize=10);fig.text(.5,.012,caption,ha='center',fontsize=7)
        if synthetic:fig.text(.5,.5,'SYNTHETIC LAYOUT ONLY\nNOT STUDY RESULTS',ha='center',va='center',fontsize=25,color='#b11c24',alpha=.28,rotation=18)
        fig.tight_layout(rect=[0,.09,1,.94]);prefix='SYNTHETIC_' if synthetic else ''
        for extension in ('png','pdf'):fig.savefig(out/(prefix+name+'.'+extension))
        plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(8.1,3.6))
    for ax,sp in zip(axes,species_all):gain(ax,sp)
    finish(fig,'paired_grid_effects')
    fig,axes=plt.subplots(2,2,figsize=(8.1,6.0))
    for i,sp in enumerate(species_all):absolute(axes[i,0],sp);gain(axes[i,1],sp)
    finish(fig,'absolute_and_partner')

def final_statistics_lines(summary):
    """Format the saved final intervals; bootstrap remains a separate sensitivity."""
    if summary['stage']!='final':return []
    rows=summary['estimates']
    lines=['','## Final school-mean estimates and prespecified t intervals','',
           'Food units throughout: fish captured per dolphin or gannet over the complete 36T encounter. Fine-grid endpoints are primary; coarse-grid intervals are secondary. SD describes the sixteen label-averaged school effects; SE is the school SD divided by four.','',
           '| Species | Grid and role | Mean partner gain | School SD | SE | 97.5% school-mean t interval |',
           '|---|---|---:|---:|---:|---:|']
    for r in rows:
        lo,hi=r['student_t_97_5_ci'];role='primary' if r['grid']=='fine' else 'secondary'
        lines.append(f"| {r['species']} | {r['grid']} ({role}) | {r['partner_gain_mean']:+.6f} | {r['school_sd']:.6f} | {r['se']:.6f} | [{lo:+.6f}, {hi:+.6f}] |")
    lines+=['','## Bootstrap sensitivity — not the primary decision','',
            'These are the separately saved 97.5% whole-school percentile intervals from the fixed 50,000-draw sensitivity analysis. The reporter draws no samples and does not substitute these intervals for the prespecified t criterion.','',
            '| Species | Grid | Saved bootstrap 97.5% interval (sensitivity) |','|---|---|---:|']
    for r in rows:
        interval=r['bootstrap_97_5_ci'];value='not supplied in synthetic layout' if interval is None else f'[{interval[0]:+.6f}, {interval[1]:+.6f}]'
        lines.append(f"| {r['species']} | {r['grid']} | {value} |")
    return lines

def report_lines(s):
    lines=['# '+('SYNTHETIC LAYOUT ONLY — NOT RESULTS' if s['synthetic'] else ('Audited descriptive paired-block progress' if s['stage']=='prefix' else 'Complete prespecified validation')),'',f"{s['independent_schools']} schools; two nested randomness labels; {s['case_count']} complete paired cases. Units: {UNIT}.",'',s['interval_scope']+'.','', '| Species | Grid | Alone | Mixed | Partner gain | Relative change of matched means |','|---|---|---:|---:|---:|---:|']
    for r in s['estimates']:
        relative='undefined (zero control)' if r['relative_percent_ratio_of_matched_means'] is None else f"{r['relative_percent_ratio_of_matched_means']:+.1f}%"
        lines.append(f"| {r['species']} | {r['grid']} | {r['control_food']:.4f} | {r['mixed_food']:.4f} | {r['partner_gain_mean']:+.4f} | {relative} |")
    lines+=final_statistics_lines(s)
    lines+=['','Labels alter capture, tie and gannet-target streams, with readiness fixed by school/identity; they are not new schools or isolated capture-probability noise. Travel, failures, recovery and any coherent absorbing prey depletion remain within the nominal 36T food denominator. Discovery schools are not pooled.','']
    if s['primary_joint_criterion_met'] is not None:lines+=['Prespecified fine-grid joint criterion: '+('met' if s['primary_joint_criterion_met'] else 'not met')+'. The criterion alone does not establish absence of benefit; interpret each estimate and interval.','']
    else:lines+=['No confirmatory decision is available. All later prespecified blocks remain mandatory; settings and grids are not reselected.','']
    return lines

def export(data,out):
    require(not out.exists(),'Never overwrite an earlier reporting snapshot');s=summaries(data);out.mkdir(parents=True)
    for file,rows in [('paired_school_means.csv',s['school_points']),('nested_world_effects.csv',s['world_points'])]:
        with (out/file).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'report_data.json').write_text(json.dumps(s,indent=2,allow_nan=False)+'\n');figures(s,out)
    lines=report_lines(s)
    (out/'REPORT.md').write_text('\n'.join(lines))
    receipt=dict(status='SYNTHETIC_LAYOUT_ONLY' if data['synthetic'] else 'audited_reporting_export',stage=data['stage'],synthetic=data['synthetic'],schools=data['school_count'],cases=len(data['rows']),primary_joint_criterion_met=s['primary_joint_criterion_met'],source_proofs=data.get('proofs',{}),source_pins_sha256=data.get('source_pins_sha256'),renderer_sha256=sha(__file__),gate_sha256=sha(HERE/'gate.py'),native_steps=0,simulator_imports=0,new_bootstrap_draws=0,files={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    (out/'render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['prefix','final'],default='prefix');p.add_argument('--through-block',type=int,default=1);p.add_argument('--output',type=Path,required=True);p.add_argument('--synthetic-fixture',type=Path);p.add_argument('--pins',type=Path,default=HERE/'source_pins.json');a=p.parse_args()
    if a.synthetic_fixture:
        fixture=read(a.synthetic_fixture);require(fixture['kind']=='SYNTHETIC_LAYOUT_ONLY' and fixture['not_study_results'] is True,'Fixture must be explicitly synthetic')
        data=dict(stage=a.stage,school_count=fixture['school_count'],rows=normalise(fixture['rows'],fixture['school_count'],synthetic=True),statistics=None,synthetic=True,proofs={str(a.synthetic_fixture):sha(a.synthetic_fixture)})
        require((a.stage=='final')==(data['school_count']==16),'Fixture stage/count mismatch')
    else:data=accept(a.stage,a.through_block,a.pins)
    result=export(data,a.output);require(not any(n=='fish_sim' or n.startswith('fish_sim.') for n in sys.modules),'No model imports');print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
if __name__=='__main__':main()
