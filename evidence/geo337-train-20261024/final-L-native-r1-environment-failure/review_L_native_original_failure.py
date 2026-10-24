from pathlib import Path
import ast,hashlib,json,re,subprocess,tarfile
BASE=Path('/workspace/train337-native-terminal-collection/completed');L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db';OUT=Path('/tmp/train337-adversarial');checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
def jread(p):return json.loads(Path(p).read_text())
summary=jread(BASE/'SUMMARY.json');pkg=jread(BASE/'PACKAGE.json');inv=jread(BASE/'RAW_INVENTORY.json');tar=tarfile.open(pkg['archive']);members=tar.getmembers();mapping={m.name:m for m in members}
def raw(name):return tar.extractfile(mapping[name]).read()
def js(name):return json.loads(raw(name))
ck('archive exact original pin',sha(Path(pkg['archive']).read_bytes())=='a9a855cf58baec13059d2eede4f0ca4d6ca3c33380fea62aea176dc123402885')
ck('archive bytes',Path(pkg['archive']).stat().st_size==2229053==pkg['archiveBytes'])
ck('inventory exact hash',sha((BASE/'RAW_INVENTORY.json').read_bytes())==pkg['rawInventorySHA256']=='51bcd3fff433ff437787e6bf85832389757315ec5e264e5a2a231d0108dd7e00')
ck('1366 unique members and bounded inventory extras',len(members)==len(mapping)==1366==pkg['memberCount'] and set(mapping)==set(inv)|{'RAW_INVENTORY.json','BUDGET.json'})
ck('selected original total11241774',sum(v['bytes']for v in inv.values())==11241774==pkg['selectedOriginalLogicalBytes'])
for name,m in mapping.items():
 ck('safe regular archive '+name,m.isfile() and not name.startswith('/') and '..'not in Path(name).parts)
 body=raw(name)
 if name in inv:
  r=inv[name];ck('member bytes/hash '+name,len(body)==r['bytes'] and sha(body)==r['sha256'])
  # The globally shared cache was released after its terminal snapshot. Do not relabel later files as historical output.
  if not name.startswith('new-runtime-cache/'):
   p=Path(r['originalPath']);ck('immutable original matches '+name,p.is_file()and p.read_bytes()==body)
 else:ck('inventory budget original '+name,body==(BASE/name).read_bytes())
path_to_member={v['originalPath']:k for k,v in inv.items()}
for name in ['outer/subcommands.json','native/subcommands.json']:
 rows=js(name);ck('original commands present '+name,bool(rows))
 for num,row in enumerate(rows,1):
  directory=row['directory'];prefix=path_to_member[directory+'/result.json'].removesuffix('/result.json')
  ck('c387 exact recorded row '+prefix,js(prefix+'/result.json')==row)
  ck('c387 sourceL '+prefix,row['acceptance_sha']==L and row['source_sha']==L and row['ended_epoch']>=row['started_epoch'])
  for stream in ['stdout','stderr']:
   b=raw(prefix+'/'+stream+'.bin');ck('c387 full '+stream+' '+prefix,len(b)==row[stream+'_bytes'] and sha(b)==row[stream+'_sha256'])
  ck('c387 stdin '+prefix,sha(raw(prefix+'/stdin.bin'))==row['stdin_sha256'])
  ck('c387 no timeout '+prefix,row['timeout_expired'] is False)
  ck('c387 original exit expected '+prefix,row['actual_process_returncode']==(1 if (name.startswith('outer/')or num==6)else 0))
