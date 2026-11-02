from pathlib import Path
import argparse, hashlib, importlib.util, json, os, shutil
p=argparse.ArgumentParser();p.add_argument('--peer',type=Path,required=True);p.add_argument('--peer-sha256',required=True);a=p.parse_args()
R=Path('/workspace/geometry-axiom');I=Path('/workspace/geo337-8d2a-architecture-four-20261024');O=Path('/workspace/geo337-8d2a-architecture-adoption-20261024')
B=Path('evidence/geo337-train-20261024');T=B/'architecture-8d2a-complete';ART=Path('geometry-core/domain-decoupling')
F='8d2a69421560b83c0b69f3e82db8f5e97ccc037b';BR='codex/train-337-continue-20261024'
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
summary=json.loads((I/'RESULT.json').read_text())
assert summary['sourceSHA']==F and summary['sourceBeforeAfterClean'] and summary['originalGateExits']==[0,0,0]
assert summary['newGuardProofExits']==[0,1,0] and summary['newGuardCases']==0 and summary['existingGuardCasesRetested']==9
assert summary['manifestDelta']=='unchanged-937-to-937'
assert H(a.peer)==a.peer_sha256
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert H(p)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,F)
def git(*args):
    row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='adopt original architecture receipts after reviewed plane range optimization')
    return out.decode().strip()
assert git('rev-parse','HEAD')==F and git('branch','--show-current')==BR and not git('status','--porcelain=v1')
changed=[]
for name,expected in summary['outputs'].items():
    src=I/'new'/name;raw=src.read_bytes();assert H(src)==expected['rawSha256']
    target=R/ART/name
    if target.read_bytes()!=raw:changed.append(str(ART/name));target.write_bytes(raw)
assert sorted(changed)==sorted([str(ART/'PRODUCT-ARCHITECTURE.md'),str(ART/'product-architecture-receipt.json')])
target=R/T;assert not target.exists()
shutil.copytree(I,target/'originals');(target/'peer').mkdir();shutil.copyfile(a.peer,target/'peer'/'ACTUAL_REVIEW.json')
shutil.copytree('/workspace/geo337-architecture-zero-delta-tool-20261024',target/'tool-preparation')
shutil.copyfile(__file__,target/Path(__file__).name)
inv=[]
for f in sorted(target.rglob('*')):
    if f.is_file():
        assert not f.is_symlink();inv.append({'path':str(f.relative_to(target)),'bytes':f.stat().st_size,'sha256':H(f)})
c.dump(target/'INVENTORY.json',{'actual_execution_source':F,'original_gate_exits':[0,0,0],'existing_guard_proofs_retested':9,'current_manifest_delta':'zero','changed_artifact_paths':changed,'files':inv})
progress=R/B/'PROGRESS.md';text=progress.read_text();start=text.index('## 唯一 current-state');end=text.index('### 前輪 U 終態與歷史矩陣',start)
previous=text[start:end].replace('## 唯一 current-state（2026-10-24；R5 正式五階段已終態）','### 歷史 R5 終態（執行來源 a22df116；不移標新來源）',1)
current='''## 唯一 current-state（2026-10-24；平面區間快取已合流，準備 R6）

最新產品／測試合流來源 M=`8d2a69421560b83c0b69f3e82db8f5e97ccc037b` 已普通 push。它將 child F=`df66452e7a514032453bea93b8b18ab74d7b1457` 的5個產品／測試葉一般 merge 到前輪列車；產品與測試 bytes 完全相同，其餘差異只有 evidence。沒有改公理、決策、原門檻或容量64。既有 scratch 在排序後記錄各完整64-bit平面區間，移除重複二分搜尋，不增加堆疊或改遮擋判定。

child F 三原 suite 真0/0/0，14+15+7=36方法、零skip，354次 compile/link 均0；整刀正常0/1/0對應 plane comparisons 0→84→0，五細控制亦0/1/0。原 full-coordinate 反證曾在R1存活；原斷言保留，補第三個同平面成員後重新全綠。這四行反例另做固定／撤回／恢復真0/1/0，撤回精確 `Guard survived: indexed-plane-coordinate`。R1紅與兩項環境未跑仍保留；不能以定向綠外推正式 N64 wall。

本提交採用 M 真執行的架構四檔：三原 exit0/0/0、generic205/product18零skip、604inputs/334owned/270excluded/798edges/0diagnostics。manifest 937→937、55 strings 與 scan bytes 完全不變；相較前份b9收據，完整架構closure僅 contact_world.c 改變。九個既有guard在M重新0/1/0，withdrawn明確使用歷史U的928版manifest，不冒稱上一份937版。完整原件與獨審在 architecture-8d2a-complete/。

新的正式效能來源將固定於本次衍生report／receipt採用提交後，以可解析SHA啟動R6；目前 R6、全123帳本、完整native、六browser及P52/Q38/§7/P189/required-eight/PF3/readers/閱讀A均為新來源UNRUN。前輪R5 N64/main=1.3369644933292553>1.3、三項exact差及required CI付款／支出上限阻擋沒有被此專項解除；以下僅保留歷史實跑SHA。沒有新增skip，沒有READY-TO-MERGE。

K觀察證據已普通合入 b4639b4d；沒有改K策略。R5小終態/v5工具原件和U完整9091member原包已於586f01d公開；R5完整原流正在封存。下一步在新固定來源獨占跑原五stage，完整保存36樣本與退出碼，不挑綠重抽。

'''
progress.write_text(text[:start]+current+previous+text[end:])
git('add','-f','--sparse',*changed,str(T),str(B/'PROGRESS.md'))
assert all(x in changed+[str(B/'PROGRESS.md')] or x.startswith(str(T)+'/') for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',*changed,str(B/'PROGRESS.md'),str(T/'INVENTORY.json'),str(T/Path(__file__).name))
git('commit','-m','docs: refresh architecture receipts for cached plane ranges')
head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','origin','refs/heads/'+BR).split()[0]==head and not git('status','--porcelain=v1')
assert sorted(git('diff','--name-only',F,head,'--','.',':(exclude)evidence').splitlines())==sorted(changed)
c.dump(O/'RESULT.json',{'actual_execution_source':F,'artifact_commit':head,'published':True,'push_exit':0,'original_gate_exits':[0,0,0],'changed_non_evidence':changed,'ledger_regenerated':False,'original_files':len(inv),'original_bytes':sum(x['bytes'] for x in inv)})
print((O/'RESULT.json').read_text())
