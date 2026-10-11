#!/usr/bin/env python3
"""Reproduce PR 194's loopback regressions and 47 targeted mutations.

Run under wsl_locked3.sh run, passing --head FULL_SHA --work NEW_DIRECTORY
--out NEW_RECEIPT_DIRECTORY --runner-tools DIRECTORY_CONTAINING_ci_run.py.
The supplied source repository is read only. Every mutation happens in a fresh
private clone; no LAN listener, user certificate directory or network settings
are used. Baseline 97 tests = existing LAN 30 + review 17 + loopback server 50.
Each mutation runs its named tests, restores the exact bytes and reruns those
tests. An unexpected result stops the run after restoration.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--head', required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runner-tools', type=Path, required=True)
    parser.add_argument('--source', default='/mnt/d/geometry-axiom')
    parser.add_argument('--only', nargs='*', default=[])
    args = parser.parse_args()
    if not re.fullmatch(r'[a-f0-9]{40}', args.head):
        parser.error('--head must be a full commit SHA')
    if not os.environ.get('WSL_CI_JOB_TAG'):
        parser.error('run this script through the WSL v3 queue with a dedicated WSL_CI_JOB_TAG')
    if args.work.exists() or args.out.exists():
        parser.error('work/output directories must be new; existing evidence is never overwritten')
    args.work.mkdir(parents=True)
    args.out.mkdir(parents=True)
    root = args.work / 'repo'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
               LANG='C.UTF-8', LC_ALL='C.UTF-8', GEOMETRY_FEEDBACK_DIR=str(args.out / 'feedback'))
    receipt = {'head': args.head, 'status': 'running', 'steps': [], 'mutants': []}

    def save():
        (args.out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    def run(label, command, *, cwd=root, expected=0, needle=None, count=None, timeout=600):
        path = args.out / (label + '.log')
        started = time.monotonic()
        with path.open('wb') as stream:
            child = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            try:
                rc = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                rc = 124
        output = path.read_text(encoding='utf-8', errors='replace')
        found = re.findall(r'^Ran (\d+) tests? in ', output, re.M)
        row = {'label': label, 'command': command, 'exit': rc, 'expected_exit': expected,
               'seconds': round(time.monotonic()-started, 3), 'log': str(path), 'log_sha256': sha(path.read_bytes())}
        receipt['steps'].append(row)
        save()
        if rc != expected or (needle and needle not in output) or (count is not None and found != [str(count)]):
            raise RuntimeError('unexpected result: ' + label)
        if count is not None and ('skipped=' in output or '\nERROR:' in output):
            raise RuntimeError('skip or unrelated test error: ' + label)
        print(json.dumps(row), flush=True)
        return output

    spec = importlib.util.spec_from_file_location('ci_runner', args.runner_tools / 'ci_run.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    if runner.scan_processes()[1]:
        raise RuntimeError('foreign process at start')
    sampler = runner.ForeignSampler()
    sampler.start()
    try:
        run('clone', ['git', '-c', 'core.autocrlf=false', 'clone', '--no-checkout', args.source, str(root)], cwd=args.work)
        run('checkout', ['git', 'checkout', '--detach', args.head])
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, env=env).decode().strip()
        if actual != args.head:
            raise RuntimeError('checkout is not the requested head')
        registry = json.loads((root / 'tests/evidence/lan_review_mutants.json').read_text(encoding='utf-8'))
        rows = registry['mutants']
        if args.only:
            selected = set(args.only)
            if selected - {row['id'] for row in rows}:
                raise RuntimeError('unknown mutation id')
            rows = [row for row in rows if row['id'] in selected]
        paths = {row['path'] for row in rows} | {'geometry-web/native_context.py',
            'tests/test_lan_review.py', 'tests/test_serve_lan.py', 'tests/test_serve.py',
            'tests/evidence/lan_review_mutants.json', 'tests/evidence/lan_review_proof.py'}
        receipt['source_hashes'] = {path: sha((root / path).read_bytes()) for path in sorted(paths)}
        unit = [sys.executable, '-m', 'unittest', '-v']
        baseline = ['tests.test_serve_lan', 'tests.test_lan_review', 'tests.test_serve']
        run('baseline-before', unit + baseline, count=97)
        for row in rows:
            path = root / row['path']
            original = path.read_bytes()
            changed = original.decode('utf-8')
            for old, new in row['edits']:
                if changed.count(old) != 1:
                    raise RuntimeError('nonunique/absent mutation anchor: ' + row['id'])
                changed = changed.replace(old, new)
            mutated = changed.encode('utf-8')
            record = {'id': row['id'], 'label': row['label'], 'path': row['path'], 'tests': row['tests'],
                      'needle': row['needle'], 'original_sha256': sha(original), 'mutated_sha256': sha(mutated),
                      'status': 'running'}
            receipt['mutants'].append(record)
            save()
            try:
                path.write_bytes(mutated)
                run(row['id'] + '-red', unit + row['tests'], expected=1, needle=row['needle'], count=len(row['tests']))
                record['status'] = 'detected'
            finally:
                path.write_bytes(original)
                if path.read_bytes() != original:
                    raise RuntimeError('restore mismatch: ' + row['id'])
                record['restored_sha256'] = sha(path.read_bytes())
                save()
            run(row['id'] + '-restored', unit + row['tests'], count=len(row['tests']))
            record['restored_green'] = True
            save()
        run('baseline-after', unit + baseline, count=97)
        receipt['status'] = 'passed'
    except BaseException as exc:
        receipt.update(status='blocked-unexpected-result', error=repr(exc))
        raise
    finally:
        receipt['exclusivity'] = {'during_run': sampler.report()}
        if receipt['exclusivity']['during_run']['foreign_processes_seen_during_run']:
            receipt['status'] = 'invalid-foreign-processes'
        save()
    if receipt['status'] != 'passed':
        raise RuntimeError(receipt['status'])


if __name__ == '__main__':
    main()
