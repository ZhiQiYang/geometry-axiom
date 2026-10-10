"""Read-only source metadata relocation review; no probes executed."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

ledger_path = Path('<workspace-path>')
out = Path('<workspace-path>')
ledger_raw = ledger_path.read_bytes()
ledger = json.loads(ledger_raw)
checks, rows, artifacts = [], [], {}
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(path):
    path = Path(path)
    data = path.read_bytes()
    artifacts[str(path)] = {'sha256': sha(data), 'bytes': len(data)}
    return data
def check(name, ok): checks.append({'check': name, 'ok': bool(ok)})
check('ledger-hash', sha(ledger_raw) == 'e675b666df85d637765f01d666fc8f53f177d1ee728fb29219c0b50b4393a1f8')
for row in ledger['rows']:
    group = row['group']
    old_path, new_path = Path(row['originalSource']['path']), Path(row['retainedSource']['path'])
    old, new = read(old_path), read(new_path)
    check(group + ':source-hashes', sha(old) == row['originalSource']['sha256'] and sha(new) == row['retainedSource']['sha256'])
    check(group + ':exact-path-only-byte-change', old.count(b"'<takeover-repository-root>'") == 1 and new == old.replace(b"'<takeover-repository-root>'", b"'<workspace-path>'", 1))
    a, b = ast.parse(old), ast.parse(new)
    old_asserts = [ast.dump(n) for n in ast.walk(a) if isinstance(n, ast.Assert)]
    new_asserts = [ast.dump(n) for n in ast.walk(b) if isinstance(n, ast.Assert)]
    check(group + ':every-assert-AST-identical', old_asserts == new_asserts)
    old_literals = [ast.get_source_segment(old.decode(), n) for n in ast.walk(a) if isinstance(n, ast.Assert)]
    new_literals = [ast.get_source_segment(new.decode(), n) for n in ast.walk(b) if isinstance(n, ast.Assert)]
    check(group + ':every-assert-source-identical', old_literals == new_literals)
    for tree in [a, b]:
        assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'REPO' for t in n.targets)]
        assert len(assignments) == 1
        assignments[0].value = ast.Constant('normalized-metadata-root')
    check(group + ':all-other-executable-AST-identical', ast.dump(a) == ast.dump(b))
    patch = read(row['patch']['path'])
    check(group + ':patch-hash-bound', sha(patch) == row['patch']['sha256'])
    changes = [line for line in patch.decode().splitlines() if line[:1] in ['-', '+'] and not line.startswith(('---', '+++'))]
    check(group + ':patch-exact-two-REPO-lines', len(changes) == 2 and all('REPO' in line for line in changes) and changes[0][0] == '-' and changes[1][0] == '+')
    siblings = []
    for name, hashes in row['retainedRelatedSources'].items():
        old_related, new_related = read(old_path.parent / name), read(new_path.parent / name)
        check(group + ':related-byte-identical:' + name, old_related == new_related and sha(old_related) == hashes['originalSHA256'] == hashes['retainedSHA256'])
        siblings.append({'name': name, 'sha256': sha(old_related)})
    repo_uses = [{'line': n.lineno, 'sourceLine': new.decode().splitlines()[n.lineno - 1]} for n in ast.walk(b) if isinstance(n, ast.Name) and n.id == 'REPO' and isinstance(n.ctx, ast.Load)]
    rows.append({'group': group, 'assertCount': len(old_asserts), 'oldSource': row['originalSource'], 'newSource': row['retainedSource'], 'relatedIdentical': siblings, 'REPOLoadUses': repo_uses})
    if group == 'cross-b':
        scripts = next(n.value for n in ast.parse(new).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCRIPTS' for t in n.targets))
        names = ast.literal_eval(scripts)
        check('cross-b:SCRIPTS-closure-complete', all((new_path.parent / name).is_file() for name in names) and set(names) == {new_path.name, *row['retainedRelatedSources']})
report = {'actor': '/root/race_review/hole_order_oracle_review', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'verdict': 'pass' if all(c['ok'] for c in checks) else 'fail', 'scope': 'Four source-only metadata root relocations; no execution or product acceptance.',
          'ledger': {'path': str(ledger_path), 'sha256': sha(ledger_raw)}, 'checks': checks, 'rows': rows, 'artifacts': artifacts,
          'semanticReview': 'All REPO load uses were read in the source identity helpers. They set git cwd, source-file hashes and relative metadata labels. They do not alter fixture commands, native operations, UI actions, expected Worlds or product assertions. Cross-B SCRIPTS includes its unchanged run wrapper and source-plan.',
          'limits': ['No browser or service run.', 'This approves source relocation identity metadata only; it does not prove actual interpreter observations or product test results.']}
p = out / 'source-metadata-relocation-independent-review.json'
p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': report['verdict'], 'checks': len(checks), 'report': str(p), 'sha256': sha(p.read_bytes()), 'assertCounts': {r['group']: r['assertCount'] for r in rows}}, ensure_ascii=False))
assert report['verdict'] == 'pass'
