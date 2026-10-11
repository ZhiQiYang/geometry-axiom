"""Prove K2a M01/M03 in Chromium by replacing only the served workspace JS."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
out = Path(tempfile.gettempdir()) / 'k2a-browser-mutants'
out.mkdir(exist_ok=True)
command = ['node', str(root / 'tests/k2a_drafts_browser.cjs')]
if os.environ.get('GEOMETRY_ISOLATED_SERVICE') != '1' or not os.environ.get('GEOMETRY_TEST_URL'):
    raise SystemExit('Require GEOMETRY_ISOLATED_SERVICE=1 and an explicitly isolated GEOMETRY_TEST_URL')
baseline = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=180)
(out / 'baseline.log').write_text(baseline.stdout + baseline.stderr)
assert baseline.returncode == 0, baseline.stdout + baseline.stderr
source = (root / 'geometry-web/grid-system-workspace.js').read_text()
cases = [
    ('M01-replacement-dialog', 'const collection=ReferenceWorkspace.readGridDrafts(),saved=collection.drafts;',
     'const collection=ReferenceWorkspace.readGridDrafts(),saved=collection.drafts;if(saved.length)window.confirm("取代舊草稿？");'),
    ('M03-fresh-continuation-id', 'draftId:restored?.draftId||crypto.randomUUID()', 'draftId:crypto.randomUUID()'),
    ('M15-cancel-updates-pin', "if(!window.confirm('重新取得基底；之後仍須預覽與確認。", "if(window.confirm('重新取得基底；之後仍須預覽與確認。"),
]
results = []
for name, before, after in cases:
    assert source.count(before) == 1
    mutant = out / (name + '.js')
    mutant.write_text(source.replace(before, after))
    env = dict(os.environ, GEOMETRY_GRID_WORKSPACE_SOURCE=str(mutant))
    run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=180)
    (out / (name + '.log')).write_text(run.stdout + run.stderr)
    result = {'id': name, 'exit': run.returncode, 'detected': run.returncode != 0 and 'AssertionError' in run.stdout + run.stderr}
    results.append(result)
    print(json.dumps(result), flush=True)
(out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
assert all(result['detected'] for result in results), results
