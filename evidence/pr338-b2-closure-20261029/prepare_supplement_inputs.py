"""Materialize only the three fixed original JSON inputs needed by audit_bindings.py."""
import hashlib
import json
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent
report = json.loads((root / 'B2_CLOSURE.json').read_text())
perf = next(value for name, value in report['r8']['invocation_manifests'].items() if '064908' in name)
requests = [
    (perf, 'selected/r8-perf-commands.json'),
    (report['f9']['invocation_manifest'], 'selected/comparison/invocation/commands/commands.json'),
    (report['f9']['equivalence'], 'selected/comparison/evidence/equivalence.json'),
]
for binding, target in requests:
    with tarfile.open(root / binding['archive'], 'r:gz') as archive:
        member = archive.getmember(binding['member'])
        assert member.isfile(), binding['member']
        raw = archive.extractfile(member).read()
    assert hashlib.sha256(raw).hexdigest() == binding['sha256']
    path = root / target
    if path.exists():
        assert path.read_bytes() == raw, 'Existing original input differs: ' + target
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    print(target, len(raw), binding['sha256'])
