#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/tmp/geometry-pr344-20261102')
out = Path(__file__).resolve().parent / 'merge-conflicts'
out.mkdir(exist_ok=False)
paths = ['geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md',
         'geometry-core/domain-decoupling/product-architecture-receipt.json']
records = []
for path in paths:
    for stage in range(1, 4):
        argv = ['git', 'show', f':{stage}:{path}']
        p = subprocess.run(argv, cwd=root, capture_output=True, check=False)
        assert p.returncode == 0
        name = Path(path).name + f'.stage-{stage}'
        (out / name).write_bytes(p.stdout)
        records.append({'argv': argv, 'exit': p.returncode, 'file': name,
                        'bytes': len(p.stdout), 'sha256': hashlib.sha256(p.stdout).hexdigest()})
(out / 'INDEX.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps({'conflicts': paths, 'stageRecords': len(records)}))
