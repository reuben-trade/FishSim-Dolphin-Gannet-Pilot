"""Complete192 scalar reader: stdlib/Fraction, no model imports or random draws."""
from __future__ import annotations
import math,re
from decimal import Decimal,InvalidOperation
from fractions import Fraction
SEEDS=tuple(range(39065501,39065517));LABELS=(71001,71002)
GRIDS={'coarse':.00125,'fine':.000625};ARMS=('D','G','DG')
CONTRASTS=('fine_D','fine_G','coarse_D','coarse_G','fine_minus_coarse_D','fine_minus_coarse_G')
SECONDARY_CRITICAL=2.131449545559776
PRIMARY_CRITICAL=2.4898797034798923
PROGRAMME_CRITICAL=2.8366274760941357
INDEX_SHA='213f6163d606a90c56b95cb5df3ccb344e600d45dbada84a815fc93c7d2e3279'
class Invalid(ValueError):pass
def need(ok,message):
 if not ok:raise Invalid(message)
def integer(v):
 need(not isinstance(v,bool),'Boolean is not an integer')
 try:d=Decimal(str(v))
 except (InvalidOperation,ValueError):raise Invalid('Finite integer required')
 need(d.is_finite() and d==d.to_integral_value(),'Finite integer required');return int(d)
def number(v):
 need(not isinstance(v,bool),'Boolean is not numeric')
 try:x=float(v)
 except (ValueError,TypeError):raise Invalid('Finite number required')
 need(math.isfinite(x),'Finite number required');return x
def boolean(v):
 if type(v)is bool:return v
 need(v in ('True','False'),'Explicit bool or canonical CSV boolean required');return v=='True'
def same_number(v,w):return number(v)==w
def digest(v):return type(v)is str and re.fullmatch('[0-9a-f]{64}',v)is not None
def aliases(r,names,convert):
 need(any(n in r for n in names),'Missing aliases:'+str(names));xs=[convert(r[n]) for n in names if n in r]
 need(all(x==xs[0] for x in xs),'Conflicting aliases');return xs[0]
def normalise(rows,*,gannets=12,herding=2):
 need((gannets,herding) in ((12,2),(36,1)),'Only locked H2/G12 or original H1/G36')
 cells={}
 for raw in rows:
  s=aliases(raw,('school_seed','school'),integer);label=aliases(raw,('replicate_label','capture_label','capture_seed'),integer)
  need(s in SEEDS and label in LABELS,'Unexpected school/label; no discovery pooling')
  grid=raw.get('grid');arm=raw.get('presence');need(grid in GRIDS and arm in ARMS,'Unexpected grid/arm')
  need(same_number(raw.get('dt'),GRIDS[grid]),'Wrong dt')
  nd=12 if 'D'in arm else 0;ng=gannets if 'G'in arm else 0
  policy=f'H{herding}_G{ng}' if nd else f'Gonly{gannets}'
  name=f's{s}_{grid}_{policy}_{arm}_c{label}'
  need(aliases(raw,('case_name','case_id'),str)==name,'Exact case identity required')
  if 'policy'in raw:need(raw['policy']==policy,'Wrong policy')
  for k,v in (('dolphins',nd),('gannets',ng),('initial_fish',160)):
   need(integer(raw.get(k))==v,'Wrong population:'+k)
  if nd:need(same_number(raw.get('herding_minimum_T'),herding),'Wrong herding duration')
  else:need(raw.get('herding_minimum_T')in(None,'','None'),'G-only has no dolphin herding parameter')
  need(same_number(raw.get('duration_T'),36),'Nominal36T required')
  counts={}
  for sp,count in (('D',nd),('G',ng)):
   values=[integer(raw.get(sp+'_'+m)) for m in ('captures','contacts','launches')]
   need(0<=values[0]<=values[1]<=values[2],'Captures/contacts/launches invalid')
   need(count or values==[0,0,0],'Absent species cannot act')
   counts.update({sp+'_'+m:x for m,x in zip(('captures','contacts','launches'),values)})
  captured=counts['D_captures']+counts['G_captures'];remaining=integer(raw.get('remaining_fish'));steps=integer(raw.get('native_steps'))
  need(0<=captured<=160 and remaining==160-captured,'Unique160 prey accounting required')
  absorbed=boolean(raw.get('native_absorbing_termination'));observed=number(raw.get('actual_duration_T'))
  need(0<observed<=36+1e-7 and steps>0 and steps==round(observed/GRIDS[grid]) and abs(observed-steps*GRIDS[grid])<=1e-7,'Actual physical clock/steps disagree')
  if absorbed:need(remaining==0 and captured==160,'Declared depletion needs all160 unique removals')
  else:need(steps==round(36/GRIDS[grid]) and abs(observed-36)<=1e-7,'Nondepleted encounter must complete36T')
  need(digest(raw.get('completion_sha256')),'Completion SHA required')
  key=(s,label,grid,arm);need(key not in cells,'Duplicate cell/control')
  cells[key]=dict(case_id=name,case_name=name,school_seed=s,replicate_label=label,capture_label=label,capture_seed=label,grid=grid,dt=GRIDS[grid],presence=arm,dolphins=nd,gannets=ng,herding_minimum_T=herding if nd else None,duration_T=36,actual_duration_T=observed,native_steps=steps,native_absorbing_termination=absorbed,remaining_fish=remaining,initial_fish=160,completion_sha256=raw['completion_sha256'],**counts)
 expected={(s,l,g,p) for s in SEEDS for l in LABELS for g in GRIDS for p in ARMS}
 need(set(cells)==expected,'All192 exact cases required; no partial inference or zero imputation')
 return [cells[s,l,g,p] for s in SEEDS for l in LABELS for g in GRIDS for p in ARMS]
