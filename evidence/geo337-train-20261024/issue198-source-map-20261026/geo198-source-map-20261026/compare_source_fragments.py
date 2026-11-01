from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).parent
GIT = ['git', '-C', '/dev/shm/geometry-axiom-geo337-20261025/publisher-source']
REFS = {
    'base196': '635dd86ee368579aec444fb3ba16e48bccf4877e',
    'pr202': '137427563de2e94e41d067282266c232f176f0d8',
    'train291': 'e8eb1da51f3b21df15869338a7e36e76e584ff9e',
    'main': '405f8c5e1a637a16cbe47470faf5ae1fa02b8676',
}
def sha(b):
    return hashlib.sha256(b).hexdigest()

commands = []
def blob(ref, path):
    argv = GIT + ['show', ref + ':' + path]
    p = subprocess.run(argv, cwd='/tmp', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commands.append({'argv': argv, 'cwd': '/tmp', 'exit_code': p.returncode,
                     'stdout_bytes': len(p.stdout), 'stdout_sha256': sha(p.stdout),
                     'stderr': p.stderr.decode(errors='replace')})
    assert p.returncode == 0, commands[-1]
    return p.stdout

def c_function(data, name):
    pattern = rb'^static [^\r\n]+\b' + name.encode() + rb'\('
    match = re.search(pattern, data, re.M)
    assert match, name
    end = re.search(rb'^}\r?\n', data[match.start():], re.M)
    assert end, name
    raw = data[match.start(): match.start() + end.end()]
    return {'line': data[:match.start()].count(b'\n') + 1, 'raw_sha256': sha(raw),
            'lf_sha256': sha(raw.replace(b'\r\n', b'\n')), 'bytes': len(raw), 'text': raw.decode()}

output = {'scope': 'static fragment identity only; no runtime or full dependency-closure claim',
          'refs': REFS, 'c': {}, 'bridge_methods': {}, 'scene_specs': {}, 'fixtures': {}, 'commands': commands}
for name, ref in REFS.items():
    data = blob(ref, 'current_geometry.c')
    output['c'][name] = {'source_sha256': sha(data),
                         'classify_rect_outline': c_function(data, 'classify_rect_outline')}
    if name == 'base196':
        continue
    native = blob(ref, 'tests/test_core_integrity.c')
    output['c'][name]['native_counterexamples'] = c_function(native, 'test_rect_outline_counterexamples')
    bridge = blob(ref, 'tests/test_reference_contract.py')
    tree = ast.parse(bridge)
    lines = bridge.decode().splitlines(keepends=True)
    output['bridge_methods'][name] = {
        n.name: {'line': n.lineno, 'end_line': n.end_lineno,
                 'sha256': sha(''.join(lines[n.lineno-1:n.end_lineno]).encode())}
        for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and
        (n.name.startswith('test_rect_outline_') or n.name in ['projection_fixture', 'notch_projection_fixture'])
    }
    runner = blob(ref, 'tests/run_tests.py')
    rt = ast.parse(runner)
    tests = next(ast.literal_eval(n.value) for n in rt.body if isinstance(n, ast.Assign) and
                 any(isinstance(t, ast.Name) and t.id == 'TESTS' for t in n.targets))
    output['scene_specs'][name] = [t for t in tests if t['scene'] in
                                  ['_ax_r7_notch_disconnected.scene', '_ax_r7_ridge_crossing.scene', '_ax_r7_ridge_strip.scene']]
    output['fixtures'][name] = {}
    for path in ['_ax_r7_notch_disconnected.scene', '_ax_r7_ridge_crossing.scene', '_ax_r7_ridge_strip.scene']:
        raw = blob(ref, path)
        output['fixtures'][name][path] = {'sha256': sha(raw), 'bytes': len(raw)}

names = ['pr202', 'train291', 'main']
output['equalities'] = {
    'classify_function_raw_all_three': len({output['c'][n]['classify_rect_outline']['raw_sha256'] for n in names}) == 1,
    'classify_function_lf_all_three': len({output['c'][n]['classify_rect_outline']['lf_sha256'] for n in names}) == 1,
    'native_counterexample_function_raw_all_three': len({output['c'][n]['native_counterexamples']['raw_sha256'] for n in names}) == 1,
    'bridge_method_bodies_all_three': all({k: v['sha256'] for k,v in output['bridge_methods'][n].items()} ==
                                         {k: v['sha256'] for k,v in output['bridge_methods']['pr202'].items()} for n in names),
    'scene_specs_all_three': all(output['scene_specs'][n] == output['scene_specs']['pr202'] for n in names),
    'fixtures_all_three': all(output['fixtures'][n] == output['fixtures']['pr202'] for n in names),
}
before = json.loads((ROOT/'original-before-probe/stdout.bin').read_bytes())
output['base_probe_source_hash_matches_base196_blob'] = before['identity']['source_sha256'] == output['c']['base196']['source_sha256']
(ROOT/'SOURCE_FRAGMENT_IDENTITY.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'exit': 0, 'equalities': output['equalities'],
                  'base_probe_source_hash_matches_base196_blob': output['base_probe_source_hash_matches_base196_blob'],
                  'bridge_method_counts': {k: len(v) for k,v in output['bridge_methods'].items()},
                  'memory_scope': 'read selected Git blobs only, no imports from repo, no native, no fixture execution'}, ensure_ascii=False))
