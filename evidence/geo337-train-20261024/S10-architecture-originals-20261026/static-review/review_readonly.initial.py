"""Read sealed tools and existing tiny receipts only; no imports or execution."""
from pathlib import Path
import ast,datetime,hashlib,json
P=Path('/tmp/geo337-S10-architecture-assembly-preparation-20261025')
O=Path(__file__).parent
checks=[]
def check(ok,label):
 checks.append({'check':label,'ok':bool(ok)})
 if not ok:raise AssertionError(label)
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(p):return {n.name:n for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def same(a,b):return ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
check(H(P/'PREPARATION.v2.json')=='96b628bcd285002ed8676fdefb7e58eaa2257a630eb04a1081aedcf47e4467bc','fixed v2 preparation')
prep=json.loads((P/'PREPARATION.v2.json').read_text())
check(H(P/'assemble_architecture_v2.py')=='b51110ff9756326a2b47d2ae4a6aded2a7995d92e2a882ddf9ec4065fae87d17','fixed v2 executor')
for row in prep['members']:
 f=P/row['path'];check(f.is_file()and not f.is_symlink(),'regular sealed member '+row['path'])
 check(f.stat().st_size==row['bytes']and H(f)==row['sha256'],'sealed bytes '+row['path'])
v1=(P/'assemble_architecture.py').read_text();v2=(P/'assemble_architecture_v2.py').read_text()
old="   result['error']=repr(e);dump(O/'RESULT.json',result);raise"
new="   result['exit_code']=1;result['error']=repr(e);dump(O/'RESULT.json',result);raise"
check(v1.count(old)==1 and v1.replace(old,new,1)==v2,'only v2 delta resets late error exit1')
f1=funcs(P/'assemble_architecture.py');f2=funcs(P/'assemble_architecture_v2.py');fp=funcs(P/'assemble_architecture.proof-version.py')
for n in f1:
 if n!='main':check(same(f1[n],f2[n]),'all helper AST unchanged '+n)
for n in ('H','need','validate_gate','validate_inputs','historical_probes'):
 check(same(fp[n],f2[n]),'original four proofs apply to final helper '+n)
legacy=Path('/tmp/geo337-architecture-h-local-init-tool-20261024/refresh_architecture_h_local_init.py')
check(H(legacy)=='94574f72984c26d72a88eac3536c6c2b316b67a63529c50835a9d6d988a194dc','original H driver pin')
fl=funcs(legacy)
for n in ('H','LF','info'):check(same(fl[n],f2[n]),'original hash/schema helper '+n)
check(ast.dump(ast.Module(body=fl['snapshot'].body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=f2['snapshot'].body,type_ignores=[]),include_attributes=False),'original complete snapshot body')
index_tool=Path('/workspace/geo314-F9-counterproof-all-private-index-preparation-20261025/run_counterproof_v3.py')
check(H(index_tool)=='74651aa907fc3f280592ac7a1f63f8d9d912f1adaa31ffc2ffe8c428d6fee568','accepted full-index helper source pin')
check(same(funcs(index_tool)['require_full_index'],f2['require_full_index']),'full DIRC parser AST unchanged')
def streams(rows,label):
 for i,entry in enumerate(rows):
  row=entry.get('command',entry);d=Path(row['directory']);saved=json.loads((d/'result.json').read_text());req=json.loads((d/'request.json').read_text())
  check(saved==row,label+' saved result '+str(i))
  for name in ('stdin','stdout','stderr'):
   b=(d/(name+'.bin')).read_bytes();check(hashlib.sha256(b).hexdigest()==row[name+'_sha256'],label+' original '+name+' '+str(i))
   if name!='stdin':check(len(b)==row[name+'_bytes'],label+' size '+name+' '+str(i))
  check(not row['timeout_expired'],label+' no timeout '+str(i))
  check(row['environment']['PYTHONOPTIMIZE']is None,label+' unoptimized '+str(i))
  check(req['actual_process_returncode']is None,label+' original prelaunch request '+str(i))
  check('synthetic' in row['source_sha'],label+' synthetic source tag '+str(i))
proof=json.loads((P/'tiny-proof/RESULT.json').read_text())
check(proof['tool_sha256']==H(P/'assemble_architecture.proof-version.py'),'first proof source pin not relabelled')
check(proof['phase_exit_codes']==[0,1,0]*4,'four original metadata proofs actual 0/1/0')
streams(proof['rows'],'original-binding-proof')
for i,row in enumerate(proof['rows']):
 cmd=row['command'];check(cmd['actual_process_returncode']==row['expected_exit'],'actual binding exit '+str(i))
 if row['mode']=='withdrawn':check(b'AssertionError: assembly binding escaped:'in(Path(cmd['directory'])/'stderr.bin').read_bytes(),'named withdrawal assertion '+str(i))
late=json.loads((P/'late-failure-proof/RESULT.json').read_text())
check(late['phases']==[0,1,0]and late['no_actual_source_or_gate_execution'],'actual late-result proof scope')
streams(late['commands'],'late-result-proof')
for label,exitcode in zip(('fixed','withdrawn','restored'),(1,0,1)):
 inner=json.loads((P/'late-failure-proof'/label/'RESULT.json').read_text());check(inner['exit_code']==exitcode,'actual saved inner late-failure '+label)
check(b'late failure must never retain inner exit0'in(P/'late-failure-proof/original-commands/subcommands/000002/stderr.bin').read_bytes(),'named false-green counterexample')
request=json.loads((P/'REQUEST.v2.pending.json').read_text())
check(request['root_execution_lease']is False and request['source_snapshot_executed']is False and request['formal_judges_will_be_rerun']is False,'formal source lease remains false and UNRUN')
check('--root-execution-lease'not in request['argv'],'pending command cannot execute silently')
check(request['executor_sha256']==H(P/'assemble_architecture_v2.py'),'pending argv binds v2')
check("historicalExecutionSource':PRIOR"in v2 and "'executedAtCurrentHead':False"in v2,'nine probes remain historical')
check("before==prior"in v2 and "len(before)==len(prior)==len(inputs)==604"in v2,'full raw/LF/Git604 comparison remains strict')
check("scan_raw==old_four[NAMES[1]]"in v2 and "only report/receipt changed"in v2,'manifest scan identity and precise two output delta')
check("originalJudgesRerun':False"in v2 and "formalLedgerOrNativeExecuted':False"in v2,'no new product execution claim')
result={'schema':'S10-architecture-assembly-static-peer/1','exit_code':0,'checks':len(checks),'blocking_findings':[],
 'executor_sha256':H(P/'assemble_architecture_v2.py'),'preparation_sha256':H(P/'PREPARATION.v2.json'),
 'source_sha':'82c922a3941525d3a094ac0158bdc7dea57ea360','static_only':True,'source_or_shm_accessed':False,'product_or_proof_tests_rerun':False,
 'resolved_v1_finding':{'executor_sha256':H(P/'assemble_architecture.py'),'issue':'Late error could leave inner exit0; v2 now explicitly sets1 before preserving error and raising.','proof_actual_exits':[0,1,0]},
 'existing_original_proofs':{'four_binding_groups_exits':[0,1,0]*4,'late_failure_group_exits':[0,1,0],'only_metadata_not_formal':True},
 'reviewed_controls':['Source read after explicit root lease and both original NB locks.','Original full index parsed and copied to private OUT; operational Git env uses private index plus optional-locks0/splitIndexfalse; final real-index bytes/inode/mtime guard.','Closed three original gate argv/source/rc/request/result/fullstreams/counts205/18 retained; no new judge command.','New snapshot timing distinct from gate execution; strict604 prior/raw/LF/Git equality; source four outputs untouched.','Old9guards+2neutral remain actualM6e50, not rerun or labelledS10.','Manifest/scan byte hard pins; only report/receipt change; receipt does not hash its future commit.'],
 'limits':['Static preparation review only; formal root lease remains false, full123 source/cache was not read.','Root still must schedule capacity after full123 terminal and use formal require_escalated.','Actual new artifacts need their original runtime result and independent actual review, ordinary publication; this peer0 is no product pass.','Base H94574 helper provenance and full tiny originals must accompany publication as PUBLICATION_SCOPE states.'],
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
(O/'REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'exit_code':0,'checks':len(checks),'review_sha256':H(O/'REVIEW.json'),'executor_sha256':result['executor_sha256']},ensure_ascii=False))
