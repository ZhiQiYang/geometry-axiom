"""Source-only review receipt; no browser or native execution."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import subprocess

base = Path('/workspace/closure-evidence/contracts/remaining-product-scope-20261008')
old = base / 'css_c2_c4_before_region_observation.py'
new = base / 'css_c2_c4_browser_probe.py'
out = Path('/workspace/closure-evidence/css-review')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def funcs(p):
    return {x.name: ast.dump(x, include_attributes=False) for x in ast.walk(ast.parse(p.read_text())) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}

assert sha(old) == 'eb29d98de713c6fdd79ba9046ce0ab6a44ff2639b8f05debcf6fcd50cf882277'
assert sha(new) == 'b81a9f25b08c581168e63f5d407a89c3afc386a160cb1dd1384dcd1cb1754a9c'
previous, current = funcs(old), funcs(new)
unchanged = ['check_beam', 'check_slots', 'styles', 'snapshot', 'native', 'assert_slot_open', 'drawer', 'identity', 'ready', 'setup']
assert all(previous[name] == current[name] for name in unchanged)
diff = subprocess.run(['git', 'diff', '--no-index', str(old), str(new)], capture_output=True, text=True)
assert diff.returncode == 1 and not diff.stderr
(out / 'css-region-observer.patch').write_text(diff.stdout)
receipt = {
    'checked_at': datetime.now(timezone.utc).isoformat(),
    'classification': 'source-approved passive-observer correction; execution pending',
    'old_probe_sha256': sha(old), 'new_probe_sha256': sha(new),
    'patch_sha256': sha(out / 'css-region-observer.patch'),
    'unchanged_function_asts': unchanged,
    'source_basis': 'app.js:9594-9638 accepts a second down on #ocv/#app .sidebar-right/canvasViewport, requires stable selection/context and <=450 ms/6 px; does not require the same target node',
    'review': [
        'Actual locator.dblclick remains unchanged; no force, internal navigation call, retry or synthesized input was added.',
        'Gesture slice must contain exactly two trusted primary-button mouse downs; the first must identify space 1, and the second must stay in the allowed region with selected space 1 and no focus.',
        'Second hit on any different card fails; context equality, pointer identity, timing, position, genuine dblclick and final entered-space assertions remain.',
        'Region/selection/context reads are capture-phase passive observations, installed before product listeners; this directly measures the previously unknown second-DIV ancestry.',
        'All computed RGB, actual visibility, native snapshot equality, non-hover slot discoverability, click and Tab/Enter assertions have identical ASTs.',
        'Original CSS runs remain failures. This receipt does not change prior results or claim 390 CSS success.'
    ],
    'browser_or_native_launched': False,
    'command': {'argv': diff.args, 'exit_code': diff.returncode, 'stdout_file': 'css-region-observer.patch', 'stderr': diff.stderr},
    'review_script_sha256': sha(Path(__file__)),
}
(out / 'css-region-observer-source-review.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': receipt['classification'], 'receipt': str(out / 'css-region-observer-source-review.json'), 'sha256': sha(out / 'css-region-observer-source-review.json')}))
