from pathlib import Path
import hashlib,json,re,datetime,collections
O=Path(__file__).parent;P=Path('/tmp/geo344-architecture-exact-20261025');W=Path('/tmp/geo344-architecture-outer-20261025');S='9aec9a32630fc65f94c53d49e99969e546574d6e'
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(Path(p).read_bytes())
N=0;fails=[];streambytes=0

def ck(v,s):
 global N
 N+=1
 if not v:fails.append(s)

def stdout(i):return (P/'subcommands'/f'{i:06d}'/'stdout.bin').read_bytes()
def stderr(i):return (P/'subcommands'/f'{i:06d}'/'stderr.bin').read_bytes()

def check_commands(root):
 global streambytes
 rows=J(root/'subcommands.json')
 for i,r in enumerate(rows,1):
  d=root/'subcommands'/f'{i:06d}';ck(Path(r['directory'])==d,'original command directory');ck(J(d/'result.json')==r,'exact original result');ck(J(d/'request.json')['command']==r['command'],'exact original argv');ck(r['source_sha']==S and r['acceptance_sha']==S,'same S344');ck(not r['timeout_expired'],'no timeout')
  for t in ['stdin','stdout','stderr']:
   b=(d/(t+'.bin')).read_bytes();streambytes+=len(b);ck(H(b)==r[t+'_sha256'],'full '+t+' hash')
   if t!='stdin':ck(len(b)==r[t+'_bytes'],'full '+t+' length')
  ck(r['environment']['PYTHONOPTIMIZE'] is None,'Python optimization disabled in executed environment')
 return rows
q=J(P/'RESULT.json');receipt=J(P/'new/product-architecture-receipt.json');scan=J(P/'new/product-architecture-scan.json');inputs=J(P/'source-inputs.json');rows=check_commands(P);outerrows=check_commands(W)
ck(len(rows)==57 and len(outerrows)==11,'57 formal +11 originalouter CLI')
ck(H((P/'RESULT.json').read_bytes())=='8dddc6d2ae8d2f715cc9d3f3625ae573a3cbd5e91c3417fa88aeb35dabde99dc','pinned original RESULT')
ck(J(W/'RESULT.json')['exit_code']==0 and J('/tmp/geo344-architecture-EXEC_FINAL-20261025.json')['exit_code']==0,'outer and truehost0')
ck(q['sourceSHA']==S and q['sourceBeforeAfterClean'] and not q['sourceCheckoutModified'] and not q['ledgerRegenerated'],'source/execution/adoption boundaries')
ck(q['originalGateExits']==[0,0,0] and q['exclusionDigestProofExits']==[0,1,0] and q['existingGuardCasesRetested']==9,'reported exact gates')
ck(stdout(1).decode().strip()==S==stdout(56).decode().strip() and stdout(2)==stdout(57)==b'','original beforeafterHEAD andclean')
for i,argv in [(21,['python3','-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json']),(22,['python3','-B','tests/test_architecture_contract.py']),(23,['python3','-B','tests/test_product_architecture.py'])]:
 ck(rows[i-1]['command']==argv and rows[i-1]['actual_process_returncode']==0,'original threejudge argv exit')
for i,tests in [(22,205),(23,18)]:
 z=stderr(i).decode();ck(re.search(r'Ran '+str(tests)+r' tests in ',z) is not None and z.rstrip().endswith('OK') and 'skipped=' not in z and '\nFAILED' not in z,'raw unittest counts/zero skips')
ck(stdout(21)==(P/'new/product-architecture-scan.json').read_bytes(),'scan is original CLI stdout')
ck(scan['ok'] and len(scan['sources'])==334 and len(scan['trustedSourcesNotParsed'])==6 and len(scan['edges'])==798 and scan['diagnostics']==[],'scan counts original')
ck(receipt['counts']=={'executableFiles':604,'ownedSources':334,'exclusions':270,'edges':798,'diagnostics':0,'layers':{'H':192,'K':69,'W':67,'vendor':6},'languages':{'c':191,'html':4,'javascript':64,'python':75},'forbiddenIdentifiers':937,'forbiddenStrings':55},'receipt exact counts')
for name,meta in q['outputs'].items():
 b=(P/'new'/name).read_bytes();ck(len(b)==meta['bytes'] and H(b)==meta['rawSha256'] and H(b.replace(b'\r\n',b'\n'))==meta['lfSha256'],'all four actual output hashes '+name)
