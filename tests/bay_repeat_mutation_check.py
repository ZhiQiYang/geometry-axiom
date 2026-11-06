"""R06 finite mutation manifest, using main's strict named-assertion judge.

    python3 tests/bay_repeat_mutation_check.py --check
    python3 tests/bay_repeat_mutation_check.py --out /tmp/r06-mutations
    python3 tests/bay_repeat_mutation_check.py --kind native --out /tmp/r06-native

Only disposable, byte-snapshotted sources are patched. Each kind first runs all
its R06 oracles green, each mutant must fail its one declared assertion, and a
restored build runs every oracle green again. Missing tools, compiler failures,
browser bootstrap failures, transport errors, skips, crashes and wrong first
assertions are never kills. Browser cases use the registered cdp_test.js assembly
scope, including the real download and fresh-process Open tests.
"""
from __future__ import annotations
import argparse
import ast
from contextlib import ExitStack
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import assembly_mutation_check as oracle

MANIFEST = 'tests/bay_repeat_mutations.json'
NATIVE_FILE = 'tests/test_assembly_bay_repeat.py'
NATIVE_MODULE = 'tests.test_assembly_bay_repeat'
PREFIX = NATIVE_MODULE + '.BayRepeat.'
NODE_ADAPTER = 'tests/bay_repeat_node_runner.cjs'
SELF = 'tests/bay_repeat_mutation_check.py'


def load_manifest(root=ROOT):
    value = json.loads((Path(root) / MANIFEST).read_text(encoding='utf-8'))
    if value.get('schema') != 'assembly-bay-repeat-mutations/1':
        raise ValueError('unknown R06 mutation manifest schema')
    return value


def static_problems(root=ROOT, manifest=None):
    manifest = load_manifest(root) if manifest is None else manifest
    cases = manifest['cases']
    problems = []
    names = [c['name'] for c in cases]
    if len(names) != len(set(names)):
        problems.append('duplicate mutation name')
    native = [(c['name'], [(p['file'], p['before'], p['after']) for p in c['patches']],
               c['test'].removeprefix(PREFIX), c['assertion']) for c in cases if c['kind'] == 'native']
    problems += oracle.binding_problems(oracle.read_lf(root, NATIVE_FILE), native, [], manifest['nativeTags'])
    entries = [(c['name'], [(p['file'], p['before'], p['after']) for p in c['patches']]) for c in cases]
    problems += oracle.anchor_problems(root, entries, [])
    for case in cases:
        if case['kind'] not in ('native', 'node', 'browser'):
            problems.append(case['name'] + ': unknown kind')
        if not case.get('covers') or any(not re.fullmatch(r'BR(?:0[1-9]|1[0-6])(?:N|b)?', area) for area in case['covers']):
            problems.append(case['name'] + ': missing or invalid BR coverage')
        for item in case['patches']:
            path = Path(item['file'])
            if path.is_absolute() or '..' in path.parts or path.parts[0] == 'tests' or '_test.' in path.name or path.name.startswith('cdp_'):
                problems.append(case['name'] + ': mutation must target product code, never its oracle')
            if item['before'] == item['after']:
                problems.append(case['name'] + ': no-op patch')
        if case['kind'] == 'node':
            text = oracle.read_lf(root, case['file'])
            if text.count("test('" + case['test'] + "'") != 1:
                problems.append(case['name'] + ': exact Node test is absent or ambiguous')
            if case['assertion'] not in text:
                problems.append(case['name'] + ': Node assertion marker is absent')
        if case['kind'] == 'browser':
            text = oracle.read_lf(root, 'geometry-web/assembly_bay_repeat_test.js')
            if case['assertion'] not in text:
                problems.append(case['name'] + ': browser assertion marker is absent')
    covered = {area for case in cases for area in case['covers']}
    problems += ['no named product mutant for BR%02d' % i for i in range(1, 17) if 'BR%02d' % i not in covered]
    return problems


