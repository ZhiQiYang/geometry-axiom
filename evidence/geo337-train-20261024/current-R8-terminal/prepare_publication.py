from pathlib import Path
import hashlib,json

O=Path('/tmp/geo337-R8-terminal-publication-preparation-20261025')
BASE='evidence/geo337-train-20261024/'
T=BASE+'current-R8-terminal/'
F='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
E='815cd2e348e47e1666371aff5060820ff29a913a'
files=[]
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(src,dest,pin=None):
    p=Path(src);assert p.is_file() and not p.is_symlink()
    h=H(p)
    if pin:assert h==pin
    files.append({'source_path':str(p),'destination':dest,'bytes':p.stat().st_size,'sha256':h})
def tree(src,dest):
    p=Path(src);assert p.is_dir()
    for f in sorted(p.rglob('*')):
        assert not f.is_symlink()
        if f.is_file():add(f,dest+'/'+str(f.relative_to(p)))
O.mkdir()
S=Path('/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json')
add(S,T+'SUMMARY.json','23c0b08133a48285bb7fd75192a9b05a2fb190fa04ca5dc5cadfb28e28a4e5dd')
summary=json.loads(S.read_text());assert summary['source_sha']==F and summary['original_outer_exit']==1
for label,row in summary['original_file_bindings'].items():add(row['path'],T+'original-terminal/'+label+'.json',row['sha256'])
for label,src in [
 ('outer-five','/tmp/geo323-final-r8-stage-tools-20261024/outer-five'),
 ('launch-five','/tmp/geo323-final-r8-stage-tools-20261024/launch-five'),
 ('ledger-freshness','/tmp/geo337-F8-ledger-freshness-20261025'),
 ('required-ci','/tmp/geo337-F8-E815-current-required-ci-20261025'),
 ('architecture-adoption','/tmp/geo337-h-architecture-adoption-20261025'),
 ('H-evidence-integration','/tmp/geo337-h-local-init-evidence-integration-20261025'),
 ('architecture-adoption-peer','/tmp/geo337-h-adoption-resume-peer-20261025'),
 ('summary-launch','/tmp/geo323-r8-collection-preparation-20261025/summary-launch'),
 ('summary-tool','/tmp/geo323-r8-collection-preparation-20261025/summary-tool')]:tree(src,T+label)
for p in sorted(Path('/tmp/geo323-final-r8-stage-tools-20261024').iterdir()):
    if p.is_file():add(p,T+'stage-tools/'+p.name)
add('/tmp/geo337-h-init-collector-peer-20261025/PUBLICATION_ACTUAL_REVIEW.json',T+'peer/H_PUBLICATION_ACTUAL.json','01fe5ac75d2df86aff88c4927c2f79dfbc697d825357ebecc7f7ff4f20873d04')
add('/tmp/capture_geo337_F8_E815_ci_status_20261025.py',T+'capture_current_ci.py')
add(__file__,T+'prepare_publication.py')
old=Path('/workspace/geometry-axiom/evidence/geo337-train-20261024/PROGRESS.md').read_text()
start=old.index('## 唯一 current-state');end=old.index('### 歷史 R7 終態',start)
history=old[start:end].replace('## 唯一 current-state（2026-10-25；H 初始化修正已合流，準備 R8）','### 歷史 H 合流與架構採用（正式 R8 前）',1)
current='''## 唯一 current-state（2026-10-25；F8 的 R8 性能全綠，exact 仍紅）

固定產品／測試／架構產物 F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad`。R8在獨立乾淨checkout完成原prepare/build/compare/perf/profile，execution=0/0/1/0/0，累積CLI=0/0/1/1/1，outer=1。完整36個交錯樣本一次保留，沒有重抽或選樣；四份真工具回覆包含terminal chunk2aff4e／exit1。

**原性能門檻全部通過：N16/base=0.9834192453688345≤1、N32/base=0.9007932884873169≤1、N48/base=0.7392862448969592≤1、N64/main=1.2846970752586067≤1.3。** source calls82668→364369，64/32=4.407618425509266≤4.5。N16 median fix0.1123812579899095s、base0.11427604098571464s；不剔除第二輪較慢樣本，不以O0工作反證或O1/pg時間代O2 wall。

原compare仍exit1：175scenes／350runs的程序與trace皆0，但role_priority、P8低／高凹角三個stdout差觸發 verify_linux.py:156 的 assert not failures,failures。ABC_result仍缺席、all_required=false／full_acceptance=null；前段graph／guards相同不能代後段未到audit。Q-323-ABC／Q-P189-EXACT維持待明確版本界線裁決，不刪必要I22診斷、不正規化輸出。

F8真正tracked `python3 tests/mutate.py --check` 已真exit1，120stale／3retired／0invalid，前後同F8 clean，所有MUTATE_*清除。外層完成0不等check0。產品暫定穩定，root接續整份123重產；完整native、六browser、P52、Q38(44)、§7、P189 full/timing、required-eight/PF3、memo、readers／RC／#314／Reading A在F8仍UNRUN。只允許原Linux Windows-GDI skip，不新增skip。

架構真正執行M=`6e50aef65513b7b38f93228919272c6d40d6c196`：三gate0/0/0、205＋18零skip、604inputs唯一references.inc變動、九guard各0/1/0／neutral2綠。F8只採用有差的report／receipt，政策937／55與scan不變。380原件／4,630,676B在architecture-6e50-complete/，本批附採用actualpeer，不把M實跑改標F8。

H定向來源S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`原14/14、零skip、work0/1/0；真memset calls0/2/0、bytes0/255168/0。完整2546members包SHA7011e2b2fcf35f15e53deac9f2e5d27aabf4429ffe32f275465d8abd4c5d4388已公開child E74a0，再普通合入root E815cd2e3；本批附其公開blobs獨審與合流原流，產品不變。這些focused結果不代完整native。

F8 required CI run40170221039與證據E815cd2e3 run40170692505，18原API讀皆0，各七job failure、runner_id0／steps0；annotation明示付款失敗或支出上限，Ubuntu migration notice另列。沒有變更帳戶或自行核可替代流程。本提交以後的新E未讀CI，不把E815結果移標。

本批current-R8-terminal/公開原六bindings、全部36樣本／profiles摘要、五CLI／outer完整流、真工具poll、帳本check、CI與採用／H公開原件。完整R8 inner/source preparation大型封包尚未公開，不能把小摘要冒完整原包；R5／R6／R7公開原件保留原source／紅燈。root將接續補全R8大包與全帳本、其餘正式驗收。**目前不是READY-TO-MERGE。**

'''
p=O/'PROGRESS.publish.md';p.write_text(old[:start]+current+history+old[end:]);add(p,BASE+'PROGRESS.md')
assert len({r['destination'] for r in files})==len(files)
p=O/'FILES.draft.json';p.write_text(json.dumps({'schema':'geo337-R8-terminal-publication/1','product_source':F,'previous_evidence_head':E,'full_R8_archive_published':False,'files':files},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manifest':str(p),'sha256':H(p),'files':len(files),'bytes':sum(x['bytes'] for x in files)}))
