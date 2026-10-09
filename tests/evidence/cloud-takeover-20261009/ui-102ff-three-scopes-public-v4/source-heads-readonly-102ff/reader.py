"""Read each requested GitHub PR/main source endpoint once; no mutation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parent / 'source-heads-102ff-readonly'
API = 'https://api.github.com/repos/ZhiQiYang/geometry-axiom'
assert not OUT.exists()
OUT.mkdir()
def now(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def fetch(pair):
    label, url = pair
    started = now()
    try:
        with urlopen(Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Geometry-source-readonly-closeout'}), timeout=20) as response:
            raw = response.read()
            status = response.status
        path = OUT / (label + '.raw.json')
        path.write_bytes(raw)
        result = json.loads(raw)
        observation = {'head': result['commit']['sha'], 'branch': 'main'} if label == 'main' else {
            'head': result['head']['sha'], 'branch': result['head']['ref'], 'base': result['base']['ref'],
            'baseSHA': result['base']['sha'], 'state': result['state'], 'draft': result['draft'], 'merged': result['merged']}
        return {'label': label, 'endpoint': url, 'startedUtc': started, 'finishedUtc': now(), 'httpStatus': status,
                'originalRawPath': str(path), 'originalRawSha256': sha(raw), 'bytes': len(raw), 'observation': observation}
    except Exception as error:
        raw = (repr(error) + '\n').encode()
        path = OUT / (label + '.error.txt')
        path.write_bytes(raw)
        return {'label': label, 'endpoint': url, 'startedUtc': started, 'finishedUtc': now(), 'error': repr(error),
                'originalRawPath': str(path), 'originalRawSha256': sha(raw), 'bytes': len(raw), 'observation': {'status': 'unknown'}}

started = now()
queries = [('pr-' + str(number), API + '/pulls/' + str(number)) for number in [171, 173, 175, 176, 169, 177, 178, 179]] + [('main', API + '/branches/main')]
with ThreadPoolExecutor(max_workers=9) as pool:
    records = list(pool.map(fetch, queries))
report = {'schema': 'geometry-source-heads-readonly/1', 'actor': '/root/delivery_closeout', 'source': 'GitHub REST public GET, each endpoint once without retry',
          'startedUtc': started, 'finishedUtc': now(), 'records': records, 'command': [sys.executable, str(Path(__file__).resolve())],
          'readerSha256': sha(Path(__file__).read_bytes()), 'actualPython': {'pid': os.getpid(), 'path': str(Path('/proc/self/exe').resolve()),
           'sha256': sha(Path('/proc/self/exe').read_bytes()), 'version': sys.version}, 'exitCode': 0, 'productTestsExecuted': False,
          'repositoryOrRemoteWrites': False, 'handoff': 'Prior local writers already stopped; this read does not require another release.',
          'limitations': ['Snapshot head read times are per-endpoint observations, not a transaction.', 'No issue/review/comment changes; #168 cancellation and #169 pending review left unchanged.']}
path = OUT / 'report.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(path), 'reportSha256': sha(path.read_bytes()), 'startedUtc': started, 'finishedUtc': report['finishedUtc'],
                  'observations': [{'label': r['label'], 'time': r['finishedUtc'], **r['observation']} for r in records]}, ensure_ascii=False))
