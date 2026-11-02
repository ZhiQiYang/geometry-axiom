import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from task_child_reaper import ChildReaper

ROOT = Path('/tmp/geometry-canvas-shards-20261102')
OUT = Path('/dev/shm/geometry-canvas-full-census-20261102')
HEAD = os.environ['CANVAS_CENSUS_EXPECTED_HEAD']
NODE = Path('/tmp/geometry-resume-20261102/pr363/node-v24.22.1-linux-x64/bin')
CACHE = '/tmp/geometry-resume-20261102/canvas-sharding/manual-mutation-S/adoption/logical-cache-not-materialized'
LIMIT = 2100

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def snapshot():
    rows = []
    for rel in sorted(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')):
        if not rel:
            continue
        p = ROOT / rel
        if not p.is_file():
            rows.append({'path': rel, 'presentInWorktree': False})
            continue
        data = p.read_bytes()
        rows.append({'path': rel, 'bytes': len(data), 'sha256': sha(data),
                     'lfSha256': sha(data.replace(b'\r\n', b'\n'))})
    return {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
            'status': git('status', '--porcelain=v1'), 'inputs': rows,
            'worktreeSha256': sha(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode())}

def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def child_limits():
    resource.setrlimit(resource.RLIMIT_STACK, (16 * 1024 * 1024, 16 * 1024 * 1024))

OUT.mkdir(exist_ok=False)
before = snapshot()
assert before['head'] == HEAD and before['status'] == '', before
# This is the first full census at the explicit new frozen canvas source, not an A retry.
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
save('source-before.json', before)
expected = ROOT / 'tests/run_all.expected.json'
(OUT / 'expected-before.json').write_bytes(expected.read_bytes())
env = os.environ.copy()
env['PATH'] = str(NODE) + os.pathsep + env['PATH']
env['MUTATE_CACHE'] = CACHE
env['GEOMETRY_FEEDBACK_DIR'] = str(OUT / 'feedback')
cmd = [sys.executable, '-u', 'tests/run_all.py', '--build', '--update-expected',
       '--report', str(OUT / 'run-all-report.json')]
reaper = ChildReaper(OUT / 'reaper.jsonl')
started = time.monotonic()
start_utc = utc()
stdout = (OUT / 'stdout.log').open('wb')
stderr = (OUT / 'stderr.log').open('wb')
proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                        start_new_session=True, preexec_fn=child_limits)
deadline = datetime.datetime.fromisoformat(start_utc) + datetime.timedelta(seconds=LIMIT)
request = {'command': cmd, 'cwd': str(ROOT), 'head': HEAD, 'startedUtc': start_utc,
           'deadlineUtc': deadline.isoformat(), 'timeoutSeconds': LIMIT,
           'stackBytes': 16 * 1024 * 1024, 'supervisorPid': os.getpid(), 'childPid': proc.pid,
           'taskChildReaperSha256': sha(Path(__file__).with_name('task_child_reaper.py').read_bytes()),
           'reapingPolicy': 'One main Popen child; reap only terminated adopted direct children, never signal live adopted children or compete for the main exit code.',
           'environmentOverrides': {k: env[k] for k in ('PATH', 'MUTATE_CACHE', 'GEOMETRY_FEEDBACK_DIR')},
           'nodeVersion': subprocess.check_output([str(NODE / 'node'), '--version']).decode().strip(),
           'cacheMeaning': 'Task-only logical source validation cache; official CI ELF bytes were separately verified without executing downloads.'}
save('request.json', request)
print(json.dumps(request, ensure_ascii=False), flush=True)
timed_out = False
signals = []
try:
    rc = reaper.wait_main(proc, started + LIMIT)
    if rc is None:
        raise subprocess.TimeoutExpired(cmd, LIMIT)
except subprocess.TimeoutExpired:
    timed_out = True
    signals.append({'utc': utc(), 'signal': 'SIGTERM', 'processGroup': proc.pid})
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        rc = proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        signals.append({'utc': utc(), 'signal': 'SIGKILL', 'processGroup': proc.pid})
        os.killpg(proc.pid, signal.SIGKILL)
        rc = proc.wait()
finally:
    stdout.close()
    stderr.close()
reaper.tick(proc.pid)
after = snapshot()
save('source-after.json', after)
(OUT / 'expected-after.json').write_bytes(expected.read_bytes())
changed = [b['path'] for b, a in zip(before['inputs'], after['inputs']) if b != a]
assert [v['path'] for v in before['inputs']] == [v['path'] for v in after['inputs']]
result = {'startedUtc': start_utc, 'finishedUtc': utc(), 'elapsedSeconds': time.monotonic() - started,
          'childExitCode': rc, 'supervisorExitCode': 124 if timed_out else rc,
          'timedOut': timed_out, 'signals': signals, 'changedTrackedInputs': changed,
          'onlyExpectedChanged': changed in ([], ['tests/run_all.expected.json']),
          'headUnchanged': after['head'] == before['head'],
          'remainingAdoptedChildren': [pid for pid in reaper.children() if pid != proc.pid],
          'reaperLogSha256': sha((OUT / 'reaper.jsonl').read_bytes()),
          'expectedBeforeSha256': sha((OUT / 'expected-before.json').read_bytes()),
          'expectedAfterSha256': sha((OUT / 'expected-after.json').read_bytes()),
          'stdoutSha256': sha((OUT / 'stdout.log').read_bytes()),
          'stderrSha256': sha((OUT / 'stderr.log').read_bytes())}
save('result.json', result)
print(json.dumps(result, ensure_ascii=False), flush=True)
sys.exit(result['supervisorExitCode'])
