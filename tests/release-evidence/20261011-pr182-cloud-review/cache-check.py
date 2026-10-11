import json
import os
from pathlib import Path
import subprocess
import sys
import time
import hashlib

out = Path('/tmp/geometry-pr182-review/checks')
cache = Path('/tmp/geometry-pr182-review/core-cache-absent')
assert not cache.exists(), 'keep this check reproducible with an absent cache, as on a clean checkout'
command = [sys.executable, 'tests/mutate.py', '--check']
start = time.monotonic()
run = subprocess.run(command, env=dict(os.environ, MUTATE_CACHE=str(cache)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(out / 'core-ledger-absent-cache.log').write_bytes(run.stdout)
receipt = json.loads((out / 'receipt.json').read_text())
receipt['runs'].append({'label': 'core-ledger-absent-cache', 'command': command, 'exit': run.returncode,
                        'env': {'MUTATE_CACHE': str(cache)}, 'seconds': time.monotonic()-start,
                        'log_sha256': hashlib.sha256(run.stdout).hexdigest(), 'cache_exists_after': cache.exists()})
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2))
print(run.stdout.decode())
assert run.returncode == 0 and not cache.exists()
