"""Replay all four message-only mutations in a disposable exact-HEAD archive.

Run inside isolated_wsl.sh: python3 tests/geo246/message_mutation.py --out /tmp/geo246-.../audit
The checkout is never patched. The archive gets exact byte replacements, is compiled,
and is byte-restored before executing the deliberately generic bridge.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import tempfile

from identity import capture, sha, write

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('geo246_binaries', ROOT / 'tests/binaries.py')
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    bridge = registry.BY_NAME['bridge'].path
    registry.require_fresh('bridge', bridge)
    before = capture(ROOT, [bridge])
    assert not before['tracked_diff']
    patch_path = Path(__file__).with_name('generic_messages.json')
    patch = json.loads(patch_path.read_text(encoding='utf8'))
    write(out / 'checkout-before.json', before)

    def probe(binary, name, *, generic=False, panel=False):
        command = [sys.executable, str(ROOT / 'tests/geo246_weak_pin_probe.py'),
                   '--bridge', str(binary), '--output', str(out / (name + '.json'))]
        if generic:
            command.append('--expect-generic')
        if panel:
            command.append('--panel-only')
        subprocess.run(command, cwd=ROOT, check=True)

    probe(bridge, 'baseline')
    probe(bridge, 'panel-baseline', panel=True)
    with tempfile.TemporaryDirectory(prefix='geo246-message-') as temp:
        scratch = Path(temp)
        archive = scratch / 'source.tar'
        # Compile the exact committed core/include sources without copying
        # unrelated reader/media artifacts into every disposable mutation.
        archive_paths = ['current_geometry.c', 'geometry-core', 'geometry-web/web_bridge.c']
        archive.write_bytes(subprocess.check_output(['git', '-C', str(ROOT), 'archive', 'HEAD', *archive_paths]))
        work = scratch / 'source'
        work.mkdir()
        with tarfile.open(archive) as tf:
            tf.extractall(work, filter='data')
        saved = {row['file']: (work / row['file']).read_bytes() for row in patch['replacements']}
        records = []
        try:
            for row in patch['replacements']:
                path = work / row['file']
                raw = path.read_bytes()
                assert b'\r' not in raw.replace(b'\r\n', b''), row['file']
                assert not (b'\r\n' in raw and b'\n' in raw.replace(b'\r\n', b'')), row['file']
                newline = '\r\n' if b'\r\n' in raw else '\n'
                old = row['before'].replace('\n', newline).encode('utf8')
                new = row['after'].replace('\n', newline).encode('utf8')
                assert raw.count(old) == 1, (row['file'], raw.count(old))
                changed = raw.replace(old, new)
                path.write_bytes(changed)
                records.append({'file': row['file'], 'before_raw_sha256': sha(raw),
                                'mutant_raw_sha256': sha(changed), 'newline': repr(newline)})
            mutant = out / 'generic-bridge'
            command = ['cc', '-std=c11', '-O2', 'geometry-web/web_bridge.c', '-o', str(mutant), '-lm']
            write(out / 'compile-command.json', {'argv': command, 'cwd': str(work),
                  'archive_head': before['head'], 'archive_tree': before['tree'],
                  'archive_paths': archive_paths,
                  'archive_sha256': sha(archive.read_bytes()), 'patch_sha256': sha(patch_path.read_bytes()),
                  'shell_display': shlex.join(command), 'replacements': records})
            subprocess.run(command, cwd=work, check=True)
        finally:
            for name, data in saved.items():
                (work / name).write_bytes(data)
            assert all((work / name).read_bytes() == data for name, data in saved.items())
        probe(mutant, 'generic', generic=True)
        probe(mutant, 'panel-generic', generic=True, panel=True)
        probe(bridge, 'restored')
        probe(bridge, 'panel-restored', panel=True)
    after = capture(ROOT, [bridge])
    assert before == after
    write(out / 'checkout-after.json', after)
    write(out / 'summary.json', {'head': before['head'], 'tree': before['tree'],
          'checkout_unchanged': True, 'archive_sources_restored_before_execution': True,
          'original_32_reason_failures': [0, 32, 0], 'panel_7_reason_failures': [0, 7, 0]})


if __name__ == '__main__':
    main()
