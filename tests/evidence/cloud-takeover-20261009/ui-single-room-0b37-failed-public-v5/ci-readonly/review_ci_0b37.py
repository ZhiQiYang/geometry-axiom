"""Single-pass read-only GitHub REST CI evidence; no retry or mutation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parent / 'pr179-ci-0b37-readonly'
SHA = '0b37d8d8d4ee501fe6208e3e88440b3d078d7c0b'
API = 'https://api.github.com/repos/ZhiQiYang/geometry-axiom'
RUN = 37951128952

def digest(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def fetch(pair):
    name, url = pair
    try:
        with urlopen(Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Geometry-readonly-closeout'}), timeout=20) as response:
            raw = response.read(); status = response.status
        path = OUT / (name + '.raw.json'); path.write_bytes(raw)
        return {'name': name, 'url': url, 'readUtc': now(), 'httpStatus': status, 'path': path.name,
                'sha256': digest(raw), 'bytes': len(raw), 'result': json.loads(raw)}
    except Exception as error:
        path = OUT / (name + '.error.txt'); raw = (repr(error) + '\n').encode(); path.write_bytes(raw)
        return {'name': name, 'url': url, 'readUtc': now(), 'error': repr(error), 'path': path.name,
                'sha256': digest(raw), 'bytes': len(raw), 'result': None}

def main():
    assert not OUT.exists(); OUT.mkdir()
    start = now()
    with ThreadPoolExecutor(max_workers=3) as pool:
        initial = list(pool.map(fetch, [('pull-179', API + '/pulls/179'), ('run-' + str(RUN), API + '/actions/runs/' + str(RUN)),
                                      ('jobs-' + str(RUN), API + '/actions/runs/' + str(RUN) + '/jobs?per_page=100')]))
    records = {r['name']: r for r in initial}
    jobs_raw = records['jobs-' + str(RUN)]['result']; run = records['run-' + str(RUN)]['result']; pr = records['pull-179']['result']
    jobs = [] if jobs_raw is None else jobs_raw['jobs']
    with ThreadPoolExecutor(max_workers=7) as pool:
        annotations = list(pool.map(fetch, [('annotations-' + str(job['id']), job['check_run_url'] + '/annotations?per_page=100') for job in jobs]))
    valid = bool(run and jobs_raw and pr and run['head_sha'] == SHA and pr['head']['sha'] == SHA and jobs_raw['total_count'] == len(jobs) == 7
                 and all(job['head_sha'] == SHA for job in jobs))
    unexecuted = valid and all(job['runner_id'] == 0 and job['runner_name'] == '' and job['steps'] == [] for job in jobs)
    messages = [entry.get('message') for record in annotations if record['result'] is not None for entry in record['result']]
    report = {'schema': 'geometry-ci-readonly/1', 'actor': '/root/delivery_closeout', 'source': 'GitHub REST unauthenticated public GET, each recorded endpoint once, no retry',
              'startedUtc': start, 'finishedUtc': now(), 'head': SHA, 'runId': RUN, 'command': [sys.executable, str(Path(__file__).resolve())],
              'scriptSha256': digest(Path(__file__).read_bytes()), 'runAndPrAndJobsSameExactHead': valid, 'allSevenJobsUnexecuted': unexecuted,
              'status': 'unexecuted' if unexecuted else 'unknown', 'jobs': [{k:job.get(k) for k in ['id','name','head_sha','runner_id','runner_name','steps','conclusion','check_run_url']} for job in jobs],
              'annotationMessages': messages, 'rawRecords': [{k:v for k,v in record.items() if k != 'result'} for record in initial + annotations],
              'limitations': ['Zero runner/steps means no product CI execution; job failure is not a test assertion result.', 'No retry, merge, deploy, account/security edits or review/comment writes.']}
    path = OUT / 'report.json'; path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'out':str(OUT), 'head':SHA, 'status':report['status'], 'annotationCount':len(messages), 'errors':[r['name'] for r in initial+annotations if r.get('error')], 'reportSha256':digest(path.read_bytes())}))

if __name__ == '__main__': main()
