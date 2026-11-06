"""Record and apply only the complete combined handoff patch, deferring manifest regeneration."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path('/tmp/g261-next299316')
work = Path('/workspace/geo299316-work')
patch = work / 'patch.diff'
assert hashlib.sha256(patch.read_bytes()).hexdigest() == '422946025137ba719ef4e42da1a527ba5bc07bbf8e52b28e687392061074fef6'
out = work / 'original-combined-apply'
out.mkdir(exist_ok=False)
exclude = '--exclude=geometry-core/domain-decoupling/product-architecture.json'
for label, options in [('check', ['--check']), ('apply-reject', ['--reject'])]:
    cmd = ['git', 'apply', *options, exclude, str(patch)]
    result = subprocess.run(cmd, cwd=root, capture_output=True)
    (out / (label + '.stdout')).write_bytes(result.stdout)
    (out / (label + '.stderr')).write_bytes(result.stderr)
    (out / (label + '.json')).write_text(json.dumps({
        'command': cmd, 'cwd': str(root), 'exit': result.returncode,
        'base_sha': '4b665fae21ab63aaffb7d84f6a32d5a469ba1675',
        'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
        'manifest': 'Original delta preserved for mechanical recomputation, never overwrite the F2 manifest.',
    }, indent=2) + '\n')
    print(label, result.returncode, result.stderr.decode(errors='replace'))
