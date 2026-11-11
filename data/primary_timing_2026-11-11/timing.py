"""Exploratory fixed2T local-entry timing diagnostics; stdlib/Fraction, no RNG."""
from fractions import Fraction
import math
SEEDS=tuple(range(39065501,39065517));LABELS=(71001,71002);GRIDS=('coarse','fine')
D_IDS=tuple(f'D{i:02d}'for i in range(12));G_IDS=tuple(f'G{i}'for i in range(36))
WINDOW=Fraction(2);CLOCK_TOL=Fraction('0.0000001');EVENT_TOL=Fraction('0.000000001')
class Invalid(ValueError):pass
def need(v,m):
 if not v:raise Invalid(m)
def clock(v):
 need(type(v)in(int,float)and math.isfinite(v),'Finite recorded numeric clock required');return Fraction(str(v))
def integer(v):need(type(v)is int and v>=0,'Nonnegative integer required');return v
def rate(n,d):return Fraction(n,d)if d else None

def classify(events,bird_events,opportunities,*,start_time,end_time,final_dolphins):
 start,end=clock(start_time),clock(end_time);need(0<end-start<=36+CLOCK_TOL,'Observed complete/depleted physical horizon required')
 need(set(final_dolphins)==set(D_IDS),'All twelve final dolphin records required')
 launches={};cycles={};closed_oral={};physical_closed={};entries={};detections={}
 for e in events:
  who=e.get('actor_id','')
  if who not in D_IDS:continue
  if e.get('kind')=='transition'and e.get('reason')=='launch':
   key=(who,integer(e['bout_id']));need(key[1]>0 and key not in launches,'Unique positive dolphin launch bout required');t=clock(e['time']);need(start-CLOCK_TOL<=t<=end+CLOCK_TOL,'Launch outside saved horizon');launches[key]=dict(time=t,target=e['target_id'])
 for e in opportunities:
  if e.get('kind')!='cycle_launch':continue
  key=(e['actor_id'],integer(e['bout_id']));need(key not in cycles,'Duplicate cycle launch');cycles[key]=(clock(e['time']),e['target_id'])
 need(set(cycles)==set(launches)and all(cycles[k]==(v['time'],v['target'])for k,v in launches.items()),'Committed physical/opportunity launches differ')
 captured_ids=[]
 for e in events:
  who=e.get('actor_id','')
  if who not in D_IDS:continue
  if e.get('kind')not in('oral','transition'):continue
  key=(who,integer(e.get('bout_id',0)))
  if e.get('kind')=='oral':
   need(type(e.get('closes_bout'))is bool,'Explicit oral closure flag required')
   if not e['closes_bout']:continue
   need(key in launches and key not in closed_oral,'Oral closure must have one unique preceding launch');t=clock(e['contact']['time']);need(launches[key]['time']-EVENT_TOL<=t<=end+CLOCK_TOL,'Oral closure outside launch/horizon')
   need(e.get('status')in('captured','contact_failed'),'Unexpected eligible-contact status');closed_oral[key]=e['status']=='captured'
   if closed_oral[key]:captured_ids.append(e['prey_id'])
  elif e.get('kind')=='transition'and e.get('before')=='attack'and e.get('after')!='attack':
   need(key in launches,'Attack termination without launch');t=clock(e['time']);need(launches[key]['time']-EVENT_TOL<=t<=end+CLOCK_TOL,'Attack termination outside launch/horizon');physical_closed.setdefault(key,[]).append(t)
 need(len(captured_ids)==len(set(captured_ids)),'Duplicate captured prey')
 for e in bird_events:
  if e.get('kind')!='water_entry':continue
  identity=e['event_id'];need(identity not in entries,'Duplicate realized water entry');need(e.get('actor_id')in G_IDS and identity==f"{e['actor_id']}:bout{integer(e['bout_id'])}",'Known bird/entry identity required')
  need(e.get('realized')is True and e.get('scheduled')is False,'Realized unscheduled entry required');need(start-CLOCK_TOL<=clock(e['time'])<=end+CLOCK_TOL,'Entry outside saved horizon');entries[identity]=e
 for e in bird_events:
  if e.get('kind')!='dive_detection':continue
  identity=e['event_id'];who=e['detected_by'];key=(identity,who)
  need(identity in entries and who in D_IDS and key not in detections,'Unique local detection of realized entry required');original=entries[identity]
  need(e.get('controller_input')is False and e.get('realized')is True and e.get('scheduled')is False,'Detection is instrumentation, never a controller input')
  need(e['actor_id']==original['actor_id']and e['bout_id']==original['bout_id']and clock(e['time'])==clock(original['time']),'Detection/entry metadata differs')
  delivery=clock(e['delivery_time']);entry=clock(e['time']);need(delivery+CLOCK_TOL>=entry and delivery<=end+CLOCK_TOL,'Detection delivery clock invalid')
  distance=clock(e['detection_distance']);need(0<=distance<=25+Fraction('0.00000001'),'Detection is not local within original25-unit range');detections[key]=(entry,delivery)
 groups={name:dict(launches=0,eligible_contacts=0,captures=0,resolved_without_oral_contact=0,censored_unresolved=0)for name in('recent','not_recent')};trace=[]
 unresolved=[];by_dolphin={who:[]for who in D_IDS}
 for(_,who),value in detections.items():by_dolphin[who].append(value)
 for key,launch in launches.items():
  t=launch['time'];recent=any(delivered<=t and 0<=t-entry<=WINDOW for entry,delivered in by_dolphin[key[0]])
  name='recent'if recent else'not_recent';g=groups[name];g['launches']+=1
  if key in closed_oral:g['eligible_contacts']+=1;g['captures']+=closed_oral[key];outcome='capture'if closed_oral[key]else'contact_failed'
  elif key in physical_closed:g['resolved_without_oral_contact']+=1;outcome='resolved_without_oral_contact'
  else:
   final=final_dolphins[key[0]];need(final.get('mode')=='attack'and final.get('bout_id')==key[1],'Unresolved earlier bout or missing terminal evidence');unresolved.append(key);g['censored_unresolved']+=1;outcome='right_censored_at_physical_horizon'
  trace.append(dict(actor_id=key[0],bout_id=key[1],launch_time=float(t),recent_local_entry=recent,outcome=outcome))
 need(len({k[0]for k in unresolved})==len(unresolved),'At most one unresolved final bout per dolphin')
 for who,final in final_dolphins.items():
  if final.get('mode')=='attack':need((who,final.get('bout_id'))in unresolved,'Final attack without unresolved recorded launch')
 for g in groups.values():
  need(g['launches']==g['eligible_contacts']+g['resolved_without_oral_contact']+g['censored_unresolved'],'Bout accounting differs')
  g['eligible_contacts_per_all_launches']=rate(g['eligible_contacts'],g['launches']);g['captures_per_all_launches']=rate(g['captures'],g['launches']);g['rate_denominator']=g['launches'];g['undefined_reason']='no_launches_in_class'if not g['launches']else None
 total=sum(g['launches']for g in groups.values());recent_fraction=rate(groups['recent']['launches'],total)
 metrics={'recent_launch_fraction':recent_fraction,'contact_rate_recent':groups['recent']['eligible_contacts_per_all_launches'],'contact_rate_not_recent':groups['not_recent']['eligible_contacts_per_all_launches'],'capture_rate_recent':groups['recent']['captures_per_all_launches'],'capture_rate_not_recent':groups['not_recent']['captures_per_all_launches']}
 for metric in('contact','capture'):
  a,b=metrics[metric+'_rate_recent'],metrics[metric+'_rate_not_recent'];metrics[metric+'_rate_recent_minus_not']=a-b if a is not None and b is not None else None
 reasons={name:(None if value is not None else 'no_total_launches'if name=='recent_launch_fraction'else'one_or_both_launch_classes_empty'if name.endswith('_minus_not')else'no_launches_in_this_class')for name,value in metrics.items()}
 return dict(window_T=2,total_launches=total,groups=groups,metrics=metrics,metric_undefined_reasons=reasons,launch_trace=trace,detection_count=len(detections),interpretation='Observed all-launch rates include explicitly counted right-censored bouts; neither completed-bout success probabilities nor causal timing effects.')

