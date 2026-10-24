"""Extract only immutable r1 archive records. Never rerun a subject or read live logs."""
from pathlib import Path
import hashlib,json,re,subprocess,tarfile
P=Path('/workspace/train337-native-terminal-collection/completed');O=Path('/tmp/train337-native-r1-special-coverage-mapping')
L='7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
assert not O.exists();O.mkdir()
def h(raw):return hashlib.sha256(raw).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
pkg=json.loads((P/'PACKAGE.json').read_text());inv=json.loads((P/'RAW_INVENTORY.json').read_text());archive=P/'ORIGINAL_FULL_NATIVE_WORKFLOW_LOGS_AND_RUNTIME_SIDECARS.tar.gz'
assert pkg['sourceSHA']==L and pkg['originalNativeExit']==pkg['workflowExit']==pkg['outerExit']==1
assert h(archive.read_bytes())==pkg['archiveSHA256']=='a9a855cf58baec13059d2eede4f0ca4d6ca3c33380fea62aea176dc123402885'
groups={'314-six':{'test_geo314_stagger_commit':47,'test_geo314_commit_paths':11,'test_geo314_ordered_facts':14,'test_geo261_wood_grid_application':23,'test_geo261_native_grid_product':5,'test_grid_inspector_contract':3},'reading-a-native-oracle':{'test_geo318_reading_a_native':7,'test_geo318_reading_a_oracle':14},'323-fixed-three':{'test_geo261_load_residual':13,'test_geo261_host_facts_authority':22,'test_geo261_contact_sources':15}}
checks=[]
def check(n,b):checks.append({'name':n,'passed':bool(b)})
with tarfile.open(archive,'r:gz') as tf:
 def read(name):
  raw=tf.extractfile(name).read();assert h(raw)==inv[name]['sha256'] and len(raw)==inv[name]['bytes'];return raw
 def locator(name,lines=None):
  return {'archive':str(archive),'archiveSHA256':pkg['archiveSHA256'],'member':name,'memberSHA256':inv[name]['sha256'],'originalRecordedPath':inv[name]['originalPath'],**({'lines':lines} if lines else {})}
 stdout_name='native/workflow/native/steps/01.stdout';stdout=read(stdout_name).decode();ss=stdout.splitlines()
 stdout_locator=locator(stdout_name)
 node_name='native/workflow/native/run_all-logs/node_tests-js.log';node=read(node_name).decode();ns=node.splitlines()
 outgroups={}
 for group,modules in groups.items():
  entries=[]
  for module,count in modules.items():
   suite='py:'+module;stem='native/workflow/native/run_all-logs/py_'+module
   data=json.loads(read(stem+'.json'));ut=read(stem+'.unittest.log').decode();mainlog=read(stem+'.log')
   final=[(n,l) for n,l in enumerate(ss,1) if re.match(r'^'+re.escape(suite)+r'\s+\d',l)]
   started=[(n,l) for n,l in enumerate(ss,1) if re.match(r'^\[\d+/230\] '+re.escape(suite)+r' ',l)]
   check(module+'_complete_final_row',len(final)==len(started)==1)
   match=re.match(r'^'+re.escape(suite)+r'\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',final[0][1]);assert match
   values=list(map(int,match.groups()[:4]));check(module+'_row_exact_pass_no_skip',values==[count,count,0,0])
   check(module+'_original_json_exact',data['file']=='tests/'+module+'.py' and data['total']==data['run']==data['passed']==count and data['failed']==data['skipped']==data['extra_errors']==0 and data['import_error'] is None and data['failures']==[])
   check(module+'_original_full_unittest_log',re.search(r'Ran '+str(count)+r' tests? in ',ut) is not None and re.search(r'(?m)^OK\s*$',ut) is not None)
   # Keep direct exit fields honest. The original aggregate does not persist each
   # unittest child's numeric OS return code. Its original final row plus the pinned
   # nonzero-exit=>failure runner contract supports the value, not a new receipt.
   entries.append({'module':module,'suite':suite,'total':count,'passed':count,'failed':0,'skipped':0,'registeredFullModule':'tests/'+module+'.py','originalRow':final[0][1],'originalRowLine':final[0][0],'originalStartLine':started[0][0],'unittestSuccessful':True,'directRecordedChildOSExit':None,'childOSExitSupportedByOriginalJudgeContract':0,'exitEvidenceBasis':'Original complete passing run_all row and full unittest OK; original run_suite marks a nonzero child return as failure. Per-suite OS returncode was not separately persisted.','json':locator(stem+'.json'),'unittestLog':locator(stem+'.unittest.log'),'exposedLog':locator(stem+'.log'),'finalRow':locator(stdout_name,[final[0][0]])})
  outgroups[group]={'modules':entries,'totalOriginalMethods':sum(modules.values()),'standaloneRerun':False}
 node_lines=[(n,l) for n,l in enumerate(ns,1) if re.match(r'^\s*✔ GEO263',l)]
 check('314_Node_exact13_pass_events',len(node_lines)==13)
 check('314_Node_parent_and12_children',sum('native inspector contract' in l for _,l in node_lines)==1 and sum('GEO263_RENAME_PRESERVES_STAGGER ' in l for _,l in node_lines)==8)
 check('Node_container_original_737_733_4_0',all(v in node for v in ('ℹ tests 737','ℹ pass 733','ℹ fail 4','ℹ skipped 0')))
 check('original_Node_errors_all_ENOENT',node.count("code: 'ENOENT'")==4)
 node_final=next((n,l) for n,l in enumerate(ss,1) if re.match(r'^node:tests-js\s+737\s+733\s+4\s+0\s+',l))
 node_row={'file':'tests/test_grid_inspector_stagger.cjs','checksObservedPassing':13,'parentChecks':1,'nestedChecks':12,'actualPassEvents':[{'line':n,'text':l} for n,l in node_lines],'events':locator(node_name,[n for n,_ in node_lines]),'containingNodeSuite':{'name':'node:tests-js','total':737,'passed':733,'failed':4,'skipped':0,'originalRow':node_final[1],'finalRow':locator(stdout_name,[node_final[0]]),'directRecordedProcessOSExit':None,'status':'FAILED; four fixture ENOENT elsewhere. No standalone Node13 process exit0 is invented.'},'separateNode13ProcessExit':None,'notAdditionalTests':True,'source':'The registered Node aggregate argv includes this exact file, no methods/test selectors used.'}
 total_line=next((n,l) for n,l in enumerate(ss,1) if l.startswith('合計(已執行、有計數者)'))
 check('native_original_aggregate_retained',re.search(r'5309\s+5304\s+4\s+1',total_line[1]) is not None)

