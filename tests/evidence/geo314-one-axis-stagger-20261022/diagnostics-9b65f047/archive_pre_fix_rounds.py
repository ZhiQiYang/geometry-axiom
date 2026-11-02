"""Archive completed original ENOSPC/recovery rounds without editing any verdict or source."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import shutil
import tarfile

SOURCE = '9b65f047d5fd470cdc89ce45e613d06af493b616'
ROOTS = [('r1-inner', Path('/workspace/geo314-core-regenerate-s')),
         ('r1-outer', Path('/workspace/geo314-core-outer/geo314-ledger-regenerate-s')),
         ('environment-retry-inner', Path('/workspace/geo314-core-recover-s-env1')),
         ('environment-retry-outer', Path('/workspace/geo314-core-recovery-outer/geo314-ledger-env-retry1'))]
CAPACITY = Path('/tmp/geo261-cold-main-clone-release')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True, type=Path)
    args = parser.parse_args()
    dest = args.dest.resolve()
    assert not dest.exists()
    reports = {label: json.loads((root / 'receipt.json').read_text()) for label, root in ROOTS}
    assert all(report.get('ended_utc') for label, report in reports.items() if label.endswith('-inner'))
    assert reports['r1-inner']['exit_code'] == 1 and reports['r1-outer']['outer_process']['actual_process_returncode'] == 1
    assert reports['r1-inner']['steps'][1]['original_command_result']['actual_process_returncode'] == 2
    assert reports['environment-retry-inner']['source_before'] == reports['environment-retry-inner']['source_after'] == {'head': SOURCE, 'status': ''}
    dest.mkdir(parents=True)
    sources = []
    for label, root in ROOTS:
        sources.extend((label + '/' + path.name, path) for path in root.iterdir() if path.is_file())
        for name in ('subcommands', 'tools'):
            folder = root / name
            if folder.is_dir():
                sources.extend((label + '/' + path.relative_to(root).as_posix(), path) for path in folder.rglob('*') if path.is_file())
    assert (CAPACITY / 'receipt.json').is_file()
    sources.extend(('capacity-repair/' + path.relative_to(CAPACITY).as_posix(), path) for path in CAPACITY.rglob('*') if path.is_file())
    for label, cache in [('r1-cache', Path('/workspace/geo314-core-regenerate-s/tmp/geometry-tests/mutants')),
                         ('environment-retry-cache', Path('/workspace/geo314-core-recover-s-env1/cache'))]:
        for directory, dirs, files in os.walk(cache):
            dirs[:] = sorted(name for name in dirs if name != '_bridge-work')
            for name in sorted(files):
                path = Path(directory) / name
                if path.is_file():
                    sources.append((label + '/' + path.relative_to(cache).as_posix(), path))
    members, excluded = [], []
    archive = dest / 'pre-fix-rounds-and-capacity-raw.tar.gz'
    with tarfile.open(archive, 'w:gz') as handle:
        for name, path in sorted(sources):
            assert not path.is_symlink()
            raw = path.read_bytes()
            row = {'path': name, 'bytes': len(raw), 'sha256': sha(raw)}
            if raw.startswith(b'\x7fELF'):
                excluded.append({**row, 'reason': 'Rebuildable compiled executable; original sidecar and execution hashes preserved.'})
                continue
            members.append(row)
            handle.add(path, arcname=name, recursive=False)
    assert archive.stat().st_size < 95 * 1024 * 1024
    with tarfile.open(archive, 'r:gz') as handle:
        entries = handle.getmembers(); assert len(entries) == len(members)
        for entry, row in zip(entries, members):
            assert entry.isfile() and entry.name == row['path']
            raw = handle.extractfile(entry).read()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    inventory = {'schema': 'geo314-pre-fix-round-archive/1', 'source_sha': SOURCE, 'archive': archive.name,
                 'archive_bytes': archive.stat().st_size, 'archive_sha256': sha(archive.read_bytes()),
                 'all_members_byte_hash_verified': True, 'members': members, 'excluded_rebuildable_executables': excluded,
                 'scratch_clones_not_archived': 'All private _bridge-work clones are reconstructable; exact source/closure/oracle identity and official build sidecars are included.',
                 'uncaptured_original_core_inner_streams': 'The original core mutation tool retains structured oracle results and stream hashes, not separate raw stdout files for each inner core compiler/oracle attempt. Top-level original command streams are archived completely.'}
    (dest / 'MEMBER_INVENTORY.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {}
    for label, root in ROOTS:
        report = reports[label]
        result[label] = {'source_sha': report.get('sha'), 'exit_code': report.get('exit_code'), 'outer_process_exit': report.get('outer_process', {}).get('actual_process_returncode'),
                         'source_before': report.get('source_before'), 'source_after': report.get('source_after'),
                         'steps': [(row['label'], row['original_command_result']['actual_process_returncode']) for row in report.get('steps', [])],
                         'errors': report.get('errors', [])}
        if (root / 'ledger.json').is_file():
            ledger = json.loads((root / 'ledger.json').read_text())
            result[label]['record_count'] = len(ledger)
            result[label]['verdict_counts'] = dict(collections.Counter(row['verdict'] for row in ledger.values()))
    (dest / 'ROUND_SUMMARY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.copy2(Path(__file__), dest / Path(__file__).name)
    (dest / 'PROGRESS.md').write_text(f'''# #314 帳本容量事故與完整環境重試

兩輪都固定實跑來源 S：`{SOURCE}`。此提交只封存診斷，不是新最終驗收 F，也沒有把原紅改綠。

第一輪原 `python3 tests/mutate.py` 退出2，outer1：/workspace滿造成M63還原測試、M64還原build與M65目錄建立受阻；checkafter及source_after未錄到。57個core execution原已完成（52 killed、4 equivalent、M20 crashed），M20不冒稱斷言killed。

容量修復僅釋三個已公開且乾淨可Git重建的舊main比較clone，真回收3,045,318,656bytes；原parent raw前後hash保留。修復全部guard／argv／退出碼／完整streams／hash已封入同archive。

第二輪新out／新cache不覆第一輪raw。private scratch僅排三類歷史evidence，完整C閉包、505個oracle inputs、40個oracle hash與RESTORED36方法先核完全相同。以原CLI跑全40個bridge IDs，原57core紀錄保留；這不是單次full0。各原命令、真退出碼與完整輸出見ROUND_SUMMARY與原receipt，原後處理例外也照保，沒有重寫結束碼。

本輪發現M110首個bridge equivalent與既有runner的執行入口／execution validator不相容，原工具會寫invalid而非真等價execution。接下來依原核心規則精準修runner：明示equivalent且真baseline/mutant/restored完整survived才記equivalent，其他崩潰／斷言／受阻不冒等價。先做真CLI/bridge撤回0/1/0，再凍結新S整份重產100筆，舊57execution不帶入新S。

archive所有成員均解包逐bytes/SHA-256核同；ELF僅列hash及原sidecar，完整top-level命令streams與bridge已落盤raw保留。原core每內層編譯／oracle的原raw沒有逐檔落盤，不聲稱補捕到不存在的streams。
''', encoding='utf-8')
    files = [path for path in sorted(dest.iterdir()) if path.is_file()]
    (dest / 'SHA256SUMS').write_text(''.join(f'{sha(path.read_bytes())}  {path.name}\n' for path in files), encoding='utf-8')
    print(json.dumps({'destination': str(dest), 'archive_bytes': archive.stat().st_size, 'members': len(members), 'excluded_elf': len(excluded)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
