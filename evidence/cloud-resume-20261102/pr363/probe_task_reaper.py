import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from task_child_reaper import ChildReaper, utc

ROOT = Path('/tmp/geometry-pr363-20261102')
OUT = Path('/tmp/geometry-resume-20261102/pr363/reaper-environment-recovery')
HEAD = 'e9f4dd75cfd4eb9965e3af249200b918907d62db'
FILES = ['tests/__init__.py', 'tests/_bridge.py', 'tests/binaries.py',
         'tests/_unittest_runner.py', 'tests/assembly_mutation_check.py',
         'tests/test_assembly_mutation_check.py', 'tests/test_assembly_rules.py',
         'geometry-templates/woodworking/native/assembly.c', 'geometry-web/engineering_bridge.inc']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == HEAD
assert subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=ROOT).strip() == b''
assert (OUT.parent / 'full-census-A/result.json').is_file(), 'The original census must be terminal first.'
OUT.mkdir(exist_ok=False)
snapshot = OUT / 'source'
original = {}
for rel in FILES:
    data = (ROOT / rel).read_bytes()
    assert data == subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=ROOT)
    target = snapshot / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    original[rel] = {'bytes': len(data), 'sha256': sha(data)}
save('source-inputs.json', {'head': HEAD, 'files': original, 'scope': 'Exact original inputs read by all 12 no-compiler assembly mutation unit tests.'})
reaper = ChildReaper(OUT / 'reaper.jsonl', observe_live=True)
phases = []
method = 'test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left'

def phase(name, expected_exit, expected_failures):
    assert reaper.children() == [], 'No competing Popen child or preceding adopted child may be present.'
    directory = OUT / name
    directory.mkdir()
    command = [sys.executable, '-u', str(snapshot / 'tests/_unittest_runner.py'),
               str(snapshot / 'tests/test_assembly_mutation_check.py'), '--json-out', str(directory / 'result.json'),
               '--log', str(directory / 'unittest.log')]
    start = time.monotonic()
    event_start = len(reaper.events)
    with (directory / 'stdout.log').open('wb') as out, (directory / 'stderr.log').open('wb') as err:
        process = subprocess.Popen(command, cwd=snapshot, stdout=out, stderr=err, env=dict(os.environ))
        code = reaper.wait_main(process, start + 45)
        # Missing group kill leaves real running sleeps. Observe their natural
        # 30-second completion; never signal them to make the assertion pass.
        remaining = reaper.drain_naturally(process.pid, start + 45)
    record = {'phase': name, 'command': command, 'cwd': str(snapshot), 'mainPid': process.pid,
              'exitCode': code, 'blocked': code is None, 'elapsedSeconds': time.monotonic() - start,
              'remainingAdoptedChildren': remaining, 'events': reaper.events[event_start:],
              'finishedUtc': utc(), 'signalsSentByReaperOrProbe': []}
    save(name + '/execution.json', record)
    assert code is not None, 'blocked: main child did not terminate before the probe deadline'
    assert remaining == [], 'blocked: adopted children did not naturally terminate'
    result = json.loads((directory / 'result.json').read_text())
    record['testResult'] = result
    assert code == expected_exit
    assert result['total'] == result['run'] == 12
    assert result['failed'] == expected_failures and result['skipped'] == 0
    assert result['extra_errors'] == 0 and not result['import_error']
    if expected_failures:
        assert len(result['failures']) == 1 and result['failures'][0]['test'].endswith('.' + method)
        raw = (directory / 'unittest.log').read_text()
        assert "self.assertEqual([], group['afterKill'])" in raw
        assert "'state': 'S'" in raw or "'state': 'R'" in raw
        assert any(event['event'] == 'observed-live-adopted-child' for event in record['events'])
        assert record['elapsedSeconds'] >= 29, 'Live sleeps must finish naturally, not be killed by the wrapper.'
    assert all(event.get('pid') != process.pid for event in record['events']
               if event['event'] == 'reaped-adopted-child')
    phases.append(record)
    save('phases-so-far.json', phases)
    print(json.dumps({'phase': name, 'exitCode': code, 'total': result['total'], 'failed': result['failed'],
                      'elapsedSeconds': record['elapsedSeconds']}, ensure_ascii=False), flush=True)

phase('baseline-reaped', 0, 0)
tool = snapshot / 'tests/assembly_mutation_check.py'
unmodified_tool = tool.read_bytes()
needle = b'os.killpg(process.pid, signal.SIGKILL)'
replacement = b'process.kill()'
assert unmodified_tool.count(needle) == 1
tool.write_bytes(unmodified_tool.replace(needle, replacement, 1))
save('negative-control-patch.json', {'file': 'tests/assembly_mutation_check.py',
     'before': needle.decode(), 'after': replacement.decode(),
     'beforeSha256': sha(unmodified_tool), 'afterSha256': sha(tool.read_bytes()),
     'meaning': 'Kill the Popen shell only; deliberately omit the process-group kill. Assertions, 2-second run timeout and 5-second group wait remain original.'})
try:
    phase('missing-group-kill-negative', 1, 1)
finally:
    tool.write_bytes(unmodified_tool)
phase('restored-reaped', 0, 0)
assert all(sha((snapshot / rel).read_bytes()) == data['sha256'] for rel, data in original.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=ROOT).strip() == b''
save('summary.json', {'head': HEAD, 'sourceRestored': True, 'realWorktreeUnchanged': True,
     'originalEnvironmentFailure': '../full-census-A/environment-zombie-failure',
     'assertionsAndOriginalTimeoutsUnchanged': True, 'reaperSignalsSent': [], 'phases': phases})
print('Environment recovery and missing-group-kill negative control verified.', flush=True)
