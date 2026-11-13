#!/usr/bin/env python3
"""Freeze parent-approved original modules from a3aeef41; static only."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = 'a3aeef41adb1bc3bb5d0da0b941342387373a238'
COUNTS = {
    'tests.test_geo261_native_entrypoints': 3,
    'tests.test_geo261_native_guides': 13,
    'tests.test_geo261_guides_product': 2,
    'tests.test_geo261_native_grid_store': 18,
    'tests.test_geo261_native_grid_product': 5,
    'tests.test_geo261_host_history': 13,
    'tests.test_geo261_wood_engineering': 12,
    'tests.test_geo261_panel_native': 10,
    'tests.test_geo261_native_sources': 9,
    'tests.test_geo261_wood_supports_product': 2,
    'tests.test_geo261_native_datums': 7,
    'tests.test_geo261_draw_annotation': 4,
}
GROUPS = {
    'actual-entrypoints': list(COUNTS)[:1],
    'new-guides': list(COUNTS)[1:3],
    'new-grid-store': list(COUNTS)[3:5],
    'new-history': list(COUNTS)[5:6],
    'new-engineering': list(COUNTS)[6:7],
    'new-panel-native': list(COUNTS)[7:8],
    'regression-source-support-datum-annotation': list(COUNTS)[8:],
}
rows = {}
for module, expected in COUNTS.items():
    path = module.replace('.', '/') + '.py'
    raw = subprocess.check_output(['git', '-C', 'D:/geometry-axiom', 'show', SOURCE + ':' + path])
    tree = ast.parse(raw, filename=path)
    names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')]
    if len(names) != expected:
        raise RuntimeError('Static method count changed: ' + module)
    rows[module] = {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'methods': names, 'count': len(names)}
recipe = {'source': SOURCE, 'label': 'native-closure-a3aeef41-v1', 'modules': list(COUNTS),
          'module_counts': COUNTS, 'groups': GROUPS,
          'group_counts': {name: sum(COUNTS[module] for module in modules) for name, modules in GROUPS.items()},
          'expected_tests': sum(COUNTS.values()),
          'scope': 'Parent-approved original new native seams73 + regression25 (including actual three-TU preflight); no full aggregate or browser claim.'}
for name, value in [('recipe.json', recipe), ('static-discovery.json', {'source': SOURCE, 'modules': rows, 'runtimeExecuted': False})]:
    path = HERE / name
    if path.exists():
        raise RuntimeError('Preserve existing freeze: ' + name)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
for name in ('run-native-receipt.py', 'exercise-native-receipt.py'):
    target = HERE / name
    if target.exists():
        raise RuntimeError('Preserve existing runner')
    shutil.copyfile(HERE.parent / 'native-next-99eeabe1' / name, target)
print(json.dumps({'source': SOURCE, 'groups': recipe['group_counts'], 'expected_tests': recipe['expected_tests']}, indent=2))
