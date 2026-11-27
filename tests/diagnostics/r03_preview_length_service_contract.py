"""Owned-service control test, using a tiny HTTP fixture, never Chromium.

This proves launcher identity/cleanup and external-URL isolation only. The
fixture's fresh flag is deliberately synthetic; it is not a native receipt.
"""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='r2054-owned-service-') as directory:
    root = Path(directory)
    (root/'tests/diagnostics').mkdir(parents=True)
    (root/'geometry-web').mkdir()
    target = root/'tests/diagnostics/r03_preview_length_withdrawals.py'
    shutil.copyfile(ROOT/'tests/diagnostics/r03_preview_length_withdrawals.py', target)
    spec = importlib.util.spec_from_file_location('owned_driver', target)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    assert callable(getattr(driver, 'run_browser', None)), 'R2054_BROWSER_DRIVER_OWNS_SERVICE'
    (root/'geometry-web/serve.py').write_text('''import http.server,json,os,pathlib,sys,uuid
root=pathlib.Path.cwd();port=int(sys.argv[1]);session=uuid.uuid4().hex
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  assert self.path=='/runtime'
  body=json.dumps(dict(pid=0 if os.environ.get('BAD_IDENTITY') else os.getpid(),fresh=True,root=str(root),session=session,source=(root/'phase.txt').read_text())).encode()
  self.send_response(200);self.end_headers();self.wfile.write(body)
server=http.server.HTTPServer(('127.0.0.1',port),Handler)
print('http://localhost:'+str(port)+' ready',flush=True)
server.serve_forever()
''')
    # A caller's unreachable URL must never be consulted, let alone reset.
    env = dict(os.environ, GEOMETRY_TEST_URL='http://127.0.0.1:1/DO-NOT-CONTACT')
    command = [sys.executable, '-B', '-c',
               'import json,os,urllib.request;print(json.load(urllib.request.urlopen(os.environ["GEOMETRY_TEST_URL"]+"runtime"))["source"])']
    sessions = set()
    pids = []
    for phase in ['first-source', 'changed-source']:
        (root/'phase.txt').write_text(phase)
        result, runtime = driver.run_browser(command, env, root/phase, sessions)
        assert result.returncode == 0 and result.stdout.decode().strip() == phase, 'R2054_BROWSER_OWNED_CURRENT_SOURCE'
        pids.append(runtime['pid'])
        assert runtime['root'] == str(root), 'R2054_BROWSER_OWNED_ROOT'
    assert len(sessions) == 2 and len(set(pids)) == 2, 'R2054_BROWSER_EVERY_PHASE_FRESH_SESSION'
    if os.name != 'nt':
        for pid in pids:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise AssertionError('R2054_BROWSER_OWNED_CHILD_REAPED')
    marker = root/'must-not-run'
    bad_command = [sys.executable, '-B', '-c', 'from pathlib import Path;Path('+repr(str(marker))+').touch()']
    try:
        driver.run_browser(bad_command, dict(env, BAD_IDENTITY='1'), root/'bad-identity', sessions)
    except AssertionError as error:
        assert str(error) == 'R03_LENGTH_OWNED_SERVICE_IDENTITY', 'R2054_BROWSER_WRONG_IDENTITY_JUDGE'
    else:
        raise AssertionError('R2054_BROWSER_REJECTS_WRONG_SERVICE_PID')
    assert not marker.exists(), 'R2054_BROWSER_NO_FIXTURE_BEFORE_OWNERSHIP'
    print('R2054_OWNED_SERVICE_CONTRACT PASS: two distinct sessions, exact phase source, wrong PID rejected before command')
