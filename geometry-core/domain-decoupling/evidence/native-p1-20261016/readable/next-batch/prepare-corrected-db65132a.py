"""Freeze original test identities from the approved immutable publication SHA."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE = 'db65132a41c4b4c815b6814784651e3980bf4f63'
HERE = Path(__file__).resolve().parent
MODULES = {
    'tests.test_geo261_native_entrypoints': 3,
    'tests.test_geo261_native_kernel': 13,
    'tests.test_geo261_native_geometry': 7,
    'tests.test_geo261_native_grid': 8,
    'tests.test_geo261_native_parameters': 7,
    'tests.test_geo261_draw_annotation': 4,
    'tests.test_geo261_native_linear': 6,
    'tests.test_geo261_native_datums': 7,
    'tests.test_geo261_native_sources': 9,
    'tests.test_geo261_wood_members': 10,
    'tests.test_geo261_wood_product': 2,
}
rows = []
for module, expected in MODULES.items():
    path = module.replace('.', '/') + '.py'
    raw = subprocess.check_output(['git', '-C', 'D:/geometry-axiom', 'show', SOURCE + ':' + path])
    tree = ast.parse(raw.decode('utf-8-sig'))
    names = [node.name + '.' + child.name for node in tree.body if isinstance(node, ast.ClassDef)
             for child in node.body if isinstance(child, ast.FunctionDef) and child.name.startswith('test_')]
    inherited = []
    if module == 'tests.test_geo261_native_kernel':
        codec = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'KernelCodec')
        if [ast.unparse(base) for base in codec.bases] != ['existing_codec.EngineeringJson']:
            raise RuntimeError('Kernel codec inheritance differs from the observed original suite')
        parent_path = 'tests/test_engineering_json.py'
        parent_raw = subprocess.check_output(['git', '-C', 'D:/geometry-axiom', 'show', SOURCE + ':' + parent_path])
        parent_class = next(node for node in ast.parse(parent_raw.decode('utf-8-sig')).body if isinstance(node, ast.ClassDef) and node.name == 'EngineeringJson')
        parent_names = ['KernelCodec.' + child.name for child in parent_class.body if isinstance(child, ast.FunctionDef) and child.name.startswith('test_')]
        names.extend(parent_names)
        inherited.append({'path': parent_path, 'sourceSha256': hashlib.sha256(parent_raw).hexdigest(), 'methodNames': parent_names})
    if len(names) != expected:
        raise RuntimeError(module + ' original static method count differs: ' + str(len(names)))
    rows.append({'module': module, 'path': path, 'sourceSha256': hashlib.sha256(raw).hexdigest(), 'methodNames': names, 'inherited': inherited, 'count': len(names)})
label = 'native-corrected-db65132a-v1'
recipe = {'source': SOURCE, 'label': label, 'modules': list(MODULES), 'module_counts': MODULES,
          'expected_tests': sum(MODULES.values()),
          'scope': 'Original three-TU entrypoint preflight first, then 35 N2a native tests, annotation4, linear/datum13, and sources/wood21. No support/guide slices and no full-suite claim.'}
legacy = {'source': SOURCE, 'label': 'parameters-legacy-db65132a-v1', 'native_label': label, 'expected_tests': 20}
for name, value in [('native-corrected-db65132a.json', recipe), ('legacy-corrected-db65132a.json', legacy),
                    ('corrected-db65132a-static-discovery.json', {'source': SOURCE, 'runtimeExecuted': False, 'modules': rows, 'totalMethods': sum(MODULES.values())})]:
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'source': SOURCE, 'originalNativeMethods': sum(MODULES.values()), 'originalLegacyMethods': 20}, indent=2))
