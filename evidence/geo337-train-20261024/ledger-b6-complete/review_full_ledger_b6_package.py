from pathlib import Path
import hashlib,json,tarfile
D=Path('/tmp/train337-adversarial');P=Path('/workspace/geo337-ledger-b6-terminal-publication');J=Path('/workspace/train337-ledger-b6e1e454-v5');C=Path('/workspace/train337-ledger-cache-b6e1e454');L=Path('/workspace/train337-ledger-b6e1e454-v5-launch');F='b6e1e45425f055cd825b259f46ef2c454f3ff13a';checks=0;fail=[]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def ck(n,v):
 global checks
 checks+=1
 if not v:fail.append(n)
idx=j(P/'INDEX.json');rows={x['path']:x for x in idx['members']};sources={x['source']:x for x in idx['members']};archive=P/idx['archive'];ledger=j(J/'mutants_results.json');root=j(J/'receipt.json')
ck('indexpin',h((P/'INDEX.json').read_bytes())=='3878f6f93d0db149b7ac78873fd0e343a9c30d2ec4e188e89bc28acd215aa5d4');ck('archive exactsizehash',archive.stat().st_size==7952104==idx['archive_bytes'] and h(archive.read_bytes())==idx['archive_sha256']=='e69d9d78e571fd798944e0c448baf768509b9b4287b80c66fd9ad1fc3355175b');ck('1239 unique members',len(rows)==len(idx['members'])==1239 and len(sources)==1239);seen=set()
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  ck('safe unique regular '+m.name,m.isfile() and m.name not in seen and not m.name.startswith('/') and '..' not in Path(m.name).parts);seen.add(m.name)
  x=rows[m.name];b=t.extractfile(m).read();ck('archive exact '+m.name,len(b)==m.size==x['bytes'] and h(b)==x['sha256']);p=Path(x['source']);ck('retained original '+m.name,p.is_file() and len(b)==p.stat().st_size and h(p.read_bytes())==x['sha256'])
ck('exact archive set',seen==set(rows));ck('all original bytes',sum(x['bytes'] for x in rows.values())==45345757)
for rootdir in [J,L]:
 actual={str(p) for p in rootdir.rglob('*') if p.is_file()};ck('entire original directory '+str(rootdir),actual <= set(sources))
required=set()
for folder in list(C.glob('M*'))+[C/'_baseline',C/'_bridge-baseline']:
 if folder.is_dir():required|={str(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ['.stdout','.stderr','.json']}
ck('every existing cache original stream andmetadata',required<=set(sources))
bridge=j(J/'BRIDGE_RAW_INVENTORY.json')
for x in bridge['files']:ck('all636 indexed bridge originals '+x['id']+x['phase']+x['stream'],str(Path(x['path'])) in sources and sources[x['path']]['sha256']==x['sha256'])
for id,v in ledger.items():
 e=v.get('execution',{})
 if e.get('schema')!='geometry-bridge-mutation-execution/1':continue
 for key,folder in [('baseline_identity',C/'_bridge-baseline'/F),('mutant_identity',C/id/'bridge-mutant'),('restored_identity',C/id/'bridge-restored')]:
  p=folder/'bridge.fingerprint.json';ident=e[key];ck(id+key+' exact retained sidecar',str(p) in sources and h(p.read_bytes())==ident['sidecar_sha256']==sources[str(p)]['sha256'] and j(p)==ident['sidecar'])
ck('b6 not futureL',idx['source_sha']==F and idx['actual_execution_head_counts']=={F:120});ck('subject actual0 complete123',idx['original_cli_exit']==idx['root_wrapper_exit']==idx['original_launcher_exit']==0 and idx['root_passed'] and idx['observation_complete'] and idx['observer_errors']==[] and idx['record_count']==idx['expected_record_count']==123 and idx['unrun_count']==0 and idx['missing_expected_files']==[])
ck('original phases preserved1/0/0/0',[x['actual_process_returncode'] for x in idx['original_phases']]==[1,0,0,0]);ck('original outcomes unchanged',idx['verdicts']==root['verdicts']=={'killed':114,'equivalent':5,'crashed':1,'retired':3})
launch=j(L/'receipt.json');ck('outerlaunch actual0 pinneddriver',launch['exit_code']==launch['command']['actual_process_returncode']==0 and launch['driver_sha256']=='6925b810d24e2902cb6b10de40e8694407e7918e3097e6547d9ec44c3ce054e1')
for label,c in [('launch',launch['command'])]:
 for s in ['stdin','stdout','stderr']:ck(label+' originalstream '+s,h((Path(c['directory'])/(s+'.bin')).read_bytes())==c[s+'_sha256'])
reaper=[json.loads(z) for z in (J/'full-ledger-reaper.jsonl').read_text().splitlines()];ck('reaper completed primary0',reaper[-1]['event']=='完成' and reaper[-1]['primary_returncode']==0 and any(z.get('primary') and z['returncode']==0 for z in reaper))
initial=D/'FULL_LEDGER_B6_INITIAL_REVIEWER_ASSUMPTIONS.json';script=D/'review_full_ledger_b6_initial_portable_subtest_assumptions.py.txt'
out={'schema':'b6-original-terminal-package-peer/1','source_sha':F,'checks':checks,'exit_code':int(bool(fail)),'findings':fail,'index_sha256':h((P/'INDEX.json').read_bytes()),'archive_sha256':idx['archive_sha256'],'member_count':len(rows),'original_bytes':sum(x['bytes'] for x in rows.values()),'actual_peer':{'path':str(D/'FULL_LEDGER_B6_TERMINAL_ACTUAL_PEER.json'),'sha256':h((D/'FULL_LEDGER_B6_TERMINAL_ACTUAL_PEER.json').read_bytes()),'checks':35756,'exit':0},'initial_reviewer_correction':{'report':str(initial),'sha256':h(initial.read_bytes()),'script':str(script),'script_sha256':h(script.read_bytes()),'reason':'初reviewer假設輸出必列unrun0、將原<work>替為<repo>、要求subTest完整名稱等method造成report1；固定原裁判實碼證明這三假設錯，僅更正reviewer並保初件，無subject重跑或放寬原oracle。'},'limits':['本包完整原JOB/launch/cache streams及metadata；ELF payload/seed/Git並未封進包，不宣稱binary archive。','原0為b6完整123生成CLI；生成前trackedcheck1仍保，下一L另須fullCLI及四phase0。','原core文字UTF8與bridge原bytes各按原schema保存；不宣稱core OS predecode pipes。','未抽取第二份原件、未跑任何subject；每member stream直接對原文件及index核。']};o=D/'FULL_LEDGER_B6_TERMINAL_PACKAGE_PEER.json';o.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(o),'sha256':h(o.read_bytes()),'checks':checks,'exit':out['exit_code'],'findings':fail},ensure_ascii=False));raise SystemExit(out['exit_code'])
