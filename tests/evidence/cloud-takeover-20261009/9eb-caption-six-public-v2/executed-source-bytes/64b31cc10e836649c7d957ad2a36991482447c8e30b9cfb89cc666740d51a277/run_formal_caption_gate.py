"""Read-only product acceptance execution; writes only scratch/TEMP evidence."""
import argparse
import datetime
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

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def process_identity(pid, role):
    proc = Path('/proc') / str(pid)
    return {'role': role, 'pid': pid, 'executable': str((proc/'exe').resolve()),
            'sha256': sha(proc/'exe'), 'cwd': str((proc/'cwd').resolve()),
            'cmdline': (proc/'cmdline').read_bytes().decode().rstrip('\0').split('\0')}

class Observer:
    def __init__(self):
        self.done = threading.Event()
        self.lock = threading.Lock()
        self.pid = None
        self.node = None
        self.browser = None
        self.errors = []
        self.thread = threading.Thread(target=self.watch, daemon=True)

    def start(self):
        self.thread.start()

    def watch(self):
        while not self.done.wait(.05):
            with self.lock:
                pid = self.pid
            if not pid:
                continue
            try:
                if self.node is None:
                    self.node = process_identity(pid, 'actual test Node process')
                rows = subprocess.check_output(['ps','-eo','pid=,ppid='], text=True)
                parents = [tuple(map(int, line.split())) for line in rows.splitlines() if line.strip()]
                descendants = {pid}
                for _ in range(8):
                    new = {child for child,parent in parents if parent in descendants}
                    if new <= descendants:
                        break
                    descendants |= new
                if self.browser is None:
                    for child in sorted(descendants - {pid}):
                        try:
                            record = process_identity(child, 'actual sandboxed Chromium browser')
                            args = record['cmdline']
                            if record['executable'] == '/usr/lib/chromium/chromium' and not any(a.startswith('--type=') for a in args):
                                profile = next(a.split('=',1)[1] for a in args if a.startswith('--user-data-dir='))
                                record['ownedProfile'] = profile
                                record['sandboxDisabledFlagsAbsent'] = all(a not in {'--no-sandbox','--disable-setuid-sandbox'} for a in args)
                                record['observedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                                self.browser = record
                                break
                        except (FileNotFoundError, ProcessLookupError, StopIteration):
                            continue
            except (FileNotFoundError, ProcessLookupError):
                continue
            except Exception as error:
                self.errors.append(repr(error))

    def stop(self):
        self.done.set()
        self.thread.join(timeout=2)
        return {'node': self.node, 'browser': self.browser, 'errors': self.errors}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['ui123'], required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--probe-source', type=Path)
    parser.add_argument('--probe-sha256')
    parser.add_argument('--ui-groups', default='caption')
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=1800)
    args = parser.parse_args()
    root = args.root.resolve()
    formal_script = root/'tests'/'issue123_caption_browser.cjs'
    script = formal_script
    assert args.probe_source is None and args.probe_sha256 is None, 'This runner executes only the committed caption test'
    assert formal_script.is_file()
    committed = subprocess.check_output(['git','-C',str(root),'show','HEAD:tests/issue123_caption_browser.cjs'])
    assert sha(formal_script) == hashlib.sha256(committed).hexdigest()
    bridge = Path('<isolated-test-directory>')
    model = Path('<isolated-test-directory>')
    core = Path('<isolated-test-directory>')
    feedback = '<isolated-test-directory>'
    original_groups = ['colors','headers','components','v3','grid-mobile','model']
    supplemental_groups = ['caption']
    groups = args.ui_groups.split(',')
    assert groups and len(groups)==len(set(groups))
    assert args.suite=='ui123' and groups==['caption'], 'Only the committed seven-width caption scope is permitted'
    scenarios = ['pdf-rectangle','pdf-l','pdf-notch','image-rectangle','image-l','image-notch','image-rectangle-box','pdf-l-mobile','image-notch-mobile','pdf-l-transform']
    assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip() == args.expected_sha
    assert subprocess.check_output(['git','-C',str(root),'status','--porcelain'], text=True) == ''
    assert not args.artifacts.exists()
    resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
    gate = load(root/'tests/release_gate.py','ui_verification_gate')
    environment = dict(os.environ)
    for key in ['GEOMETRY_ROOM_SCENARIOS','GEOMETRY_ROOM_EXTRA_CASES','GEOMETRY_UI123_GROUPS']:
        environment.pop(key,None)
    environment.update(GEOMETRY_REPO=str(root), GEOMETRY_EXPECTED_SHA=args.expected_sha,
                       GEOMETRY_ISOLATED_SERVICE='1', GEOMETRY_TEST_BRIDGE=str(bridge),
                       GEOMETRY_BRIDGE=str(bridge), GEOMETRY_MODEL_BASE=str(model),
                       GEOMETRY_FEEDBACK_DIR=feedback, GEOMETRY_CHROME='/usr/bin/chromium',
                       PYTHONDONTWRITEBYTECODE='1')
    if args.suite == 'ui123':
        environment.update(GEOMETRY_UI123_OUT=str(args.artifacts), GEOMETRY_UI123_GROUPS=','.join(groups))
    else:
        environment['GEOMETRY_ROOM_ACCEPTANCE_DIR'] = str(args.artifacts)
    def configured():
        result = {}
        for role,command in [('node',shutil.which('node')),('python',sys.executable),('chrome-launcher','/usr/bin/chromium'),('actual-chrome','/usr/lib/chromium/chromium')]:
            resolved = Path(command).resolve()
            result[role] = {'path':str(command), 'resolved':str(resolved), 'sha256':sha(resolved)}
            if role != 'actual-chrome':
                result[role]['version'] = subprocess.check_output([command,'--version'],stderr=subprocess.STDOUT,text=True).strip()
        return result
    def capture(repo,url,env):
        value = gate.snapshot(repo,url,env)
        value['executables'] = configured()
        value['sources'] = {str(p.relative_to(root)):sha(p) for folder in ['geometry-web','tests'] for p in sorted((root/folder).iterdir()) if p.is_file() and p.suffix in {'.js','.cjs','.css','.html','.py'}}
        value['runnerSHA256'] = sha(__file__)
        value['executionFiles'] = {str(script):sha(script),str(formal_script):sha(formal_script)}
        if args.probe_source and sha(script)!=args.probe_sha256:
            value['problems'].append('explicit approved probe SHA mismatch')
        value['configuredNativeCore'] = {'path':str(core), 'sha256':sha(core)}
        try:
            server = value['runtime']['pid']
            rows = subprocess.check_output(['ps','--ppid',str(server),'-o','pid='],text=True).split()
            children = [process_identity(int(pid),'actual service direct child bridge') for pid in rows]
            matching = [r for r in children if r['executable']==str(bridge)]
            assert len(matching)==1 and matching[0]['sha256']==sha(bridge), children
            value['liveBridge'] = matching
        except Exception as error:
            value['problems'].append('live bridge identity: '+str(error))
        return value
    observer = Observer()
    observer.start()
    def runner(command,cwd,env,log,timeout):
        record = {'started':gate.now(), 'exitCode':None, 'timedOut':False, 'interrupted':False}
        child = None
        with Path(log).open('xb') as stream:
            try:
                child = subprocess.Popen(command,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                record['pid'] = child.pid
                with observer.lock:
                    observer.pid = child.pid
                record['exitCode'] = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record['timedOut'] = True
            except Exception as error:
                record['error'] = repr(error)
            finally:
                if child and child.poll() is None:
                    gate.stop_child(child)
                    record['exitCode'] = child.returncode
                record['finished'] = gate.now()
        return record
    command = [shutil.which('node'),str(script)]
    try:
        code,receipt = gate.run_gate(root,args.url,args.output,command,environment,args.timeout,capture=capture,runner=runner)
    finally:
        observed = observer.stop()
    receipt['executionIdentity'] = observed
    receipt['scopeEnvironment'] = {key:value for key,value in environment.items() if key.startswith('GEOMETRY_')}
    receipt['actualScope'] = ('six adopted UI groups with independently pinned oracle source; not all #123, full CDP or full space'
        if groups==original_groups else 'Explicit separate supplemental UI groups: '+','.join(groups)) if args.suite=='ui123' else 'all ten original normal scenarios plus all original negative cases; six measured canonical cost cases'
    receipt['testSourceProvenance'] = {'productFullSHA':args.expected_sha,'productDirtyBefore':receipt.get('before',{}).get('git',{}).get('status'),
        'executedProbe':str(script),'executedProbeSHA256':sha(script),'formalCandidateProbe':str(formal_script),
        'formalCandidateProbeSHA256':sha(formal_script),'sourceOverride':bool(args.probe_source),
        'approvedOverrideExpectedSHA256':args.probe_sha256,
        'productBeforeAfterIdentityMatches':receipt.get('before',{}).get('git')==receipt.get('after',{}).get('git')
            and receipt.get('before',{}).get('sources')==receipt.get('after',{}).get('sources'),
        'note':'The committed caption test executes without source override. Its seven-width result is separate from the original six groups and full CDP; original scratch failures retain their original identities.'}
    receipt['stackBytes'] = 16777216
    if not observed['node'] or not observed['browser'] or not observed['browser']['sandboxDisabledFlagsAbsent'] or observed['errors']:
        receipt['problems'].append('actual Node/browser sandbox identity was not completely established')
    before,after = receipt.get('before'),receipt.get('after')
    if before and observed['node'] and observed['browser']:
        node,chrome=observed['node'],observed['browser']
        configured_node=before['executables']['node']
        configured_chrome=before['executables']['actual-chrome']
        if (node['sha256']!=configured_node['sha256'] or node['executable']!=configured_node['resolved']
                or node['cmdline']!=command or node['cwd']!=str(root)
                or node['pid']!=receipt.get('execution',{}).get('pid')):
            receipt['problems'].append('actual Node executable/command/cwd/pid differs from pinned execution')
        if chrome['sha256']!=configured_chrome['sha256'] or chrome['executable']!=configured_chrome['resolved']:
            receipt['problems'].append('actual Chrome executable differs from pinned configured bytes')
    if before and after:
        for key in ['executables','sources','runnerSHA256','configuredNativeCore','liveBridge','executionFiles']:
            if before.get(key)!=after.get(key):
                receipt['problems'].append(key+' changed during the actual test command')
    log = args.output/'command.log'
    probe = args.artifacts/('receipt.json' if args.suite=='ui123' else 'results.json')
    structured = json.loads(probe.read_text()) if probe.is_file() else {}
    summary = {'completed':False,'passed':0,'failed':0,'probePath':str(probe),'probeSHA256':sha(probe) if probe.is_file() else None}
    if args.suite=='ui123':
        rows = structured.get('groupResults',[])
        summary.update(attemptedAllGroups=structured.get('completed') is True, groupResults=rows,
                       passed=structured.get('passed',0), failed=structured.get('failed',0))
        results=structured.get('results',[])
        counts={name:sum(r.get('group')==name for r in results) for name in ['preflight',*groups,'final']}
        actual_pass=sum(r.get('ok') is True for r in results)
        actual_fail=sum(r.get('ok') is not True for r in results)
        scope=structured.get('run',{}).get('scope',{})
        lines=log.read_text(errors='replace').splitlines()
        canonical=[json.loads(line[len('UI123_RESULT '):]) for line in lines if line.startswith('UI123_RESULT ')]
        summary['canonicalResults']=canonical
        canonical_agrees=(len(canonical)==1 and canonical[0].get('completed') is True
            and canonical[0].get('passed')==summary['passed'] and canonical[0].get('failed')==summary['failed']
            and canonical[0].get('exitCode')==structured.get('run',{}).get('exitCode')
            and canonical[0].get('groupResults')==rows and canonical[0].get('scope')==scope)
        census=(len(results)>0 and actual_pass==summary['passed'] and actual_fail==summary['failed']
                and set(r.get('group') for r in results)==set(counts)
                and all(r.get('checks')==counts.get(r.get('group')) and r.get('checks',0)>0 for r in rows))
        summary['independentCensus']={'counts':counts,'passed':actual_pass,'failed':actual_fail,'agrees':census}
        summary['completed'] = (structured.get('completed') is True and [r.get('group') for r in rows]==groups
                and all(r.get('ok') is True for r in rows) and census and actual_fail==0
                and scope.get('included')==groups and canonical_agrees
                and scope.get('omitted')==original_groups
                and structured.get('run',{}).get('scriptSHA256')==sha(script))
    else:
        lines = log.read_text(errors='replace').splitlines()
        done = [line.split()[1] for line in lines if line.startswith('SCENARIO_DONE ')]
        canonical = [json.loads(line[len('ACCEPTANCE_RESULT '):]) for line in lines if line.startswith('ACCEPTANCE_RESULT ')]
        checks = structured.get('results',[])
        summary.update(normalScenariosCompleted=done,canonicalResults=canonical,
                       passed=sum(r.get('ok') is True for r in checks),failed=sum(r.get('ok') is not True for r in checks),
                       measurements=structured.get('measurements',[]),errors=structured.get('errors',[]))
        negative_names=[
            'image-open-doorway: explicit failure leaves original scene and no completion receipt',
            'image-neighbor: connected neighbor is disclosed instead of silently excluded',
            'image-neighbor: explicit search separator excludes neighbor without editing source geometry',
            'native-rejection-and-source-change: core rejects self-crossing orthogonal ring without changing original',
            'native-rejection-and-source-change: recalibration requires review and retains exact confirmed geometry',
            'native-rejection-and-source-change: source replacement retains exact geometry and becomes unreviewed']
        negatives=[{'name':name,'matches':sum(r.get('name')==name for r in checks),
                    'ok':sum(r.get('name')==name and r.get('ok') is True for r in checks)==1} for name in negative_names]
        census=(len(checks)>0 and len(canonical)==1 and canonical[0].get('checks')==len(checks)
                and canonical[0].get('failures')==summary['failed'])
        summary['independentCensus']={'total':len(checks),'agrees':census,'negativeAssertions':negatives}
        summary['completed'] = (len(canonical)==1 and canonical[0].get('ok') is True and done==scenarios
                and [r.get('scenario') for r in summary['measurements']]==scenarios[:6]
                and all(r['matches']==1 and r['ok'] for r in negatives)
                and census and summary['failed']==0 and summary['errors']==[])
    receipt['acceptanceResult'] = summary
    receipt['probeVerified'] = code==0 and not receipt['problems'] and summary['completed'] and summary['failed']==0
    if not receipt['probeVerified'] and code==0:
        code = 1
    receipt['gateExitCode'] = code
    (args.output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'gateExitCode':code,'probeVerified':receipt['probeVerified'],'acceptanceResult':summary,'receipt':str(args.output/'receipt.json')},ensure_ascii=False))
    return code

if __name__=='__main__':
    sys.exit(main())
