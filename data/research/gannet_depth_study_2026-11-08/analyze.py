"""Read sealed depth outputs; no simulator imports or model steps."""
from __future__ import annotations
import argparse,csv,gzip,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'exposed_replication_2026-11-08/results/full_36T_v1/cases'
COLORS={'baseline':'#087F8C','depth8':'#D98525','depth11':'#8C539A'}
plt.rcParams.update({'font.size':9,'axes.titlesize':10,'axes.spines.right':False,'axes.spines.top':False,'pdf.fonttype':42})

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sealed(directory,duration):
 seal=read(directory/'completion.json');assert seal['status']=='complete'
 for name,digest in seal['files'].items():assert sha(directory/name)==digest,(directory,name)
 summary=read(directory/'summary.json');assert summary['status']=='complete' and abs(summary['actual_duration']-duration)<1e-7
 assert read(directory/'audit.json')['status']=='passed'
 return summary,read(directory/'school_metrics.json')
def savefig(fig,out,name):
 fig.savefig(out/(name+'.pdf'),bbox_inches='tight');fig.savefig(out/(name+'.png'),bbox_inches='tight',dpi=200);plt.close(fig)
def brief_depth_metrics(rows):
 t=np.array([r['elapsed'] for r in rows]);d=np.array([r['depth_mean'] for r in rows]);a=np.array([r['reference_accessible_fraction'] for r in rows])
 return dict(initial_mean_depth=d[0],final_mean_depth=d[-1],mean_depth_over_encounter=float(np.trapezoid(d,t)/(t[-1]-t[0])),initial_accessible_fraction=a[0],final_accessible_fraction=a[-1],mean_accessible_fraction=float(np.trapezoid(a,t)/(t[-1]-t[0])),surface_reflections=max(r['surface_reflections'] for r in rows)-rows[0]['surface_reflections'])
def curves(records,out,name):
 fig,axs=plt.subplots(1,2,figsize=(7.1,2.8),layout='constrained')
 fig.suptitle('Solid: school39063501; dashed: school39063502',fontsize=8.5)
 for treatment in ('baseline','depth8','depth11'):
  matching=[r for r in records if r['treatment']==treatment]
  for j,r in enumerate(matching):
   times=[x['elapsed'] for x in r['metrics']]
   label=treatment.replace('depth','Initial mean ')
   if treatment=='baseline':label='Unshifted (~5.57)'
   axs[0].plot(times,[x['depth_mean'] for x in r['metrics']],color=COLORS[treatment],ls='-' if j==0 else '--',label=label if j==0 else None)
   axs[1].plot(times,[x['reference_accessible_fraction'] for x in r['metrics']],color=COLORS[treatment],ls='-' if j==0 else '--')
 axs[0].axhspan(3,7,color='#eeeeee',zorder=-1);axs[0].set(xlabel='Elapsed model time (T)',ylabel='Mean fish depth',title='(a) Realised depth')
 axs[1].set(xlabel='Elapsed model time (T)',ylabel='Fraction at depth ≤7.93',ylim=(-.03,1.03),title='(b) Reference accessibility')
 axs[0].legend(frameon=False,fontsize=8);savefig(fig,out,name)
def controls(output):
 out=output/'analysis';out.mkdir(exist_ok=False);records=[];rows=[]
 for seed in (39063501,39063502):
  for treatment in ('depth8','depth11'):
   case=output/'cases'/f's{seed}_{treatment}_none_c61001';summary,metrics=sealed(case,4.)
   assert summary['species']['G']['count']==0 and summary['species']['D']['count']==0
   row=dict(school_seed=seed,treatment=treatment,**brief_depth_metrics(metrics));rows.append(row)
   records.append(dict(treatment=treatment,metrics=metrics))
 assert not any(r['surface_reflections'] for r in rows)
 table(out/'depth_drift.csv',rows);curves(records,out,'predator_free_depth_drift')
 (out/'review.json').write_text(json.dumps(dict(status='passed',rows=rows,interpretation='Four translated fish-only controls; initial-depth relaxation retained as part of model, not corrected.',native_steps=12800),indent=2)+'\n')
 print(json.dumps(rows,indent=2))
