#!/usr/bin/env python3
"""Seal package files after byte validation; never rewrite original evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    args = parser.parse_args()
    root = args.package.resolve()
    target = root / 'PACKAGE-SHA256.json'
    if target.exists():
        raise ValueError('Refusing to replace an existing seal')
    verification = json.loads((root / 'VERIFICATION.json').read_bytes())
    if not verification['ok'] or verification['originalFilesByteCompared'] != 536:
        raise ValueError('Original-byte validation must complete before sealing')
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_file():
            if path.is_symlink():
                raise ValueError('Unexpected symlink')
            raw = path.read_bytes()
            files[path.relative_to(root).as_posix()] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    target.write_text(json.dumps({'schema': 'geometry-p1-publication-package/1', 'files': files}, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'sealedFiles': len(files), 'packageManifest': str(target)}))


if __name__ == '__main__':
    main()
