#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/tmp/geometry-pr345-20261102')
OUT = Path(__file__).resolve().parent
identity = json.loads((OUT / 'TOOLS_MERGE_IDENTITY.json').read_text())
ledger = ROOT / 'tests/mutants_results.json'
before = identity['ledgerBeforeCheck']
raw = ledger.read_bytes()
after = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
         'mtimeNs': ledger.stat().st_mtime_ns}
assert all(after[k] == before[k] for k in after)
status = subprocess.run(['git', 'status', '--porcelain=v1', '--untracked-files=all'],
                        cwd=ROOT, capture_output=True, check=False)
assert status.returncode == 0 and status.stdout == b'' and status.stderr == b''
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == identity['head']
check = json.loads((OUT / 'commands/16-mutation-check/RESULT.json').read_text())
stdout = (OUT / 'commands/16-mutation-check/stdout.bin').read_bytes()
assert check['actualProcessReturncode'] == 1
assert hashlib.sha256(stdout).hexdigest() == check['streams']['stdout.bin']['sha256']
text = stdout.decode()
stale = [s for s in text.splitlines() if s.startswith('  STALE ')]
assert len(stale) == 53
assert all('bridge source/oracle restoration' in s for s in stale)
judge_changed = [s for s in stale if '裁判已變' in s]
equivalence_changed = [s for s in stale if 'M110(原 equivalent):equivalence audit oracle changed;' in s]
assert len(judge_changed) == 52 and len(equivalence_changed) == 1
assert '過期 stale 53' in text
result = {'head': head, 'ledgerAfterCheck': after, 'ledgerBytesAndMtimeUnchanged': True,
          'statusCommand': ['git', 'status', '--porcelain=v1', '--untracked-files=all'],
          'statusExit': status.returncode, 'statusStdout': status.stdout.decode(),
          'mutationCheckExecutionHead': head, 'mutationCheckExit': 1,
          'mutationCheckSeconds': check['elapsedSeconds'], 'defined': 123, 'records': 123,
          'killed': 62, 'crashed': 1, 'survived': 0, 'equivalent': 4,
          'invalid': 0, 'stale': 53, 'blocked': 0, 'retired': 3,
          'staleCause': 'bridge source/oracle restoration: original judge source changed',
          'staleReasons': {'judgeSourceChanged': 52, 'M110EquivalenceAuditOracleChanged': 1},
          'newFull123MutationExecution': False, 'freshLedgerGeneratedOrAdopted': False,
          'newRequiredCiCompleted': False, 'selected19Rerun': False,
          'selected19ActualExecutionHead': identity['previousCandidateAndSelectedExecution'],
          'noLedgerExpectedOrFingerprintEdits': True}
(OUT / 'TOOLS_MERGE_AFTER.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result))
