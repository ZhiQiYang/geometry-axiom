#!/usr/bin/env python3
"""Preserve selected-suite artifacts and runtime identity without changing judges."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('/tmp/geometry-pr345-20261102')
OUT = Path(__file__).resolve().parent
phase = sys.argv[1]
assert phase in ('before', 'after')
destination = OUT / ('shared-' + phase)
destination.mkdir(exist_ok=False)
sys.path.insert(0, str(ROOT / 'tests'))
import binaries

def identity(path):
    if not path.exists():
        return {'exists': False}
    raw = path.read_bytes()
    st = path.stat()
    return {'exists': True, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'mode': st.st_mode, 'inode': st.st_ino, 'device': st.st_dev,
            'mtimeNs': st.st_mtime_ns}

paths = []
for binary in binaries.REGISTRY:
    paths.extend([binary.path, binary.sidecar])
state = {str(p): identity(p) for p in paths}
rowbase = binaries.OUT_DIR / 'run_all-logs' / 'py_test_rule_case_workbench_http'
logs = [rowbase.with_suffix(suffix) for suffix in ('.log', '.json', '.unittest.log')]
logstate = {str(p): identity(p) for p in logs}
for path in logs:
    if path.exists():
        shutil.copy2(path, destination / path.name)
protected = ['AGENTS.md', '公理層.md', '決策佇列.md', 'geometry-guide/公理層-閱讀器.html',
             'tests/binaries.py', 'tests/run_all.py', 'tests/run_all.expected.json',
             'tests/test_rule_case_workbench_http.py']
result = {'phase': phase, 'runtime': state, 'rowLogs': logstate,
          'sourceHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
          'protectedSources': {p: identity(ROOT / p) for p in protected}}
if phase == 'after':
    private = OUT / 'runtime'
    private.mkdir(exist_ok=False)
    bridge = binaries.BY_NAME['bridge']
    for path in (bridge.path, bridge.sidecar):
        shutil.copy2(path, private / path.name)
    info = binaries.inspect_one(bridge, private / bridge.path.name)
    result['privateBridge'] = info.as_dict()
    assert info.state == 'fresh', result['privateBridge']
    result['privateBridgeIdentity'] = identity(private / bridge.path.name)
    before = json.loads((OUT / 'RUNTIME_BEFORE.json').read_text())
    assert result['sourceHead'] == before['sourceHead']
    assert result['protectedSources'] == before['protectedSources']
    # Save this execution's row logs, then restore any pre-existing shared rows.
    for path in logs:
        saved = OUT / 'shared-before' / path.name
        if saved.exists():
            shutil.copy2(saved, path)
        else:
            path.unlink(missing_ok=True)
    result['restoredRowLogs'] = {str(p): identity(p) for p in logs}
    assert all(result['restoredRowLogs'][p].get('sha256') == meta.get('sha256')
               for p, meta in before['rowLogs'].items())
(OUT / ('RUNTIME_' + phase.upper() + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'phase': phase, 'head': result['sourceHead'],
                  'sharedBridge': state[str(binaries.BY_NAME['bridge'].path)],
                  'privateBridge': result.get('privateBridge'),
                  'rowLogSizes': {p: s.get('bytes') for p, s in logstate.items()}}, ensure_ascii=False))
