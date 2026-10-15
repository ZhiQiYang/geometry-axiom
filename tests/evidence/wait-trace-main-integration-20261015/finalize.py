import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

work=Path('/tmp/geometry-wake40')
root=Path('/tmp/geometry-209-segments')
native=work/'native'
result=json.loads((native/'native.json').read_text())
tested='3642e67d974f4aa712f174a4483e4b5bc3589667'
assert result['exit']==0 and result['headBefore']==result['headAfter']==tested
assert result['trackedBeforeAfterEqual'] and result['trackedExcluded']==[]
assert json.loads((native/'expected-before.json').read_text())==json.loads((native/'expected-after.json').read_text())
stdout=(native/'native.stdout').read_text()
totals=re.search(r'合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',stdout)
assert totals and tuple(map(int,totals.groups()[:4]))==(2853,2852,0,1), totals.groups() if totals else 'missing totals'
assert '[89/89]' in stdout
with tarfile.open(native/'native-current-logs.tar.gz') as archive:
    manifest=json.loads((native/'native-log-manifest.json').read_text())
    files={m.name:m for m in archive.getmembers() if m.isfile()}
    assert set(files)=={m['path'] for m in manifest}
    for row in manifest:
        raw=archive.extractfile(files[row['path']]).read()
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    reader=json.loads(archive.extractfile('py_test_axiom_reader.json').read())
    wait=json.loads(archive.extractfile('py_test_wait_trace.json').read())
    assert reader['total']==reader['passed']==41 and reader['failed']==reader['skipped']==0
    assert wait['total']==wait['passed']==20 and wait['failed']==wait['skipped']==0
(native/'native-totals.json').write_text(json.dumps(dict(total=2853,passed=2852,failed=0,skipped=1,suiteSeconds=float(totals[5]),reader=41,waitTrace=20),indent=2)+'\n')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==tested
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root)
destination=root/'tests/evidence/wait-trace-main-integration-20261015'
assert not destination.exists()
destination.mkdir()
shutil.copytree(native,destination/'native')
endpoints=[]
for name in ('tracked-before.json','tracked-after.json'):
    path=destination/'native'/name; raw=path.read_bytes()
    endpoints.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),storedAs=name+'.gz'))
    path.with_name(name+'.gz').write_bytes(gzip.compress(raw,mtime=0));path.unlink()
(destination/'native'/'tracked-endpoint-manifest.json').write_text(json.dumps(endpoints,indent=2)+'\n')
for name in ('run_native.py','finalize.py','merge-tree.txt','expected-base.json','expected-main.json','expected-ours.json','expected-resolution.json','source-audit.json','preflight.json','author-diff-check.stdout','author-diff-check.stderr','expected-resolution-diff-check.stdout','expected-resolution-diff-check.stderr','product-pr-diff-check.stdout','product-pr-diff-check.stderr','inherited-merge-diff-check.stdout','inherited-merge-diff-check.stderr','canonical-check.stdout','canonical-check.stderr'):
    shutil.copy2(work/name,destination/name)
readme=(work/'README-draft.md').read_text().replace('待填終局。','原完整 native actual0；89 suites、2852 pass／0 fail／1具名允許Windows GDI skip，Node711/711，wall %.3f秒。\n原41題及等待追蹤20題全過。前後固定 head、%d個追蹤普通檔案SHA全同，包含expected。\n本輪%d個log成員逐件bytes／SHA核符。' % (result['seconds'],result['trackedRegularFiles'],result['currentRunLogMembers']))
(destination/'README.md').write_text(readme)
index=dict(testedCodeHead=tested,mainHead='839063b9eecbd3592f48cab5ea74f306cacc5fa3',
           deliveryCommit='See the exact delivery SHA in the PR body and delivery comment; this directory is added after the tested commit without product/test changes.',
           cloudNative=dict(executionHead=tested,formalWSL=False,exit=0,passed=2852,failed=0,skipped=1,seconds=result['seconds'],receipt='native/native.json',stdout='native/native.stdout',logs='native/native-current-logs.tar.gz'),
           formalWSL=[dict(job=name,status='unverified',executionHead=None,actualExit=None,traceReceipt=None) for name in ('native','assembly','documents','grid','canvas','space','timber')],
           legacyExcludedFromCurrentValidation=[dict(head='c54324f7c7e2e3552a8d7fe709ec219dcdaeb3ff',reason='P-119 original train; lacks B1. No current formal result is inferred.'),dict(head='fa713704aac53b40b46cb0ee4acdcbf38f6b9c59',reason='Previous B1 cloud validation before current main integration; not the current integration native.')])
(destination/'execution-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
inventory=[]
for path in sorted(destination.rglob('*')):
    if path.is_file():
        raw=path.read_bytes();inventory.append(dict(path=str(path.relative_to(destination)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
(destination/'raw-manifest.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(destination=str(destination),head=tested,files=len(inventory)+1,native=result),ensure_ascii=False))
