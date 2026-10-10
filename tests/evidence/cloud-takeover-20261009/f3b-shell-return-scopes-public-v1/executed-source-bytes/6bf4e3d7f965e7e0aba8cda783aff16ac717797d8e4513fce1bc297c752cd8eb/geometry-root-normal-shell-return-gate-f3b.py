from pathlib import Path
import argparse, hashlib, importlib.util, json, os, resource, shutil, subprocess, sys

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser()
    for key in ['root', 'url', 'output', 'expected-head', 'bridge', 'model-base', 'feedback-dir']:
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--timeout', type=float, default=180)
    args = parser.parse_args()
    root, output = Path(args.root).resolve(), Path(args.output).resolve()
    assert args.expected_head == 'f3b8285729b42cd22451c98cba1e2ec4514517f3'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == args.expected_head
    assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True) == ''
    observer_source = Path('<workspace-path>')
    driver = Path('<workspace-path>')
    helper = Path('<workspace-path>')
    assert sha(observer_source) == '94a30d7bd7b7f291e3913e5192f5640152ce27b9a80a7adaebe37e3f48b79f70'
    assert sha(driver) == '31d0233a74630ee97fa9fae8a185b0c191f9a7142432306b3fa5cf783421aef1'
    assert sha(helper) == 'ca3ecb98d6091283bb242f4528ae0a47b153888626f7fe1d85479de649e74471'
    ui = load(observer_source, 'original_shell_actor_observer')
    gate = load(root / 'tests/release_gate.py', 'original_shell_release_gate')
    artifacts = Path('/tmp') / (output.name + '-artifacts')
    assert not artifacts.exists() and not output.exists()
    env = dict(os.environ)
    env.update(GEOMETRY_REPO=str(root), GEOMETRY_EXPECTED_SHA=args.expected_head,
               GEOMETRY_TEST_URL=args.url, GEOMETRY_ISOLATED_SERVICE='1',
               GEOMETRY_TEST_BRIDGE=args.bridge, GEOMETRY_BRIDGE=args.bridge,
               GEOMETRY_MODEL_BASE=args.model_base, GEOMETRY_FEEDBACK_DIR=args.feedback_dir,
               GEOMETRY_SHELL_RETURN_OUT=str(artifacts), PYTHONDONTWRITEBYTECODE='1')
    resource.setrlimit(resource.RLIMIT_STACK, (16777216, resource.getrlimit(resource.RLIMIT_STACK)[1]))
    source_files = [p for p in sorted((root / 'geometry-web').iterdir()) if p.is_file() and p.suffix in {'.js', '.css', '.html'}]
    source_files += [root / 'tests/release_gate.py', root / 'tests/binaries.py']
    actual_python = Path('/proc/self/exe').resolve()
    def capture(repo, url, environment):
        record = gate.snapshot(repo, url, environment)
        record['sourceSha256'] = {str(p.relative_to(root)): sha(p) for p in source_files}
        record['executionFiles'] = {str(p): sha(p) for p in [Path(__file__), driver, helper, observer_source]}
        record['executables'] = {role: {'path': str(p), 'sha256': sha(p)} for role, p in
                                [('node', Path(shutil.which('node')).resolve()), ('actual-chrome', Path('/usr/lib/chromium/chromium')), ('python', actual_python)]}
        children = subprocess.check_output(['ps', '--ppid', str(record['runtime']['pid']), '-o', 'pid='], text=True).split()
        record['liveBridge'] = [ui.process_identity(int(pid), 'actual owned direct native bridge') for pid in children]
        assert len(record['liveBridge']) == 1 and record['liveBridge'][0]['executable'] == args.bridge
        assert record['liveBridge'][0]['sha256'] == sha(args.bridge)
        record['actualGatePython'] = ui.process_identity(os.getpid(), 'actual shell probe gate Python')
        return record
    observer = ui.Observer()
    observer.start()
    def run(command, cwd, environment, log, timeout):
        record = {'started': gate.now(), 'exitCode': None, 'timedOut': False, 'interrupted': False}
        child = None
        with Path(log).open('xb') as stream:
            try:
                child = subprocess.Popen(command, cwd=cwd, env=environment, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                record['pid'] = child.pid
                with observer.lock: observer.pid = child.pid
                record['exitCode'] = child.wait(timeout=min(timeout, 180))
            except subprocess.TimeoutExpired:
                record['timedOut'] = True
            finally:
                if child and child.poll() is None:
                    gate.stop_child(child)
                    record['exitCode'] = child.returncode
                record['finished'] = gate.now()
        return record
    command = [shutil.which('node'), str(driver)]
    try:
        code, receipt = gate.run_gate(root, args.url, output, command, env, args.timeout, capture=capture, runner=run)
    finally:
        observed = observer.stop()
    receipt['executionIdentity'] = observed
    lines = (output / 'command.log').read_text().splitlines()
    canonicals = [json.loads(l[len('SHELL_RETURN_RESULT '):]) for l in lines if l.startswith('SHELL_RETURN_RESULT ')]
    result_path = artifacts / 'driver-receipt.json'
    helper_path = artifacts / 'results.json'
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    probe = json.loads(helper_path.read_text()) if helper_path.exists() else {}
    cases = [{'width': 1400, 'family': 'ASM'}, {'width': 1400, 'family': 'SP'}, {'width': 390, 'family': 'ASM'}, {'width': 390, 'family': 'SP'}]
    checks = probe.get('checks', [])
    acceptance = (len(canonicals) == 1 and canonicals[0].get('completed') is True
                  and canonicals[0].get('cases') == cases and canonicals[0].get('passed') == 40 and canonicals[0].get('failed') == 0
                  and result.get('completed') is True and result.get('exitCode') == 0 and result.get('errors') == []
                  and probe.get('completed') is True and len(checks) == 40 and all(c.get('ok') is True for c in checks)
                  and result.get('scope', {}).get('cases') == cases and result.get('helperProbeSHA256') == sha(helper_path)
                  and [{'width': r['width'], 'family': r['family']} for r in probe.get('results', [])] == cases)
    for key in ['sourceSha256', 'executionFiles', 'executables', 'liveBridge', 'actualGatePython']:
        if receipt.get('before', {}).get(key) != receipt.get('after', {}).get(key): receipt['problems'].append(key + ' changed')
    node, chrome = observed.get('node'), observed.get('browser')
    if (not node or not chrome or observed.get('errors') or not chrome['sandboxDisabledFlagsAbsent']
        or node['cmdline'] != command or node['pid'] != receipt.get('execution', {}).get('pid')
        or node['sha256'] != receipt['before']['executables']['node']['sha256']
        or chrome['sha256'] != receipt['before']['executables']['actual-chrome']['sha256']):
        receipt['problems'].append('actual owned Node/Chromium identity incomplete or mismatched')
    receipt['actualScope'] = 'Four normal ASM/SP entry/Cancel/return cases at1400/390; original helper40 strongchecks, exact native and original projectBar identity. Explicit bounded supplement only.'
    receipt['acceptanceResult'] = {'completed': acceptance, 'passed': sum(c.get('ok') is True for c in checks), 'failed': sum(c.get('ok') is not True for c in checks),
                                   'canonicalResults': canonicals, 'driverReceiptPath': str(result_path), 'driverReceiptSHA256': sha(result_path) if result_path.exists() else None,
                                   'helperReceiptPath': str(helper_path), 'helperReceiptSHA256': sha(helper_path) if helper_path.exists() else None}
    receipt['probeVerified'] = code == 0 and not receipt['problems'] and acceptance
    if not receipt['probeVerified'] and code == 0: code = 1
    receipt['gateExitCode'] = code
    archive = output / 'executed-harness-sources'
    for p in source_files + [Path(__file__), driver, helper, observer_source]:
        relative = p.relative_to(root) if p.is_relative_to(root) else Path('scratch-source') / p.name
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'gateExitCode': code, 'probeVerified': receipt['probeVerified'], 'acceptanceResult': receipt['acceptanceResult'], 'receipt': str(output / 'receipt.json')}))
    return code

if __name__ == '__main__': sys.exit(main())
