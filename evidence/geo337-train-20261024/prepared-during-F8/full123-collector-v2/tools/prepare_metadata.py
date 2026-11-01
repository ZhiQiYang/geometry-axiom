"""One-time preparation and pure metadata checks; does not inspect active outputs."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys
HERE=Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
D=Path('/tmp/geo337-full123-F7-admission-draft-20261024')
cap=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert h(cap.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
tools=[('run_full_ledger.py',D/'run_full_ledger.py'),('launch_full_ledger.py',D/'launch_full_ledger.py'),('resource_admission.py',D/'resource_admission.py'),('retain_mutation_streams.py',D/'retain_mutation_streams.py'),('verify_observed_core_raw.py',D/'verify_observed_core_raw.py'),('capture.py',cap),('reap_children.py',Path('/workspace/geo261-environment/reap_children.py'))]
original_tools=[]
for name,p in tools:
 b=p.read_bytes();original_tools.append({'path':str(p),'archive_name':name,'bytes':len(b),'sha256':h(b)})
source_scope={'source_sha':F8,'formal_executed_by_preparation':False,'root':'/tmp/train337-323-f64d638f-source','job':'/tmp/geo337-full123-F8-job-20261025','outer':'/tmp/geo337-full123-F8-launch-20261025','cache':'/workspace/geo337-full123-F8-cache-20261025','tmp':'/tmp/geo337-full123-F8-tmp-20261025','scope_rule':'all regular JOB+outer files; cache M*/_baseline/_bridge-baseline recursive stdout/stderr/json only; original tools and collection control; do not add ELF/source/Git/cache payloads','live_scope_enumerated_or_hashed':False,'original_scope_script':'/workspace/prepare_geo337_ledger_4f4_terminal.py','original_scope_script_sha256':h(Path('/workspace/prepare_geo337_ledger_4f4_terminal.py').read_bytes()),'legacy_adoption_reference_only':'/workspace/adopt_geo337_b6_ledger.py','legacy_adoption_reference_sha256':h(Path('/workspace/adopt_geo337_b6_ledger.py').read_bytes())}
(HERE/'SCOPE.json').write_text(json.dumps(source_scope,ensure_ascii=False,indent=2)+'\n')
request={'schema':'F8-full123-original-terminal-binding/1','binding_status':'UNBOUND_DO_NOT_EXECUTE','source_sha':F8,'terminal_bindings':{'job_receipt':{'path':source_scope['job']+'/receipt.json','sha256':None},'outer_result':{'path':source_scope['outer']+'/RESULT.json','sha256':None},'original_tool_final':{'path':None,'sha256':None}},'root_rule':'Create a different request only after actual original exec terminal; preserve this unbound draft.'}
(HERE/'REQUEST.unbound.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
for p in HERE.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
spec=importlib.util.spec_from_file_location('original_c387_metadata_only',cap);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','GEOMETRY_','MUTATE_')) and k not in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONOPTIMIZE')};env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONIOENCODING']='utf-8'
r=m.Recorder(HERE/'metadata-original-capture',env,F8);rows=[]
for phase,expected in [('fixed',0),('withdrawn',1),('restored',0)]:
 row,out,err=r.run([sys.executable,'-B',str(HERE/'check_terminal_metadata.py'),'--phase',phase],cwd=HERE,timeout=30,check=False,source_sha=F8,source_variant='synthetic-metadata-only-no-live-read')
 assert row['actual_process_returncode']==expected
 rows.append({'phase':phase,'actual_exit':row['actual_process_returncode'],'expected_metadata_exit':expected,'original_command':row})
result={'schema':'terminal-classifier-synthetic-metadata-checks/1','subject_formal_executed':False,'live_payload_read_or_hashed':False,'actual_exits':[x['actual_exit'] for x in rows],'rows':rows,'exit':0,'scope':'Pure synthetic dictionaries; no root/job/cache/outer inspection, original CLI/import/compiler/browser or ledger generation.'}
(HERE/'METADATA_CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
files=[]
for p in sorted(HERE.rglob('*')):
 if p.is_file() and p.name!='PREPARATION.json' and '__pycache__' not in p.parts:
  b=p.read_bytes();files.append({'path':p.relative_to(HERE).as_posix(),'bytes':len(b),'sha256':h(b)})
prep={'schema':'F8-full123-terminal-tools-preparation/1','source_sha':F8,'prepared_only':True,'formal_executed':False,'collection_executed':False,'adoption_executed':False,'active_payload_enumerated_or_hashed':False,'files':files,'original_tools':original_tools}
(HERE/'PREPARATION.json').write_text(json.dumps(prep,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'preparation':str(HERE/'PREPARATION.json'),'sha256':h((HERE/'PREPARATION.json').read_bytes()),'files':len(files),'original_tools':len(original_tools),'metadata_actual_exits':result['actual_exits'],'formal_executed':False,'collection_executed':False},ensure_ascii=False))
