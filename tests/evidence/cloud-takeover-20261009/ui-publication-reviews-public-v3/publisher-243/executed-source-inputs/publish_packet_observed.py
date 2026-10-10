"""Record a scratch publisher execution; never runs product tests."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NAME = sys.argv[1]
TARGET = HERE / NAME
GATE = HERE / (NAME + '-publisher-execution')
assert not TARGET.exists() and not GATE.exists()
GATE.mkdir()
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
source_names = ['publish_packet_observed.py', 'prepare_ui_history_packet_v5.py', 'prepare_resume_packet.py', 'prepare_cdp_diagnosis.py', 'configure_243_packet.py',
                'ui-243-config.json', 'ui-243-extra-evidence.json', 'ui-243-metadata.json', 'ui-243-README.md']
source_before = {name: sha(HERE / name) for name in source_names}
command = [sys.executable, str(HERE / 'prepare_ui_history_packet_v5.py'), '--output', str(TARGET), '--only-extra',
           '--extra-config', str(HERE / 'ui-243-config.json'), '--extra-evidence', str(HERE / 'ui-243-extra-evidence.json'),
           '--readme', str(HERE / 'ui-243-README.md'), '--metadata', str(HERE / 'ui-243-metadata.json')]
started = now()
with (GATE / 'command.log').open('wb') as raw:
    process = subprocess.Popen(command, cwd=HERE, stdout=raw, stderr=subprocess.STDOUT)
    proc = Path('/proc') / str(process.pid)
    actual_exe = (proc / 'exe').resolve()
    actual = {'pid': process.pid, 'executablePath': str(actual_exe), 'executableSha256': sha(actual_exe),
              'commandLine': (proc / 'cmdline').read_bytes().decode().replace('\0', ' '),
              'procStat': (proc / 'stat').read_text()}
    exit_code = process.wait()
source_after = {name: sha(HERE / name) for name in source_names}
receipt = {'schema': 'geometry-scratch-publication-execution/1', 'actor': '/root/delivery_closeout', 'startedUtc': started, 'finishedUtc': now(),
           'command': command, 'actualPublisherPython': actual, 'sourceBefore': source_before, 'sourceAfter': source_after,
           'sourceUnchanged': source_before == source_after, 'exitCode': exit_code, 'completed': exit_code == 0,
           'rawLog': {'path': str(GATE / 'command.log'), 'bytes': (GATE / 'command.log').stat().st_size, 'sha256': sha(GATE / 'command.log')},
           'productTestExecuted': False, 'repositoryOrRemoteWrites': False, 'sourceCopiesWereExecutedByPublisherOnly': True,
           'note': 'This identity and exit belong to evidence publication, never to a product/browser test.'}
if (TARGET / 'manifest.json').exists():
    receipt['manifest'] = {'path': str(TARGET / 'manifest.json'), 'sha256': sha(TARGET / 'manifest.json')}
(GATE / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'exitCode': exit_code, 'completed': receipt['completed'], 'receipt': str(GATE / 'receipt.json'), 'rawLog': str(GATE / 'command.log'), 'manifest': receipt.get('manifest')}))
sys.exit(exit_code)
