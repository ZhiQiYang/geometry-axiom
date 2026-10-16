#!/usr/bin/env python3
"""Freeze only the parent-approved 99eeabe1 groups; static Git/AST work."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = '99eeabe11875f4d18b1bc35607cd3601a0ac3b4b'
COUNTS = {
    'tests.test_geo261_native_entrypoints': 3,
    'tests.test_geo261_model_sources': 10,
    'tests.test_geo261_wood_supports': 13,
    'tests.test_geo261_wood_supports_product': 2,
    'tests.test_geo261_native_regions': 13,
    'tests.test_geo261_regions_product': 2,
    'tests.test_geo261_wood_contacts': 10,
    'tests.test_geo261_wood_contacts_product': 1,
}
GROUPS = {
    'actual-entrypoints': list(COUNTS)[:1],
    'source-support': list(COUNTS)[1:4],
    'regions-contact': list(COUNTS)[4:],
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
recipe = {'source': SOURCE, 'label': 'native-groups-99eeabe1-v1', 'modules': list(COUNTS),
          'module_counts': COUNTS, 'groups': GROUPS,
          'group_counts': {name: sum(COUNTS[module] for module in modules) for name, modules in GROUPS.items()},
          'expected_tests': sum(COUNTS.values()),
          'scope': 'Parent-approved original source/support25 + regions/contact26 + actual CLI/model-base/bridge3; no G1/history or full-suite claim.'}
for name, value in [('recipe.json', recipe), ('static-discovery.json', {'source': SOURCE, 'modules': rows, 'runtimeExecuted': False})]:
    path = HERE / name
    if path.exists():
        raise RuntimeError('Preserve an existing prepared freeze: ' + name)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
target = HERE / 'run-native-receipt.py'
if target.exists():
    raise RuntimeError('Preserve existing runner')
shutil.copyfile(HERE.parent / 'next-batch/run-native-receipt.py', target)
print(json.dumps({'source': SOURCE, 'groups': recipe['group_counts'], 'expected_tests': recipe['expected_tests']}, indent=2))
