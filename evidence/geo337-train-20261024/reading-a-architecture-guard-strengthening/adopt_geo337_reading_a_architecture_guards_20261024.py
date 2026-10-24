from pathlib import Path
import copy,hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-architecture-guard-adoption-20261024');BEFORE='48f6e79d1192c8bcdb37cee631795bf147e2445b';BR='codex/train-337-continue-20261024';B=Path('evidence/geo337-train-20261024');T=B/'reading-a-architecture-guard-strengthening';MP=Path('geometry-core/domain-decoupling/product-architecture.json')
CANDIDATE=Path('/workspace/geo337-U-architecture-policy-proof-20261024/candidate-manifest.json');assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()=='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975'
PEER=Path('/workspace/train337-canvas-peer-resume/U_ARCHITECTURE_POLICY_PROPOSAL_AND_ACTUAL_PEER.json');assert hashlib.sha256(PEER.read_bytes()).hexdigest()=='655510bee8dfdbe48a2d272359ed6ed3f981970dd6eda55d134e26f331403cc4'
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(p.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,BEFORE)
def git(*args):
 row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='adopt independently reviewed additive Reading A architecture guards');return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BR and not git('status','--porcelain=v1')
a=json.loads((R/MP).read_bytes());b=json.loads(CANDIDATE.read_bytes());added=sorted(set(b['policy']['forbiddenIdentifiers'])-set(a['policy']['forbiddenIdentifiers']));assert len(added)==9 and set(a['policy']['forbiddenIdentifiers'])<=set(b['policy']['forbiddenIdentifiers'])
check=copy.deepcopy(b);check['policy']['forbiddenIdentifiers']=a['policy']['forbiddenIdentifiers'];assert check==a
(R/MP).write_bytes(CANDIDATE.read_bytes());inv=[]
for label,src in [('original-U-proposal',Path('/workspace/geo337-U-architecture-policy-preparation-20261024')),('original-U-proof',Path('/workspace/geo337-U-architecture-policy-proof-20261024')),('monotonic-source-merge',Path('/workspace/geo337-monotonic-integration-20261024'))]:
 target=R/T/label;assert not target.exists();shutil.copytree(src,target)
 for f in sorted(src.rglob('*')):
  if f.is_file():
   assert not f.is_symlink();d=target/f.relative_to(src);raw=f.read_bytes();assert d.read_bytes()==raw;inv.append({'path':str(d.relative_to(R/T)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
for src in [PEER,Path('/workspace/train337-canvas-peer-resume/review_U_architecture_policy_actual.py'),Path(__file__)]:
 d=R/T/src.name;shutil.copyfile(src,d);raw=src.read_bytes();inv.append({'path':d.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
c.dump(R/T/'INVENTORY.json',{'policy_proof_actual_product_source':'ca7838e0f4950452b9befcf40899d606db9b81fa','policy_proof_physical_head':'4d0ef8dee14873256efae1ee646c01d8dcfe947f','monotonic_merge_source':BEFORE,'child_test_source':'aa16e73d6e1f2965e0a911581e2a545aaaf66870','added_identifiers':added,'source_receipt_not_relabelled':True,'files':inv})
p=R/B/'PROGRESS.md';text=p.read_text();heading='## 唯一 current-state（2026-10-24；開始合流下一個來源）';assert text.count(heading)==1
text=text.replace(heading,'''## 唯一 current-state（2026-10-24；新修正已合流，準備固定下一輪來源）

已一般 merge 排序修正來源 `aa16e73d6e1f2965e0a911581e2a545aaaf66870`，整合提交 `48f6e79d1192c8bcdb37cee631795bf147e2445b`。原三suite共35方法／零skip、332 compile/link全0；整刀實際128→896→128、exit0/1/0，四細控制正常assert撤回／恢復；獨立3139／0。這些實跑屬子分支S，不移標到合流提交；完整native／browser／新載入性能尚未跑。

本提交再採完整W原lexer盤點出的9個Reading A guard，928→937 identifiers，55 strings與全部原分類／排除／trust／其餘政策不變。原U產品／physical E4d上的九組原scanner assertion各0/1/0、兩neutral0、fullscanner0，329／0獨審；完整原件在reading-a-architecture-guard-strengthening。舊架構receipt仍是歷史，接著在新的可解析來源重跑三原裁判、同來源guard反證並重產四檔，再由root處理最終整份帳本。沒有把U舊紅燈或CI改綠，也沒有READY-TO-MERGE。

### 前輪 U 終態與歷史矩陣（不代表上述新來源）''',1)
p.write_text(text)
git('add','-f','--sparse',str(MP),str(T),str(B/'PROGRESS.md'));paths=git('diff','--cached','--name-only').splitlines();assert all(x in [str(MP),str(B/'PROGRESS.md')] or x.startswith(str(T)+'/') for x in paths)
git('diff','--cached','--check','--',str(MP),str(B/'PROGRESS.md'),str(T/Path(__file__).name),str(T/'INVENTORY.json'))
git('commit','-m','fix: guard Reading A woodworking identifiers at architecture boundaries');head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','origin','refs/heads/'+BR).split()[0]==head and not git('status','--porcelain=v1')
assert git('diff','--name-only',BEFORE,head,'--','.',':(exclude)evidence')==str(MP)
c.dump(O/'RESULT.json',{'product_source':head,'previous_source':BEFORE,'published':True,'push_exit':0,'only_non_evidence_change':str(MP),'added_identifiers':added,'identifiers_before_after':[928,937],'strings_unchanged':55,'four_artifacts_regenerated':False,'ledger_regenerated':False,'original_evidence_files':len(inv),'original_evidence_bytes':sum(x['bytes'] for x in inv)});print((O/'RESULT.json').read_text())
