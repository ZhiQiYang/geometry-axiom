from pathlib import Path
import hashlib,json,re,subprocess,sys,time
P=Path('/tmp/geo337-F9-architecture-original-20261025');OUT=Path(__file__).parent
F='4f8a794f4167c3562eb182045102e86e9e37cca9';F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad';M='6e50aef65513b7b38f93228919272c6d40d6c196'
checks=[];bindings={};gitcommands=[]
def H(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 b=p.read_bytes();bindings[str(p)]=H(b);return b
def j(p):return json.loads(raw(p))
def check(v,msg):checks.append({'check':msg,'passed':bool(v)})
def git(args):
 argv=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args];t=time.time();r=subprocess.run(argv,cwd='/workspace/geometry-axiom',capture_output=True);n=len(gitcommands)+1;d=OUT/f'readonly-git/{n:04}';d.mkdir(parents=True);(d/'stdout.bin').write_bytes(r.stdout);(d/'stderr.bin').write_bytes(r.stderr);row={'command':argv,'cwd':'/workspace/geometry-axiom','exit_code':r.returncode,'started_epoch':t,'ended_epoch':time.time(),'stdout_sha256':H(r.stdout),'stderr_sha256':H(r.stderr),'directory':str(d)};gitcommands.append(row);check(r.returncode==0,'readonly Git success '+str(n));return r.stdout
request=j(P/'REQUEST.json');result=j(P/'RESULT.json');commands=j(P/'subcommands.json')
expected=[['python','-B','tests/architecture_contract.py','--root','.','--manifest','geometry-core/domain-decoupling/product-architecture.json'],['python','-B','tests/test_architecture_contract.py'],['python','-B','tests/test_product_architecture.py']]
check(request['source_sha']==result['source_sha']==F,'actual F9 request/result');check(request['argv']==expected,'three original argv exact');check(result['gate_exits']==[0,0,0],'three original gate exits')
check(len(commands)==7 and result['commands']==commands[2:5],'all seven original commands')
for c in commands:
 d=Path(c['directory']);check(j(d/'result.json')==c,'catalog original result '+d.name);q=j(d/'request.json')
 for k,v in q.items():
  if k not in ['actual_process_returncode','timeout_expired']:check(c[k]==v,'original request '+d.name+' '+k)
 for s in ['stdout','stderr']:
  b=raw(d/(s+'.bin'));check(H(b)==c[s+'_sha256'] and len(b)==c[s+'_bytes'],'full '+s+' '+d.name)
 check(H(raw(d/'stdin.bin'))==c['stdin_sha256'],'stdin '+d.name)
 check(c['actual_process_returncode']==0 and c['timeout_expired'] is False and c['ended_epoch']>=c['started_epoch'],'true original completed0 '+d.name)
 check(c['source_sha']==c['acceptance_sha']==F and c['cwd']=='/workspace/geometry-axiom','source/cwd '+d.name)
 check(c['environment']['PYTHONOPTIMIZE'] is None and c['environment']['PYTHONDONTWRITEBYTECODE']=='1' and c['environment']['LC_ALL']=='C.UTF-8','assertions/runtime environment '+d.name)
for i in [0,5]:check(commands[i]['command']==['git','rev-parse','HEAD'] and raw(Path(commands[i]['directory'])/'stdout.bin').decode().strip()==F,'original source HEAD '+str(i))
for i in [1,6]:check(commands[i]['command']==['git','status','--porcelain=v1','--untracked-files=all'] and raw(Path(commands[i]['directory'])/'stdout.bin')==b'','original source clean '+str(i))
check([c['command'] for c in commands[2:5]]==expected,'actual complete original gate argv')
scan=j(Path(commands[2]['directory'])/'stdout.bin');check(scan['ok'] is True and scan['diagnostics']==[],'actual scan no diagnostics')
counts={'sources':len(scan['sources']),'trustedSourcesNotParsed':len(scan['trustedSourcesNotParsed']),'edges':len(scan['edges']),'diagnostics':len(scan['diagnostics'])};check(counts=={'sources':334,'trustedSourcesNotParsed':6,'edges':798,'diagnostics':0},'actual scanner counts')
err1=raw(Path(commands[3]['directory'])/'stderr.bin').decode();err2=raw(Path(commands[4]['directory'])/'stderr.bin').decode()
check(re.search(r'\nRan 205 tests in [0-9.]+s\n\nOK\n\Z',err1) is not None,'architecture contract205 exact terminal OK')
names=re.findall(r'^(test_\S+) \([^\n]+\) \.\.\. ok$',err1,re.M);check(len(names)==205 and len(set(names))==205,'all205 unique named cases ok no skip')
check(re.fullmatch(r'\.{18}\n-+\nRan 18 tests in [0-9.]+s\n\nOK\n',err2) is not None,'product architecture18 dots exact OK no skip')
check(result['source_head_and_status_unchanged'] is True and result['architecture_regeneration_performed'] is False and result['prior_architecture_receipt_execution_sha']==M,'fresh F9 judges not relabel prior receipt')
check(git(['rev-parse',F+'^{commit}']).decode().strip()==F,'F9 Git resolvable')
delta=git(['diff','--no-renames','--name-only','-z',F8,F]);paths=[p.decode() for p in delta.split(b'\0') if p];non=[p for p in paths if not p.startswith('evidence/')];check(non==['tests/mutants_results.json'],'F8->F9 only ledger outside evidence')
base='geometry-core/domain-decoupling/';artifacts=[base+n for n in ['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json']]
a=git(['ls-tree','-z',F8,'--',*artifacts]);b=git(['ls-tree','-z',F,'--',*artifacts]);check(a==b and len([x for x in b.split(b'\0') if x])==4,'four artifacts identical F8/F9 blobs and modes')
receipt=json.loads(git(['show',F+':'+artifacts[-1]]));check(receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==M,'retained original receipt actual M binding')
check(receipt['scanSha256']==H(raw(Path(commands[2]['directory'])/'stdout.bin')),'new F9 scanner bytes equal originally accepted scan')
r={'schema':'F9-three-original-architecture-actual-peer/1','source_sha':F,'exit_code':int(any(not x['passed'] for x in checks)),'checks':len(checks),'failures':[x for x in checks if not x['passed']],'gate_exits':[0,0,0],'scan_counts':counts,'architecture_contract_tests':205,'product_architecture_tests':18,'source_before_after_clean':True,'prior_four_artifact_execution_sha':M,'architecture_artifacts_regenerated_or_relabelled':False,'F8_F9_nonevidence_delta':non,'original_commands':commands,'readonly_git_commands':gitcommands,'bindings':bindings,'limits':['僅核已完成原件與唯讀Git；沒有重跑裁判、重產四檔或修改來源。','原三條裁判各有完整c387終態0；root另回報session11004真終態0，本目錄未提供獨立EXEC_FINAL API物件，不冒稱核過該物件。','既有receipt仍綁M6e50，F9是本次三條原judge真實執行，不替native/browser或CI。']}
(OUT/'CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');(OUT/'REVIEW.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['exit_code','checks','failures','scan_counts']},ensure_ascii=False));sys.exit(r['exit_code'])
