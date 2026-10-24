from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-U-architecture-ci-publication-20261024')
B=Path('evidence/geo337-train-20261024');T=B/'current-U-architecture-and-ci'
U='ca7838e0f4950452b9befcf40899d606db9b81fa';BEFORE='b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5';BRANCH='codex/train-337-continue-20261024'
INPUTS={'architecture':'/workspace/geo337-U-architecture-precheck-20261024','ci':'/workspace/geo337-U-current-required-ci-20261024'}
a=json.loads((Path(INPUTS['architecture'])/'RESULT.json').read_text());assert a['execution_head']==BEFORE and a['product_source']==U and a['architecture_gate_exits']==[0,0,0] and a['source_unchanged']
ci=json.loads((Path(INPUTS['ci'])/'SUMMARY.json').read_text());assert ci['product_source']==U and ci['evidence_head']==BEFORE
assert [x['run_id'] for x in ci['runs']]==[40058889738,40059064935]
assert all(len(x['jobs'])==7 and all(j['conclusion']=='failure' and j['steps_count']==0 for j in x['jobs']) for x in ci['runs'])
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert hashlib.sha256(p.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
s=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,U)
def git(*args):
 row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='current U architecture and required CI evidence publication');return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BRANCH and not git('status','--porcelain=v1')
assert not git('diff','--name-only',U,BEFORE,'--','.',':(exclude)evidence')
target=R/T;target.mkdir();inventory=[]
for label,directory in INPUTS.items():
 source=Path(directory);dest=target/label;shutil.copytree(source,dest)
 for f in sorted(source.rglob('*')):
  if not f.is_file():continue
  assert not f.is_symlink();other=dest/f.relative_to(source);raw=f.read_bytes();assert other.read_bytes()==raw
  inventory.append({'path':str(other.relative_to(target)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
shutil.copyfile('/workspace/capture_geo337_U_ci_status_20261024.py',target/'capture_geo337_U_ci_status_20261024.py');shutil.copyfile(__file__,target/Path(__file__).name)
c.dump(target/'INVENTORY.json',{'product_source':U,'architecture_execution_head':BEFORE,'files':inventory,'original_files':len(inventory),'original_bytes':sum(x['bytes'] for x in inventory),'four_architecture_artifacts_refreshed':False,'required_ci_passed':False})
progress=R/B/'PROGRESS.md';text=progress.read_text();needle='**新來源尚未通過最終帳本、架構或整套驗收，也沒有新的效能結論。**';assert text.count(needle)==1
text=text.replace(needle,'**新來源尚未通過最終帳本、架構四檔重產或整套驗收，也沒有新的效能結論。** 架構三原裁判已於實際 HEAD `b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5` 執行 0／0／0（205／18 方法、334 sources／6 trusted／798 edges／零 diagnostics）；原 Git diff 證明該 HEAD 除 evidence 外與 U 完全相同，但不把實際 execution SHA 改寫為 U。完整指令／原流封存於 `current-U-architecture-and-ci/architecture/`。\n\n新 required CI 原件已讀並封存：U 的 Actions run **40058889738**、證據頭 b09 的 run **40059064935**，各七個 job 為 failure，steps 都是空；原 annotation 明載付款失敗或支出上限導致工作未啟動。Ubuntu 26 runner label 遷移 notice 另外保留，不冒充失敗原因。尚未修復帳戶環境，也沒有正式替代已獲接受的證據，B3 仍未解除；f05 舊 run 只留歷史。完整原 API 指令與退出碼在 `current-U-architecture-and-ci/ci/`。',1)
progress.write_text(text)
q=R/B/'QUESTIONS.md';text=q.read_text();assert '## Q-CI-CURRENT-U' not in text
text+='''\n\n## Q-CI-CURRENT-U：新合流來源的 required jobs 仍受帳戶環境阻擋

U=`ca7838e0f4950452b9befcf40899d606db9b81fa` 的 run40058889738，及證據頭 b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5 的 run40059064935，七個 required jobs 都是 failure／steps=[]，原 annotation 明載 recent account payments failed 或 spending limit。原 API 讀取全退出0；沒有把未啟動的 job 算作產品測試紅燈或成功。完整原件已封 current-U-architecture-and-ci/ci。

保守處理是保留 required checks 阻擋，繼續同產品來源的雲端原門檻與修正；本代理不改付款設定、支出上限、required checks 或原 workflow。可由帳戶環境修復後取得同 head 真 CI 終態，或由既有正式替代流程明確接受同來源補跑收據；目前兩者都尚未成立，不能自行解除 B3 或標 READY-TO-MERGE。這不阻斷其他工作線，也不在對話要求使用者回覆。
'''
q.write_text(text)
git('add','-f','--sparse',str(T),str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'))
assert all(x.startswith(str(T)+'/') or x in [str(B/'PROGRESS.md'),str(B/'QUESTIONS.md')] for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'),str(T/'INVENTORY.json'),str(T/Path(__file__).name))
git('commit','-m','docs: record current architecture gates and required CI environment failures')
head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BRANCH);assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head
assert not git('status','--porcelain=v1') and not git('diff','--name-only',U,head,'--','.',':(exclude)evidence')
c.dump(O/'RESULT.json',{'product_source':U,'previous_evidence_head':BEFORE,'evidence_head':head,'published':True,'push_exit':0,'architecture_exits':[0,0,0],'architecture_execution_head':BEFORE,'four_architecture_artifacts_refreshed':False,'required_ci_passed':False})
print((O/'RESULT.json').read_text())