def signs(values):return dict(positive=sum(x>0 for x in values),zero=sum(x==0 for x in values),negative=sum(x<0 for x in values))
def summarise(points,worlds,critical):
 mean=sum(points,Fraction())/16;variance=sum(((x-mean)**2 for x in points),Fraction())/15
 sd=math.sqrt(float(variance));se=sd/4;w=sum(((a-b)**2/2 for a,b in worlds),Fraction())/16
 return dict(mean=float(mean),mean_exact=str(mean),school_sd=sd,se=se,n_schools=16,n_worlds=32,df=15,student_t_ci=[float(mean)-critical*se,float(mean)+critical*se],school_signs=signs(points),world_signs=signs([v for pair in worlds for v in pair]),within_school_variance_W=float(w),conditional_mcse=math.sqrt(float(w)/32),label_effect_differences=[float(a-b) for a,b in worlds],mean_rate_change_per_individual_per_T=float(mean/36))
def calculate(rows,*,gannets=12,herding=2):
 cases=normalise(rows,gannets=gannets,herding=herding);bank={(r['school_seed'],r['replicate_label'],r['grid'],r['presence']):r for r in cases}
 deltas={};world=[];gridworld=[];school=[];fractions={};worlds={}
 for s in SEEDS:
  for l in LABELS:
   for g in GRIDS:
    mix=bank[s,l,g,'DG'];d=bank[s,l,g,'D'];b=bank[s,l,g,'G'];dd=mix['D_captures']-d['D_captures'];gd=mix['G_captures']-b['G_captures'];deltas[s,l,g]=(dd,gd)
    world.append(dict(school_seed=s,replicate_label=l,grid=g,D_mixed_group_captures=mix['D_captures'],D_alone_group_captures=d['D_captures'],G_mixed_group_captures=mix['G_captures'],G_alone_group_captures=b['G_captures'],D_group_capture_change=dd,G_group_capture_change=gd,D_effect_per_individual_36T=float(Fraction(dd,12)),G_effect_per_individual_36T=float(Fraction(gd,gannets)),D_rate_change_per_individual_per_T=float(Fraction(dd,12*36)),G_rate_change_per_individual_per_T=float(Fraction(gd,gannets*36))))
  pairs=[]
  for l in LABELS:
   f,c=deltas[s,l,'fine'],deltas[s,l,'coarse'];pairs.append([Fraction(f[0],12),Fraction(f[1],gannets),Fraction(c[0],12),Fraction(c[1],gannets),Fraction(f[0]-c[0],12),Fraction(f[1]-c[1],gannets)])
   gridworld.append(dict(school_seed=s,replicate_label=l,D_group_effect_fine_minus_coarse=f[0]-c[0],G_group_effect_fine_minus_coarse=f[1]-c[1],D_effect_fine_minus_coarse_per_individual_36T=float(pairs[-1][4]),G_effect_fine_minus_coarse_per_individual_36T=float(pairs[-1][5])))
  vector=[(a+b)/2 for a,b in zip(*pairs)];fractions[s]=dict(zip(CONTRASTS,vector));worlds[s]=dict(zip(CONTRASTS,zip(*pairs)))
  school.append(dict(school_seed=s,**{k:float(v) for k,v in fractions[s].items()}))
 critical=SECONDARY_CRITICAL if herding==2 else PRIMARY_CRITICAL
 summaries={k:summarise([fractions[s][k] for s in SEEDS],[worlds[s][k] for s in SEEDS],critical) for k in CONTRASTS}
 groups=[]
 for g in GRIDS:
  for p in ARMS:
   subset=[bank[s,l,g,p] for s in SEEDS for l in LABELS];r=dict(grid=g,presence=p,n_schools=16,n_worlds=32)
   for sp,n in (('D',12 if 'D'in p else 0),('G',gannets if 'G'in p else 0)):
    for metric in ('captures','contacts','launches'):
     total=sum(x[sp+'_'+metric] for x in subset);r[sp+'_group_total_'+metric]=total;r[sp+'_mean_group_'+metric+'_per_world']=total/32;r[sp+'_mean_'+metric+'_per_individual_36T']=float(Fraction(total,32*n)) if n else None;r[sp+'_mean_'+metric+'_per_individual_per_T']=float(Fraction(total,32*n*36)) if n else None
   groups.append(r)
 return dict(status='complete_h2_secondary_scalar_reconstruction' if herding==2 else 'original_h1_primary_scalar_reconstruction',case_count=192,independent_school_clusters=16,nested_labels=2,gannets=gannets,herding_T=herding,t_critical=critical,confidence=.95 if herding==2 else .975,estimates=summaries,case_points=cases,world_points=world,school_points=school,paired_grid_world_points=gridworld,group_returns=groups,joint_positive_fine_schools=sum(fractions[s]['fine_D']>0 and fractions[s]['fine_G']>0 for s in SEEDS),automated_success_decision=None if herding==2 else all(summaries['fine_'+sp]['student_t_ci'][0]>0 for sp in 'DG'),mcse_added_to_total_se=False,new_bootstrap_draws=0,unit='captures per individual per nominal36T; per-T rates separately labelled')