def native_child(argv):
    binary, destination, *names = argv
    sys.path.insert(0, str(ROOT))
    modules = {name.rsplit('.', 2)[0]: None for name in names}
    result = None
    try:
        with ExitStack() as stack:
            for name in modules:
                module = modules[name] = importlib.import_module(name)
                stack.enter_context(patch.object(module, 'find_bridge', return_value=binary))
                getattr(module, 'REACHED', set()).clear()
            runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=oracle.recording_result_class())
            result = runner.run(unittest.defaultTestLoader.loadTestsFromNames(names))
    finally:
        if result is not None:
            reached = sorted({tag for module in modules.values() for tag in getattr(module, 'REACHED', ())})
            oracle.write(Path(destination), dict(selected=names, run=result.testsRun, **result.records,
                                                reached=reached, python=sys.version.split()[0]))
    return 0 if result is not None and result.wasSuccessful() else 1


def selected_native(root):
    tree = ast.parse(oracle.read_lf(root, NATIVE_FILE))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'BayRepeat']
    if len(classes) != 1:
        raise ValueError('one BayRepeat class is required')
    return [PREFIX + n.name for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]


def clean_environment():
    # Preserve normal proxy, trust, compiler and PATH settings. A caller's test
    # scope, service address or existing profile must not leak into this run.
    allowed = {'GEOMETRY_CHROME', 'GEOMETRY_CHROME_FLAGS', 'GEOMETRY_PYTHON', 'GEOMETRY_VCVARS'}
    env = {k: v for k, v in os.environ.items() if not k.startswith('GEOMETRY_') or k in allowed}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def observation(directory, argv, root, env, timeout):
    code, timed_out, group = oracle.run_logged(argv, directory, root, env, timeout)
    try:
        result = json.loads((directory / 'result.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        result = None
    return dict(exit=code, timeout=timed_out, result=result, processGroup=group)


def compile_native(root, directory, env, registry=False):
    binary_dir = directory / 'binary'
    binary_dir.mkdir(parents=True, exist_ok=True)
    if registry:
        # Caller-owned OUT_DIR is supported by the imported registry's public
        # Binary.path/build_one interface. The normal source/byte/smoke checks
        # still create and verify the sidecar; no fingerprint is fabricated.
        script = ('import sys,json;from pathlib import Path;sys.path.insert(0,"tests");import binaries;'
                  'binaries.OUT_DIR=Path(sys.argv[1]);r=binaries.build_one(binaries.BY_NAME["bridge"]);'
                  'i=binaries.inspect_one(binaries.BY_NAME["bridge"]);print(json.dumps(i.as_dict()));'
                  'sys.exit(0 if i.state=="fresh" else 1)')
        argv = [sys.executable, '-B', '-c', script, str(binary_dir)]
        binary = binary_dir / ('bridge.exe' if os.name == 'nt' else 'bridge')
    else:
        binary = binary_dir / 'bridge'
        argv = [env.get('CC', 'cc'), '-std=c11', '-O2', str(root / 'geometry-web/web_bridge.c'), '-lm', '-o', str(binary)]
    code, timeout, group = oracle.run_logged(argv, directory / 'build', root, env, 900)
    return dict(path=str(binary), sha256=oracle.sha256(binary.read_bytes()) if code == 0 and binary.is_file() else None,
                exit=code, timeout=timeout, processGroup=group)


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def stop_group(process):
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def cleanup_cold_children(ledger, token, root):
    """Only the helper's exact PID/birth-tick/run-token ownership records qualify."""
    if not ledger.is_file():
        return []
    cleaned = []
    for line in ledger.read_text(encoding='utf-8').splitlines():
        item = json.loads(line)
        if item.get('token') != token or item.get('root') != str(root) or not isinstance(item.get('pid'), int) or item['pid'] <= 1:
            raise ValueError('cold child ownership record does not belong to this run')
        stat = Path('/proc') / str(item['pid']) / 'stat'
        try:
            birth = stat.read_text().rsplit(') ', 1)[1].split()[19]
        except FileNotFoundError:
            continue
        if not item.get('birth') or birth != item['birth']:
            raise ValueError('cold child PID no longer has the recorded birth tick')
        # This exact, still-live process was spawned detached by our helper.
        try:
            if os.getpgid(item['pid']) != item['pid']:
                raise ValueError('cold child is not the recorded detached group owner')
            os.killpg(item['pid'], signal.SIGTERM)
        except ProcessLookupError:
            continue
        end = time.monotonic() + 2
        while stat.exists() and time.monotonic() < end:
            time.sleep(.05)
        if stat.exists():
            try:
                os.killpg(item['pid'], signal.SIGKILL)
            except ProcessLookupError:
                pass
        cleaned.append(dict(pid=item['pid'], birth=birth))
    return cleaned


def expected_browser_transport_fault(record):
    """Accept only a receipt emitted at the existing deliberate post-commit throw.

    The complete trace remains mandatory: an expected first fault must never
    suppress a subsequent real transport failure or an extra unmarked event.
    """
    if not isinstance(record, dict):
        return False
    receipt = record.get('expectedFault')
    return (isinstance(receipt, dict) and
            record.get('source') == 'api-result' and record.get('transport') is True and
            record.get('step') == '=== P77 review #33 #35 #36 #37 ===' and
            re.fullmatch(r'assembly-confirm [0-9]+', str(record.get('command', ''))) is not None and
            record.get('error') == 'Injected lost success response' and
            receipt.get('schema') == 'geometry-cdp-injected-transport/1' and
            receipt.get('fixture') == 'assembly-review-confirm-response' and
            receipt.get('mode') in ('lost', 'unknown') and receipt.get('serverOk') is True and
            receipt.get('command') == record.get('command') and
            receipt.get('error') == record.get('error'))


def browser_observation(code, timed_out, log, manifest):
    records = []
    for line in log.splitlines():
        if line.startswith('CDP_RESULT '):
            try:
                records.append(json.loads(line[len('CDP_RESULT '):]))
            except ValueError:
                pass
    checks = re.findall(r'^P77 R06 (R06_[A-Z0-9_]+)(?:[^\r\n]*?) ([✓✗])(?: |$)', log, re.M)
    tags = [name for name, _ in checks]
    empty = dict(run=1, selected=['formal-cdp-assembly'], failures=[], errors=[], skipped=[],
                 expectedFailures=[], unexpectedSuccesses=[], reached=sorted(set(tags)))
    if len(records) != 1:
        return dict(exit=code, timeout=timed_out, result=None)
    record = records[0]
    expected_scope = record.get('scope', {}).get('filters') == ['GEOMETRY_ASSEMBLY_ONLY']
    failed = [name for name, verdict in checks if verdict == '✗']
    transports = record.get('apiTransportFailures')
    complete_transport_trace = (record.get('apiTransportTraceComplete') is True and isinstance(transports, list))
    transport_infrastructure = (not complete_transport_trace or
                               (record.get('firstTransportFailure') or None) != (transports[0] if transports else None) or
                               any(not expected_browser_transport_fault(item) for item in (transports or [])))
    infrastructure = (not expected_scope or transport_infrastructure or record.get('firstNetworkFailure') or
                      record.get('uncaughtBrowserExceptions', 0) or re.search(r'^\[EXCEPTION\]|R06_ARCHIVE_INFRASTRUCTURE', log, re.M))
    if infrastructure:
        empty['errors'].append(dict(test='formal-cdp-assembly', tags=[], message='scope/transport/browser infrastructure failure'))
    elif record.get('completed') is True and record.get('failedAssertions') == 0 and not failed:
        if code != 0:
            empty['errors'].append(dict(test='formal-cdp-assembly', tags=[], message='green footer with nonzero exit'))
    elif len(failed) == 1 and record.get('failedAssertions') == 1 and code == 1 and \
            str(record.get('fatal', '')).startswith('P77 R06 assertion failed: ' + failed[0]):
        empty['failures'].append(dict(test='formal-cdp-assembly', tags=failed, exception='ControlledCDPAssertion', bridgeClosed=False))
    else:
        empty['errors'].append(dict(test='formal-cdp-assembly', tags=[], message='incomplete run or uncontrolled/wrong assertion'))
    return dict(exit=code, timeout=timed_out, result=empty, footer=record)


def run_browser(root, directory, env, binary, timeout, manifest):
    chrome = env.get('GEOMETRY_CHROME')
    if not chrome or not Path(chrome).is_file():
        return dict(exit=None, timeout=False, result=None, infrastructure='GEOMETRY_CHROME must name an installed browser')
    port, cdp_port = free_port(), free_port()
    while port == cdp_port:
        cdp_port = free_port()
    temporary_state = tempfile.TemporaryDirectory(prefix='r06-browser-state-')
    feedback = Path(temporary_state.name) / 'feedback'
    feedback.mkdir(parents=True)
    ledger = Path(temporary_state.name) / 'owned-children.jsonl'
    token = uuid.uuid4().hex
    run_env = dict(env, GEOMETRY_TEST_URL='http://127.0.0.1:%d/' % port,
                   GEOMETRY_FEEDBACK_DIR=str(feedback), GEOMETRY_BRIDGE_EXECUTABLE=binary,
                   GEOMETRY_TEST_BRIDGE=binary, GEOMETRY_ISOLATED_SERVICE='1', GEOMETRY_ASSEMBLY_ONLY='1', GEOMETRY_R06_MAIN_INTEGRATION='1',
                   GEOMETRY_CHROME_PROFILE=str(directory / 'chrome-profile'), GEOMETRY_CDP_PORT=str(cdp_port),
                   GEOMETRY_R06_OWNER_LEDGER=str(ledger), GEOMETRY_R06_OWNER_TOKEN=token)
    server = None
    try:
        with (directory / 'server.stdout').open('wb') as stdout, (directory / 'server.stderr').open('wb') as stderr:
            server = subprocess.Popen([sys.executable, '-B', 'geometry-web/serve.py', str(port)], cwd=root,
                                      env=run_env, stdout=stdout, stderr=stderr, start_new_session=True)
            end = time.monotonic() + 30
            service = None
            while time.monotonic() < end:
                if server.poll() is not None:
                    break
                try:
                    with urlopen(run_env['GEOMETRY_TEST_URL'] + 'runtime', timeout=1) as response:
                        service = json.load(response)
                    break
                except OSError:
                    time.sleep(.05)
            if not service or service.get('pid') != server.pid or service.get('fresh') is not True or Path(service.get('root', '')).resolve() != root:
                return dict(exit=None, timeout=False, result=None, infrastructure='isolated current native service did not start')
            oracle.write(directory / 'service.json', service)
            code, timed_out, group = oracle.run_logged(['node', 'geometry-web/cdp_test.js'], directory / 'tests', root, run_env, timeout)
            result = browser_observation(code, timed_out, oracle.read_log(directory / 'tests'), manifest)
            result['processGroup'] = group
            return result
    finally:
        try:
            if ledger.is_file():
                shutil.copyfile(ledger, directory / 'owned-children.jsonl')
            oracle.write(directory / 'cleanup.json', {'coldChildren': cleanup_cold_children(ledger, token, root)})
        finally:
            try:
                stop_group(server)
            finally:
                temporary_state.cleanup()


def run_oracle(kind, root, directory, env, manifest, selected=None, timeout=120, binary=None):
    directory.mkdir(parents=True, exist_ok=True)
    if kind == 'native':
        names = selected or selected_native(root)
        return observation(directory, [sys.executable, '-B', str(root / SELF), '--native-child', binary,
                                        str(directory / 'result.json'), *names], root, env, timeout)
    if kind == 'browser':
        return run_browser(root, directory, env, binary, timeout, manifest)
    records = []
    for index, test in enumerate(selected or manifest['nodeBaseline']):
        folder = directory / str(index)
        pattern = '^' + re.escape(test['test']) + '$' if selected else test['pattern']
        records.append(observation(folder, ['node', str(root / NODE_ADAPTER), str(folder / 'result.json'),
                                           str(root / test['file']), pattern], root, env, timeout))
    if any(r['result'] is None or r['timeout'] or r['exit'] not in (0, 1) for r in records):
        return dict(exit=None, timeout=any(r['timeout'] for r in records), result=None, children=records)
    result = dict(run=0, selected=[], failures=[], errors=[], skipped=[], expectedFailures=[], unexpectedSuccesses=[], reached=[])
    for record in records:
        for key in result:
            if key == 'run':
                result[key] += record['result'][key]
            else:
                result[key] += record['result'][key]
    result['reached'] = sorted(set(result['reached']))
    return dict(exit=1 if any(r['exit'] for r in records) else 0, timeout=False, result=result, children=records)


def apply_patches(root, patches):
    originals, staged = {}, {}
    for item in patches:
        target = root / item['file']
        data = staged.get(item['file'], target.read_bytes())
        originals.setdefault(item['file'], data)
        ending = b'\r\n' if b'\r\n' in data else b'\n'
        before = item['before'].replace('\r\n', '\n').encode().replace(b'\n', ending)
        after = item['after'].replace('\r\n', '\n').encode().replace(b'\n', ending)
        if data.count(before) != 1:
            raise ValueError('%s: mutation needle no longer occurs once' % item['file'])
        staged[item['file']] = data.replace(before, after, 1)
    try:
        for relative, data in staged.items():
            (root / relative).write_bytes(data)
    except OSError:
        for relative, data in originals.items():
            (root / relative).write_bytes(data)
        raise
    return originals


def run_kind(kind, cases, root, out, env, manifest, timeout):
    out.mkdir(parents=True)
    digest_before = oracle.digest(oracle.tree_hashes(root))
    phase = dict(kind=kind, baseline=None, cases=[], restored=None, ok=False)
    build = compile_native(root, out / 'baseline', env, registry=kind == 'browser') if kind != 'node' else None
    phase['baselineBuild'] = build
    if build and not build['sha256']:
        phase['reason'] = 'compile-failed'
        return phase
    baseline = run_oracle(kind, root, out / 'baseline' / 'tests', env, manifest,
                          timeout=timeout, binary=build['path'] if build else None)
    tags = (list(manifest['nativeTags']) if kind == 'native' else
            manifest['browserTags'] if kind == 'browser' else manifest['nodeTags'])
    selected = selected_native(root) if kind == 'native' else ['formal-cdp-assembly'] if kind == 'browser' else manifest['nodeTests']
    verdict, reason = oracle.judge_pass(baseline, selected, tags)
    phase['baseline'] = dict(baseline, verdict=verdict, reason=reason)
    oracle.write(out / 'baseline' / 'observation.json', phase['baseline'])
    print(kind + ': baseline ' + verdict + '/' + reason, flush=True)
    if verdict != 'pass':
        phase['reason'] = 'baseline-not-green'
        return phase
    for case in cases:
        folder = out / 'cases' / case['name']
        folder.mkdir(parents=True)
        record = dict(name=case['name'], expectedTest=case['test'], expectedAssertion=case['assertion'], patches=case['patches'])
        originals = {}
        try:
            originals = apply_patches(root, case['patches'])
            mutant_build = compile_native(root, folder, env, registry=kind == 'browser') if kind != 'node' else None
            record['build'] = mutant_build
            if mutant_build and not mutant_build['sha256']:
                record.update(verdict='not-killed', reason='compile-failed')
            else:
                names = [case['test']] if kind == 'native' else [case] if kind == 'node' else None
                obs = run_oracle(kind, root, folder / 'tests', env, manifest, selected=names, timeout=timeout,
                                 binary=mutant_build['path'] if mutant_build else None)
                record['observation'] = obs
                if kind == 'native':
                    obs = dict(obs, binary=mutant_build['sha256'], baselineBinary=build['sha256'])
                record['verdict'], record['reason'] = oracle.judge_mutant(obs, [case['test']], case['test'], case['assertion'])
        except (OSError, ValueError) as error:
            record.update(verdict='not-killed', reason='infrastructure', error=str(error))
        finally:
            for relative, data in originals.items():
                (root / relative).write_bytes(data)
            record['sourcesRestored'] = oracle.digest(oracle.tree_hashes(root)) == digest_before
            if not record['sourcesRestored']:
                record.update(verdict='not-killed', reason='source-restore-failed')
            oracle.write(folder / 'record.json', record)
        phase['cases'].append(record)
        print(case['name'] + ': ' + record['verdict'] + '/' + record['reason'], flush=True)
    restore_build = compile_native(root, out / 'restored', env, registry=kind == 'browser') if kind != 'node' else None
    phase['restoredBuild'] = restore_build
    if restore_build and not restore_build['sha256']:
        phase['reason'] = 'restored-compile-failed'
        return phase
    restored = run_oracle(kind, root, out / 'restored' / 'tests', env, manifest,
                          timeout=timeout, binary=restore_build['path'] if restore_build else None)
    verdict, reason = oracle.judge_pass(restored, selected, tags)
    phase['restored'] = dict(restored, verdict=verdict, reason=reason)
    phase['restoredBinaryMatches'] = not build or build['sha256'] == restore_build['sha256']
    phase['ok'] = verdict == 'pass' and phase['restoredBinaryMatches'] and all(c['verdict'] == 'killed' and c['sourcesRestored'] for c in phase['cases'])
    oracle.write(out / 'restored' / 'observation.json', phase['restored'])
    print(kind + ': restored ' + verdict + '/' + reason, flush=True)
    return phase


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--native-child', nargs='+')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--kind', choices=['native', 'node', 'browser'], action='append')
    parser.add_argument('--case', action='append')
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--browser-timeout', type=int, default=1200)
    args = parser.parse_args(argv)
    if args.native_child:
        return native_child(args.native_child)
    if args.selftest:
        problems = oracle.selftest()
        print('\n'.join(problems) if problems else 'strict judge selftest: all inherited negative controls hold')
        return bool(problems)
    manifest = load_manifest()
    problems = static_problems(manifest=manifest)
    if args.check:
        print('\n'.join(problems) if problems else 'R06 manifest: all BR01–BR16 have live product needles and named assertions')
        return bool(problems)
    if problems:
        print('\n'.join(problems))
        return 2
    if os.name != 'posix':
        parser.error('Use GCC on Linux/WSL; no security settings are changed.')
    if not args.out:
        parser.error('--out is required')
    cases = [c for c in manifest['cases'] if (not args.kind or c['kind'] in args.kind) and (not args.case or c['name'] in args.case)]
    if not cases or args.case and set(args.case) - {c['name'] for c in cases}:
        parser.error('selected case is unknown or excluded by kind')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    result = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True, check=True)
    inputs = {name: (ROOT / name).read_bytes() for name in result.stdout.decode().split('\0') if name and (ROOT / name).is_file()}
    hashes = {name: oracle.sha256(data) for name, data in inputs.items()}
    oracle.write(out / 'sources.json', hashes)
    summary = dict(schema=manifest['schema'], ok=False, sourcesDigest=oracle.digest(hashes),
                   selection=[c['name'] for c in cases], phases=[], startedAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    with tempfile.TemporaryDirectory(prefix='r06-mutation-sources-') as temporary:
        root = Path(temporary)
        for name, data in inputs.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for kind in ('native', 'node', 'browser'):
            chosen = [c for c in cases if c['kind'] == kind]
            if chosen:
                summary['phases'].append(run_kind(kind, chosen, root, out / kind, clean_environment(), manifest,
                                                 args.browser_timeout if kind == 'browser' else args.timeout))
                oracle.write(out / 'summary.json', summary)
    summary['checkoutUnchanged'] = all((ROOT / name).is_file() and (ROOT / name).read_bytes() == data for name, data in inputs.items())
    summary['ok'] = summary['checkoutUnchanged'] and all(phase['ok'] for phase in summary['phases'])
    oracle.write(out / 'summary.json', summary)
    print(json.dumps(dict(ok=summary['ok'], checkoutUnchanged=summary['checkoutUnchanged'],
                          phases=[dict(kind=p['kind'], ok=p['ok'], reason=p.get('reason')) for p in summary['phases']]), ensure_ascii=False))
    return 0 if summary['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
