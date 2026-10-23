from pathlib import Path
import hashlib,json,re,subprocess
D=Path('/tmp/train337-adversarial');P=Path('/tmp/geo339-light-gates-M1f0ebd3e-preflight');A=Path('/tmp/geo339-architecture-four-M1f0ebd3e');R=Path('/tmp/geo324-faces-work-20261024');M='1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599';N=0;fail=[]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(n,v):
 global N
 N+=1
 if not v:fail.append(n)
def git(*a):return subprocess.check_output(['git','-C',str(R),*a])
indexpath=Path('/tmp/geo339-M-light-checks-and-architecture-INDEX.json');idx=j(indexpath);ck('fixed index',h(indexpath.read_bytes())=='88e82ff782a09615c538ced03d407790ecc447e4ade10b65e41495337a8e8616');ck('316unique originals',len(idx['members'])==len({x['member'] for x in idx['members']})==316)
for x in idx['members']:
 b=Path(x['source']).read_bytes();ck('original '+x['member'],len(b)==x['bytes'] and h(b)==x['sha256'])
f=j(P/'FOUR_ORIGINAL_CHECKS.json');g=j(P/'GENERIC_ACTUAL.json');ar=j(A/'RESULT.json');receipt=j(A/'new/product-architecture-receipt.json');prev=j(A/'previous/product-architecture-receipt.json');inputs=j(P/'M_INPUT_IDENTITY_BEFORE.json');ainputs=j(A/'source-inputs.json')
ck('all execution sourceM',f['executionSHA']==g['executionSHA']==ar['sourceSHA']==receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==M);ck('original4exit0001', [x['originalExit'] for x in f['rows']]==[0,0,0,1] and not f['allFourOriginalExitZero'] and not f['ledgerRegenerated'] and not f['testsAssertionsProductChanged']);ck('seven remaining gatesUNRUN',len(f['remainingFormalUnrun'])==7 and f['remainingFormalUnrun'][0]=='native-and-full-expected')
commands=j(P/'subcommands.json')+j(A/'subcommands.json');commands += [j('/tmp/geo339-architecture-four-launch-M1f0ebd3e/receipt.json')]
for i,c in enumerate(commands):
 ck('command '+str(i)+' no timeout',not c['timeout_expired'])
 for s in ['stdin','stdout','stderr']:
  b=(Path(c['directory'])/(s+'.bin')).read_bytes();ck('command '+str(i)+' exact '+s,h(b)==c[s+'_sha256'] and (s=='stdin' or len(b)==c[s+'_bytes']))
