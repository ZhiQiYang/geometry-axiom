"""Synthetic recorder contracts only; no product compilation or benchmark."""
from pathlib import Path
import argparse, importlib.util, json, os, subprocess, sys
from unittest import mock


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tools',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--only',choices=['all','pipe','defer'],default='all')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(args.tools))
    import geo323_record as capture
    spec=importlib.util.spec_from_file_location('fidelity_driver',args.tools/'run.py')
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    checks=[]
    def check(name,value):
        checks.append({'name':name,'passed':bool(value)})
        assert value,name
    env=dict(os.environ,GEO323_BASE_SHA='b'*40,GEO323_MAIN_SHA='c'*40)
    def recorder(name):return capture.Recorder(args.out/name,args.out,'a'*40,env)
    original_run=capture._ORIGINAL_RUN

    if args.only in ('all','pipe'):
        # Pure Python child describes its actual OS descriptor types. No sleep,
        # timing threshold, C compiler or product test can make this pass.
        code='import os,stat,json,sys;sys.stdout.write(json.dumps({"stdout_fifo":stat.S_ISFIFO(os.fstat(1).st_mode),"stderr_fifo":stat.S_ISFIFO(os.fstat(2).st_mode),"stdin_fifo":stat.S_ISFIFO(os.fstat(0).st_mode),"same_session":os.getsid(0)==os.getsid(os.getppid())}));sys.stderr.buffer.write(b"original\\x00\\xff\\r\\n")'
        argv=[sys.executable,'-B','-c',code]
        direct=subprocess.run(argv,input=b'',capture_output=True,timeout=5)
        rec=recorder('pipe');result=rec.run(argv,input=b'',capture_output=True,timeout=5)
        a,b=json.loads(direct.stdout),json.loads(result.stdout)
        check('original caller uses actual PIPE descriptors',all(a.values()))
        check('recorded child stdout/stderr remain original PIPE',b['stdout_fifo'] and b['stderr_fifo'])
        check('original stdin and process session preserved',b==a)
        check('original binary stderr preserved',result.stderr==direct.stderr==b'original\x00\xff\r\n')
        check('actual child exit preserved',result.returncode==direct.returncode==0)
        row=rec.rows[0];d=Path(row['directory'])
        check('complete persisted raw stdout/stderr', (d/'stdout.bin').read_bytes()==result.stdout and (d/'stderr.bin').read_bytes()==result.stderr and row['recording_complete'])

    if args.only in ('all','defer'):
        rec=recorder('driver-defer')
        marker=ValueError('synthetic original perf assertion')
        cp=subprocess.CompletedProcess(['synthetic'],0,b'full\x00\xff',b'stderr')
        session=object.__new__(driver.Session)
        session.a=argparse.Namespace(repo=args.out)
        session.work=args.out;session.evidence=args.out;session.r=rec
        session.require_binaries=lambda labels:check('driver original three binary precondition',labels==('base','fix','main'))
        class FakeVerifier:
            def perf(self,*original_args):
                check('driver forwards original perf arguments',original_args==(args.out,args.out,args.out))
                got=rec.run(['synthetic'],input=b'loadfile original.scene\n',timeout=600)
                check('original CompletedProcess identity in perf',got is cp)
                check('no recorder disk serialization inside original perf',list(rec.root.iterdir())==[])
                raise marker
        session.v=FakeVerifier()
        with mock.patch.object(capture,'_ORIGINAL_RUN',return_value=cp):
            try:session.perf()
            except ValueError as got:check('same original perf assertion preserved',got is marker)
            else:raise AssertionError('original perf exception swallowed')
        check('finally flush retains original result after perf failure',rec.rows[0]['recording_complete'] and (Path(rec.rows[0]['directory'])/'stdout.bin').read_bytes()==cp.stdout)

    if args.only=='all':
        rec=recorder('identity');calls=[]
        argv=['synthetic'];data=b'\x00\xff\r\n';explicit_env={'LANG':'C','SYNTHETIC':'yes'};cwd=args.out
        preexec=lambda:None
        cp=subprocess.CompletedProcess(argv,7,b'binary\x00\xff',b'err\r\n')
        def fake(*a,**kw):calls.append((a,kw));return cp
        real_dump,real_sha=capture.dump,capture.sha;writes=[];hashes=[]
        def traced_dump(*a,**kw):writes.append(a[0]);return real_dump(*a,**kw)
        def traced_sha(*a,**kw):hashes.append(len(a[0]));return real_sha(*a,**kw)
        with mock.patch.object(capture,'_ORIGINAL_RUN',side_effect=fake),mock.patch.object(capture,'dump',side_effect=traced_dump),mock.patch.object(capture,'sha',side_effect=traced_sha):
            with rec.defer_flush():
                def no_fixture_io(*a,**kw):raise AssertionError('fixture/source file I/O inside timed original call')
                with mock.patch.object(Path,'read_bytes',side_effect=no_fixture_io),mock.patch.object(Path,'stat',side_effect=no_fixture_io),mock.patch.object(Path,'rglob',side_effect=no_fixture_io):
                    got=rec.run(argv,cwd=cwd,input=data,env=explicit_env,preexec_fn=preexec,timeout=600,check=False)
                check('normal CP and binary object identities preserved',got is cp and got.stdout is cp.stdout)
                check('no hash or JSON serialization before original perf returns',not writes and not hashes and not list(rec.root.iterdir()))
                a,k=calls[0]
                check('exact caller argv/input/env/cwd/preexec identities',a[0] is argv and k['input'] is data and k['env'] is explicit_env and k['cwd'] is cwd and k['preexec_fn'] is preexec)
                check('original timeout/check/capture flags unchanged',k['timeout']==600 and k['check'] is False and k['capture_output'] is True and k['text'] is False)
                check('no injected stdio/session/group options',not any(x in k for x in ['stdin','stdout','stderr','start_new_session','process_group']))
            check('deferred writes and hashes happen after return boundary',bool(writes) and bool(hashes) and rec.rows[0]['recording_complete'])
        check('original nonzero return not converted to failure',rec.rows[0]['actual_process_returncode']==7 and len(calls)==1)

        for label,error in [('check',subprocess.CalledProcessError(9,['synthetic'],output=b'failure-out',stderr=b'failure-err')),
                            ('timeout',subprocess.TimeoutExpired(['synthetic'],600,output=b'partial\x00\xff',stderr=b'partial-err')),
                            ('launch',FileNotFoundError('synthetic missing executable'))]:
            rec=recorder(label)
            with mock.patch.object(capture,'_ORIGINAL_RUN',side_effect=error) as run:
                try:rec.run(['synthetic'],input=b'x',check=label=='check',timeout=600)
                except BaseException as got:check(label+' same original exception identity',got is error)
                else:raise AssertionError(label+' original exception swallowed')
                check(label+' exactly one original invocation',run.call_count==1)
            row=rec.rows[0]
            check(label+' observer complete does not invent product success',row['recording_complete'] and row['original_exception_type']==type(error).__name__)
            if label=='timeout':
                check('timeout true child return remains unknown not guessed -9',row['actual_process_returncode'] is None and row['timeout_expired'] and not row['original_process_completed'])
                check('timeout exposes original partial bytes explicitly', (Path(row['directory'])/'stdout.bin').read_bytes()==error.stdout and 'not a claim of all bytes after kill' in row['timeout_output_scope'])
            if label=='launch':check('absent outputs not claimed empty child streams',not row['stdout_available_from_original'] and not row['stderr_available_from_original'])

        rec=recorder('read-output-false')
        with mock.patch.object(capture,'_ORIGINAL_RUN',return_value=cp):result=rec.run(argv,read_output=False)
        check('storage-only read_output false legacy result',result.returncode==7 and result.stdout==result.stderr==b'')
        check('storage-only full original binary retained', (Path(rec.rows[0]['directory'])/'stdout.bin').read_bytes()==cp.stdout)

        for deferred in (False,True):
            rec=recorder('flush-failure-'+str(deferred));subject=subprocess.TimeoutExpired(['synthetic'],600,output=b'partial')
            storage=OSError('synthetic disk failure')
            def fail_result(path,value):
                if Path(path).name=='result.json':raise storage
                return real_dump(path,value)
            with mock.patch.object(capture,'_ORIGINAL_RUN',side_effect=subject),mock.patch.object(capture,'dump',side_effect=fail_result):
                try:
                    if deferred:
                        with rec.defer_flush():rec.run(['synthetic'],timeout=600)
                    else:rec.run(['synthetic'],timeout=600)
                except BaseException as got:check('flush failure preserves original timeout '+str(deferred),got is subject)
                else:raise AssertionError('subject timeout was swallowed by recording failure')
            check('flush failure explicitly marks incomplete '+str(deferred),bool(rec.recording_errors) and not rec.rows[0]['recording_complete'])
            check('failed raw input remains retained in memory '+str(deferred),bool(rec._pending) and rec._pending[0]['stdout']==b'partial')

        rec=recorder('flush-failure-after-success');storage=OSError('synthetic failed successful-result flush')
        with mock.patch.object(capture,'_ORIGINAL_RUN',return_value=cp),mock.patch.object(capture,'dump',side_effect=storage):
            try:
                with rec.defer_flush():rec.run(argv)
            except OSError as got:check('successful child cannot hide recording failure',got is storage)
            else:raise AssertionError('recording failure incorrectly passed')
        check('original successful/nonzero return remains exact despite flush failure',rec.rows[0]['actual_process_returncode']==7)

        # Real binary subprocess regression with output exceeding pipe capacity.
        rec=recorder('large-pipe');payload=b'\x00\xff\r\n'*24576
        argv=[sys.executable,'-B','-c','import sys;d=sys.stdin.buffer.read();sys.stdout.buffer.write(d);sys.stderr.buffer.write(d[::-1]);sys.exit(6)']
        direct=subprocess.run(argv,input=payload,capture_output=True,timeout=5)
        got=rec.run(argv,input=payload,timeout=5)
        check('large actual pipe binary equivalence without deadlock',got.returncode==direct.returncode==6 and got.stdout==direct.stdout==payload and got.stderr==direct.stderr==payload[::-1])

        rec=recorder('inherited-stdin')
        argv=[sys.executable,'-B','-c','import os,json;v=os.fstat(0);print(json.dumps([v.st_dev,v.st_ino]))']
        got=rec.run(argv,timeout=5)
        parent=os.fstat(0)
        check('input None inherits original stdin descriptor',json.loads(got.stdout)==[parent.st_dev,parent.st_ino])

        rec=recorder('real-timeout')
        argv=[sys.executable,'-B','-c','import sys,time;sys.stdout.buffer.write(b"prefix\\x00\\xff");sys.stdout.flush();time.sleep(30)']
        try:rec.run(argv,timeout=.02)
        except subprocess.TimeoutExpired as original:
            check('real stdlib timeout retains exact original limit',original.timeout==.02)
            row=rec.rows[0];body=(Path(row['directory'])/'stdout.bin').read_bytes()
            check('real timeout exposed bytes and unknown true OS exit explicit',body==(original.stdout or b'') and row['actual_process_returncode'] is None and row['timeout_expired'])
        else:raise AssertionError('synthetic sleeping child should reach original timeout')

    result={'scope':'Synthetic external recorder contracts; no C/product/performance samples',
            'only':args.only,'checks':len(checks),'passed':all(x['passed'] for x in checks),
            'details':checks,'product_tests_executed':False,'C_executed':False}
    (args.out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(checks),'passed':result['passed'],'only':args.only}))


if __name__=='__main__':main()