# Only immutable Git blobs; no live ROOT source or original global log reads.
src={}
for name in ('tests/run_all.py','tests/_unittest_runner.py','tests/test_grid_inspector_stagger.cjs'):
 p=subprocess.run(['git','-C','/workspace/geometry-axiom','show',L+':'+name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True);src[name]=p.stdout
 (O/('L_'+Path(name).name+'.txt')).write_bytes(p.stdout)
check('run_all_nonzero_exit_not_green_contract',b'if code not in (0, None) and not row.failed' in src['tests/run_all.py'] and b'row.failed = max(row.failed, 1)' in src['tests/run_all.py'])
check('original_full_module_no_method_filter',b'[*suite.cmd, \'--json-out\'' in src['tests/run_all.py'] and b"[py, str(RUNNER), str(f)]" in src['tests/run_all.py'])
check('exact_Node_module_registered',b"'tests/test_grid_inspector_stagger.cjs'" in src['tests/run_all.py'])
report={'schema':'L-native-r1-specific-original-module-and-Node-subtest-coverage/1','L':L,'archiveSHA256':pkg['archiveSHA256'],'archive':str(archive),'groups':outgroups,'314Node13':node_row,'aggregateNative':{'originalNativeExit':1,'workflowExit':1,'outerExit':1,'CI35GateExit':0,'originalCountedTotal':5309,'passed':5304,'failed':4,'skipped':1,'originalTotalRow':total_line[1],'row':{**stdout_locator,'lines':[total_line[0]]}},'checks':len(checks),'exitCode':0 if all(c['passed'] for c in checks) else 1,'findings':[c['name'] for c in checks if not c['passed']],'details':checks,'sourcePins':{k:h(v) for k,v in src.items()},'coverageRequestSource':'/tmp/train337-final-L-coverage/COVERAGE.txt','limits':['Subset successes are original r1 coverage, not a complete native pass; native/workflow/outer remain1.','Node13 are original passing events inside failed737 Node aggregate; no separate process exit0.','Original Python final rows and unittest reports/logs show complete success; separate raw per-suite OS returncode fields were not retained, so direct exit=null and source-contract-supported exit0 is labeled explicitly.','These slices do not replace required-eight676/PF3/complete quick/precision RC proof or any separate performance/ABC gate.','No subject, compiler, Node, browser, live source/index/cache or current run_all-log read.']}
dump(O/'MAPPING.json',report)
lines=['# L native r1 指定切片原件對照','','此表只描述已封存 r1。完整 native／workflow／outer 仍 **1／1／1**；四個Node ENOENT未改判。','', '| 切片 | 原方法／事件 | 原結果 | 退出碼界線 |','|---|---:|---|---|']
for g in ('314-six','reading-a-native-oracle','323-fixed-three'):
 lines.append('| '+g+' | '+str(outgroups[g]['totalOriginalMethods'])+' | 各完整原module皆pass，0fail／0skip | 原JSON/完整row支持child0；未另存per-child OS碼 |')
lines+=['| #314 Node inspector | 13（parent1＋nested12） | 13個原✔事件 | enclosing Node737仍733pass/4fail，無獨立Node13 exit |','','每module原行號、JSON、unittest完整log與archive member/hash都在 MAPPING.json。原123帳本、各專項與整體native的結果不因此改標。']
(O/'MAPPING.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'checks':report['checks'],'exitCode':report['exitCode'],'findings':report['findings'],'path':str(O/'MAPPING.json')},ensure_ascii=False));raise SystemExit(report['exitCode'])
