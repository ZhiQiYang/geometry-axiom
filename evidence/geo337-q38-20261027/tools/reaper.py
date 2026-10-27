import ctypes, os
from pathlib import Path

def enable():
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0)!=0:
        raise OSError(ctypes.get_errno(),'PR_SET_CHILD_SUBREAPER')

def reap(excluded):
    result=[]
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit(): continue
        pid=int(entry.name)
        if pid in excluded: continue
        try:
            fields=(entry/'stat').read_text().rsplit(')',1)[1].split()
            if fields[0]!='Z' or int(fields[1])!=os.getpid(): continue
            found,status=os.waitpid(pid,os.WNOHANG)
            if found: result.append({'pid':found,'wait_status':status})
        except (FileNotFoundError,ProcessLookupError,PermissionError,ChildProcessError): pass
    return result

if __name__=='__main__':
    import subprocess,time,json
    enable()
    proc=subprocess.Popen(['sh','-c','sleep 0.1 &'])
    assert proc.wait()==0
    result=[]
    for _ in range(100):
        result.extend(reap({proc.pid}))
        if result: break
        time.sleep(.02)
    assert len(result)==1 and result[0]['wait_status']==0,result
    print(json.dumps({'selftest':'pass','adopted_and_reaped':result}))