native=js('native/RECEIPT.json');w=js('native/workflow/native/receipt.json');outer=js('outer/receipt.json')
ck('natural L before/after clean immutable original snapshot',native['source_sha']==L and native['source_before']==native['source_after'] and native['source_before']['head']==L and native['source_before']['status']=='')
ck('original workflow/driver/outer failure retained',native['actual_exit']==native['original_workflow_exit']==native['reaper_primary_exit']==w['exit_code']==summary['outerExit']==summary['originalDriverExit']==1 and native['passed']is False and not native['metadata_errors'])
ck('CI original35 not exceeded',w['ci_timeout_minutes']==35 and w['seconds']==1873.2407616440032 and w['seconds']<2100 and w['over_ci_timeout']is False and native['ci_35_minute_gate_exit']==0)
ck('original full CLI no selectors',native['original_native_cli']=='ulimit -s 16384; python3 tests/run_all.py --build'and native['all_suites_selected'] is True and native['selectors']==[])
step=w['steps'][1];ck('original unmodified shell script',step['original_run']==step['executed_run'] and raw('native/workflow/native/steps/01.executed.sh').decode()==step['executed_run'])
ck('original native primary1 no watchdog',step['result']['actual_process_returncode']==1 and not step['result']['watchdog_expired'])
ck('workflow GitL exact raw',sha(raw('native/workflow/native/workflow.yml.txt'))==w['workflow_sha256']==native['original_workflow_sha256'])
ck('original workflowdriver pin',sha(raw('native/workflow/native/driver.py.txt'))==w['driver_sha256']=='6a3e3c327687ee6fdafb1044e4c4036f4d2f881a75498af97bd1e1af861e1310')
events=[json.loads(x)for x in raw('native/reaper.jsonl').splitlines()];terms=[x for x in events if x.get('event')=='完成'];ck('original reaper terminal1',len(terms)==1 and terms[0]['primary_returncode']==1 and events[-1]==terms[0])
gitraw={}
for relative in ['tests/run_all.expected.json','tests/run_all.py','.github/workflows/integration-tests.yml']:
 argv=['git','--git-dir=/workspace/geometry-axiom/.git','show',L+':'+relative];c=subprocess.run(argv,capture_output=True);ck('fixed Git object read '+relative,c.returncode==0);gitraw[relative]=c.stdout
ck('workflow original Git bytes',gitraw['.github/workflows/integration-tests.yml']==raw('native/workflow/native/workflow.yml.txt'))
expected=json.loads(gitraw['tests/run_all.expected.json'])['suites'];stdout=raw('native/workflow/native/steps/01.stdout').decode();parsed={}
for line in stdout.splitlines():
 m=re.match(r'^(\S+:\S+)\s+(\d+|-)\s+(\d+|ok|FAIL|-)\s+(\d+|-)\s+(\d+|-)\s+([0-9.]+)(?:\s+(.*))?$',line)
 if m:parsed[m[1]]=m.groups()[1:]
ck('all230 original registered names exactly once',len(parsed)==len(expected)==230 and set(parsed)==set(expected))
totals=[0]*4;reds=[];skips=[]
for name,e in expected.items():
 row=parsed[name];count,pas,fail,skip,secs,note=row
 if e['mode']=='count':
  nums=list(map(int,(count,pas,fail,skip)));ck('exact registered count '+name,nums[0]==e['count'] and nums[0]==sum(nums[1:]));totals=[a+b for a,b in zip(totals,nums)]
  if nums[2]:reds.append(name)
  if nums[3]:skips.append(name)
  if name.startswith('py:'):
   r=js('native/workflow/native/run_all-logs/py_'+name.split(':',1)[1]+'.json');ck('original unittest JSON counts '+name,[r['total'],r['passed'],r['failed'],r['skipped']]==nums and not r.get('import_error')and not r.get('extra_errors'))
 else:ck('original exit-only row green '+name,((count,pas,fail,skip)==('-','-','-','-') and 'mutation inventory freshness (not test assertions); exit 0' in note) if name=='mutation:check' else (count,pas,fail,skip)==('-','ok','-','-'))
