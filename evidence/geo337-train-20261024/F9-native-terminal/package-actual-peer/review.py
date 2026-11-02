from pathlib import Path
import ast,datetime,hashlib,json,tarfile
P=Path('/tmp/geo337-F9-native-terminal-package-20261025');C=Path('/tmp/geo337-F9-native-terminal-collection-launch-20261025');OUT=Path(__file__).parent
F9='4f8a794f4167c3562eb182045102e86e9e37cca9';checks=[];fails=[];bindings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);b=p.read_bytes();bindings.append(dict(path=str(p),bytes=len(b),sha256=h(b)));return b
def j(p):return json.loads(read(p))
def ck(n,v):
 checks.append(n)
 if not v:fails.append(n)
pkg=j(P/'PACKAGE.json');inv=j(P/'RAW_INVENTORY.json');summary=j(P/'SUMMARY.json');budget=j(P/'BUDGET.json');outer=j(C/'RESULT.json');final=j('/tmp/geo337-F9-native-terminal-collection-EXEC_FINAL-20261025.json')
request_path=Path('/tmp/geo337-F9-native-terminal-REQUEST-root-lease-20261025.json');request=j(request_path)
ck('exact root request pin',h(request_path.read_bytes())=='988a9b8057278e013b4b74c423581efef56941745931df3e26e1955bbc07ac3c')
ck('root lease and source',request['root_source_cache_collection_lease'] is True and request['source_sha']==F9)
ck('true collector terminal0',final['exit_code']==outer['actual_exit']==pkg['collectionExit']==0 and 'session_id' not in final and outer['collector_only'] is True and outer['subject_rerun'] is False)
ck('collection is not native pass',pkg['originalNativeExit']==pkg['workflowExit']==pkg['outerExit']==pkg['originalExecFinalExit']==1 and pkg['CI35GateExit']==0 and pkg['originalFormalCandidate'] is False and pkg['formalAcceptanceRequiresActualPeer'] is True and summary['passed'] is False)
ck('formal identity source',pkg['sourceSHA']==summary['sourceSHA']==outer['source_sha']==F9 and pkg['originalTerminalBindingIssues']==summary['originalTerminalBindingIssues']==[])
ck('before after source preserved',summary['sourceBefore']==summary['sourceAfter'] and summary['sourceBefore']['head']==F9 and summary['sourceBefore']['status']=='')
ck('source not rewritten or rerun',summary['nativeCacheModifiedByCollector'] is False and summary['ROOTModifiedByCollector'] is False and summary['noFilesDeleted'] is True and summary['noSubjectRerun'] is True)
peer_path=Path(request['independent_static_review']['path']);peer=j(peer_path);ck('actual tool static peer',h(peer_path.read_bytes())==request['independent_static_review']['sha256'] and peer['collector_sha256']=='17352ac43c5dbd911143c5771e0280d61e58a487293d2b3ad38e8cb272001e54' and peer['guard_sha256']=='226015a2722a447ec3fceb5b18eaa5c918f7b0befd730cf2925fdf96aaef1834' and peer.get('exit_code',peer.get('exit'))==0)
commands=j(C/'subcommands.json');ck('one collector invocation',len(commands)==1 and commands[0]==outer['command'])
row=commands[0];d=Path(row['directory']);ck('original collector result',j(d/'result.json')==row and row['actual_process_returncode']==0 and row['timeout_expired'] is False and row['source_sha']==row['acceptance_sha']==F9)
rq=j(d/'request.json');ck('original request fields',rq['actual_process_returncode'] is None and all(row[k]==v for k,v in rq.items() if k!='actual_process_returncode'))
for stream in ['stdout','stderr']:
 b=read(d/(stream+'.bin'));ck('collector full '+stream,len(b)==row[stream+'_bytes'] and h(b)==row[stream+'_sha256'])
