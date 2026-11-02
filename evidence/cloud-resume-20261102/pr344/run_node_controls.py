#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/tmp/geometry-pr344-20261102')
OUT = Path(__file__).resolve().parent / 'node-controls'
OUT.mkdir(exist_ok=False)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
app = (ROOT / 'geometry-web/app.js').read_bytes()
test = (ROOT / 'tests/test_connection_recovery.js').read_bytes()
fixed = b'connection.phase = "ready"; connection.known = true; connection.error = "";'
withdrawn = b'connection.phase = "ready"; connection.known = true;'
assert app.count(fixed) == 1
variant = app.replace(fixed, withdrawn)
expected_assertions = ['successful recovery kept stale error', 'completed retry kept stale error', 'loading echoed stale error']
phases = []
for name, source in [('fixed', app), ('withdrawn', variant), ('restored', app)]:
    phase = OUT / name
    phase.mkdir()
    if name == 'fixed':
        cwd = ROOT
    else:
        cwd = phase / 'source'
        (cwd / 'geometry-web').mkdir(parents=True)
        (cwd / 'tests').mkdir()
        (cwd / 'geometry-web/app.js').write_bytes(source)
        (cwd / 'tests/test_connection_recovery.js').write_bytes(test)
    argv = ['node', '--test', '--test-reporter=spec', 'tests/test_connection_recovery.js']
    request = {'argv': argv, 'cwd': str(cwd), 'executionHead': head,
               'variant': name, 'appSha256': hashlib.sha256(source).hexdigest(),
               'testSha256': hashlib.sha256(test).hexdigest(), 'timeoutSeconds': 300,
               'domTransportPeers': 'original test declares explicit substitutes; not a real-browser receipt'}
    (phase / 'REQUEST.json').write_text(json.dumps(request, indent=2) + '\n')
    started = time.monotonic()
    with (phase / 'stdout.bin').open('wb') as stdout, (phase / 'stderr.bin').open('wb') as stderr:
        p = subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr, timeout=300, check=False,
                           env={**os.environ, 'NO_COLOR': '1'})
    rawout = (phase / 'stdout.bin').read_bytes()
    rawerr = (phase / 'stderr.bin').read_bytes()
    text = (rawout + rawerr).decode()
    counts = {}
    for field in ['tests', 'pass', 'fail', 'skipped']:
        found = re.search(r'^.*?\b' + field + r'\s+(\d+)\s*$', text, re.MULTILINE)
        assert found is not None, (field, text)
        counts[field] = int(found[1])
    result = {'actualProcessReturncode': p.returncode, 'elapsedSeconds': time.monotonic() - started,
              'counts': counts, 'stdoutSha256': hashlib.sha256(rawout).hexdigest(),
              'stderrSha256': hashlib.sha256(rawerr).hexdigest()}
    (phase / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    assert counts['tests'] == 9 and counts['skipped'] == 0
    if name == 'withdrawn':
        assert p.returncode == 1 and counts['fail'] == 3 and counts['pass'] == 6
        assert all(message in text for message in expected_assertions)
    else:
        assert p.returncode == 0 and counts['fail'] == 0 and counts['pass'] == 9
    phases.append({'phase': name, **request, **result})
assert (ROOT / 'geometry-web/app.js').read_bytes() == app
assert (ROOT / 'tests/test_connection_recovery.js').read_bytes() == test
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=all'], cwd=ROOT) == b''
summary = {'executionHead': head, 'phases': phases, 'exits': [p['actualProcessReturncode'] for p in phases],
           'namedWithdrawalAssertions': expected_assertions, 'realBrowserExecuted': False,
           'originalSourceAndIndexUnchanged': True}
(OUT / 'SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'executionHead': head, 'exits': summary['exits'],
                  'passCounts': [p['counts']['pass'] for p in phases],
                  'failCounts': [p['counts']['fail'] for p in phases], 'realBrowserExecuted': False}))
