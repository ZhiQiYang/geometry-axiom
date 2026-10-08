"""Source-only review of a separate established entry route."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import subprocess

base = Path('/workspace/closure-evidence/contracts/remaining-product-scope-20261008')
old = base / 'css_c2_c4_before_inspector_entry.py'
new = base / 'css_c2_c4_browser_probe.py'
out = Path('/workspace/closure-evidence/css-review')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(p):
    return {x.name: ast.dump(x, include_attributes=False) for x in ast.walk(ast.parse(p.read_text())) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}

assert sha(old) == 'b81a9f25b08c581168e63f5d407a89c3afc386a160cb1dd1384dcd1cb1754a9c'
assert sha(new) == '4db7be7eadd9ccfec9ea72ec648a1c53ea4e20c7aaeaa72608c9367421aba881'
previous, current = funcs(old), funcs(new)
unchanged = ['check_beam', 'check_slots', 'styles', 'snapshot', 'native', 'assert_slot_open', 'drawer', 'identity', 'ready', 'setup']
assert all(previous[k] == current[k] for k in unchanged)
marker = '        page.locator(\'.ocard[data-kind="space"][data-id="1"] .ocard-frame\').dblclick(timeout=15000)'
end = '\n    def setup(lines):'
assert old.read_text().split(marker, 1)[1].split(end, 1)[0] == new.read_text().split(marker, 1)[1].split(end, 1)[0]
diff = subprocess.run(['git', 'diff', '--no-index', str(old), str(new)], capture_output=True, text=True)
assert diff.returncode == 1 and not diff.stderr
(out / 'css-inspector-entry.patch').write_text(diff.stdout)
report = {'checked_at': datetime.now(timezone.utc).isoformat(),
          'classification': 'source-approved separate existing UI entry for CSS precondition; execution pending',
          'old_probe_sha256': sha(old), 'new_probe_sha256': sha(new),
          'source_basis': ['app.js:9452-9454 renders Enter Space for selected space', 'app.js:9494-9497 binds enterFocus', 'DOM-CONTRACT.md:383 preserves inspector-button entry'],
          'unchanged_function_asts': unchanged,
          'original_double_click_action_and_oracles_unchanged': True,
          'review': [
              'Explicit --entry inspector selects the separate route; default remains original dblclick.',
              'Uses one real card click, exact selected identity wait, optional one real drawer-toggle click only if needed, and real locator click on existing #inspEnter. No force, internal navigation call, synthetic DOM click, repeat loop or fixture mutation.',
              'Requires a trusted first card down, exactly one trusted inspector Enter click and the exact entered space 1 completion state; raw events and route limitation are recorded.',
              'Computed CSS, native World/ref snapshots, visible empty-slot assertions and actual slot click/Tab/Enter behavior are unchanged.',
              'The mobile card double-click collision remains a separate observed unresolved defect. A successful inspector-route run must not relabel r3 or assert repaired double-click entry.'
          ],
          'browser_or_native_launched': False,
          'patch_sha256': sha(out / 'css-inspector-entry.patch'),
          'review_script_sha256': sha(Path(__file__)),
          'diff_command': {'argv': diff.args, 'exit_code': diff.returncode, 'stdout_file': 'css-inspector-entry.patch', 'stderr': diff.stderr}}
target = out / 'css-inspector-entry-source-review.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'receipt': str(target), 'sha256': sha(target), 'verdict': report['classification']}))
