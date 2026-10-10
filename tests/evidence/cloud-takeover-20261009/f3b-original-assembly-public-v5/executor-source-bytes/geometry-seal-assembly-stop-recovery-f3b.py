from pathlib import Path
import datetime, hashlib, json, subprocess, sys

root = Path('<workspace-path>')
gate = Path('<workspace-path>')
control = Path('<workspace-path>')
stop = Path('<workspace-path>')
out = Path('<workspace-path>')
assert not out.exists()
receipt = json.loads((gate / 'receipt.json').read_text())
error = json.loads((control / 'controller-error.json').read_text())
recovery = json.loads((stop / 'terminal-receipt.json').read_text())
assert receipt['gateExitCode'] == 0 and receipt['executionVerified'] is True
assert receipt['evidence']['canonicalResult']['scope']['filters'] == ['GEOMETRY_ASSEMBLY_ONLY']
assert receipt['evidence']['canonicalResult']['passedAssertions'] == 150
assert error['actualGateExitCode'] == 0 and error['stopExitCode'] == 1
assert '9eb670110379ec0d726914f3e5b2d8e7237f2b9c' in (control / 'stop-controller.stderr.raw.log').read_text()
assert recovery['exitCode'] == 0 and recovery['portObservation']['accepting'] is False
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True)
assert head == 'f3b8285729b42cd22451c98cba1e2ec4514517f3' and dirty == ''
paths = [gate / 'receipt.json', gate / 'command.log', control / 'controller-error.json',
         control / 'gate.stdout.raw.log', control / 'gate.stderr.raw.log',
         control / 'stop-controller.stdout.raw.log', control / 'stop-controller.stderr.raw.log',
         stop / 'terminal-receipt.json']
record = {'schema': 'geometry-root-assembly-stop-recovery-observation/1',
          'observedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'root': str(root), 'fullSHA': head, 'dirtyObserved': dirty,
          'productGateActualExitCode': 0, 'productCanonicalScope': receipt['evidence']['canonicalResult']['scope'],
          'productCompleted': True, 'productPassedAssertions': 150, 'productFailedAssertions': 0,
          'originalLifecycleActualExitCode': 1, 'originalLifecycleExitSource': 'ROOT received terminal unified exec session 70298: exit_code 1, original AssertionError retained in stop-controller.stderr.raw.log and controller-error.json',
          'originalLifecycleCommand': ['python', '<workspace-path>', 'assembly', 'geometry-root-f3b82857-original-assembly'],
          'originalServiceActualExitCode': None, 'originalServiceExitStatus': 'unknown; original parent exited after stale stop guard before service wait',
          'recoveryStopActualExitCode': 0, 'recoveryStopTerminalReceipt': str(stop / 'terminal-receipt.json'),
          'productTestsRepeatedForStopRepair': False, 'historicalFilesModified': False,
          'note': 'Product Node/gate exit 0 and complete partial are distinct from lifecycle exit 1. Later exact owned-service stop restores terminal port state; it does not replace the original lifecycle error or unknown server exit.',
          'command': sys.argv, 'scriptSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'actualPython': str(Path('/proc/self/exe').resolve()),
          'actualPythonSHA256': hashlib.sha256(Path('/proc/self/exe').read_bytes()).hexdigest(),
          'files': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
out.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'observation': str(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest()}))
