"""Archive the completed #314 real equivalence proof without touching any source or original raw file."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import re
import shutil
import tarfile

INNER = Path('/tmp/geo314-equivalence-proof-c4aad5d7')
OUTER = Path('/workspace/geo314-equivalence-proof-outer/geo314-equivalence-real-c4aad5d7')
DEST = Path('/workspace/geo314-work/equivalence-proof-publication-001')
SOURCE = 'c4aad5d7bb98ea864639f9e6d85c99bb2613c24b'
CONTROL = '160e9dc9759aea2cd6b6f7c9eb717590924d1a24'
PHASES = ('fixed-baseline', 'withdrawn', 'fixed-restored')
SOFT_LIMIT = 80 * 1024 * 1024
HARD_LIMIT = 95 * 1024 * 1024

def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def verify_command_rows(rows):
    streams = []
    for row in rows:
        folder = Path(row['directory'])
        assert row['actual_process_returncode'] is not None and not row.get('timeout_expired')
        for kind in ('stdin', 'stdout', 'stderr'):
            path = folder / (kind + '.bin')
            assert path.is_file() and not path.is_symlink()
            assert digest_file(path) == row[kind + '_sha256']
            if kind != 'stdin':
                assert path.stat().st_size == row[kind + '_bytes']
            streams.append(str(path))
    return streams

def main():
    assert not DEST.exists()
    report = json.loads((INNER / 'receipt.json').read_text())
    outer = json.loads((OUTER / 'receipt.json').read_text())
    assert report['source_sha'] == SOURCE and report['exit_code'] == 0 and not report['errors']
    assert report['source_before'] == report['source_after'] == {'head': SOURCE, 'status': ''}
    assert outer['outer_process']['actual_process_returncode'] == 0
    assert report['controlled_withdrawal_sha'] == CONTROL
    assert [row['original_subset_exit'] for row in report['phases']] == [0, 1, 0]
    assert [row['verdict'] for row in report['phases']] == ['equivalent', 'invalid', 'equivalent']
    assert [row['real_baseline_mutant_restored_exits'] for row in report['phases']] == [[0, 0, 0], [None, None, None], [0, 0, 0]]
    command_streams = verify_command_rows(report['commands']) + verify_command_rows(outer['subcommands'])
    honesty = next(row['original_command_result'] for row in report['steps'] if row['label'] == 'original-honesty-suite')
    assert honesty['actual_process_returncode'] == 0
    honesty_text = (Path(honesty['directory']) / 'stderr.bin').read_text()
    test_counts = re.findall(r'^Ran (\d+) tests? in [0-9.]+s\s*$', honesty_text, re.M)
    assert test_counts == ['74'] and honesty_text.rstrip().splitlines()[-1] == 'OK'
    tool_snapshots = []
    for original, expected in report['tool_hashes'].items():
        snapshot = INNER / 'tools' / Path(original).name
        assert snapshot.is_file() and digest_file(snapshot) == expected
        tool_snapshots.append({'original_path': original, 'snapshot_path': str(snapshot), 'bytes': snapshot.stat().st_size, 'sha256': expected})
    phase_validations = []
    for name in PHASES:
        validation = json.loads((INNER / name / 'M110_VALIDATION.json').read_text())
        ledger = json.loads((INNER / name / 'ledger.json').read_text())
        assert validation['complete_record'] == ledger['M110']
        if name == 'withdrawn':
            assert validation['verdict'] == 'invalid' and 'execution' not in ledger['M110']
            assert validation['execution_problems'] == ['missing bridge execution receipt']
        else:
            assert validation['verdict'] == 'equivalent' and not validation['execution_problems']
            assert validation['execution_head'] == SOURCE
            assert [validation[key] for key in ('baseline_exit', 'mutant_exit', 'restored_exit')] == [0, 0, 0]
        phase_validations.append({key: value for key, value in validation.items() if key not in ('complete_record', 'all_ledger_verdict_counts')})
    clone_roots = [(INNER / 'controlled-repo', CONTROL)]
    clone_roots.extend((INNER / phase / 'cache/_bridge-work' / (CONTROL if phase == 'withdrawn' else SOURCE) / 'repo',
                        CONTROL if phase == 'withdrawn' else SOURCE) for phase in PHASES)
    clone_metadata = []
    for root, source_sha in clone_roots:
        assert root.is_dir() and (root / '.git').is_dir()
        files = []
        for parent, _, names in os.walk(root, followlinks=False):
            for name in names:
                path = Path(parent) / name
                assert not path.is_symlink()
                files.append(path)
        clone_metadata.append({'path': str(root), 'source_sha': source_sha, 'present_at_collection': True,
                               'file_count': len(files), 'bytes': sum(path.stat().st_size for path in files),
                               'payload_archived': False, 'raw_deleted_or_modified': False,
                               'reason': 'private sparse Git source/control clone and Git metadata; excluded from publication, not absent from original proof'})
    selected, excluded_elf = [], []
    for label, root in [('inner', INNER), ('outer', OUTER)]:
        for parent, directories, names in os.walk(root, followlinks=False):
            parent = Path(parent)
            directories[:] = sorted(name for name in directories if not any(parent / name == q for q, _ in clone_roots))
            for name in sorted(names):
                path = parent / name
                assert path.is_file() and not path.is_symlink()
                assert not any(path.is_relative_to(q) for q, _ in clone_roots)
                size = path.stat().st_size
                with path.open('rb') as handle:
                    magic = handle.read(4)
                row = {'path': label + '/' + path.relative_to(root).as_posix(), 'original_path': str(path),
                       'bytes': size, 'sha256': digest_file(path)}
                if magic == b'\x7fELF':
                    excluded_elf.append({**row, 'reason': 'rebuildable ELF binary; bytes/hash retained, payload excluded',
                                         'present_at_collection': True, 'raw_deleted_or_modified': False})
                else:
                    selected.append(row)
    selected.sort(key=lambda row: row['path'])
    assert len({row['path'] for row in selected}) == len(selected)
    selected_paths = {row['original_path'] for row in selected}
    assert set(command_streams) <= selected_paths
    assert len(excluded_elf) == 7
    DEST.mkdir(parents=True)
    (DEST / 'archives').mkdir()
    archives, current, current_bytes = [], [], 0
    def pack(rows):
        archive = DEST / 'archives' / ('proof-raw-%02d.tar.gz' % (len(archives) + 1))
        with tarfile.open(archive, 'w:gz') as handle:
            for row in rows:
                path = Path(row['original_path'])
                assert path.stat().st_size == row['bytes'] and digest_file(path) == row['sha256']
                handle.add(path, arcname=row['path'], recursive=False)
        assert archive.stat().st_size < HARD_LIMIT
        with tarfile.open(archive, 'r:gz') as handle:
            entries = handle.getmembers()
            assert len(entries) == len(rows)
            for entry, row in zip(entries, rows):
                assert entry.isfile() and entry.name == row['path'] and entry.size == row['bytes']
                extracted = handle.extractfile(entry)
                value = hashlib.sha256()
                for chunk in iter(lambda: extracted.read(1024 * 1024), b''):
                    value.update(chunk)
                assert value.hexdigest() == row['sha256']
                assert digest_file(Path(row['original_path'])) == row['sha256']
                row['archive'] = archive.relative_to(DEST).as_posix()
        archives.append({'path': archive.relative_to(DEST).as_posix(), 'bytes': archive.stat().st_size,
                         'sha256': digest_file(archive), 'member_count': len(rows),
                         'uncompressed_file_bytes': sum(row['bytes'] for row in rows), 'every_member_verified': True})
    for row in selected:
        if current and current_bytes + row['bytes'] > SOFT_LIMIT:
            pack(current); current, current_bytes = [], 0
        current.append(row); current_bytes += row['bytes']
    if current:
        pack(current)
    save(DEST / 'MEMBER_INVENTORY.json', {'schema': 'geo314-equivalence-proof-members/1', 'source_sha': SOURCE,
         'verified_member_count': len(selected), 'uncompressed_file_bytes': sum(row['bytes'] for row in selected),
         'archives': archives, 'members': selected})
    save(DEST / 'EXCLUDED.json', {'schema': 'geo314-equivalence-proof-excluded/1', 'source_sha': SOURCE,
         'private_source_and_control_clones': clone_metadata, 'elf_files': excluded_elf,
         'note': 'Exclusion concerns this publication payload only. All original raw files and source/control clones remain present and unmodified.'})
    save(DEST / 'TOOL_SNAPSHOTS.json', {'snapshots': tool_snapshots,
         'policy': 'Only exact tools snapshots already captured by the completed proof are archived; no current same-path PREPARER bytes are substituted.'})
    shutil.copy2(Path(__file__), DEST / Path(__file__).name)
    shutil.copy2(INNER / 'receipt.json', DEST / 'proof-receipt.json')
    shutil.copy2(OUTER / 'receipt.json', DEST / 'outer-receipt.json')
    save(DEST / 'PUBLICATION.json', {'schema': 'geo314-equivalence-proof-publication/1', 'source_sha': SOURCE,
         'control_sha': CONTROL, 'scope': 'Completed real M110 CLI proof and original single-record validator; no global strict acceptance claim.',
         'collector': {'path': str(Path(__file__).resolve()), 'sha256': digest_file(Path(__file__).resolve())},
         'collected_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'inner_exit': report['exit_code'],
         'outer_process_exit': outer['outer_process']['actual_process_returncode'], 'original_honesty_methods': 74,
         'original_honesty_exit': honesty['actual_process_returncode'], 'original_M110_subset_exits': [0, 1, 0],
         'phase_validations': phase_validations, 'archives': archives, 'member_count': len(selected),
         'verified_command_streams': len(command_streams), 'excluded_ELF_count': len(excluded_elf),
         'source_checkout_written': False, 'original_raw_written_or_deleted': False,
         'test_compiler_or_retry_started_by_collector': False, 'git_commit_or_push_performed': False})
    (DEST / 'README.md').write_text(f'''# #314 bridge equivalent 真實突變自證封存

產品／裁判修正實跑來源：`{SOURCE}`。內層 proof 與外層 reaper 原退出碼均 0，來源 HEAD 與乾淨狀態前後相同。
原 `python3 -B tests/test_mutation_freshness.py` 完整 74 方法，退出 0；既有 honesty suite bytes 未因這份封存而改動。

| phase | 原 M110 subset CLI | 原判決 | 原 baseline／mutant／restored |
|---|---:|---|---|
| fixed-baseline | 0 | equivalent | 0／0／0 |
| withdrawn（只撤裁判修正的本地已提交 `{CONTROL}`） | 1 | invalid | 沒有 M110 execution receipt；不宣稱 mutant 或 restored 執行 |
| fixed-restored | 0 | equivalent | 0／0／0 |

固定版與恢復版使用獨立 cache／scratch；各自真編譯、真 bridge、原具名 unittest 與原 `execution_problems()` 單筆驗證均保留。沒有 mock build／oracle。
撤回版的 invalid 是 runner 對第一個 bridge equivalent 定義不相容，沒有 execution；這是裁判修正的 0/1/0 控制，**不是產品斷言 killed 或 crash detection**。

這份 proof 只主張 M110 原 subset CLI、原單筆 execution validator 與完整既有 honesty suite；**沒有主張全表 strict --check 通過，也沒有取代新來源的整份帳本與最終正式七項驗收**。

archive 保存完成當時 inner／outer 的全部 top-level、subcommands、tools、三 phase identity／ledger／validation、所有非 ELF cache stdout／stderr／sidecars，以及原 CONTROL_COMMIT／WITHDRAWAL.diff。每個成員的 path／bytes／SHA-256 已解包核同，原命令所有 stdin／stdout／stderr 也依原收據 hash 核同。`MEMBER_INVENTORY.json` 是逐檔清單，`EXCLUDED.json` 明列排除項。

四個 private scratch／control Git source clone 的 payload 與 7 個可重建 ELF 沒有封入；ELF 原 bytes／SHA-256 逐檔保留，clone 的 path／source SHA／存在與 file count／bytes 也保留。**排除僅指這份發布封包，不代表原 source 不存在；原 raw、source/control clone 與 ELF 都仍在雲端，未修改或刪除。**

原 proof/tools 中的 PREPARER 快照 SHA-256 是 `e14e75825102060aaa3c0361b7a6ffcbf892bc3150f1df39fa06cbe413391f17`；proof 結束後同路徑工具另有版本命令更新，這裡只封當次舊快照，不以現在 bytes 取代。所有當次工具快照與原收據 hash 綁定見 `TOOL_SNAPSHOTS.json`。

本 collector 只在 repository 外產生封存，不執行測試、compiler、retry、commit 或 push，不動目前正在重產帳本的新 source SHA。
''', encoding='utf-8')
    files = [path for path in sorted(DEST.rglob('*')) if path.is_file()]
    assert all(path.stat().st_size < HARD_LIMIT for path in files)
    (DEST / 'SHA256SUMS').write_text(''.join(f'{digest_file(path)}  {path.relative_to(DEST).as_posix()}\n' for path in files), encoding='utf-8')
    print(json.dumps({'staging': str(DEST), 'archives': archives, 'member_count': len(selected),
                      'member_bytes': sum(row['bytes'] for row in selected), 'excluded_ELF_count': len(excluded_elf),
                      'excluded_clone_count': len(clone_metadata), 'verified_command_streams': len(command_streams),
                      'staging_files': len(files) + 1, 'staging_bytes': sum(path.stat().st_size for path in DEST.rglob('*') if path.is_file()),
                      'SHA256SUMS_sha256': digest_file(DEST / 'SHA256SUMS')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
