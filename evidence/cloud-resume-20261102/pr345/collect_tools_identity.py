#!/usr/bin/env python3
"""Bind the tool-only merge to the previous selected-suite execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('/tmp/geometry-pr345-20261102')
OUT = Path(__file__).resolve().parent
PREVIOUS = 'c8db6777819c844064aa79baf089ff1ce58d5e5f'
TOOLS = '502a64ff6214dd6060927b7f14643a533536f20d'
PATHS = ['.github/scripts/architecture_evidence.py', '.github/scripts/mutation_evidence.py',
         '.github/workflows/mutation-evidence.yml', 'tests/MUTATION-EVIDENCE.md']
commands = []

def git(*args):
    argv = ['git', *args]
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    n = len(commands) + 1
    for name, raw in [('stdout', p.stdout), ('stderr', p.stderr)]:
        (OUT / f'tools-identity-{n:02d}-{name}.bin').write_bytes(raw)
    commands.append({'argv': argv, 'cwd': str(ROOT), 'exit': p.returncode,
                     'stdoutSha256': hashlib.sha256(p.stdout).hexdigest(),
                     'stderrSha256': hashlib.sha256(p.stderr).hexdigest()})
    assert p.returncode == 0, argv
    return p.stdout

def entries(ref, paths):
    rows = git('ls-tree', '-z', ref, '--', *paths).split(b'\0')
    result = {}
    for row in rows:
        if row:
            meta, name = row.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            result[name.decode()] = {'mode': mode, 'type': kind, 'blob': oid}
    return result

head = git('rev-parse', 'HEAD').decode().strip()
parents = git('show', '-s', '--format=%P', 'HEAD').decode().strip().split()
assert parents == [PREVIOUS, TOOLS], parents
delta = git('diff', '--name-only', PREVIOUS, head).decode().splitlines()
assert delta == PATHS, delta
raw = git('diff', '--raw', '--no-abbrev', PREVIOUS, head)
(OUT / 'TOOLS_ONLY_DELTA.raw').write_bytes(raw)
current = entries(head, PATHS)
original = entries(TOOLS, PATHS)
assert current == original
protected = ['AGENTS.md', '公理層.md', '決策佇列.md', 'geometry-guide/公理層-閱讀器.html',
             'tests/binaries.py', 'tests/run_all.py', 'tests/run_all.expected.json',
             'tests/test_rule_case_workbench_http.py', 'tests/mutate.py',
             'tests/mutants_results.json']
assert entries(head, protected) == entries(PREVIOUS, protected)
assert git('diff', '--check') == b''
assert git('status', '--porcelain=v1', '--untracked-files=all') == b''
sys.path.insert(0, str(ROOT / 'tests'))
import binaries
fp, hashes, command = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
old = json.loads((OUT / 'BRIDGE_SOURCE_INPUTS.json').read_text())
assert fp == old['fingerprint'] and hashes == old['sourceHashes'] and command == old['compileCommand']
ledger = ROOT / 'tests/mutants_results.json'
ledger_before = {'sha256': hashlib.sha256(ledger.read_bytes()).hexdigest(),
                 'bytes': ledger.stat().st_size, 'mtimeNs': ledger.stat().st_mtime_ns,
                 'gitEntry': entries(head, ['tests/mutants_results.json'])['tests/mutants_results.json']}
result = {'head': head, 'parents': parents, 'previousCandidateAndSelectedExecution': PREVIOUS,
          'toolDependencyHead': TOOLS, 'toolDependencyPr': 366,
          'toolDependencyUnmergedAtHandoff': True, 'targetPrBase': 'main',
          'deltaFromPreviousCandidate': delta, 'toolEntries': current,
          'toolEntriesExactlyEqualDependency': True,
          'protectedSourceEntriesEqualPreviousCandidate': True,
          'bridgeFingerprint': fp, 'bridgeInputCount': len(hashes),
          'bridgeCompileClosureEqualPreviousCandidate': True,
          'ledgerBeforeCheck': ledger_before,
          'selected19ExecutionRemains': PREVIOUS,
          'selected19RerunAtNewHead': False, 'fullMutationRerunAtNewHead': False,
          'requiredCiAtNewHead': 'UNRUN', 'worktreeClean': True}
(OUT / 'TOOLS_MERGE_IDENTITY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
(OUT / 'TOOLS_IDENTITY_SUBCOMMANDS.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'head': head, 'parents': parents, 'toolCount': len(current),
                  'bridgeInputs': len(hashes), 'toolBlobsPreserved': True,
                  'selectedExecutionRemains': PREVIOUS, 'newTestsRun': False}))