actual=[g['actualCommand']]+[x['actualCommand'] for x in f['rows'][1:]];expected=[['python3','-B','tests/test_architecture_contract.py'],['python3','-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['python3','-B','tests/test_product_architecture.py'],['python3','-B','tests/mutate.py','--check']]
for i,c in enumerate(actual):ck('original gate argv/source/exit '+str(i),c['command']==expected[i] and c['actual_process_returncode']==[0,0,0,1][i] and c['acceptance_sha']==c['source_sha']==M and c['environment']['PYTHONOPTIMIZE'] is None)
for c,count in [(actual[0],205),(actual[2],18)]:
 s=(Path(c['directory'])/'stderr.bin').read_text();ck('original unittest '+str(count),bool(re.search(r'Ran '+str(count)+r' tests in [\d.]+s',s)) and s.rstrip().endswith('OK') and 'skipped=' not in s and 'FAILED' not in s)
s=(Path(actual[3]['directory'])/'stdout.bin').read_text();ck('ledger red107stale13unrun preserved',all(x in s for x in ['變異表 123 筆,紀錄 110 筆','過期 stale 107','退役 retired 3','未跑 unrun 13']))
ck('M initialfinal clean bindings',f['sourceBefore']==f['sourceAfter'] and f['sourceBefore'][0]==M and f['sourceBeforeClean'] and f['sourceAfterClean'] and f['allOriginalGitBytesBeforeAfterSame'] and f['inputCount']==len(inputs)==1119)
tree={}
for z in git('ls-tree','-rz',M).split(b'\0'):
 if z:
  meta,p=z.split(b'\t');mode,kind,oid=meta.split();tree[p.decode()]=(mode.decode(),oid.decode())
names=[x['path'] for x in inputs];raw=subprocess.run(['git','-C',str(R),'cat-file','--batch'],input=''.join(M+':'+p+'\n' for p in names).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout;off=0;blobs={}
for x in inputs:
 p=x['path'];end=raw.index(b'\n',off);header=raw[off:end].split();size=int(header[2]);off=end+1;b=raw[off:off+size];off+=size+1;blobs[p]=b
 ck('Git exact1119 '+p,len(b)==x['bytes'] and h(b)==x['sha256'] and h(b.replace(b'\r\n',b'\n'))==x['lfSha256'] and header[0].decode()==x['blob']==tree[p][1] and tree[p][0]==x['mode'])
ck('604exactsubset',len(ainputs)==604 and len({x['path'] for x in ainputs})==604 and {x['path'] for x in ainputs}<set(names))
for x in ainputs:
 b=blobs[x['path']];ck('architecture exact input '+x['path'],len(b)==x['bytes'] and h(b)==x['rawSha256'] and h(b.replace(b'\r\n',b'\n'))==x['lfSha256'])
expectedrows=[{'path':x['path'],'sha256':x['lfSha256']} for x in ainputs];ck('pathsorted closure serialization',receipt['inputs']==expectedrows and expectedrows==sorted(expectedrows,key=lambda x:x['path']) and h(json.dumps(expectedrows,ensure_ascii=False,separators=(',',':')).encode())==ar['inputClosureSHA256']==receipt['inputClosureSha256'])
changed=[x for x,y in zip(receipt['inputs'],prev['inputs']) if x!=y];ck('only W source changed fromec8',len(changed)==1 and changed==ar['changedPriorReceiptInputs'] and changed[0]['path']=='geometry-templates/woodworking/geometry_woodworking/model_sources.py' and [x['path'] for x in receipt['inputs']]==[x['path'] for x in prev['inputs']]);ck('original schema preserved',receipt['schema']==prev['schema']=='geometry-product-architecture-receipt/1' and set(receipt)==set(prev))
for name,x in ar['outputs'].items():
 b=(A/'new'/name).read_bytes();ck('new artifact '+name,len(b)==x['bytes'] and h(b)==x['rawSha256'] and h(b.replace(b'\r\n',b'\n'))==x['lfSha256'])
for name in ['product-architecture.json','product-architecture-scan.json']:ck('same immutable policies/scan '+name,(A/'new'/name).read_bytes()==(A/'previous'/name).read_bytes())
ck('receipt derivedhashes',{k:receipt[k] for k in ['manifestSha256','scanSha256','reportSha256']}=={'manifestSha256':ar['outputs']['product-architecture.json']['lfSha256'],'scanSha256':ar['outputs']['product-architecture-scan.json']['lfSha256'],'reportSha256':ar['outputs']['PRODUCT-ARCHITECTURE.md']['lfSha256']});ck('not self hashing',all(x['path'] not in receipt['inputClosureExcludes'] for x in receipt['inputs']))
ck('counts exact604/334/270/798/928/55',ar['counts']==receipt['counts']=={'executableFiles':604,'ownedSources':334,'exclusions':270,'edges':798,'diagnostics':0,'layers':{'H':192,'K':69,'W':67,'vendor':6},'languages':{'c':191,'html':4,'javascript':64,'python':75},'forbiddenIdentifiers':928,'forbiddenStrings':55})
scan=j(A/'new/product-architecture-scan.json');ck('actualscan no diagnostics',scan['ok'] and len(scan['sources'])==334 and len(scan['edges'])==798 and scan['diagnostics']==[] and (Path(actual[1]['directory'])/'stdout.bin').read_bytes()==(A/'new/product-architecture-scan.json').read_bytes())
ac=j(A/'subcommands.json');withdraw,restore=ac[3:5];diag=j(Path(withdraw['directory'])/'stdout.bin')['diagnostics'];ck('trueM manifest0/1/0',ar['manifestProofExits']==[0,1,0] and actual[1]['actual_process_returncode']==0 and withdraw['actual_process_returncode']==1 and restore['actual_process_returncode']==0 and withdraw['source_sha']==restore['source_sha']==M and len(diag)==1 and diag[0]['code']=='EXCLUSION_DIGEST' and diag[0]['path']=='geometry-core/card-reference/run_axiom_mutations.py');ck('restoredscan exact', (Path(restore['directory'])/'stdout.bin').read_bytes()==(A/'new/product-architecture-scan.json').read_bytes());ck('historicalproof remains historical',receipt['manifestRefresh']['inheritedManifestProof']['executedAtCurrentHead'] is False and receipt['manifestRefresh']['inheritedManifestProof']['executionSha']=='17b3576434ffd0833056668898e1fd1a8cc2d560')
ck('new proof receipt exact commandrows',[x['exit'] for x in receipt['manifestRefresh']['manifestProof']]==[0,1,0] and [x['directory'] for x in receipt['manifestRefresh']['manifestProof']]==[actual[1]['directory'],withdraw['directory'],restore['directory']]);ck('no false native or ledgergreen',ar['ledgerOriginalExit']==1 and not ar['ledgerRegenerated'] and not ar['sourceCheckoutModified'] and receipt['supplementalStaticGuardProbes']['executedAtCurrentHead'] is False)
ck('architecture beforeafter HEAD/tree andclean', (Path(ac[0]['directory'])/'stdout.bin').read_bytes()==(Path(ac[5]['directory'])/'stdout.bin').read_bytes() and (Path(ac[0]['directory'])/'stdout.bin').read_text().splitlines()[0]==M and (Path(ac[1]['directory'])/'stdout.bin').read_bytes()==(Path(ac[6]['directory'])/'stdout.bin').read_bytes()==b'')
out={'schema':'geo339-M-four-checks-and-four-artifacts-actual-peer/1','source_sha':M,'checks':N,'exit_code':int(bool(fail)),'findings':fail,'original_gate_exits':[0,0,0,1],'manifest_control_exits':[0,1,0],'counts':ar['counts'],'generic':205,'product':18,'original_inputs':1119,'arch_inputs':604,'original_raw_files':316,'index_sha256':h(indexpath.read_bytes()),'limits':['只讀原終態raw與fixedM Git，沒有重跑裁判或subject。','Mutation原check1：123定義/110紀錄/107stale/3retired/13unrun；沒有重產帳本，完整native＋6browser仍7UNRUN。','新四檔只有manifest/scan byte同，report/receipt新M；原P17反證僅歷史，新0/1/0確M。','四檔repo外，owner尚須正常提交出版；原M execution不轉標後續evidenceSHA。','928/55只沿政策count，不冒新詞彙完整性或Windows supplemental動態驗收。','初metadata讀取假設每row皆receipt欄發KeyError：hostchunk19e29f/exit1；未改subject原件，改讀actualCommand異質schema後完成。']};p=D/'GEO339_M_FOUR_CHECKS_ARCHITECTURE_ACTUAL_PEER.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p.read_bytes()),'checks':N,'exit':out['exit_code'],'findings':fail},ensure_ascii=False));raise SystemExit(out['exit_code'])
