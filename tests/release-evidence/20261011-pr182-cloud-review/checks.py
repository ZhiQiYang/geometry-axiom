import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path.cwd()
OUT = Path('/tmp/geometry-pr182-review/checks')
OUT.mkdir(parents=True, exist_ok=True)
receipt = []
for label, command in (
    ('selection-guard', [sys.executable, 'tests/test_section_profile_mutation_check.py']),
    ('core-ledger-freshness', [sys.executable, 'tests/mutate.py', '--check']),
):
    start = time.monotonic()
    run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / (label + '.log')).write_bytes(run.stdout)
    receipt.append({'label': label, 'command': command, 'exit': run.returncode,
                    'seconds': time.monotonic()-start, 'log_sha256': hashlib.sha256(run.stdout).hexdigest()})

historic = ROOT / 'tests/release-evidence/20261010-q38-i44'
lines = (historic / 'SHA256SUMS.txt').read_text().splitlines()
entries = []
for line in lines:
    digest, name = line.split(' *', 1)
    actual = hashlib.sha256((historic / name).read_bytes()).hexdigest()
    assert digest == actual, name
    entries.append({'path': name, 'sha256': actual})
raw_changes = []
for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'aa4067b3', '--', str(historic.relative_to(ROOT))], text=True).splitlines():
    if name.endswith(('/README.md', '/SHA256SUMS.txt')):
        continue
    old = subprocess.check_output(['git', 'show', 'aa4067b3:' + name])
    if old != (ROOT / name).read_bytes():
        raw_changes.append(name)
assert not raw_changes
data = {'runs': receipt, 'historical_manifest_entries_verified': entries, 'historical_raw_changes': raw_changes}
(OUT / 'receipt.json').write_text(json.dumps(data, indent=2))
print(json.dumps({'runs': receipt, 'historical_manifest_count': len(entries), 'historical_raw_changes': raw_changes}))
assert all(r['exit'] == 0 for r in receipt)
