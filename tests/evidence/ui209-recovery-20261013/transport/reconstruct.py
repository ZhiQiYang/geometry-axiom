#!/usr/bin/env python3
"""Rebuild the immutable 52c34a6 archive and verify all members; execute no payload.

Usage: python3 transport/reconstruct.py /tmp/ui209-52c34a6.raw.tar.xz
The output must not already exist. All inputs are local ASCII/JSON files.
"""
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

SOURCE = '52c34a6d6faef1d3cdaf52d52b6f8edb66eda012'
ARCHIVE_SHA = '89a7ea908a7fb3d0957d1103d45f00b11c5de55d2a305b589b5a5bfcf7d6f5ba'
HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    require(len(sys.argv) == 2, 'Specify a new output archive path')
    index = json.loads((HERE/'index.json').read_text())
    require(index['source_commit'] == SOURCE, 'Source commit changed')
    require(index['archive']['sha256'] == ARCHIVE_SHA, 'Original archive identity changed')
    require(len(index['parts']) == index['part_count'] == 80, 'Part count differs')
    require({p.name for p in HERE.glob('part-*.b64.txt')} == {p['file'] for p in index['parts']}, 'Missing/extra transport parts')
    pieces, offset = [], 0
    for sequence, part in enumerate(index['parts'], 1):
        require(part['sequence'] == sequence and part['file'] == f'part-{sequence:03d}.b64.txt', 'Part order/name differs')
        data = (HERE/part['file']).read_bytes()
        require(len(data) == part['file_bytes'] and digest(data) == part['file_sha256'], f'ASCII checksum: {part["file"]}')
        require(data.endswith(b'\n') and b'\n' not in data[:-1], 'Expected one base64 line plus LF')
        encoded = data[:-1]
        require(part['base64_start'] == offset and part['base64_end'] == offset + len(encoded), 'Noncontiguous base64 offsets')
        require(len(encoded) == (48000 if sequence < 80 else 28368), 'Unexpected part length')
        decoded = base64.b64decode(encoded, validate=True)
        require(len(decoded) == part['decoded_bytes'] and digest(decoded) == part['decoded_sha256'], 'Decoded part checksum differs')
        pieces.append(decoded)
        offset += len(encoded)
    require(offset == index['base64_characters'] == 3820368, 'Total base64 length differs')
    archive = b''.join(pieces)
    require(len(archive) == index['archive']['bytes'] == 2865276 and digest(archive) == ARCHIVE_SHA, 'Archive bytes/checksum differ')
    manifest_bytes = (HERE.parent/'manifest.json').read_bytes()
    require(digest(manifest_bytes) == index['member_manifest']['sha256'] and len(manifest_bytes) == index['member_manifest']['bytes'], 'Original member manifest differs')
    manifest = json.loads(manifest_bytes)
    require(len(manifest) == index['member_manifest']['members'] == 328, 'Manifest member count differs')
    binaries = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:xz') as tar:
        members = tar.getmembers()
        names = [m.name for m in members]
        require(len(names) == len(set(names)) and set(names) == set(manifest), 'Duplicate/missing/extra archive member')
        for member in members:
            require(member.isfile(), 'Expected a regular file: '+member.name)
            data = tar.extractfile(member).read()
            expected = manifest[member.name]
            require(len(data) == expected['bytes'] and digest(data) == expected['sha256'], 'Member checksum differs: '+member.name)
            if member.name.startswith('binaries/'):
                require(digest(data) == Path(member.name).name, 'Archived binary differs from its declared digest')
                binaries.append({'member':member.name, 'bytes':len(data), 'sha256':digest(data)})
    with Path(sys.argv[1]).open('xb') as output:
        output.write(archive)
    print(json.dumps({'kind':'transport-and-file-integrity-only', 'source_commit':SOURCE,
        'archive_bytes':len(archive), 'archive_sha256':ARCHIVE_SHA, 'parts_verified':len(pieces),
        'members_verified':len(manifest), 'archived_binaries_verified':binaries,
        'payloads_executed':False, 'output':sys.argv[1]}, indent=2))


if __name__ == '__main__':
    main()
