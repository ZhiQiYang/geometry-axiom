"""One bounded diagnostic on a private frozen original source, not acceptance."""
import datetime,hashlib,importlib.util,json,os,resource,socket,sys,tempfile,threading
from pathlib import Path
import cdp_execution_identity_v2 as identity

base=Path(__file__).resolve().parent
root=Path('<workspace-path>')
out=base/'diagnose-0b37d8d8-layout-20261009'
spec=importlib.util.spec_from_file_location('diagnostic_release_gate',root/'tests/release_gate.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
profile=tempfile.mkdtemp(prefix='geometry-0b-layout-diagnostic-profile-')
env=dict(os.environ)
for key in list(env):
    if key.startswith('GEOMETRY_') and key.endswith('_ONLY'):env.pop(key)
env.update(GEOMETRY_DIAGNOSTIC_ROOT=str(root),GEOMETRY_TEST_URL='http://127.0.0.1:19190/',GEOMETRY_FEEDBACK_DIR='<isolated-test-directory>',GEOMETRY_TEST_BRIDGE='<isolated-test-directory>',GEOMETRY_BRIDGE='<isolated-test-directory>',GEOMETRY_MODEL_BASE='<isolated-test-directory>',GEOMETRY_REQUIRE_CLEAN='1',GEOMETRY_VERIFY_ROOT=str(root),GEOMETRY_CHROME='/usr/bin/chromium',GEOMETRY_CHROME_PROFILE=profile,GEOMETRY_CDP_PORT=str(port),GEOMETRY_SPACE_TEST_DIR=str(out/'artifacts'),NODE_OPTIONS='--require='+str(base/'full-launch-adapters/sandbox-launch.cjs'),PYTHONDONTWRITEBYTECODE='1')
done=threading.Event();observed={'liveBinding':None,'errors':[]}
def watch():
    while not done.wait(.05):
        log=out/'command.log'
        if not log.exists():continue
        rows=[line for line in log.read_text(errors='replace').splitlines() if line.startswith('DIAGNOSTIC_SCOPE ')]
        if not rows:continue
        try:
            scope=json.loads(rows[0][len('DIAGNOSTIC_SCOPE '):]);pid=scope['browserPid'];exe=str(Path('/proc',str(pid),'exe').resolve(strict=True));argv=identity.cmdline(pid)
            if not identity.is_main_chromium(exe,argv,profile,port):continue
            processes=[identity.process_snapshot('actual owned diagnostic Chromium main process',pid),identity.process_snapshot('actual diagnostic Node driver',scope['nodePid'])]
            assert processes[0]['executableMagicHex']=='7f454c46'
            assert any(arg.endswith('diagnose_adopted_layout.cjs') for arg in processes[1]['cmdline'])
            observed['liveBinding']={'observedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual live diagnostic processes only; not bound to prior full runs','diagnosticScope':scope,'processes':processes};return
        except (FileNotFoundError,ProcessLookupError):continue
        except Exception as error:observed['errors'].append(repr(error));return
def capture(repo,url,environment):
    value=gate.snapshot(repo,url,environment)
    value['executables']=identity.configured()
    value['scratchSha256']={p.name:identity.digest(p) for p in [Path(__file__),base/'diagnose_adopted_layout.cjs',base/'cdp_execution_identity_v2.py',base/'full-launch-adapters/sandbox-launch.cjs']}
    value['sourceSha256']={str(p.relative_to(root)):identity.digest(p) for p in sorted((root/'geometry-web').iterdir()) if p.is_file() and p.suffix in {'.js','.css','.html'}}
    return value
thread=threading.Thread(target=watch,daemon=True);thread.start()
try:code,receipt=gate.run_gate(root,env['GEOMETRY_TEST_URL'],out,['node',str(base/'diagnose_adopted_layout.cjs')],env,300,capture=capture)
finally:done.set();thread.join(timeout=2)
receipt['purpose']='Bounded normal Tab/wheel/summary diagnostic on original 0b; no original oracle/full acceptance claim'
receipt['executionIdentity']=observed
receipt['ownedBrowserProfile']=profile;receipt['ownedCdpPort']=port
receipt['diagnosticResultPath']=str(out/'artifacts/diagnostic-results.json')
if not observed['liveBinding'] or observed['errors']:
    receipt['problems'].append('Actual live diagnostic Node/Chromium identity not established')
    if code==0:code=2;receipt['executionVerified']=False
receipt['gateExitCode']=code
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'gateExitCode':code,'receipt':str(out/'receipt.json'),'identityErrors':observed['errors']}))
sys.exit(code)
