#!/usr/bin/env python3
"""Record the existing canonical reader generator; this is not an acceptance gate."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

repo = Path('/tmp/g261-next314')
out = Path('/workspace/geo314-owner-20261023/reader-sync-source')
out.mkdir(exist_ok=False)
command = ['python3', '-B', 'geometry-guide/sync_axiom_reader.py']
inputs = ['tests/mutate.py', 'tests/mutation_bridge.py', 'tests/test_geo261_mutation_migration.py',
          'geometry-templates/woodworking/native/grid_application.c',
          'tests/test_geo314_stagger_commit.py', '公理層.md', '決策佇列.md']
receipt = {
    'purpose': 'mechanical canonical reader generation; no acceptance tests executed',
    'command': command, 'cwd': str(repo),
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
    'worktreeIsCommitted': False,
    'inputSha256': {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in inputs},
    'environment': {'platform': platform.platform(), 'python': sys.version, 'PATH': os.environ.get('PATH')},
    'startedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
with (out / 'stdout.txt').open('wb') as stdout, (out / 'stderr.txt').open('wb') as stderr:
    result = subprocess.run(command, cwd=repo, stdout=stdout, stderr=stderr)
receipt['exitCode'] = result.returncode
receipt['endedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
for name in ['stdout.txt', 'stderr.txt']:
    receipt[name + 'Sha256'] = hashlib.sha256((out / name).read_bytes()).hexdigest()
receipt['canonicalSha256'] = hashlib.sha256((repo / 'geometry-guide/公理層-閱讀器.html').read_bytes()).hexdigest()
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'exitCode': result.returncode, 'receipt': str(out / 'receipt.json')}, ensure_ascii=False))
sys.exit(result.returncode)
