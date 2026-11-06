from pathlib import Path
import collections,datetime,hashlib,json,os,re,stat,sys,subprocess

HERE=Path(__file__).parent
BASE=Path('/dev/shm/geometry-axiom-geo337-20261025')
ASM=BASE/'S10-architecture-four-assembly-20261025'
OUTER=BASE/'S10-architecture-assembly-root-original-20261025'
GATES=BASE/'S10-preledger-checks-original-20261025'
POOL=BASE/'F10-pool'
SOURCE='82c922a3941525d3a094ac0158bdc7dea57ea360'
PRIOR='6e50aef65513b7b38f93228919272c6d40d6c196'
ADOPT='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
NAMES=['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json']
EXPECTED_PINS=['81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975','18f24f186445928e79159bbd49dc10b586a42ab17ded1cf15f2608de4354a728','e6510266388f06d19acf650ff0ecc4c307dc1f4cb41df5a8632cb5caffe17afc','5aee34b55d42569c6d8ec012f17d631a3417cb98bd33ce6cc183a34d1d6136de']
COUNT=0
FAIL=[]
def H(b):return hashlib.sha256(b).hexdigest()
def LF(b):return b.replace(b'\r\n',b'\n')
def read(p):return json.loads(p.read_bytes())
def check(ok,label):
 global COUNT
 COUNT+=1
 if not ok:FAIL.append(label)
def pin(p,h):check(H(p.read_bytes())==h,'pin '+str(p))
def rowcheck(folder,expected=None):
 row=read(folder/'result.json'); req=read(folder/'request.json')
 check(row['actual_process_returncode']==0,'true exit0 '+str(folder))
 check(row['timeout_expired'] is False,'not timed out '+str(folder))
 check(row['ended_epoch']>=row['started_epoch'],'time order '+str(folder))
 check(row['source_sha']==row['acceptance_sha']==SOURCE,'source bind '+str(folder))
 for key,value in req.items():
  check(value is None if key=='actual_process_returncode' else row.get(key)==value,'request/result '+str(folder)+' '+key)
 for stream in ['stdin','stdout','stderr']:
  raw=(folder/(stream+'.bin')).read_bytes()
  check(H(raw)==row[stream+'_sha256'],'hash '+str(folder)+' '+stream)
  if stream!='stdin':check(len(raw)==row[stream+'_bytes'],'length '+str(folder)+' '+stream)
 if expected is not None:check(row==expected,'row/index equality '+str(folder))
 return row

result=read(ASM/'RESULT.json');receipt=read(ASM/'new'/NAMES[3]);old=read(ASM/'previous-artifact'/NAMES[3]);manifest=read(ASM/'new'/NAMES[0]);scan=read(ASM/'new'/NAMES[1]);inp=read(ASM/'source-inputs.json')
check(result['exit_code']==0 and result['sourceSHA']==SOURCE,'inner success identity')
check(read(OUTER/'RESULT.json')['actual_exit']==0,'outer success')
host=read(Path('/tmp/geo337-S10-full123-host-results-20261025/ARCHITECTURE_ASSEMBLY_FINAL.json'))
check(host['exit_code']==0,'host true exit')
static=Path('/tmp/geo337-S10-architecture-assembly-static-peer-20261025/REVIEW.json')
pin(static,'7ddd650a7fa987e34688c6d83f52cf36c0642ec9ca18b501f6ffc49ce17ef3da')
check(read(static)['exit_code']==0,'static peer exit')
pin(ASM/'ASSEMBLER.py','b51110ff9756326a2b47d2ae4a6aded2a7995d92e2a882ddf9ec4065fae87d17')
check((ASM/'ASSEMBLER.py').read_bytes()==Path(receipt['refreshDriver']['path']).read_bytes(),'executed reviewed assembler bytes')
inner=read(ASM/'subcommands.json');outer=read(OUTER/'subcommands.json')
check(len(inner)==16 and len(outer)==1,'exact sixteen identity commands plus one assembler')
for i,row in enumerate(inner,1):
 rowcheck(ASM/'subcommands'/f'{i:06d}',row)
 check(row['command'][0]=='git','assembly subprocess must be Git identity only')