def full(output):
 out=output/'analysis_final';out.mkdir(exist_ok=False);rows=[];records=[];receipts=[]
 for treatment,cap in [('baseline',61001),('baseline',61002),('depth8',61001),('depth11',61001)]:
  for seed in (39063501,39063502):
   case=output/'cases'/f's{seed}_{treatment}_G_c{cap}';summary,metrics=sealed(case,36.)
   assert summary['species']['D']['count']==0 and summary['species']['G']['count']==3
   g=summary['species']['G'];row=dict(school_seed=seed,treatment=treatment,capture_seed=cap,G_captures=g['captures'],G_launches=g['launches'],G_contacts=g['contacts'],water_entries=summary['water_entries'],G_captures_per_individual_T=g['captures']/108.,captures_per_launch=g['captures']/g['launches'] if g['launches'] else None,contacts_per_launch=g['contacts']/g['launches'] if g['launches'] else None,**brief_depth_metrics(metrics));rows.append(row)
   receipts.append({'case':str(case),'completion_sha256':sha(case/'completion.json')})
   if cap==61001:records.append(dict(treatment=treatment,metrics=metrics))
 assert not any(r['surface_reflections'] for r in rows)
 table(out/'case_outcomes.csv',rows);curves(records,out,'depth_and_accessibility')
 fig,axs=plt.subplots(1,2,figsize=(7.1,2.8),layout='constrained')
 for j,seed in enumerate((39063501,39063502)):
  rr=[r for r in rows if r['school_seed']==seed and r['capture_seed']==61001]
  rr.sort(key=lambda r:r['initial_mean_depth']);x=[r['initial_mean_depth'] for r in rr]
  axs[0].plot(x,[r['G_captures_per_individual_T'] for r in rr],marker=['o','s'][j],label=str(seed))
  axs[1].plot(x,[r['G_launches'] for r in rr],marker=['o','s'][j],label=str(seed))
 axs[0].set(xlabel='Initial mean depth (model units)',ylabel='Captures / gannet / T',title='(a) Gannet-only feeding');axs[0].legend(frameon=False,fontsize=8)
 axs[1].set(xlabel='Initial mean depth (model units)',ylabel='Launches / 36T',title='(b) Attack opportunities');savefig(fig,out,'gannet_depth_feeding')
 joint=[]
 for r in rows:
  if r['treatment']!='baseline':continue
  seed,cap=r['school_seed'],r['capture_seed']
  dm,_=sealed(PRIOR/f's{seed}_exposed_D_c{cap}',36.);mixed,_=sealed(PRIOR/f's{seed}_exposed_DG_c{cap}',36.)
  dc,md=dm['species']['D']['captures'],mixed['species']['D']['captures'];mg=mixed['species']['G']['captures'];gonly=r['G_captures']
  joint.append(dict(school_seed=seed,capture_seed=cap,D_alone=dc,D_mixed=md,D_difference=md-dc,G_alone=gonly,G_mixed=mg,G_difference=mg-gonly,D_rate_difference=(md-dc)/432.,G_rate_difference=(mg-gonly)/108.,joint_positive=md>dc and mg>gonly))
 joint.sort(key=lambda r:(r['school_seed'],r['capture_seed']));table(out/'reciprocity_pairs.csv',joint)
 school=[]
 for seed in (39063501,39063502):
  rr=[r for r in joint if r['school_seed']==seed]
  school.append(dict(school_seed=seed,D_mean_difference=float(np.mean([r['D_difference'] for r in rr])),G_mean_difference=float(np.mean([r['G_difference'] for r in rr])),paired_repetitions=len(rr)))
 table(out/'reciprocity_school_means.csv',school)
 fig,axs=plt.subplots(1,2,figsize=(7.1,2.7),layout='constrained')
 labels=[f'S{i//2+1} / {r["capture_seed"]}' for i,r in enumerate(joint)]
 for ax,key,title,color in zip(axs,['D_difference','G_difference'],['(a) Dolphin change (DG − D)','(b) Gannet change (DG − G)'],['#087F8C','#D98525']):
  y=np.arange(4)[::-1];ax.axvline(0,color='#777777',lw=.8)
  for yy,r in zip(y,joint):ax.plot([0,r[key]],[yy,yy],color=color);ax.scatter(r[key],yy,color=color,zorder=3)
  ax.set(yticks=y,yticklabels=labels,xlabel='Capture difference / 36T',title=title)
 savefig(fig,out,'joint_mutual_benefit')
 report=dict(status='passed',full_cases=8,independent_schools=2,depth_pairs_per_treatment=2,baseline_stochastic_pairs=4,native_steps=230400,full_T=288.,case_outcomes=rows,reciprocity_pairs=joint,school_means=school,inputs=receipts,limitations=['Initial-depth intervention permits native habitat relaxation.','Depth-only accessibility is a reference envelope, not guaranteed physical interception.','Four baseline random repetitions share two school configurations.','No confidence intervals, biological unit calibration, or timing-coupling inference.','D gains and G gains must occur within same matched pair; no pooling across depths for reciprocity.'])
 (out/'analysis_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 lines=['# Gannet depth and matching G-only pilot','',f'Eight 36T gannet-only encounters complete; two independent schools. The depth comparison uses capture seed61001 only; the extra baseline stream supplies all four matched G-only controls.','', '| School / stream | D → DG (dolphins) | G → DG (gannets) | Both improve |','|---|---:|---:|---|']
 for r in joint:lines.append(f'| {r["school_seed"]} / {r["capture_seed"]} | {r["D_alone"]} → {r["D_mixed"]} | {r["G_alone"]} → {r["G_mixed"]} | {r["joint_positive"]} |')
 lines+=['','Depth is initially translated, not constrained; realised depth/accessibility curves show relaxation under unchanged habitat preference5±2. These are model-unit pilot findings, not calibration or proof of intentional cooperation.','', 'Source identity, event accounting, unique removals and private stream replay passed each sealed case. Numerical convergence remains unestablished.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'joint':joint,'school_means':school,'depth':rows},indent=2))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--controls',action='store_true');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 (controls if args.controls else full)(args.output.resolve())
if __name__=='__main__':main()
