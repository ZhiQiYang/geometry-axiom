"""AST and exact-byte inspection only: no imports of product/test modules and no execution."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT = Path('/tmp/g261-next299316')
OUT = Path('/workspace/geo299316-work')
BASE = '4b665fae21ab63aaffb7d84f6a32d5a469ba1675'

def original(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)

def text(path):
    return (ROOT / path).read_bytes().decode('utf-8').replace('\r\n', '\n')

def mutants(source):
    result = []
    for node in ast.parse(source).body:
        value = None
        if isinstance(node, ast.Assign) and any(isinstance(v, ast.Name) and v.id == 'MUTANTS' for v in node.targets):
            value = node.value
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == 'MUTANTS':
            value = node.value
        if value is not None:
            assert isinstance(value, ast.List)
            for item in value.elts:
                assert isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == 'dict'
                fields = {}
                for field in item.keywords:
                    try:
                        fields[field.arg] = ast.literal_eval(field.value)
                    except ValueError:
                        fields[field.arg] = {'unevaluated_ast': ast.dump(field.value)}
                result.append(fields)
    assert len(result) == len({m['id'] for m in result})
    return {m['id']: m for m in result}

changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
python_files = [name for name in changed if name.endswith('.py')]
for name in python_files:
    ast.parse(text(name))
before = mutants(original('tests/mutate.py').decode())
after = mutants(text('tests/mutate.py'))
new = sorted(set(after) - set(before), key=lambda name: int(name[1:]))
assert new == ['M' + str(number) for number in range(89, 99)]
for name, item in before.items():
    assert {k: v for k, v in after[name].items() if k != 'desc'} == {k: v for k, v in item.items() if k != 'desc'}, name
anchors = []
for name, item in after.items():
    source = item.get('file', 'current_geometry.c')
    count = text(source).count(item['old'])
    anchors.append({'id': name, 'file': source, 'anchor_count': count, 'retired': item.get('retired')})
    if name in new:
        assert count == 1, (name, count)

path = 'geometry-templates/woodworking/native/contact_world.c'
old = original(path).decode().replace('\r\n', '\n')
current = text(path)
index_start = 'enum { CONTACT_ORDER_SLOTS='
index_end = 'bool wood_contact_boundary_interval('
preserved_old = old[old.index(index_start):old.index(index_end)]
preserved_new = current[current.index(index_start):current.index('bool wood_contact_boundary_edge(')]
assert preserved_old == preserved_new
world_test = text('tests/test_geo261_wood_contact_world.py')
assert 'app_contact_facts_prepare(world,placement,boundary,facts,NULL);' in world_test
assert 'adapter = function(source, "app_contact_facts_prepare")' in world_test
assert '"index->minimum[slot]<order", "index->minimum[slot]<=order"' in world_test
host_path = 'tests/geo261_host_facts_authority_harness.c'
old_host = original(host_path).decode().replace('\r\n', '\n')
new_host = text(host_path)
old_error = 'V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍'
new_error = old_error + '——定位邊 e2 [50,100] mm，低端超出 [0,50] mm'
assert old_host.replace('"' + old_error + '"', '"' + new_error + '"') == new_host

current_c = (ROOT / 'current_geometry.c').read_bytes()
assert current_c.count(b'\n') == current_c.count(b'\r\n')
manifest_path = 'geometry-core/domain-decoupling/product-architecture.json'
assert original(manifest_path) == (ROOT / manifest_path).read_bytes()
manifest = json.loads(original(manifest_path))
assert len(manifest['policy']['forbiddenIdentifiers']) == 920
expected = json.loads(text('tests/run_all.expected.json'))['suites']
test_tree = ast.parse(text('tests/run_tests.py'))
scenes = next(ast.literal_eval(n.value) for n in test_tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TESTS' for t in n.targets))
world_tree = ast.parse(world_test)
method_count = sum(isinstance(n, ast.FunctionDef) and n.name.startswith('test_') for c in world_tree.body if isinstance(c, ast.ClassDef) for n in c.body)
assert len(scenes) == expected['core:run_tests']['count'] == 166
assert method_count == expected['py:test_geo261_wood_contact_world']['count'] == 9
result = {'inspection_only': True, 'base_sha': BASE, 'python_ast_valid': python_files,
          'mutants_before': len(before), 'mutants_after_derived_from_AST': len(after), 'new_ids': new,
          'existing_mutant_definitions_preserved_except_M13_description': True, 'anchors': anchors,
          'F2_order_index_and_complete_collect_stops_exact_bytes_preserved': True,
          'F2_prepare_wrapper_and_index_equal_order_control_preserved': True,
          'F2_host_facts_harness_only_exact_V_EXTENSION_string_changed': True,
          'current_geometry_uniform_CRLF': True, 'manifest_unchanged': True,
          'manifest_policy_before': len(manifest['policy']['forbiddenIdentifiers']),
          'manifest_delta_to_recompute': {'add': ['wood_contact_boundary_edge'], 'retire': ['wood_contact_footprint_collides']},
          'core_scene_count_AST': len(scenes), 'wood_contact_world_methods_AST': method_count,
          'PENDING': 'All compiler/runtime/mutation/architecture/ledger/browser/performance verdicts remain unexecuted.'}
(OUT / 'static-inspection.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'anchors'}, ensure_ascii=False))
