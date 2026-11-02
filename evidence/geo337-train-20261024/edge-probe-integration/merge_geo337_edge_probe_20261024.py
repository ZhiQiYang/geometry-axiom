from pathlib import Path
import hashlib, importlib.util, json, os, shutil

R=Path('/workspace/geometry-axiom')
O=Path('/workspace/geo337-edge-probe-integration-20261024')
B=Path('evidence/geo337-train-20261024')
T=B/'edge-probe-integration'
BEFORE='1952b0ae604291a2ec447a5cc684d6ab91306779'
SOURCE='a543eef67b81f8d8800f32d5dc4a5641840d2943'
BRANCH='codex/train-337-continue-20261024'
cp=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(cp.read_bytes()).hexdigest()=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('cap',cp);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
peer=Path('/workspace/geo323-source-index-peer-specials-20261024/ACTUAL_R2_REVIEW.json')
p=json.loads(peer.read_bytes());assert p['source']==SOURCE and p['checkCount']==1427 and not p['failures']
O.mkdir(); env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0');env.pop('PYTHONOPTIMIZE',None)
rec=c.Recorder(O,env,SOURCE)
def git(*args):
    row,out,err=rec.run(['git',*args],cwd=R,timeout=None,check=False,source_variant='normal-edge-probe-integration')
    assert row['actual_process_returncode']==0,(args,err)
    return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE
assert git('branch','--show-current')==BRANCH
assert not git('status','--porcelain=v1','--untracked-files=all')
git('merge-base','--is-ancestor','b621a4fbc3cdea359b3676fb22dc8ef566968b8a',SOURCE)
expected={'geometry-core/kernel/source.c','tests/geo261_source_index_harness.c','tests/test_geo261_source_index.py','tests/run_all.expected.json'}
assert set(git('diff','--name-only','b621a4fbc3cdea359b3676fb22dc8ef566968b8a',SOURCE).splitlines())==expected
git('diff','--check','b621a4fbc3cdea359b3676fb22dc8ef566968b8a',SOURCE)
git('merge','--no-ff','--no-commit',SOURCE)
assert set(git('diff','--cached','--name-only').splitlines())==expected
target=R/T;target.mkdir()
shutil.copyfile(peer,target/'ACTUAL_R2_REVIEW.json')
shutil.copyfile(__file__,target/Path(__file__).name)
c.dump(target/'SOURCE_BINDING.json',{'source_sha':SOURCE,'previous_evidence_head':BEFORE,'mode':'normal merge; no history rewrite','independent_actual_review_checks':1427,'suite_methods':17,'suite_exit':0,'compiler_link_commands':56,'compiler_link_exits_all_zero':True,'native_processes':43,'whole_withdrawal_cost_calls':[21,31,21],'whole_withdrawal_exits':[0,1,0],'first_attempt':'test directory and executable name collision; preserved; not a mutation kill','limits':['No new performance result','Final union ledger, architecture and full gates pending','Previous L raw gates keep original execution SHA']})
progress=R/B/'PROGRESS.md';text=progress.read_text()
old='唯一最終驗收來源 **L='
assert text.count(old)==1
text=text.replace(old,'上一輪完整驗收來源 **L=',1)
anchor='## 唯一 current-state（2026-10-24 03:07 UTC）'
assert text.count(anchor)==1
text=text.replace(anchor,'''## 唯一 current-state（2026-10-24；開始合流下一個來源）

目前產品已一般 merge 核心 edge probe 修正來源 `a543eef67b81f8d8800f32d5dc4a5641840d2943`；此提交的 HEAD 是新整合來源，但最後 union 尚未固定。子分支原 17 方法零 skip、56 次 compile/link 全 0、43 次 native 已實跑；十組語意控制及完整撤回／恢復（hash calls 21／31／21、exit 0／1／0）已通過，獨立原流審查 1427／0。第一輪 Linux 測試目錄／執行檔撞名的失敗完整保留，修測試路徑後重跑，未更動斷言或時限。詳見 `edge-probe-integration/`；完整子分支原包由 owner 接續發布後合入。

**新來源尚未通過最終帳本、架構或整套驗收，也沒有新的效能結論。** 下表是上一輪固定 L 的真終態，不能移標為目前 HEAD；四個既有阻擋仍保留。其餘工作線先完成定向驗收再合流，之後由 root 一次重產帳本／架構並執行受影響正式項。
''',1)
progress.write_text(text)
git('add','-f','--sparse',str(T),str(B/'PROGRESS.md'))
git('diff','--cached','--check')
git('commit','-m','perf: integrate verified source edge probe reuse')
head=git('rev-parse','HEAD')
assert git('rev-list','--parents','-n','1',head).split()==[head,BEFORE,SOURCE]
git('push','origin','HEAD:'+BRANCH)
assert git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all')
c.dump(O/'RESULT.json',{'previous_head':BEFORE,'merged_source':SOURCE,'integration_head':head,'published':True,'push_exit':0,'product_performance_unrun':True,'final_union_unfixed':True})
print((O/'RESULT.json').read_text())