ck('collector original package stdout',json.loads((d/'stdout.bin').read_bytes())==pkg)
ck('inventory hash/count',h((P/'RAW_INVENTORY.json').read_bytes())==pkg['rawInventorySHA256'] and len(inv)+2==pkg['memberCount']==1374)
ck('exact selected logical bytes',sum(x['bytes'] for x in inv.values())==pkg['selectedOriginalLogicalBytes']==13895527)
arc=Path(pkg['archive']);raw=read(arc);ck('original archive hash/size',len(raw)==pkg['archiveBytes']==2605652 and h(raw)==pkg['archiveSHA256']=='42217b1827d010e8eac017b95799a24910835c202aa1e32a0137cfee32e95d5c')
content={};members=[];elf_members=[];link_members=[]
with tarfile.open(arc,'r:gz') as t:
 for m in t:
  ck('safe unique member:'+m.name,m.name not in members and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts);members.append(m.name)
  if m.name in ['RAW_INVENTORY.json','BUDGET.json']:
   ck('extra archive metadata:'+m.name,m.isfile() and t.extractfile(m).read()==(P/m.name).read_bytes());continue
  ck('member declared in inventory:'+m.name,m.name in inv)
  v=inv[m.name]
  if v['kind']=='symlink':ck('symlink exact:'+m.name,m.issym() and m.linkname==v['target']);continue
  ck('regular or explicit hardlink:'+m.name,m.isfile() or m.islnk())
  if m.islnk():link_members.append(dict(name=m.name,target=m.linkname))
  b=t.extractfile(m).read();ck('complete original bytes:'+m.name,len(b)==v['bytes'] and h(b)==v['sha256'])
  if b.startswith(b'\x7fELF'):elf_members.append(m.name)
  content[m.name]=b
ck('all inventory members present',set(members)==set(inv)|{'RAW_INVENTORY.json','BUDGET.json'})
ck('root request archived exact',content['collection/BOUND_REQUEST.json']==request_path.read_bytes())
ck('collector tool archived exact',h(content['tools/collect_terminal_native.py'])==peer['collector_sha256'] and h(content['tools/terminal_guard.py'])==peer['guard_sha256'])
for role,proof in request['terminal_files'].items():
 names={'exec_final':'original-exec-FINAL.json','outer':'outer/RESULT.json','native':'native/RECEIPT.json','workflow':'native/workflow/native/receipt.json'}
 ck('archived terminal exact:'+role,h(content[names[role]])==proof['sha256'])
workflow=json.loads(content['native/workflow/native/receipt.json']);native=json.loads(content['native/RECEIPT.json'])
ck('archived original native1 CI0',native['actual_exit']==workflow['exit_code']==1 and native['ci_35_minute_gate_exit']==0 and workflow['over_ci_timeout'] is False and workflow['ci_timeout_minutes']==35 and workflow['watchdog_factor']==3)
for name,v in workflow['files'].items():ck('every original workflow artifact:'+name,len(content['native/workflow/native/'+name])==v['bytes'] and h(content['native/workflow/native/'+name])==v['sha256'])
actual_peer=j('/tmp/geo337-F9-native-actual-peer-20261025/REVIEW.json');ck('original230 row peer retained',h(Path('/tmp/geo337-F9-native-actual-peer-20261025/REVIEW.json').read_bytes())=='0ff05176ec8cf72d715a7cf11982174b6e0f30ba26f288e874f1805c84409cd7' and actual_peer['exit_code']==0 and actual_peer['formal_native_exit']==1 and actual_peer['suite_rows']==230)
stdio=content['native/workflow/native/steps/01.stdout'].decode();rows=recs=[]
import re
for m in re.finditer(r'^\[(\d+)/230\] (\S+) …$',stdio,re.M):rows.append((int(m[1]),m[2]))
ck('all230 original progress archived',[i for i,n in rows]==list(range(1,231)) and len(set(n for i,n in rows))==230)
gdi=json.loads(content['native/workflow/native/run_all-logs/py_test_gdi_contract.json']);bad=json.loads(content['native/workflow/native/run_all-logs/py_test_geo314_commit_paths.json'])
ck('only approved skip exact archived',gdi['skipped']==1 and gdi['skip_items']==[actual_peer['allowed_skip']])
ck('unique assertion preserved',bad['failures']==[actual_peer['only_failure']] and b"geometry-core/kernel/source.c\\n" in content['native/workflow/native/run_all-logs/py_test_geo314_commit_paths.unittest.log'])
registry=content['registry-original-Git.stdout.bin'];tree=ast.parse(registry);reg=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REGISTRY' for t in n.targets));ordinary={ast.literal_eval(n.args[1]) for n in reg.elts if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Binary'}
ck('exact original F9 registry read',summary['originalRegistryGitRead']['exit']==0 and summary['originalRegistryGitRead']['argv'][-1]==F9+':tests/binaries.py' and h(registry)==summary['originalRegistryGitRead']['stdoutSHA256'] and h(content['registry-original-Git.stderr.bin'])==summary['originalRegistryGitRead']['stderrSHA256'])
ck('ordinary names exact',set(summary['ordinaryRegistryExeNames'])==ordinary)
for item in summary['excludedOrdinaryELFs']:
 p=Path(item['originalPath']);ck('only known top-level ordinary ELF excluded:'+p.name,p.parent==Path('/tmp/geometry-tests') and p.name in ordinary and 'new-runtime-cache/'+p.name not in inv)
 side=json.loads(content['new-runtime-cache/'+p.name+'.fingerprint.json']);ck('excluded ELF terminal sidecar identity:'+p.name,side['exe']==p.name and side['exe_size']==item['bytes'] and side['exe_sha256']==item['sha256'])
