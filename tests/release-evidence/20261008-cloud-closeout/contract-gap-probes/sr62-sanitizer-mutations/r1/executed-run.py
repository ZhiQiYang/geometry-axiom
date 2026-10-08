#!/usr/bin/env python3
"""Root-owned serial execution entry. No work happens without --execute and a new --out."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import sys
import time
import traceback

PROBE_ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def verify_source(source, rows, mutation=None):
    for row in rows:
        expected = mutation['afterSha256'] if mutation and mutation['path'] == row['path'] else row['sha256']
        if sha(source / row['path']) != expected:
            raise RuntimeError('source mismatch: ' + row['path'])


def stack_limit():
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    desired = 64 * 1024 * 1024
    if hard != resource.RLIM_INFINITY and hard < desired:
        raise RuntimeError('cannot provide required 64 MiB process stack')
    resource.setrlimit(resource.RLIMIT_STACK, (desired, hard))


def command(out, label, argv, cwd, env, timeout, stack=False):
    before = datetime.datetime.now(datetime.timezone.utc).isoformat()
    started = time.monotonic()
    record = {'command': list(map(str, argv)), 'cwd': str(cwd), 'startedAt': before,
              'timeoutSeconds': timeout, 'stackBytes': 64 * 1024 * 1024 if stack else None,
              'environment': {key: env.get(key) for key in ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'PYTHONDONTWRITEBYTECODE']}}
    child = None
    interrupt = None
    try:
        with (out / (label + '.stdout')).open('wb') as stdout, (out / (label + '.stderr')).open('wb') as stderr:
            child = subprocess.Popen(record['command'], cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                     start_new_session=True, preexec_fn=stack_limit if stack else None)
            try:
                child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record['timeout'] = True
                os.killpg(child.pid, signal.SIGKILL)  # this command's own isolated session only
                child.wait()
            record['exitCode'] = child.returncode
    except BaseException as exc:
        record['launchError'] = traceback.format_exc()
        record['exitCode'] = None
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            record['exitCode'] = child.returncode
            record['exceptionOwnedProcessGroupKilledAndReaped'] = True
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            interrupt = exc
    record['elapsedSeconds'] = time.monotonic() - started
    for stream in ['stdout', 'stderr']:
        path = out / (label + '.' + stream)
        if path.exists():
            record[stream + 'Sha256'] = sha(path)
    save(out / (label + '.command.json'), record)
    if interrupt is not None:
        raise interrupt
    return record


def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt('driver received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cc', default='cc')
    parser.add_argument('--compile-timeout', type=int, default=300)
    parser.add_argument('--oracle-timeout', type=int, default=300)
    args = parser.parse_args()
    out = args.out.resolve()
    plan = json.loads((PROBE_ROOT / 'plan.json').read_text())
    repo = Path(plan['repo'])
    if out.is_relative_to(repo) or out == PROBE_ROOT or out.is_relative_to(PROBE_ROOT / 'source'):
        parser.error('output must be a fresh private run directory outside repository and frozen source')
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update({'PYTHONDONTWRITEBYTECODE': '1', 'ASAN_OPTIONS': 'detect_leaks=1:halt_on_error=1:abort_on_error=1',
                'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'})
    for key in ['GEOMETRY_TEST_BRIDGE', 'GEOMETRY_ENGINEERING_BRIDGE', 'PYTHONPATH', 'LD_PRELOAD']:
        env.pop(key, None)
    summary = {'schema': 'geometry-sgr62-sanitizer-mutation-run/1', 'preparedHead': plan['head'],
               'planSha256': sha(PROBE_ROOT / 'plan.json'), 'platform': platform.platform(),
               'python': sys.version, 'mutations': [], 'complete': False, 'passed': False,
               'historical152Reproduced': False}
    base = out / 'pristine-source'
    try:
        verify_source(PROBE_ROOT / 'source', plan['sourceFiles'])
        # Compare source bytes rather than demanding unchanged docs/publication HEAD.
        verify_source(repo, plan['sourceFiles'])
        summary['liveHead'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
        summary['liveStatusBefore'] = subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True)
        if summary['liveStatusBefore']:
            raise RuntimeError('live repository must be clean before isolated execution')
        compiler = shutil.which(args.cc)
        if not compiler:
            raise RuntimeError('compiler unavailable')
        command(out, 'compiler-version', [compiler, '--version'], PROBE_ROOT, env, 10)
        shutil.copytree(PROBE_ROOT / 'source', base)
        pristine_binary = out / 'pristine-bridge'
        active_binary = out / 'active-bridge'
        flags = plan['compileFlags']

        def compile_one(label, source, binary):
            return command(out, label, [compiler, *flags, str(source / 'geometry-web/web_bridge.c'),
                           '-o', str(binary), '-lm'], source, env, args.compile_timeout)

        def run_oracle(label, tests, expected_count):
            binary_hash = sha(active_binary)
            argv = [sys.executable, str(PROBE_ROOT / 'oracle_runner.py'), '--source', str(base),
                    '--binary', str(active_binary), '--binary-sha256', binary_hash, '--out', str(out / label)]
            for test in tests:
                argv.extend(['--test', test])
            receipt = command(out, label, argv, base, env, args.oracle_timeout, stack=True)
            path = out / label / 'result.json'
            result = json.loads(path.read_text()) if path.exists() else None
            ok = bool(receipt['exitCode'] == 0 and not receipt.get('timeout') and result
                      and result['testsRun'] == expected_count and not result['failures'] and not result['errors']
                      and not result['skipped'] and not result['expectedFailures'] and not result['unhealthySessions'])
            return {'command': receipt, 'result': result, 'passed': ok}

        full_tests = ['tests.test_grid_subdivision_oracle', 'tests.test_grid_system_contract']
        compiled = compile_one('baseline-compile', base, pristine_binary)
        summary['baselineCompile'] = compiled
        if compiled['exitCode'] != 0 or compiled.get('timeout'):
            raise RuntimeError('baseline compilation failed; no mutation is credited')
        pristine_sha = sha(pristine_binary)
        summary['pristineBinarySha256'] = pristine_sha
        shutil.copy2(pristine_binary, active_binary)
        summary['baseline'] = run_oracle('baseline', full_tests, 54)
        if not summary['baseline']['passed']:
            raise RuntimeError('baseline failed; mutation execution stops')
        for mutation in plan['mutations']:
            row = {'id': mutation['id'], 'expectedSemanticFailure': mutation['expectedSemanticFailure'],
                   'verdict': 'NOT_EXECUTED'}
            summary['mutations'].append(row)
            source = out / (mutation['id'] + '-source')
            shutil.copytree(base, source)
            path = source / mutation['path']
            original = path.read_bytes()
            if original.count(mutation['old'].encode()) != 1:
                raise RuntimeError('mutation anchor changed')
            path.write_bytes(original.replace(mutation['old'].encode(), mutation['new'].encode(), 1))
            verify_source(source, plan['sourceFiles'], mutation)
            row['diffSha256'] = sha(PROBE_ROOT / 'patches' / (mutation['id'] + '.diff'))
            row['compile'] = compile_one(mutation['id'] + '-compile', source, active_binary)
            if row['compile']['exitCode'] != 0 or row['compile'].get('timeout'):
                row['verdict'] = 'COMPILE_FAILURE_NOT_A_KILL'
            else:
                row['mutantBinarySha256'] = sha(active_binary)
                observed = run_oracle(mutation['id'], [mutation['test']], 1)
                row['oracle'] = observed
                result = observed['result']
                semantic = bool(observed['command']['exitCode'] == 1 and not observed['command'].get('timeout')
                    and result and result['testsRun'] == 1 and result['failures'] > 0 and result['errors'] == 0
                    and not result['skipped'] and not result['expectedFailures'] and not result['unhealthySessions']
                    and result['details'] and all(d['kind'] == 'failure' and d['exception'] == 'AssertionError'
                        and d['test'].startswith(mutation['test'])
                        and any(f['file'] == str(base / 'tests/test_grid_subdivision_oracle.py')
                                and f['line'] == mutation['expectedAssertionLine'] for f in d['frames'])
                        for d in result['details']))
                row['verdict'] = ('SEMANTIC_ASSERTION_KILL' if semantic else
                                  'SURVIVED' if observed['passed'] else 'OTHER_FAILURE_NOT_A_KILL')
            # Explicitly restore the same private active path to pristine bytes.
            shutil.copy2(pristine_binary, active_binary)
            row['restoredBinarySha256'] = sha(active_binary)
            if row['restoredBinarySha256'] != pristine_sha:
                raise RuntimeError('restore hash differs')
            row['restoredOracle'] = run_oracle(mutation['id'] + '-restored', [mutation['test']], 1)
            save(out / 'summary.json', summary)
            if not row['restoredOracle']['passed']:
                raise RuntimeError('restored original oracle failed; subsequent mutations stop')
        summary['finalRestoredBinarySha256'] = sha(active_binary)
        summary['restorationEvidence'] = 'All five original target methods passed after restoring the same private binary path; pristine source was never mutated.'
        verify_source(base, plan['sourceFiles'])
        verify_source(repo, plan['sourceFiles'])
        summary['liveStatusAfter'] = subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True)
        summary['complete'] = True
        summary['passed'] = (summary['finalRestoredBinarySha256'] == pristine_sha and not summary['liveStatusAfter']
              and len(summary['mutations']) == 5 and all(r['verdict'] == 'SEMANTIC_ASSERTION_KILL'
                  and r['restoredOracle']['passed'] for r in summary['mutations']))
    except BaseException:
        summary['error'] = traceback.format_exc()
    finally:
        # On exceptional exits, preserve a pristine active copy as well. This is
        # byte restoration only, not a successful oracle claim.
        retained = out / 'pristine-bridge'
        active = out / 'active-bridge'
        if retained.exists():
            try:
                shutil.copy2(retained, active)
                summary['finallyRestoredBinarySha256'] = sha(active)
            except BaseException:
                summary['restorationError'] = traceback.format_exc()
                summary['passed'] = False
        summary['finishedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for name in ['prepare.py', 'run.py', 'oracle_runner.py', 'plan.json']:
            shutil.copy2(PROBE_ROOT / name, out / ('executed-' + name))
        save(out / 'summary.json', summary)
    print(json.dumps({'complete': summary['complete'], 'passed': summary['passed'],
                      'verdicts': [(r['id'], r['verdict']) for r in summary['mutations']]}))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
