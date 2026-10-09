"""Wait for the owned Chromium ELF, then attest its live Node parent, scratch only.

The Debian Chromium launcher initially runs as /usr/bin/dash in the same PID.
That launcher stage is recorded separately and never accepted as browser bytes.
No process environment, browser state or product state is read or changed.
"""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024): h.update(chunk)
    return h.hexdigest()

def configured():
    result = {}
    for name, command in [('node', shutil.which('node')), ('python', sys.executable), ('chromeLauncher', '/usr/bin/chromium')]:
        resolved = Path(command).resolve()
        result[name] = {'commandPath': str(command), 'resolvedPath': str(resolved), 'sha256': digest(resolved),
                        'version': subprocess.check_output([str(command), '--version'], stderr=subprocess.STDOUT, text=True).strip()}
    return result

def cmdline(pid):
    return Path('/proc', str(pid), 'cmdline').read_bytes().decode().rstrip('\0').split('\0')

def is_main_chromium(exe, argv, profile, port):
    return (Path(exe).name in {'chrome', 'chromium'}
            and '--user-data-dir=' + str(profile) in argv
            and '--remote-debugging-port=' + str(port) in argv
            and not any(arg.startswith('--type=') for arg in argv))

def process_snapshot(role, pid):
    proc = Path('/proc', str(pid))
    source = proc / 'exe'
    resolved = str(source.resolve(strict=True))
    argv = cmdline(pid)
    with source.open('rb') as stream: magic = stream.read(4)
    sha = digest(source)
    if resolved != str(source.resolve(strict=True)) or argv != cmdline(pid):
        raise ProcessLookupError('Process exec/argv changed while attesting owned PID ' + str(pid))
    return {'role': role, 'pid': pid, 'exe': resolved, 'sha256': sha, 'executableMagicHex': magic.hex(),
            'cmdline': argv, 'cwd': str((proc / 'cwd').resolve(strict=True))}

class Observer:
    def __init__(self, log, profile):
        self.log = Path(log); self.profile = profile; self.done = threading.Event()
        self.binding = None; self.errors = []; self.launcher_stages = []
        self.thread = threading.Thread(target=self.watch, daemon=True)
    def start(self): self.thread.start()
    def watch(self):
        while not self.done.wait(.05):
            if not self.log.exists(): continue
            rows = [line for line in self.log.read_text(errors='replace').splitlines() if line.startswith('CDP_SCOPE ')]
            if not rows: continue
            try:
                scope = json.loads(rows[0][len('CDP_SCOPE '):]); browser = scope['browserPid']
                exe = str(Path('/proc', str(browser), 'exe').resolve(strict=True))
                argv = cmdline(browser)
                if not is_main_chromium(exe, argv, self.profile, scope['cdpPort']):
                    stage = {'pid': browser, 'exe': exe, 'cmdline': argv}
                    if stage not in self.launcher_stages: self.launcher_stages.append(stage)
                    continue
                status = Path('/proc', str(browser), 'status').read_text()
                node = int(next(line.split()[1] for line in status.splitlines() if line.startswith('PPid:')))
                processes = [process_snapshot('actual CDP_SCOPE Chromium main process', browser),
                             process_snapshot('actual browser parent Node', node)]
                if not is_main_chromium(processes[0]['exe'], processes[0]['cmdline'], self.profile, scope['cdpPort']): continue
                assert processes[0]['executableMagicHex'] == '7f454c46', 'Owned Chromium is not an ELF executable'
                assert Path(processes[1]['exe']).name in {'node', 'nodejs'}, 'Owned Chromium parent is not Node'
                assert any(arg.endswith('cdp_test.js') for arg in processes[1]['cmdline']), 'Owned Node is not the canonical CDP command'
                self.binding = {'observedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                'scope': 'Observed the actual owned Chromium ELF and live canonical Node parent during this command; launcher stages excluded',
                                'cdpScope': scope, 'processes': processes}
                return
            except (FileNotFoundError, ProcessLookupError): continue
            except Exception as error: self.errors.append(repr(error)); return
    def stop(self):
        self.done.set(); self.thread.join(timeout=2)
        return {'liveBinding': self.binding, 'errors': self.errors, 'excludedLauncherStages': self.launcher_stages}
