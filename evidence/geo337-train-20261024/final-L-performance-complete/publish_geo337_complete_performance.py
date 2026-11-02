"""發布已獨審的原件；不執行產品、不改原收據、不物化第二份 tar。"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, shutil, sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--manifest-sha256', required=True)
a = p.parse_args()
R = Path('/workspace/geometry-axiom')
O = Path('/workspace/geo337-complete-performance-publication-20261024')
B = Path('evidence/geo337-train-20261024')
T = B / 'final-L-performance-complete'
L = '7af8c5d80d34cb4f49d01ba67deb78a3a6d725db'
BRANCH = 'codex/train-337-continue-20261024'
GATES = {'p52', 'p189', 'p189-timing', 'geo323', 'memo'}
ROOTS = [Path('/workspace/train337-final-performance-collection-preparation'),
         Path('/workspace/train337-canvas-peer-resume')]

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

assert not sys.flags.optimize
assert re.fullmatch('[0-9a-f]{64}', a.manifest_sha256)
assert digest(a.manifest) == a.manifest_sha256
m = json.loads(a.manifest.read_text())
assert m['source_sha'] == L and re.fullmatch('[0-9a-f]{40}', m['expected_head'])
assert m['independent_actual_reviews_complete'] is True
assert set(m['archives']) == GATES
files = m['files']
assert len({r['destination'] for r in files}) == len(files)
archives = {}
raw_pins = {}
for row in files:
    source, target = Path(row['source_path']), Path(row['destination'])
    assert source.is_absolute() and any(source.is_relative_to(root) for root in ROOTS)
    assert source.resolve() == source
    assert not any(x.is_symlink() for x in [source, *source.parents])
    assert source.is_file() and source.stat().st_size == row['bytes']
    assert digest(source) == row['sha256']
    assert not target.is_absolute() and '..' not in target.parts
    assert target.is_relative_to(T / row['gate']) and row['gate'] in GATES
    assert row['role'] in {'archive', 'metadata'}
    if row['role'] == 'archive':
        assert row['gate'] not in archives and source.name.endswith('.tar.gz')
        assert target.name == source.name
        archives[row['gate']] = row
    raw_pins[str(target)] = row['sha256']
assert set(archives) == GATES
for gate, row in archives.items():
    package = json.loads((Path(row['source_path']).parent / 'PACKAGE.json').read_text())
    assert package['source_sha'] == L and package['gate'] == gate
    assert package['all_selected_original_bytes_roundtrip'] is True
    assert package['subject_executions'] == 0 and package['original_elf_files_retained'] is True
    assert package['archive']['sha256'] == row['sha256'] == m['archives'][gate]['sha256']
    assert package['archive']['bytes'] == row['bytes'] == m['archives'][gate]['bytes']
    assert package['archive']['members'] == m['archives'][gate]['members']

progress = Path(m['progress_draft'])
assert progress.is_file() and not progress.is_symlink()
assert digest(progress) == m['progress_draft_sha256']
capture = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
assert digest(capture) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec = importlib.util.spec_from_file_location('cap', capture)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
O.mkdir()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
env.pop('PYTHONOPTIMIZE', None)
rec = c.Recorder(O, env, L)
free_before = shutil.disk_usage(R).free
required_free = 2 * sum(r['bytes'] for r in files if r['role'] == 'archive')
required_free += sum(r['bytes'] for r in files if r['role'] == 'metadata') + 16 * 1024 * 1024
c.dump(O / 'SPACE_PREFLIGHT.json', dict(free_before=free_before,
       required_free=required_free, archive_worktree_copies_created=False,
       scope='保守預留loose blob與push pack；這是發布資源守門，不是產品門檻。'))
assert free_before >= required_free

def git(*args):
    row, out, err = rec.run(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args],
                           cwd=R, timeout=None, check=False,
                           source_variant='complete-original-performance-evidence-publication')
    assert row['actual_process_returncode'] == 0, (args, err)
    return out.decode().strip()

assert git('rev-parse', 'HEAD') == m['expected_head']
assert git('branch', '--show-current') == BRANCH
assert not git('status', '--porcelain=v1', '--untracked-files=all')
assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == m['expected_head']
assert digest(R / B / 'PROGRESS.md') == m['progress_before_sha256']
assert not (R / T).exists()
allowed = set(raw_pins)
plain = []
for row in files:
    source, target = Path(row['source_path']), Path(row['destination'])
    assert not (R / target).exists()
    (R / target).parent.mkdir(parents=True, exist_ok=True)
    if row['role'] == 'archive':
        blob = git('hash-object', '-w', '--', str(source))
        assert re.fullmatch('[0-9a-f]{40}', blob)
        git('update-index', '--add', '--cacheinfo', '100644', blob, str(target))
        git('update-index', '--skip-worktree', str(target))
        assert not (R / target).exists() and digest(source) == row['sha256']
    else:
        shutil.copyfile(source, R / target)
        assert digest(R / target) == row['sha256']
        plain.append(str(target))
for source, target in [(a.manifest, T / 'PUBLICATION_MANIFEST.json'),
                       (Path(__file__), T / Path(__file__).name),
                       (progress, B / 'PROGRESS.md')]:
    shutil.copyfile(source, R / target)
    plain.append(str(target))
    allowed.add(str(target))
git('add', '-f', '--sparse', '--', *plain)
assert set(git('diff', '--cached', '--name-only').splitlines()) == allowed
row, out, err = rec.run(['git', 'diff', '--cached', '--check'], cwd=R, timeout=None,
                        check=False, source_variant='verbatim-original-format-check')
if row['actual_process_returncode']:
    assert row['actual_process_returncode'] == 2 and not err
    excluded = set()
    for line in out.decode().splitlines():
        match = re.match(r'(.+):\d+: (.+)', line)
        if not match:
            continue
        name, message = match.groups()
        assert name in raw_pins and message in {'trailing whitespace.', 'new blank line at EOF.'}
        assert digest(R / name) == raw_pins[name]
        excluded.add(name)
    assert excluded
    c.dump(O / 'VERBATIM_ORIGINAL_FORMAT_EXCLUSIONS.json',
           {'original_exit': 2, 'paths': {n: raw_pins[n] for n in sorted(excluded)}})
    git('diff', '--cached', '--check', '--', '.', *[':(exclude)' + n for n in sorted(excluded)])
git('commit', '-m', 'docs: publish complete final performance acceptance evidence')
head = git('rev-parse', 'HEAD')
git('push', 'origin', 'HEAD:' + BRANCH)
assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == head
assert not git('status', '--porcelain=v1', '--untracked-files=all')
result = dict(source_sha=L, previous_evidence_head=m['expected_head'], evidence_head=head,
              published=True, push_exit=0, complete_raw_archives_published=sorted(GATES),
              original_product_exits_unchanged=True, product_tests_executed=0,
              publication_manifest_sha256=a.manifest_sha256, prbody_unchanged=True,
              free_before=free_before, free_after=shutil.disk_usage(R).free)
c.dump(O / 'RESULT.json', result)
print(json.dumps(result))
