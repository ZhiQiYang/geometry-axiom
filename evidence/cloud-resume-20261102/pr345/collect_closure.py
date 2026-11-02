#!/usr/bin/env python3
"""Collect Git identities and original registry metadata without running suites."""
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('/tmp/geometry-pr345-20261102')
OUT = Path(__file__).resolve().parent
BASE = '5775a9e9e46bca801a9a70aaeafcdab9f597bc4d'
OLD = '99646d418bc5e886a92bfdabe33e68780e88fe3b'
TARGET = 'tests/test_rule_case_workbench_http.py'
commands = []

def git(*args):
    argv = ['git', *args]
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    number = len(commands) + 1
    for name, raw in [('stdout', p.stdout), ('stderr', p.stderr)]:
        (OUT / f'static-{number:02d}-{name}.bin.gz').write_bytes(gzip.compress(raw, mtime=0))
    commands.append({'argv': argv, 'cwd': str(ROOT), 'exit': p.returncode,
                     'stdoutBytes': len(p.stdout), 'stdoutSha256': hashlib.sha256(p.stdout).hexdigest(),
                     'stderrBytes': len(p.stderr), 'stderrSha256': hashlib.sha256(p.stderr).hexdigest()})
    if p.returncode:
        raise RuntimeError(f'Git subcommand failed: {argv!r}')
    return p.stdout

def tree(ref):
    raw = git('ls-tree', '-r', '-z', ref)
    result = {}
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        metadata, path = entry.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        result[path.decode()] = {'mode': mode, 'type': kind, 'blob': oid}
    return result

head = git('rev-parse', 'HEAD').decode().strip()
parents = git('show', '-s', '--format=%P', 'HEAD').decode().strip().split()
assert parents == [OLD, BASE], parents
trees = {ref: tree(ref) for ref in [BASE, OLD, head]}
main, old, current = (trees[ref] for ref in [BASE, OLD, head])
delta = {p: {'main': main.get(p), 'head': current.get(p)}
         for p in sorted(set(main) | set(current)) if main.get(p) != current.get(p)}
source_delta = {p: d for p, d in delta.items() if not p.startswith('evidence/')}
assert list(source_delta) == [TARGET], list(source_delta)
evidence = {p: d for p, d in delta.items() if p.startswith('evidence/')}
assert len(evidence) == 13, len(evidence)
assert all(current[p] == old.get(p) for p in evidence)
assert current[TARGET] == old[TARGET]
diff = git('diff', BASE, head, '--', TARGET)
(OUT / 'MAIN_DELTA.patch').write_bytes(diff)
assert diff.count(b'\n-') == 2 and diff.count(b'\n+') == 2
assert b'kwargs={"poll_interval": 0.05}' in diff
assert git('diff', '--check') == b''
status = git('status', '--porcelain=v1', '--untracked-files=all').decode()
assert status == '', status

sys.path.insert(0, str(ROOT / 'tests'))
import binaries
fingerprint, hashes, command = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
binary_inputs = {'fingerprint': fingerprint, 'sourceHashes': hashes, 'compileCommand': command}
(OUT / 'BRIDGE_SOURCE_INPUTS.json').write_text(json.dumps(binary_inputs, ensure_ascii=False, indent=2) + '\n')
assert all(current.get(path) == main.get(path) for path in hashes), 'Bridge Git closure changed'

spec = importlib.util.spec_from_file_location('pr345_original_run_all', ROOT / 'tests/run_all.py')
run_all = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_all)
selected = [s for s in run_all.build_suites() if s.name == 'py:test_rule_case_workbench_http']
assert len(selected) == 1
suite = selected[0]
expected = json.loads((ROOT / 'tests/run_all.expected.json').read_text())
expected_row = expected['suites'][suite.name]
assert expected_row['count'] == 19, expected_row
assert suite.timeout == 1200, suite.timeout
method_count = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')
                   for n in ast.walk(ast.parse((ROOT / TARGET).read_text())))
assert method_count == 19, method_count
registry_errors = run_all.check_registry()
assert not registry_errors, registry_errors

def digest(entries):
    raw = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()

summary = {'head': head, 'parents': parents, 'main': BASE, 'originalPrHead': OLD,
           'sourceTargetBlobUnchangedFromOriginalPr': current[TARGET]['blob'],
           'deltaFromMain': delta, 'evidenceBytesRetainedByExactGitEntry': list(evidence),
           'treeCounts': {ref: len(entries) for ref, entries in trees.items()},
           'treeEntryDigests': {ref: digest(entries) for ref, entries in trees.items()},
           'bridgeSourceInputCount': len(hashes), 'bridgeFingerprint': fingerprint,
           'bridgeInputsEqualMainByGitEntry': True,
           'selected': {'name': suite.name, 'command': suite.cmd, 'needs': suite.needs,
                        'timeoutSeconds': suite.timeout, 'expected': expected_row,
                        'testMethods': method_count, 'registryErrors': registry_errors},
           'statusPorcelain': status, 'testsExecuted': False,
           'historyReceiptExecutionSha': '2199cda8896b47c7ad2b6c10479e5e0cbdb67c83',
           'historyReceiptRelabelledAsCurrentExecution': False}
(OUT / 'STATIC_CLOSURE.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
(OUT / 'STATIC_SUBCOMMANDS.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'head': head, 'parents': parents, 'sourceDeltaCount': len(source_delta),
                  'evidenceDeltaCount': len(evidence), 'bridgeInputCount': len(hashes),
                  'selectedExpected': expected_row, 'selectedTimeout': suite.timeout,
                  'worktreeClean': not status, 'testsExecuted': False}, ensure_ascii=False))
