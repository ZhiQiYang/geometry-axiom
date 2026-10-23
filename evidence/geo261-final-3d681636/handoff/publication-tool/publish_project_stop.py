"""Publish the user-requested stage-stop handoff; no product or test execution."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

BASE = Path('/workspace/geo288-main-merge-20261023')
REPO = Path('/workspace/geometry-axiom')
F = '3d681636902371ecc528b20f51eea33e272581c9'
EXPECTED = 'a5e7c2719a7a5c3af3db49b5ca409313e5cb190f'
BRANCH = 'architecture/geo261-integration-20261016'
PREFIX = 'evidence/geo261-final-3d681636'
helper = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('capture', helper)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
out = BASE / 'project-stop-publication-details'
out.mkdir()
r = capture.Recorder(out, dict(os.environ, LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONDONTWRITEBYTECODE='1'), F)

def git(*args):
    _, stdout, _ = r.run(['git', *args], cwd=REPO, source_variant='stage-stop-metadata-only')
    return stdout.decode().strip()

assert git('branch', '--show-current') == BRANCH
assert git('rev-parse', 'HEAD') == EXPECTED
assert git('status', '--porcelain=v1', '--untracked-files=all') == ''
assert git('ls-remote', '--heads', 'origin', BRANCH).split()[0] == EXPECTED
assert all(p.startswith(PREFIX + '/') for p in git('diff', '--name-only', F, 'HEAD').splitlines())
target = REPO / PREFIX
manifest = target / 'SHA256SUMS'
old_sums = dict((line.split('  ', 1)[1], line.split('  ', 1)[0]) for line in manifest.read_text().splitlines())
for name in ('NEXT.md', 'PROGRESS.json', 'PROGRESS.md'):
    assert hashlib.sha256((target / name).read_bytes()).hexdigest() == old_sums[name]
assert hashlib.sha256((target / 'NEXT.md').read_bytes()).hexdigest() == '6c50f27dc9310900bb6b230b5e8df5df59708fa4c55ce7c5afc3c4726d2ad901'
inputs = json.loads((BASE / 'STOP_HANDOFF_INPUTS.json').read_text())
assert inputs['source_sha'] == F
next_data = (BASE / 'NEXT.md').read_bytes()
assert '待本輪最後發布回報補入' not in next_data.decode()
assert inputs['reviewed_next_sha256'] == hashlib.sha256(next_data).hexdigest()
new_names = []
for item in inputs['files']:
    name = item['path']
    assert name.startswith('handoff/') and '..' not in Path(name).parts
    dest = target / name
    assert not dest.exists(), str(dest)
    data = Path(item['source']).read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    new_names.append(name)
assert len(new_names) == len(set(new_names))
(target / 'NEXT.md').write_bytes(next_data)
(target / 'HANDOFF_INDEX.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n')
progress_path = target / 'PROGRESS.json'
progress = json.loads(progress_path.read_text())
assert progress['tested_sha'] == F
utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
progress['entries'].append({
    'utc': utc, 'label': 'stage-stopped-handoff',
    'result': '依使用者最新指示階段收尾並停止；各線來源、證據與正文已普通推送，NEXT列完整SHA。#288產品及驗收審查已接受，只剩live正文套用，仍非READY；#318三項oracle紅與#323負控制／性能／帳本紅如實保留。READY-TO-MERGE #331、READY-TO-MERGE #333，審查適用head及後續差異明列；未合併任何PR。',
    'next': '交下一位先讀NEXT及各PROGRESS再fresh-fetch審查；本代理與子代理停止新工作、測試和監看。專案尚未全部完成。',
    'archives': [], 'documents': ['NEXT.md', 'HANDOFF_INDEX.json'],
})
progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')
with (target / 'PROGRESS.md').open('a') as handle:
    handle.write(f'\n- {utc} — **stage-stopped-handoff**：已依使用者指示階段收尾並停止。接手入口：[NEXT.md](NEXT.md)，各線最終原件索引：[HANDOFF_INDEX.json](HANDOFF_INDEX.json)。#288只剩live正文，未標READY；#318／#323原紅及其餘未跑項如實保留。**READY-TO-MERGE #331**、**READY-TO-MERGE #333** 的審查適用head及限制詳見NEXT。未合併PR、未force push；專案未全部完成，不留背景測試或監看。\n')
small_names = ['NEXT.md', 'PROGRESS.json', 'PROGRESS.md', 'HANDOFF_INDEX.json'] + new_names
for name in small_names:
    old_sums[name] = hashlib.sha256((target / name).read_bytes()).hexdigest()
manifest.write_text(''.join(f'{old_sums[name]}  {name}\n' for name in sorted(old_sums)))
allowed = {f'{PREFIX}/{name}' for name in small_names + ['SHA256SUMS']}
git('add', '--sparse', '--', *sorted(allowed))
assert set(git('diff', '--cached', '--name-only').splitlines()) == allowed
# Preserve imported raw streams and historical patches verbatim. Check only newly authored metadata.
git('diff', '--cached', '--check', '--', *[f'{PREFIX}/{name}' for name in ('NEXT.md', 'PROGRESS.json', 'PROGRESS.md', 'HANDOFF_INDEX.json', 'SHA256SUMS')])
git('commit', '-m', 'Finalize project stage handoff and stop checkpoint')
git('push', 'origin', 'HEAD:refs/heads/' + BRANCH)
head = git('rev-parse', 'HEAD')
assert git('ls-remote', '--heads', 'origin', BRANCH).split()[0] == head
assert git('status', '--porcelain=v1', '--untracked-files=all') == ''
assert all(p.startswith(PREFIX + '/') for p in git('diff', '--name-only', F, 'HEAD').splitlines())
capture.dump(out / 'RESULT.json', {'head': head, 'source_sha': F, 'exit_code': 0,
    'file': PREFIX + '/NEXT.md', 'next_sha256': hashlib.sha256(next_data).hexdigest(),
    'new_acceptance_executed': False, 'stopped': True, 'commands': r.rows})
print(json.dumps({'head': head, 'file': PREFIX + '/NEXT.md', 'exit_code': 0, 'stopped': True}))
