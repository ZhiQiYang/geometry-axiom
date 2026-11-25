"""Physical P2054 projection-guard withdrawals, never a Chrome/CI receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tests/diagnostics/r03_preview_length_canvas_extension.cjs'
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
original = SOURCE.read_bytes()
cases = {
    'R2054_WITHDRAW_COUNT_GUARD': (
        "  assert.equal(golden.sections[SECTION],COUNT,'R2054_CANVAS_EXACT_COUNT');\n",
        'R2054_CANVAS_COUNT_GUARD_REQUIRED'),
    'R2054_WITHDRAW_OWNER_GUARD': (
        "    assert.deepEqual(plan.shards.map(row=>row.sections.filter(id=>id===name)),[[],[name]],'R2054_CANVAS_EXACT_OWNER:'+name);\n",
        'R2054_CANVAS_OWNER_GUARD_REQUIRED'),
    'R2054_WITHDRAW_ORDER_GUARD': (
        "  assert.deepEqual(plan.shards[1].sections.slice(at-1,at+2),['P1231',SECTION,'P359'],'R2054_CANVAS_EXACT_NEIGHBORS');\n",
        'R2054_CANVAS_ORDER_GUARD_REQUIRED'),
}
command = ['node', '--test', '--test-reporter=tap', 'tests/test_r03_preview_length.js']
records = []
try:
    for name, (before, marker) in cases.items():
        token = before.encode()
        assert original.count(token) == 1, name + '_SITE'
        phases = []
        for phase, expected in [('baseline', 0), ('withdrawn', 1), ('restored', 0)]:
            SOURCE.write_bytes(original.replace(token, b'', 1) if phase == 'withdrawn' else original)
            result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=60)
            for stream, raw in [('stdout', result.stdout), ('stderr', result.stderr)]:
                (args.out / (name + '.' + phase + '.' + stream)).write_bytes(raw)
            output = (result.stdout + result.stderr).decode('utf-8', 'replace')
            assert result.returncode == expected, (name, phase, output)
            for key, value in [('tests', 10), ('fail', expected), ('cancelled', 0), ('skipped', 0), ('todo', 0)]:
                assert re.search(r'^# ' + key + ' ' + str(value) + r'$', output, re.M), (name, phase, output)
            if expected:
                assert marker in output and 'AssertionError' in output, (name, output)
            phases.append({'phase': phase, 'exit': result.returncode,
                           'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                           'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                           'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()})
        records.append({'name': name, 'marker': marker, 'phases': phases})
        print(name + ' 0/1/0', flush=True)
finally:
    SOURCE.write_bytes(original)
assert SOURCE.read_bytes() == original
(args.out / 'result.json').write_text(json.dumps({
    'scope': 'physical source guards; synthetic section inputs; not Chrome or CI measurement',
    'command': command, 'restored_sha256': hashlib.sha256(original).hexdigest(), 'cases': records}, indent=2) + '\n')
