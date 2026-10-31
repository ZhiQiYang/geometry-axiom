#!/usr/bin/env python3
"""以 Linux subreaper 回收本命令產生的孤兒程序，保留主命令退出碼。"""
import ctypes
import errno
import json
import os
from pathlib import Path
import signal
import sys
import time

def main():
    command = sys.argv[1:]
    assert command, '需要命令'
    libc = ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0) != 0:
        raise OSError(ctypes.get_errno(),'PR_SET_CHILD_SUBREAPER')
    flag = ctypes.c_int()
    if libc.prctl(37,ctypes.byref(flag),0,0,0) != 0 or flag.value != 1:
        raise RuntimeError('無法確認 subreaper 已啟用')
    log = Path(os.environ['GEO261_REAPER_LOG'])
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('x',encoding='utf-8') as output:
        def record(value):
            output.write(json.dumps(value,ensure_ascii=False)+'\n')
            output.flush()
        record({'event':'啟用子程序回收','pid':os.getpid(),'pr_get_child_subreaper':flag.value,'command':command,'utc_epoch':time.time()})
        child = os.fork()
        if child == 0:
            output.close()
            os.setsid()
            os.execvp(command[0],command)
        def forward(signum,frame):
            try: os.killpg(child,signum)
            except ProcessLookupError: pass
        signal.signal(signal.SIGINT,forward)
        signal.signal(signal.SIGTERM,forward)
        primary = None
        while True:
            try:
                pid,status = os.waitpid(-1,0)
            except InterruptedError:
                continue
            except ChildProcessError:
                break
            code = os.waitstatus_to_exitcode(status)
            record({'event':'回收','pid':pid,'primary':pid==child,'returncode':code,'utc_epoch':time.time()})
            if pid == child:
                primary = code
        assert primary is not None, '沒有主命令退出碼'
        record({'event':'完成','primary_returncode':primary,'utc_epoch':time.time()})
        return primary if primary >= 0 else 128-primary

if __name__ == '__main__':
    raise SystemExit(main())