def ranks(values):
 out={};ordered=sorted(set(values));position=1
 for value in ordered:
  n=values.count(value);out[value]=Fraction(2*position+n-1,2);position+=n
 return[out[v]for v in values]
def correlation(x,y,method):
 need(len(x)==len(y),'Paired association vectors required');need(method in('Pearson','Spearman'),'Only two fixed deterministic associations');n=len(x)
 if n<3:return dict(method=method,n=n,value=None,undefined_reason='fewer_than_three_complete_school_pairs')
 if method=='Spearman':x,y=ranks(x),ranks(y)
 need(method in('Pearson','Spearman'),'Only two fixed deterministic associations')
 mx,my=sum(x,Fraction())/n,sum(y,Fraction())/n;xx=sum((v-mx)**2 for v in x);yy=sum((v-my)**2 for v in y)
 if not xx or not yy:return dict(method=method,n=n,value=None,undefined_reason='constant_predictor_or_response')
 covariance=sum((a-mx)*(b-my)for a,b in zip(x,y));value=(-1 if covariance<0 else 1)*math.sqrt(float(covariance*covariance/(xx*yy)))
 return dict(method=method,n=n,value=value,undefined_reason=None)

def summarise(count_rows,world_diagnostics):
 expected={(s,l,g,a)for s in SEEDS for l in LABELS for g in GRIDS for a in('D','G','DG')};bank={}
 for r in count_rows:
  key=(r['school_seed'],r['replicate_label'],r['grid'],r['presence']);need(key in expected and key not in bank,'Exact unique primary192 count inventory required')
  for sp in'DG':
   values=[integer(r[sp+'_'+metric])for metric in('captures','contacts','launches')];need(values[0]<=values[1]<=values[2],'Capture/contact/launch accounting required');need(sp in r['presence']or values==[0,0,0],'Absent species cannot hunt')
  need(r['D_captures']+r['G_captures']<=160,'At most160 unique captures')
  bank[key]=r
 need(set(bank)==expected,'All192 matched controls required')
 need(set(world_diagnostics)=={(s,l,g)for s in SEEDS for l in LABELS for g in GRIDS},'All64 mixed timing worlds required')
 worlds=[];schools=[];summaries=[];associations=[]
 for s in SEEDS:
  for l in LABELS:
   for grid in GRIDS:
    d=world_diagnostics[s,l,grid];need(d.get('window_T')==2,'Only fixed2T classification is allowed');mixed=bank[s,l,grid,'DG'];need(d['total_launches']==mixed['D_launches']and sum(x['eligible_contacts']for x in d['groups'].values())==mixed['D_contacts']and sum(x['captures']for x in d['groups'].values())==mixed['D_captures'],'Timing classification/raw accepted counts differ')
    metrics=dict(d['metrics'],D_partner_gain=Fraction(mixed['D_captures']-bank[s,l,grid,'D']['D_captures'],12),G_partner_gain=Fraction(mixed['G_captures']-bank[s,l,grid,'G']['G_captures'],36))
    worlds.append(dict(school_seed=s,replicate_label=l,grid=grid,total_launches=d['total_launches'],metrics=metrics,groups=d['groups'],undefined_reasons=d['metric_undefined_reasons']))
 for s in SEEDS:
  for grid in GRIDS:
   pair=[next(w for w in worlds if(w['school_seed'],w['replicate_label'],w['grid'])==(s,l,grid))for l in LABELS];metrics={};reasons={}
   for name in pair[0]['metrics']:
    values=[w['metrics'][name]for w in pair];metrics[name]=sum(values,Fraction())/2 if all(v is not None for v in values)else None;reasons[name]=None if metrics[name]is not None else'one_or_both_label_denominators_undefined'
   schools.append(dict(school_seed=s,grid=grid,metrics=metrics,undefined_reasons=reasons,defined_labels={name:sum(w['metrics'][name]is not None for w in pair)for name in metrics},nested_labels=2))
 for grid in GRIDS:
  subset=[s for s in schools if s['grid']==grid]
  for name in subset[0]['metrics']:
   values=[s['metrics'][name]for s in subset if s['metrics'][name]is not None];n=len(values)
   summaries.append(dict(grid=grid,metric=name,n_defined_schools=n,n_undefined_schools=16-n,mean=sum(values,Fraction())/n if n else None,positive=sum(v>0 for v in values),zero=sum(v==0 for v in values),negative=sum(v<0 for v in values)))
  for response in('D_partner_gain','G_partner_gain'):
   pairs=[(s['metrics']['recent_launch_fraction'],s['metrics'][response])for s in subset if s['metrics']['recent_launch_fraction']is not None and s['metrics'][response]is not None]
   for method in('Pearson','Spearman'):associations.append(dict(grid=grid,predictor='recent_launch_fraction',response=response,n_excluded_schools=16-len(pairs),**correlation([x for x,y in pairs],[y for x,y in pairs],method)))
 return dict(status='complete_exploratory_fixed2T_timing_diagnostics',window_T=2,schools=16,labels_per_school=2,worlds=worlds,school_points=schools,summaries=summaries,associations=associations,confidence_intervals=None,pvalues=None,bootstrap_or_permutation_draws=0,causal_or_coordination_claim=False,original_primary_97_5_changed=False,selection='Exploratory after primary feeding effects were known; one fixed window, no lag or metric selection.')

def serialise(value):
 if isinstance(value,Fraction):return{'value':float(value),'exact':str(value)}
 if isinstance(value,dict):return{k:serialise(v)for k,v in value.items()}
 if isinstance(value,list):return[serialise(v)for v in value]
 return value
