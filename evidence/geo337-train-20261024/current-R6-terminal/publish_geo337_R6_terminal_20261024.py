from pathlib import Path
import hashlib, importlib.util, json, os
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-R6-terminal-publication-20261024');B=Path('evidence/geo337-train-20261024');T=B/'current-R6-terminal'
F='2bbe54f19b2d19e8a816530f0c4edca950629a34';BEFORE='12f36515d61011ea6072d52a425370aa5fdcd932';BR='codex/train-337-continue-20261024'
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=Path('/workspace/geo323-r6-terminal-summary-20261024/SUMMARY.json')
assert H(S)=='349c75785e5b08cf6623a1eba532ae5a39cdcd386c2e0a64431aa13c9bf2d9a1'
summary=json.loads(S.read_text());assert summary['source_sha']==F and summary['original_outer_exit']==1
p=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');assert H(p)=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
sp=importlib.util.spec_from_file_location('cap',p);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
O.mkdir();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONOPTIMIZE',None);r=c.Recorder(O,env,F)
def git(*args):
    row,out,err=r.run(['git',*args],cwd=R,timeout=None,check=True,source_variant='publish all current R6 terminal failures and exact-source environmental classification')
    return out.decode().strip()
assert git('rev-parse','HEAD')==BEFORE and git('branch','--show-current')==BR and not git('status','--porcelain=v1')
assert not git('diff','--name-only',F,BEFORE,'--','.',':(exclude)evidence')
inventory=[]
def copy(source,target,pin=None,size=None):
    source=Path(source);target=R/target;assert source.is_file() and not source.is_symlink() and not target.exists()
    raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if pin:assert sha==pin
    if size is not None:assert len(raw)==size
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    inventory.append({'path':str(target.relative_to(R)),'original_path':str(source),'bytes':len(raw),'sha256':sha})
def tree(source,target):
    source=Path(source)
    for f in sorted(source.rglob('*')):
        assert not f.is_symlink()
        if f.is_file():copy(f,target/f.relative_to(source))
copy(S,T/'SUMMARY.json')
for label,x in summary['original_file_bindings'].items():copy(x['path'],T/'original-terminal'/(label+'.json'),x['sha256'],x['bytes'])
for label,path in [('launch-five','/workspace/geo323-final-r6-stage-tools-20261024/launch-five'),('outer-five','/workspace/geo323-final-r6-stage-tools-20261024/outer-five'),('ledger-freshness','/workspace/geo337-2bbe54f1-ledger-freshness-20261024'),('required-ci','/workspace/geo337-2bbe-12f-current-required-ci-20261024'),('required-ci-outer','/workspace/geo337-2bbe-12f-current-required-ci-launch-20261024')]:
    assert Path(path).is_dir();tree(path,T/label)
for f in sorted(Path('/workspace/geo323-final-r6-stage-tools-20261024').iterdir()):
    if f.is_file():copy(f,T/'stage-tool-preparation'/f.name)
for name,pin in [('R6_TERMINAL_CI_LEDGER_ACTUAL_PEER.json','81761ddcbc87af507c86a047efaa6d98ad5b407359cca6aa89b53dadc7abd875'),('R6_SOURCE_PREPARATION_ACTUAL_PEER.json','3d6bb08868c9cd82778de2717ca22145311f317a3e91fc68cb2a0eef5520f58d'),('F2BBE_ARCHITECTURE_ADOPTION_AND_LEDGER_ACTUAL_PEER.json','86204ee19cc11308d6671fcd4d36b1ec95488ecaeaf220353d51a6aab3bfb48f'),('R6_STAGE_PARAMETER_TOOLS_STATIC_PEER.json','753dac214ac8607b4b0d47053be2a80d953cd323193127275b3621317ec575a3')]:
    copy(Path('/workspace/train337-canvas-peer-resume')/name,T/'peer'/name,pin)
