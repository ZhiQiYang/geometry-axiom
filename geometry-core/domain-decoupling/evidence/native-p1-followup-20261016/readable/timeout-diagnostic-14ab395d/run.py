"""Recompile two original 14ab harnesses and measure them; never acceptance."""
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
ORIGINAL = EVIDENCE / 'native-candidate-14ab395d-v1'
SOURCE = '14ab395d56ce1dcabe43e65b5311776a8d3e6221'
OUT = EVIDENCE / 'timeout-diagnostic-14ab395d-v1'
RUNNERS = ('run.py', 'namespace.sh')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(directory):
    return {str(p.relative_to(directory)): sha(p)
            for p in sorted(directory.rglob('*')) if p.is_file()}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def measured(command, label, original_limit, old_hash):
    directory = OUT / label
    directory.mkdir()
    binary = Path(command[0])
    binary_before = sha(binary)
    symbols = subprocess.run(['nm', '-S', '--defined-only', str(binary)],
                             cwd=root, capture_output=True, timeout=20)
    (directory / 'nm.stdout.txt').write_bytes(symbols.stdout)
    (directory / 'nm.stderr.txt').write_bytes(symbols.stderr)
    world_symbols = [line for line in symbols.stdout.decode('utf-8', errors='replace').splitlines()
                     if line.split()[-1:] == ['g_world']]
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    started = time.monotonic()
    timed_out = False
    with (directory / 'stdout.bin').open('xb') as stdout, (directory / 'stderr.bin').open('xb') as stderr:
        child = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() - started >= 120:
                timed_out = True
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                pid, status, usage = os.wait4(child.pid, 0)
                break
            time.sleep(0.05)
        child.returncode = os.waitstatus_to_exitcode(status)
    elapsed = time.monotonic() - started
    result = {
        'label': label, 'kind': 'newly-recompiled-original-harness-diagnostic-only',
        'command': command, 'cwd': str(root), 'started_utc': started_utc,
        'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'watchdog_seconds': 120, 'watchdog_expired': timed_out,
        'original_unittest_limit_seconds': original_limit,
        'observed_exit': child.returncode, 'elapsed_seconds': elapsed,
        'user_seconds': usage.ru_utime, 'system_seconds': usage.ru_stime,
        'max_rss_kib': usage.ru_maxrss,
        'voluntary_context_switches': usage.ru_nvcsw,
        'involuntary_context_switches': usage.ru_nivcsw,
        'measurement': 'Linux wait4 for the direct harness process; monotonic wall clock includes launch and final wait.',
        'binary_sha256_before': binary_before, 'binary_sha256_after': sha(binary),
        'original_binary_sha256': old_hash,
        'binary_matches_original': binary_before == old_hash,
        'stdout_sha256': sha(directory / 'stdout.bin'),
        'stderr_sha256': sha(directory / 'stderr.bin'),
        'stdout_bytes': (directory / 'stdout.bin').stat().st_size,
        'stderr_bytes': (directory / 'stderr.bin').stat().st_size,
        'nm_exit': symbols.returncode, 'g_world_symbols': world_symbols,
        'nm_stdout_sha256': sha(directory / 'nm.stdout.txt'),
        'nm_stderr_sha256': sha(directory / 'nm.stderr.txt'),
        'acceptance_result': None,
        'meaning': 'This observation cannot revise the original 20/30-second unittest timeout or make the original receipt green.'
    }
    save(directory / 'measurement.json', result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


held, lock = os.fstat(7), Path('/run/lock/ga-wsl-v3.lock').stat()
assert (held.st_dev, held.st_ino) == (lock.st_dev, lock.st_ino)
prior = json.loads((ORIGINAL / 'summary.json').read_bytes())
assert prior['source'] == SOURCE and prior['source_unchanged']
root = Path(prior['source_root'])
before = manifest(root)
assert before == json.loads((ORIGINAL / 'source-after.json').read_bytes())
original_before = manifest(ORIGINAL)
runner_before = {name: sha(HERE / name) for name in RUNNERS}
OUT.mkdir(exist_ok=False)
save(OUT / 'source-before.json', before)
save(OUT / 'original-receipt-before.json', original_before)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
sys.path.insert(0, str(root))
results, build, error = [], None, None
try:
    domain = importlib.import_module('tests.test_geo261_domain_product')
    candidate = importlib.import_module('tests.test_geo261_candidate_product')
    domain.DomainStoreProduct.setUpClass()
    build = domain.native()
    candidate.CandidateProduct.setUpClass()
    assert candidate.native() is build
    original_artifacts = json.loads((ORIGINAL / 'native-build-artifacts.json').read_bytes())
    cases = [
        ([str(domain.DomainStoreProduct.exe), 'rollback'], 'rollback', 20, 'domain-host-product'),
        ([str(candidate.CandidateProduct.exe), 'imports', str(candidate.CandidateProduct.scene)],
         'imports', 30, 'candidate-product-client'),
    ]
    print(json.dumps({'stage': 'original NativeBuild and two setUpClass methods complete',
                      'compiler_commands': len(build.logs), 'cases': [case[1] for case in cases]}), flush=True)
    for command, label, limit, original_name in cases:
        results.append(measured(command, label, limit, original_artifacts[original_name]['sha256']))
except BaseException:
    error = traceback.format_exc()
    (OUT / 'diagnostic-error.txt').write_text(error, encoding='utf-8')
finally:
    artifacts = {}
    if build is not None:
        save(OUT / 'build-log.json', build.logs)
        for path in sorted(build.work.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(build.work)
            artifacts[str(relative)] = {'sha256': sha(path), 'bytes': path.stat().st_size}
            if path.suffix in ('.json', '.c', '.h', '.scene'):
                target = OUT / 'build-inputs' / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    save(OUT / 'build-artifacts.json', artifacts)
    after = manifest(root)
    save(OUT / 'source-after.json', after)
    original_after = manifest(ORIGINAL)
    save(OUT / 'original-receipt-after.json', original_after)
    runner_after = {name: sha(HERE / name) for name in RUNNERS}
    captured = (error is None and len(results) == 2 and before == after
                and original_before == original_after and runner_before == runner_after
                and all(r['binary_sha256_before'] == r['binary_sha256_after'] for r in results))
    summary = {
        'kind': 'two-recompiled-original-harness-timing-diagnostics-not-acceptance',
        'source': SOURCE, 'source_root': str(root), 'original_receipt': str(ORIGINAL),
        'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'platform': platform.platform(), 'python': sys.version,
        'results': results, 'diagnostic_error': error,
        'source_files': len(before), 'source_unchanged': before == after,
        'source_before_sha256': sha(OUT / 'source-before.json'),
        'source_after_sha256': sha(OUT / 'source-after.json'),
        'original_receipt_unchanged': original_before == original_after,
        'original_receipt_before_sha256': sha(OUT / 'original-receipt-before.json'),
        'original_receipt_after_sha256': sha(OUT / 'original-receipt-after.json'),
        'runner_sha256_before': runner_before, 'runner_sha256_after': runner_after,
        'runners_unchanged': runner_before == runner_after,
        'compiler_commands': len(build.logs) if build is not None else None,
        'build_artifacts': len(artifacts),
        'shared_lock_holder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
        'unittest_methods_executed': 0, 'mutations_executed': False,
        'full_suite_executed': False, 'acceptance_result': None,
        'capture_exit': 0 if captured else 1,
        'meaning': 'Capture completion is not product acceptance; the original 101-method failed receipt remains unchanged.'
    }
    save(OUT / 'summary.json', summary)
    (OUT / 'exit.txt').write_text(str(summary['capture_exit']) + '\n', encoding='ascii')
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
sys.exit(summary['capture_exit'])
