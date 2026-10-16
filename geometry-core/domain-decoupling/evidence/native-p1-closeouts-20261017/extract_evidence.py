#!/usr/bin/env python3
"""Recover exact retained bytes, without overwriting files or executing evidence."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--path', action='append', help='Original relative catalog path; repeat, or omit for all')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.package.resolve(), args.out.resolve()
    if output == root or output.is_relative_to(root):
        raise ValueError('Extraction must be outside the sealed package')
    catalog = json.loads((root / 'CONTENT-MANIFEST.json').read_bytes())
    names = args.path if args.path is not None else list(catalog['files'])
    targets = {}
    for name in names:
        path = PurePosixPath(name)
        if name not in catalog['files'] or path.is_absolute() or '..' in path.parts:
            raise ValueError('Unknown or unsafe catalog path: ' + name)
        target = output.joinpath(*path.parts)
        if not target.resolve().is_relative_to(output) or target.exists():
            raise ValueError('Refusing to overwrite or escape output: ' + name)
        targets[name] = target
    archive_info = catalog['archive']
    archive_path = root / archive_info['file']
    archive_raw = archive_path.read_bytes()
    if len(archive_raw) != archive_info['bytes'] or hashlib.sha256(archive_raw).hexdigest() != archive_info['sha256']:
        raise ValueError('Archive fingerprint mismatch')
    needed = {catalog['files'][name]['archiveEntry'] for name in names}
    found = {}
    with tarfile.open(archive_path, 'r:xz') as archive:
        for member in archive:
            if member.name in needed:
                if not member.isfile() or member.name in found:
                    raise ValueError('Invalid/duplicate member')
                found[member.name] = archive.extractfile(member).read()
    for name in names:
        record = catalog['files'][name]
        raw = found[record['archiveEntry']]
        if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('Retained bytes mismatch: ' + name)
    for name, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(found[catalog['files'][name]['archiveEntry']])
    print(json.dumps({'filesExtracted': len(targets), 'originalBytesPreserved': True}))


if __name__ == '__main__':
    main()
