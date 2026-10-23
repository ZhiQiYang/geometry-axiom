"""Archive the terminal native-rAF diagnostic without changing its verdict."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path('/tmp/g288p88r')
HERE = Path(__file__).resolve().parent
F = '3d681636902371ecc528b20f51eea33e272581c9'
OUT = HERE / 'native-raf-diagnostic-archive'


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def h(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    launch_path = HERE / 'native-raf-controlled-v2-launch.exit.json'
    launch = json.loads(launch_path.read_text())
    need(launch['sha'] == F and 'launcher_exit_code' in launch, 'Launcher terminal identity required')
    need(launch.get('heavy_process_started') is True and launch.get('actual_process_returncode') is not None,
         'This archive requires an actual completed diagnostic child; archive prelaunch guard failures separately')
    for stream in ('stdout', 'stderr'):
        need(h((HERE / ('native-raf-controlled-v2-launch.' + stream)).read_bytes()) == launch[stream + '_sha256'],
             'Launcher terminal stream hash differs: ' + stream)
    receipt = json.loads((ROOT / 'receipt.json').read_text())
    need(receipt['sha'] == F and receipt.get('actual_driver_exit_code') is not None,
         'Diagnostic driver terminal identity required')
    need(not OUT.exists(), 'Archive output must be fresh')
    OUT.mkdir()
    manifest = {'schema': 'geo288-p88-native-raf-raw-archive/1', 'source': str(ROOT), 'sha': F,
        'original_driver_exit': receipt['actual_driver_exit_code'], 'original_proof_passed': receipt['passed'],
        'launcher_exit': launch['launcher_exit_code'], 'actual_outer_process_exit': launch['actual_process_returncode'],
        'exclusions': 'Only each phase/tmp tree (compiled executables, Chrome profile/cache and runtime scratch) is excluded. Every remaining original receipt, command, complete stdout/stderr, trace, source variant and frozen tool snapshot is retained. Existing failed prior experiment is preserved separately.',
        'files': {}}
    files = []
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if len(relative.parts) >= 2 and relative.parts[0] in ('fixed', 'withdrawn', 'restored') and relative.parts[1] == 'tmp':
            continue
        if path.is_file():
            files.append((path, Path('raw') / relative))
    folder = HERE / 'outers/p88-native-raf-controlled-v2'
    need(folder.is_dir(), 'Original outer receipt folder required')
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            files.append((path, Path('outer') / path.relative_to(folder)))
    for path in sorted(HERE.glob('native-raf-controlled-v2-launch.*')):
        files.append((path, Path('context') / path.name))
    for path in (HERE / 'continue_native_raf_after_final_canvas.py', Path(__file__)):
        files.append((path, Path('context') / path.name))
    archive = OUT / 'NATIVE_RAF_RAW.tar.gz'
    with tarfile.open(archive, 'w:gz', compresslevel=1) as tar:
        for path, relative in files:
            need(path.is_file() and not path.is_symlink(), 'Only regular files are allowed: ' + str(path))
            need(str(relative) not in manifest['files'], 'Duplicate archive path: ' + str(relative))
            data = path.read_bytes()
            manifest['files'][str(relative)] = {'bytes': len(data), 'sha256': h(data), 'source': str(path)}
            tar.add(path, arcname=str(relative), recursive=False)
    manifest['archive'] = {'path': str(archive), 'bytes': archive.stat().st_size, 'sha256': h(archive.read_bytes())}
    save(OUT / 'MANIFEST.json', manifest)
    with tarfile.open(archive, 'r:gz') as tar:
        members = [member for member in tar if member.isfile()]
        need(len(members) == len(manifest['files']) and {m.name for m in members} == set(manifest['files']),
             'Archived file set differs')
        for member in members:
            data = tar.extractfile(member).read()
            pin = manifest['files'][member.name]
            need(len(data) == pin['bytes'] and h(data) == pin['sha256'], 'Roundtrip bytes/hash differ: ' + member.name)
    save(OUT / 'ROUNDTRIP.json', {'all_archived_files_roundtrip_bytes_and_hashes_match': True,
        'file_count': len(files), 'archive_sha256': manifest['archive']['sha256']})
    print(json.dumps({'archive': manifest['archive'], 'file_count': len(files)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
