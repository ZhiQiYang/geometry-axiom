#!/usr/bin/env python3
"""One bounded, isolated cloud P78 run; all executables and output stay in TEMP.

Example: python3 tests/diagnostics/p78_run.py --out /tmp/p78-baseline
--hold 18 injects one bridge-lock hold before a trial command is written.
--cpu-rate 20 throttles Chromium only. Neither changes the 15s/20s deadlines.
Exit is the actual browser exit, including 1 for an injected red.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(os.environ.get('P78_SOURCE_ROOT', Path(__file__).resolve().parents[2])).resolve()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--cpu-rate', type=float, default=1)
parser.add_argument('--hold', type=float, default=0)
parser.add_argument('--mode', choices=['full', 'prefix'], default='full')
parser.add_argument('--bridge', type=Path)
args = parser.parse_args()
out = args.out.resolve()
if Path(tempfile.gettempdir()) not in out.parents or out.exists():
    parser.error('--out must be a new directory under TEMP')
if not 1 <= args.cpu_rate <= 20 or not 0 <= args.hold <= 22:
    parser.error('bounded limits: cpu-rate 1..20, hold 0..22 seconds')
out.mkdir(parents=True)
soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


commands = []


def run(argv, name, **kw):
    t = time.monotonic()
    with (out / (name + '.log')).open('wb') as log:
        p = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, **kw)
    row = dict(argv=list(map(str, argv)), cwd=str(ROOT), exit=p.returncode, seconds=time.monotonic()-t)
    commands.append(row)
    (out / 'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    print(json.dumps(row), flush=True)
    return p.returncode


sys.path.insert(0, str(ROOT / 'geometry-web'))
from runtime_version import source_files  # noqa: E402
files = source_files(ROOT)
before = {str(p.relative_to(ROOT)): digest(p) for p in files if p.is_file()}
tool_files = list(Path(__file__).parent.glob('p78_*'))
before.update({'diagnostic-tools/'+p.name: digest(p) for p in tool_files if p.is_file()})
(out / 'sources-before.json').write_text(json.dumps(before, indent=2)+'\n')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
run(['git', 'status', '--short'], 'git-status')
run(['git', 'diff', '--stat', '6855f9b11478e7fad30ab3c0f268ffc985b5dda1', 'HEAD', '--',
     'geometry-web/app.js', 'geometry-web/grid-trial.js', 'geometry-web/grid_trial_test.js',
     'geometry-web/serve.py', 'geometry-web/native_context.py', 'geometry-web/cdp_helpers.js'], 'historical-path-diff')
bridge = args.bridge.resolve() if args.bridge else out / 'bridge'
if args.bridge is None:
    code = run(['gcc', '-std=c11', '-O2', 'geometry-web/web_bridge.c', '-o', str(bridge), '-lm'], 'compile', timeout=180)
    if code:
        sys.exit(code)
run(['gcc', '-MM', 'geometry-web/web_bridge.c'], 'include-closure', timeout=30)
for name, cmd in [('compiler-version',['gcc','--version']),('node-version',['node','--version']),
                  ('browser-version',[os.environ.get('GEOMETRY_CHROME','/usr/bin/chromium'),'--version'])]:
    run(cmd, name, timeout=30)
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
url = f'http://127.0.0.1:{port}/'
env = {k: v for k, v in os.environ.items() if not k.startswith('GEOMETRY_')}
env.update(GEOMETRY_CHROME=os.environ.get('GEOMETRY_CHROME','/usr/bin/chromium'),
           GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR=str(out / 'screens'), GEOMETRY_FEEDBACK_DIR=str(out/'feedback'))
argv = [sys.executable, '-u', str(Path(__file__).with_name('p78_server.py')), str(port), str(out), str(bridge), str(args.hold)]
metadata = dict(head=head, url=url, platform=sys.platform, python=sys.version, cpuRate=args.cpu_rate,
                holdSeconds=args.hold, bridge=str(bridge), bridgeSha256=digest(bridge),
                serverArgv=argv, harnessArgv=sys.argv, environmentOverrides={k:v for k,v in env.items() if k.startswith('GEOMETRY_')},
                fullCanvas=False, historicalWSL=False, stackBytes=resource.getrlimit(resource.RLIMIT_STACK)[0])
metadata['toolIdentities'] = {str(Path(p).resolve()): digest(Path(p).resolve()) for p in
    (sys.executable, shutil.which('node'), shutil.which('gcc'), env['GEOMETRY_CHROME'])}
chromium_elf = Path('/usr/lib/chromium/chromium')
if env['GEOMETRY_CHROME']=='/usr/bin/chromium' and chromium_elf.is_file():
    metadata['toolIdentities'][str(chromium_elf)] = digest(chromium_elf)
(out/'identity.json').write_text(json.dumps(metadata, indent=2)+'\n')
code = 2
with (out/'host.log').open('wb') as log:
    server = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic()+30
        while time.monotonic()<deadline:
            if server.poll() is not None:
                raise RuntimeError('diagnostic server exited before ready')
            try:
                with urlopen(url+'runtime', timeout=1) as response:
                    runtime = json.load(response)
                if runtime['fresh'] and runtime['pid']==server.pid and runtime['root']==str(ROOT):
                    (out/'runtime.json').write_text(json.dumps(runtime, indent=2)+'\n')
                    break
            except (OSError, ValueError):
                pass
            time.sleep(.2)
        else:
            raise RuntimeError('runtime readiness deadline')
        code = run(['node', str(Path(__file__).with_name('p78_browser.cjs')), url, str(out), str(args.cpu_rate), args.mode],
                   'browser', env=env, timeout=300)
    finally:
        server.terminate()
        try:
            server.wait(timeout=35)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        metadata.update(serverPid=server.pid, serverExit=server.returncode, browserExit=code, bridgeSha256After=digest(bridge))
        after = {str(p.relative_to(ROOT)): digest(p) for p in files if p.is_file()}
        after.update({'diagnostic-tools/'+p.name: digest(p) for p in tool_files if p.is_file()})
        metadata['sourcesUnchanged'] = before == after
        (out/'sources-after.json').write_text(json.dumps(after, indent=2)+'\n')
        (out/'identity.json').write_text(json.dumps(metadata, indent=2)+'\n')
if not metadata['sourcesUnchanged'] or metadata['bridgeSha256'] != metadata['bridgeSha256After']:
    raise RuntimeError('source or binary changed during run')
sys.exit(code)
