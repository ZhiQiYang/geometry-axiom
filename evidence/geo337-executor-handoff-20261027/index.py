from pathlib import Path
import datetime,fcntl,hashlib,json,subprocess
OUT=Path(__file__).parent;F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';BASE='https://github.com/ZhiQiYang/geometry-axiom/tree/'
def read(p):return json.loads(Path(p).read_text())
scopes=[
 ('native','732ef20e34876379a37eb69693a481becebea43e','evidence/geo337-native-validation-20261027/F-final/','/workspace/scratch/geo337-native-F-cbf0fb62-20261027-r2','230 suites; 5328 pass, 0 fail, one original GDI skip; exit 0 within 2100 seconds'),
 ('oracle/reader','7886f2eaa3da7f9f4855104ca4b028d2d06ce6da','evidence/geo337-reading-a-oracle-20261027/','/workspace/scratch/geo337-reading-a-oracle-F-cbf0fb62-20261027','oracle unit 14/14 and default CI reused from F native; original golden 0/1/0, generation/compare, mutants-only and full quick exit 0; reader generation/check 0 and unit 51/51 reused'),
 ('RC','7886f2eaa3da7f9f4855104ca4b028d2d06ce6da','evidence/geo337-reading-a-oracle-20261027/rc/','/workspace/scratch/geo337-reading-a-rc-F-cbf0fb62-20261027','builder/checker original proofs each 0/1/0, original assertion failures, no errors/skips'),
 ('required-eight','7886f2eaa3da7f9f4855104ca4b028d2d06ce6da','evidence/geo337-reading-a-oracle-20261027/oracle/required-eight-native-originals/','/workspace/scratch/geo337-reading-a-oracle-F-cbf0fb62-20261027/required-eight-native-originals','same-F native reuse; exact eight rows, 681 counted passes, zero fail/skip; no separate selected-wrapper run claimed'),
 ('PF3','1d9b980defec2659d7b08ee0a3ac782e00354780','evidence/geo337-pf3-20261027/','/workspace/scratch/geo337-pf3-F-cbf0fb62-20261027','original exit 0; baseline 20/20, 19 semantic kills, restored 20/20; all 21 source/binary variants retained'),
 ('Q38','dd2cbf6a558b4af240ab4702cc8402621380881b','evidence/geo337-q38-20261027/','/workspace/scratch/geo337-q38-F-cbf0fb62-20261027','original exit 0; 43 killed + SPM24 equivalent; baselines native 29/model 20; original ModelError outcomes retained'),
 ('P52','a08a036db335e88608ead761539d3e60b75e8e5d','evidence/geo337-p52-20261027/','/tmp/g337p52F27','formal/verifier/outer 0; fixed main adbaebf9c73ea6801d7b4d5214e4b846b132923b; 16+16 samples, ratio 0.849147775; controls 0/0/1/1/1'),
 ('#314','cbf8df4facf87b40db0fe46581c0b20131afada2','evidence/geo337-followup-scope-20261027/geo314/','/workspace/scratch/geo337-next-scope-review-20261027/geo314','same-F six native suites 103/103 and inspector 12/12; M121 original execution 82c922a3941525d3a094ac0158bdc7dea57ea360, 0/1/0 streams verified; no rerun or SHA relabelling'),
]
# Discover exact published native directory rather than inventing a mapping.
manifest=json.loads(subprocess.check_output(['git','-C','/workspace/geometry-axiom','show',scopes[0][1]+':evidence/geo337-native-validation-20261027/MANIFEST.json']))
native_result=[p for p in manifest['files'] if p.endswith('/F-complete/RESULT.json')]
assert len(native_result)==1,native_result
native_actual=json.loads(subprocess.check_output(['git','-C','/workspace/geometry-axiom','show',scopes[0][1]+':'+native_result[0]]))
assert native_actual['actual_process_returncode']==0 and native_actual['workflow_gate_exit']==0 and native_actual['sha']==F
scope_rows=[]
for name,commit,prefix,raw,status in scopes:
 if name=='native':prefix=native_result[0].removesuffix('RESULT.json')
 assert Path(raw).exists()
 verified=read('/workspace/scratch/geo337-remote-verification-'+commit+'.json');assert verified['all_files_match']
 scope_rows.append({'scope':name,'actual_source_F':F,'status':status,'evidence_commit':commit,'remote_prefix':prefix,'local_raw':raw,'remote_byte_verification_receipt':'/workspace/scratch/geo337-remote-verification-'+commit+'.json'})