ck('only node-js original four fails',reds==['node:tests-js'] and parsed['node:tests-js'][:4]==('737','733','4','0'))
ck('complete totals5309/5304/4/1',totals==[5309,5304,4,1]and re.search(r'合計\(已執行、有計數者\)\s+5309\s+5304\s+4\s+1',stdout))
ck('sole original GDI platform skip',skips==['py:test_gdi_contract'])
a=ast.parse(gitraw['tests/run_all.py']);allow=ast.literal_eval(next(n.value for n in a.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='ALLOWED_SKIPS'for t in n.targets)))
gdi=js('native/workflow/native/run_all-logs/py_test_gdi_contract.json');item=gdi['skip_items'][0];ck('skip matches exact original allowed name/reason/platform',len(gdi['skip_items'])==1 and any(x['suite']=='py:test_gdi_contract'and x['test']==item['test']and x['reason']==item['reason']and 'posix'in x['platforms']for x in allow))
node=raw('native/workflow/native/run_all-logs/node_tests-js.log').decode();tail=node.split('✖ failing tests:')[-1];failureblocks=re.split(r'\ntest at ',tail)[1:];ck('four raw node failures all ENOENT no assertion/crash',len(failureblocks)==4 and all("code: 'ENOENT'"in x and 'Error: ENOENT: no such file or directory' in x and 'AssertionError'not in x for x in failureblocks))
missing_dir=Path('/workspace/train337-native-terminal-collection/missing-fixture-environment-before-repair');before=jread(missing_dir/'BEFORE_CLOSURE.json');paths=[r['path']for r in before['rows']];seen=re.findall(r"path: '/tmp/train337-323-f64d638f-source/([^']+)'",tail)
ck('four failures only these three exact missing original fixtures',set(seen)==set(paths)and len(seen)==4 and len(paths)==3)
ck('pre-repair absence explicitly recorded',before['sourceSHA']==L and before['sourceChanged']is False and before['fixtureMaterialized']is False and all(r['existsBeforeRepair']is False and r['isSymlinkBeforeRepair']is False for r in before['rows']))
for row in before['rows']:
 q=row['expectedOriginalLInputRead'];c=subprocess.run(q['argv'],capture_output=True);ck('same L original fixture exists in Git '+row['path'],c.returncode==0==q['exit'] and c.stdout.decode()==q['stdout'] and sha(c.stdout)==q['stdoutSHA256'] and sha(c.stderr)==q['stderrSHA256'])
for e in summary['excludedOrdinaryELFs']:
 name=Path(e['originalPath']).name;r=js('new-runtime-cache/'+name+'.fingerprint.json');ck('ordinary excluded ELF has full original sidecar '+name,r['exe_sha256']==e['sha256']and r['exe_size']==e['bytes']and r['exe']==name and (r['name']==name or name=='engineering-json-test' and r['name']=='engjson'))
ck('exact historical cache prune only',summary['excludedOldCache']['exactPath']=='/tmp/train337-full-native-L-7af8c5d8/preserved-global-geometry-tests' and not any(k.startswith('native/preserved-global-geometry-tests/')for k in inv))
ck('original native mutation check included green','mutation:check'in parsed and parsed['mutation:check'][1]=='-' and 'exit 0' in parsed['mutation:check'][5])
r={'schema':'original-native-failure-actual-package-peer/1','source_sha':L,'check_count':len(checks),'checks':checks,'findings':[x['check']for x in checks if not x['passed']],'exit_code':int(any(not x['passed']for x in checks)),'original_subject_exit':1,'reviewer_initial_correction':'Initial checker incorrectly demanded ok for mutation inventory (original deliberately prints dashes and explicit exit0), and internal registry name engineering-json-test instead of original engjson. Original initial report/script retained; only checker interpretation corrected.','original_full_rows':230,'original_counts':{'total':5309,'passed':5304,'failed':4,'skipped':1},'failure_classification':'ENVIRONMENT: four original node tests fail while opening three absent same-L tracked fixtures; original native/workflow/reaper/outer exit1 remains unchanged.','allowed_skip':item,'missing_fixtures':paths,'package':{'sha256':pkg['archiveSHA256'],'members':1366,'raw_bytes':11241774},'limits':['No subject rerun and no correction to original receipts. Later same-L materialization/rerun is separate evidence.','Global cache released after collection; package snapshots, not later active-cache contents, represent original run.','Only original exposed pipes/build logs and sidecars retained; no claim for hidden compiler/test OS pipes or cleaned NativeBuild sources/ELFs.','Only six registry ordinary ELF bodies excluded and represented by original hashes/sidecars; old cache exact path pruned with preservation manifests retained.','Git HEAD/index clean is not a claim all tracked fixtures were physically present; absent inputs are explicitly proven.']}
p=OUT/'FINAL_L_NATIVE_ORIGINAL_FAILURE_ACTUAL_PACKAGE_PEER.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':str(p),'sha256':sha(p.read_bytes()),'checks':len(checks),'exit_code':r['exit_code'],'findings':r['findings']}))
