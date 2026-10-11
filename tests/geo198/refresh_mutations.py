"""Refresh the native mutation inventory using four independent TEMP caches.

Workers have disjoint mutation ids, result files and baseline caches. Source
files must remain unchanged throughout the run. No test/verification is disabled.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tests'))
import mutate


def main():
    evidence = Path(sys.argv[1]).resolve()
    evidence.mkdir(parents=True,exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='geo198-mutations-'))
    ids = [m['id'] for m in mutate.MUTANTS]
    assert len(ids)==len(set(ids))
    groups = [ids[i::4] for i in range(4)]

    def worker(index):
        result_file = scratch/f'worker-{index}.json'
        log_file = evidence/f'worker-{index}.log'
        env = dict(os.environ,MUTATE_CACHE=str(scratch/f'cache-{index}'),MUTATE_RESULTS=str(result_file))
        argv = [sys.executable,'-u','tests/mutate.py',*groups[index]]
        started = time.monotonic()
        with log_file.open('wb') as log:
            proc = subprocess.run(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        return {'index':index,'ids':groups[index],'argv':argv,'cwd':str(ROOT),
                'exit':proc.returncode,'seconds':time.monotonic()-started,
                'log_sha256':hashlib.sha256(log_file.read_bytes()).hexdigest()},mutate.load_records(result_file)

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(worker,range(4)))
    merged = {}
    for _, records in rows:
        assert not set(records)&set(merged)
        merged.update(records)
    assert set(merged)==set(ids), (set(ids)-set(merged))
    mutate.save_records(ROOT/'tests/mutants_results.json',merged)
    (evidence/'workers.json').write_text(json.dumps([row for row,_ in rows],indent=2)+'\n')
    print('Merged',len(merged),'independently executed mutation records.')
    return subprocess.call([sys.executable,'tests/mutate.py','--check'],cwd=ROOT)


if __name__=='__main__':
    sys.exit(main())
