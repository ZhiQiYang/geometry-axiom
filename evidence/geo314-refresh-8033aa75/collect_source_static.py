#!/usr/bin/env python3
"""Small AST/blob inventory only. Does not import product/tests or execute any gate."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

repo = Path('/tmp/g261-next314')
predecessor = '5c29eba30a40f20ea5c7eb8dc139e5788235d3b6'
files = ['tests/mutate.py', 'tests/mutation_bridge.py', 'tests/test_geo261_mutation_migration.py',
         'tests/test_geo314_stagger_commit.py']
trees = {p: ast.parse((repo / p).read_text(encoding='utf-8'), filename=p) for p in files}
registry = []
for statement in trees['tests/mutate.py'].body:
    values = None
    if isinstance(statement, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MUTANTS' for t in statement.targets):
        values = statement.value
    if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name) and statement.target.id == 'MUTANTS':
        values = statement.value
    if isinstance(values, ast.List):
        for call in values.elts:
            if isinstance(call, ast.Call):
                row = {k.arg: k.value.value for k in call.keywords if isinstance(k.value, ast.Constant)}
                if 'id' in row:
                    registry.append(row)
source = (repo / 'geometry-templates/woodworking/native/grid_application.c').read_text(encoding='utf-8')
rows = {r['id']: r for r in registry}
counts = json.loads((repo / 'tests/run_all.expected.json').read_text(encoding='utf-8'))['suites']
test_count = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')
                 for n in ast.walk(trees['tests/test_geo314_stagger_commit.py']))
def blob(ref, path):
    return subprocess.check_output(['git', 'rev-parse', ref + ':' + path], cwd=repo, text=True).strip()
protected = {p: {'currentBlob': blob('HEAD', p), 'predecessorBlob': blob(predecessor, p),
                  'worktreeSha256': hashlib.sha256((repo / p).read_bytes()).hexdigest(),
                  'worktreeEqualsPredecessor': (repo / p).read_bytes() == subprocess.check_output(['git', 'show', predecessor + ':' + p], cwd=repo)}
             for p in ['公理層.md', '決策佇列.md']}
current = (repo / 'current_geometry.c').read_bytes()
receipt = {
    'scope': 'static metadata only; no tests/compiler/Chrome/scanner/ledger executed',
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
    'worktreeIsCommitted': False,
    'pythonAstParsed': files,
    'registeredMutantCount': len(registry),
    'uniqueMutantCount': len(rows),
    'staggerIds': [r['id'] for r in registry if 99 <= int(r['id'][1:]) <= 121],
    'anchorCounts': {i: source.count(rows[i]['old']) for i in ['M102', 'M103', 'M105', 'M121']},
    'staggerTestMethods': test_count,
    'expectedCounts': {k: counts[k]['count'] for k in ['py:test_geo314_stagger_commit', 'py:test_contact_sources', 'py:test_host_facts_authority', 'py:test_load_residual'] if k in counts},
    'protectedFiles': protected,
    'currentGeometry': {'crlfCount': current.count(b'\r\n'), 'lfCount': current.count(b'\n'), 'loneLfCount': current.count(b'\n') - current.count(b'\r\n')},
}
out = Path('/workspace/geo314-owner-20261023/SOURCE_STATIC.json')
out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False))
