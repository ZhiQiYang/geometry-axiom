#!/usr/bin/env python3
"""Static count and exact-target preflight of the original PF-3 referee."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = 'a3aeef41adb1bc3bb5d0da0b941342387373a238'


def read(path):
    return subprocess.check_output(['git', '-C', 'D:/geometry-axiom', 'show', SOURCE + ':' + path])


modules = ['tests.test_panel_fill_layout', 'tests.test_panel_fill_host', 'tests.test_panel_fill_support']
counts, hashes = {}, {}
for module in modules:
    path = module.replace('.', '/') + '.py'
    raw = read(path)
    counts[module] = sum(isinstance(node, ast.FunctionDef) and node.name.startswith('test_') for node in ast.walk(ast.parse(raw)))
    hashes[path] = hashlib.sha256(raw).hexdigest()
driver_path = 'tests/pf3_mutation_check.py'
driver = read(driver_path)
tree = ast.parse(driver)
names = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in ('HOST', 'SOURCE'):
            names[name] = ast.literal_eval(node.value)
        if name == 'CASES':
            cases_node = node.value


class NamedPaths(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id not in names:
            raise RuntimeError('Unexpected dynamic case input')
        return ast.Constant(names[node.id])


cases = ast.literal_eval(NamedPaths().visit(cases_node))
if len(cases) != 19 or len({case[0] for case in cases}) != 19:
    raise RuntimeError('Original PF-3 mutation inventory changed')
targets = []
for name, changes, selection, marker in cases:
    for path, before, after in changes:
        raw = read(path)
        count = raw.count(before.encode())
        if count != 1:
            raise RuntimeError('Mutation target does not match once: ' + name)
        targets.append({'id': name, 'path': path, 'before': before, 'after': after, 'matchCount': count,
                        'sourceSha256': hashlib.sha256(raw).hexdigest(), 'selection': selection, 'requiredMarker': marker})
hashes[driver_path] = hashlib.sha256(driver).hexdigest()
recipe = {'source': SOURCE, 'label': 'pf3-regressions-a3aeef41-v1', 'modules': modules[:2],
          'module_counts': {name: counts[name] for name in modules[:2]}, 'expected_tests': sum(counts[name] for name in modules[:2]),
          'mutation_cases': 19, 'mutation_positive_tests_each': counts[modules[2]], 'original_source_sha256': hashes,
          'mutation_driver': driver_path, 'mutation_targets': targets,
          'scope': 'Original PF-2 layout and host regressions plus unchanged PF-3 referee baseline20/19 mutations/restored20. No duplicate separate support run, full aggregate or browser claim.'}
if counts[modules[2]] != 20:
    raise RuntimeError('PF-3 original positive count changed')
target = HERE / 'recipe.json'
if target.exists():
    raise RuntimeError('Preserve existing recipe')
target.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'source': SOURCE, 'counts': counts, 'mutations': 19, 'exact_targets': len(targets)}, indent=2))
