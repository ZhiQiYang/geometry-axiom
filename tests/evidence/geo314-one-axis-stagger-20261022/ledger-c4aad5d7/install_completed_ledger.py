"""Install a completed original 100-mutant #314 ledger with verified command and proof evidence."""
from pathlib import Path
import argparse
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tarfile

REPO = Path('/tmp/g261-next314')
HELPER = Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
LIMIT = 95 * 1024 * 1024

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)

def verified_copy_tree(source, destination):
    shutil.copytree(source, destination)
    for path in source.rglob('*'):
        if path.is_file():
            assert path.read_bytes() == (destination / path.relative_to(source)).read_bytes()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--raw', required=True, type=Path)
    parser.add_argument('--outer', required=True, type=Path)
    parser.add_argument('--proof', required=True, type=Path)
    parser.add_argument('--anchor-proof', required=True, type=Path)
    args = parser.parse_args()
    source, raw_root, outer_root, proof = args.source, args.raw.resolve(), args.outer.resolve(), args.proof.resolve()
    anchor_proof = args.anchor_proof.resolve()
    assert git('rev-parse', 'HEAD').decode().strip() == source
    assert not git('status', '--porcelain=v1', '--untracked-files=all')
    report = json.loads((raw_root / 'receipt.json').read_text())
    outer = json.loads((outer_root / 'receipt.json').read_text())
    assert report['sha'] == outer['sha'] == source
    assert report['ended_utc'] and report['exit_code'] == outer['outer_process']['actual_process_returncode'] == 0
    assert not report['errors']
    assert report['source_before'] == report['source_after'] == {'head': source, 'status': ''}
    original_steps = [(step['label'], step['original_command_result']['actual_process_returncode']) for step in report['steps']
                      if step['label'] in ('precheck', 'full-ledger', 'checkafter')]
    assert original_steps == [('precheck', 1), ('full-ledger', 0), ('checkafter', 0)]
    assert report['all_nonretired_execution_head_equal_source']
    ledger_raw = (raw_root / 'ledger.json').read_bytes()
    assert sha(ledger_raw) == report['ledger_sha256']
    ledger = json.loads(ledger_raw)
    counts = dict(collections.Counter(row['verdict'] for row in ledger.values()))
    assert len(ledger) == 100
    assert counts == {'killed': 91, 'equivalent': 5, 'crashed': 1, 'retired': 3}
    active = {key: row for key, row in ledger.items() if row['verdict'] != 'retired'}
    assert len(active) == 97 and all(row['execution']['head'] == source for row in active.values())
    assert ledger['M20']['verdict'] == 'crashed'
    new = {f'M{number}': ledger[f'M{number}'] for number in range(99, 121)}
    assert all(row['verdict'] == ('equivalent' if key == 'M110' else 'killed') for key, row in new.items())
    m110 = ledger['M110']['execution']
    assert [m110[label]['exit_code'] for label in ('baseline', 'mutant', 'restored')] == [0, 0, 0]
    assert m110['byte_restored']
    for proof_root in (proof, anchor_proof):
        assert proof_root.is_dir() and (proof_root / 'SHA256SUMS').is_file()
        for line in (proof_root / 'SHA256SUMS').read_text().splitlines():
            expected, relative = line.split('  ', 1)
            path = (proof_root / relative).resolve()
            assert path.is_relative_to(proof_root) and sha(path.read_bytes()) == expected
    equivalent_receipt = json.loads((proof / 'proof-receipt.json').read_text())
    anchor_receipt = json.loads((anchor_proof / 'completion-002-receipt.json').read_text())
    for receipt in (equivalent_receipt, anchor_receipt):
        assert receipt['source_sha'] == source and receipt['exit_code'] == 0
        assert receipt['source_before'] == receipt['source_after'] == {'head': source, 'status': ''}
    assert [phase['original_subset_exit'] for phase in equivalent_receipt['phases']] == [0, 1, 0]
    assert anchor_receipt['proof_original_exits'] == [0, 1, 0]
    index_paths = [Path('/workspace/geo314-work') / name for name in ('FIX_PROOF_INDEX.json', 'FIX_PROOF_INDEX.md')]
    assert all(path.is_file() for path in index_paths)
    dest = REPO / 'tests/evidence/geo314-one-axis-stagger-20261022' / ('ledger-' + source[:8])
    assert not dest.exists()
    dest.mkdir(parents=True)
    sources = []
    for label, root in [('inner', raw_root), ('outer', outer_root)]:
        sources.extend((label + '/' + path.name, path) for path in root.iterdir() if path.is_file())
        for name in ('subcommands', 'tools'):
            directory = root / name
            if directory.is_dir():
                sources.extend((label + '/' + path.relative_to(root).as_posix(), path) for path in directory.rglob('*') if path.is_file())
    cache = raw_root / 'cache'
    for directory, dirs, files in os.walk(cache):
        dirs[:] = sorted(name for name in dirs if name != '_bridge-work')
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_file():
                sources.append(('private-cache/' + path.relative_to(cache).as_posix(), path))
    archive, members, excluded = dest / 'complete-ledger-raw.tar.gz', [], []
    with tarfile.open(archive, 'w:gz') as handle:
        for name, path in sorted(sources):
            assert not path.is_symlink()
            raw = path.read_bytes()
            row = {'path': name, 'bytes': len(raw), 'sha256': sha(raw)}
            if raw.startswith(b'\x7fELF'):
                excluded.append({**row, 'reason': 'Rebuildable executable; original sidecar and actual execution hash preserved.'})
                continue
            members.append(row)
            handle.add(path, arcname=name, recursive=False)
    assert archive.stat().st_size < LIMIT
    with tarfile.open(archive, 'r:gz') as handle:
        entries = handle.getmembers(); assert len(entries) == len(members)
        for entry, row in zip(entries, members):
            assert entry.isfile() and entry.name == row['path']
            raw = handle.extractfile(entry).read()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    save(dest / 'MEMBER_INVENTORY.json', {'schema': 'geo314-complete-ledger-archive/1', 'source_sha': source,
         'archive': archive.name, 'archive_bytes': archive.stat().st_size, 'archive_sha256': sha(archive.read_bytes()),
         'all_members_byte_hash_verified': True, 'members': members, 'excluded_rebuildable_executables': excluded,
         'not_archived': 'Reconstructable private _bridge-work Git/source clone; exact complete closure/oracle bindings and official per-build sidecars are archived.',
         'core_inner_stream_limit': 'Original core tool records structured oracle results and output hashes without separate raw inner compiler/oracle stdout files; complete top-level original command streams are archived.'})
    verified_copy_tree(proof, dest / 'real-equivalence-proof')
    verified_copy_tree(anchor_proof, dest / 'real-assembly-anchor-proof')
    for path in index_paths:
        shutil.copy2(path, dest / path.name)
        assert (dest / path.name).read_bytes() == path.read_bytes()
    shutil.copy2(Path(__file__), dest / Path(__file__).name)
    shutil.copy2(raw_root / 'receipt.json', dest / 'ledger-receipt.json')
    shutil.copy2(outer_root / 'receipt.json', dest / 'outer-receipt.json')
    save(dest / 'NEW_MUTANTS.json', {key: {'desc': row['desc'], 'verdict': row['verdict'], 'why': row['why'],
         'killed_by': row.get('killed_by'), 'execution': row['execution']} for key, row in new.items()})
    protected = ['公理層.md', '決策佇列.md', 'BACKLOG.md', 'geometry-guide/公理層-白話.md']
    protected_before = {name: sha((REPO / name).read_bytes()) for name in protected}
    (REPO / 'tests/mutants_results.json').write_bytes(ledger_raw)
    ignore = REPO / '.gitignore'
    raw = ignore.read_bytes(); line = b'!/evidence/geo314-final-*/'
    assert line not in raw.splitlines()
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    ignore.write_bytes(raw + (b'' if raw.endswith(b'\n') else newline) + line + newline)
    assert sha(HELPER.read_bytes()) == 'c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
    spec = importlib.util.spec_from_file_location('geo314_final_install_capture', HELPER)
    capture = importlib.util.module_from_spec(spec); spec.loader.exec_module(capture)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('GIT_', 'GEOMETRY_', 'MUTATE_'))
           and key not in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONOPTIMIZE', 'NODE_OPTIONS', 'LD_PRELOAD')}
    env.update(LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               GITHUB_SHA=source, GITHUB_WORKSPACE=str(REPO), TMPDIR=str(raw_root / 'tmp'),
               MUTATE_CACHE=str(raw_root / 'cache'), MUTATE_RESULTS=str(REPO / 'tests/mutants_results.json'))
    recorder = capture.Recorder(dest / 'postinstall', env, source)
    postinstall = []
    for label, command in [('reader-sync', ['python3', '-B', 'geometry-guide/sync_axiom_reader.py']),
                           ('reader-check', ['python3', '-B', 'geometry-guide/sync_axiom_reader.py', '--check']),
                           ('ledger-check', ['python3', '-B', 'tests/mutate.py', '--check'])]:
        row, _, _ = recorder.run(command, cwd=REPO, timeout=None, check=False, source_sha=source,
             source_variant='completed-ledger-and-publication-metadata-installed-uncommitted')
        postinstall.append({'label': label, 'original_command_result': row})
    assert all(sha((REPO / name).read_bytes()) == value for name, value in protected_before.items())
    save(dest / 'INSTALLATION.json', {'schema': 'geo314-completed-ledger-install/1', 'source_sha': source,
         'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'ledger_sha256': sha(ledger_raw),
         'record_count': len(ledger), 'verdict_counts': counts, 'executed_count': len(active),
         'all_execution_head_equal_source': True, 'original_three_steps': original_steps,
         'postinstall': postinstall, 'protected_files_unchanged': protected_before,
         'private_mutation_cache': str(raw_root / 'cache'), 'global_cache_touched': False})
    assert all(row['original_command_result']['actual_process_returncode'] == 0 for row in postinstall)
    (dest / 'PROGRESS.md').write_text(f'''# #314 新S整份突變帳本重產

實跑產品／裁判來源 P=新S：`{source}`；開始與結束 HEAD 相同，工作樹全乾淨。

| 原命令 | 實際退出碼 |
|---|---:|
| `python3 tests/mutate.py --check`（完整重產前） | 1 |
| `python3 tests/mutate.py`（不帶 IDs、整份100筆） | 0 |
| `python3 tests/mutate.py --check`（完整重產後） | 0 |

原 outer／reaper退出0。100筆=91 killed、5 equivalent、M20 crashed、3 retired；97個真execution.head全為上述新S，沒有把原舊S的57筆execution拼入。M20原三次同夾具存取違規照列crashed，不冒稱斷言killed。新增M99–120共22筆：21 killed，M110有真baseline/mutant/restored 0/0/0的equivalent execution。

58個未變C的合法原編譯快取（57mutant＋baseline）先以新S原fingerprint/cache_state核hit、複製bytes/hash一致，保原sidecar與原編譯來源；每個原oracle仍在新S整份重新實跑。編譯快取不當作舊execution證據。private scratch只排歷史evidence，完整Cclosure／505 oracle inputs／40原oracle hash與RESTORED36方法先核相同，沒有改原判準或使用者鎖定決定。

本輪先前容量full2／retry40原1與M110原invalid都在公開診斷D `01f1130fd0e93f61c698a963ee74ea349ac6820d` 原樣保留。runner精準修正只支援明示equivalent的完整真execution，原honesty suite74/74通過；真CLI／真bridge修正撤回0/1/0原輸出收於real-equivalence-proof。負控invalid且無execution，不冒killed；單筆proof不冒globalstrict0，本輪全100與strict原0才是整份帳本有效證據。

ASM錨點修正另以同一精簡private clone、原test_mutation_anchors三方法完成真正修正撤回0/1/0。原001收錄器因unittest字串repr換行誤判而退出1，原baseline0、撤回1與兩個正常AssertionError完整保留；002只補讀原finding與缺少的還原0，不重跑前兩相，不改產品或斷言。完整原兩輪與outer收於real-assembly-anchor-proof；FIX_PROOF_INDEX逐項區分修正自證與舊範圍產品mutations、環境retry及未適用項。

archive完整保存原命令／退出碼／top-level與bridge已落盤完整stdout/stderr／環境／SHA／工具與sidecars，全部逐member解包bytes/hash核同；原core子層未逐檔落盤streams只保其原structured outcome和hash，不捏造原raw。可重建ELF列hash，source clone可由真Git來源與原側錄重建，原雲端檔案仍保留。
安裝後原canonical sync／reader --check／mutation --check均退出0，公理層／決策佇列／Backlog／白話bytes保持相同；mutationcheck只用本輪private cache。帳本保真execution來源，不改寫成保存提交。

下一步：一般推送帳本保存提交L，在乾淨L以Linux重產架構四檔和原三裁判，固定公開A=正式驗收F；完整native與六browser仍由root排同一F，這裡不預填其結果。
''', encoding='utf-8')
    files = [path for path in sorted(dest.rglob('*')) if path.is_file()]
    assert all(path.stat().st_size < LIMIT for path in files)
    (dest / 'SHA256SUMS').write_text(''.join(f'{sha(path.read_bytes())}  {path.relative_to(dest).as_posix()}\n' for path in files), encoding='utf-8')
    print(json.dumps({'source': source, 'destination': str(dest), 'ledger_sha256': sha(ledger_raw), 'counts': counts,
                      'archive_bytes': archive.stat().st_size, 'members': len(members), 'excluded_elf': len(excluded), 'postinstall_exits': [row['original_command_result']['actual_process_returncode'] for row in postinstall]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
