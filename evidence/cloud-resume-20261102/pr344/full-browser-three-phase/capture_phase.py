"""Read source/runtime identities and original receipts; no test or binary run."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
phase, stage = sys.argv[1:]
assert phase in ('fixed', 'fixed-02', 'withdrawn', 'restored') and stage in ('before', 'after')
prep = Path(__file__).resolve().parent
p = json.loads((prep / ('phase-' + phase + '.json')).read_text())
root, out = Path(p['source']), Path(p['phaseRoot'])
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=root).decode().strip()
spec = importlib.util.spec_from_file_location('phase_runtime_version', root / 'geometry-web/runtime_version.py')
runtime_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime_module)
inputs = []
for path in runtime_module.source_files(root):
    st = path.stat()
    inputs.append({'path': str(path.relative_to(root)), 'sha256': sha(path), 'bytes': st.st_size,
                   'mtimeNs': st.st_mtime_ns, 'mode': st.st_mode})
spec = importlib.util.spec_from_file_location('phase_registry', root / 'tests/binaries.py')
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)
binaries = {}
for name in ('core', 'bridge', 'model-base'):
    path = out / 'tmp/runtime' / name
    info = registry.inspect_one(registry.BY_NAME[name], path)
    assert info.state == 'fresh', info.as_dict()
    binaries[name] = {'state': info.state, 'fingerprint': info.fingerprint, 'sha256': sha(path),
                      'sidecarSha256': sha(path.with_name(path.name + registry.SIDECAR_SUFFIX)),
                      'bytes': path.stat().st_size, 'mode': path.stat().st_mode}
assert git('rev-parse', 'HEAD') == p['head']
assert git('rev-parse', 'HEAD^{tree}') == p['tree']
assert git('status', '--porcelain=v1', '--untracked-files=all') == ''
data = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phase': phase,
        'head': p['head'], 'source': str(root), 'sourceTree': p['tree'],
        'sourceInputCount': len(inputs), 'binaries': binaries,
        'goldenSha256': sha(root / 'geometry-web/cdp_sections.golden.json'), 'sourceClean': True}
if stage == 'before':
    assert not (out / 'PHASE_BEFORE.json').exists()
    data['runtime'] = json.loads((out / 'commands/probe/stdout.bin').read_text())
    assert data['runtime']['fresh'] is True and data['runtime']['root'] == str(root)
    data['originalGolden'] = json.loads((root / 'geometry-web/cdp_sections.golden.json').read_text())
    (out / 'runtime-source-inputs-before.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n')
    (out / 'PHASE_BEFORE.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
else:
    before = json.loads((out / 'PHASE_BEFORE.json').read_text())
    before_inputs = json.loads((out / 'runtime-source-inputs-before.json').read_text())
    data['sourceInputsBeforeAfterIdentical'] = inputs == before_inputs
    data['binaryIdentitiesBeforeAfterIdentical'] = binaries == before['binaries']
    data['goldenBytesUnchanged'] = data['goldenSha256'] == before['goldenSha256']
    receipt = json.loads((out / 'gate/receipt.json').read_text())
    log = (out / 'gate/command.log').read_text(errors='replace')
    results = [json.loads(line[len('CDP_RESULT '):]) for line in log.splitlines() if line.startswith('CDP_RESULT ')]
    data.update({'releaseGateReceipt': receipt, 'canonicalResultCount': len(results),
                 'canonicalResult': results[0] if len(results) == 1 else None,
                 'allFailureMarkerLines': [line for line in log.splitlines() if '✗' in line],
                 'floorDiagnosticLines': [line for line in log.splitlines() if '[CDP FLOOR]' in line],
                 'expectedExceptionLines': [line for line in log.splitlines() if '[EXPECTED EXCEPTION]' in line],
                 'logSha256': sha(out / 'gate/command.log')})
    (out / 'runtime-source-inputs-after.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n')
    (out / 'PHASE_AFTER.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    assert data['sourceInputsBeforeAfterIdentical'] and data['binaryIdentitiesBeforeAfterIdentical'] and data['goldenBytesUnchanged']
    assert len(results) == 1 and results[0]['completed'] is True
    result = results[0]
    assert result['scope']['mode'] == 'full' and result['scope']['filters'] == [] and result['scope']['modifiers'] == []
    assert result['skipped'] == []
    if phase != 'withdrawn':
        assert receipt['gateExitCode'] == 0 and receipt['executionVerified'] is True
        assert result['failedAssertions'] == 0 and result['goldenCompare'] == 'matched'
    else:
        assert receipt['gateExitCode'] == 1 and receipt['execution']['timedOut'] is False
        targets = ['P53-3 ', 'P61-10 ', 'P61-11 ']
        assert all(any(line.startswith(target) and '✗' in line for line in data['allFailureMarkerLines']) for target in targets)
print(json.dumps({'phase': phase, 'stage': stage, 'head': p['head'], 'sourceInputs': len(inputs),
                  'sourceClean': True, 'gateExit': data.get('releaseGateReceipt', {}).get('gateExitCode'),
                  'canonicalResult': {k: data['canonicalResult'].get(k) for k in ['passedAssertions', 'failedAssertions', 'goldenCompare', 'uncaughtBrowserExceptions']} if data.get('canonicalResult') else None}))
