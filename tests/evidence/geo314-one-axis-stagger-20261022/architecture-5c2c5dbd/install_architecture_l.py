"""Install completed Linux #314 architecture artifacts and verified raw evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo, out, source = Path('/tmp/g261-next314'), args.out.resolve(), args.source
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo).decode().strip() == source
    assert not subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=all'], cwd=repo)
    result = json.loads((out / 'refresh/RESULT.json').read_text())
    outer = json.loads((out / 'receipt.json').read_text())
    assert result['source_sha'] == outer['source_sha'] == source
    assert result['passed'] and result['scan_exit_code'] == 0 and result['validation_exit_codes'] == [0, 0]
    assert outer['actual_process_returncode'] == outer['exit_code'] == 0 and outer['passed']
    assert result['allRawAndLfInputsUnchanged'] and result['manifest_byte_unchanged']
    names = ('product-architecture.json', 'product-architecture-scan.json', 'PRODUCT-ARCHITECTURE.md', 'product-architecture-receipt.json')
    new = out / 'refresh/new'
    receipt = json.loads((new / names[3]).read_text())
    assert receipt['sourceBaseHead'] == receipt['headObservedBefore'] == receipt['headObservedAfter'] == source
    assert receipt['scanPassed'] and receipt['counts']['diagnostics'] == 0
    dest = repo / 'tests/evidence/geo314-one-axis-stagger-20261022' / ('architecture-' + source[:8])
    assert not dest.exists()
    dest.mkdir(parents=True)
    archive, members = dest / 'linux-architecture-raw.tar.gz', []
    with tarfile.open(archive, 'w:gz') as handle:
        for path in sorted(out.rglob('*')):
            if not path.is_file():
                continue
            assert not path.is_symlink()
            raw, name = path.read_bytes(), path.relative_to(out).as_posix()
            members.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
            handle.add(path, arcname=name, recursive=False)
    assert archive.stat().st_size < 95 * 1024 * 1024
    with tarfile.open(archive, 'r:gz') as handle:
        entries = handle.getmembers()
        assert len(entries) == len(members)
        for entry, row in zip(entries, members):
            assert entry.isfile() and entry.name == row['path']
            raw = handle.extractfile(entry).read()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    inventory = {'schema': 'geo314-architecture-raw-archive/1', 'source_sha': source, 'archive': archive.name,
                 'archive_bytes': archive.stat().st_size, 'archive_sha256': sha(archive.read_bytes()),
                 'verified_each_member': True, 'members': members}
    (dest / 'MEMBER_INVENTORY.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.copy2(Path(__file__), dest / Path(__file__).name)
    shutil.copy2(out / 'receipt.json', dest / 'outer-receipt.json')
    shutil.copy2(out / 'refresh/RESULT.json', dest / 'RESULT.json')
    for name in names:
        shutil.copy2(new / name, repo / 'geometry-core/domain-decoupling' / name)
    (dest / 'PROGRESS.md').write_text(f'''# #314 Linux 架構四檔重產

本輪真受驗來源／帳本保存提交 L：`{source}`。
原三條裁判全部退出 0：architecture_contract.py、test_architecture_contract.py、test_product_architecture.py。未改原裁判、根目錄、責任、route、trust 或斷言。
實際 inventory：{json.dumps(result['counts'], ensure_ascii=False)}。
完整五 roots 與三 standalone 的 raw/LF bytes、固定 Git blobs、原工具、HEAD、SSOT、乾淨狀態前後均核對；manifest bytes 保持指定 L 原樣。

本目錄 archive 保存 argv、完整 stdout/stderr、退出碼、環境、SHA、source inventory、工具、原四檔與新四檔，所有成員已解包逐 bytes/SHA-256 驗同。產物保留真 sourceBaseHead=L，沒有改寫成保存產物的後續 A。
下一步：一般推送四檔與收據，固定 A=最終正式驗收 F；之後仍須在同一 F 執行完整 native、六 browser 與適用專項，這份架構收據沒有預先宣稱其結果。
''', encoding='utf-8')
    files = [path for path in sorted(dest.iterdir()) if path.is_file()]
    assert all(path.stat().st_size < 95 * 1024 * 1024 for path in files)
    (dest / 'SHA256SUMS').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in files), encoding='utf-8')
    print(json.dumps({'source': source, 'destination': str(dest), 'archive_bytes': archive.stat().st_size,
                      'archive_members': len(members), 'counts': result['counts']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
