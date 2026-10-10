"""Execute the committed EDGE harness unchanged; attest its actual private server."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import threading
from urllib.request import urlopen
import cdp_execution_identity as execution_identity

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('<takeover-repository-root>'))
    parser.add_argument('--url',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--bridge',type=Path,default=Path('<configured-native-directory>/bridge'))
    parser.add_argument('--model-base',type=Path,default=Path('<configured-native-directory>/model-base'))
    parser.add_argument('--feedback-dir',default='<isolated-test-directory>')
    parser.add_argument('--expected-checks',type=int,default=38)
    parser.add_argument('--timeout',type=float,default=900)
    args=parser.parse_args()
    root=args.root.resolve();bridge=args.bridge.resolve()
    assert not args.output.resolve().is_relative_to(root)
    resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
    gate=load(root/'tests/release_gate.py','formal_edge_release_gate')
    head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    assert head==args.expected_head,(head,args.expected_head)
    assert subprocess.check_output(['git','-C',str(root),'status','--short'],text=True)==''
    environment=dict(os.environ,GEOMETRY_TEST_BRIDGE=str(bridge),GEOMETRY_BRIDGE=str(bridge),
        GEOMETRY_BRIDGE_EXECUTABLE=str(bridge),GEOMETRY_MODEL_BASE=str(args.model_base.resolve()),
        GEOMETRY_CHROME='/usr/bin/chromium',GEOMETRY_FEEDBACK_DIR=args.feedback_dir,
        PYTHONDONTWRITEBYTECODE='1')
    # Literal python is part of the unchanged formal harness. Record which one it invokes.
    python=shutil.which('python');assert python
    events=[];server={};live_processes=[]
    def process_identity(pid,role):
        path=Path(f'/proc/{pid}/exe')
        return {'role':role,'pid':pid,'exe':str(path.resolve()),'sha256':sha(path),'cmdline':Path(f'/proc/{pid}/cmdline').read_bytes().decode().rstrip('\0').split('\0'),'cwd':str(Path(f'/proc/{pid}/cwd').resolve())}
    def native_binding(runtime):
        response=json.load(urlopen(f"http://127.0.0.1:{server['port']}/runtime",timeout=10))
        assert response==runtime and response['fresh'] is True and Path(response['root']).resolve()==root
        assert runtime['pid']==server['pid']
        parents=subprocess.check_output(['ps','-eo','pid=,ppid='],text=True)
        children=[{'pid':p,'parent':parent,'exe':str(Path(f'/proc/{p}/exe').resolve()),'sha256':sha(f'/proc/{p}/exe')}
                  for p,parent in [tuple(map(int,line.split())) for line in parents.splitlines() if line.strip()]
                  if parent==runtime['pid'] and Path(f'/proc/{p}/exe').resolve()==bridge]
        assert len(children)==1 and children[0]['sha256']==sha(bridge),children
        return {'checkedAt':gate.now(),'runtime':response,'liveBridge':children}
    def execute(command,repo,env,log,timeout):
        started=gate.now()
        child=subprocess.Popen(command,cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                               text=True,bufsize=1,start_new_session=True)
        def collect():
            with log.open('w') as stream:
                for line in child.stdout:
                    stream.write(line);stream.flush()
                    if line.startswith('EDGE_SERVER '):
                        server.update(json.loads(line[len('EDGE_SERVER '):]))
                        try:
                            live_processes.extend([process_identity(child.pid,'Actual Node executing formal EDGE'),process_identity(server['pid'],'Actual literal-python formal service')])
                        except Exception as error:live_processes.append({'error':str(error)})
                    elif line.startswith('EDGE_RUNTIME '):
                        try: events.append(native_binding(json.loads(line[len('EDGE_RUNTIME '):])))
                        except Exception as error: events.append({'error':str(error),'checkedAt':gate.now()})
                    elif line.startswith(('PASS ','FAIL ')) and not any(p.get('role')=='Actual formal Chrome' for p in live_processes):
                        try:
                            parents=subprocess.check_output(['ps','-eo','pid=,ppid='],text=True)
                            found=[process_identity(pid,'Actual formal Chrome') for pid,parent in [tuple(map(int,s.split())) for s in parents.splitlines() if s.strip()] if parent==child.pid and Path(f'/proc/{pid}/cmdline').exists() and ('--remote-debugging-port='+str(server['cdp'])).encode() in Path(f'/proc/{pid}/cmdline').read_bytes()]
                            assert len(found)==1,found;live_processes.extend(found)
                        except Exception as error:live_processes.append({'error':str(error)})
        thread=threading.Thread(target=collect,daemon=True);thread.start()
        timed=False
        try: child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed=True;gate.stop_child(child)
        thread.join(timeout=30)
        return {'started':started,'finished':gate.now(),'exitCode':child.returncode,
                'timedOut':timed,'interrupted':False,'pid':child.pid,'logReaderAlive':thread.is_alive()}
    command=['node','geometry-web/edge_draft_redraw_test.js']
    def capture(repo,url,env):
        # This committed test creates its own server after file preflight.
        # The caller URL is an orchestration label, not a service observation.
        value=gate.snapshot(repo,url,env)
        value['problems']=[p for p in value['problems'] if not p.startswith('runtime')]
        value.pop('runtime',None)
        value['executables']=execution_identity.configured()
        value['literalPython']={'path':python,'resolvedPath':str(Path(python).resolve()),'sha256':sha(python),'version':subprocess.check_output([python,'--version'],text=True).strip()}
        value['runnerSha256']=sha(__file__)
        value['identityObserverSha256']=sha(Path(__file__).with_name('cdp_execution_identity.py'))
        value['sources']={str(p.relative_to(root)):sha(p) for p in sorted((root/'geometry-web').iterdir()) if p.is_file() and p.suffix in {'.js','.css','.html'}}
        value['runtimeObservation']='Owned formal server created after preflight; attested at EDGE_RUNTIME'
        return value
    code,receipt=gate.run_gate(root,args.url,args.output,command,environment,args.timeout,runner=execute,capture=capture)
    receipt['orchestrationUrlArgument']=receipt['url']
    receipt['url']=f"http://127.0.0.1:{server['port']}/" if server else None
    receipt['serviceLifetime']='Committed EDGE harness launches isolated server after file preflight and stops it before final file snapshot; actual runtime/live native are recorded in actualFormalNativeBindings'

    receipt['testedHead']=head
    receipt['formalHarnessSha256']=sha(root/'geometry-web/edge_draft_redraw_test.js')
    receipt['runnerSha256']=sha(__file__)
    receipt['sourceSha256']={name:sha(root/name) for name in ['geometry-web/app.js','geometry-web/space-workspace.js',
                                                          'geometry-web/edge_draft_redraw_test.js']}
    receipt['literalPython']=receipt['before']['literalPython']
    receipt['actualExecutableBindings']=live_processes
    if receipt.get('before') and receipt.get('after'):
        for name in ['executables','literalPython','runnerSha256','identityObserverSha256','sources']:
            if receipt['before'].get(name)!=receipt['after'].get(name):receipt['problems'].append(name+' changed during formal EDGE')
    if len(live_processes)!=3 or any('error' in p for p in live_processes):receipt['problems'].append('Live Node/python/Chrome executable binding missing')
    elif live_processes[0]['sha256']!=receipt['before']['executables']['node']['sha256'] or live_processes[1]['sha256']!=receipt['before']['literalPython']['sha256']:receipt['problems'].append('Actual interpreter does not match configured binary bytes')
    receipt['ownedFormalServer']=server
    receipt['actualFormalNativeBindings']=events
    receipt['stackBytes']=16777216
    lines=(args.output/'command.log').read_text().splitlines()
    canonical=[json.loads(line[len('EDGE_RESULT '):]) for line in lines if line.startswith('EDGE_RESULT ')]
    checks=[line for line in lines if line.startswith(('PASS ','FAIL '))]
    fatal=[line for line in lines if line.startswith('EDGE_FATAL ')]
    original_result=Path(server['feedback']).parent/'result.json' if server else None
    if original_result and original_result.is_file():
        target=args.output/'original-result.json';shutil.copyfile(original_result,target)
        receipt['originalResult']={'originalPath':str(original_result),'copyPath':str(target),'sha256':sha(target)}
    expected=args.expected_checks
    valid=(code==0 and len(canonical)==1 and canonical[0]=={'passed':expected,'failed':0,'completed':True}
           and len(checks)==expected and all(line.startswith('PASS ') for line in checks) and not fatal
           and len(events)==1 and 'error' not in events[0] and not receipt['problems'])
    receipt['formalResult']={'canonical':canonical,'assertionLines':len(checks),'expectedChecks':expected,'fatal':fatal,'verified':valid}
    receipt['scope']='Unchanged EDGE draft/redraw harness; API/internal fixture navigation; real CDP field input; 1400/390 viewport; not full CDP or Windows acceptance'
    if not valid and code==0:code=1
    receipt['gateExitCode']=code
    (args.output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'gateExitCode':code,'formalResult':receipt['formalResult'],'receipt':str(args.output/'receipt.json')}))
    return code
if __name__=='__main__':sys.exit(main())
