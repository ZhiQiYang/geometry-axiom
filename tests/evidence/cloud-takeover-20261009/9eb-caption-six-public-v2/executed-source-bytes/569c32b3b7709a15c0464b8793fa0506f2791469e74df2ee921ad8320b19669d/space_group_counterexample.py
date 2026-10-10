"""Public-source omission/return/throw probes against an explicitly isolated server.

Reuse the space harness, with only the named deliberate fault in a TEMP copy.
No product source, user scene, expected counts or browser assertions are changed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--ref', default='HEAD', help='Exact source commit to mutate')
parser.add_argument('--full-omit', action='store_true', help='Omit font group in the default full space suite')
parser.add_argument('--expect-vulnerable', action='store_true', help='Verify the pre-fix green omission/return counterexample')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
ref = subprocess.check_output(['git', 'rev-parse', args.ref], cwd=root, text=True).strip()
source = subprocess.check_output(['git', 'show', ref + ':geometry-web/space_model_test.js'], cwd=root, text=True)
# Existing helpers are read from this checkout. They must match the selected ref.
for relative in re.findall(r"require\('(\./[^']+)'\)", source):
    helper = root / 'geometry-web' / relative
    committed = subprocess.check_output(['git', 'show', ref + ':geometry-web/' + helper.name], cwd=root)
    if helper.read_bytes() != committed:
        raise SystemExit('Helper does not match exact ref: ' + helper.name)
source = re.sub(r"require\('(\./[^']+)'\)", lambda m: 'require(' + json.dumps(str(root / 'geometry-web' / m[1])) + ')', source)
call = "  await runGroup('font-layout', fontLayoutRegression);" if 'createGroupCensus' in source else '  await fontLayoutRegression();'
if args.full_omit:
    index = source.rfind(call)
    assert index >= 0
    variants = {'full-omit-font': source[:index] + source[index:].replace(call, '  // deliberate omission', 1)}
else:
    variants = {
        'omit-font-call': source.replace(call, '  // deliberate omission'),
        'return-from-font': source.replace('async function fontLayoutRegression() {', 'async function fontLayoutRegression() { return;'),
        'throw-from-font': source.replace('async function fontLayoutRegression() {', "async function fontLayoutRegression() { throw Error('deliberate group exception');"),
    }
for name, content in variants.items():
    artifacts = Path(tempfile.mkdtemp(prefix='geometry-space-negative-'))
    script = artifacts / (name + '.js')
    script.write_text(content)
    env = {**os.environ, 'GEOMETRY_SPACE_TEST_DIR': str(artifacts / 'run')}
    for flag in ['SPACE_FLOW_ONLY', 'TIMBER_ONLY', 'TIMBER_GUARDS_ONLY', 'SPACE_STYLE_ONLY', 'PROJECTION_PLACEMENT_ONLY', 'TIMBER_HISTORY_ONLY']:
        env.pop('GEOMETRY_' + flag, None)
    if not args.full_omit:
        env['GEOMETRY_SPACE_STYLE_ONLY'] = '1'
    with (artifacts / 'run.log').open('w') as log:
        result = subprocess.run(['node', str(script)], env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    data = json.loads((artifacts / 'run/result.json').read_text())
    expected_exit = 0 if args.expect_vulnerable and name != 'throw-from-font' else 1
    print(json.dumps({'ref': ref, 'variant': name, 'exit': result.returncode, 'passed': data['passed'], 'failed': data['failed'], 'completed': data.get('completed'), 'groups': data.get('groups'), 'scope': data['scope'], 'artifacts': str(artifacts)}), flush=True)
    assert result.returncode == expected_exit, (name, expected_exit, result.returncode)
    assert not data['exceptions'] and not data['consoleErrors'], 'Unexpected browser errors contaminated the probe'
    if expected_exit == 0:
        assert data['failed'] == 0
    elif not args.expect_vulnerable:
        assert data['completed'] is False
        assert any('font-layout' in problem for problem in data['completenessProblems'])
        if name != 'throw-from-font':
            assert data['failed'] == 1, 'Only the completeness gate should fail'
