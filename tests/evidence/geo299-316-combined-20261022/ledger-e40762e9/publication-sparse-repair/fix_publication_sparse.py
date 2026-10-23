"""Preserve the failed sparse staging attempt and unstage only its two owned entries."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/tmp/g261-next299316')
DEST = ROOT / 'tests/evidence/geo299-316-combined-20261022/ledger-e40762e9'
SOURCE = Path('/workspace/geo299316-work/publication-ledger-L')
OUT = Path('/workspace/geo299316-work/publication-sparse-repair')
assert not OUT.exists()
OUT.mkdir()
rows = []


def run(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    number = len(rows) + 1
    (OUT / (str(number) + '.stdout')).write_bytes(result.stdout)
    (OUT / (str(number) + '.stderr')).write_bytes(result.stderr)
    rows.append({'command': argv, 'cwd': str(ROOT), 'actual_process_returncode': result.returncode,
                 'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                 'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()})
    assert result.returncode == 0
    return result.stdout


expected = {'.gitignore', 'tests/mutants_results.json'}
assert set(run(['git', 'diff', '--cached', '--name-only', '-z']).decode().split('\0')) - {''} == expected
before = {name: (ROOT / name).read_bytes() for name in expected}
run(['git', 'restore', '--staged', '--', *sorted(expected)])
assert run(['git', 'diff', '--cached', '--name-only', '-z']) == b''
assert all((ROOT / name).read_bytes() == raw for name, raw in before.items())
(OUT / 'receipt.json').write_text(json.dumps({'schema': 'geo299316-sparse-publication-environment-repair/1',
    'commands': rows, 'owned_entries_only_unstaged': sorted(expected), 'worktree_bytes_unchanged': True,
    'reason': 'git add declined evidence outside sparse definition; subsequent explicit staging uses git add --sparse, without --force or ignore changes',
    'product_tests_or_assertions_changed': False}, ensure_ascii=False, indent=2) + '\n')
shutil.copy2(__file__, OUT / 'fix_publication_sparse.py')
shutil.copytree(SOURCE, DEST / 'publication-first-sparse-attempt')
shutil.copytree(OUT, DEST / 'publication-sparse-repair')
with (DEST / 'PROGRESS.md').open('a') as stream:
    stream.write('\nL 首次 publisher 在任何 commit/push 前因主工作樹 sparse 定義排除 tests/evidence 而於原 git add 退出1。原收據已保 publication-first-sparse-attempt/；只撤我方兩個暫存 index entries，工作檔 bytes不變，再以 Git 原 --sparse 精確加入本目錄。沒有 force-add、force-push、merge 或改忽略規則以外的產品判準。\n')
paths = [path for path in sorted(DEST.rglob('*')) if path.is_file() and path != DEST / 'SHA256SUMS']
(DEST / 'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(DEST).as_posix() + '\n' for path in paths))
print(json.dumps({'restored_index_entries': sorted(expected), 'worktree_bytes_unchanged': True}))