def interval(v):
 need(type(v)is list and len(v)==2 and all(type(y)in(int,float) for y in v),'Exactly two finite numeric cached endpoints required');x=[number(y) for y in v];need(x[0]<=x[1],'Cached endpoints must be ordered');return x
def close(a,b):
 need(type(a)in(int,float) and type(b)in(int,float),'Cached numeric fields must be numeric, not strings or booleans')
 need(abs(number(a)-number(b))<=1e-13,'Cached/recomputed numeric mismatch')
def cached_summary(cached,k):
 sp=k[-1]
 if k.startswith('fine_minus_coarse'):return cached['secondary']['fine_minus_coarse'][sp]
 if k.startswith('coarse'):return cached['secondary']['coarse'][sp]
 return cached['secondary_estimation']['species'][sp]
def validate_cached(cached,computed,independent):
 need(cached.get('status')=='complete_prespecified_secondary_estimation' and cached.get('case_count')==192,'Wrong cached H2 scope')
 d=cached['design'];need(d['schools']==list(SEEDS) and d['replicate_labels']==list(LABELS) and d['grids']==GRIDS and d['presence_arms']==list(ARMS),'Wrong cached matched design')
 for k,w in (('dolphins',12),('gannets',12),('fish',160),('duration_T',36)):need(type(d[k])in(int,float) and d[k]==w,'Wrong cached numeric design')
 need(cached['secondary_estimation']['automated_joint_decision']is None and cached['secondary_estimation']['parent_primary_unchanged']is True and 'primary'not in cached,'Secondary cannot become a replacement primary')
 need(cached['t_critical']==SECONDARY_CRITICAL and cached['uncertainty']['mcse_added_to_total_se']is False,'Wrong t or SE contract')
 b=cached['bootstrap'];need(b['role']=='sensitivity only; never select an inference method by whether it passes' and b['draws']==50000 and b['seed']==8611030 and b['generator']=='PCG64' and b['quantiles']==[.025,.975] and b['quantile_method']=='linear' and b['common_draws_across_all_contrasts']is True and b['unit']=='whole matched school vector' and b['index_matrix_sha256']==INDEX_SHA,'Wrong fixed cached bootstrap method')
 need(independent['independent_schools']==16 and independent['capture_repeats_per_school']==2 and independent['encounter_rows']==192 and independent['secondary_success_decision']is None and independent['original_primary_unchanged']is True,'Wrong independent oracle scope')
 ib=independent['bootstrap'];need(ib['draws']==50000 and ib['seed']==8611030 and ib['quantiles']==[.025,.975],'Wrong independent bootstrap scope')
 for k in CONTRASTS:
  x=cached_summary(cached,k);c=computed['estimates'][k];oname=(k[-1]+'_fine_minus_coarse') if 'minus'in k else k[-1]+'_'+k.split('_')[0];o=independent['endpoints'][oname]
  need(type(x['n_schools'])is int and x['n_schools']==16 and type(x['n_worlds'])is int and x['n_worlds']==32 and type(x['df'])is int and x['df']==15,'Wrong cached cluster scope')
  for key in ('mean','school_sd','se','within_school_variance_W','conditional_mcse','mean_rate_change_per_individual_per_T'):close(x[key],c[key])
  for key in ('school_signs','world_signs'):need(x[key]==c[key],'Wrong cached signs')
  need(len(x['label_effect_differences'])==16,'Wrong label-point scope')
  for a,b in zip(x['label_effect_differences'],c['label_effect_differences']):close(a,b)
  for a,b in zip(interval(x['student_t_95_ci']),c['student_t_ci']):close(a,b)
  ci=interval(x['bootstrap_95_ci']);close(ci[0],o['bootstrap_95_low']);close(ci[1],o['bootstrap_95_high'])
  for a,b in ((o['mean'],c['mean']),(o['sample_sd_school_means'],c['school_sd']),(o['sampling_se'],c['se']),(o['school_t_95_low'],c['student_t_ci'][0]),(o['school_t_95_high'],c['student_t_ci'][1]),(o['mean_within_school_repeat_variance'],c['within_school_variance_W']),(o['conditional_mcse'],c['conditional_mcse'])):close(a,b)
  c['cached_bootstrap_95_ci']=ci
 # Reconcile every cached school/world vector, not just means.
 for role,keys in (('school_points',('school_seed',)),('world_points',('school_seed','replicate_label','grid')),('paired_grid_world_points',('school_seed','replicate_label'))):
  a={tuple(r[k] for k in keys):r for r in cached[role]};z={tuple(r[k] for k in keys):r for r in computed[role]}
  need(len(cached[role])==len(a)==len(z) and a.keys()==z.keys(),'Wrong cached vector inventory')
  for key,r in z.items():
   need(set(a[key])==set(r),'Wrong cached point fields')
   for field,value in r.items():
    if isinstance(value,(int,float)):close(a[key][field],value)
    else:need(a[key][field]==value,'Wrong cached point identity')
 # Six cached group capture returns; contacts/launches are retained from acceptedCSV separately.
 savedgroups={(r['grid'],r['presence']):r for r in cached['group_returns']}
 need(len(cached['group_returns'])==len(savedgroups)==6,'Wrong cached group inventory')
 for r in computed['group_returns']:
  x=savedgroups.get((r['grid'],r['presence']));need(x is not None,'Missing cached group/control')
  required={'grid','presence','n_schools','n_worlds'}|{sp+suffix for sp in 'DG' for suffix in ('_group_total_captures','_mean_group_captures_per_world','_mean_captures_per_individual_36T','_mean_captures_per_individual_per_T')}
  need(set(x)==required,'Wrong cached group fields')
  for key,v in x.items():
   if r[key] is None:need(v is None,'Absent-species group rate differs')
   elif isinstance(r[key],(int,float)):close(v,r[key])
   else:need(v==r[key],'Group identity differs')
 # Nineteen f992 casepoint fields, including actual clock and nominal rates.
 raw={r['case_id']:r for r in computed['case_points']};points={r['case_id']:r for r in cached['case_points']}
 fields={'case_id','school_seed','replicate_label','grid','dt','presence','dolphins','gannets','D_captures','G_captures','duration_T','actual_duration_T','native_steps','native_absorbing_termination','remaining_fish','D_captures_per_individual_36T','D_captures_per_individual_per_T','G_captures_per_individual_36T','G_captures_per_individual_per_T'}
 need(len(cached['case_points'])==len(points)==192 and points.keys()==raw.keys(),'Wrong cached case inventory')
 for key,r in raw.items():
  x=points[key];need(set(x)==fields,'Wrong cached casepoint fieldset')
  for field in fields:
   if '_per_individual_'in field:
    sp=field[0];n=r['dolphins' if sp=='D' else 'gannets'];want=r[sp+'_captures']/n/(36 if field.endswith('_per_T')else 1) if n else None
    if want is None:need(x[field]is None,'Absent species has no per-animal rate')
    else:close(x[field],want)
   elif field=='actual_duration_T':need(abs(number(x[field])-r[field])<=1e-7,'Wrong cached observed clock')
   elif type(r[field])is bool:need(type(x[field])is bool and x[field]is r[field],'Wrong cached absorption flag')
   elif isinstance(r[field],int):need(type(x[field])is int and x[field]==r[field],'Wrong cached integer metadata')
   elif isinstance(r[field],float):close(x[field],r[field])
   else:need(x[field]==r[field],'Wrong cached case identity')
 computed['cached_bootstrap_verification']='Six hashed owner intervals match independently accepted oracle; no draws generated'
 return computed

