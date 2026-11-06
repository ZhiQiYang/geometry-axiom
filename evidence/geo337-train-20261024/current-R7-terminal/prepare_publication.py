from pathlib import Path
import hashlib, json

O=Path('/tmp/geo337-R7-terminal-publication-preparation-20261024')
BASE='evidence/geo337-train-20261024/'
T=BASE+'current-R7-terminal/'
F='6df0264f75e84f03adb70746b6ac3db07a9910fc'
E='597bce63e296c85e64d33ca4496f167a599f0848'
files=[]
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(src,dest,pin=None):
 p=Path(src);assert p.is_file() and not p.is_symlink()
 h=H(p)
 if pin:assert h==pin
 files.append({'source_path':str(p),'destination':dest,'bytes':p.stat().st_size,'sha256':h})
def tree(src,dest):
 p=Path(src)
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink()
  if f.is_file():add(f,dest+'/'+str(f.relative_to(p)))
O.mkdir()
S=Path('/tmp/geo323-r7-terminal-summary-20261024/SUMMARY.json')
add(S,T+'SUMMARY.json','9833baf464d50dd98bdd401788d77a6f98eb342831972b89c0acda91451e037a')
summary=json.loads(S.read_text());assert summary['source_sha']==F and summary['original_outer_exit']==1
for label,x in summary['original_file_bindings'].items():add(x['path'],T+'original-terminal/'+label+'.json',x['sha256'])
for label,src in [
 ('outer-five','/tmp/geo323-final-r7-stage-tools-20261024/outer-five'),
 ('launch-five','/tmp/geo323-final-r7-stage-tools-20261024/launch-five'),
 ('ledger-freshness','/tmp/geo337-6df-at-51e-ledger-freshness-20261024'),
 ('required-ci','/tmp/geo337-6df-597b-current-required-ci-20261024'),
 ('architecture-adoption','/tmp/geo337-e321-architecture-adoption-20261024'),
 ('provider-evidence-integration','/tmp/geo337-provider-hint-evidence-integration-20261024'),
 ('provider-source-integration','/tmp/geo337-provider-hint-source-integration-20261024')]:
 tree(src,T+label)
for p in sorted(Path('/tmp/geo323-final-r7-stage-tools-20261024').iterdir()):
 if p.is_file():add(p,T+'stage-tool-preparation/'+p.name)
for src,pin in [
 ('/tmp/train337-terminal-peer-20261024/R7_TERMINAL_CI_LEDGER_ACTUAL_PEER.json','70a2c44cb9fbc88825f899da83950863c6ba2248d3ee920e12f2e1ea6c32f7fc'),
 ('/workspace/train337-canvas-peer-resume/R7_SOURCE_PREPARATION_ACTUAL_PEER.json','c79231c1c26a865642f1e0cc2c68986e8cdf12b7d5bae0921ac2dab055600992'),
 ('/tmp/geo337-e321-architecture-adoption-peer-specials-20261024/REVIEW.json','ac121204beecc1d41d89b45d218a83d6e8dfa7f3657b82ff9f5c31e0f24e8260'),
 ('/workspace/train337-canvas-peer-resume/ROOT_K_PROVIDER_NORMAL_MERGE_ACTUAL_PEER.json','888baff67383fad1446255b73e21e79c9f0f50e6dd4a1faded2670411e766c69'),
 ('/workspace/train337-canvas-peer-resume/K_PROVIDER_EVIDENCE_BODY_PUBLICATION_ACTUAL_PEER.json','65e6d7815d0b2dd2085e1d327cb9652faffd81b9add8ac1ff343549f5958267a'),
 ('/workspace/train337-canvas-peer-resume/ROOT_R5_R6_FINAL_PUBLICATION_MANIFEST_STATIC_PEER.json','b955d50bc554bd71a3715aabb515e1a572e67e4b4a1297071ba0f0c2fe93d12f')]:
 label='ARCHITECTURE_ADOPTION_ACTUAL_REVIEW.json' if src.endswith('/REVIEW.json') else Path(src).name
 add(src,T+'peer/'+label,pin)
