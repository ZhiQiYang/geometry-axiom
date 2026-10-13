"""Capture actual fresh scratch builder execution, its sources and raw streams."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
builder = HERE / 'prepare_f3b_durable_space_packet_v2.py'
stdout = HERE / 'f3b-durable-space-builder-v2.stdout.raw.log'
stderr = HERE / 'f3b-durable-space-builder-v2.stderr.raw.log'
receipt = HERE / 'f3b-durable-space-builder-execution-v2.json'
assert not any(p.exists() for p in (stdout, stderr, receipt))
saved = HERE / 'ui-retained-source-snapshots/f3b8285729b42cd22451c98cba1e2ec4514517f3'
saved_before = {str(p): {'sha256': sha(p), 'mtimeNs': p.stat().st_mtime_ns} for p in sorted(saved.rglob('*')) if p.is_file()}
python = Path('/proc/self/exe').resolve()
command = [str(python), '-B', str(builder)]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with stdout.open('xb') as out, stderr.open('xb') as err:
    result = subprocess.run(command, stdout=out, stderr=err)
saved_after = {str(p): {'sha256': sha(p), 'mtimeNs': p.stat().st_mtime_ns} for p in sorted(saved.rglob('*')) if p.is_file()}
sources = [Path(__file__), builder, HERE / 'prepare_ui_history_packet_v8.py',
           HERE / 'prepare_resume_packet.py', HERE / 'prepare_cdp_diagnosis.py']
record = {'schema': 'geometry-f3b-durable-space-builder-actual-execution/1',
          'startedUTC': started, 'finishedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'actualCommand': command, 'outerExecutorCommand': sys.orig_argv,
          'actualExitCode': result.returncode, 'actualPython': str(python), 'actualPythonSHA256': sha(python),
          'actualUID': os.getuid(), 'executorSources': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sources],
          'rawStreams': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in (stdout, stderr)],
          'savedSourceSnapshotsBefore': saved_before, 'savedSourceSnapshotsAfter': saved_after,
          'savedSourceSnapshotBytesAndMtimesUnchanged': saved_before == saved_after,
          'productExecuted': False, 'validatorExecuted': False, 'browserOrServiceUsed': False,
          'repositoryWritten': False, 'independentQA': False}
if result.returncode == 0:
    summary = json.loads(stdout.read_text().splitlines()[-1])
    record['builderSummary'] = summary
    record['manifestSHA256'] = sha(Path(summary['output']) / 'manifest.json')
    record['innerBuildReceiptSHA256'] = sha(summary['buildReceipt'])
    record['packagerSelfcheckSHA256'] = sha(summary['selfcheck'])
receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'actualBuilderExitCode': result.returncode, 'executionReceipt': str(receipt),
                  'executionReceiptSHA256': sha(receipt), 'savedSnapshotsUnchanged': saved_before == saved_after,
                  'builderStdout': stdout.read_text(), 'builderStderr': stderr.read_text()}))
sys.exit(result.returncode)