cli=read(OUT/'cli-order/RESULT.json');assert cli['sha']==F and cli['diagnostic_complete'] and not cli['construction_route_observed']
cli['original_stage_criterion_evaluation']={'expression':'diagnostic_completed and construction_route_observed','value':False,'derived_only':True,'standalone_historical_stage_wrapper_executed':False}
cli['cli_build_coverage']='Reused unchanged fresh fixed-F P52 npm build / start_local --build-only. No new standalone --binary-dir invocation or compile claimed.'
(OUT/'cli-order/CLASSIFICATION.json').write_text(json.dumps(cli,indent=2)+'\n')
remaining=[
 {'scope':'six browser jobs / card / axiom / extra168 / whole-memo','owner':'existing browser/recovery task 01a162a6-2bb5-7393-902c-19dd519d60b9 under coordinator','state':'Assigned elsewhere; coordinator reports browser completion/collection and has assigned original-R8-holder whole-memo. This executor does not rerun or relabel them.'},
 {'scope':'Reading A CLI construction / #335','owner':'coordinator and original specification decision owner','state':'New original diagnostic completes, but both tested placement orders reject one timber. No construction route observed; original stage criterion evaluates false. No new unplaced-contact or batch-exemption semantics authorized or implemented.'},
 {'scope':'P189 comparison policy and remote required CI','owner':'coordinator','state':'No new whitelist adopted. Keep original comparator and original red results; local acceptance is not remote CI. Do not resample valid R8 or fabricate a CI runner result.'},
]
remaining_processes=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  comm=(p/'comm').read_text().strip()
  if any(s in comm for s in ['chrom','node','cc1']):remaining_processes.append({'pid':int(p.name),'comm':comm})
 except OSError:pass
assert not remaining_processes
with open('/tmp/geo337-native-owner.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
identity={}
for path in ['/workspace/geometry-axiom','/workspace/geo337-native-F-cbf0fb62','/workspace/geo337-p52-sources-20261027/fix','/workspace/geo337-p52-sources-20261027/main']:
 head=subprocess.check_output(['git','-C',path,'rev-parse','HEAD'],text=True).strip();status=subprocess.check_output(['git','-C',path,'status','--porcelain'],text=True);assert not status;identity[path]={'head':head,'status':status}
result={'scope':'executor handoff, not replacement release matrix','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixed_F':F,'completed':scope_rows,'new_diagnostic':cli,'remaining_owner_assignment':remaining,'no_independent_unowned_executable_acceptance_gap_found':True,'execution_released':True,'owner_lock_available':True,'remaining_heavy_processes':remaining_processes,'checkout_identity':identity,'original_raw_preserved':True,'new_redundant_archive_created':False}
(OUT/'HANDOFF.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
lines=['# Native/special executor final handoff','',f'Fixed F: `{F}`. This is an executor scope index, not a replacement for the coordinator’s release matrix. Existing raw packages are referenced, not repacked.','', '| Scope | Verified actual result | Existing raw |','|---|---|---|']
for r in scope_rows:
 lines.append('| '+r['scope']+' | '+r['status']+' | ['+r['evidence_commit'][:8]+']('+BASE+r['evidence_commit']+'/'+r['remote_prefix']+') |')
lines+=['','## Only new execution in this closeout','','The original Reading A CLI-order probe was not in native and had not been collected at F. It now completed with real exit 0 and complete protocols using the unchanged fresh F bridge from accepted P52. No compile was repeated. Both orders `(1,2)` and `(2,1)` have `both_place_accepted=false`: timber 1 is rejected respectively for a free span endpoint and for no legal span on its centerline. **This is diagnostic completion, not construction acceptance.** The original historical stage criterion `diagnostic_completed and construction_route_observed` evaluates false; that evaluation is derived, not a fabricated execution exit of the historical wrapper. Original probe, 30-second child deadlines, raw stdin/stdout/stderr in the receipt, and source/binary hashes are retained. No #335 rule or axiom changed.','','## Ownership and release','','- Browser/card/axiom/extra168 and whole-memo remain with the existing browser/recovery owner. The coordinator has sent whole-memo to the environment holding the original R8 ELF payloads; do not duplicate or rebuild them here.','- Reading A initial construction/#335 remains a specification/route question with actual negative observations now preserved. No unplaced-contact or batch exception is introduced.','- P189 comparison-policy approval and remote CI remain coordinator items. Original comparison rules and red receipts are unchanged; valid R8 samples are not redrawn.','- Architecture original F checks were already present in recovery handoff; native/oracle/reader/required-eight/PF3/Q38/P52/#314 are not rerun. No other unowned, independently executable original acceptance gap was found in the original command plan.','','All inspected checkouts are clean, original raw remains retained, no Chrome/Node/compiler remains, and the owner lock is available. This executor releases execution after publication of this small index plus the new CLI diagnostic; it does not wait or start duplicate same-SHA work.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'completed_scope_rows':len(scope_rows),'cli_diagnostic_complete':True,'construction_route_observed':False,'lock_available':True,'execution_released':True}))
