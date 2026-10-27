"""Read-only adversarial verification of completed a6 four-artifact assembly."""
from pathlib import Path
import collections,datetime,hashlib,json,os,re,stat

OUT=Path(__file__).parent
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
BASE=OWN/'a6-architecture-four-original-20261026'
OUTER=OWN/'a6-assembly-root-original-20261026'
ROOT=OWN/'a6-architecture-source-20261026'
PREP=OWN/'a6-architecture-source-original-20261026'
GATES=OWN/'a6-architecture-gates-original-20261026'
SOURCE='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
PRIOR='6e50aef65513b7b38f93228919272c6d40d6c196'
ADOPTION='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
PIN='a532b83a67e19b37e2cf724fb4d9ec86753b3a090de554093646b2e2c3d1b2df'
ASSEMBLER_PIN='97da235f9a9d69b4cdfbc67dc3f49e5b447b574176e39e3300ffd887993fab62'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
ART='geometry-core/domain-decoupling/'
NAMES=['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json']
PRIOR_PINS=['81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975','18f24f186445928e79159bbd49dc10b586a42ab17ded1cf15f2608de4354a728','fa1357b249c19708824d480993a80821b7bfeccb7606be773a000395f28aafd6','00a33c42ca07a9077aa5abf758ed8b0a3650a031cdc8387128f285050b7c13af']
SUFFIXES={'.c','.cc','.cjs','.cpp','.cxx','.h','.hh','.hpp','.htm','.html','.inc','.js','.jsx','.mjs','.py','.ts','.tsx'}
JUDGES=['tests/architecture_contract.py','tests/test_architecture_contract.py','tests/test_product_architecture.py']
checks=0;findings=[];captures=0;streambytes=0
def H(b):return hashlib.sha256(b).hexdigest()
def LF(b):return b.replace(b'\r\n',b'\n')
def oid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def info(b):return {'bytes':len(b),'rawSha256':H(b),'lfSha256':H(LF(b))}
def load(p):return json.loads(p.read_bytes())
def need(ok,msg):
 global checks
 checks+=1
 if not ok:findings.append(msg);raise RuntimeError(msg)
def pinned(item):
 b=Path(item['path']).read_bytes();need(H(b)==item['sha256'],'exact input binding '+item['path']);return json.loads(b)
def audit_capture(directory):
 global captures,streambytes
 rows=load(directory/'subcommands.json')
 for number,row in enumerate(rows,1):
  d=directory/'subcommands'/f'{number:06d}';need(row['directory']==str(d)and row==load(d/'result.json'),'exact original capture identity '+str(d))
  for key,value in load(d/'request.json').items():need(value is None if key=='actual_process_returncode'else row.get(key)==value,'original request/result '+str(d)+' '+key)
  for name in ['stdin','stdout','stderr']:
   b=(d/(name+'.bin')).read_bytes();streambytes+=len(b);need(H(b)==row[name+'_sha256'],'complete original stream hash '+str(d)+' '+name)
   if name!='stdin':need(len(b)==row[name+'_bytes'],'complete original stream size '+str(d)+' '+name)
  need(row['source_sha']==row['acceptance_sha']==SOURCE,'original source identity '+str(d))
  need(row['actual_process_returncode']==0 and row['timeout_expired']is False and row['ended_epoch']>=row['started_epoch'],'original actual zero/no timeout '+str(d));captures+=1
 return rows
