"""Adopt only the exact verified official #345 ledger; run no product cases."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
SOURCE = Path('/tmp/geometry-pr345-20261102')
M = '577b2e81967b3019352f65df5ffe6dc48eb6202f'
LEDGER = 'tests/mutants_results.json'
EXPECTED = '0be90a297b4f4b4fd5a2e60d528886845cc2c8d823e912ef3b0763ba68f7eb1c'
OFFICIAL = OUT.parent / 'extracted/mutation-complete-evidence/mutants_results.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=SOURCE)

sys.path.insert(0, str(SOURCE / 'tests'))
import mutate as mt
import mutation_bridge
import binaries
assert mt.ROOT == SOURCE and mt.RESULTS == SOURCE / LEDGER


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def identity():
    tracked = []
    # The source is a sparse checkout. Absent versioned evidence remains bound
    # to its actual M Git object; do not materialize or rewrite unrelated paths.
    objects = {}
    for entry in git('ls-tree', '-rz', '--full-tree', M).split(b'\0'):
        if entry:
            meta, name = entry.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            objects[name.decode()] = {'git_mode': mode, 'git_kind': kind, 'git_object': oid}
    for name in sorted(git('ls-files', '-z').decode().split('\0')):
        if not name:
            continue
        path = SOURCE / name
        if not path.exists() and not path.is_symlink():
            tracked.append({'path': name, 'materialized': False, **objects[name]})
            continue
        body = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        tracked.append({'path': name, 'materialized': True, 'bytes': len(body), 'sha256': sha(body), 'lf_sha256': sha(body.replace(b'\r\n', b'\n'))})
    closure = mt.Sources(SOURCE)
    native_builds = {}
    for binary in binaries.REGISTRY:
        fingerprint, inputs, command = binaries.compute_fingerprint(binary)
        native_builds[binary.name] = {'fingerprint': fingerprint, 'inputs': inputs, 'command': command}
    cache = mt.MUT_ROOT
    cache_files = [{'path': str(p.relative_to(cache)), 'sha256': sha(p.read_bytes())}
                   for p in sorted(cache.rglob('*')) if p.is_file()] if cache.exists() else []
    return {'tracked': tracked, 'non_ledger_tracked_closure_sha256': sha(json.dumps([r for r in tracked if r['path'] != LEDGER], sort_keys=True).encode()),
            'mutation_closure_sha256': closure.closure, 'mutation_source_hashes': closure.hashes,
            'mutation_table_sha256': sha(json.dumps(mt.MUTANTS, ensure_ascii=False, sort_keys=True).encode()),
            'core_oracle_sha256': mt.oracle_hash(),
            'bridge_oracle_sha256': {m['id']: mutation_bridge.oracle_hash(m, SOURCE) for m in mt.MUTANTS if m.get('binary') == 'bridge'},
            'tool_sha256': mt.tool_hash(), 'compile_sha256': mt.compile_hash(), 'native_build_inputs': native_builds,
            'selected_cache': {'path': str(cache), 'exists': cache.exists(), 'files': cache_files}}


assert git('rev-parse', 'HEAD').decode().strip() == M
assert git('status', '--porcelain') == b''
remote = json.loads((OUT / 'api/remote-before.json').read_text())
assert remote['object']['sha'] == M
assert git('ls-remote', 'origin', 'refs/heads/codex/issue214-http-fixture-20261024').decode().split()[0] == M
original = (SOURCE / LEDGER).read_bytes()
assert original == git('show', M + ':' + LEDGER)
incoming = OFFICIAL.read_bytes()
assert sha(incoming) == EXPECTED
receipt = json.loads((OUT.parent / 'mutation-verify-receipt.json').read_text())
assert receipt['exit_code'] == 0 and receipt['head'] == M and receipt['ledger_sha256'] == EXPECTED
records = json.loads(incoming)
assert len(records) == 123
assert all(row['execution']['head'] == M for row in records.values() if row['verdict'] != 'retired')
(OUT / 'committed-ledger.before.json').write_bytes(original)
before = identity()
save('identity-before.json', before)
(SOURCE / LEDGER).write_bytes(incoming)
after = identity()
save('identity-after-write.json', after)
changed = [b['path'] for b, a in zip(before['tracked'], after['tracked']) if b != a]
assert changed == [LEDGER]
assert {k: v for k, v in before.items() if k != 'tracked'} == {k: v for k, v in after.items() if k != 'tracked'}
assert git('diff', '--name-only').decode().splitlines() == [LEDGER]
command = [sys.executable, '-B', 'tests/mutate.py', '--check']
with (OUT / 'candidate-check.stdout').open('wb') as stdout, (OUT / 'candidate-check.stderr').open('wb') as stderr:
    process = subprocess.run(command, cwd=SOURCE, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=stdout, stderr=stderr)
assert (SOURCE / LEDGER).read_bytes() == incoming
after_check = identity()
assert after_check == after
save('candidate-check-receipt.json', {'command': command, 'cwd': str(SOURCE), 'exit_code': process.returncode,
     'stdout_sha256': sha((OUT / 'candidate-check.stdout').read_bytes()), 'stderr_sha256': sha((OUT / 'candidate-check.stderr').read_bytes()),
     'selected_cache': after['selected_cache'], 'cache_overrides_added': False,
     'limitation': 'Original logical freshness/receipt --check only. Selected shared cache was preserved. Downloaded binary bytes/sidecars were independently verified earlier; this check is not a new product/binary execution.'})
save('preparation-receipt.json', {'source_M': M, 'original_ledger_sha256': sha(original), 'official_ledger_sha256': EXPECTED,
     'changed_paths': changed, 'non_ledger_identity_equal': True, 'all_native_build_inputs_equal': True,
     'core_and_all_bridge_oracles_equal': True, 'source_closure_runner_tool_compile_equal': True,
     'source_execution_heads': sorted({r['execution']['head'] for r in records.values() if r['verdict'] != 'retired'}),
     'original_check_exit': process.returncode, 'shared_cache_preserved': True,
     'identity_before_sha256': sha((OUT / 'identity-before.json').read_bytes()), 'identity_after_sha256': sha((OUT / 'identity-after-write.json').read_bytes())})
print(json.dumps({'changed_paths': changed, 'before_sha256': sha(original), 'after_sha256': EXPECTED, 'original_check_exit': process.returncode,
                  'non_ledger_identity_equal': True, 'cache_path': str(mt.MUT_ROOT), 'cache_exists': mt.MUT_ROOT.exists()}, indent=2))
raise SystemExit(process.returncode)
