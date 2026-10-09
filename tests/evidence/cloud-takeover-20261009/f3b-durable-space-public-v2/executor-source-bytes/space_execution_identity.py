"""Observe this owned standalone Space profile while it is alive, scratch only."""
import datetime
from pathlib import Path
import threading
from cdp_execution_identity_v2 import configured,cmdline,is_main_chromium,process_snapshot

class Observer:
    def __init__(self,log,profile):
        self.log=Path(log);self.profile=profile;self.done=threading.Event();self.binding=None;self.errors=[]
        self.launcher_stages=[]
        self.thread=threading.Thread(target=self.watch,daemon=True)
    def start(self):self.thread.start()
    def watch(self):
        while not self.done.wait(.05):
            for p in Path('/proc').iterdir():
                if not p.name.isdigit():continue
                try:
                    cmd=cmdline(int(p.name))
                    if not any(self.profile in x for x in cmd) or not any(x.startswith('--remote-debugging-port=') for x in cmd) or any(x.startswith('--type=') for x in cmd):continue
                    port=next(x.split('=',1)[1] for x in cmd if x.startswith('--remote-debugging-port='))
                    exe=str((p/'exe').resolve(strict=True))
                    if not is_main_chromium(exe,cmd,self.profile,port):
                        stage={'pid':int(p.name),'exe':exe,'cmdline':cmd}
                        if stage not in self.launcher_stages:self.launcher_stages.append(stage)
                        continue
                    node=int(next(line.split()[1] for line in (p/'status').read_text().splitlines() if line.startswith('PPid:')))
                    nodecmd=Path('/proc',str(node),'cmdline').read_bytes().decode().rstrip('\0').split('\0')
                    if not any('space_model_test.js' in arg for arg in nodecmd):continue
                    processes=[]
                    for role,pid in [('actual owned Space browser',int(p.name)),('actual browser parent Node',node)]:
                        processes.append(process_snapshot(role,pid))
                    if not is_main_chromium(processes[0]['exe'],processes[0]['cmdline'],self.profile,port):continue
                    assert processes[0]['executableMagicHex']=='7f454c46','Owned Space Chromium is not ELF'
                    assert Path(processes[1]['exe']).name in {'node','nodejs'},'Owned Space parent is not Node'
                    self.binding={'observedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Observed actual owned Space Chromium ELF and its live canonical Node parent; launcher stages excluded','processes':processes}
                    return
                except (FileNotFoundError,ProcessLookupError,PermissionError):continue
                except Exception as error:self.errors.append(repr(error));return
    def stop(self):
        self.done.set();self.thread.join(timeout=2)
        return {'liveBinding':self.binding,'errors':self.errors,'excludedLauncherStages':self.launcher_stages}
