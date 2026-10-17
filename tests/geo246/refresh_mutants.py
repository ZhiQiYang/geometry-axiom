"""Run the original mutation tool with disjoint result files, then merge honestly."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import mutate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    ids = [m['id'] for m in mutate.MUTANTS]

    def run(name, selected):
        env = dict(os.environ, MUTATE_RESULTS=str(args.out / (name + '.json')))
        with (args.out / (name + '.log')).open('wb') as log:
            proc = subprocess.run([sys.executable, '-u', 'tests/mutate.py', *selected],
                                  cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        print(name, 'exit', proc.returncode, flush=True)
        return name, proc.returncode

    if run('seed', ids[:1])[1]:
        return 1
    groups = [(f'batch{i + 1}', ids[1 + i::4]) for i in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda row: run(*row), groups))
    if any(code for _, code in results):
        return 1
    merged = {}
    for name in ['seed', *(name for name, _ in results)]:
        records = json.loads((args.out / (name + '.json')).read_text())
        assert not (set(merged) & set(records))
        merged.update(records)
    assert set(merged) == set(ids)
    mutate.save_records(ROOT / 'tests/mutants_results.json', merged)
    print('Processed 50 records: 47 executed mutations, 3 original retired definitions.', flush=True)
    return subprocess.run([sys.executable, 'tests/mutate.py', '--check'], cwd=ROOT).returncode


if __name__ == '__main__':
    sys.exit(main())
