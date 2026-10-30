#!/usr/bin/env python3
"""Run real CDP controls/mutants in temporary source snapshots (never edit repo).

Requires native Linux (including a Linux Python inside WSL), with /proc.
Windows process-tree cleanup is not supported and is rejected before launch.
Each manifest names one existing CDP scope, its complete case IDs, and exact
single-site source replacements. Native executables must already be built from
the reported product revision. An assertion failure is a kill only after green
controls and a completed harness result; startup/fixture/cleanup failures block.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Expected relative repository path')
    unresolved = root / relative
    if unresolved.is_symlink():
        raise ValueError('Snapshot does not follow symlinks: ' + relative)
    path = unresolved.resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path escapes snapshot: ' + relative)
    return path


def command(argv, cwd, timeout=30, env=None):
    return subprocess.run(argv, cwd=cwd, env=env, text=True, encoding='utf-8', errors='replace',
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, check=False)


def proc_identity(pid):
    """Read Linux process identity without treating a reused PID as our child."""
    try:
        raw = (Path('/proc') / str(pid) / 'stat').read_text(encoding='utf-8', errors='replace')
    except (FileNotFoundError, ProcessLookupError):
        return None
    fields = raw[raw.rfind(')') + 2:].split()
    try:
        actual_pid = int(raw.split(' ', 1)[0])
        if actual_pid != int(pid):
            raise ValueError('PID mismatch')
        return {'pid': actual_pid, 'state': fields[0], 'group': int(fields[2]),
                'session': int(fields[3]), 'start': int(fields[19])}
    except (IndexError, ValueError) as error:
        raise RuntimeError('Cannot verify Linux process identity: ' + str(pid)) from error


def require_process_namespace():
    if not sys.platform.startswith('linux') or not Path('/proc/self/stat').is_file():
        raise RuntimeError('Requires native Linux/WSL Python with /proc; Windows owned-tree cleanup is unsupported')
    # Some hosted executors expose a host /proc alongside virtual child PIDs.
    # Never use that unrelated process table to decide what may be signalled.
    self_stat = Path('/proc/self/stat').read_text(encoding='utf-8', errors='replace')
    if int(self_stat.split(' ', 1)[0]) != os.getpid():
        raise RuntimeError('/proc does not describe this process namespace; refusing to launch')
    current = proc_identity(os.getpid())
    if current is None or current['group'] != os.getpgrp() or current['session'] != os.getsid(0):
        raise RuntimeError('/proc process-group/session identity disagrees with the OS; refusing to launch')


def remember_owner(process):
    # Popen(start_new_session=True) makes this child both group and session leader.
    process.mutation_owner = proc_identity(process.pid)
    owner = process.mutation_owner
    if owner is not None and (owner['group'] != process.pid or owner['session'] != process.pid):
        raise RuntimeError('Child did not acquire its isolated process group')


def live_group_members(group):
    members = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        row = proc_identity(int(entry.name))
        # A zombie holds no executable, socket or profile file; the parent reaps it.
        if row is not None and row['group'] == group and row['state'] not in ['Z', 'X', 'x']:
            members.append(row)
    return members


def stop(process):
    if process is None:
        return None
    group = process.pid
    owner = getattr(process, 'mutation_owner', None)
    leader = proc_identity(group)
    if owner is not None and leader is not None and leader['start'] != owner['start']:
        raise RuntimeError('Owned process-group id was reused; refusing to signal it')
    sent = []
    for sig, grace in [(signal.SIGTERM, 5), (signal.SIGKILL, 5)]:
        # Do not return just because the leader exited: its browser/bridge can live on.
        if not live_group_members(group):
            break
        try:
            os.killpg(group, sig)
            sent.append(sig.name)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + grace
        while live_group_members(group) and time.monotonic() < deadline:
            time.sleep(0.05)
    remaining = live_group_members(group)
    if remaining:
        raise RuntimeError('Owned process group still has live members: ' + str(remaining))
    process.wait(timeout=2)
    return {'group': group, 'signals': sent, 'liveMembers': 0, 'completed': True}


def snapshot(repo, destination, extras):
    result = subprocess.run(['git', '-C', str(repo), 'ls-files', '-z'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=True)
    names = set(os.fsdecode(x) for x in result.stdout.split(b'\0') if x)
    names.update(extras)
    files = {}
    for name in sorted(names):
        source = safe_path(repo, name)
        if source.is_symlink():
            raise ValueError('Snapshot does not follow symlinks: ' + name)
        if not source.is_file():
            if name in extras:
                raise ValueError('Missing test input: ' + name)
            continue  # A tracked deletion remains a deletion in the snapshot.
        target = safe_path(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        # Attest to the bytes actually executed, not a later read of a live worktree.
        files[name] = digest(target.read_bytes())
    return files


RESERVED_GEOMETRY_ENV = frozenset([
    'GEOMETRY_TEST_URL', 'GEOMETRY_FEEDBACK_DIR', 'GEOMETRY_CHROME',
    'GEOMETRY_CHROME_FLAGS', 'GEOMETRY_CHROME_PROFILE', 'GEOMETRY_CDP_PORT',
    'GEOMETRY_TEST_SERVER_PATH_STYLE', 'GEOMETRY_BRIDGE', 'GEOMETRY_BRIDGE_EXECUTABLE',
    'GEOMETRY_BRIDGE_WSL', 'GEOMETRY_MODEL_BASE', 'GEOMETRY_CDP_UPDATE_GOLDEN',
    'GEOMETRY_CDP_FROM_P31', 'GEOMETRY_TEST_SCREENSHOT',
    'GEOMETRY_GRID_SCREENSHOT_DIR', 'GEOMETRY_REPAIR_SCREENSHOT_DIR',
])


def subcase_environment(manifest, value):
    allowed = manifest.get('subcaseVariables', [])
    reserved = RESERVED_GEOMETRY_ENV | {manifest['scope'], manifest['caseFilter']}
    if (not isinstance(value, dict) or not set(value).issubset(allowed) or set(value) & reserved or
            any(not isinstance(item, str) or not item or '\0' in item for item in value.values())):
        raise ValueError('Mutation env must use declared non-reserved subcase keys and string values')
    return dict(value)


def read_manifest(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    required = ['schema', 'suite', 'scope', 'caseFilter', 'resultPrefix',
                'cases', 'inputs', 'mutations']
    if not isinstance(value, dict) or any(k not in value for k in required):
        raise ValueError('Incomplete mutation manifest')
    if value['schema'] != 'geometry-browser-mutations/1':
        raise ValueError('Unknown mutation manifest schema')
    for key in ['scope', 'caseFilter']:
        name = value[key]
        if not isinstance(name, str) or not name.startswith('GEOMETRY_') or not name.replace('_', '').isalnum():
            raise ValueError('Invalid environment key: ' + key)
    if value['scope'] == value['caseFilter']:
        raise ValueError('Scope and case filter must be distinct')
    variables = value.get('subcaseVariables', [])
    if (not isinstance(variables, list) or
            any(not isinstance(name, str) or not name.startswith('GEOMETRY_') or
                not name.endswith('_ONLY') or not name.isascii() or not name.replace('_', '').isalnum()
                for name in variables) or len(set(variables)) != len(variables) or
            set(variables) & (RESERVED_GEOMETRY_ENV | {value['scope'], value['caseFilter']})):
        raise ValueError('Invalid or reserved subcase variable declaration')
    for key in ['cases', 'inputs']:
        items = value[key]
        if not isinstance(items, list) or not items or any(not isinstance(x, str) or not x for x in items) or len(set(items)) != len(items):
            raise ValueError('Invalid or duplicate ' + key)
    ids = set()
    for mutation in value['mutations']:
        if not isinstance(mutation, dict) or not {'id', 'case', 'assertions', 'changes'} <= mutation.keys():
            raise ValueError('Incomplete mutation')
        mid = mutation['id']
        if not isinstance(mid, str) or not mid.replace('-', '').replace('_', '').isalnum() or mid in ids:
            raise ValueError('Invalid/duplicate mutation id')
        ids.add(mid)
        if mutation['case'] not in value['cases'] or not mutation['assertions'] or not mutation['changes']:
            raise ValueError('Mutation lacks a case, assertion or change')
        subcase_environment(value, mutation.get('env', {}))
        for change in mutation['changes']:
            if not {'file', 'before', 'after'} <= change.keys() or not change['before'] or change['before'] == change['after']:
                raise ValueError('Mutation must replace one nonempty exact site')
    if not ids:
        raise ValueError('No mutations requested')
    return value


def parse_result(log, manifest, expected_cases, exit_code, reject_transport=False):
    cases, footer, malformed = [], [], []
    for line in log.splitlines():
        prefix = next((p for p in [manifest['resultPrefix'], 'CDP_RESULT '] if line.startswith(p)), None)
        if prefix is None:
            continue
        try:
            row = json.loads(line[len(prefix):])
            if not isinstance(row, dict):
                raise ValueError('Result is not an object')
            (footer if prefix == 'CDP_RESULT ' else cases).append(row)
        except (ValueError, TypeError) as error:
            malformed.append(str(error))
    errors = []
    assertions = []
    ids = [x.get('case', x.get('id')) for x in cases]
    valid_ids = all(isinstance(value, str) and value for value in ids)
    if not valid_ids:
        errors.append('Malformed case id')
    final = footer[0] if len(footer) == 1 else {}
    counters = ['passedAssertions', 'failedAssertions', 'uncaughtBrowserExceptions']
    valid_counters = all(type(final.get(key)) is int and final[key] >= 0 for key in counters)
    if len(footer) == 1 and (final.get('schema') != 'geometry-cdp-result/1' or not valid_counters):
        errors.append('Malformed CDP footer schema or counters')
    complete = (not malformed and valid_ids and len(ids) == len(expected_cases) and
                set(ids) == set(expected_cases) and len(set(ids)) == len(ids) and
                len(footer) == 1 and final.get('completed') is True and valid_counters and
                final.get('uncaughtBrowserExceptions') == 0)
    for case in cases:
        status = case.get('status')
        failures = case.get('failures', [])
        if not isinstance(failures, list):
            errors.append('Malformed failures list')
            continue
        if status not in ['passed', 'pass', 'failed', 'fail', 'error']:
            errors.append('Unknown case status')
        if status == 'error' or case.get('kind') in ['precondition', 'exception', 'cleanup']:
            errors.append(case)
        if status in ['passed', 'pass'] and (failures or case.get('kind') == 'assertion'):
            errors.append('Passing case also reports an assertion failure')
        if case.get('kind') == 'assertion' and status in ['failed', 'fail']:
            name = case.get('assertion')
            if not isinstance(name, str) or not name:
                errors.append('Assertion failure has no valid name')
            else:
                assertions.append(name)
        for failure in failures:
            if (not isinstance(failure, dict) or failure.get('kind') != 'assertion' or
                    not isinstance(failure.get('name'), str) or not failure['name']):
                errors.append(failure)
            else:
                assertions.append(failure['name'])
        if status in ['failed', 'fail'] and not failures and case.get('kind') != 'assertion':
            errors.append('Failure without a named assertion')
    if assertions and final.get('failedAssertions') == 0:
        errors.append('Named failures contradict the zero-failure footer')
    traces = {key: final.get(key) for key in ['firstTransportFailure', 'firstNetworkFailure']}
    if reject_transport and len(footer) == 1:
        if any(key not in final for key in traces):
            errors.append('Single-case result is missing transport trace fields')
        if any(value is not None for value in traces.values()):
            errors.append('Unexpected transport/network failure in a mutation control or mutant')
    green = (complete and not errors and not assertions and exit_code == 0 and
             all(x.get('status') in ['passed', 'pass'] for x in cases) and
             final.get('failedAssertions') == 0 and final.get('passedAssertions', 0) > 0)
    return {'complete': complete, 'green': green, 'cases': cases,
            'footer': footer, 'errors': errors + malformed,
            'assertions': assertions, 'exitCode': exit_code, 'transportTraces': traces,
            'transportPolicy': 'require-null' if reject_transport else 'suite-defined'}


SAFE_CHROME_FLAGS = frozenset(['--no-sandbox', '--disable-setuid-sandbox',
                             '--disable-dev-shm-usage', '--disable-gpu',
                             '--disable-software-rasterizer'])


def isolated_environment(environ):
    # Only the executable and an explicit safe set of Linux flags may be inherited.
    # In particular, no caller profile, port, output path, WSL bridge mode, model
    # executable, fixture filter or golden update can override this run's values.
    env = {name: value for name, value in environ.items() if not name.startswith('GEOMETRY_')}
    if environ.get('GEOMETRY_CHROME'):
        env['GEOMETRY_CHROME'] = environ['GEOMETRY_CHROME']
    flags = shlex.split(environ.get('GEOMETRY_CHROME_FLAGS', ''))
    if any(flag not in SAFE_CHROME_FLAGS for flag in flags):
        raise ValueError('GEOMETRY_CHROME_FLAGS contains a flag outside the isolated-run allowlist')
    if flags:
        env['GEOMETRY_CHROME_FLAGS'] = ' '.join(flags)
    return env


def run_cdp(root, manifest, options, output, label, case=None, extra_env=None):
    run_dir = output / label
    run_dir.mkdir(parents=True)
    env = isolated_environment(os.environ)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        with socket.socket() as browser_sock:
            browser_sock.bind(('127.0.0.1', 0))
            browser_port = browser_sock.getsockname()[1]
    env.update({manifest['scope']: '1',
                'GEOMETRY_TEST_URL': 'http://127.0.0.1:' + str(port) + '/',
                'GEOMETRY_FEEDBACK_DIR': str(root.parent / ('feedback-' + label)),
                'GEOMETRY_CHROME_PROFILE': str(root.parent / ('chrome-' + label)),
                'GEOMETRY_CDP_PORT': str(browser_port),
                'GEOMETRY_TEST_SERVER_PATH_STYLE': 'native',
                'GEOMETRY_BRIDGE_EXECUTABLE': str(options.bridge.resolve()),
                'GEOMETRY_TEST_SCREENSHOT': str(run_dir / 'screens' / 'phase1-shell.png'),
                'GEOMETRY_GRID_SCREENSHOT_DIR': str(run_dir / 'screens'),
                'GEOMETRY_REPAIR_SCREENSHOT_DIR': str(run_dir / 'screens')})
    if case is not None:
        env[manifest['caseFilter']] = case
    subcase_env = subcase_environment(manifest, {} if extra_env is None else extra_env)
    if subcase_env and case is None:
        raise ValueError('Subcase filters may not narrow the full-suite baseline')
    env.update(subcase_env)
    if options.model_base:
        env['GEOMETRY_MODEL_BASE'] = str(options.model_base.resolve())
    server = test = None
    started = time.monotonic()
    expected = [case] if case else manifest['cases']
    result = {'complete': False, 'green': False, 'errors': [], 'assertions': []}
    try:
        with (run_dir / 'server.log').open('w', encoding='utf-8') as server_log:
            server = subprocess.Popen([options.python, 'geometry-web/serve.py', str(port)],
                                      cwd=root, env=env, stdout=server_log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
            remember_owner(server)
            deadline = time.monotonic() + 60
            probe = None
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError('Isolated server exited: ' + str(server.returncode))
                probe = command([options.python, 'geometry-web/runtime_version.py', '--probe', str(port)],
                                root, timeout=10, env=env)
                if probe.returncode == 0:
                    break
                time.sleep(0.25)
            if probe is None or probe.returncode != 0:
                raise RuntimeError('Runtime fingerprint/ready probe failed: ' + (probe.stdout if probe else 'no probe'))
            (run_dir / 'runtime.log').write_text(probe.stdout, encoding='utf-8')
            with (run_dir / 'cdp.log').open('w', encoding='utf-8') as test_log:
                test = subprocess.Popen([options.node, 'geometry-web/cdp_test.js'],
                                        cwd=root, env=env, stdout=test_log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                remember_owner(test)
                exit_code = test.wait(timeout=options.timeout)
            log = (run_dir / 'cdp.log').read_text(encoding='utf-8', errors='replace')
            # Full-suite controls include intentionally offline cases. All current
            # mutation cases are non-offline, so both their mutant and restored
            # controls must have null transport traces. A future offline mutation
            # needs an explicit expected/unexpected transport protocol first.
            result = parse_result(log, manifest, expected, exit_code, reject_transport=case is not None)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result['errors'].append(type(error).__name__ + ': ' + str(error))
    finally:
        result['cleanup'] = []
        for process in [test, server]:
            try:
                cleanup = stop(process)
                if cleanup is not None:
                    result['cleanup'].append(cleanup)
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                result['errors'].append('cleanup: ' + str(error))
                result['green'] = False
        result['elapsedSeconds'] = round(time.monotonic() - started, 3)
        result['command'] = [options.node, 'geometry-web/cdp_test.js']
        result['scope'] = manifest['scope']
        result['caseFilter'] = case
        result['subcaseEnv'] = subcase_env
        result['logs'] = str(run_dir)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--model-base', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--node', default='node')
    parser.add_argument('--timeout', type=int, default=900)
    options = parser.parse_args()
    try:
        require_process_namespace()
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    repo, output = options.repo.resolve(), options.output_dir.resolve()
    if output.exists():
        parser.error('--output-dir must be new; old receipts are never overwritten')
    if output.is_relative_to(repo):
        parser.error('--output-dir must be outside the product repository')
    if not options.bridge.is_file() or (options.model_base and not options.model_base.is_file()):
        parser.error('Pass existing native executable paths')
    manifest_path = options.manifest.resolve()
    manifest = read_manifest(manifest_path)
    output.mkdir(parents=True)
    report = {'schema': 'geometry-browser-mutation-receipt/1', 'suite': manifest['suite'],
              'manifestHash': digest(manifest_path.read_bytes()), 'mutations': [],
              'head': command(['git', 'rev-parse', 'HEAD'], repo).stdout.strip(),
              'bridgeHash': digest(options.bridge.read_bytes()), 'status': 'blocked'}
    if options.model_base:
        report['modelBaseHash'] = digest(options.model_base.read_bytes())
    exit_code = 2
    try:
        with tempfile.TemporaryDirectory(prefix='geometry-browser-mutations-') as directory:
            temporary = Path(directory)
            baseline = temporary / 'baseline'
            baseline.mkdir()
            report['files'] = snapshot(repo, baseline, manifest['inputs'])
            report['sourceHash'] = digest(json.dumps(report['files'], sort_keys=True).encode())
            report['baseline'] = run_cdp(baseline, manifest, options, output, 'baseline')
            if not report['baseline']['green']:
                report['reason'] = 'Baseline is not green; no mutation counts as killed.'
                return 2
            for mutation in manifest['mutations']:
                subcase_env = subcase_environment(manifest, mutation.get('env', {}))
                row = {'id': mutation['id'], 'case': mutation['case'], 'status': 'blocked',
                       'subcaseEnv': subcase_env}
                report['mutations'].append(row)
                work = temporary / mutation['id']
                shutil.copytree(baseline, work)
                originals = {}
                try:
                    for change in mutation['changes']:
                        target = safe_path(work, change['file'])
                        data = target.read_bytes()
                        originals.setdefault(target, data)
                        before, after = change['before'].encode(), change['after'].encode()
                        if data.count(before) != 1:
                            raise ValueError('Exact mutation site drifted: ' + change['file'])
                        target.write_bytes(data.replace(before, after, 1))
                        row.setdefault('changes', []).append({**change, 'beforeHash': digest(data),
                                                            'afterHash': digest(target.read_bytes())})
                    for target in originals:
                        if target.suffix == '.js':
                            syntax = command([options.node, '--check', str(target)], work)
                            if syntax.returncode != 0:
                                raise ValueError('Mutant syntax failure: ' + syntax.stdout)
                    row['mutant'] = run_cdp(work, manifest, options, output, mutation['id'] + '-mutant', mutation['case'], extra_env=subcase_env)
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    row['reason'] = str(error)
                finally:
                    for target, data in originals.items():
                        target.write_bytes(data)
                row['restored'] = run_cdp(work, manifest, options, output, mutation['id'] + '-restored', mutation['case'], extra_env=subcase_env)
                mutant = row.get('mutant')
                if not row['restored']['green']:
                    row['reason'] = 'Restored control is not green.'
                elif mutant and mutant['green']:
                    row['status'] = 'survived'
                elif mutant and mutant['complete'] and not mutant['errors'] and mutant.get('exitCode') == 1 and \
                        mutant['footer'][0].get('failedAssertions', 0) > 0 and \
                        set(mutant['assertions']).intersection(mutation['assertions']):
                    row['status'] = 'killed'
                elif 'reason' not in row:
                    row['reason'] = 'No completed, named assertion failure; environment/fixture/timeouts do not kill.'
            statuses = [x['status'] for x in report['mutations']]
            report['status'] = 'passed' if all(x == 'killed' for x in statuses) else 'blocked' if 'blocked' in statuses else 'failed'
            exit_code = 0 if report['status'] == 'passed' else 2 if report['status'] == 'blocked' else 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report['reason'] = type(error).__name__ + ': ' + str(error)
        report['status'] = 'blocked'
        exit_code = 2
    except KeyboardInterrupt:
        report['reason'] = 'Interrupted; incomplete cleanup or execution cannot pass.'
        report['status'] = 'blocked'
        exit_code = 2
    finally:
        (output / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': report['status'], 'receipt': str(output / 'receipt.json')}, ensure_ascii=False))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
