"""Configured executable bytes plus live CDP Node/browser binding, scratch only."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def configured():
    result={}
    for name,command in [('node',shutil.which('node')),('python',sys.executable),('chromeLauncher','/usr/bin/chromium')]:
        resolved=Path(command).resolve()
        result[name]={'commandPath':str(command),'resolvedPath':str(resolved),'sha256':digest(resolved),
            'version':subprocess.check_output([str(command),'--version'],stderr=subprocess.STDOUT,text=True).strip()}
    return result
class Observer:
    def __init__(self,log,profile):
        self.log=Path(log);self.profile=profile;self.done=threading.Event();self.binding=None;self.errors=[]
        self.thread=threading.Thread(target=self.watch,daemon=True)
    def start(self):self.thread.start()
    def watch(self):
        while not self.done.wait(.05):
            if not self.log.exists():continue
            rows=[l for l in self.log.read_text(errors='replace').splitlines() if l.startswith('CDP_SCOPE ')]
            if not rows:continue
            try:
                scope=json.loads(rows[0][len('CDP_SCOPE '):]);browser=scope['browserPid']
                status=Path(f'/proc/{browser}/status').read_text()
                node=int(next(l.split()[1] for l in status.splitlines() if l.startswith('PPid:')))
                processes=[]
                for role,pid in [('actual CDP_SCOPE browser',browser),('actual browser parent Node',node)]:
                    source=Path(f'/proc/{pid}/exe')
                    processes.append({'role':role,'pid':pid,'exe':str(source.resolve()),'sha256':digest(source),
                        'cmdline':Path(f'/proc/{pid}/cmdline').read_bytes().decode().rstrip('\0').split('\0'),
                        'cwd':str(Path(f'/proc/{pid}/cwd').resolve())})
                assert any(self.profile in value for value in processes[0]['cmdline'])
                self.binding={'observedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'scope':'Observed live during this command, not retrospectively bound to prior runs',
                    'cdpScope':scope,'processes':processes}
            except Exception as error:self.errors.append(repr(error))
            return
    def stop(self):
        self.done.set();self.thread.join(timeout=2)
        return {'liveBinding':self.binding,'errors':self.errors}
