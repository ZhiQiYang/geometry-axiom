"""Collect audit receipts without altering tests, thresholds, or product files."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
temp = Path(os.environ['TEMP']) / 'geometry-tests/audit-20261016'
for name in ['section', 'section-retry', 'section-diagnostic']:
    source = temp / name
    if source.exists():
        shutil.copytree(source, HERE / name, dirs_exist_ok=True)

receipts = []
for logfile in sorted(HERE.glob('*.log')):
    content = logfile.read_text(encoding='utf-8-sig', errors='replace')
    for marker in ['CDP_RESULT ', 'SPACE_RESULT ']:
        matches = [line[len(marker):] for line in content.splitlines() if line.startswith(marker)]
        if matches:
            receipt = json.loads(matches[-1])
            receipt['log'] = logfile.name
            receipts.append(receipt)
for name in ['section', 'section-retry', 'section-diagnostic']:
    p = HERE / name / 'result.json'
    if p.exists():
        receipt = json.loads(p.read_text(encoding='utf-8-sig'))
        receipt.update({'schema': 'section-audit-receipt/1', 'log': name + '.log',
                        'passedAssertions': len(receipt.get('results', [])),
                        'failedAssertions': 0 if receipt.get('ok') else 1})
        receipts.append(receipt)

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

state = {'schema': 'geometry-user-flow-audit/1', 'head': git('rev-parse','HEAD'),
         'originMain': git('rev-parse','origin/main'),
         'aheadBehind': git('rev-list','--left-right','--count','HEAD...origin/main'),
         'receipts': receipts,
         'notes': ['Assertion counts are not user workflow counts.',
                   'Failed and incomplete attempts are retained.',
                   'No product source, original harness, SSOT, or golden thresholds changed.']}
(HERE/'receipts.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# 本次執行結果', '', '所有數字都是測試斷言，不能相加當作使用者流程數。失敗／中斷的嘗試保留在表中。', '',
         '| 執行 | 範圍 | 完成 | 通過 | 失敗 |', '|---|---|---:|---:|---:|']
for r in receipts:
    scope = r.get('scope', {})
    filters = scope.get('filters', [])
    mode = ', '.join(filters) or scope.get('mode', '斷面桌面＋手機完整驗收')
    lines.append(f"| [{r['log']}]({r['log']}) | {mode} | {'是' if r.get('completed') else '**否**'} | {r.get('passedAssertions',r.get('passed',0))} | {r.get('failedAssertions',r.get('failed',0))} |")
lines += ['', '## 解讀界限', '',
          '- `cdp.log`：Windows＋WSL bridge 的固定等待在六面建立尚未完成時取樣；不以此判定六面功能失敗。',
          '- `cdp-wsl.log`：WSL 服務多次 API 逾時，未完成；不作全套通過證據。',
          '- `cdp-native.log`：本機 MSVC 新編 bridge／model-base；各 section 收據見下。',
          '- 主回歸收據的 1 筆瀏覽器例外是 P38 刻意觸發的 `fb-auto-probe`；log 標為 EXPECTED EXCEPTION，並通過自動回報驗收。',
          '- 空間 full suite 與角材、歷史、延遲回應專項為不同 scope，部分 setup／字級檢查重複。',
          '- `infinite-face.log` 的 9 項也包含於主回歸 P71（網格套件間接呼叫）；獨立重跑屬重複驗證，不另算新增覆蓋。',
          '- 保存重開兩次在找子線時中斷，沒有完成保存重開階段，不能解讀成資料丟失。',
          '- 斷面完整驗收在桌面歷史後的更新 3D 中斷；後續手機與完整 .gcanvas 驗收未執行。',
          '- 斷面測試使用實際下載 fallback，原生 OS 保存對話框被測試明確停用；不構成原生檔案視窗驗收。',
          '- Native build 成功，見 [native-build.log](native-build.log)；不是沿用舊二進位。',
          '- 人工 `.scene` 下載與當下 dump 逐字一致，見 [manual-export-check.json](manual-export-check.json)。',
          '', '## 全套 CDP 的 section 收據', '']
native = next((r for r in receipts if r['log']=='cdp-native.log'), None)
if native:
    lines += ['| Section | 通過 | 失敗 |', '|---|---:|---:|']
    for section, passed in native.get('sections', {}).items():
        lines.append(f"| {section} | {passed} | {native.get('sectionsFailed',{}).get(section,0)} |")
    lines += ['', '```json', json.dumps(native.get('goldenCompare'), ensure_ascii=False, indent=2), '```']
else:
    lines += ['執行尚未產生完成／失敗收據，不能宣稱全套完成。']
lines += ['', '完整機器收據：[receipts.json](receipts.json)。', '']
(HERE/'TEST-RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
manifest = {}
for p in sorted(HERE.rglob('*')):
    if p.is_file() and p.name not in ['sha256.json']:
        manifest[p.relative_to(HERE).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
(HERE/'sha256.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'receipts':len(receipts),'cdpNativeCompleted':bool(native and native.get('completed')),'files':len(manifest)}, ensure_ascii=False))
