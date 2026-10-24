from pathlib import Path
import hashlib, importlib.util, json, os, shutil

R = Path('/workspace/geometry-axiom')
I = Path('/tmp/geo337-e321-architecture-four-20261024')
O = Path('/tmp/geo337-e321-architecture-adoption-20261024')
B = Path('evidence/geo337-train-20261024')
T = B / 'architecture-e321-complete'
ART = Path('geometry-core/domain-decoupling')
M = 'e321026fb9bc9bc19c54b8034af6e6eaec2857f9'
BR = 'codex/train-337-continue-20261024'
PEER = Path('/tmp/geo337-e321-architecture-peer-specials-20261024/REVIEW.json')
def H(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert H(PEER) == 'a17da5cca4d0ef704658de127f752a5a99fc483456b464b3b9675b54a0cf91f6'
assert H(I / 'RESULT.json') == 'a683fd4215d6bc08155f7506f0ec35c5568a0466b651ce4a16a177b0efc33951'
summary = json.loads((I / 'RESULT.json').read_text())
assert summary['sourceSHA'] == M and summary['sourceBeforeAfterClean']
assert summary['originalGateExits'] == [0, 0, 0] and summary['newGuardProofExits'] == [0, 1, 0]
assert summary['existingGuardCasesRetested'] == 9 and summary['manifestDelta'] == 'unchanged-937-to-937'
assert [x['path'] for x in summary['changedPriorReceiptInputs']] == ['geometry-core/kernel/source.c']
capture = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert H(capture) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('capture', capture)
cap = importlib.util.module_from_spec(spec); spec.loader.exec_module(cap)
O.mkdir()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1'); env.pop('PYTHONOPTIMIZE', None)
rec = cap.Recorder(O, env, M)
def git(*argv):
    _, stdout, _ = rec.run(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *argv],
                         cwd=R, check=True, timeout=None, source_variant='adopt reviewed K-only architecture artifacts')
    return stdout.decode().strip()
assert git('rev-parse', 'HEAD') == M and git('branch', '--show-current') == BR
assert not git('status', '--porcelain=v1')
assert shutil.disk_usage(R).free > 24 * 1024 * 1024
changed = []
for name, expected in summary['outputs'].items():
    source = I / 'new' / name
    assert H(source) == expected['rawSha256']
    target = R / ART / name
    if target.read_bytes() != source.read_bytes():
        assert target.stat().st_nlink == 1, 'shared artifact requires explicit delinking'
        target.write_bytes(source.read_bytes()); changed.append(str(ART / name))
assert sorted(changed) == sorted([str(ART / 'PRODUCT-ARCHITECTURE.md'), str(ART / 'product-architecture-receipt.json')])
target = R / T
assert not target.exists()
for label, source in [('originals', I),
                      ('original-outer', Path('/tmp/geo337-e321-architecture-four-launch-20261024')),
                      ('preparation', Path('/tmp/geo337-e321-architecture-preparation-20261024')),
                      ('peer', PEER.parent)]:
    shutil.copytree(source, target / label)
shutil.copyfile(__file__, target / Path(__file__).name)
inventory = []
for path in sorted(target.rglob('*')):
    assert not path.is_symlink()
    if path.is_file():
        inventory.append({'path': str(path.relative_to(target)), 'bytes': path.stat().st_size, 'sha256': H(path)})
cap.dump(target / 'INVENTORY.json', {'actual_execution_source': M, 'files': inventory,
        'original_gate_exits': [0, 0, 0], 'guard_phase_exits': [0, 1, 0],
        'changed_artifact_paths': changed, 'ledger_regenerated': False})
progress = R / B / 'PROGRESS.md'
old = progress.read_text()
start = old.index('## 唯一 current-state')
end = old.index('### 歷史 W 合流與架構採用', start)
historical = old[start:end].replace('## 唯一 current-state（2026-10-24；F2bbe 的 R6 已收齊終態）',
                                   '### 歷史 R6 終態（來源 F2bbe；不可移標新 K 來源）', 1)
current = '''## 唯一 current-state（2026-10-24；K provider hint 已合流，準備 R7）

目前產品／測試合流來源 **M=`e321026fb9bc9bc19c54b8034af6e6eaec2857f9`**，已一般 merge 並 push 子來源 **S=`1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`**。四個產品／測試葉與 S 完全相同；本次採用 M 實跑的衍生架構 report／receipt，採用後的可解析 SHA 才作為 R7 來源，不能把 M 或 S 的結果改標。

修正沿既有 256-entry hint 對 provider token 做乘法混合，保留完整 key／provider equality、graph 有序內容、失效／清除／fallback 與 allocation 行為。外部同場景 shadow 先確認跨 provider 碰撞；單樣本的計數不宣稱 wall 改善。原 18 方法與相關 24 方法在 S 全綠、零 skip。整刀反證 warm lookup calls 為 0→16→0、正常 exit 0/1/0；十組既有鄰接控制及 full-provider／middle-byte 對照保留。完整 child 原件已另推其 E，稍後一般合入。

架構三原裁判於 M exit 0/0/0，generic205／product18、604 inputs、334 owned／270 excluded、798 edges／0 diagnostics。九組原 guard 重新 0/1/0、neutral2 綠；manifest 937／55 與 scan bytes 不變，對前份 receipt 的 input delta 僅 K source.c。四檔原件、51 原命令流與 1755/0 獨審在 architecture-e321-complete/。本次只採用兩個實際有差的衍生檔，沒有改架構裁判或公理。

R7 原五 stage／36 交錯樣本／四 profile 尚未執行。全帳本重產、完整 native、六 browser、P52、Q38(44)、§7、P189、required-eight/PF3、readers／RC／#314／Reading A 在此新來源均 UNRUN。R6 的 N64/main1.373156>1.3、N16/base1.043458>1 與三個跨版本 stdout 差仍是歷史紅燈，必須以原門檻確認是否解除；不重抽同源樣本挑綠、不刪診斷、不改 comparator。

required CI 的既有原 failure annotation 明確是付款失敗或支出上限而未啟動，沒有正式替代接受紀錄；不以較早 run 代新 head。除了原 Linux Windows-GDI skip 外，零新增允許 skip。**目前不是 READY-TO-MERGE。**

下一步：固定本次採用 SHA，獨立 checkout 執行 R7；同時公開已完成 R5／R6 的全部原件，維持唯一 current-state，其他歷史矩陣不作目前通過證明。

'''
progress.write_text(old[:start] + current + historical + old[end:])
git('add', '-f', '--sparse', *changed, str(T), str(B / 'PROGRESS.md'))
assert all(x in changed + [str(B / 'PROGRESS.md')] or x.startswith(str(T) + '/')
           for x in git('diff', '--cached', '--name-only').splitlines())
git('diff', '--cached', '--check', '--', *changed, str(B / 'PROGRESS.md'), str(T / 'INVENTORY.json'))
git('commit', '-m', 'docs: refresh architecture receipts for provider hint mixing')
head = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:' + BR)
assert git('ls-remote', 'origin', 'refs/heads/' + BR).split()[0] == head
assert not git('status', '--porcelain=v1')
assert sorted(git('diff', '--name-only', M, head, '--', '.', ':(exclude)evidence').splitlines()) == sorted(changed)
cap.dump(O / 'RESULT.json', {'actual_execution_source': M, 'artifact_commit': head,
          'published': True, 'push_exit': 0, 'original_gate_exits': [0, 0, 0],
          'changed_non_evidence': changed, 'ledger_regenerated': False,
          'original_files': len(inventory), 'original_bytes': sum(x['bytes'] for x in inventory)})
print((O / 'RESULT.json').read_text())
