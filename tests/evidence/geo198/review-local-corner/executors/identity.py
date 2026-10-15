"""Capture exact checkout/tree and binary identities without conflating newlines."""
from pathlib import Path
import hashlib
import json
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def capture(root, binary_paths=()):
    root = Path(root).resolve(strict=True)
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    tree = git(root, 'rev-parse', 'HEAD^{tree}').decode().strip()
    tracked_diff = git(root, 'diff', '--name-only', 'HEAD').decode().splitlines()
    source_names = ['current_geometry.c', 'geometry-core/grid_systems.inc',
                    'geometry-core/grid_bindings.inc', 'geometry-core/subgrid_commands.inc',
                    'tests/test_grid_system_contract.py', 'tests/test_infinite_grid_contract.py',
                    'tests/test_subgrid_contract.py', 'tests/run_all.py', '公理層.md',
                    'geometry-guide/公理層-閱讀器.html']
    sources = {}
    for relative in ['tests/geo246_weak_pin_probe.py', 'tests/geo246/identity.py',
                     'tests/geo246/message_mutation.py', 'tests/geo246/generic_messages.json',
                     'tests/geo246/isolated_wsl.sh', 'tests/geo246/refresh_mutants.py',
                     'tests/geo246/ci_job.py', 'tests/geo246/parent_reader.py',
                     '.github/workflows/integration-tests.yml']:
        if (root / relative).is_file():
            source_names.append(relative)
    for name in source_names:
        disk = (root / name).read_bytes()
        committed = git(root, 'show', head + ':' + name)
        sources[name] = {
            'raw_sha256': sha(disk), 'git_blob_sha256': sha(committed),
            'lf_normalized_sha256': sha(disk.replace(b'\r\n', b'\n')),
            'git_lf_normalized_sha256': sha(committed.replace(b'\r\n', b'\n')),
            'normalized_equal': disk.replace(b'\r\n', b'\n') == committed.replace(b'\r\n', b'\n'),
            'crlf': disk.count(b'\r\n'), 'bare_lf': disk.count(b'\n') - disk.count(b'\r\n'),
        }
    binaries = {}
    for binary in binary_paths:
        path = Path(binary).resolve(strict=True)
        sidecar = Path(str(path) + '.fingerprint.json')
        binaries[str(path)] = {'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
                               'sidecar': json.loads(sidecar.read_text()) if sidecar.exists() else None}
    return {'head': head, 'tree': tree, 'checkout': str(root),
            'tracked_diff': tracked_diff,
            'status': git(root, 'status', '--porcelain', '--untracked-files=all').decode().splitlines(),
            'sources': sources, 'binaries': binaries,
            'identity_executor': {'path': str(Path(__file__).resolve()),
                                  'sha256': sha(Path(__file__).read_bytes())},
            'newline_policy': 'Raw byte hashes and Git blob hashes are separate; only CRLF-to-LF normalized hashes establish text identity.'}


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
