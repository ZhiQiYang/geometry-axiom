#!/usr/bin/env python3
"""Freeze the parent's corrected coherent candidate; no product execution."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = '6f1fd92f6886d6512c355baba4435e297b4e9664'
COUNTS = {
    'tests.test_geo261_native_entrypoints': 3,
    'tests.test_geo261_native_candidate': 17,
    'tests.test_geo261_host_candidate': 17,
    'tests.test_geo261_native_placements': 12,
    'tests.test_geo261_domain_product': 9,
    'tests.test_geo261_candidate_product': 11,
    'tests.test_geo261_staged_candidate_graph': 7,
    'tests.test_geo261_wood_assembly': 13,
    'tests.test_geo261_wood_section_profile': 12,
}
GROUPS = {
    'actual-entrypoints': list(COUNTS)[:1],
    'kernel-candidate': list(COUNTS)[1:2],
    'host-candidate': list(COUNTS)[2:3],
    'native-placements': list(COUNTS)[3:4],
    'domain-product': list(COUNTS)[4:5],
    'candidate-product': list(COUNTS)[5:6],
    'staged-candidate-graph': list(COUNTS)[6:7],
    'wood-assembly': list(COUNTS)[7:8],
    'wood-section-profile': list(COUNTS)[8:9],
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
recipe = {'source': SOURCE, 'label': 'native-candidate-6f1fd92f-v1', 'modules': list(COUNTS),
          'module_counts': COUNTS, 'groups': GROUPS,
          'group_counts': {name: sum(COUNTS[module] for module in modules) for name, modules in GROUPS.items()},
          'expected_tests': sum(COUNTS.values()),
          'scope': 'Parent-approved original candidate/placement/domain/staged/assembly/section groups98 plus actual three-entrypoint preflight3. No full aggregate, section mutation or browser claim.'}
assert recipe['expected_tests'] == 101
for name, value in [('recipe.json', recipe), ('static-discovery.json', {'source': SOURCE, 'modules': rows, 'runtimeExecuted': False})]:
    path = HERE / name
    if path.exists():
        raise RuntimeError('Preserve existing freeze: ' + name)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
for name in ('run-native-receipt.py', 'exercise-native-receipt.py'):
    target = HERE / name
    if target.exists():
        raise RuntimeError('Preserve existing runner')
    shutil.copyfile(HERE.parent / 'native-next-b21334a2' / name, target)
print(json.dumps({'source': SOURCE, 'groups': recipe['group_counts'], 'expected_tests': recipe['expected_tests']}, indent=2))