copy('/workspace/geo337-2bbe-12f-ci-peer-backlog-20261024/REVIEW.json',T/'peer'/'CI_INDEPENDENT_REVIEW.json','4a5fe66daf1f121c055c85989f63b27593b83e1a9fdec8d8913ceea1cb2f265d')
copy(__file__,T/Path(__file__).name)
c.dump(R/T/'PUBLICATION_INVENTORY.json',{'product_source':F,'previous_evidence_head':BEFORE,'full_R6_raw_archive_published':False,'full_R6_source_preparation_raw_published':False,'limits':'This is a complete terminal projection with original outer command streams, current CI and ledger freshness. Inner compare/perf/profile raw streams remain at their original paths pending the separately reviewed full archive.','files':inventory})
progress=R/B/'PROGRESS.md';text=progress.read_text();start=text.index('## 唯一 current-state');end=text.index('### 歷史 R5 終態',start)
old=text[start:end].replace('## 唯一 current-state（2026-10-24；平面區間快取已合流，準備 R6）','### 歷史 W 合流與架構採用（正式 R6 前的狀態）',1)
current='''## 唯一 current-state（2026-10-24；F2bbe 的 R6 已收齊終態）

固定產品／測試／架構產物來源 **F=`2bbe54f19b2d19e8a816530f0c4edca950629a34`**。後續普通 evidence 合流不改來源；獨立乾淨F checkout已一次跑完R6原prepare/build/compare/perf/profile，stage execution=0/0/1/0/0、累積CLI=0/0/1/1/1、outer1，原雙鎖正常釋放。全36交錯樣本保留，未重抽、未放寬門檻。

原性能判定兩紅：**N64 fix/main=1.3731562025736295>1.3**（median fix0.6787833540s、main0.4943234810s）；**N16 fix/base=1.0434575834374764>1**。N32/base0.8823227658668896與N48/base0.7581122695004152綠；source calls82668→364369、64/32=4.407618425509266≤4.5綠。不能把stage本身exit0冒作量化門檻全綠，或以gprof秒數代原O2 wall。

原compare完成175scenes/350base-fix runs，仍在verify_linux.py:156的assert not failures,failures真1：role_priority、P8低／高凹角三個stdout差。完整有序圖／guards前段相同不能代後段audit，原ABC_result缺席、all_required_stages_completed=false、full_acceptance_passed=null保留。QUESTIONS既有診斷版本界線仍待決；不刪I22必要定位、不過濾或正規化exact。

F自身原tracked `python3 tests/mutate.py --check` 真1：123筆、120stale/3retired/0invalid，前後HEAD=F且clean；全量帳本尚未重產。完整native、六browser、P52、Q38(44)、§7兩項、P189full/timing、required-eight/PF3/native後段、memo/隔離ABC、三reader/RC兩刀/#314/ReadingA專項在F仍UNRUN。既有Linux Windows-GDI skip以外零新增允許skip，原斷言/golden/時限均保。

F required CI run40066383912與當時E12f36515 run40066703178各七job failure，runner_id0、steps0；18API原讀均0，原failure annotation為付款失敗或支出上限，Ubuntu migration notice另列。這是未啟動的環境阻擋，沒有修付款／required checks，沒有自認正式替代被接受；新純證據E不能冒用上述E12f的CI run。B3未解除。

架構三原裁判實跑M=`8d2a69421560b83c0b69f3e82db8f5e97ccc037b`真0/0/0，generic205/product18零skip；F已採四檔，937→937、604inputs/798edges/0diagnostics，九fresh guard0/1/0。實跑SHA不移標。W來源df664的36方法與整刀0/84/0、五細控制及四行反例0/1/0全包已普通合入E12f的evidence/geo343-plane-ranges-df66452e/；定向綠不能解除本輪wall雙紅。

本次current-R6-terminal公開原終態投影/六原bindings/五CLI與outer全流、當前CI/帳本原件、671/0實績/3353來源準備/704架構採用與check等獨審。完整R6 inner graph/所有命令/gprof原流及source準備原件仍在雲端待完整封包；小摘要不冒全包。R5完整9055member/31,186,327B原包已在TMP封成，尚待公開；U9091member全包已公開E586。

下一步依新profile分工：W剩餘查詢成本只準備可撤回證明，K做外部shadow觀察以量測短key衝突；不先猜新策略、不並改產品、不以同源重抽樣本取得綠。**目前非READY-TO-MERGE。**

'''
progress.write_text(text[:start]+current+old+text[end:])
q=R/B/'QUESTIONS.md';q.write_text(q.read_text()+'''\n\n### F2bbe／R6 原判補記\n\nF2bbe54f19b2d19e8a816530f0c4edca950629a34 的36原樣本現為 N64/main1.3731562025736295>1.3、N16/base1.0434575834374764>1。它們是繼續自主尋因的效能缺陷，不請求改門檻、不挑綠重抽；其餘小N/calls綠不解除兩紅。exact仍原三個診斷差，Q-323-ABC／Q-P189-EXACT的核可界線不變。F與E12f本輪required CI仍由原annotation分類為付款失敗或支出上限未啟動，B3未解除；詳細原件見current-R6-terminal。\n''')
git('add','-f','--sparse',str(T),str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'))
assert all(x in [str(B/'PROGRESS.md'),str(B/'QUESTIONS.md')] or x.startswith(str(T)+'/') for x in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--',str(B/'PROGRESS.md'),str(B/'QUESTIONS.md'),str(T/'PUBLICATION_INVENTORY.json'),str(T/Path(__file__).name))
git('commit','-m','docs: publish complete current performance verdicts and CI classification')
head=git('rev-parse','HEAD');git('push','origin','HEAD:'+BR)
assert git('ls-remote','origin','refs/heads/'+BR).split()[0]==head and not git('status','--porcelain=v1')
assert not git('diff','--name-only',F,head,'--','.',':(exclude)evidence')
c.dump(O/'RESULT.json',{'product_source':F,'evidence_head':head,'previous_evidence_head':BEFORE,'published':True,'push_exit':0,'full_R6_raw_archive_published':False,'original_outer_exit':1,'files':len(inventory),'bytes':sum(x['bytes'] for x in inventory)})
print((O/'RESULT.json').read_text())
