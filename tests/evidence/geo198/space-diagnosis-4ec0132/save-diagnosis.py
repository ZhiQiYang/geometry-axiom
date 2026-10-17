from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import urllib.request

root = Path('/workspace/geometry-axiom')
out = Path('/tmp/geometry-198-space-diagnosis')
result = json.loads((out / 'original/result.json').read_text())
spec = importlib.util.spec_from_file_location('identity', root / 'tests/geo246/identity.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
binary_root = Path('/tmp/geometry-198-review/browser/tmp/geometry-runtime/b9bc23103ebb114398f3')
after = identity.capture(root, [binary_root / n for n in ['core', 'bridge', 'model-base']])
identity.write(out / 'checkout-after.json', after)
before = json.loads((out / 'checkout-during.json').read_text())
assert all(before[k] == after[k] for k in ['head', 'tree', 'sources', 'tracked_diff', 'status'])
assert after['tracked_diff'] == after['status'] == []
runtime = json.loads(subprocess.check_output(['python3', 'geometry-web/runtime_version.py', '--probe', '18844'], cwd=root))
(out / 'runtime-after.json').write_text(json.dumps(runtime, indent=2))
req = urllib.request.Request('http://127.0.0.1:18844/api', data=json.dumps({'cmd': 'dump'}).encode(), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=10) as response:
    (out / 'final-native-dump.json').write_bytes(response.read())
sources = ['geometry-web/app.js', 'geometry-web/space-workspace.js', 'geometry-web/space_model_test.js']
mapping = {}
for name in sources:
    data = (root / name).read_bytes()
    gitbytes = subprocess.check_output(['git', 'show', after['head'] + ':' + name], cwd=root)
    assert data == gitbytes
    mapping[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'same_blob_as_main': subprocess.check_output(['git', 'rev-parse', 'origin/main:' + name], cwd=root) == subprocess.check_output(['git', 'rev-parse', after['head'] + ':' + name], cwd=root)}
metadata = {
    'head': after['head'], 'tree': after['tree'], 'actor': 'Codex Linux diagnosis; not WSL reviewer',
    'browser_plugin': 'Browser plugin not available; existing Chromium CDP harness used',
    'sources': mapping,
    'original': {'argv': ['node', 'geometry-web/space_model_test.js'], 'environment': {'GEOMETRY_TEST_URL': 'http://127.0.0.1:18844/', 'GEOMETRY_FEEDBACK_DIR': str(out / 'feedback'), 'GEOMETRY_CHROME': '/usr/bin/chromium', 'GEOMETRY_CHROME_FLAGS': '--no-sandbox', 'GEOMETRY_CDP_PORT': '9349', 'GEOMETRY_SPACE_TEST_DIR': str(out / 'original')}, 'exit_code': 0 if result['failed'] == 0 else 1, 'passed': result['passed'], 'failed': result['failed'], 'completed': result['completed']},
    'instrumented': {'scope': 'Original lifecycle only with click/close event observation; intentional diagnostic stop after lifecycle', 'lifecycle_passed': 18, 'aggregate_exit': 1, 'aggregate_failed': 2, 'not_a_full_space_pass': True},
    'server_broken_pipe_count': (out / 'server.log').read_text().count('BrokenPipeError'),
    'isolation': 'Owned service/profile/cache with current runtime. checkout-during capture was taken after start; process-snapshot is one observation, not a whole-run foreign census. No formal isolation proof or seven-job acceptance.',
    'original_failure': 'Retained prior 13/2 completed=false result. No same-test main failure receipt, no root cause demonstrated, and no flaky waiver.',
}
(out / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
shutil.copyfile('/tmp/geometry-198-space-diagnose.cjs', out / 'diagnose.cjs')
files = ['metadata.json', 'checkout-during.json', 'checkout-after.json', 'runtime-during.json', 'runtime-after.json', 'final-native-dump.json', 'server.log', 'diagnostic.log', 'original.log', 'diagnose.cjs', 'process-snapshot.json', 'run/result.json', 'run/fp-diagnostic.json', 'run/instrumented-harness.js', 'run/final-state.png', 'original/result.json', 'original/final-state.png']
dest = root / 'tests/evidence/geo198/space-diagnosis-4ec0132'
assert not dest.exists()
for name in files:
    p = dest / name
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out / name, p)
shutil.copyfile(__file__, dest / 'save-diagnosis.py')
manifest = {str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file()}
(dest / 'sha256.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps({'original': metadata['original'], 'files': len(manifest), 'server_broken_pipe_count': metadata['server_broken_pipe_count']}, ensure_ascii=False))
