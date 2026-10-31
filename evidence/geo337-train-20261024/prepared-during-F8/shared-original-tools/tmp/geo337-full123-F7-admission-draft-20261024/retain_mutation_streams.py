"""Observe original subprocess.run outcomes while executing unmodified mutate.py.

The real run receives the exact same positional and keyword argument objects.
The returned CompletedProcess is returned by identity. Original exceptions are
re-raised unchanged. No retries, timeouts, subprocess environment changes or
test verdict changes are introduced. Original text output is retained as UTF-8,
the exact representation hashed by tests/mutate.py::attempt_receipt.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time


def digest(body):
    return hashlib.sha256(body).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def serial(value):
    if isinstance(value, Path):
        return os.fspath(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return [serial(v) for v in value]
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    return {"python_type": type(value).__name__, "repr": repr(value)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('original_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if len(args.sha) != 40 or any(c not in '0123456789abcdef' for c in args.sha):
        raise ValueError('expected full source SHA')
    root, out = args.root.resolve(), args.out.resolve()
    if out.is_relative_to(root) or out.exists():
        raise ValueError('observation output must be fresh and outside source')
    if Path.cwd().resolve() != root:
        raise ValueError('launch cwd must be the original repository root')
    for name in ('MUTATE_RESULTS', 'MUTATE_CACHE'):
        if not os.environ.get(name) or Path(os.environ[name]).resolve().is_relative_to(root):
            raise ValueError(name+' must name an external path')
    if sys.flags.optimize:
        raise ValueError('original assertions require non-optimized Python')
    original_run = subprocess.run
    preflights = []
    def preflight(argv):
        completed = original_run(argv, cwd=root, capture_output=True, check=False)
        preflights.append({'argv':argv,'exit_code':completed.returncode,
                           'stdout_hex':completed.stdout.hex(),'stderr_hex':completed.stderr.hex()})
        return completed
    check = preflight(['git', 'rev-parse', 'HEAD'])
    if check.returncode or check.stdout.decode().strip() != args.sha:
        raise ValueError('source HEAD does not match the expected SHA')
    clean = preflight(['git', 'status', '--porcelain=v1', '--untracked-files=all'])
    if clean.returncode or clean.stdout:
        raise ValueError('source checkout must be clean, including untracked files')
    watched = ['tests/mutate.py', 'tests/mutation_bridge.py', 'tests/run_tests.py']
    for path in watched:
        committed = preflight(['git', 'show', args.sha+':'+path])
        if committed.returncode or committed.stdout != (root/path).read_bytes():
            raise ValueError('source tool bytes differ from committed F: '+path)
    argv = list(args.original_args)
    if argv[:1] == ['--']:
        argv = argv[1:]
    out.mkdir(parents=True)
    commands = out / 'commands'
    commands.mkdir()
    counter = itertools.count(1)
    records, observation_errors = [], []
    before = {p: digest((root/p).read_bytes()) for p in watched}
    selected_env = ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'CC', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS',
                    'PYTHONOPTIMIZE', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPATH', 'PYTHONSTARTUP',
                    'NODE_OPTIONS', 'MUTATE_RESULTS', 'MUTATE_CACHE')
    request = {'schema': 'original-mutation-run-observer/1', 'started_utc': utc(),
               'source_sha': args.sha, 'root': str(root), 'out': str(out),
               'original_entry': 'tests/mutate.py', 'original_argv': ['tests/mutate.py', *argv],
               'python_executable':sys.executable, 'source_preflights':preflights,
               'outer_argv': sys.argv[:], 'source_tool_sha256_before': before,
               'observer_sha256': digest(Path(__file__).read_bytes()),
               'environment': {k: os.environ.get(k) for k in selected_env},
               'scope': 'Parent original subprocess.run calls only; original bridge Popen streams remain in original mutation-cache files.',
               'stream_representation': 'bytes are copied unchanged; str is UTF-8 encoded exactly as original attempt_receipt hashes; never described as pre-decode OS pipe bytes.'}
    (out/'request.json').write_text(json.dumps(request, ensure_ascii=False, indent=2)+'\n')

    def retain(number, positional, keyword, started, completed=None, failure=None):
        folder = commands / ('%06d' % number)
        folder.mkdir()
        active_env = keyword.get('env')
        if active_env is None:
            active_env = os.environ
        row = {'number': number, 'started_epoch': started, 'ended_epoch': time.time(),
               'args': serial(positional), 'keyword_arguments_except_env': serial({k:v for k,v in keyword.items() if k != 'env'}),
               'selected_environment': {k: active_env.get(k) for k in selected_env},
               'completed_process_returned': completed is not None,
               'returncode': completed.returncode if completed is not None else None,
               'exception': None if failure is None else {'type': type(failure).__name__, 'repr': repr(failure)}}
        source = completed if completed is not None else failure
        for stream in ('stdout', 'stderr'):
            value = getattr(source, stream, None)
            if value is None:
                row[stream] = {'captured': False, 'python_type': 'NoneType'}
                continue
            if isinstance(value, bytes):
                body, representation = value, 'original-bytes'
            elif isinstance(value, str):
                body, representation = value.encode('utf-8'), 'original-text-encoded-utf8'
            else:
                raise TypeError('unexpected original '+stream+' type '+type(value).__name__)
            path = folder/(stream+'.bin')
            path.write_bytes(body)
            row[stream] = {'captured': True, 'python_type': type(value).__name__,
                           'representation': representation, 'path': str(path),
                           'bytes': len(body), 'sha256': digest(body)}
        (folder/'result.json').write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n')
        records.append(row)

    def safe_retain(*a, **kw):
        try:
            retain(*a, **kw)
        except Exception as error:
            # Audit failure is separate; never turn the original run result into a fake failure/pass.
            observation_errors.append({'type': type(error).__name__, 'repr': repr(error)})

    def observed_run(*positional, **keyword):
        number, started = next(counter), time.time()
        try:
            completed = original_run(*positional, **keyword)
        except BaseException as original_exception:
            try:
                safe_retain(number, positional, keyword, started, failure=original_exception)
            except BaseException as observation_interrupt:
                # Keep the already-raised original exception identity, including interrupts.
                observation_errors.append({'while_preserving_original_exception': repr(observation_interrupt)})
            raise
        safe_retain(number, positional, keyword, started, completed=completed)
        return completed

    original_exception = None
    original_completed = False
    original_exit = None
    old_argv, old_path = sys.argv, sys.path[:]
    subprocess.run = observed_run
    sys.argv = ['tests/mutate.py', *argv]
    sys.path[0] = str(root/'tests')
    try:
        runpy.run_path('tests/mutate.py', run_name='__main__')
        original_completed, original_exit = True, 0
    except BaseException as error:
        original_exception = error
        if isinstance(error, SystemExit):
            original_completed = True
            original_exit = 0 if error.code is None else error.code if isinstance(error.code, int) else 1
        elif isinstance(error, KeyboardInterrupt):
            original_exit = 130
        raise
    finally:
        subprocess.run = original_run
        sys.argv, sys.path[:] = old_argv, old_path
        after = {}
        for path in watched:
            try:
                after[path] = digest((root/path).read_bytes())
            except Exception as error:
                observation_errors.append({'source_after_read':path, 'type':type(error).__name__, 'repr':repr(error)})
        postflights=[]
        for command in (['git','rev-parse','HEAD'], ['git','status','--porcelain=v1','--untracked-files=all']):
            try:
                completed=original_run(command,cwd=root,capture_output=True,check=False)
                postflights.append({'argv':command,'exit_code':completed.returncode,
                                    'stdout_hex':completed.stdout.hex(),'stderr_hex':completed.stderr.hex()})
                expected=(args.sha+'\n').encode() if command[1]=='rev-parse' else b''
                if completed.returncode or completed.stdout!=expected:
                    observation_errors.append({'source_postflight_mismatch':command})
            except Exception as error:
                observation_errors.append({'source_postflight_error':repr(error),'argv':command})
        audit = {'schema': 'original-mutation-run-observer-receipt/1', 'ended_utc': utc(),
                 'source_sha': args.sha, 'original_completed': original_completed,
                 'original_exit': original_exit,
                 'original_exception': None if original_exception is None else {'type':type(original_exception).__name__, 'repr':repr(original_exception)},
                 'source_tool_sha256_after': after, 'source_tool_bytes_unchanged': before == after,
                 'source_postflights':postflights,
                 'commands': records, 'observation_errors': observation_errors,
                 'observer_complete': not observation_errors and before == after,
                 'subject_verdicts_changed': False}
        try:
            (out/'receipt.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
        except Exception as error:
            observation_errors.append({'final_receipt_write':repr(error)})
            print('OBSERVATION_RECEIPT_WRITE_FAILED '+repr(error), file=sys.stderr, flush=True)
        # Original failures/interrupts retain their original exception. A successful CLI with
        # incomplete raw must instead produce an explicitly separate observation failure.
        if original_exit == 0 and (observation_errors or before != after):
            raise RuntimeError('original CLI exit0, but raw observation/integrity is incomplete')


if __name__ == '__main__':
    main()
