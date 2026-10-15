"""Restore the original process sample bytes in memory and verify the lossless text parts."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
metadata = json.loads((root / 'metadata.json').read_text(encoding='utf-8'))
parts = []
for part in metadata['parts']:
    data = (root / part['file']).read_bytes()
    assert len(data) == part['bytes']
    assert hashlib.sha256(data).hexdigest() == part['sha256']
    parts.append(b''.join(data.split()))
compressed = base64.b64decode(b''.join(parts), validate=True)
assert len(compressed) == metadata['compressed_bytes']
assert hashlib.sha256(compressed).hexdigest() == metadata['compressed_sha256']
original = gzip.decompress(compressed)
assert len(original) == metadata['original_bytes']
assert hashlib.sha256(original).hexdigest() == metadata['original_sha256']
samples = json.loads(original)
assert samples['scope'] == metadata['scope']
assert len(samples['samples']) == metadata['sample_count']
assert samples['runner_pid'] == metadata['runner_pid']
assert all(set(s) == {'seconds', 'processes'} for s in samples['samples'])
assert all(set(p) == {'pid', 'ppid', 'comm'} for s in samples['samples'] for p in s['processes'])
assert all(type(p['pid']) is int and type(p['ppid']) is int and isinstance(p['comm'], str)
           for s in samples['samples'] for p in s['processes'])
report = dict(original_sha256=metadata['original_sha256'], original_bytes=len(original),
              original_lines=len(original.splitlines()), parts=len(parts), samples=len(samples['samples']),
              process_observations=sum(len(s['processes']) for s in samples['samples']),
              scope=samples['scope'], lossless=True)
print(json.dumps(report, ensure_ascii=False, indent=2))
