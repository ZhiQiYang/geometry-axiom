"""Run an unchanged scoped probe with canonical identity/log receipt plus live native binding.

This creates only new evidence outside the repository. It does not launch or
restart any service, and does not infer product completion from an exit code.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--url', required=True)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--model-base', type=Path, required=True)
    parser.add_argument('--feedback-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--expected-cases', type=int, required=True)
    parser.add_argument('--timeout', type=float, default=900)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root.resolve()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    assert command and args.expected_cases > 0
    assert not args.feedback_dir.resolve().is_relative_to(root)
    resource.setrlimit(resource.RLIMIT_STACK, (16777216, resource.getrlimit(resource.RLIMIT_STACK)[1]))
    gate = load(root/'tests/release_gate.py', 'takeover_release_gate')
    environment = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(args.bridge.resolve()),
        GEOMETRY_BRIDGE=str(args.bridge.resolve()), GEOMETRY_MODEL_BASE=str(args.model_base.resolve()),
        GEOMETRY_FEEDBACK_DIR=str(args.feedback_dir.resolve()), GEOMETRY_CHROME='/usr/bin/chromium',
        PYTHONDONTWRITEBYTECODE='1')
    def capture(repo, url, env):
        value = gate.snapshot(repo, url, env)
        value['sources'] = {name: sha(root/name) for name in ['geometry-web/app.js',
            'geometry-web/space-workspace.js', 'geometry-web/app.css', 'geometry-web/index.html',
            'geometry-web/serve.py', 'tests/release_gate.py', 'tests/binaries.py']}
        for source in [Path(__file__), *[Path(a) for a in command if Path(a).is_file()]]:
            value.setdefault('executionFiles', {})[str(source.resolve())] = sha(source)
        try:
            pid = value['runtime']['pid']
            info = subprocess.run(['ps', '-eo', 'pid=,ppid='], capture_output=True, text=True, check=True)
            bridge = args.bridge.resolve()
            children = [{'pid': p, 'parent': parent, 'exe': str(Path(f'/proc/{p}/exe').resolve()),
                        'sha256': sha(f'/proc/{p}/exe')} for p, parent in
                        [tuple(map(int, line.split())) for line in info.stdout.splitlines() if line.strip()]
                        if parent == pid and Path(f'/proc/{p}/exe').resolve() == bridge]
            value['liveBridge'] = children
            assert len(children) == 1 and children[0]['sha256'] == sha(bridge), children
        except Exception as error:
            value['problems'].append('live direct-child bridge: '+str(error))
        return value
    code, receipt = gate.run_gate(root, args.url, args.output, command, environment, args.timeout, capture=capture)
    receipt['harnessScope'] = 'Scoped unchanged probe, synthetic fixtures; not full product acceptance'
    receipt['stackBytes'] = 16777216
    receipt['runnerSha256'] = sha(__file__)
    if receipt.get('before') and receipt.get('after'):
        for key in ['sources', 'executionFiles', 'liveBridge']:
            if receipt['before'].get(key) != receipt['after'].get(key):
                receipt['problems'].append(key+' changed during scoped probe')
    results_path = args.artifact_dir/'results.json'
    if results_path.is_file():
        results = json.loads(results_path.read_text())
        cases = [{'name': r.get('name'), 'ok': r.get('ok') is True,
                  'harnessError': r.get('preconditionOrHarnessError'),
                  'pageErrors': r.get('pageErrors')} for r in results]
    else:
        probe_receipt = args.artifact_dir/'receipt.json'
        probe = json.loads(probe_receipt.read_text()) if probe_receipt.is_file() else {}
        cases = [{'name': f"{r.get('case')}-{r.get('width')}", 'ok': r.get('passed') is True,
                  'harnessError': r.get('error'), 'pageErrors': r.get('page_errors')} for r in probe.get('cases', [])]
        results_path = probe_receipt
    complete = len(cases) == args.expected_cases and all(c['harnessError'] is None for c in cases)
    receipt['probeCensus'] = {'resultsPath': str(results_path),
        'resultsSha256': sha(results_path) if results_path.is_file() else None,
        'expectedCases': args.expected_cases, 'actualCases': len(cases),
        'pass': sum(c['ok'] for c in cases), 'fail': sum(not c['ok'] for c in cases),
        'completed': complete, 'cases': cases}
    if not complete or any(not c['ok'] or c['pageErrors'] for c in cases):
        receipt['probeVerified'] = False
        if code == 0: code = 1
    else: receipt['probeVerified'] = code == 0 and not receipt['problems']
    if receipt['problems'] and code == 0: code = 2
    receipt['gateExitCode'] = code
    (args.output/'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'gateExitCode':code, 'probeVerified':receipt['probeVerified'],
        'probeCensus':receipt['probeCensus'], 'receipt':str(args.output/'receipt.json')}, ensure_ascii=False))
    return code
if __name__ == '__main__': sys.exit(main())
