"""Read-only paired36T comparisons across two numerical integration grids."""
from pathlib import Path
import csv,hashlib,json
HERE=Path(__file__).resolve().parent
COARSE=HERE.parent/'longer_replication_2026-11-09/results/full_72T_v1'
FINE=HERE/'results/full_36T_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def horizon(folder,seed,presence):
 case=folder/'cases'/f's{seed}_exposed_{presence}_c61001'
 complete=read(case/'completion.json');assert complete['status']=='complete'
 for name,digest in complete['files'].items():assert sha(case/name)==digest
 seal=read(case/'checkpoint_36T.seal.json');assert seal['status']=='complete'
 for name,digest in seal['files'].items():assert sha(case/name)==digest
 for name,digest in seal['source_sha256'].items():assert sha(Path(name))==digest
 record=read(case/'checkpoint_36T.json');assert record['nominal_horizon_T']==36.
 assert record['physical_accounting_audit']['status']=='passed'
 return record,dict(case=str(case),completion_sha256=sha(case/'completion.json'),horizon_seal_sha256=sha(case/'checkpoint_36T.seal.json'))
def writecsv(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 cases=[];paired=[];evidence=[]
 for seed in range(39064501,39064509):
  grids={}
  for grid,dt,folder in (('coarse',.00125,COARSE),('fine',.000625,FINE)):
   grids[grid]={}
   for presence in ('D','G','DG'):
    h,receipt=horizon(folder,seed,presence);evidence.append(receipt);grids[grid][presence]=h
    for species in presence:
     s=h['species'][species];structure=h['school_structure']
     cases.append(dict(grid=grid,dt=dt,school_seed=seed,presence=presence,species=species,captures=s['captures'],launches=s['launches'],contacts=s['contacts'],captures_per_actor_per_nominal_T=s['captures_per_actor_per_nominal_T'],observed_effort_T=s['observed_effort_T'],observed_distance=s['observed_distance'],observed_native_duration_T=h['observed_native_duration_T'],native_steps=h['native_steps'],final_live_fish=h['final_count'],school_mean_depth=structure.get('mean_depth'),school_r90=structure.get('r90')))
  row=dict(school_seed=seed)
  for grid,g in grids.items():
   for species in ('D','G'):
    alone=g[species]['species'][species]['captures'];mixed=g['DG']['species'][species]['captures']
    row[f'{grid}_{species}_alone']=alone;row[f'{grid}_{species}_mixed']=mixed;row[f'{grid}_{species}_partner_effect']=mixed-alone
   row[f'{grid}_joint_positive']=row[f'{grid}_D_partner_effect']>0 and row[f'{grid}_G_partner_effect']>0
  for species in ('D','G'):
   row[f'{species}_effect_fine_minus_coarse']=row[f'fine_{species}_partner_effect']-row[f'coarse_{species}_partner_effect']
   row[f'{species}_mixed_fine_minus_coarse']=row[f'fine_{species}_mixed']-row[f'coarse_{species}_mixed']
   row[f'{species}_effect_same_sign']=(row[f'fine_{species}_partner_effect']>0)-(row[f'fine_{species}_partner_effect']<0)==(row[f'coarse_{species}_partner_effect']>0)-(row[f'coarse_{species}_partner_effect']<0)
  paired.append(row)
 out=FINE/'analysis_final';out.mkdir(exist_ok=False)
 writecsv(out/'case_grid_comparison.csv',cases);writecsv(out/'paired_effect_grid_differences.csv',paired)
 aggregate=dict(status='complete',schools=8,grids=2,independent_schools=8,native_steps_executed_by_analysis=0,evidence=evidence,interpretation='Two-grid sensitivity diagnostic,not convergence or16independent schools',joint_positive_schools={grid:sum(r[f'{grid}_joint_positive'] for r in paired) for grid in ('coarse','fine')})
 for species in ('D','G'):
  values=[r[f'{species}_effect_fine_minus_coarse'] for r in paired]
  aggregate[species]=dict(effect_grid_difference_mean=sum(values)/8,effect_grid_difference_range=[min(values),max(values)],effect_same_sign_schools=sum(r[f'{species}_effect_same_sign'] for r in paired))
 (out/'analysis_audit.json').write_text(json.dumps(aggregate,indent=2)+'\n')
 lines=['# Numerical sensitivity at36T','', 'The same eight schools, actor starts, behavior and private random streams were run on dt0.00125 and dt0.000625. These are paired numerical grids, not additional independent schools.','', '|School|D effect coarse|D effect fine|G effect coarse|G effect fine|','|---|---:|---:|---:|---:|']
 for r in paired:lines.append('|'+ '|'.join(str(r[k]) for k in ('school_seed','coarse_D_partner_effect','fine_D_partner_effect','coarse_G_partner_effect','fine_G_partner_effect'))+'|')
 lines+=['','Partner effect means mixed-species catches minus same-species-alone catches. The CSV tables retain catches,effort and fish structure on each grid. Agreement between two grids does not establish numerical convergence or timestep independence. No parameters or schools were changed to obtain agreement.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(aggregate))
if __name__=='__main__':main()
