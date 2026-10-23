#!/usr/bin/env python3
"""Second immutable targeted batch; no claim of whole-suite acceptance."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUNNERS = Path(__file__).resolve().parent
OUT = RUNNERS.parent
stages = [
    ('native-corrected-db65132a', [str(RUNNERS / 'run-native-receipt.py'), str(RUNNERS / 'native-corrected-db65132a.json')]),
    ('legacy-corrected-db65132a', [str(RUNNERS / 'run-legacy-receipt.py'), str(RUNNERS / 'legacy-corrected-db65132a.json')]),
    ('rename-73aca666', [str(RUNNERS / 'run-rename-native-v3.py')]),
    ('region-a88d3c57', [str(RUNNERS / 'run-region-edges-v2.py')]),
]
frozen = ['run-next-stages.py', 'next-targeted-namespace.sh', 'run-native-receipt.py',
          'exercise-native-receipt.py', 'native-receipt-namespace.sh', 'native-corrected-db65132a.json',
          'run-legacy-receipt.py', 'legacy-receipt-namespace.sh', 'exercise-legacy-receipt.py', 'legacy-corrected-db65132a.json',
          'run-rename-native-v3.py', 'run-region-edges-v2.py', 'exercise-region-edges.py']
def hashes():
    return {name: hashlib.sha256((RUNNERS / name).read_bytes()).hexdigest() for name in frozen}

receipt = OUT / 'next-batch-v1-stage-results.json'
if receipt.exists():
    raise SystemExit('Preserve the old batch receipt; choose a new run')
before = hashes()
(OUT / 'next-batch-v1-runner-before.json').write_text(json.dumps(before, indent=2) + '\n', encoding='utf-8')
rows = []
for name, arguments in stages:
    log = OUT / (name + '-next-batch-v1-console.log')
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log.open('xb') as output:
        run = subprocess.Popen(['python3', '-u', *arguments], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, pass_fds=(7,))
        for line in iter(run.stdout.readline, b''):
            output.write(line)
            output.flush()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        code = run.wait()
    rows.append({'name': name, 'arguments': arguments, 'started_utc': start,
                 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'exit': code, 'console_log': str(log), 'console_sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
    receipt.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
after = hashes()
(OUT / 'next-batch-v1-runner-after.json').write_text(json.dumps(after, indent=2) + '\n', encoding='utf-8')
sys.exit(0 if all(row['exit'] == 0 for row in rows) and before == after else 1)
