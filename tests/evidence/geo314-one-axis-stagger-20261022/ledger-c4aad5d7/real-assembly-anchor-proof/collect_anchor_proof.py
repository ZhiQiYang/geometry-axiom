"""Archive both original #314 anchor proof attempts and index the completed original 0/1/0 evidence."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import tarfile

BASE = Path('/workspace/geo314-work')
FIRST = BASE / 'anchor-repair-proof-c4aad5d7-001'
COMPLETION = BASE / 'anchor-repair-proof-c4aad5d7-002'
FIRST_OUTER = Path('/workspace/geo314-anchor-proof-outer/geo314-anchor-repair-c4aad5d7')
COMPLETION_OUTER = Path('/workspace/geo314-anchor-proof-outer/geo314-anchor-completion-c4aad5d7')
DEST = BASE / 'anchor-proof-publication-001'
SOURCE = 'c4aad5d7bb98ea864639f9e6d85c99bb2613c24b'
CONTROL = '238a5125c95e77d74603fdd943baaa81e140f7da'
SOFT_LIMIT, HARD_LIMIT = 80 * 1024 * 1024, 95 * 1024 * 1024

def digest_file(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()

def load(path):
    return json.loads(path.read_text())

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def reference(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest_file(path)}

def verify_rows(rows):
    paths = []
    for row in rows:
        directory = Path(row['directory'])
        assert row['actual_process_returncode'] is not None and not row.get('timeout_expired')
        for name in ('stdin', 'stdout', 'stderr'):
            path = directory / (name + '.bin')
            assert path.is_file() and digest_file(path) == row[name + '_sha256']
            if name != 'stdin':
                assert path.stat().st_size == row[name + '_bytes']
            paths.append(str(path))
    return paths

def main():
    assert not DEST.exists()
    first, completion = load(FIRST / 'receipt.json'), load(COMPLETION / 'receipt.json')
    first_outer, completion_outer = load(FIRST_OUTER / 'receipt.json'), load(COMPLETION_OUTER / 'receipt.json')
    assert first['source_sha'] == completion['source_sha'] == SOURCE
    assert first['exit_code'] == first_outer['outer_process']['actual_process_returncode'] == 1
    assert completion['exit_code'] == completion_outer['outer_process']['actual_process_returncode'] == 0
    assert first['controlled_withdrawal_sha'] == CONTROL
    assert first['source_before'] == first['source_after'] == completion['source_before'] == completion['source_after'] == {'head': SOURCE, 'status': ''}
    assert completion['original_receipt_sha256'] == digest_file(FIRST / 'receipt.json')
    assert completion['original_collector_exit'] == 1 and not completion['errors']
    assert completion['proof_original_exits'] == [0, 1, 0]
    assert completion['proof_source_shas'] == [SOURCE, CONTROL, SOURCE]
    assert completion['completed_original_methods_per_phase'] == [3, 3, 3]
    assert completion['negative_normal_assertion_failures'] == 2
    steps1 = {step['label']: step['original_command_result'] for step in first['steps']}
    steps2 = {step['label']: step['original_command_result'] for step in completion['steps']}
    baseline = steps1['baseline-original-three-methods']
    withdrawn = steps1['withdrawn-original-three-methods']
    restored = steps2['restored-original-three-methods']
    phases = []
    for label, row, expected, source_sha in [('baseline', baseline, 0, SOURCE), ('withdrawn', withdrawn, 1, CONTROL), ('restored', restored, 0, SOURCE)]:
        assert row['command'] == ['python3', '-B', 'tests/test_mutation_anchors.py']
        assert row['actual_process_returncode'] == expected and row['source_sha'] == source_sha
        directory = Path(row['directory'])
        text = (directory / 'stderr.bin').read_text()
        assert 'Ran 3 tests' in text
        if label == 'withdrawn':
            assert 'FAILED (failures=2)' in text and 'AssertionError' in text
        else:
            assert text.rstrip().endswith('OK')
        phases.append({'label': label, 'source_sha': source_sha, 'exit_code': expected, 'argv': row['command'],
                       'cwd': row['cwd'], 'original_methods': 3, 'raw_stdout': reference(directory / 'stdout.bin'),
                       'raw_stderr': reference(directory / 'stderr.bin'), 'original_command_result': row})
    finding = load(COMPLETION / 'ORIGINAL_WITHDRAWN_FINDING.json')
    assert len(finding['findings']) == 1 and finding['findings'][0]['id'] == 'cancelled-preview'
    assert finding['findings'][0]['tool'] == 'tests/assembly_mutation_check.py'
    assert 'anchor occurs 0 times' in finding['findings'][0]['detail']
    assert not first['compiler_requested'] and not first['original_assertions_modified']
    assert set(steps2).isdisjoint(('baseline-original-three-methods', 'withdrawn-original-three-methods'))
    stream_paths = verify_rows(first['commands']) + verify_rows(completion['commands'])
    stream_paths += verify_rows(first_outer['subcommands']) + verify_rows(completion_outer['subcommands'])
    roots = [('attempt-001', FIRST), ('completion-002', COMPLETION), ('outer-001', FIRST_OUTER), ('outer-002', COMPLETION_OUTER)]
    selected, excluded_git = [], []
    for label, root in roots:
        for directory, directories, names in os.walk(root, followlinks=False):
            directory = Path(directory)
            for name in list(directories):
                if name == '.git':
                    path = directory / name
                    excluded_git.append({'path': str(path), 'reason': 'Git bookkeeping only; all private tracked source files are archived.',
                                         'present_at_collection': True, 'deleted_or_modified_by_collector': False})
            directories[:] = sorted(name for name in directories if name != '.git')
            for name in sorted(names):
                path = directory / name
                assert path.is_file() and not path.is_symlink()
                if name == '.git':
                    excluded_git.append({'path': str(path), 'reason': 'Git bookkeeping file only.', 'present_at_collection': True})
                    continue
                with path.open('rb') as handle:
                    assert handle.read(4) != b'\x7fELF', 'Unexpected executable payload; the proof did not request compilation.'
                selected.append({'path': label + '/' + path.relative_to(root).as_posix(), 'original_path': str(path),
                                 'bytes': path.stat().st_size, 'sha256': digest_file(path)})
    selected.sort(key=lambda row: row['path'])
    assert len({row['path'] for row in selected}) == len(selected)
    assert set(stream_paths) <= {row['original_path'] for row in selected}
    source_head = (FIRST / 'source/.git/HEAD').read_text().strip()
    assert source_head == SOURCE
    DEST.mkdir(parents=True); (DEST / 'archives').mkdir()
    archives, current, current_bytes = [], [], 0
    def pack(rows):
        path = DEST / 'archives' / ('anchor-raw-%02d.tar.gz' % (len(archives) + 1))
        with tarfile.open(path, 'w:gz') as handle:
            for row in rows:
                raw = Path(row['original_path'])
                assert raw.stat().st_size == row['bytes'] and digest_file(raw) == row['sha256']
                handle.add(raw, arcname=row['path'], recursive=False)
        assert path.stat().st_size < HARD_LIMIT
        with tarfile.open(path, 'r:gz') as handle:
            members = handle.getmembers()
            assert len(members) == len(rows)
            for member, row in zip(members, rows):
                assert member.isfile() and member.name == row['path'] and member.size == row['bytes']
                raw, value = handle.extractfile(member), hashlib.sha256()
                for chunk in iter(lambda: raw.read(1024 * 1024), b''):
                    value.update(chunk)
                assert value.hexdigest() == row['sha256'] and digest_file(Path(row['original_path'])) == row['sha256']
                row['archive'] = path.relative_to(DEST).as_posix()
        archives.append({'path': path.relative_to(DEST).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest_file(path),
                         'member_count': len(rows), 'uncompressed_file_bytes': sum(row['bytes'] for row in rows),
                         'every_member_verified': True})
    for row in selected:
        if current and current_bytes + row['bytes'] > SOFT_LIMIT:
            pack(current); current, current_bytes = [], 0
        current.append(row); current_bytes += row['bytes']
    if current:
        pack(current)
    save(DEST / 'MEMBER_INVENTORY.json', {'schema': 'geo314-anchor-proof-members/1', 'source_sha': SOURCE,
         'archives': archives, 'members': selected, 'member_count': len(selected),
         'uncompressed_file_bytes': sum(row['bytes'] for row in selected), 'verified_each_member': True})
    save(DEST / 'EXCLUDED.json', {'schema': 'geo314-anchor-proof-excluded/1', 'git_bookkeeping': excluded_git,
         'source_payload_archived': True, 'private_source_snapshot_after_completion_head': source_head,
         'original_raw_or_source_deleted_or_modified': False})
    for name, path in [('attempt-001-receipt.json', FIRST / 'receipt.json'), ('completion-002-receipt.json', COMPLETION / 'receipt.json'),
                       ('outer-001-receipt.json', FIRST_OUTER / 'receipt.json'), ('outer-002-receipt.json', COMPLETION_OUTER / 'receipt.json')]:
        shutil.copy2(path, DEST / name)
    shutil.copy2(Path(__file__), DEST / Path(__file__).name)
    publication = {'schema': 'geo314-assembly-anchor-proof-publication/1', 'source_sha': SOURCE, 'control_sha': CONTROL,
         'collected_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'scope': 'Exact one-line cancellation anchor repair through all original three test_mutation_anchors methods; not the full ASM behavior gate.',
         'original_attempt_inner_exit': 1, 'original_attempt_outer_process_exit': 1,
         'completion_inner_exit': 0, 'completion_outer_process_exit': 0,
         'original_test_exit_sequence': [0, 1, 0], 'phases': phases, 'normal_assertion_failures_in_withdrawn': 2,
         'original_withdrawn_finding': finding, 'baseline_or_withdrawn_rerun_in_completion': False,
         'compiler_requested': False, 'original_product_or_judge_assertions_modified': False,
         'archives': archives, 'member_count': len(selected), 'command_streams_verified': len(stream_paths),
         'collector': reference(Path(__file__)), 'source_private_snapshot_head': source_head,
         'original_raw_or_main_source_written_or_deleted': False, 'test_compile_retry_commit_or_push_started_by_collector': False}
    save(DEST / 'PUBLICATION.json', publication)
    (DEST / 'README.md').write_text(f'''# #314 ASM cancellation anchor 修正真撤回自證

固定受驗來源：`{SOURCE}`；只撤回一行工具 anchor 的本地已提交負控：`{CONTROL}`。原 `python3 -B tests/test_mutation_anchors.py` 全部三方法真退出為 **0／1／0**。負控有兩條正常 unittest AssertionError，原 finding 精確指出 tests/assembly_mutation_check.py 的 cancelled-preview anchor 在現行 engineering_bridge.inc 出現0次。產品與原測試斷言沒有改動，沒有編譯請求。

這是 **anchor 修正本身**的原三方法撤回控制；它沒有重新跑完整 ASM 產品行為 gate，不能與先前三個產品 guard mutants 的 killed 判決混稱。

001 已完成原 baseline0 與 withdrawn1，但外部 collector 對 stderr 片語的預期不符，故原 inner／outer 都是1，完整原錯誤與raw照保。002讀取同一份原負控 finding，**沒有重抽 baseline 或 withdrawn**，只完成原缺少的 restored 三方法，原退出0；002 inner／outer都0。這份封存沒有把001的1改成0，也沒有以新的測試代替原紅。

archive 保存兩次inner、兩次outer的全部原receipt／argv／stdin／stdout／stderr／退出碼／環境／SHA／tools，原CONTROL_COMMIT及精確一行WITHDRAWAL.diff，以及完整私有source的目前恢復後 `{SOURCE}` bytes。僅 `.git` bookkeeping 未封；負控commit原物件文字與diff、原P2工具bytes也由當次原命令stdout保留。每個封包成員path／bytes／SHA-256均已解包核同，所有原command streams也按原收據核同。

`PUBLICATION.json`／`MEMBER_INVENTORY.json`／`EXCLUDED.json`明列範圍、退出碼與hash；沒有改動／釋放任何原raw、private source或main source，也沒有啟動測試、compiler、retry、commit或push。這份小proof不冒稱整份帳本／最終F七項驗收結果。
''', encoding='utf-8')
    files = [path for path in sorted(DEST.rglob('*')) if path.is_file()]
    assert all(path.stat().st_size < HARD_LIMIT for path in files)
    (DEST / 'SHA256SUMS').write_text(''.join(f'{digest_file(path)}  {path.relative_to(DEST).as_posix()}\n' for path in files), encoding='utf-8')
    # Update only the repository-external index; keep the earlier diagnostic outer 1 intact.
    index_path = BASE / 'FIX_PROOF_INDEX.json'
    index = load(index_path)
    entry = next(row for row in index['entries'] if row['id'] == 'assembly_cancel_mutation_anchor_repair')
    entry['fix_withdrawal_010'] = {'verified': True, 'exit_codes': [0, 1, 0], 'source_shas': [SOURCE, CONTROL, SOURCE],
         'scope': publication['scope'], 'phases': phases, 'negative_normal_assertion_failures': 2,
         'original_collector_inner_exit': 1, 'original_collector_outer_process_exit': 1,
         'completion_inner_exit': 0, 'completion_outer_process_exit': 0,
         'baseline_or_withdrawn_rerun': False, 'is_full_ASM_behavior_gate_rerun': False,
         'control_commit': reference(FIRST / 'CONTROL_COMMIT.txt'), 'control_diff': reference(FIRST / 'CONTROL_WITHDRAWAL.diff'),
         'staged_publication': reference(DEST / 'PUBLICATION.json')}
    entry['repair_proof_source_sha'] = SOURCE
    entry['limitations'] = [
         'The new proof runs all three original mutation-anchor methods; it does not rerun the complete ASM behavior gate.',
         'The earlier P3/E3 product mutation controls and recording-guard outer 1 remain a separate diagnostic scope.',
         'Attempt001 collector/outer exit1 is preserved; completion002 adds only the missing restored phase and does not rerun baseline/withdrawn.',
         'The new proof is at c4aad5d7, not the older E3 diagnostic checkout or an unexecuted final F.']
    entry['raw_receipts'].extend(reference(path) for path in (FIRST / 'receipt.json', COMPLETION / 'receipt.json',
         FIRST_OUTER / 'receipt.json', COMPLETION_OUTER / 'receipt.json', COMPLETION / 'ORIGINAL_WITHDRAWN_FINDING.json'))
    index['actual_gaps'] = [row for row in index['actual_gaps'] if row['id'] != 'assembly_anchor_fix_withdrawal']
    index['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    index['update_method'] = 'Read existing 001 and 002 raw receipts; preserve original collector1 and add only original restored0 to the already captured baseline0/withdrawn1.'
    index['index_update_collector'] = reference(Path(__file__))
    save(index_path, index)
    md_path = BASE / 'FIX_PROOF_INDEX.md'
    text = md_path.read_text()
    old_row = '| ASM cancelled-preview 工具舊anchor重錨 | 同P3／c0a20078 | **null：缺只撤anchor修正的控制** | 原完整工具0、unit12與anchors3均0；三產品mutants正常ASSERT killed與restored0不能取代anchor修正自證。 |'
    new_row = '| ASM cancelled-preview 工具舊anchor重錨 | 原診斷P3／c0a20078；修正自證c4aad5d7／負控238a5125 | **原anchor三方法真0/1/0** | 只撤一行舊anchor，2條正常AssertionError；001 collector/outer1保留，002只補restored0，無重抽／compiler；不是重跑完整ASM行為gate。 |'
    assert text.count(old_row) == 1
    text = text.replace(old_row, new_row)
    old_gap = '具體待補只有 ASM **anchor修正本身**的撤回證據。原完整工具的產品負控已存在，須保持兩者語意分開；不能以舊P2紅與P3綠串成0/1/0。'
    new_gap = 'ASM **anchor修正本身**的缺口已以原三方法、三態精確SHA與完整原raw補齊。001的原baseline0／withdrawn1沒有重抽，原collector／outer1仍保留；002只補缺失的restored0。與較早完整工具三個產品mutants／outer1分開，沒有拼接P2紅與P3綠，也不冒稱重跑完整ASM行為gate。封存見 `anchor-proof-publication-001/`。'
    assert text.count(old_gap) == 1
    md_path.write_text(text.replace(old_gap, new_gap), encoding='utf-8')
    print(json.dumps({'staging': str(DEST), 'schema': publication['schema'], 'archives': archives,
                      'member_count': len(selected), 'member_bytes': sum(row['bytes'] for row in selected),
                      'verified_command_streams': len(stream_paths), 'staging_files': len(files) + 1,
                      'staging_bytes': sum(path.stat().st_size for path in DEST.rglob('*') if path.is_file()),
                      'SHA256SUMS_sha256': digest_file(DEST / 'SHA256SUMS'),
                      'updated_index': reference(index_path), 'updated_short_index': reference(md_path)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
