from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def need(value,message):
    if not value:raise RuntimeError(message)
def main():
    need(digest(ROOT/'collect.py')=='004f29e9f8097394f6909869d406a6b1fc0d38bd053b1ace8cc302ad80403e0d','frozen collector')
    need(digest(ROOT/'PLAN.json')=='8c7758c125b3dc83ff10ae57dbeef85e3641f9d4648cd66f956c6bd46a290742','frozen membership plan')
    plan=json.loads((ROOT/'PLAN.json').read_bytes())
    pin=plan['terminal_bindings']['outer'];terminal=Path(pin['path'])
    need(digest(terminal)==pin['sha256'] and terminal.stat().st_size==pin['bytes'],'original R8 terminal pin')
    k=json.loads(terminal.read_bytes())
    need(k['source_sha']=='75a1e93811a52b69385cbdaf6a09d773ed9052ad' and type(k['exit']) is int and k['exit']==plan['expected_terminal']['outer_exit'],'actual R8 terminal before heavy collection')
    held=None;slot=None
    for name in ['/tmp/g261r3/heavy.lock','/tmp/g261r3/secondary.lock']:
        handle=open(name,'a+b')
        try:fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:handle.close();continue
        held=handle;slot=name;break
    need(held is not None,'Both shared heavy slots are busy; no collector started, no sleep or retry loop.')
    try:
        out=ROOT/'execution';out.mkdir(exist_ok=False)
        command=[sys.executable,'-B',str(ROOT/'collect.py')]
        request={'command':command,'cwd':str(ROOT),'heavy_slot':slot,'environment':{n:os.environ.get(n) for n in ['PATH','LANG','LC_ALL','TMPDIR','PYTHONPATH','PYTHONOPTIMIZE']},'source_sha':'75a1e93811a52b69385cbdaf6a09d773ed9052ad','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subject_executed':False}
        (out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
        with (out/'stdout').open('wb') as stdout,(out/'stderr').open('wb') as stderr:
            result=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr)
        request.update(actual_process_exit=result.returncode,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=digest(out/'stdout'),stderr_sha256=digest(out/'stderr'))
        (out/'RESULT.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'actual_process_exit':result.returncode,'out':str(ROOT)},ensure_ascii=False));return result.returncode
    finally:fcntl.flock(held.fileno(),fcntl.LOCK_UN);held.close()
if __name__=='__main__':raise SystemExit(main())
