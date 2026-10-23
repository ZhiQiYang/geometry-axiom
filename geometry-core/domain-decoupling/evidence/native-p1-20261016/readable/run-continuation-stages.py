#!/usr/bin/env python3
"""Independent fixed-source stages under the inherited shared lock."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT = Path('/mnt/d/geometry-axiom-work/geo261-evidence/p1')
stages = ('run-native-geometry.py', 'run-rename-native-v2.py', 'run-region-edges.py', 'run-native-grid49.py',
          'run-native-parameters.py', 'run-parameters-legacy.py', 'run-native-annotation.py', 'run-native-datums-c28.py',
          'run-rectangular-template.py')
receipt = OUT / 'continuation-stage-results.json'
if receipt.exists():
    raise SystemExit('Preserve the completed receipt; select a fresh run')
def runner_manifest():
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(OUT.iterdir()) if path.is_file() and path.suffix in ('.py', '.sh')}

runner_before = runner_manifest()
(OUT / 'continuation-runner-before.json').write_text(json.dumps(runner_before, indent=2) + '\n', encoding='utf-8')
rows = []
for name in stages:
    script = OUT / name
    script_before = hashlib.sha256(script.read_bytes()).hexdigest()
    log = OUT / (script.stem + '-continuation-console.log')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log.open('xb') as output:
        run = subprocess.Popen(['python3', '-u', str(script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               pass_fds=(7,))
        for line in iter(run.stdout.readline, b''):
            output.write(line)
            output.flush()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        code = run.wait()
    script_after = hashlib.sha256(script.read_bytes()).hexdigest()
    rows.append({'script': str(script), 'script_sha256_before': script_before, 'script_sha256_after': script_after,
                 'script_unchanged': script_before == script_after,
                 'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'exit': code, 'console_log': str(log), 'console_log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
    receipt.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
runner_after = runner_manifest()
(OUT / 'continuation-runner-after.json').write_text(json.dumps(runner_after, indent=2) + '\n', encoding='utf-8')
sys.exit(0 if all(row['exit'] == 0 and row['script_unchanged'] for row in rows) and runner_before == runner_after else 1)
