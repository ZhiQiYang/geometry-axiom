#!/usr/bin/env python3
"""Recover named original raw files, verifying their exact recorded bytes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('--path', action='append', default=[])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    catalog = json.loads((package / 'CONTENT-MANIFEST.json').read_bytes())
    selected = args.path or list(catalog['files'])
    if len(selected) != len(set(selected)) or set(selected) - set(catalog['files']):
        raise RuntimeError('Duplicate or unknown evidence path')
    destination = args.out.resolve()
    targets = {}
    for name in selected:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise RuntimeError('Unsafe evidence path')
        target = (destination / Path(*path.parts)).resolve()
        if not target.is_relative_to(destination) or target.exists():
            raise RuntimeError('Preserve existing file or unsafe target: ' + name)
        targets[name] = target
    archive_path = package / catalog['archive']['file']
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != catalog['archive']['sha256']:
        raise RuntimeError('Archive identity differs')
    with tarfile.open(archive_path, 'r:xz') as archive:
        for name, target in targets.items():
            record = catalog['files'][name]
            raw = archive.extractfile(record['archiveEntry']).read()
            if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
                raise RuntimeError('Evidence identity differs: ' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(raw)
    print(json.dumps({'filesExtracted': len(targets), 'destination': str(destination)}))


if __name__ == '__main__':
    main()
