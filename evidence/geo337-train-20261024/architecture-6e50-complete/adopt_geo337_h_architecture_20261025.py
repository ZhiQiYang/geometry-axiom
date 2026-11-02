from pathlib import Path
import hashlib, importlib.util, json, os, shutil

R=Path('/workspace/geometry-axiom')
I=Path('/tmp/geo337-h-architecture-four-20261025')
O=Path('/tmp/geo337-h-architecture-adoption-20261025')
T=Path('evidence/geo337-train-20261024/architecture-6e50-complete')
ART=Path('geometry-core/domain-decoupling')
M='6e50aef65513b7b38f93228919272c6d40d6c196'
BR='codex/train-337-continue-20261024'
PEER=Path('/tmp/geo337-h-architecture-resume-peer-20261025/REVIEW.json')
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(PEER)=='2eb380806aa1e60e06152fd156819b6b1107c44389b3a83f8d51d5249add6560'
peer=json.loads(PEER.read_text());assert peer['exit_code']==0
for name,pin in peer['bindings'].items():assert H(name)==pin
s=json.loads((I/'RESULT.json').read_text())
assert s['sourceSHA']==M and s['sourceBeforeAfterClean']
assert s['originalGateExits']==[0,0,0] and s['newGuardProofExits']==[0,1,0]
assert s['existingGuardCasesRetested']==9 and s['manifestDelta']=='unchanged-937-to-937'
assert [x['path'] for x in s['changedPriorReceiptInputs']]==['geometry-core/references.inc']
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert H(CAP)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('capture',CAP); cap=importlib.util.module_from_spec(spec); spec.loader.exec_module(cap)
O.mkdir(); env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None)
rec=cap.Recorder(O,env,M)
def git(*args):
    _, out, _=rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=R,
                     check=True,timeout=None,source_variant='adopt original H architecture receipts')
    return out.decode().strip()
assert git('rev-parse','HEAD')==M and git('branch','--show-current')==BR
assert not git('status','--porcelain=v1') and shutil.disk_usage(R).free>24*1024*1024
changed=[]
for name,pin in s['outputs'].items():
    source=I/'new'/name; target=R/ART/name
    assert H(source)==pin['rawSha256']
    if target.read_bytes()!=source.read_bytes():
        assert target.stat().st_nlink==1
        target.write_bytes(source.read_bytes());changed.append(str(ART/name))
assert sorted(changed)==sorted([str(ART/'PRODUCT-ARCHITECTURE.md'),str(ART/'product-architecture-receipt.json')])
target=R/T;assert not target.exists()
for label,source in [('originals',I),('original-outer',Path('/tmp/geo337-h-architecture-four-launch-20261025')),
    ('preparation',Path('/tmp/geo337-h-architecture-preparation-20261025')),('peer',PEER.parent),
    ('integration',Path('/tmp/geo337-h-local-init-integration-20261025'))]:
    shutil.copytree(source,target/label)
shutil.copyfile(__file__,target/Path(__file__).name)
inventory=[]
for p in sorted(target.rglob('*')):
    assert not p.is_symlink()
    if p.is_file():inventory.append({'path':str(p.relative_to(target)),'bytes':p.stat().st_size,'sha256':H(p)})
cap.dump(target/'INVENTORY.json',{'actual_execution_source':M,'files':inventory,
    'original_gate_exits':[0,0,0],'guard_phase_exits':[0,1,0],'changed_artifact_paths':changed,
    'ledger_regenerated':False})
p=R/'evidence/geo337-train-20261024/PROGRESS.md';assert p.stat().st_nlink==1
old=p.read_text();start=old.index('## 唯一 current-state');end=old.index('### 歷史 K 合流與架構採用',start)
historical=old[start:end].replace('## 唯一 current-state（2026-10-24；F6df 的 R7 已收齊終態）',
    '### 歷史 R7 終態（F6df；不可移標 H 修正來源）',1)
current='''## 唯一 current-state（2026-10-25；H 初始化修正已合流，準備 R8）

產品／測試合流來源 M=`6e50aef65513b7b38f93228919272c6d40d6c196`，子來源 S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`。四個產品／測試葉與公開 S 相同；本提交採用 M 的架構 report／receipt。採用 commit 將固定為 R8 的 F8，再獨立 checkout 執行；M 與 S 的實跑不得改標 F8。

H 修正把原每次 reference_rebuild 都做的 127,584-byte 區域清零移入 fallback，持續快取路徑不再做這段無用工作。S 原 LoadResidual 14/14、零 skip、exit0；舊13方法未改。固定／撤回／恢復 actual memset calls=0/2/0、bytes=0/255168/0，work exit0/1/0；各 phase 的 persistent、fallback、allocation-failure、ordered-graph 語意均0。精確撤回 assertion 是 persistent-reference-local-zero-work。這是 O0 focused 反證，尚不代表 O2/N16 wall 通過；子分支原件正在另行出版，不能把未出版件稱為已入庫。

M 架構三原 judge exit0/0/0，generic205／product18、零 skip；604 inputs、798 edges／0 diagnostics，唯一 input delta 是 references.inc。九既有 guard 各0/1/0、neutral2綠；937／55政策與 scan bytes 不變。完整原件、51原命令、合流原流及獨審在 architecture-6e50-complete/。本提交只採用 report／receipt 兩個實際改動的衍生檔，未改公理、裁判或架構政策。

R8 原五 stage／36交錯樣本／4 profiles 尚未執行；全123帳本、完整native、六browser、P52、Q38(44)、§7、P189、required-eight/PF3、memo、readers／RC／#314／Reading A在新來源均UNRUN。只允許原Linux Windows-GDI skip。原R7 N16/base=1.05190582882169>1與三個stdout exact差保留為歷史紅；N64/main=1.2292230778583162是舊F7綠，不移標新F8。

Q-323-ABC／Q-P189-EXACT 的診斷版本界線尚無裁決，維持原exact紅，不刪I22診斷、不正規化比較。required CI既有付款失敗或支出上限分類仍在；新M／採用commit的CI未讀，沒有正式替代接受紀錄，不變更付費或安全設定。

下一步：固定採用SHA，以原工具和門檻跑R8；性能與完整canvas獨占，其他重測最多兩個。**目前不是READY-TO-MERGE。**

'''
p.write_text(old[:start]+current+historical+old[end:])
git('add','-f','--sparse',*changed,str(T),'evidence/geo337-train-20261024/PROGRESS.md')
assert all(x in changed+['evidence/geo337-train-20261024/PROGRESS.md'] or x.startswith(str(T)+'/') for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',*changed,'evidence/geo337-train-20261024/PROGRESS.md',str(T/'INVENTORY.json'))
git('commit','-m','docs: refresh architecture evidence for conditional reference initialization')
F=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','--exit-code','origin','refs/heads/'+BR).split()[0]==F
assert not git('status','--porcelain=v1')
assert sorted(git('diff','--name-only',M,F,'--','.',':(exclude)evidence').splitlines())==sorted(changed)
cap.dump(O/'RESULT.json',{'actual_execution_source':M,'artifact_commit':F,'published':True,'push_exit':0,
    'original_gate_exits':[0,0,0],'changed_non_evidence':changed,'ledger_regenerated':False,
    'original_files':len(inventory),'original_bytes':sum(x['bytes'] for x in inventory)})
print((O/'RESULT.json').read_text())