def programme(primary_rows,lower_rows):
 p=calculate(primary_rows,gannets=36,herding=1);h=calculate(lower_rows)
 need(not({r['case_id'] for r in p['case_points']}&{r['case_id'] for r in h['case_points']}),'Distinct setting-specific controls required')
 endpoints={};points=[]
 for study,result in (('H1_G36',p),('H2_G12',h)):
  for sp in 'DG':
   x=result['estimates']['fine_'+sp];mean=x['mean'];se=x['se'];name='fine_'+study+'_'+sp
   endpoints[name]=dict(mean=mean,school_sd=x['school_sd'],se=se,n_schools=16,df=15,student_t_98_75_ci=[mean-PROGRAMME_CRITICAL*se,mean+PROGRAMME_CRITICAL*se],school_signs=x['school_signs'])
 for i,s in enumerate(SEEDS):points.append(dict(school_seed=s,**{'fine_'+study+'_'+sp:result['school_points'][i]['fine_'+sp] for study,result in (('H1_G36',p),('H2_G12',h)) for sp in 'DG'}))
 return dict(status='complete_additional_programme_family',confidence=.9875,t_critical=PROGRAMME_CRITICAL,case_count=384,independent_school_clusters=16,nested_labels=2,endpoints=endpoints,school_points=points,programme_criterion_met=all(x['student_t_98_75_ci'][0]>0 for x in endpoints.values()),original_h1_primary=p['automated_success_decision'],original_h1_primary_97_5_estimates={sp:p['estimates']['fine_'+sp] for sp in 'DG'},h2_automated_success_decision=None,bootstrap=None,new_bootstrap_draws=0,qualification='Both H and bird count change; no factor isolation, pooledn32 or outcome-selected family.')
