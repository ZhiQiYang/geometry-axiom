#!/usr/bin/env python3
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('/tmp/geometry-pr344-20261102')
OUT = Path(__file__).resolve().parent
MAIN = '5775a9e9e46bca801a9a70aaeafcdab9f597bc4d'
ORIGINAL = 'df39d1933402c76b2f8b35ca013412daf16ed4c9'
TOOLS = '502a64ff6214dd6060927b7f14643a533536f20d'
TOOL_PATHS = ['.github/scripts/architecture_evidence.py', '.github/scripts/mutation_evidence.py',
              '.github/workflows/mutation-evidence.yml', 'tests/MUTATION-EVIDENCE.md']
SOURCE_PATHS = ['geometry-core/domain-decoupling/product-architecture.json', 'geometry-web/app.js',
                'geometry-web/cdp_test.js', 'tests/run_all.expected.json', 'tests/run_all.py',
                'tests/test_connection_recovery.js']
DERIVED = ['geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md',
           'geometry-core/domain-decoupling/product-architecture-receipt.json']
commands = []

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args):
    argv = ['git', *args]
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    n = len(commands) + 1
    for name, raw in [('stdout', p.stdout), ('stderr', p.stderr)]:
        (OUT / f'source-{n:02d}-{name}.bin.gz').write_bytes(gzip.compress(raw, mtime=0))
    commands.append({'argv': argv, 'cwd': str(ROOT), 'exit': p.returncode,
                     'stdoutSha256': sha(p.stdout), 'stderrSha256': sha(p.stderr)})
    assert p.returncode == 0, argv
    return p.stdout

def tree(ref):
    result = {}
    for row in git('ls-tree', '-r', '-z', ref).split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            result[path.decode()] = {'mode': mode, 'type': kind, 'blob': oid}
    return result

head = git('rev-parse', 'HEAD').decode().strip()
parents = git('show', '-s', '--format=%P', head).decode().strip().split()
main_merge = parents[0]
assert parents[1] == TOOLS
assert git('show', '-s', '--format=%P', main_merge).decode().strip().split() == [ORIGINAL, MAIN]
trees = {ref: tree(ref) for ref in [MAIN, ORIGINAL, TOOLS, head]}
main, old, tools, current = (trees[ref] for ref in [MAIN, ORIGINAL, TOOLS, head])
delta = {p: {'main': main.get(p), 'head': current.get(p)}
         for p in sorted(set(main) | set(current)) if main.get(p) != current.get(p)}
non_evidence = {p: v for p, v in delta.items() if not p.startswith('evidence/')}
assert sorted(non_evidence) == sorted(SOURCE_PATHS + TOOL_PATHS), sorted(non_evidence)
assert all(current[p] == tools[p] for p in TOOL_PATHS)
assert all(current[p] == main[p] for p in DERIVED)
assert all(current[p] == old[p] for p in ['geometry-web/app.js', 'geometry-web/cdp_test.js', 'tests/test_connection_recovery.js'])
evidence = {p: v for p, v in delta.items() if p.startswith('evidence/')}
assert all(current[p] == old.get(p) for p in evidence)
main_manifest = json.loads(git('show', MAIN + ':geometry-core/domain-decoupling/product-architecture.json'))
manifest = json.loads((ROOT / 'geometry-core/domain-decoupling/product-architecture.json').read_text())
policy = copy.deepcopy(manifest)
for entry in policy['exclusions']:
    if entry['path'] == 'geometry-web/cdp_test.js':
        entry['sha256'] = next(e['sha256'] for e in main_manifest['exclusions'] if e['path'] == entry['path'])
assert policy == main_manifest
cdp_lf_sha = sha((ROOT / 'geometry-web/cdp_test.js').read_bytes().replace(b'\r\n', b'\n'))
assert cdp_lf_sha == next(e['sha256'] for e in manifest['exclusions'] if e['path'] == 'geometry-web/cdp_test.js')
expected = json.loads((ROOT / 'tests/run_all.expected.json').read_text())
node_expected = expected['suites'].pop('node:connection_recovery')
assert node_expected == {'mode': 'count', 'count': 9, 'unit': 'node test'}
assert expected == json.loads(git('show', MAIN + ':tests/run_all.expected.json'))
diff = git('diff', MAIN, head, '--', *SOURCE_PATHS, *TOOL_PATHS)
(OUT / 'SOURCE_DELTA.patch').write_bytes(diff)
assert git('diff', '--check') == b''
assert git('status', '--porcelain=v1', '--untracked-files=all') == b''
inputs = []
for entry in sorted(manifest['sources'] + manifest['exclusions'], key=lambda e: e['path']):
    path = entry['path']
    raw = (ROOT / path).read_bytes()
    st = (ROOT / path).stat()
    inputs.append({'path': path, 'sha256': sha(raw.replace(b'\r\n', b'\n')),
                   'rawSha256': sha(raw), 'bytes': len(raw), 'mode': st.st_mode,
                   'mtimeNs': st.st_mtime_ns, 'gitEntry': current[path]})
assert len(inputs) == 604
(OUT / 'ARCHITECTURE_INPUTS_BEFORE.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n')
sys.path.insert(0, str(ROOT / 'tests'))
import binaries
fp, hashes, command = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
assert all(current.get(path) == main.get(path) for path in hashes)
ledger = ROOT / 'tests/mutants_results.json'
result = {'head': head, 'parents': parents, 'mainConvergence': main_merge, 'main': MAIN,
          'originalPrHead': ORIGINAL, 'toolDependency': TOOLS, 'toolDependencyPr': 366,
          'nonEvidenceDelta': non_evidence, 'historicalEvidenceCount': len(evidence),
          'historicalEvidenceEntriesRetained': list(evidence),
          'conflictResolution': {'paths': DERIVED, 'adoptedEntries': 'exact current-main historical derived entries',
                                 'notCurrentExecutionReceipts': True},
          'policySemanticallyEqualsMainExceptOneCdpDigest': True,
          'cdpLfSha256': cdp_lf_sha, 'architectureInputCount': len(inputs),
          'architectureLfClosureSha256': sha(json.dumps([{'path': e['path'], 'sha256': e['sha256']} for e in inputs], ensure_ascii=False, separators=(',', ':')).encode()),
          'nodeExpected': node_expected, 'allExistingExpectedEntriesUnchanged': True,
          'bridgeInputsEqualMain': True, 'bridgeInputCount': len(hashes), 'bridgeFingerprint': fp,
          'ledgerBeforeCheck': {'gitEntry': current['tests/mutants_results.json'], 'sha256': sha(ledger.read_bytes()),
                                'bytes': ledger.stat().st_size, 'mtimeNs': ledger.stat().st_mtime_ns},
          'protectedEntries': {p: current[p] for p in ['AGENTS.md', '公理層.md', '決策佇列.md', 'geometry-guide/公理層-閱讀器.html']},
          'worktreeClean': True}
(OUT / 'SOURCE_IDENTITY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
(OUT / 'SOURCE_SUBCOMMANDS.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'head': head, 'mainConvergence': main_merge, 'nonEvidencePaths': len(non_evidence),
                  'historicalEvidenceCount': len(evidence), 'architectureInputs': len(inputs),
                  'bridgeInputs': len(hashes), 'nodeExpected': node_expected, 'worktreeClean': True}))