add('/tmp/capture_geo337_6df_597b_ci_status_20261024.py',T+'capture_current_ci.py')
add(__file__,T+'prepare_publication.py')
old=Path('/workspace/geometry-axiom/evidence/geo337-train-20261024/PROGRESS.md').read_text()
start=old.index('## 唯一 current-state');end=old.index('### 歷史 R6 終態',start)
history=old[start:end].replace('## 唯一 current-state（2026-10-24；K provider hint 已合流，準備 R7）','### 歷史 K 合流與架構採用（正式 R7 前的狀態）',1)
current='''## 唯一 current-state（2026-10-24；F6df 的 R7 已收齊終態）

固定產品／測試／架構產物 **F=`6df0264f75e84f03adb70746b6ac3db07a9910fc`**。R7 在獨立乾淨 F checkout 於 06:36:52–06:40:10 UTC 一次完成原 prepare/build/compare/perf/profile；stage execution=0/0/1/0/0、累積 CLI=0/0/1/1/1、outer=1。完整36交錯樣本保留，沒有重抽或混入 R6；原雙鎖正常釋放。三份真正工具 poll JSON 亦保留，終態 chunk87c3e8 明確 exit1。

**N64 fix/main=1.2292230778583162≤1.3，已綠；N16 fix/base=1.05190582882169>1，仍紅。** N16 median fix0.12007854899275117s、base0.1141533259942662s，差5.925ms。N32/base0.8290229168845338、N48/base0.7499983665267913與source calls82668→364369、64/32=4.407618425509266≤4.5綠。不把 perf/profile stage exit0 冒作量化門檻全過，也不以 O1/pg 時間代 O2 wall。

原 compare 完成175 scenes／350 runs，程序／trace皆0，但 verify_linux.py:156 的 assert not failures,failures 仍真1：role_priority、P8低／高凹角三個 stdout 差。完整 graph／guards 前段相同不能代未到的後段 audit；ABC_result缺席、all_required=false、full_acceptance=null保原。Q-323-ABC／Q-P189-EXACT仍待診斷版本界線裁決，不刪I22必要診斷、不過濾或正規化 exact。

原 tracked `python3 tests/mutate.py --check` 在實際 E51e36b94 真1，120 stale／3 retired／0 invalid；E51前後clean、非evidence tree與F相同，不移標成F實跑。全123帳本尚未重產。完整native、六browser、P52、Q38(44)、§7、P189 full/timing、required-eight/PF3、memo/隔離ABC、readers/RC/#314/ReadingA在F仍UNRUN。只允許原Linux Windows-GDI skip，不新增skip、不放寬golden／斷言／時限。

F 的 required CI run40070571951 與證據 E597bce63 的 run40070806058，原18次API讀皆0；兩組各七job failure，runner_id0／steps0，原annotation為付款失敗或支出上限而未啟動。Ubuntu migration notice另列。這是環境阻擋，沒有修改付款設定或宣稱正式替代已接受；本提交以後的新E之CI未讀，不以E597的run移標。

架構實跑 M=e321026fb9bc9bc19c54b8034af6e6eaec2857f9 的三原judge0/0/0、205/18零skip、604inputs/798edges/0diagnostics，九guard各0/1/0＋neutral2。F已採四檔，只有report/receipt兩個實際差異；manifest937／55與scan bytes不變。299原件在 architecture-e321-complete/，本批附674/0採用獨審，不把M結果改標F。

K定向真實來源 S1449d430 的18＋24方法全綠、整刀calls0→16→0／正常exit0/1/0及原鄰接控制，完整3201member原包已公開child E4d3ac4bf，再一般合入root E51e36b94。這些定向結果不代本輪N16 wall或全native。

R5／R6兩輪完整原件已在 E597bce63 普通推送至 full-R5-five-stage-raw/ 與 full-R6-five-stage-raw/，附全部inventory/hash與獨審。原outer1、各自性能紅與三exact差均保原執行SHA；每輪七ELF為hash inventory，原payload仍在雲端。archive-object-store/ 同批公開永久TMP Gitobjects的原接線／讀者收據，禁止清理此store。維護原件不算產品gate。

本批 current-R7-terminal/ 公開六原binding、完整外層／五CLI流、真API poll、當前CI／帳本check、stage工具與672/0獨審。完整R7 inner／source preparation原件正在一次封包，尚未公開，小摘要不冒完整原包。

下一步：依已收齊結果修N16額外成本；原單次N16 pg診斷只用作因果分析，不當新正式樣本。後續在新來源重跑受影響原門檻，穩定後由root整份重產帳本及完整驗收。其他獨立工作線繼續。**目前不是READY-TO-MERGE。**

'''
p=O/'PROGRESS.publish.md';p.write_text(old[:start]+current+history+old[end:]);add(p,BASE+'PROGRESS.md')
assert len({x['destination'] for x in files})==len(files)
p=O/'FILES.json';p.write_text(json.dumps({'schema':'geo337-R7-terminal-publication/1','product_source':F,'previous_evidence_head':E,'full_R7_archive_published':False,'files':files},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manifest':str(p),'sha256':H(p),'files':len(files),'bytes':sum(x['bytes'] for x in files)}))