ck(receipt['manifestSha256']==q['outputs']['product-architecture.json']['rawSha256'] and receipt['scanSha256']==q['outputs']['product-architecture-scan.json']['rawSha256'] and receipt['reportSha256']==q['outputs']['PRODUCT-ARCHITECTURE.md']['rawSha256'],'receipt binds three other outputs')
new=(P/'new/product-architecture.json').read_bytes();old=(P/'previous-artifact/product-architecture.json').read_bytes();oldhash=b'bb66742aa10b603b84362277f9f2c4275da8904925e75c618f252bd7df42cc3e';newhash=b'1f3e2e36283ed7bbf6c4ad2cf3dc12c685667356d186d9fbd47bc5f0520f07ee'
ck(old.count(oldhash)==1 and old.replace(oldhash,newhash)==new,'sole cdp LF digest bytes change')
ck(new==(P/'execution-source-originals/product-architecture.json').read_bytes(),'new manifest equals execution manifest')
ck((P/'single-cdp-digest-withdrawn.json').read_bytes()==old,'singlewithdrawn restores only original digest')
proof=J(P/'single-exclusion-digest-proof.json');ck([x['phase'] for x in proof]==['fixed','withdrawn','restored'] and [x['actualExit'] for x in proof]==[0,1,0],'single digest phase010')
for i,r in zip([24,25,26],proof):ck(r['command']['actual_process_returncode']==rows[i-1]['actual_process_returncode'] and r['sourceGitSHA']==S,'digest actual row bind')
bad=json.loads(stdout(25));ck(len(bad['diagnostics'])==1 and bad['diagnostics'][0]['code']=='EXCLUSION_DIGEST' and bad['diagnostics'][0]['path']=='geometry-web/cdp_test.js' and bad['sources']==[],'unique exclusion digest failure cause');ck(stdout(24)==stdout(26)==stdout(21),'fixed/restored exact originalscan')
historical=(P/'historical-928-manifest.json').read_bytes();derived=(P/'historical-928-with-current-cdp-digest.json').read_bytes()
ck(H(historical)=='80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525' and historical==stdout(10),'historical raw original')
ck(historical.count(oldhash)==1 and historical.replace(oldhash,newhash)==derived and H(derived)=='2661beb6a5223d2aeecd64d708194261d97f0a738c1fc3adb22ff431c07bbbb8','derived historical onlycdpdigest');ck((P/'withdrawn-manifest.json').read_bytes()==derived,'actual Wwithdrawn exact derivedcontrol')
policy=J(P/'policy-guard-inventory.json');names=[x['identifier'] for x in policy['historicalGuardIdentifiers']];ck(len(names)==9 and len(set(names))==9 and policy['oldCount']==policy['newCount']==937 and policy['stringCount']==55 and policy['addedIdentifiers']==policy['removedIdentifiers']==[],'unchanged policy nine existing identifiers')
for g,name in enumerate(names):
 a=27+g*3;triple=rows[a-1:a+2];ck([x['actual_process_returncode'] for x in triple]==[0,1,0],'W010 '+name)
 outputs=[json.loads(stdout(i)) for i in range(a,a+3)]
 for j,z in enumerate(outputs):
  ck(z['identifier']==name,'W exact identifier')
  if j==1:ck(z['diagnostics']==[] and ('new W identifier must be rejected from K: '+name).encode() in stderr(a+j),'W withdrawn exact assertion notenvironment')
  else:ck(len(z['diagnostics'])==1 and z['diagnostics'][0]['code']=='FORBIDDEN_IDENTIFIER' and z['diagnostics'][0]['path']=='geometry-core/kernel/geometry.c' and name in z['diagnostics'][0]['message'],'W fixed/restored exact diagnostic')
 ck(triple[0]['command']==triple[2]['command'] and triple[0]['command'][3]==triple[1]['command'][3],'same original probe fixed/restored')
for i in [54,55]:
 z=json.loads(stdout(i));ck(rows[i-1]['actual_process_returncode']==0 and z['identifier']=='geo261_architecture_neutral_probe' and z['diagnostics']==[],'neutral controls retained')
expected_red={25,*range(28,54,3)};ck({i for i,r in enumerate(rows,1) if r['actual_process_returncode']!=0}==expected_red and all(rows[i-1]['actual_process_returncode']==1 for i in expected_red),'exact ten expected proof reds only')
ck(all(r['actual_process_returncode']==0 for r in outerrows),'all outerCLI0')
# Cross-check all604 original inventory OIDs against both preserved original Git ls-tree outputs. No live product files are read.
def parse_tree(b):
 out={}
 for z in b.split(b'\0'):
  if not z:continue
  a,name=z.split(b'\t',1);mode,kind,oid=a.split();out[name.decode()]=(mode.decode(),kind.decode(),oid.decode())
 return out