for i,row in enumerate(outer,1):rowcheck(OUTER/'subcommands'/f'{i:06d}',row)
check(outer[0]['command']==read(OUTER/'ROOT_REQUEST.json')['argv'],'root argv exact')
check(outer[0]['command'][2]==receipt['refreshDriver']['path'],'outer executed reviewed assembler')
check(receipt['createdUtc']>datetime.datetime.fromtimestamp(outer[0]['started_epoch'],datetime.timezone.utc).isoformat(),'assembly timestamp begins after launch')
changed=[]
for name,p in zip(NAMES,EXPECTED_PINS):
 raw=(ASM/'new'/name).read_bytes(); pin(ASM/'new'/name,p)
 expected={'bytes':len(raw),'rawSha256':H(raw),'lfSha256':H(LF(raw))}
 check(result['outputs'][name]==expected,'artifact metadata '+name)
 previous=(ASM/'previous-artifact'/name).read_bytes()
 check(previous==(POOL/'geometry-core/domain-decoupling'/name).read_bytes(),'pool original artifacts preserved '+name)
 check(previous==(ASM/'subcommands'/f'{4+NAMES.index(name):06d}'/'stdout.bin').read_bytes(),'prior Git show exact '+name)
 if previous!=raw:changed.append(name)
check(changed==NAMES[2:]==result['changedArtifacts'],'only report and receipt changed')
check(receipt['manifestSha256']==EXPECTED_PINS[0] and receipt['scanSha256']==EXPECTED_PINS[1] and receipt['reportSha256']==EXPECTED_PINS[2],'receipt output hashes')
pin(ASM/'original-gates/batch-RESULT.json','0d592b7c18749bf36d162e82be4d586e7aa017b4eca22695402d9d686d4788f3')
check((ASM/'original-gates/batch-RESULT.json').read_bytes()==(GATES/'RESULT.json').read_bytes(),'batch exact copied original')
batch=read(ASM/'original-gates/batch-RESULT.json')
check([x['exit_code']for x in batch['gates']]==[1,0,0,0,0,0],'old stale ledger1 remains visible')
check(batch['all_gates_passed'] is False and batch['before']==batch['after'],'batch does not hide red or source change')
check(batch['before']['head']==SOURCE and batch['before']['status']=='','original gate source clean')
gate_rows=[]
for i in range(3):
 f=ASM/'original-gates'/f'{i+5:06d}'
 row=rowcheck(f,batch['gates'][i+1]['command']);gate_rows.append(row)
 for leaf in ['request.json','result.json','stdin.bin','stdout.bin','stderr.bin']:
  check((f/leaf).read_bytes()==(GATES/'subcommands'/f'{i+5:06d}'/leaf).read_bytes(),'original gate copy '+str(i)+' '+leaf)
 expected=[['tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['tests/test_architecture_contract.py'],['tests/test_product_architecture.py']][i]
 check(row['command'][1:]==['-B',*expected],'original exact judge argv '+str(i))
 check(row['cwd']==str(POOL),'original cwd '+str(i))
 target=receipt['actualCliScan'] if i==0 else receipt['validation'][i-1]
 for k,v in row.items():check(target.get(k)==v,'receipt original command field '+str(i)+' '+k)
 check(target['exitCode']==0,'receipt gate exit '+str(i))
 check(row['ended_epoch']<outer[0]['started_epoch'],'original gate time predates assembly '+str(i))
 if i==0:check((f/'stdout.bin').read_bytes()==(ASM/'new'/NAMES[1]).read_bytes(),'scan exact judge stdout')
 else:
  text=((f/'stdout.bin').read_bytes()+b'\n'+(f/'stderr.bin').read_bytes()).decode()
  counts=re.findall(r'^Ran (\d+) tests? in ([0-9.]+)s$',text,re.M)
  check(len(counts)==1 and int(counts[0][0])==[205,18][i-1],'unit count '+str(i))
  check(text.rstrip().endswith('OK') and not re.search(r'\b(skipped|FAILED)\b',text),'zero skip actual stream '+str(i))
  check(target['passed']==[205,18][i-1] and target['failed']==target['skipped']==0,'receipt unittest counts '+str(i))
check(scan['ok'] is True and scan['diagnostics']==[] and len(scan['edges'])==798,'scan actual pass and count')
paths=sorted(x['path']for section in ['sources','exclusions'] for x in manifest[section])
check(len(paths)==len(set(paths))==604,'manifest complete distinct604')
check(len(manifest['sources'])==334 and len(manifest['exclusions'])==270,'ownership334 exclusions270')
check(len(manifest['policy']['forbiddenIdentifiers'])==937 and len(manifest['policy']['forbiddenStrings'])==55,'policy937 and55')
check([x['path']for x in inp]==paths,'source-inputs exact sorted closure')
expected_inputs=[{'path':x['path'],'sha256':x['lfSha256']}for x in inp]
check(expected_inputs==receipt['inputs']==old['inputs'],'new and historical LF604 exact')
closure=H(json.dumps(expected_inputs,ensure_ascii=False,separators=(',',':')).encode())
check(closure==receipt['inputClosureSha256']==result['inputClosureSHA256']=='8d47b6202e793aa5755a887ea2cbb6b90506c68ca4270e0c0df0716142ca3b89','recomputed input closure')
prior_inp=Path('/tmp/geo337-h-architecture-four-20261025/source-inputs.json')
pin(prior_inp,'ee4eced205432217111ba597f565128ae598f87246c0cc3cc6d9194b52f59618')
check(read(prior_inp)==inp,'604 all raw LF Git snapshot unchanged from actual prior')
tree={}
for entry in (ASM/'subcommands/000009/stdout.bin').read_bytes().split(b'\0'):
 if not entry:continue
 meta,name=entry.split(b'\t',1);mode,kind,oid=meta.split()
 tree[name.decode()]={'mode':mode.decode(),'kind':kind.decode(),'oid':oid.decode()}
suffixes={'.c','.cc','.cjs','.cpp','.cxx','.h','.hh','.hpp','.htm','.html','.inc','.js','.jsx','.mjs','.py','.ts','.tsx'}
check(sorted(k for k in tree if Path(k).suffix.lower() in suffixes)==paths,'independent original S10 Git tree full executable inventory')
inventory=set(manifest['sourceFiles'])
for root in manifest['sourceRoots']:
 for parent,dirs,files in os.walk(POOL/root,followlinks=False):
  for name in dirs:check(not(Path(parent)/name).is_symlink(),'no source symlink directory')
  for name in files:
   path=Path(parent)/name
   if path.suffix.lower()in suffixes:inventory.add(path.relative_to(POOL).as_posix())
check(sorted(inventory)==paths,'current filesystem executable inventory no missing or added input')
for x in inp:
 p=POOL/x['path'];check(stat.S_ISREG(p.lstat().st_mode),'input regular '+x['path']);b=p.read_bytes()
 check(len(b)==x['bytes'] and H(b)==x['rawSha256'] and H(LF(b))==x['lfSha256'],'input actual raw LF '+x['path'])
 oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 check(oid==x['gitBlobOid']==tree[x['path']]['oid'],'input actual Git OID '+x['path'])
historical=receipt['supplementalStaticGuardProbes']
check(historical['executedAtCurrentHead'] is False and historical['guardIdentifiersRetested']==historical['neutralCases']==0,'no old probes relabelled current')
check(historical['historicalExecutionSource']==PRIOR and historical['historicalAdoptionCommit']==ADOPT,'historical source preserved')
check(historical['historicalSupplementalStaticGuardProbes']==old['supplementalStaticGuardProbes'],'historical original fields exact')
check(historical['historicalSupplementalStaticGuardProbes']['fixedWithdrawnRestored']==[0,1,0] and historical['historicalSupplementalStaticGuardProbes']['guardIdentifiersRetested']==9 and historical['historicalSupplementalStaticGuardProbes']['neutralCases']==2,'historical nine010 two neutral scope')
pin(ASM/'previous-artifact'/NAMES[3],historical['historicalReceiptRawSha256'])
for key in ['originalJudgesRerun','formalLedgerOrNativeExecuted','sourceCheckoutModified','historicalProbesReexecuted']:check(result[key] is False,'not claimed '+key)
check(receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==SOURCE,'receipt fixed S10 execution source')
for n in [1,14]:check((ASM/'subcommands'/f'{n+1:06d}'/'stdout.bin').read_bytes()==(SOURCE+'\n').encode(),'original before/after head '+str(n))
for n in [3,16]:check((ASM/'subcommands'/f'{n:06d}'/'stdout.bin').read_bytes()==b'','original before/after clean '+str(n))
ci=receipt['completeInventoryVerification']
check(ci['protectedSsotBefore']==ci['protectedSsotAfter'],'SSOT before after exact')
check(ci['toolHashesBefore']==ci['toolHashesAfter'],'judges before after exact')
for i,(name,data) in enumerate(ci['protectedSsotBefore'].items(),10):
 b=(ASM/'subcommands'/f'{i:06d}'/'stdout.bin').read_bytes()
 check(H(b)==data['rawSha256'] and H(LF(b))==data['lfSha256'] and len(b)==data['bytes'],'original Git SSOT '+name)
 check(b==(POOL/name).read_bytes(),'protected SSOT still preserved '+name)
for i,(name,h) in enumerate(ci['toolHashesBefore'].items(),12):
 b=(ASM/'subcommands'/f'{i:06d}'/'stdout.bin').read_bytes()
 check(H(LF(b))==h and b==(POOL/name).read_bytes(),'original Git judge '+name)
index=(ASM/'private-index').read_bytes()
check(index[:4]==b'DIRC' and hashlib.sha1(index[:-20]).digest()==index[-20:],'full private index checksum')
idx=(POOL/(ASM/'subcommands/000001/stdout.bin').read_text().strip())
check(idx.read_bytes()==index,'current source original index bytes still preserved')
records=[]
for root in [ASM,OUTER]:
 for p in sorted(root.rglob('*')):
  if p.is_file():records.append({'path':str(p),'bytes':p.stat().st_size,'sha256':H(p.read_bytes())})
inventory_json=json.dumps(records,ensure_ascii=False,separators=(',',':')).encode()
(HERE/'ARTIFACTS.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
review={'schema':'geo337-resume-architecture-actual-audit/1','reviewedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA':SOURCE,'exit_code':int(bool(FAIL)),'checkCount':COUNT,'blockingFindings':FAIL,'formalProductTestsRerun':False,'productSourceModified':False,'gitCommandsExecuted':False,'adoptionPerformed':False,'usableForS10ArchitectureArtifactAdoption':not FAIL,'requiresBeforeFinalAdoption':['Root must publish full original package and verify remote bytes.','Root must verify final adoption diff contains only intended generated ledger/report/receipt.','S10 execution source remains S10; future final SHA must not be labelled as the execution source of these original gates.'],'actualOriginalAssemblyExit':outer[0]['actual_process_returncode'],'originalAssemblyStartedUtc':datetime.datetime.fromtimestamp(outer[0]['started_epoch'],datetime.timezone.utc).isoformat(),'originalAssemblyEndedUtc':datetime.datetime.fromtimestamp(outer[0]['ended_epoch'],datetime.timezone.utc).isoformat(),'originalGateExits':[x['actual_process_returncode']for x in gate_rows],'originalGateTestCounts':[None,205,18],'originalLedgerStaleExitRetained':1,'inputCount':604,'inputClosureSHA256':closure,'changedArtifacts':changed,'artifactPins':dict(zip(NAMES,EXPECTED_PINS)),'originalRegularFileCount':len(records),'originalLogicalBytes':sum(x['bytes']for x in records),'artifactInventoryCanonicalSHA256':H(inventory_json),'reviewScriptSHA256':H(Path(__file__).read_bytes()),'limits':['This is a read-only actual evidence audit, not a rerun of architecture, native, browser or mutation tests.','Historical 9 fixed/withdrawn/restored controls and 2 neutral cases remain M6e50; their raw execution archive was not reaudited here.','Outer receipt/complete streams and current source confirm recorded assembly; independent cryptographic timestamps or remote delivery are outside this audit.']}
latest='a6f4013364e21bcb7239b5dcc25caac0f6d61f77'
args=['git','--no-optional-locks','-C',str(BASE/'publisher-source'),'show',latest+':決策佇列.md']
current=subprocess.run(args,capture_output=True,check=False)
latest_context={'headReportedByRoot':latest,'command':args,'exit_code':current.returncode,'stdoutBytes':len(current.stdout),'stdoutSHA256':H(current.stdout),'stderrSHA256':H(current.stderr),'historicalS10DecisionSHA256':ci['protectedSsotAfter']['決策佇列.md']['rawSha256'],'formalGate':False,'onlyMetadataSaved':True}
latest_context['decisionSnapshotDiffersFromS10']=current.returncode==0 and H(current.stdout)!=latest_context['historicalS10DecisionSHA256']
review['latestHeadContext']=latest_context
review['gitCommandsExecuted']=True
review['limits'].append('Latest head a6f4013364e21bcb7239b5dcc25caac0f6d61f77 has a different decision-queue snapshot. This is only an S10 historical architecture receipt; it cannot certify a6f40133 or a later final source without fresh identity/snapshot handling.')
(HERE/'REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
(HERE/'SUMS.sha256').write_text(''.join(H(p.read_bytes())+'  '+p.name+'\n'for p in sorted(HERE.iterdir())if p.is_file()and p.name!='SUMS.sha256'))
print(json.dumps({'exit_code':review['exit_code'],'checks':COUNT,'failures':FAIL,'review_sha256':H((HERE/'REVIEW.json').read_bytes()),'review_path':str(HERE/'REVIEW.json'),'total_written_bytes':sum(p.stat().st_size for p in HERE.iterdir()if p.is_file())},ensure_ascii=False))
sys.exit(review['exit_code'])
