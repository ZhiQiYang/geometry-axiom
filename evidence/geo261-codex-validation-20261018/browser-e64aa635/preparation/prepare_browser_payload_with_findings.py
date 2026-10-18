#!/usr/bin/env python3
"""只封存六個 final browser job 的原始證據；不跑產品、測試或 Git。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


BASE = Path('/workspace/geo261-validation-20261018')
SOURCE = BASE / 'browser-e64aa635'
REPO = Path('/workspace/geometry-axiom')
TESTED = 'e64aa6359d600f43313ec9d7ba1112c465b6a40c'
TOPIC = 'geo261-codex-validation-20261018'
PHASE = 'browser-e64aa635'
CONTRACT_HASH = 'e587f5e4717b6b8fa743fc638b8939202a67d91643d00725a08389b43941d277'
PARSER_HASH = 'ee76fbc6dbd5c59fa4f6157c91bab2e161a43dbae1f74aa9ce5dc6026213b2a7'
JOBS = ('canvas', 'assembly', 'documents', 'grid', 'space', 'timber')
MINUTES = (35, 15, 10, 15, 15, 20)
FIXED = ('environment.json', 'summary.json', 'browser-stage-report.md', 'browser-stage-results.json',
         'browser-stage-findings.md', 'browser-stage-findings.json')
# 六 job final 且附記獨立審查後才填入；PENDING 狀態禁止執行打包。
FINDINGS_HASHES = {'browser-stage-findings.md': '519a0327a8035455d9b11e6f5b20e90aa3b0dc969b779c2fc46f853892923373',
                   'browser-stage-findings.json': '1fb49ee537bf2ee7cb310ecd20b35a995bc5dd0b2e213fe9d028a9052575c1d0'}
LOGS = {'build.log', 'runtime-probe.log', 'runtime-final-probe.log', 'server.log', 'test.log'}
CANVAS_LOGS = {'prepare-wait-trace.log', 'archive-wait-trace.log'}
TRACE = {'receipt.json', 'wait-trace.jsonl'}
DATA_SUFFIXES = {'.json', '.jsonl', '.scene', '.gcanvas', '.zip', '.pdf', '.png', '.jpg', '.jpeg',
                 '.webp', '.gif', '.svg', '.html', '.txt', '.md', '.log', '.csv'}
BINARY_SUFFIXES = {'.exe', '.dll', '.so', '.dylib', '.node', '.o', '.a', '.lib', '.pdb', '.pyc'}
ROOT_XDG = {'cache', 'config', 'data'}
PRIVATE_COMPONENTS = {'chrome-profile', 'node-compile-cache', '.cache', '.config', '.aws', '.ssh', '.git', '.codex'}
PRIVATE_NAMES = {'Cookies', 'Cookies-journal', 'Login Data', 'Login Data-journal', 'Local State',
                 'Web Data', 'Web Data-journal', 'credentials', 'credentials.json', '.netrc', '.env'}
PROFILE_PREFIXES = ('geometry-documents-chrome-', 'geometry-cdp-', 'com.google.Chrome.', '.com.google.Chrome.')
SECRET = re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}|'
                    rb'gh[pousr]_[A-Za-z0-9]{20,}|Authorization\s*:\s*(?:Bearer|Basic)\s+\S+', re.I)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'JSON 重複 key：' + key)
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)


def relative_name(value):
    require(isinstance(value, str) and value and '\\' not in value and '\x00' not in value,
            '不合法相對檔名')
    name = PurePosixPath(value)
    require(not name.is_absolute() and all(p not in ('', '.', '..') for p in value.split('/'))
            and name.as_posix() == value, '非正規相對檔名：' + value)
    return name


def read_regular(path, *, public=True):
    require(path.is_absolute() and path.resolve() == path, '證據路徑包含 symlink：' + str(path))
    require(stat.S_ISREG(path.lstat().st_mode), '證據不是一般檔案：' + str(path))
    require(path.stat().st_size < 95 * 1024 * 1024, '單檔需另審封存方式：' + str(path))
    raw = path.read_bytes()
    if public:
        require(not SECRET.search(raw), '疑似憑證；拒絕整包且不輸出內容：' + str(path))
    return raw


def timestamp(value):
    require(isinstance(value, str), '缺少完成時間')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, '時間未含時區')
    return result


def artifact_classification(name, raw):
    """只接受 runner manifest 的逐檔候選；未知資料種類拒絕，不靜默略過。"""
    parts = relative_name(name).parts
    suffix = PurePosixPath(name).suffix.lower()
    if parts[0] in ROOT_XDG or any(part in PRIVATE_COMPONENTS or part in PRIVATE_NAMES or part.startswith(PROFILE_PREFIXES)
                                  for part in parts):
        return False, 'profile／cache／憑證路徑；只保留原 runner manifest 的 hash'
    if parts[-1] in {'build.lock', 'SingletonLock', 'SingletonSocket', 'SingletonCookie'}:
        return False, '鎖或 socket 身分；不發布執行期產物'
    binary_magic = raw.startswith((b'\x7fELF', b'MZ', b'!<arch>\n', b'\xfe\xed\xfa\xce',
                                   b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe'))
    if suffix in BINARY_SUFFIXES or binary_magic:
        return False, '編譯 binary／object；不發布二進位檔'
    if parts[0] == 'geometry-runtime':
        require((suffix == '.json' and parts[-1].endswith('.fingerprint.json')) or
                (suffix == '.scene' and 'smoke' in parts), '未知 runtime artifact，須另審：' + name)
        return True, 'runner 建置指紋或 smoke 場景資料'
    if parts[0] == 'screens':
        require(suffix in {'.png', '.jpg', '.jpeg', '.webp'}, 'screens 非圖片，須另審：' + name)
        return True, '實際瀏覽器 screenshot'
    if parts[0] in {'feedback', 'space-results', 'evidence-results', 'downloads', 'geometry-tests'}:
        require(suffix in DATA_SUFFIXES, '未知 harness 證據副檔名：' + name)
        return True, 'runner 隔離目錄內的 harness 證據／專案／原始資料'
    if parts[0].startswith('geometry-') and len(parts) > 1:
        require(suffix in DATA_SUFFIXES, '未知 geometry harness 暫存資料：' + name)
        return True, 'runner 隔離的 harness fixture／匯出專案'
    if len(parts) == 1 and suffix in DATA_SUFFIXES:
        require(parts[0].startswith(('tmp', 'verify-upload-', 'geometry-')),
                '未知根目錄 artifact，須逐項審查：' + name)
        return True, 'runner 根目錄的具名場景／fixture'
    raise ValueError('runner 新 artifact 未列入可分享類型，須逐項審查：' + name)


def collect():
    entries = {}
    excluded = []
    archival_issues = []

    def add(path, target, kind, expected=None):
        relative_name(target)
        raw = read_regular(path)
        item = {'path': target, 'bytes': len(raw), 'sha256': sha(raw),
                'original_path': str(path), 'kind': kind}
        if expected is not None:
            require(item['bytes'] == expected.get('bytes') and item['sha256'] == expected.get('sha256'),
                    '原文 bytes／hash 與 final 收據不同：' + str(path))
        if target in entries:
            require(entries[target] == item, '同一路徑出現矛盾收據：' + target)
        else:
            entries[target] = item
        return raw

    raw = {name: add(SOURCE / name, PHASE + '/' + name, 'final phase report／runner metadata')
           for name in FIXED}
    env, summary, doc = (parse(raw[name]) for name in
                         ('environment.json', 'summary.json', 'browser-stage-results.json'))
    require(doc.get('schema') == 'geo261-browser-stage-report/1', '不是固定 phase2 報告 schema')
    require(doc.get('source_sha') == TESTED and summary.get('expected_sha') == TESTED
            and env.get('source', {}).get('sha') == TESTED, 'phase2 測試來源不符')
    require(summary.get('ordered_suites') == list(JOBS) and len(summary.get('results', [])) == 6,
            '不是六 job 完整 runner 收據')
    require(summary.get('all_passed') == all(r.get('status') == 'passed' for r in summary['results']),
            'runner all_passed 與六份原始狀態不符')
    require(not summary.get('interrupted') and doc.get('all_jobs_finished') is True
            and doc.get('runner_finished') is True, 'partial／interrupted 報告禁止打包')
    require(timestamp(summary['ended_utc']) >= timestamp(summary['started_utc']), 'runner 時間倒置')
    require(timestamp(doc['generated_utc']) >= timestamp(summary['ended_utc']), '報告早於 runner 結束')
    require(doc.get('runner_summary') == summary and doc.get('environment') == env, '最終報告與原 metadata 不一致')
    require([row.get('job') for row in doc.get('jobs', [])] == list(JOBS), 'final report job 集合／順序不符')
    report = raw['browser-stage-report.md'].decode('utf-8')
    require('六個 job 已有終止收據。' in report and '此為進度報告' not in report and TESTED in report,
            '文字報告仍為 partial 或 SHA 不符')
    # 新版只新增兩份公開人工診斷附記；原始報告、raw、artifact 的守門完全保留。
    for name, expected in FINDINGS_HASHES.items():
        require(re.fullmatch(r'[0-9a-f]{64}', expected) is not None and sha(raw[name]) == expected,
                '診斷附記尚未 final review 或 bytes 改變：' + name)
    findings = parse(raw['browser-stage-findings.json'])
    require(findings.get('schema') == 'geo261-browser-stage-findings/1'
            and findings.get('source_sha') == TESTED and findings.get('all_jobs_finished') is True,
            '診斷附記 schema／測試來源／完整性不符')
    require(timestamp(findings['generated_utc']) >= timestamp(doc['generated_utc']), '診斷附記早於 final 報告')
    require(findings.get('applied_fixes') == [], '原始基準不得宣稱本階段已套修正')
    expected_reports = [{'relative_path': name, 'bytes': len(raw[name]), 'sha256': sha(raw[name])}
                        for name in ('browser-stage-report.md', 'browser-stage-results.json')]
    require(findings.get('report_evidence') == expected_reports, '附記未鎖定本次 final 報告 hash')
    require([row.get('job') for row in findings.get('jobs', [])] == list(JOBS), '附記 job 集合／順序不符')
    for note, observed in zip(findings['jobs'], doc['jobs']):
        name = observed['job']
        for key in ('job', 'status', 'verified_pass', 'harness_completed', 'harness_exit_code', 'timed_out',
                    'work_elapsed_seconds', 'elapsed_seconds', 'passed_assertions', 'failed_assertions',
                    'fatal', 'evidence_issues'):
            require(note.get(key) == observed.get(key), '附記改寫原始觀測值：' + name + '/' + key)
        expected_raw = [item for item in observed['raw_files']
                        if item['relative_path'] in (name + '/test.log', name + '/result.json')]
        require(note.get('raw_evidence') == expected_raw, '附記的 test/result 原始 hash 不符：' + name)
        require(note.get('fix_branch') is None and note.get('fix_sha') is None
                and note.get('after_fix_verified') is False and note.get('mutation_verified') is False,
                '原始基準附記不得宣稱修後／突變已驗：' + name)
    findings_text = raw['browser-stage-findings.md'].decode('utf-8')
    require(TESTED in findings_text and '原始基準' in findings_text, '公開文字附記未明列來源及基準範圍')
    contract_raw = add(BASE / 'browser-harness-contract-e64aa635.json',
                       PHASE + '/preparation/browser-harness-contract-e64aa635.json', '固定 harness 契約快照')
    require(sha(contract_raw) == CONTRACT_HASH == doc.get('harness_contract_sha256')
            and parse(contract_raw) == doc.get('harness_contract'), '固定 harness 契約不符')
    metadata = {row['relative_path']: row for row in doc.get('metadata_evidence', [])}
    require(set(metadata) == {'environment.json', 'summary.json'}, 'metadata hash 白名單不符')
    for name, evidence in metadata.items():
        require(evidence['bytes'] == len(raw[name]) and evidence['sha256'] == sha(raw[name]), 'metadata hash 不符：' + name)
    for name, minutes, row, stored in zip(JOBS, MINUTES, doc['jobs'], summary['results']):
        directory = SOURCE / name
        result_raw = read_regular(directory / 'result.json')
        result = parse(result_raw)
        require(result == stored and result.get('suite') == name, 'summary／result 身分不一致：' + name)
        require(row.get('job_finished') is True and result.get('status') not in {'running', 'not_started', 'interrupted'},
                'job 尚未 final：' + name)
        require(timestamp(result['ended_utc']) >= timestamp(result['started_utc'])
                and timestamp(result['ended_utc']) <= timestamp(summary['ended_utc']), 'job 時間不完整：' + name)
        require(row.get('ci_timeout_minutes') == result.get('ci_timeout_minutes') == minutes,
                '原 job 時限不同：' + name)
        require(row.get('expected_sha') == TESTED and result.get('source_unchanged') is True,
                'job 未證實測試來源不變：' + name)
        for key in ('source_before', 'source_after'):
            state = result.get(key, {})
            require(state.get('sha') == TESTED and state.get('status') == '' and state.get('tracked_changes') == [],
                    'job 來源不是固定乾淨提交：' + name)
        for key in ('started_utc', 'ended_utc', 'harness_exit_code', 'timed_out', 'steps', 'server',
                    'source_before', 'source_after', 'source_unchanged', 'initial_server_ownership',
                    'final_server_ownership', 'artifact_archive'):
            require(row.get(key) == result.get(key), 'final 報告改寫原 job 欄位：' + name + '/' + key)
        require(row.get('actual_environment') == result.get('environment'), 'job 環境不同：' + name)
        allowed_status = result['status']
        if allowed_status == 'passed' and row.get('verified_pass') is not True:
            allowed_status = 'receipt_incomplete'
        require(row.get('status') == allowed_status, '報告狀態不是原始狀態或合法收據降級：' + name)
        if row.get('verified_pass') is True:
            require(result.get('status') == 'passed' and result.get('harness_exit_code') == 0
                    and result.get('timed_out') is False and row.get('harness_completed') is True
                    and row.get('failed_assertions') == 0 and row.get('passed_assertions', 0) > 0
                    and row.get('evidence_issues') == [] and row.get('runtime_evidence_issues') == [],
                    'verified_pass 沒有一致完整的成功收據：' + name)
        allowed_logs = LOGS | (CANVAS_LOGS if name == 'canvas' else set())
        listed = {}
        for item in row.get('raw_files', []):
            relative = item.get('relative_path')
            parts = relative_name(relative).parts
            allowed = (len(parts) == 2 and parts[0] == name and
                       (parts[1] in allowed_logs or parts[1] in {'result.json', 'artifact-manifest.json'}))
            allowed = allowed or relative == name + '/artifacts/space-results/result.json'
            require(allowed and relative not in listed, 'raw log 不在精確白名單或重複：' + str(relative))
            listed[relative] = item
            add(SOURCE / relative, PHASE + '/' + relative, 'job 原始收據／log', item)
        require(name + '/result.json' in listed and name + '/artifact-manifest.json' in listed,
                'job 缺 final result 或 artifact manifest：' + name)
        prefix = 'DOCUMENTS_RESULT' if name == 'documents' else ('SPACE_RESULT' if name in {'space', 'timber'} else 'CDP_RESULT')
        log_path = directory / 'test.log'
        log_lines = read_regular(log_path).decode('utf-8', errors='replace').splitlines() if log_path.exists() else []
        markers = []
        for number, line in enumerate(log_lines, 1):
            if line.startswith(prefix + ' '):
                try:
                    value = json.loads(line[len(prefix) + 1:])
                except ValueError:
                    continue  # malformed 原文仍留在 log；不是有效 completion marker。
                markers.append({'line': number, 'original': line, 'value': value})
        require(row.get('completion_markers') == markers, 'completion markers 不是 test.log 的原文：' + name)
        actual_logs = {p.name for p in directory.iterdir() if p.suffix == '.log'}
        require(actual_logs <= allowed_logs and
                {name + '/' + f for f in actual_logs} <= set(listed), '實際 job log 未全部列入報告：' + name)
        for step in result.get('steps', []):
            log_path = Path(step['log'])
            require(log_path.parent == directory and log_path.name in allowed_logs, 'step log 路徑越界：' + name)
            require(step.get('ended_utc'), 'step 尚未終止：' + name)
            if not step.get('not_started') and not step.get('launch_error'):
                require(name + '/' + log_path.name in listed, '已執行 step 缺 log：' + name)
        if result.get('server'):
            require(result['server'].get('log') == str(directory / 'server.log')
                    and name + '/server.log' in listed and result['server'].get('ended_utc'), 'server log／清理收據不完整：' + name)
        archive = parse(read_regular(directory / 'artifact-manifest.json'))
        receipt = result.get('artifact_archive', {})
        require(receipt.get('manifest') == str(directory / 'artifact-manifest.json')
                and receipt.get('path') == archive.get('destination') == str(directory / 'artifacts'),
                'artifact 封存路徑不符：' + name)
        require(archive.get('errors') == receipt.get('errors'), 'artifact errors 收據不同：' + name)
        require(archive.get('ended_utc') and archive.get('source_tmp_directory') == receipt.get('source_tmp_directory'),
                'artifact 封存尚未結束或來源不符：' + name)
        files = archive.get('files', [])
        require(type(files) is list and len(files) == receipt.get('file_count') == row.get('archived_file_count')
                == row.get('archive_files_hash_verified'), 'artifact 完整 hash 核對計數不符：' + name)
        require(sum(item['bytes'] for item in files) == receipt.get('bytes'), 'artifact byte 合計不符：' + name)
        manifest_item = row.get('archive_manifest', {})
        archive_bytes = read_regular(directory / 'artifact-manifest.json')
        require(manifest_item.get('relative_path') == name + '/artifact-manifest.json'
                and manifest_item.get('sha256') == sha(archive_bytes) and manifest_item.get('bytes') == len(archive_bytes),
                'artifact manifest hash 不符：' + name)
        seen = set()
        for item in files:
            relative = item['path']
            relative_name(relative)
            require(relative not in seen, 'artifact 路徑重複：' + name + '/' + relative)
            seen.add(relative)
            path = directory / 'artifacts' / relative
            data = read_regular(path, public=False)
            require(len(data) == item['bytes'] and sha(data) == item['sha256'], 'artifact 原文 hash 不符：' + str(path))
            include, reason = artifact_classification(relative, data)
            if include:
                target = PHASE + '/' + name + '/artifacts/' + relative
                # 某些 result.json 同時列入 row.raw_files，保留同一份 bytes。
                if target in entries:
                    require(entries[target]['sha256'] == item['sha256'] and entries[target]['bytes'] == item['bytes'],
                            'artifact 雙收據矛盾：' + relative)
                else:
                    add(path, target, reason, item)
            else:
                excluded.append({'job': name, 'path': relative, 'bytes': item['bytes'], 'sha256': item['sha256'],
                                 'original_path': str(path), 'reason': reason})
        artifact_root = directory / 'artifacts'
        require(not artifact_root.is_symlink(), 'artifact root 是 symlink')
        actual = set()
        for current, dirs, names in os.walk(artifact_root, followlinks=False):
            for basename in dirs:
                require(not (Path(current) / basename).is_symlink(), 'artifact 含 symlink 目錄')
            for basename in names:
                path = Path(current) / basename
                require(stat.S_ISREG(path.lstat().st_mode), 'artifact 含非一般檔案：' + str(path))
                actual.add(path.relative_to(artifact_root).as_posix())
        require(actual == seen, 'artifacts 實體檔案集合與 runner manifest 不符：' + name)
        if archive.get('errors') or row.get('evidence_issues'):
            archival_issues.append({'job': name, 'archive_errors': archive.get('errors'),
                                    'report_evidence_issues': row.get('evidence_issues')})
        if name == 'canvas':
            traces = row.get('wait_trace_files', [])
            trace_seen = set()
            for item in traces:
                relative = item['relative_path']
                parts = relative_name(relative).parts
                require(len(parts) == 3 and parts[:2] == ('canvas', 'wait-trace-artifact')
                        and parts[2] in TRACE and relative not in trace_seen, '未知 wait trace 檔案')
                trace_seen.add(relative)
                add(SOURCE / relative, PHASE + '/' + relative, 'canvas wait trace 原始收據', item)
            require('canvas/wait-trace-artifact/receipt.json' in trace_seen, 'canvas 缺 wait trace 終止收據')
            trace_root = directory / 'wait-trace-artifact'
            require({p.relative_to(SOURCE).as_posix() for p in trace_root.iterdir()} == trace_seen,
                    'wait trace 實體集合與報告不同')
    require(doc.get('all_verified_passed') == all(row.get('verified_pass') is True for row in doc['jobs']),
            '最終 verified_pass 合計不一致')
    for name in ('run_browser_jobs.py', 'build_browser_report.py'):
        script = add(BASE / name, PHASE + '/preparation/' + name, '準備腳本目前 bytes；不是 execution-start loaded-byte 證明')
        if name == 'build_browser_report.py':
            require(sha(script) == PARSER_HASH, '已審 baseline parser bytes 改變；須另審新版，不能冒用')
    add(Path(__file__).absolute(), PHASE + '/preparation/prepare_browser_payload_with_findings.py', '本次封存 helper（明列新增兩份診斷附記）')
    return entries, excluded, archival_issues, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path, help='checkout／來源外、不存在的新 payload 目錄')
    args = parser.parse_args()
    out = args.out.absolute()
    require(out.resolve() == out and not out.exists() and not out.is_relative_to(REPO)
            and not out.is_relative_to(SOURCE), '輸出必須無 symlink、不存在且位於 checkout／來源外')
    entries, excluded, issues, doc = collect()
    # 先讀完並核全部 final 收據；任何 partial 或未審 artifact 都不會建立 payload。
    for items, public in ((entries.values(), True), (excluded, False)):
        for item in items:
            data = read_regular(Path(item['original_path']), public=public)
            require(len(data) == item['bytes'] and sha(data) == item['sha256'], '準備期間來源改變：' + item['original_path'])
    out.mkdir(parents=True, exist_ok=False)
    target = out / 'evidence' / TOPIC
    target.mkdir(parents=True)
    for name, item in sorted(entries.items()):
        data = read_regular(Path(item['original_path']))
        require(len(data) == item['bytes'] and sha(data) == item['sha256'], '複製時來源改變：' + item['original_path'])
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    manifest = {'schema': 'geo261-browser-baseline-publication/1', 'tested_source_sha': TESTED,
                'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
                'publication_state': '僅外部 payload；未提交、未推送、未留言',
                'runner_started_utc': doc['runner_summary']['started_utc'],
                'runner_ended_utc': doc['runner_summary']['ended_utc'],
                'all_jobs_finished': True, 'all_verified_passed': doc['all_verified_passed'],
                'jobs': [{'job': r['job'], 'status': r['status'], 'verified_pass': r['verified_pass'],
                          'harness_completed': r['harness_completed']} for r in doc['jobs']],
                'files': sorted(entries.values(), key=lambda item: item['path']),
                'excluded_runner_artifacts': excluded, 'original_evidence_issues': issues,
                'limits': ['保留真實失敗／timeout，不要求全綠；job final 不等於 harness 全部完成。',
                           '原 runner artifact manifest 原 bytes 保留；binary/cache/credentials 只留 hash 與排除理由。',
                           '附錄準備腳本是封存時 bytes；沒有據此補稱 execution-start 載入 bytes。',
                           '不包含 Chrome profile、node compile cache、socket、binary 或憑證。']}
    for item in manifest['files']:
        data = read_regular(target / item['path'])
        require(sha(data) == item['sha256'] and len(data) == item['bytes'], 'payload 複製後 hash 不符')
    for items, public in ((entries.values(), True), (excluded, False)):
        for item in items:
            data = read_regular(Path(item['original_path']), public=public)
            require(len(data) == item['bytes'] and sha(data) == item['sha256'], '封存前來源改變：' + item['original_path'])
    # 只在全部 copy 與 hash 成功後產生 seal；沒有此 manifest 的目錄一律不是可發布 payload。
    manifest_path = target / PHASE / 'publication-manifest.json'
    with manifest_path.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'payload': str(out), 'manifest': str(manifest_path), 'files': len(entries),
                      'excluded_runner_artifacts': len(excluded), 'all_jobs_finished': True,
                      'all_verified_passed': doc['all_verified_passed']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
