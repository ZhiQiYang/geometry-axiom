"""跨分片核對原始執行收據，不接受缺片、漏跑、重複、數量漂移或假綠。"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess

from native_shards import partition_suites, profile_digest, validate_partition


def validate_rows(selected, rows, expected):
    wanted = Counter(selected)
    if any(n != 1 for n in wanted.values()) or Counter(row['name'] for row in rows) != wanted:
        raise ValueError('執行收據缺少或重複suite，不能當完整分片')
    for row in rows:
        for key in ['total', 'passed', 'failed', 'skipped', 'allowed_skips']:
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError('套件計數必須是非負整數：'+row['name'])
        if any(type(row[key]) is not bool for key in ['counted', 'ran', 'crashed', 'env_problem']):
            raise ValueError('套件狀態必須是布林值：'+row['name'])
        if type(row.get('process_exit_code')) is not int or row['process_exit_code'] != 0:
            raise ValueError('套件真實子行程退出碼未通過：'+row['name'])
        if (not row['ran'] or row['failed'] or row['crashed'] or row['env_problem'] or row['expected_problem']
                or not 0 <= row['allowed_skips'] <= row['skipped'] or row['skipped'] != row['allowed_skips']):
            raise ValueError('套件未嚴格通過：'+row['name'])
        registered = expected[row['name']]
        if row['counted']:
            if row['passed'] + row['skipped'] != row['total']:
                raise ValueError('套件計數不守恆：'+row['name'])
            if registered['mode'] != 'count' or row['total'] != registered['count']:
                raise ValueError('套件expected數量不符：'+row['name'])
        else:
            # The original mutation inventory deliberately counts no assertions.
            # Preserve its zero counters and require the actual child exit above.
            wanted_passed = 0 if row['name'] == 'mutation:check' else 1
            if (registered['mode'] != 'exit-code-only' or row['passed'] != wanted_passed
                    or row['total'] != 0 or row['skipped'] != 0):
                raise ValueError('僅退出碼套件未通過：'+row['name'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--parts', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import run_all
    registry_errors = run_all.check_registry()
    if registry_errors:
        raise ValueError(registry_errors)
    suites = run_all.build_suites()
    expected, error = run_all.load_expected()
    if error or set(expected['suites']) != {s.name for s in suites}:
        raise ValueError('完整登記／expected清單不相等：'+error)
    plans = partition_suites(suites, args.parts)
    validate_partition(suites, plans)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    expected_sha = hashlib.sha256(run_all.EXPECTED_FILE.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    paths = sorted(args.input.glob('shard-*.json'))
    if len(paths) != args.parts:
        raise ValueError('缺少原始分片收據')
    seen, rows = set(), []
    for path in paths:
        report = json.loads(path.read_text(encoding='utf-8'))
        index, count = report['shard']
        if (report['schema'] != 'geometry-native-shard/1' or count != args.parts or index in seen
                or not 1 <= index <= count or report['commit_sha'] != head
                or report['expected_sha256'] != expected_sha or report['timings_sha256'] != profile_digest()
                or not isinstance(report['seconds'], (int, float)) or not math.isfinite(report['seconds'])
                or not 0 <= report['seconds'] < 1200
                or report['exit_code'] != 0 or report['registry_errors'] or report['expected_problems']
                or report['universe'] != [s.name for s in suites]
                or report['selected'] != [s.name for s in plans[index-1]]):
            raise ValueError('分片身分／規劃／真實退出不符：'+str(path))
        validate_rows(report['selected'], report['rows'], expected['suites'])
        seen.add(index)
        rows.extend(report['rows'])
    validate_rows([s.name for s in suites], rows, expected['suites'])
    result = dict(passed=True, commit_sha=head, parts=args.parts, suite_count=len(suites),
                  executed_suites=len(rows), union_equals_full_registry=True, overlap=[],
                  counted_tests=sum(r['total'] for r in rows if r['counted']),
                  counted_passed=sum(r['passed'] for r in rows if r['counted']),
                  allowed_skips=sum(r['allowed_skips'] for r in rows),
                  shard_suites={str(i+1):len(part) for i,part in enumerate(plans)},
                  expected_sha256=expected_sha, timings_sha256=profile_digest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