def physical_index():
 p=ROOT/'.git/index';s=p.lstat();b=p.read_bytes()
 need(b[:4]==b'DIRC'and hashlib.sha1(b[:-20]).digest()==b[-20:],'actual full Git index checksum')
 return {'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'nlink':s.st_nlink,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'sha256':H(b)}

report={'schema':'a6-four-artifact-assembly-actual-peer/1','source_sha':SOURCE,'result_sha256':PIN,'exit_code':1,'blocking_findings':findings,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'formal_judges_rerun_by_peer':False,'assembly_rerun_by_peer':False,'source_or_refs_modified_by_peer':False,'network_used_by_peer':False}
try:
 raw=(BASE/'RESULT.json').read_bytes();need(H(raw)==PIN,'fixed actual assembly result pin');r=json.loads(raw)
 need(r['sourceSHA']==SOURCE and r['exit_code']==0 and r['originalGateExits']==[0,0,0] and r['inputCount']==604 and r['sourceBeforeAfterClean']is True,'true successful a6 assembly')
 need(r['originalJudgesRerun']is False and r['formalLedgerOrNativeExecuted']is False and r['sourceCheckoutModified']is False and r['historicalProbesReexecuted']is False,'execution/source boundary recorded')
 need(H((BASE/'ASSEMBLER.py').read_bytes())==ASSEMBLER_PIN and H(CAP.read_bytes())==CAP_PIN,'actual assembler and original capture pins')
 binding_raw=(BASE/'ROOT_BINDINGS.json').read_bytes();need(binding_raw==(OUTER/'BINDINGS.json').read_bytes(),'outer/inner exact root binding');binding=json.loads(binding_raw)
 need(binding['source_sha']==SOURCE and binding['root_execution_lease']is True,'actual root source/lease')
 prep=pinned(binding['source_result']);sp=pinned(binding['source_actual_peer']);batch=pinned(binding['gate_result']);gp=pinned(binding['gate_actual_peer'])
 need(prep['source_sha']==sp['source_sha']==batch['source_sha']==gp['source_sha']==SOURCE,'all actual source identities a6')
 need(prep['exit_code']==sp['exit_code']==batch['exit_code']==gp['exit_code']==0 and not sp['blocking_findings']and not gp['blocking_findings'],'actual source/gate peers zero')
 need(sp['source_result_sha256']==binding['source_result']['sha256']and gp['gate_result_sha256']==binding['gate_result']['sha256']==r['originalGateBatchSha256'],'source/gate peers exact results')
 manifest_source_raw=(PREP/'SOURCE_MANIFEST.json').read_bytes();need(H(manifest_source_raw)==prep['source_manifest_sha256'],'original selected source manifest pin');source_manifest=json.loads(manifest_source_raw)
 index_before=physical_index();need(index_before==sp['current_source_index'],'current physical source index exactly matches independent pre-gates peer identity')
 need((ROOT/'.git/HEAD').read_text().strip()==SOURCE,'actual detached current a6 HEAD')
 outer=audit_capture(OUTER);inner=audit_capture(BASE)
 need(len(outer)==1 and len(inner)==16,'complete outer and original assembly command count')
 outer_result=load(OUTER/'RESULT.json');need(outer_result=={'exit_code':0,'source_sha':SOURCE,'stack_soft_bytes':16777216},'actual outer zero/original stack')
 need(outer[0]['command']==['python3','-B','/tmp/geo337-a6-architecture-preparation-20261026/assemble_a6.py','--root',str(ROOT),'--sha',SOURCE,'--out',str(BASE),'--root-execution-lease','--bindings',str(OUTER/'BINDINGS.json'),'--bindings-sha256',H(binding_raw)],'exact actual assembler argv')
 for row in inner:need(row['command'][:5]==['git','-c','gc.auto=0','-c','maintenance.auto=false']and row['cwd']==str(ROOT),'assembly command is Git identity only, no judge')
 for n in [2,15]:need((BASE/'subcommands'/f'{n:06d}'/'stdout.bin').read_bytes().strip().decode()==SOURCE,'original assembly HEAD exact a6')
 for n in [3,16]:need((BASE/'subcommands'/f'{n:06d}'/'stdout.bin').read_bytes()==b'','original assembly clean status')
 admitted=load(BASE/'RESOURCE_ADMISSION.json');need(admitted['additional_bound']==67108864 and admitted['shared_ceiling']==2147483648 and admitted['shared_before']+67108864<=2147483648,'original shared/64MiB admission values')
 git_env=load(BASE/'GIT_ENVIRONMENT.json');need(git_env['GIT_INDEX_FILE']==str(BASE/'private-index')and git_env['GIT_CONFIG_KEY_0']=='core.splitIndex'and git_env['GIT_CONFIG_VALUE_0']=='false'and git_env['GIT_OPTIONAL_LOCKS']=='0','separate assembly Git index environment')
 oldbytes={};newbytes={}
 for i,name in enumerate(NAMES):
  old=(BASE/'previous-artifact'/name).read_bytes();new=(BASE/'new'/name).read_bytes();oldbytes[name]=old;newbytes[name]=new
  need(H(old)==PRIOR_PINS[i]and old==(ROOT/ART/name).read_bytes()and old==(BASE/'subcommands'/f'{i+4:06d}'/'stdout.bin').read_bytes(),'prior artifacts remain exact source/adoption Git bytes '+name)
  need(info(new)==r['outputs'][name],'actual output raw/LF/size result '+name)
 need(newbytes[NAMES[0]]==oldbytes[NAMES[0]]and newbytes[NAMES[1]]==oldbytes[NAMES[1]],'manifest and scan byte-for-byte unchanged')
 need([n for n in NAMES if oldbytes[n]!=newbytes[n]]==r['changedArtifacts']==NAMES[2:],'only report/receipt change')
 manifest=json.loads(newbytes[NAMES[0]]);scan=json.loads(newbytes[NAMES[1]]);receipt=json.loads(newbytes[NAMES[3]]);prior=json.loads(oldbytes[NAMES[3]])
 need(prior['sourceBaseHead']==PRIOR and receipt['schema']==prior['schema']=='geometry-product-architecture-receipt/1','original schema and historical actual source')
 need(receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==SOURCE,'new receipt actual source a6')
 snapshot=load(BASE/'source-inputs.json');old_snapshot_path=Path('/tmp/geo337-h-architecture-four-20261025/source-inputs.json');old_snapshot_raw=old_snapshot_path.read_bytes();need(H(old_snapshot_raw)=='ee4eced205432217111ba597f565128ae598f87246c0cc3cc6d9194b52f59618','pinned historical snapshot')
 need(snapshot==json.loads(old_snapshot_raw)and len(snapshot)==604,'entire 604 snapshot exact historical raw/LF/Git identity')
 declared=sorted(x['path']for k in ['sources','exclusions']for x in manifest[k]);need(len(declared)==len(set(declared))==604 and set(declared)==set(source_manifest['architecture_paths']),'complete manifest/selected architecture path set')
 physical=set(manifest['sourceFiles'])
 for source_root in manifest['sourceRoots']:
  for parent,dirs,files in os.walk(ROOT/source_root,followlinks=False):
   need(all(not(Path(parent)/n).is_symlink()for n in dirs),'no architecture directory symlinks')
   for n in files:
    if Path(n).suffix.lower()in SUFFIXES:physical.add((Path(parent)/n).relative_to(ROOT).as_posix())
 need(sorted(physical)==declared,'full real source-root executable inventory exact 604')
 tree={}
 for entry in (BASE/'subcommands/000009/stdout.bin').read_bytes().split(b'\0'):
  if not entry:continue
  meta,name=entry.split(b'\t',1);mode,kind,obj=meta.split();path=name.decode()
  if Path(path).suffix.lower()in SUFFIXES:
   need(kind==b'blob'and mode in[b'100644',b'100755'],'original source Git tree regular blob');tree[path]=obj.decode()
 need(sorted(tree)==declared,'independent original Git tree complete 604')
 current=[]
 for n in declared:
  p=ROOT/n;st=p.lstat();b=p.read_bytes();need(stat.S_ISREG(st.st_mode)and st.st_nlink==1,'current independent source '+n)
  need(oid(b)==tree[n]==source_manifest['files'][n]['oid'],'physical source matches original a6 Git blob '+n)
  current.append({'path':n,'bytes':len(b),'rawSha256':H(b),'lfSha256':H(LF(b)),'gitBlobOid':oid(b)})
 need(current==snapshot,'actual current604 snapshot equals assembly original')
 inputs=[{'path':x['path'],'sha256':x['lfSha256']}for x in current];closure=H(json.dumps(inputs,ensure_ascii=False,separators=(',',':')).encode())
 need(inputs==receipt['inputs']==prior['inputs']and closure==r['inputClosureSHA256']==receipt['inputClosureSha256']==prior['inputClosureSha256'],'all604 ordered LF closure independently recomputed')
 counts={'executableFiles':604,'ownedSources':len(manifest['sources']),'exclusions':len(manifest['exclusions']),'edges':len(scan['edges']),'diagnostics':len(scan['diagnostics']),'layers':dict(sorted(collections.Counter(x['layer']for x in manifest['sources']).items())),'languages':dict(sorted(collections.Counter(x['language']for x in manifest['sources']).items())),'forbiddenIdentifiers':len(manifest['policy']['forbiddenIdentifiers']),'forbiddenStrings':len(manifest['policy']['forbiddenStrings'])}
 need(counts==receipt['counts']and counts['ownedSources']==334 and counts['exclusions']==270 and counts['edges']==798 and counts['diagnostics']==0 and counts['forbiddenIdentifiers']==937 and counts['forbiddenStrings']==55 and scan['ok']is True,'all manifest/scan counts independently recomputed')
 need(receipt['manifestSha256']==H(LF(newbytes[NAMES[0]]))and receipt['scanSha256']==H(LF(newbytes[NAMES[1]]))and receipt['reportSha256']==H(LF(newbytes[NAMES[2]])),'actual four artifact hashes')
 inv=receipt['completeInventoryVerification'];need(inv['filesBefore']==inv['filesAfter']==604 and inv['allRawAndLfInputsUnchanged']is True and inv['inputClosureSha256Before']==inv['inputClosureSha256After']==closure,'receipt inventory snapshot fields')
 for i,n in enumerate(JUDGES,12):
  b=(ROOT/n).read_bytes();need(b==(BASE/'subcommands'/f'{i:06d}'/'stdout.bin').read_bytes(),'current original judge Git bytes '+n)
  need(H(LF(b))==inv['toolHashesBefore'][n]==inv['toolHashesAfter'][n]==prior['completeInventoryVerification']['toolHashesBefore'][n],'judge tool hashes unchanged '+n)
 for i,n in enumerate(['公理層.md','決策佇列.md'],10):
  b=(ROOT/n).read_bytes();need(b==(BASE/'subcommands'/f'{i:06d}'/'stdout.bin').read_bytes(),'protected current source exact original Git '+n)
  need(info(b)==inv['protectedSsotBefore'][n]==inv['protectedSsotAfter'][n],'protected before/after bytes and hashes '+n)
 need(inv['protectedSsotBefore']['決策佇列.md']['rawSha256']=='e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740','exact a6 decision snapshot, not S10')
 need((BASE/'original-gates/batch-RESULT.json').read_bytes()==(GATES/'RESULT.json').read_bytes(),'copied original actual gate batch exact')
 need([x['exit_code']for x in batch['gates']]==[0,0,0]and batch['all_gates_passed']is True and batch['before']==batch['after']and batch['before']['head']==SOURCE,'actual closed a6 gate batch')
 gate_summaries=[]
 for i,g in enumerate(batch['gates'],4):
  original=GATES/'subcommands'/f'{i:06d}';copied=BASE/'original-gates'/f'{i:06d}'
  for n in ['request.json','result.json','stdin.bin','stdout.bin','stderr.bin']:need((copied/n).read_bytes()==(original/n).read_bytes(),'complete copied original gate payload '+str(i)+' '+n)
  row=load(copied/'result.json');need(row==g['command']and row['source_sha']==row['acceptance_sha']==SOURCE and row['cwd']==str(ROOT)and row['actual_process_returncode']==0 and row['timeout_expired']is False,'actual gate execution source/cwd/zero '+str(i))
  for key,value in load(copied/'request.json').items():need(value is None if key=='actual_process_returncode'else row.get(key)==value,'gate request/result '+key)
  for name in ['stdin','stdout','stderr']:
   b=(copied/(name+'.bin')).read_bytes();need(H(b)==row[name+'_sha256'],'copied complete gate hash '+name)
   if name!='stdin':need(len(b)==row[name+'_bytes'],'copied complete gate bytes '+name)
  expected=['-B',JUDGES[i-4]]+(['--root','.','--manifest',ART+NAMES[0]]if i==4 else[]);need(row['command'][1:]==expected,'original exact judge argv')
  if i==4:
   need((copied/'stdout.bin').read_bytes()==newbytes[NAMES[1]],'scan is exact original judge stdout')
   need(receipt['actualCliScan']=={**row,'exitCode':0},'receipt original CLI row exact')
  else:
   text=((copied/'stdout.bin').read_bytes()+b'\n'+(copied/'stderr.bin').read_bytes()).decode();m=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$',text,re.M);expected_count=205 if i==5 else 18
   need(len(m)==1 and int(m[0][0])==expected_count and text.rstrip().endswith('OK'),'true complete test count and zero skips')
   expected_validation={**row,'exitCode':0,'tests':expected_count,'passed':expected_count,'failed':0,'skipped':0,'unittestSeconds':float(m[0][1])}
   need(receipt['validation'][i-5]==expected_validation,'receipt original validation row exact')
  need(row['ended_epoch']<=outer[0]['started_epoch'],'gates terminated before assembly; no execution time relabel')
  gate_summaries.append({'command':row['command'],'exit_code':0,'stdout_sha256':row['stdout_sha256'],'stderr_sha256':row['stderr_sha256'],'started_epoch':row['started_epoch'],'ended_epoch':row['ended_epoch']})
 probes=receipt['supplementalStaticGuardProbes'];need(probes['executedAtCurrentHead']is False and probes['guardIdentifiersRetested']==0 and probes['neutralCases']==0 and probes['historicalExecutionSource']==PRIOR and probes['historicalAdoptionCommit']==ADOPTION and probes['historicalReceiptRawSha256']==PRIOR_PINS[3]and probes['historicalSupplementalStaticGuardProbes']==prior['supplementalStaticGuardProbes'],'all historical M6e50 probes preserved without a6 relabel')
 need(probes['historicalSupplementalStaticGuardProbes']['guardIdentifiersRetested']==9 and probes['historicalSupplementalStaticGuardProbes']['neutralCases']==2,'historical nine probes/two neutrals retained')
 refresh=receipt['manifestRefresh'];need(refresh['previousSource']==PRIOR and refresh['previousArtifactCommit']==ADOPTION and refresh['changedPriorInputs']==[]and refresh['originalThreeGateExits']==[0,0,0],'refresh identities correct')
 need(receipt['nativeAcceptance']==prior['nativeAcceptance']and receipt['notClaimed']==prior['notClaimed'],'no extra native/ledger/browser acceptance claims')
 text=newbytes[NAMES[2]].decode();need('全帳本保留S10實際重產原件'in text and '其於a6有效性由獨立--check判定'in text and '未在a6重跑或移標'in text and '不以其內容自行擴張授權'in text,'report explicitly retains ledger/history/authorization boundaries')
 driver=receipt['refreshDriver'];need(driver['rawSha256']==ASSEMBLER_PIN and driver['recorderSha256']==CAP_PIN and driver['originalThreeGateBatchSha256']==binding['gate_result']['sha256']and driver['originalGatePeerSha256']==binding['gate_actual_peer']['sha256']and driver['sourcePrepPeerSha256']==binding['source_actual_peer']['sha256']and driver['originalJudgesRerun']is False,'driver exact original bindings')
 need(physical_index()==index_before and(ROOT/'.git/HEAD').read_text().strip()==SOURCE,'peer left original full index and HEAD unchanged')
 report.update(exit_code=0,input_count=604,input_closure_sha256=closure,original_gate_exits=[0,0,0],original_gates=gate_summaries,all_four_actual_output_hashes=r['outputs'],manifest_scan_byte_unchanged=True,only_report_receipt_changed=True,all604_raw_lf_git_inputs_verified=True,source_index_identity=index_before,source_index_matches_pre_gates_actual_peer=True,original_heads_clean_before_after=True,historical_mutation_execution_source=PRIOR,historical_probes_relabelled=False,S10_ledger_relabelled=False,source_result_sha256=binding['source_result']['sha256'],gate_result_sha256=binding['gate_result']['sha256'],outer_result_sha256=H((OUTER/'RESULT.json').read_bytes()),root_bindings_sha256=H(binding_raw),original_capture_commands=captures,original_capture_stream_bytes=streambytes,resource_admission=admitted,limits=['This verifies four artifacts assembled from the three original a6 judge executions. It is not product testing at any later adoption/final SHA.','Gate times and assembly snapshot times are distinct; all original execution records were retained exactly.','The source physical index exactly matches the earlier independent source peer, including bytes and inode/metadata; pinned original assembler additionally checked its own before/after state.','Original actual mount free capacity was checked by the pinned assembler but not persisted as a separate numeric field. This peer confirms recorded original shared bound/reserve, not future admission.','Native/browser/performance and S10 ledger applicability require separate original receipts. Historical M6e50 controls remain historical.','SHM artifacts and receipts still require separate byte-exact preservation/publication; this report does not prove remote delivery.'])
except BaseException as exc:
 if not findings:findings.append(repr(exc))
 report['exception']=repr(exc)
finally:
 report.update(exit_code=1 if findings else 0,blocking_findings=findings,checked_count=checks)
 (OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'exit_code':report['exit_code'],'checked_count':checks,'blocking_findings':findings,'review_sha256':H((OUT/'REVIEW.json').read_bytes()),'review_bytes':(OUT/'REVIEW.json').stat().st_size},ensure_ascii=False))
raise SystemExit(report['exit_code'])
