#!/usr/bin/env python3
"""Freeze the five original grid product tests; static discovery only."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = 'b21334a2f5b912a876e0cf98b3cca8ae11065037'
MODULE = 'tests.test_geo261_native_grid_product'
path = MODULE.replace('.', '/') + '.py'
raw = subprocess.check_output(['git', '-C', 'D:/geometry-axiom', 'show', SOURCE + ':' + path])
tree = ast.parse(raw, filename=path)
names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')]
if len(names) != 5:
    raise RuntimeError('Frozen original method count changed')
recipe = {'source': SOURCE, 'label': 'native-grid-product-b21334a2-v1', 'modules': [MODULE],
          'module_counts': {MODULE: 5}, 'groups': {'corrected-grid-product': [MODULE]},
          'group_counts': {'corrected-grid-product': 5}, 'expected_tests': 5,
          'scope': 'Parent-approved frozen original grid product tests after a3 red receipt; no full aggregate or browser claim.'}
discovery = {'source': SOURCE, 'modules': {MODULE: {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'methods': names, 'count': len(names)}}, 'runtimeExecuted': False}
for name, value in [('recipe.json', recipe), ('static-discovery.json', discovery)]:
    target = HERE / name
    if target.exists():
        raise RuntimeError('Preserve existing freeze')
    target.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
for name in ('run-native-receipt.py', 'exercise-native-receipt.py'):
    target = HERE / name
    if target.exists():
        raise RuntimeError('Preserve existing runner')
    shutil.copyfile(HERE.parent / 'native-next-a3aeef41' / name, target)
print(json.dumps(recipe, indent=2))