ck('no unknown ELF exclusion',len(summary['excludedOrdinaryELFs'])==6 and {Path(x['originalPath']).name for x in summary['excludedOrdinaryELFs']}==ordinary-{'gdi-contract'})
ck('historical old cache remains excluded only explicitly',summary['excludedOldCache']['exactPath']=='/tmp/geo337-F9-native-4f8a794f-20261025/preserved-global-geometry-tests' and summary['excludedOldCache']['payloadNotTraversed'] is True and not any('/preserved-global-geometry-tests/' in n for n in inv))
for n in summary['excludedOldCache']['originalManifestsIncluded']:ck('old cache manifest retained:'+n,n in content)
ck('all current copied native logs also archived',[n for n in content if n.startswith('native/workflow/native/run_all-logs/')]==[n for n in inv if n.startswith('native/workflow/native/run_all-logs/')])
logical=budget['selectedOriginalLogicalBytes'];exact_inv=len((P/'RAW_INVENTORY.json').read_bytes());tar=4096*(len(inv)+4)+10240;jsonupper=exact_inv*2+65536;n=logical+tar+jsonupper;deflate=(n+4095)//4096+(n+16383)//16384+(n+33554431)//33554432+1024
ck('exact conservative budget calculation',budget['exactInventoryBytes']==exact_inv and budget['tarAndFramingUpperBytes']==tar and budget['jsonMetadataUpperBytes']==jsonupper and budget['uncompressedTarAndMetadataUpperBytes']==n and budget['deflateGzipExpansionUpperBytes']==deflate)
ck('64MiB reserve true original admission',budget['minimumReserveBytes']==67108864 and budget['requiredBeforeArchiveBytes']==n+deflate+67108864 and budget['freeBeforeArchiveBytes']>=budget['requiredBeforeArchiveBytes'] and budget['admitted'] is True and budget['noCompressedSizeGuess'] is True)
limits=['本獨審只驗封存包、原 collector 全流及已獨審的完整230列證據；collection0不改 native1／CI35gate0。','未重跑 native、未修改 ROOT/cache。root已可接其他工作，故本審核沒有再掃描或重新hash目前可變的 /tmp/geometry-tests payload。','六普通ELF依原collector實際hash與已封入sidecar一致而排除；本peer核排除名單全部為原F9 REGISTRY頂層普通執行檔，沒有未知ELF排除，未第二次讀它們的payload。','原未知/反證ELF預設納入，tar每個已選member完整核hash；歷史 preserved cache 明確整份排除且原BEFORE/PRESERVED manifest保留，不冒新native產物。','原run_all內部未另存的管線／測試自行刪除scratch不能重建，沿原收據限制；沒有把另驗browser/owner整合當native通過。']
report=dict(schema='geo337-F9-native-terminal-package-actual-peer/1',source_sha=F9,exit_code=0 if not fails else 1,review_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=len(checks),failed_checks=fails,formal_native_exit=1,CI35MinuteGateExit=0,collection_exit=0,archive_sha256=pkg['archiveSHA256'],archive_bytes=pkg['archiveBytes'],inventory_sha256=pkg['rawInventorySHA256'],members=len(members),selected_original_logical_bytes=logical,ordinary_excluded_elfs=len(summary['excludedOrdinaryELFs']),included_elf_members=elf_members,tar_hardlink_members=link_members,unknown_elf_excluded=False,full230_peer_sha256='0ff05176ec8cf72d715a7cf11982174b6e0f30ba26f288e874f1805c84409cd7',limits=limits,bindings=bindings)
(OUT/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'REVIEW.md').write_text('# F9 native 終態封存包獨立核對\n\n'+f"{len(checks)} 項核對，{len(fails)} 項錯誤；1374 members／2,605,652B gzip。collection exit0，原 native exit1，CI35 gate0。\n\n"+'\n'.join('- '+x for x in limits)+'\n')
print(json.dumps({k:report[k] for k in ['exit_code','checks','failed_checks','members','formal_native_exit','CI35MinuteGateExit','collection_exit']},ensure_ascii=False));print('REVIEW_SHA256',h((OUT/'REVIEW.json').read_bytes()))
raise SystemExit(report['exit_code'])
