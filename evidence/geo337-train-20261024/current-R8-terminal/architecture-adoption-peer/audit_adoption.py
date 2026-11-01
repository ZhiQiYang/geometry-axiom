from pathlib import Path
import datetime, hashlib, json, subprocess

R=Path('/workspace/geometry-axiom'); O=Path('/tmp/geo337-h-architecture-adoption-20261025')
P=Path('/tmp/geo337-h-adoption-resume-peer-20261025')
T='evidence/geo337-train-20261024/architecture-6e50-complete/'
M='6e50aef65513b7b38f93228919272c6d40d6c196'; F='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
def H(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
assert not (P/'REVIEW.json').exists()
result=J(O/'RESULT.json'); rows=J(O/'subcommands.json')
assert result['actual_execution_source']==M and result['artifact_commit']==F
assert result['published'] and result['push_exit']==0 and not result['ledger_regenerated']
assert git('show','-s','--format=%P',F).decode().strip()==M
changed=git('diff','--name-only',M,F,'--','.',':(exclude)evidence').decode().splitlines()
assert changed==sorted(['geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md','geometry-core/domain-decoupling/product-architecture-receipt.json'])
assert sorted(result['changed_non_evidence'])==changed
for r in rows:
    d=Path(r['directory']); assert d.parent==O/'subcommands' and J(d/'result.json')==r
    assert r['actual_process_returncode']==0 and not r['timeout_expired']
    assert r['source_sha']==r['acceptance_sha']==M
    req=J(d/'request.json')
    for key in ['command','cwd','source_sha','acceptance_sha','source_variant','environment','stdin_sha256']:
        assert req[key]==r[key]
    for name in ['stdout','stderr']:
        b=(d/(name+'.bin')).read_bytes(); assert H(b)==r[name+'_sha256'] and len(b)==r[name+'_bytes']
    assert H((d/'stdin.bin').read_bytes())==r['stdin_sha256']
push=[r for r in rows if 'push' in r['command']]
remote=[r for r in rows if 'ls-remote' in r['command']]
assert len(push)==len(remote)==1 and '--force' not in push[0]['command']
assert (Path(remote[0]['directory'])/'stdout.bin').read_text().split()[0]==F
inventory=json.loads(git('show',F+':'+T+'INVENTORY.json'))
assert inventory['actual_execution_source']==M and inventory['original_gate_exits']==[0,0,0]
assert len(inventory['files'])==result['original_files']==380
assert sum(x['bytes'] for x in inventory['files'])==result['original_bytes']==4630676
paths=[x['path'] for x in inventory['files']]
assert len(paths)==len(set(paths))
tree=git('ls-tree','-r','--name-only',F,'--',T).decode().splitlines()
assert sorted(tree)==sorted([T+x for x in paths]+[T+'INVENTORY.json'])
raw=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join(F+':'+T+x+'\n' for x in paths).encode(),capture_output=True,check=True).stdout
offset=0
for item in inventory['files']:
    end=raw.index(b'\n',offset);oid,kind,size=raw[offset:end].split(); size=int(size)
    b=raw[end+1:end+1+size]; assert raw[end+size+1:end+size+2]==b'\n';offset=end+size+2
    assert kind==b'blob' and size==item['bytes'] and H(b)==item['sha256']
    assert (R/T/item['path']).read_bytes()==b
assert offset==len(raw)
sources={'originals':Path('/tmp/geo337-h-architecture-four-20261025'),
    'original-outer':Path('/tmp/geo337-h-architecture-four-launch-20261025'),
    'preparation':Path('/tmp/geo337-h-architecture-preparation-20261025'),
    'integration':Path('/tmp/geo337-h-local-init-integration-20261025'),
    'peer':Path('/tmp/geo337-h-architecture-resume-peer-20261025')}
for item in inventory['files']:
    parts=Path(item['path']).parts
    if parts[0] in sources: assert H(sources[parts[0]].joinpath(*parts[1:]).read_bytes())==item['sha256']
    else: assert parts==('adopt_geo337_h_architecture_20261025.py',)
assert H((R/T/'adopt_geo337_h_architecture_20261025.py').read_bytes())=='d1416be00347ea15166bb4ee4b542ed341fb855d1b9772ff0bd660d6b367b387'
for name in ['product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json']:
    assert git('show',F+':geometry-core/domain-decoupling/'+name)==(sources['originals']/'new'/name).read_bytes()
receipt=json.loads(git('show',F+':geometry-core/domain-decoupling/product-architecture-receipt.json'))
assert receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==M
progress=git('show',F+':evidence/geo337-train-20261024/PROGRESS.md').decode()
assert progress.count('## 唯一 current-state')==1 and '### 歷史 R7 終態（F6df；不可移標 H 修正來源）' in progress
current=progress.split('## 唯一 current-state',1)[1].split('### 歷史 R7 終態',1)[0]
assert M in current and 'R8 原五 stage／36交錯樣本／4 profiles 尚未執行' in current
assert '目前不是READY-TO-MERGE' in current and '新M／採用commit的CI未讀' in current
report={'schema':'geo337-h-architecture-adoption-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'findings':[],
    'actual_architecture_source':M,'adoption_sha':F,'original_files':380,'original_bytes':4630676,'adoption_command_count':len(rows),
    'normal_push_verified_from_original':True,'changed_non_evidence':changed,'originals_match_git_blobs':True,'unique_current_state':True,
    'bindings':{str(p):H(p.read_bytes()) for p in [O/'RESULT.json',O/'subcommands.json',P/'STATIC_REVIEW.json',P/'audit_adoption.py']},
    'limits':['No network reads or product gate reruns.','Architecture actually executed at M; F8 adoption does not rewrite execution source.','R8/native/browser/ledger gates remain separate.']}
(P/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'exit_code':0,'adoption_sha':F,'review':str(P/'REVIEW.json'),'sha256':H((P/'REVIEW.json').read_bytes())}))