current=parse_tree(stdout(14));prior=parse_tree(stdout(15));ck(len(inputs)==604 and [x['path'] for x in inputs]==sorted(x['path'] for x in inputs),'pathsorted 604 inventory')
closure=[];changed=[]
for r in inputs:
 p=r['path'];ck(p in current and current[p][1]=='blob' and current[p][2]==r['gitBlobOid'],'604 originalGitOID '+p);ck(len(r['rawSha256'])==64 and len(r['lfSha256'])==64 and r['bytes']>=0,'inventory raw/LF shape')
 ck(p in prior,'prior input exists')
 if prior[p][2]!=current[p][2]:changed.append(p)
 closure.append({'path':p,'sha256':r['lfSha256']})
ck(changed==['geometry-web/app.js','geometry-web/cdp_test.js'],'exact 2 changed/602 unchanged Gitinputs');ck(closure==receipt['inputs'],'receipt completeclosurematches original inventory')
ch=H(json.dumps(closure,ensure_ascii=False,separators=(',',':')).encode());ck(ch==q['inputClosureSHA256']==receipt['inputClosureSha256'],'exact canonical604closurehash')
inv=receipt['completeInventoryVerification'];ck(inv['filesBefore']==inv['filesAfter']==604 and inv['allRawAndLfInputsUnchanged'] and inv['inputClosureSha256Before']==inv['inputClosureSha256After']==ch and inv['toolHashesBefore']==inv['toolHashesAfter'] and inv['protectedSsotBefore']==inv['protectedSsotAfter'],'original beforeafter recorded closure/SSOT/tool equality')
for i,name in [(16,'tests/architecture_contract.py'),(17,'tests/test_architecture_contract.py'),(18,'tests/test_product_architecture.py')]:ck(H(stdout(i).replace(b'\r\n',b'\n'))==inv['toolHashesBefore'][name],'original exactjudge bytes')
for i,name in [(19,'公理層.md'),(20,'決策佇列.md')]:ck(H(stdout(i))==inv['protectedSsotBefore'][name]['rawSha256'],'original SSOT bytehash')
for tool,pin in [('refresh_architecture_cdp_exclusion.py','71cb2e314a3d3e7c3419bbe436f2c308a702d6b3be5f9668594fe729248de2de'),('capture.py','c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762')]:ck(H((P/'tools'/tool).read_bytes())==pin,'executedtool retained '+tool)
ck(H((W/'LAUNCHER.py').read_bytes())=='1dc3e7ee783dda593a4ab539e09b12903dd88193fd49b732d5cf4dbb261aa3d6','executedlauncher exact')
budget=J(W/'RESOURCE_PLAN.json');ck(budget['workspace_free']>=60000000 and budget['tmp_free']>budget['tmp_estimated_peak_with_reserve'] and budget['materialized_needed']==613,'original resourceadmission');ck(J(W/'STACK.json')['after'][0]==16777216,'original16MiBstack')
r={'schema':'geo344-exact-architecture-independent-actual-peer/1','exit_code':0 if not fails else 1,'checks':N,'failed_checks':fails,'source_sha':S,'original_gate_exits':[0,0,0],'generic_unit_tests':205,'product_unit_tests':18,'skipped':0,'single_digest_proof_exits':[0,1,0],'single_digest_failure':'EXCLUSION_DIGEST only','W_guard_groups':9,'W_guard_exits':[0,1,0],'neutral_controls':2,'formal_original_commands':57,'outer_original_commands':11,'original_stream_bytes_checked':streambytes,'input_count':604,'input_bytes_recorded':sum(x['bytes'] for x in inputs),'changed_inputs':changed,'input_closure_sha256':ch,'output_hashes':q['outputs'],'outer_exit':0,'host_exit':0,'result_sha256':H((P/'RESULT.json').read_bytes()),'source_before_after_clean_original':True,'derived_four_files_not_yet_adopted_at_review':True,'tests_rerun':False,'limits':['Original all raw CLI streams and output hashes read; no formal judge, C/browser, source materialization or Git mutation rerun.','Did not reread all20,713,378B live product payloads. All604 recorded Git OIDs are independently compared with preserved original current/prior ls-tree bytes; original reviewed adapter performed before/after raw/LF hashes, captured equality is retained.','Historical928 raw remains80f44…; effective withdrawal is explicit2661… derived control differing onlycdp digest, not falsely labelled historical raw.','This accepts architecture actual only. Ledger/native/fullcanvas/#344PR acceptance remain separate; no newW lexicon completeness claim.','Four new artifacts remain external and need exact byte adoption plus normal commit/push; this peer does not claim they are already committed.'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));assert r['exit_code']==0
