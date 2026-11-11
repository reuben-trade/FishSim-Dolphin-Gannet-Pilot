"""Public scalar-only H2 snapshot reader. No operator witnesses, models or RNG."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re
from pathlib import Path
import statistics_reader as stats
HERE=Path(__file__).resolve().parent
DATA=('h2_case_csv','h2_statistics','primary_case_csv','numeric_reference')
HASH_ROLES=('h2_independent_final','h2_owner_analysis','supervisor_witness','terminal_witness','completed_acceptance','h1_independent_final','h1_owner_analysis','h1_metadata')
PROFILE={'schools':list(stats.SEEDS),'labels':list(stats.LABELS),'grids':stats.GRIDS,'cases_per_setting':192,'school_clusters':16,'nested_labels':2,'D':12,'H1_G':36,'H1_H':1,'H2_G':12,'H2_H':2,'fish':160,'duration_T':36,'eligible_contact_q':.7,'prepared_checkpoint_T':20,'preparation_dt':.00125,'grid_scope':'Same coarse-prepared states; encounter-grid sensitivity, not preparation convergence','H2_pointwise_confidence':.95,'H2_t_critical':stats.SECONDARY_CRITICAL,'original_primary_confidence':.975,'original_primary_t_critical':stats.PRIMARY_CRITICAL,'programme_confidence':.9875,'programme_t_critical':stats.PROGRAMME_CRITICAL,'df':15,'bootstrap_draws_cached':50000,'bootstrap_seed':8611030,'bootstrap_generator':'PCG64','bootstrap_quantiles':[.025,.975],'bootstrap_index_sha256':stats.INDEX_SHA,'bootstrap_role':'cached sensitivity only; no new draws or inference switching','base_module_sha256':'6c1018930dcd736c83d41ed0d21690e10ba33c3c221deb35c0768350403e8fd8','operational_adapter_sha256':'32bc044c059b3a835bdf96c708e0d48d7cb1bb58813c89b730630d325b377368','composite_source_sha256':'e6a23fa0422fa3d5dea46143edd9bdc0540c64e7517f4c6705b0c1b62ef53942','unmodified_frozen_6c_cli_passed':False}
class Closed(RuntimeError):pass
def need(ok,m):
 if not ok:raise Closed(m)
class GateCompat:
 need=staticmethod(need)
gate=GateCompat() # Existing eight table-export function remains byte-identical.
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def csvrows(p):
 with Path(p).open(newline='') as f:return list(csv.DictReader(f))
def public_value(value):
 """Reject private-path/body additions even in a re-sealed scalar package."""
 forbidden={'actual_terminal','feeding_supervisor','root_final_acceptance','same_tool_session_id','tool_session_id','python_executable','argv','command','activation','operator_evidence','native_approval'}
 if isinstance(value,dict):
  need(not(set(value)&forbidden),'Operator witness/body field is not public scalar data')
  for k,v in value.items():public_value(k);public_value(v)
 elif isinstance(value,list):
  for v in value:public_value(v)
 elif isinstance(value,str):need(not value.startswith(('/','file://')) and '\\'not in value and '--authority'not in value,'Private absolute path/authority text is forbidden')
 elif isinstance(value,float):need(math.isfinite(value),'Nonfinite public scalar')
 else:need(value is None or type(value)in(int,bool),'Unsupported public scalar type')
def file_for(root,b):
 need(type(b)is dict and set(b)=={'path','sha256'} and stats.digest(b['sha256']),'Exact public file binding required')
 p=Path(b['path']);need(not p.is_absolute()and '..'not in p.parts,'Public paths must be relative')
 p=(root/p).resolve();need(p.is_relative_to(root.resolve())and p.is_file()and sha(p)==b['sha256'],'Missing/changed public scalar file');return p

def validate_certificate(cert,kind,data):
 need(set(cert)=={'schema','data_kind','scope','method_profile','evidence_sha256','source_sha256','accepted_input_sha256','public_data_sha256','private_completed_acceptance_attested','original_primary_criterion','raw_audit_reproduced','native_replay_certificate'},'Exact hash-only certificate fields required')
 public_value(cert)
 need(cert['schema']=='fishsim_h2_public_scalar_attestation_v1'and cert['data_kind']==kind and json.dumps(cert['method_profile'],sort_keys=True,allow_nan=False)==json.dumps(PROFILE,sort_keys=True,allow_nan=False),'Wrong public design/method profile')
 need(set(cert['evidence_sha256'])==set(HASH_ROLES)and all(stats.digest(v)for v in cert['evidence_sha256'].values()),'Eight private-evidence hashes required; bodies are not public')
 need(set(cert['public_data_sha256'])==set(DATA)and cert['public_data_sha256']=={k:v['sha256']for k,v in data.items()},'Public projection hash mismatch')
 need(set(cert['accepted_input_sha256'])=={'h2_case_csv','h2_statistics','primary_case_csv'}and all(stats.digest(v)for v in cert['accepted_input_sha256'].values()),'Accepted scalar origin hashes required')
 need(set(cert['source_sha256'])=={'private_completed_gate','private_exporter','public_reader','statistics_reader'}and all(stats.digest(v)for v in cert['source_sha256'].values()),'Source hash attestation required')
 need(cert['source_sha256']['public_reader']==sha(__file__)and cert['source_sha256']['statistics_reader']==sha(HERE/'statistics_reader.py'),'Public reader source identity differs')
 need(type(cert['original_primary_criterion'])is bool and cert['raw_audit_reproduced']is False and cert['native_replay_certificate']is False,'Honest scalar-only scope required')
 need(cert['private_completed_acceptance_attested']is(kind=='PRODUCTION_ACCEPTED_H2_192'),'Synthetic cannot claim private production acceptance')

def analyse_snapshot(path,*,expected_receipt_sha256=None,allow_synthetic=False):
 path=Path(path);root=path.parent;m=read(path);synthetic=m.get('data_kind')=='SYNTHETIC_TEST_DATA_ONLY'
 need(set(m)=={'schema','data_kind','data','source_files','certificate','scope'},'Public manifest cannot contain operator evidence roles')
 public_value(m);need(m['schema']=='fishsim_h2_public_scalar_snapshot_v1','Wrong public snapshot schema')
 need(synthetic and allow_synthetic or not synthetic and m['data_kind']=='PRODUCTION_ACCEPTED_H2_192','Explicit synthetic mode or accepted production snapshot required')
 receipt=root/'EXPORT_RECEIPT.json';need(receipt.is_file(),'Public export receipt absent')
 if not synthetic:need(expected_receipt_sha256 is not None and sha(receipt)==expected_receipt_sha256,'Caller must bind actual public export receipt')
 rec=read(receipt);public_value(rec);need(set(rec)=={'data_kind','manifest_sha256'}and rec['manifest_sha256']==sha(path)and rec['data_kind']==m['data_kind'],'Manifest/export lineage differs')
 need(set(m['source_files'])=={'portable_reader.py','statistics_reader.py'}and set(m['data'])==set(DATA),'Only two public source modules/four scalar inputs allowed')
 for name,digest in m['source_files'].items():need(sha(HERE/name)==digest,'Public source module changed')
 cert=read(file_for(root,m['certificate']));validate_certificate(cert,m['data_kind'],m['data'])
 files={k:file_for(root,v)for k,v in m['data'].items()};lower=csvrows(files['h2_case_csv']);primary=csvrows(files['primary_case_csv']);cached=read(files['h2_statistics']);numeric=read(files['numeric_reference'])
 for value in (lower,primary,cached,numeric):public_value(value)
 result=stats.calculate(lower);stats.validate_cached(cached,result,numeric)
 result['cached_bootstrap_verification']='Cached50k endpoints equal the hash-attested independent numeric reference; no new draws or private raw-audit reproduction'
 programme=stats.programme(primary,lower);need(programme['original_h1_primary']==cert['original_primary_criterion'],'Original primary criterion differs from accepted scalar attestation')
 result.update(programme=programme,data_kind=m['data_kind'],production_accepted=not synthetic,synthetic=synthetic,native_steps=0,native_model_imports=0,new_bootstrap_draws=0,portable_manifest_sha256=sha(path),private_completed_acceptance_attested=not synthetic,raw_audit_reproduced=False,native_replay_certificate=False,scope='Recomputed accepted model scalars plus cached numeric checks; private operator acceptance is hash-attested, not reproduced')
 return result
def export_tables(result,directory):
 out=Path(directory);gate.need(not out.exists(),'Preserve earlier table exports');out.mkdir(parents=True)
 synthetic=result['synthetic'];prefix='SYNTHETIC_' if synthetic else ''
 estimates=[]
 for name,x in result['estimates'].items():estimates.append(dict(contrast=name,**{k:v for k,v in x.items() if not isinstance(v,(dict,list))},t_low=x['student_t_ci'][0],t_high=x['student_t_ci'][1],cached_bootstrap_low=x['cached_bootstrap_95_ci'][0],cached_bootstrap_high=x['cached_bootstrap_95_ci'][1],**{k+'_schools':v for k,v in x['school_signs'].items()}))
 prog=[dict(endpoint=k,**{f:v for f,v in x.items() if not isinstance(v,(dict,list))},t_low=x['student_t_98_75_ci'][0],t_high=x['student_t_98_75_ci'][1]) for k,x in result['programme']['endpoints'].items()]
 tables={'h2_case_counts.csv':result['case_points'],'h2_world_effects.csv':result['world_points'],'h2_school_effects.csv':result['school_points'],'h2_paired_grid_world_effects.csv':result['paired_grid_world_points'],'h2_estimates.csv':estimates,'h2_group_returns.csv':result['group_returns'],'programme_four_endpoints.csv':prog,'programme_school_vectors.csv':result['programme']['school_points']}
 for name,rows in tables.items():
  if synthetic:rows=[dict(data_kind='SYNTHETIC_TEST_DATA_ONLY',**r) for r in rows]
  with (out/(prefix+name)).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary={'data_kind':result['data_kind'],'production_accepted':result['production_accepted'],'native_steps':0,'new_bootstrap_draws':0,'tables':{p.name:sha(p) for p in out.glob('*.csv')},'h2_automated_success_decision':None,'programme_criterion_met':result['programme']['programme_criterion_met'],'old_h1_primary_unchanged':True}
 write(out/(prefix+'TABLE_EXPORT_RECEIPT.json'),summary);return summary
def compact_report(result):
 """Return compact proposed table text after verified input; never writes paper."""
 rows=[]
 for sp in 'DG':
  x=result['estimates']['fine_'+sp];rows.append({'setting':'H2/G12','species':sp,'n_schools':16,'mean':x['mean'],'school_sd':x['school_sd'],'se':x['se'],'t95_low':x['student_t_ci'][0],'t95_high':x['student_t_ci'][1],'W':x['within_school_variance_W'],'conditional_mcse':x['conditional_mcse']})
 return {'data_kind':result['data_kind'],'secondary_table':rows,'programme_four_endpoint_table':result['programme']['endpoints'],'programme_criterion_met':result['programme']['programme_criterion_met'],'text_scope':'Same16 schools; two labels averaged within school. H2 intervals are95% pointwise; fourprogramme intervals98.75%. H and G both change. Original H1 primary97.5% remains unchanged.','bootstrap_scope':'Cached50k sensitivity; no method switching or new draws.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--expected-receipt-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyse_snapshot(a.snapshot,expected_receipt_sha256=a.expected_receipt_sha256);print(json.dumps(export_tables(r,a.output),indent=2))
