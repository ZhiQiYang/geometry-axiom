#!/usr/bin/env python3
"""Freeze all portable package files after successful package verification."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('package', type=Path)
args = parser.parse_args()
package = args.package.resolve()
target = package / 'PACKAGE-SHA256.json'
if target.exists():
    raise RuntimeError('Preserve existing package checksum manifest')
report = json.loads((package / 'VERIFICATION.json').read_bytes())
if report.get('exit') != 0 or report.get('errors'):
    raise RuntimeError('Package verification must succeed before freezing')
shutil.copyfile(Path(__file__), package / Path(__file__).name)
files = {str(path.relative_to(package)).replace('\\', '/'): {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
         for path in sorted(package.rglob('*')) if path.is_file()}
target.write_text(json.dumps({'schema': 'geometry-p1-package-files/1', 'files': files}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files.values()),
                  'manifestSha256': hashlib.sha256(target.read_bytes()).hexdigest()}))
