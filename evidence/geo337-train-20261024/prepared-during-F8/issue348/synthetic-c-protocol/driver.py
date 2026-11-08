"""Real synthetic C/pipe protocol calibration; never compiles or runs a product.

Each command receives a fresh receipt directory. The 0.25-second timeout is a
synthetic hanging-stub control and does not modify the original product 600.
"""
import errno, hashlib, importlib.util, json, os, selectors, shutil, struct
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = Path('/tmp/geo348-command-boundary-diagnostic-tools-20261025')
WRAPPER_SHA = '1a3cb2ae9cc0cad814dce190aae5d7e39f839e9440425f3cf3c33583fc8ed75d'
SIDECAR_SHA = 'f0180d1d40158f5994c4937e6feb786f9494c28315ed72e6929a52badfd12142'
MAX_BYTES = 8 * 1024 * 1024
STATUS = struct.Struct('=8Q')
MAGIC = 0x3334384449414731
PAYLOAD = ('loadfile ' + str(ROOT/'fixture.txt') + '\ndump\nobjects\nreferences\n').encode()
SYNTHETIC_TIMEOUT = 0.25
LAST_FAILURE = None
records, checks = [], []

def sha(raw): return hashlib.sha256(raw).hexdigest()
def write_json(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def check(name, value, **detail):
    checks.append({'name':name, 'passed':bool(value), **detail})
def volume():
    size = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    if size >= MAX_BYTES: raise RuntimeError('Protocol-only artifact budget exceeded')
    return size
def receipt_dir(name):
    path = ROOT/'runs'/name
    path.mkdir(mode=0o700)
    return path
def file_binding(path):
    raw = path.read_bytes()
    return {'path':str(path), 'bytes':len(raw), 'sha256':sha(raw)}
def reaped_pid(run):
    path = run/'pid.txt'
    if not path.exists(): return {'pid_file_present':False, 'no_child':False}
    pid = int(path.read_text())
    try:
        waited = os.waitpid(pid, os.WNOHANG)
        reaped_already = False
        wait_detail = {'unexpected_waitpid_result':list(waited)}
    except ChildProcessError as exc:
        reaped_already = True
        wait_detail = {'waitpid_errno':exc.errno, 'waitpid_error':type(exc).__name__}
    try:
        os.kill(pid, 0)
        absent = False
    except ProcessLookupError:
        absent = True
    return {'pid_file_present':True, 'pid':pid, 'already_reaped':reaped_already,
            'process_absent':absent, 'no_child':reaped_already and absent, **wait_detail}

def command(name, argv, *, payload=None, timeout=10, mode=None, wrapped=False):
    """Use real subprocess.run; return its object or rethrow its exact exception."""
    global LAST_FAILURE
    run = receipt_dir(name)
    env = dict(os.environ)
    env.update(LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONDONTWRITEBYTECODE='1')
    for key in ('GEO348_DIAG_EVENT_FD','GEO348_DIAG_STATUS_FD'):
        env.pop(key, None)
    descriptors = []
    if payload is not None: (run/'stdin.bin').write_bytes(payload)
    if mode is not None:
        env.update(STUB_PID_PATH=str(run/'pid.txt'), STUB_FIXTURE=str(ROOT/'fixture.txt'))
    if wrapped:
        event_fd = os.open(run/'events.jsonl', os.O_RDWR|os.O_CREAT|os.O_EXCL, 0o600)
        status_fd = os.open(run/'status.bin', os.O_RDWR|os.O_CREAT|os.O_EXCL, 0o600)
        descriptors = [event_fd, status_fd]
        assert os.write(status_fd, STATUS.pack(MAGIC,1,0,0,0,0,0,0)) == 64
        env.update(GEO348_DIAG_EVENT_FD=str(event_fd), GEO348_DIAG_STATUS_FD=str(status_fd))
    request = {'schema':'geo348-protocol-only-command/1','name':name,'argv':argv,
               'cwd':str(ROOT),'timeout_seconds':timeout,'synthetic_protocol_only':True,
               'product_process':False,'input':None if payload is None else {'bytes':len(payload),'sha256':sha(payload)},
               'selected_environment':{k:env.get(k) for k in ['LANG','LC_ALL','PYTHONDONTWRITEBYTECODE',
                  'STUB_PID_PATH','STUB_FIXTURE','GEO348_DIAG_EVENT_FD','GEO348_DIAG_STATUS_FD']}}
    write_json(run/'COMMAND.json', request)
    result, failure = None, None
    try:
        result = subprocess.run(argv, input=payload, capture_output=True, timeout=timeout,
                                cwd=ROOT, env=env, pass_fds=tuple(descriptors))
        return result
    except BaseException as exc:
        failure = exc
        LAST_FAILURE = exc
        raise
    finally:
        origin = result if result is not None else failure
        row = {**request,'completed_process_returned':result is not None,
               'returncode':result.returncode if result is not None else None,
               'exception':None if failure is None else {'type':type(failure).__name__,'repr':repr(failure)}}
        for stream in ('stdout','stderr'):
            raw = getattr(origin, stream, None)
            if raw is None: row[stream] = {'captured':False}
            else:
                assert isinstance(raw, bytes)
                (run/(stream+'.bin')).write_bytes(raw)
                row[stream] = {'captured':True,'bytes':len(raw),'sha256':sha(raw)}
        if mode is not None: row['child_after_run'] = reaped_pid(run)
        for fd in descriptors: os.close(fd)
        if wrapped:
            row['events'] = file_binding(run/'events.jsonl')
            row['status'] = file_binding(run/'status.bin')
        write_json(run/'COMMAND_RESULT.json', row)
        records.append({'name':name, **file_binding(run/'COMMAND_RESULT.json')})
        volume()

def run_stub(name, exe, mode='normal', wrapped=True, timeout=10):
    return command(name,[str(exe),mode],payload=PAYLOAD,timeout=timeout,mode=mode,wrapped=wrapped)

def observe(name, *, completed):
    run = ROOT/'runs'/name
    r = sidecar.inspect_events((run/'events.jsonl').read_bytes(),(run/'status.bin').read_bytes(),
                               PAYLOAD,completed=completed)
    write_json(run/'OBSERVATION.json',r)
    return r

def raw_equal(left,right):
    return all((ROOT/'runs'/left/(s+'.bin')).read_bytes()==(ROOT/'runs'/right/(s+'.bin')).read_bytes()
               for s in ['stdout','stderr'])

def pipe_chunks(name, exe):
    """Separate real-Popen pipe observation, explicitly not subprocess.run."""
    run=receipt_dir(name)
    (run/'stdin.bin').write_bytes(PAYLOAD)
    env=dict(os.environ)
    env.update(STUB_PID_PATH=str(run/'pid.txt'),STUB_FIXTURE=str(ROOT/'fixture.txt'))
    efd=os.open(run/'events.jsonl',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600)
    sfd=os.open(run/'status.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600)
    assert os.write(sfd,STATUS.pack(MAGIC,1,0,0,0,0,0,0))==64
    env.update(GEO348_DIAG_EVENT_FD=str(efd),GEO348_DIAG_STATUS_FD=str(sfd))
    argv=[str(exe),'stress']
    request={'schema':'geo348-protocol-only-popen-pipe/1','argv':argv,'cwd':str(ROOT),
             'synthetic_protocol_only':True,'product_process':False,'capture':'Popen+selectors+os.read',
             'timeout_seconds':3,'input_sha256':sha(PAYLOAD)}
    write_json(run/'COMMAND.json',request)
    proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          cwd=ROOT,env=env,pass_fds=(efd,sfd))
    chunks=[];raw={'stdout':bytearray(),'stderr':bytearray()};failure=None
    try:
        proc.stdin.write(PAYLOAD);proc.stdin.close()
        with selectors.DefaultSelector() as sel:
            for stream in ('stdout','stderr'):sel.register(getattr(proc,stream),selectors.EVENT_READ,stream)
            deadline=time.monotonic()+3
            while sel.get_map():
                remaining=deadline-time.monotonic()
                if remaining<=0:raise subprocess.TimeoutExpired(argv,3)
                for key,_ in sel.select(remaining):
                    body=os.read(key.fileobj.fileno(),32768)
                    if not body:sel.unregister(key.fileobj);continue
                    stream=key.data
                    chunks.append({'stream':stream,'offset':len(raw[stream]),'bytes':len(body),
                                   'sha256':sha(body),'monotonic_ns':time.monotonic_ns(),
                                   'ends_with_newline':body.endswith(b'\n')})
                    raw[stream].extend(body)
        proc.wait(timeout=max(0.01,deadline-time.monotonic()))
    except BaseException as exc:
        failure=exc;proc.kill();proc.wait();raise
    finally:
        for stream in ('stdout','stderr'):
            getattr(proc,stream).close();(run/(stream+'.bin')).write_bytes(raw[stream])
        os.close(efd);os.close(sfd)
        write_json(run/'CHUNKS.json',chunks)
        row={**request,'returncode':proc.returncode,'exception':None if failure is None else repr(failure),
             'child_after_run':reaped_pid(run),'stdout':file_binding(run/'stdout.bin'),
             'stderr':file_binding(run/'stderr.bin'),'chunks':file_binding(run/'CHUNKS.json')}
        write_json(run/'COMMAND_RESULT.json',row)
        records.append({'name':name,**file_binding(run/'COMMAND_RESULT.json')})
    return row,chunks

if __name__=='__main__':
    if (ROOT/'runs').exists() or (ROOT/'builds').exists(): raise SystemExit('Fresh run/build directories required')
    (ROOT/'runs').mkdir();(ROOT/'builds').mkdir();(ROOT/'sources').mkdir()
    original=(TOOLS/'trace_wrap.c').read_bytes();assert sha(original)==WRAPPER_SHA
    parser=(TOOLS/'sidecar.py').read_bytes();assert sha(parser)==SIDECAR_SHA
    (ROOT/'sources/trace_wrap.original.c').write_bytes(original)
    (ROOT/'sidecar_snapshot.py').write_bytes(parser)
    (ROOT/'fixture.txt').write_bytes(b'protocol-only fixture\n')
    spec=importlib.util.spec_from_file_location('sidecar_snapshot',ROOT/'sidecar_snapshot.py')
    sidecar=importlib.util.module_from_spec(spec);spec.loader.exec_module(sidecar)
    command('001-cc-version',['/usr/bin/cc','--version'])
    executables={}
    for i,phase in enumerate(['unwrapped','fixed','withdrawn','restored'],2):
        build=ROOT/'builds'/phase;build.mkdir()
        args=['/usr/bin/cc','-std=c11','-O0','-Wall','-Wextra','-Werror',str(ROOT/'stub.c')]
        if phase!='unwrapped':
            body=original
            if phase=='withdrawn':
                needle=b'trace_emit("stdout_flush_return", result, 0, eof_flag, error_flag);'
                assert original.count(needle)==1
                body=original.replace(needle,b'/* PROTOCOL-ONLY NEGATIVE CONTROL: omit flush-return event. */')
            wrapper=build/'trace_wrap.c';wrapper.write_bytes(body)
            args += [str(wrapper),'-Wl,--wrap=fgets','-Wl,--wrap=fflush']
        exe=build/'stub';args += ['-o',str(exe)]
        r=command(f'{i:03}-compile-{phase}',args);check('compile-'+phase,r.returncode==0)
        if r.returncode: raise SystemExit('Synthetic C compile failed; original failure retained')
        executables[phase]=exe
        n=command(f'{i+4:03}-nm-{phase}',['/usr/bin/nm','-a',str(exe)])
        check('nm-'+phase,n.returncode==0)
        if phase!='unwrapped':
            text=n.stdout.decode()
            check('wrap-symbols-'+phase,' T __wrap_fgets\n' in text and ' T __wrap_fflush\n' in text
                  and ' U fgets@' in text and ' U fflush@' in text)
    for j,mode in enumerate(['normal','stress','stdin_error','stdout_error']):
        names=[]
        for which in ['unwrapped','fixed']:
            name=f'{20+j*2+(which=="fixed"):03}-{which}-{mode}'
            r=run_stub(name,executables[which],mode,which!='unwrapped');names.append(name)
            check(name+'-exit',r.returncode==({'stdin_error':23,'stdout_error':24}.get(mode,0)))
            receipt=json.loads((ROOT/'runs'/name/'COMMAND_RESULT.json').read_bytes())
            check(name+'-reaped',receipt['child_after_run']['no_child'])
            if which=='fixed':
                obs=observe(name,completed=r.returncode==0)
                check(name+'-valid-observation',obs['valid'])
                if mode in ['normal','stress']:check(name+'-13-events',len(obs['events'])==13)
                if mode=='stdin_error':check('stdin-error-not-eof',obs['events'][0]['kind']=='stdin_error' and obs['events'][0]['ferror']!=0)
                if mode=='stdout_error':check('flush-error-recorded',obs['events'][-1]['kind']=='stdout_flush_return' and obs['events'][-1]['rc']==-1 and obs['events'][-1]['ferror']!=0)
        check(mode+'-unwrapped-wrapped-raw-equal',raw_equal(*names))
    normal_err=(ROOT/'runs/021-fixed-normal/stderr.bin').read_text()
    check('nonmatching-file-NULL-flush-and-errno',all(x in normal_err for x in [
        'file_ok=1 file_errno='+str(errno.EDOM),'tmp_rc=0 tmp_errno='+str(errno.ERANGE),
        'all_rc=0 all_errno='+str(errno.EOVERFLOW),'bad_null=1 bad_errno='+str(errno.EBADF),
        'read_errno='+','.join([str(errno.EBUSY)]*5),'flush_errno='+','.join([str(errno.ERANGE)]*4)]))
    check('stress-real-256KiB-stderr',(ROOT/'runs/023-fixed-stress/stderr.bin').read_bytes().startswith(b'E'*(256*1024)))
    fault=run_stub('030-event-write-failure',executables['fixed'],'event_write_error')
    fault_obs=observe('030-event-write-failure',completed=True)
    check('observer-write-fault-detected',fault.returncode==0 and not fault_obs['valid']
          and fault_obs['status']['faults']>0)
    check('observer-write-fault-preserves-raw-and-errno',raw_equal('021-fixed-normal','030-event-write-failure'))
    caught=None
    try:run_stub('031-real-timeout-0.25s',executables['fixed'],'hang',timeout=SYNTHETIC_TIMEOUT)
    except subprocess.TimeoutExpired as exc:caught=exc
    check('actual-timeout-original-exception-preserved',caught is not None and caught is LAST_FAILURE and caught.timeout==0.25)
    timeout_row=json.loads((ROOT/'runs/031-real-timeout-0.25s/COMMAND_RESULT.json').read_bytes())
    timeout_obs=observe('031-real-timeout-0.25s',completed=False)
    check('actual-timeout-null-returncode-and-reaped',timeout_row['returncode'] is None and not timeout_row['completed_process_returned'] and timeout_row['child_after_run']['no_child'])
    check('actual-timeout-has-partial-raw',caught is not None and caught.stdout==b'{"ok":true,"command":1}\n{"ok":'
          and caught.stderr==b'synthetic timeout partial stderr\n')
    check('actual-timeout-command2-prefix',timeout_obs['valid'] and len(timeout_obs['events'])==4
          and timeout_obs['last_boundary']['kind']=='stdin_line_returned' and timeout_obs['last_boundary']['command']==2)
    pipe_row,chunks=pipe_chunks('032-real-pipe-chunks',executables['fixed'])
    pipe_obs=observe('032-real-pipe-chunks',completed=True)
    check('real-pipe-stress-reaped-and-observed',pipe_row['returncode']==0 and pipe_row['child_after_run']['no_child'] and pipe_obs['valid'])
    check('real-pipe-raw-equals-run-stress',raw_equal('023-fixed-stress','032-real-pipe-chunks'))
    stdout_chunks=[c for c in chunks if c['stream']=='stdout']
    check('real-stdout-arrived-in-partial-chunks',len(stdout_chunks)>4 and any(not c['ends_with_newline'] for c in stdout_chunks),chunks=len(stdout_chunks))
    proof=[]
    for i,phase in enumerate(['fixed','withdrawn','restored'],40):
        name=f'{i:03}-c-control-{phase}'
        r=run_stub(name,executables[phase]);check(name+'-stub-exit',r.returncode==0)
        check(name+'-raw-equal-baseline',raw_equal('020-unwrapped-normal',name))
        g=command(f'{i+3:03}-guard-{phase}',[sys.executable,'-B',str(ROOT/'guard.py'),'--run',str(ROOT/'runs'/name),'--completed'])
        wanted=1 if phase=='withdrawn' else 0
        check('real-guard-'+phase,g.returncode==wanted)
        proof.append({'phase':phase,'run':name,'guard_run':f'{i+3:03}-guard-{phase}','guard_exit':g.returncode,'guard':json.loads(g.stdout)})
    write_json(ROOT/'C_WITHDRAWAL_PROOF.json',{'schema':'geo348-protocol-only-c-withdrawal/1','phases':proof,'product_gate_verdict':None})
    check('original-wrapper-unchanged',(TOOLS/'trace_wrap.c').read_bytes()==original)
    check('original-parser-unchanged',(TOOLS/'sidecar.py').read_bytes()==parser)
    result={'schema':'geo348-synthetic-c-protocol-only/1','synthetic_protocol_only':True,
            'product_sources_compiled':False,'product_elf_calibrated':False,'n512_executed':False,
            'performance_tested':False,'browser_used':False,'heavy_lock_used':False,
            'synthetic_timeout_seconds':SYNTHETIC_TIMEOUT,'original_product_timeout_seconds_unchanged':600,
            'checks':checks,'exit':int(any(not c['passed'] for c in checks)),
            'original_wrapper':file_binding(TOOLS/'trace_wrap.c'),'original_parser':file_binding(TOOLS/'sidecar.py'),
            'stub':file_binding(ROOT/'stub.c'),'driver':file_binding(ROOT/'driver.py'),
            'guard':file_binding(ROOT/'guard.py'),'commands':records,
            'artifact_bytes_before_result':volume(),
            'limits':['Only this synthetic stub ELF was compiled and calibrated.','No geometry/product source or product ELF was compiled or run.','Original N512, performance, and product gate remain UNRUN.','0.25 seconds applies only to the synthetic hanging stub.']}
    write_json(ROOT/'RESULT.json',result)
    print(json.dumps({'checks':len(checks),'exit':result['exit'],'failed':[c['name'] for c in checks if not c['passed']],
                      'artifact_bytes':volume(),'result_sha256':sha((ROOT/'RESULT.json').read_bytes())}))
    raise SystemExit(result['exit'])
