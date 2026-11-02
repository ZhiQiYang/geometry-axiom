#!/usr/bin/env python3
"""Close actual local gate receipts without modifying tracked source artifacts."""
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path('/tmp/geometry-pr344-20261102')
OUT = Path(__file__).resolve().parent
source = json.loads((OUT / 'SOURCE_IDENTITY.json').read_text())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == source['head']
before = json.loads((OUT / 'ARCHITECTURE_INPUTS_BEFORE.json').read_text())

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

after = []
for entry in before:
    path = ROOT / entry['path']
    raw = path.read_bytes()
    st = path.stat()
    after.append({**entry, 'sha256': sha(raw.replace(b'\r\n', b'\n')), 'rawSha256': sha(raw),
                  'bytes': len(raw), 'mode': st.st_mode, 'mtimeNs': st.st_mtime_ns})
assert after == before
(OUT / 'ARCHITECTURE_INPUTS_AFTER.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n')
ledger = ROOT / 'tests/mutants_results.json'
ledger_after = {'sha256': sha(ledger.read_bytes()), 'bytes': ledger.stat().st_size,
                'mtimeNs': ledger.stat().st_mtime_ns}
assert all(value == source['ledgerBeforeCheck'][key] for key, value in ledger_after.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=all'], cwd=ROOT) == b''

records = []
for name, label, count in [('15-architecture-cli', 'architecture-contract', None),
                           ('16-architecture-unit', 'architecture-unit', 205),
                           ('17-architecture-product', 'architecture-product', 18)]:
    folder = OUT / 'commands' / name
    request = json.loads((folder / 'REQUEST.json').read_text())
    result = json.loads((folder / 'RESULT.json').read_text())
    assert result['actualProcessReturncode'] == 0
    for stream, meta in result['streams'].items():
        raw = (folder / stream).read_bytes()
        assert len(raw) == meta['bytes'] and sha(raw) == meta['sha256']
    stderr = (folder / 'stderr.bin').read_bytes()
    row = {'command': request['argv'], 'cwd': request['cwd'], 'acceptance_sha': head,
           'source_sha': head, 'source_variant': label, 'environment': request['environment'],
           'startedUtc': request['startedUtc'], 'endedUtc': result['endedUtc'],
           'actual_process_returncode': 0, 'exitCode': 0, 'timeout_expired': False,
           'elapsedSeconds': result['elapsedSeconds'], 'directory': str(folder),
           'stdout_sha256': result['streams']['stdout.bin']['sha256'],
           'stderr_sha256': result['streams']['stderr.bin']['sha256'],
           'stdout_bytes': result['streams']['stdout.bin']['bytes'],
           'stderr_bytes': result['streams']['stderr.bin']['bytes']}
    if count is not None:
        match = re.search(rb'Ran (\d+) tests in ', stderr)
        assert match and int(match[1]) == count and stderr.rstrip().endswith(b'OK')
        assert b'skipped=' not in stderr
        row.update({'testsRun': count, 'skipped': 0})
    records.append(row)

scan_bytes = (OUT / 'commands/15-architecture-cli/stdout.bin').read_bytes()
scan = json.loads(scan_bytes)
assert scan['ok'] is True and scan['diagnostics'] == [] and len(scan['edges']) == 798
manifest_path = 'geometry-core/domain-decoupling/product-architecture.json'
manifest_raw = (ROOT / manifest_path).read_bytes()
manifest = json.loads(manifest_raw)
inputs = [{'path': e['path'], 'sha256': e['sha256']} for e in after]
closure_sha = sha(json.dumps(inputs, ensure_ascii=False, separators=(',', ':')).encode())
assert closure_sha == source['architectureLfClosureSha256']
counts = {'executableFiles': len(inputs), 'ownedSources': len(manifest['sources']),
          'exclusions': len(manifest['exclusions']), 'edges': len(scan['edges']), 'diagnostics': 0,
          'layers': dict(Counter(e['layer'] for e in manifest['sources'])),
          'languages': dict(Counter(e['language'] for e in manifest['sources'])),
          'forbiddenIdentifiers': len(manifest['policy']['forbiddenIdentifiers']),
          'forbiddenStrings': len(manifest['policy']['forbiddenStrings'])}
artifact = OUT / 'architecture'
artifact.mkdir(exist_ok=False)
report = (
    '# Product architecture — PR344 local fixed-source receipt\n\n'
    f'實際 execution source `{head}`；普通 main merge 採入 `{source["main"]}`。'
    '這是本機雲端 Linux 的原三命令實跑，沒有 GitHub run id，也不冒稱 Actions 執行。\n\n'
    '三命令 exit 0／0／0；generic205、product18，零 skip。604 inputs、334 owned／270 exclusions、'
    f'798 edges／0 diagnostics；LF closure `{closure_sha}`。原來源與 index、604 個 raw/LF/Git 身分前後一致。\n\n'
    '保留 main 的937 identifiers／55 strings與全部政策；只有原 PR 的 CDP exclusion digest 變動，'
    '實際 LF bytes 與之相符。這份外置組裝不改 repo 內仍標明歷史來源的報告／receipt。\n\n'
    '本收據不認證完整 native、browser、mutation fresh ledger、效能、Windows 或舊控制在此來源的新執行。'
    'Node9 三相另有獨立原件，使用明示 DOM／transport 替身，不能解除真 browser S/V/S。\n'
)
report_raw = report.encode()
receipt = {
    'schema': 'geometry-product-architecture-receipt/1',
    'hashMode': 'sha256 after CRLF-to-LF normalization',
    'inputClosureHashSerialization': 'SHA-256 of UTF-8 JSON for the path-sorted inputs array, with ensure_ascii=false and separators=(comma,colon); each entry has path then sha256, and no trailing newline.',
    'inputClosureExcludes': [manifest_path, 'geometry-core/domain-decoupling/product-architecture-scan.json',
                           'geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md',
                           'geometry-core/domain-decoupling/product-architecture-receipt.json'],
    'inputClosureExclusionReason': 'Non-executable derived artifacts; receipt does not hash itself.',
    'notClaimed': ['native', 'fresh mutation ledger', 'browser', 'new performance comparison',
                   'Windows probes', 'new W lexicon completeness audit', 'historical controls rerun'],
    'headBinding': 'Original three commands ran at this exact clean source; 604 raw/LF/Git identities are identical before and after. Assembly remains outside tracked source.',
    'createdUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'basis': 'Existing local product-architecture receipt schema, original three unchanged judges, current-main policies and exact original PR CDP digest.',
    'sourceBaseHead': head, 'headObservedBefore': head, 'headObservedAfter': head,
    'actualAdoptedMain': source['main'], 'executionEnvironment': 'local managed cloud Linux; no GitHub run ID',
    'manifestSha256': sha(manifest_raw.replace(b'\r\n', b'\n')),
    'scannerSha256': sha((ROOT / 'tests/architecture_contract.py').read_bytes().replace(b'\r\n', b'\n')),
    'scanSha256': sha(scan_bytes), 'reportSha256': sha(report_raw), 'inputClosureSha256': closure_sha,
    'counts': counts, 'scanPassed': True, 'actualCliScan': records[0], 'validation': records[1:], 'inputs': inputs,
    'environment': {'pythonExecutable': sys.executable, 'pythonVersion': sys.version,
                    'platform': platform.platform(), 'nodeVersion': subprocess.check_output(['node', '--version']).decode().strip()},
    'uncertainties': ['No true-browser S/V/S or full canvas execution in this phase.',
                      'No full 123 mutation regeneration or required CI terminal state.',
                      'Repository historical derived files remain unchanged and are not relabelled.']}
(artifact / 'product-architecture.json').write_bytes(manifest_raw)
(artifact / 'product-architecture-scan.json').write_bytes(scan_bytes)
(artifact / 'PRODUCT-ARCHITECTURE.md').write_bytes(report_raw)
(artifact / 'product-architecture-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')

mutation_folder = OUT / 'commands/18-mutation-check'
mutation_result = json.loads((mutation_folder / 'RESULT.json').read_text())
mutation_text = (mutation_folder / 'stdout.bin').read_text()
stale = [s for s in mutation_text.splitlines() if s.startswith('  STALE ')]
assert mutation_result['actualProcessReturncode'] == 1 and len(stale) == 53
assert all('bridge source/oracle restoration' in row for row in stale)
assert len([row for row in stale if '裁判已變' in row]) == 52
assert len([row for row in stale if 'M110(原 equivalent):equivalence audit oracle changed;' in row]) == 1
summary = {'sourceHead': head, 'architectureExitCodes': [0, 0, 0], 'architectureCounts': counts,
           'architectureInputsBeforeAfterIdentical': True, 'nodeControls': json.loads((OUT / 'node-controls/SUMMARY.json').read_text()),
           'mutationCheckExit': 1, 'mutationDefined': 123, 'mutationRecords': 123,
           'mutationCounts': {'killed': 62, 'crashed': 1, 'equivalent': 4, 'stale': 53,
                              'retired': 3, 'survived': 0, 'invalid': 0, 'blocked': 0},
           'mutationStaleReasons': {'judgeSourceChanged': 52, 'M110EquivalenceAuditOracleChanged': 1},
           'ledgerAfterCheck': ledger_after, 'ledgerUnchanged': True, 'fullMutationRerun': False,
           'trueBrowserSvs': 'UNRUN', 'fullCanvas': 'UNRUN', 'otherBrowserGates': 'UNRUN',
           'fullNative': 'UNRUN', 'requiredCi': 'UNRUN', 'sharedCacheUsed': False,
           'trackedDerivedFilesRemainMainHistorical': True, 'artifactAssemblyOutsideSource': True,
           'worktreeClean': True, 'pushed': False, 'prBaseEdited': False, 'prBodyEdited': False, 'commented': False}
(OUT / 'FINAL_RESULTS.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'head': head, 'architecture': [0, 0, 0], 'genericTests': 205, 'productTests': 18,
                  'nodeExits': summary['nodeControls']['exits'], 'mutationCheckExit': 1,
                  'mutationStale': 53, 'ledgerUnchanged': True, 'architectureClosureBeforeAfterEqual': True,
                  'worktreeClean': True, 'sharedCacheUsed': False}))
