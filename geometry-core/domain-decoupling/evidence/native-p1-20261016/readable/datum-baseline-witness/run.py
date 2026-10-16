#!/usr/bin/env python3
import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'fixture-reopen'))
from run_native_pair import BASELINE, git, import_file, save, sha, source_manifest

root = Path('/var/tmp/geo261-baseline-a898ad6e')
bridge = Path('/tmp/geometry-tests/bridge')
out = HERE.parent / 'datum-baseline-a898-v1'
held, lock = os.fstat(7), Path('/run/lock/ga-wsl-v3.lock').stat()
if (held.st_dev, held.st_ino) != (lock.st_dev, lock.st_ino):
    raise RuntimeError('Original shared lock is not inherited')
if git(root, 'rev-parse', 'HEAD').decode().strip() != BASELINE or git(root, 'status', '--porcelain'):
    raise RuntimeError('Baseline source changed')
registry = import_file('datum_baseline_registry', root / 'tests/binaries.py')
fresh_before = registry.inspect_one(registry.BY_NAME['bridge'], str(bridge))
if fresh_before.state != 'fresh':
    raise RuntimeError('Baseline bridge is not fresh: ' + fresh_before.reason)
out.mkdir(exist_ok=False)
input_path = HERE / 'input.json'
input_sha = sha(input_path)
data = json.loads(input_path.read_bytes())
runner_files = [Path(__file__), HERE / 'namespace.sh', HERE.parent / 'fixture-reopen/run_native_pair.py']
runner_before = {str(path): sha(path) for path in runner_files}
before = source_manifest(root)
save(out / 'source-before.json', before)
scene_path = out / 'original-test.scene'
scene_path.write_bytes(data['scene'].encode('utf-8'))
commands = ['loadfile ' + str(scene_path), 'dump']
for expression in data['expressions']:
    commands += ['line preview datum 9 x ' + expression, 'dump']
payload = ('\n'.join(commands) + '\n').encode('utf-8')
(out / 'commands.txt').write_bytes(payload)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
run = subprocess.run([str(bridge)], input=payload, capture_output=True, cwd=out, timeout=30)
(out / 'bridge.stdout').write_bytes(run.stdout)
(out / 'bridge.stderr').write_bytes(run.stderr)
rows = [json.loads(line) for line in run.stdout.decode('utf-8').splitlines()] if run.returncode == 0 else []
complete = run.returncode == 0 and len(rows) == len(commands) and rows[0].get('ok') is True and rows[1].get('ok') is True
observations = []
if complete:
    for index, expression in enumerate(data['expressions']):
        preview, dump = rows[2 + index * 2:4 + index * 2]
        observations.append({'expression': expression, 'response': preview, 'dump': dump,
                             'invalidPreviewObserved': preview.get('ok') is True and preview.get('preview', {}).get('valid') is False,
                             'worldUnchanged': dump == rows[1]})
    complete = all(row['invalidPreviewObserved'] and row['worldUnchanged'] for row in observations)
after = source_manifest(root)
save(out / 'source-after.json', after)
fresh_after = registry.inspect_one(registry.BY_NAME['bridge'], str(bridge))
summary = {'kind': 'observed-original-baseline-diagnostic-not-an-oracle-correction', 'source': BASELINE,
           'testInputProvenance': data, 'inputSha256': input_sha, 'inputUnchanged': input_sha == sha(input_path),
           'startedUtc': started, 'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'bridgeSha256': sha(bridge), 'bridgeSidecar': json.loads(Path(str(bridge) + registry.SIDECAR_SUFFIX).read_bytes()),
           'bridgeFreshBefore': fresh_before.state, 'bridgeFreshAfter': fresh_after.state,
           'rawExit': run.returncode, 'observations': observations, 'witnessComplete': complete,
           'sourceUnchanged': before == after, 'sourceFiles': len(before),
           'stdoutSha256': sha(out / 'bridge.stdout'), 'stderrSha256': sha(out / 'bridge.stderr'),
           'runnersUnchanged': runner_before == {str(path): sha(path) for path in runner_files},
           'runnersSha256': runner_before, 'sharedLockHolder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
           'expectedDiagnosticAsserted': False,
           'exit': 0 if complete and before == after and fresh_after.state == 'fresh' and input_sha == sha(input_path)
                      and runner_before == {str(path): sha(path) for path in runner_files} else 1}
save(out / 'summary.json', summary)
(out / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(summary['exit'])
