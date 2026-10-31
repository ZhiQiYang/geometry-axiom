from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom');I=Path('/workspace/geo337-b9c9-architecture-four-20261024');O=Path('/workspace/geo337-b9-architecture-adoption-20261024');B=Path('evidence/geo337-train-20261024');T=B/'architecture-b9-complete';ART=Path('geometry-core/domain-decoupling');F='b9c9fb818f031828530994a4d66f1976da0d8138';BR='codex/train-337-continue-20261024'
summary=json.loads((I/'RESULT.json').read_text());assert summary['sourceSHA']==F and summary['sourceBeforeAfterClean'] and summary['originalGateExits']==[0,0,0] and summary['newGuardProofExits']==[0,1,0] and summary['newGuardCases']==9
PEER=Path('/workspace/geo337-b9-architecture-peer-specials-20261024/REVIEW.json');assert hashlib.sha256(PEER.read_bytes()).hexdigest()=='412cbeee92d6e0f6718796bfce3917d141cededa29864f0a5f6b8c08877bdfa5'
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(p.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762';sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,F)
def git(*args):
 row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='adopt actual Linux four-artifact receipt with unchanged executable closure');return out.decode().strip()
assert git('rev-parse','HEAD')==F and git('branch','--show-current')==BR and not git('status','--porcelain=v1')
changed=[]
for name,expected in summary['outputs'].items():
 src=I/'new'/name;raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected['rawSha256']
 target=R/ART/name
 if target.read_bytes()!=raw:changed.append(str(ART/name));target.write_bytes(raw)
assert sorted(changed)==sorted([str(ART/'PRODUCT-ARCHITECTURE.md'),str(ART/'product-architecture-receipt.json')])
target=R/T;assert not target.exists();shutil.copytree(I,target/'originals');shutil.copytree(PEER.parent,target/'peer');shutil.copyfile(__file__,target/Path(__file__).name)
inv=[]
for f in sorted(target.rglob('*')):
 if f.is_file():
  assert not f.is_symlink();raw=f.read_bytes();inv.append({'path':str(f.relative_to(target)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
c.dump(target/'INVENTORY.json',{'actual_execution_source':F,'original_gate_exits':[0,0,0],'guard_proofs':9,'changed_artifact_paths':changed,'files':inv})
p=R/B/'PROGRESS.md';t=p.read_text();needle='舊架構receipt仍是歷史，接著在新的可解析來源重跑三原裁判、同來源guard反證並重產四檔，再由root處理最終整份帳本。';assert t.count(needle)==1
t=t.replace(needle,'三原裁判及四檔已在固定來源 `b9c9fb818f031828530994a4d66f1976da0d8138` 真完成並於本提交採用；generic205／product18、零skip，604 inputs／334 owned／270 exclusions／798 edges／零diagnostics，九組同來源guard反證各0/1/0與兩neutral0。原execution仍為b9，不把產物提交冒作執行來源；1696／0獨審與完整原流在architecture-b9-complete。由root接著處理最終整份帳本。',1)
t+='\n### b9 架構四檔採用\n\n三原裁判0/0/0、九組原scanner具名assert反證0/1/0已在同一可解析b9完成，完整48條原命令、604Git/blob/raw/LF與兩SSOT初末保全。manifest／scan bytes不變，衍生diff只有report／receipt；前份928產物與本次937執行來源分開保存，沒有把較早native/browser/ledger移標。下一次性能使用已獨審的PIPE計時收件工具，原v4／U紅燈完整保留；測試門檻與樣本不變。\n';p.write_text(t)
git('add','-f','--sparse',*changed,str(T),str(B/'PROGRESS.md'));assert all(x in changed+[str(B/'PROGRESS.md')] or x.startswith(str(T)+'/') for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',*changed,str(B/'PROGRESS.md'),str(T/'INVENTORY.json'),str(T/Path(__file__).name));git('commit','-m','docs: regenerate integration architecture receipt from the fixed source');head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','origin','refs/heads/'+BR).split()[0]==head and not git('status','--porcelain=v1')
assert sorted(git('diff','--name-only',F,head,'--','.',':(exclude)evidence').splitlines())==sorted(changed)
c.dump(O/'RESULT.json',{'actual_execution_source':F,'artifact_commit':head,'published':True,'push_exit':0,'original_gate_exits':[0,0,0],'changed_non_evidence':changed,'ledger_regenerated':False,'original_files':len(inv),'original_bytes':sum(x['bytes'] for x in inv)});print((O/'RESULT.json').read_text())
