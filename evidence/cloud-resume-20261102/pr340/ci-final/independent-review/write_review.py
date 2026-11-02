import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
DATA = OUT.parent
SOURCE = Path('/tmp/geometry-pr340-20261102')
SNAPSHOT = DATA / 'api/20261102T033519Z'
HEAD = 'b3a248607d7eb68d3167abbb926cf491d9b35a26'
MERGE = 'fc1c9f565a2e15660e931b3884dca2220cb1b7b2'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda path: json.loads(path.read_text())
git = lambda *args: subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()
assert git('rev-parse', 'HEAD') == HEAD
assert git('rev-parse', HEAD+'^{tree}') == git('rev-parse', MERGE+'^{tree}')
assert git('show', '-s', '--format=%P', MERGE).split() == ['5775a9e9e46bca801a9a70aaeafcdab9f597bc4d', HEAD]
assert git('status', '--porcelain') == ''

artifacts = []
for kind, run_id in [('integration', 41382015317), ('mutation', 41382015277)]:
    manifest_path = SNAPSHOT / (kind+'-artifacts.json')
    for artifact in load(manifest_path)['artifacts']:
        archive = DATA / 'official-zips' / f"{artifact['id']}-{artifact['name']}.zip"
        assert artifact['workflow_run']['id'] == run_id
        assert artifact['workflow_run']['head_sha'] == HEAD
        assert artifact['digest'] == 'sha256:' + sha(archive.read_bytes())
        members = []
        with zipfile.ZipFile(archive) as opened:
            assert len(opened.namelist()) == len(set(opened.namelist()))
            for info in opened.infolist():
                rel = Path(info.filename)
                assert not rel.is_absolute() and '..' not in rel.parts
                assert (info.external_attr >> 16) & 0o170000 != 0o120000
                if info.is_dir():
                    continue
                raw = opened.read(info.filename)
                extracted = DATA / 'extracted' / artifact['name'] / info.filename
                assert raw == extracted.read_bytes()
                members.append({'member': info.filename, 'sha256': sha(raw), 'bytes': len(raw)})
        artifacts.append({'kind': kind, 'run_id': run_id, 'id': artifact['id'], 'name': artifact['name'],
                          'official_digest': artifact['digest'], 'zip_sha256': sha(archive.read_bytes()),
                          'api_file_sha256': sha(manifest_path.read_bytes()), 'members': members})

report = load(OUT / 'independent-native-browser-check.json')
native = load(DATA / 'native-reverify-receipt.json')
assert native['sourceHead'] == HEAD and native['executionHead'] == MERGE
assert native['exit_code'] == 0 and native['official_reaggregation_equal']
assert native['summary'] == report['native_complete']
assert (DATA / 'native-reverified.json').read_bytes() == (DATA / 'extracted/native-complete-coverage/native-complete.json').read_bytes()
for stream in ['stdout', 'stderr']:
    assert native[stream+'_sha256'] == sha((DATA / ('native-reverify.'+stream)).read_bytes())
architecture = load(DATA / 'architecture-audit.json')
assert architecture['sourceHead'] == HEAD and architecture['run_id'] == 41382015277 and architecture['exit_code'] == 0
mutation = load(DATA / 'mutation-shard-audit.json')
assert mutation['head'] == HEAD and mutation['run_id'] == 41382015277
assert mutation['complete'] is False and mutation['downloaded_shards'] == 4

receipt = {'passed': True, 'scope': 'Independent downloaded ZIP/extracted/raw native and completed-browser audit; read-only Git metadata; no product tests or binaries executed.',
           'pr_head': HEAD, 'execution_commit': MERGE, 'execution_tree': git('rev-parse', MERGE+'^{tree}'),
           'source_clean': True, 'official_zip_count': len(artifacts), 'official_zip_digests_and_extracted_bytes_equal': True,
           'native_original_aggregate_byte_equal': True, 'native_browser_report_sha256': sha((OUT / 'independent-native-browser-check.json').read_bytes()),
           'parent_receipts': {name: sha((DATA / name).read_bytes()) for name in ['artifact-byte-audit.json','native-reverify-receipt.json','architecture-audit.json','mutation-shard-audit.json']},
           'audit_scripts': {path.name: sha(path.read_bytes()) for path in OUT.glob('*.py')},
           'pending_browser': report['pending_browser'], 'all_browser_complete': report['all_browser_complete'],
           'mutation_complete': mutation['complete'], 'artifacts': artifacts}
(OUT / 'independent-envelope-check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
browser = ', '.join(f"{row['name']}: {row['passed']}/0" for row in report['browser'])
text = f'''#340 獨立核收（固定 source {HEAD}）

真 GitHub execution merge `{MERGE}`，tree `{receipt['execution_tree']}` 與 source HEAD 完全相同；父提交是 `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` 與本 head。核對時 source 工作目錄乾淨。

原始 native 230 suites 恰好一次，三片 77/76/77，5340 計數、5339 pass、1 指定 GDI skip、0 failed。194 份 Python unittest 原始輸出及 32 份 Node log 已逐項比對。當前 source AST registry、expected 數量與雜湊、timing profile 與分片配置均相符；原聚合工具收據與官方 aggregate 逐 byte 相同。coverage 負控制原件為 0/1/0，移除 c:integrity 產生指定測試的真 AssertionError、無 error/skip。

已完成 browser 原始 assertion 與結構收據一致：{browser}。canvas 仍 in_progress，沒有當作完成。

獨立重算 {len(artifacts)} 個官方 ZIP SHA-256，全部等於 API digest、固定 head/run，且所有解壓檔案逐 byte 等於 ZIP member；無重複名稱、逃逸路徑或 symlink。父 native/architecture 收據的 head/run/原件雜湊正確。mutation 目前只有四個 core shard、70 筆，父收據正確標 complete=false；bridge 及完整 aggregate 仍待核。

未發現目前已核範圍的新阻擋；這不是整輪 CI 的終態綠燈。此處僅讀既存 API/ZIP/log/source/Git metadata，沒有網路請求、產品 suite、ELF 執行或 source/PR 寫入。
'''
(OUT / 'independent-review.md').write_text(text)
print(json.dumps({key:receipt[key] for key in ['passed','official_zip_count','all_browser_complete','mutation_complete','source_clean']}))
