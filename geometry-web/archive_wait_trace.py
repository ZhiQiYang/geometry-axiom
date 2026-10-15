"""Preserve an isolated runner's raw wait trace, even after a failed canvas job."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def main(destination):
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=True)
    copied = target / 'wait-trace.jsonl'
    copied.unlink(missing_ok=True)
    keys = ('GEOMETRY_WAIT_TRACE', 'GEOMETRY_FEEDBACK_DIR', 'GEOMETRY_BROWSER_SUITE', 'GEOMETRY_WAIT_TRACE_RUN_ID')
    environment = {key: os.environ.get(key) for key in keys}
    enabled = environment['GEOMETRY_WAIT_TRACE'] == '1'
    directory = environment['GEOMETRY_FEEDBACK_DIR']
    source = Path(directory) / 'wait-trace.jsonl' if directory else None
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
    receipt = {'effectiveEnvironment': environment, 'kernel': platform.release(),
               'platform': platform.system(), 'head': head.stdout.strip() if head.returncode == 0 else None,
               'status': 'trace-disabled-for-this-runner', 'records': 0}
    status = 0
    if enabled:
        receipt['status'] = 'missing-enabled-trace'
        status = 1
        if source and source.is_file():
            shutil.copyfile(source, copied)
            raw = copied.read_bytes()
            receipt.update(status='archived', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), records=len(raw.splitlines()))
            status = 0 if raw else 1
            if not raw:
                receipt['status'] = 'empty-enabled-trace'
            else:
                try:
                    rows = [json.loads(line) for line in raw.splitlines()]
                    run_id = environment['GEOMETRY_WAIT_TRACE_RUN_ID']
                    complete = rows[-1]
                    begun = {r['traceRequestId'] for r in rows if r['stage'] == 'request_begin'}
                    ended = {r['traceRequestId'] for r in rows if r['stage'] == 'request_end'}
                    count_keys = ('droppedEvents', 'writeErrors', 'writtenEvents', 'acceptedEvents')
                    valid_counts = all(type(complete.get(key)) is int and complete[key] >= 0 for key in count_keys)
                    valid = (valid_counts and run_id and all(r.get('traceRunId') == run_id for r in rows)
                             and rows[0]['stage'] == 'trace_start' and complete['stage'] == 'trace_complete'
                             and complete.get('incomplete') is False
                             and complete['droppedEvents'] == 0 and complete['writeErrors'] == 0
                             and complete['writtenEvents'] == len(rows)-1 and begun == ended)
                    valid = valid and complete['acceptedEvents']+1 == complete['writtenEvents']
                    receipt.update(traceRunId=run_id, unfinishedRequests=sorted(begun-ended))
                    if not valid:
                        receipt['status'] = 'incomplete-or-mixed-trace'
                        status = 1
                except (ValueError, KeyError, TypeError):
                    receipt['status'] = 'invalid-trace'
                    status = 1
    (target / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
