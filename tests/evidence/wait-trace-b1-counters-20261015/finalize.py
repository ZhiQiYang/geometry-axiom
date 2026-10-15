import hashlib
import gzip
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

work = Path('/tmp/geometry-wake38')
root = Path('/tmp/geometry-209-segments')
native = work / 'native'
result = json.loads((native/'native.json').read_text())
assert result['exit'] == 0, result
assert result['headBefore'] == result['headAfter'] == 'fa713704aac53b40b46cb0ee4acdcbf38f6b9c59'
assert result['trackedBeforeAfterEqual']
stdout=(native/'native.stdout').read_text()
totals=re.search(r'合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',stdout)
assert totals and tuple(map(int,totals.groups()[:4])) == (2806,2805,0,1), totals.groups() if totals else 'missing totals'
assert '[89/89]' in stdout
(native/'native-totals.json').write_text(json.dumps(dict(total=2806,passed=2805,failed=0,skipped=1,suiteSeconds=float(totals[5])),indent=2)+'\n')
before = json.loads((native/'expected-before.json').read_text())
after = json.loads((native/'expected-after.json').read_text())
changes = {k:[before['suites'].get(k),after['suites'].get(k)] for k in set(before['suites'])|set(after['suites'])
           if before['suites'].get(k)!=after['suites'].get(k)}
assert set(changes) == {'py:test_wait_trace'}, changes
assert changes['py:test_wait_trace'][0]['count'] == 19 and changes['py:test_wait_trace'][1]['count'] == 20
old = subprocess.check_output(['git','show',result['headBefore']+':tests/run_all.expected.json'],cwd=root)
new, count = re.subn(rb'("py:test_wait_trace":\s*\{[^{}]*"count":\s*)19',rb'\g<1>20',old)
assert count == 1 and json.loads(new) == after
(root/'tests/run_all.expected.json').write_bytes(new)
(native/'expected-audit.json').write_text(json.dumps(dict(changes=changes,sameSuiteKeys=True,onlyOneCountChanged=True,
  formattingPreserved=True,generatedSha256=hashlib.sha256(json.dumps(after,ensure_ascii=False,indent=1).encode()+b'\n').hexdigest(),
  committedCandidateSha256=hashlib.sha256(new).hexdigest()),ensure_ascii=False,indent=2)+'\n')

def verify_archive(path, manifest):
    with tarfile.open(path) as archive:
        files = {m.name:m for m in archive.getmembers() if m.isfile()}
        assert set(files)=={r['path'] for r in manifest}
        for row in manifest:
            raw=archive.extractfile(files[row['path']]).read()
            assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
verify_archive(native/'native-current-logs.tar.gz',json.loads((native/'native-log-manifest.json').read_text()))
matrix = work/'collector-matrix'
manifest=[]
with tarfile.open(work/'collector-matrix.tar.gz','w:gz') as archive:
    for path in sorted(matrix.rglob('*')):
        if path.is_file():
            raw=path.read_bytes(); name=str(path.relative_to(matrix))
            manifest.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            archive.add(path,arcname=name)
verify_archive(work/'collector-matrix.tar.gz',manifest)
(work/'collector-matrix-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

destination=root/'tests/evidence/wait-trace-b1-counters-20261015'
assert not destination.exists()
destination.mkdir()
for name in ('b1','native'):
    shutil.copytree(work/name,destination/name)
endpoints=[]
for name in ('tracked-before.json','tracked-after.json'):
    path=destination/'native'/name
    raw=path.read_bytes()
    endpoints.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),storedAs=name+'.gz'))
    path.with_name(name+'.gz').write_bytes(gzip.compress(raw,mtime=0))
    path.unlink()
(destination/'native'/'tracked-endpoint-manifest.json').write_text(json.dumps(endpoints,indent=2)+'\n')
for name in ('collector-matrix.tar.gz','collector-matrix-manifest.json','collector_matrix.py','run_native.py','finalize.py'):
    shutil.copy2(work/name,destination/name)
shutil.copy2(matrix/'matrix.json',destination/'collector-matrix.json')
readme=(work/'README-draft.md').read_text()
readme=readme.replace('tracked-before.json`／`tracked-after.json','tracked-before.json.gz`／`tracked-after.json.gz')
readme=readme.replace('是測試兩端的逐檔 SHA，','是 gzip 保存的原始兩端逐檔 SHA（解壓後 bytes／SHA 在 tracked-endpoint-manifest.json），')
readme=readme.replace('待填終局。', '原完整 native 終局 actual0；89 suites、2805 pass／0 fail／1具名允許 Windows GDI skip，Node711/711；wall %.3f秒。\n前後固定 head、%d 個追蹤普通檔 SHA 一致（排除 expected），%d 個本輪 log 成員逐件核符。\n' % (result['seconds'],result['trackedRegularFiles'],result['currentRunLogMembers']))
(destination/'README.md').write_text(readme)
inventory=[]
for path in sorted(destination.rglob('*')):
    if path.is_file():
        raw=path.read_bytes()
        inventory.append(dict(path=str(path.relative_to(destination)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
(destination/'raw-manifest.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(destination=str(destination),native=result,censusChanges=changes,files=len(inventory)+1),ensure_ascii=False))
