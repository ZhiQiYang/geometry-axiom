"""Named R03 host withdrawals through real Session/ReferenceWorkspace/ZIP code.

Only transport responses are controlled by the Node protocol fixture. This is
not native geometry or browser evidence. Each kill requires 0/1/0, the named
AssertionError, byte-identical restoration and no syntax/import/timeout error.
The working sources and tests/mutants_results.json are never modified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'geometry-web/framing-template-session.js'
JUDGE = ROOT / 'tests/test_framing_template_session.js'
FAULTS = [
    ('R03_HOST_CANCEL_WRITES', 'FT_H10_CANCEL_NO_WRITE',
     'const command=`framing-template-cancel ${this.candidate.token} ${this.ownerKey}`;',
     'const command=`framing-template-confirm ${this.candidate.token} ${this.ownerKey}`;'),
    ('R03_HOST_COLD_OPEN_SEARCH', 'FT_H11_COLD_OPEN_NO_SEARCH',
     'this.collection=clone(value); // FT_H11_COLD_OPEN_NO_SEARCH: restoration has no native request.',
     "this.collection=clone(value); this.transport.post('/framing-template/preview',{schema:'framing-template-generate/1'});"),
    ('R03A_HOST_COLD_OPEN_SEARCH', 'R03A_HOST_COLD_OPEN_NO_SEARCH',
     'this.collection=clone(value); // FT_H11_COLD_OPEN_NO_SEARCH: restoration has no native request.',
     "this.collection=clone(value); this.transport.post('/framing-template/preview',{schema:'framing-template-generate/1'});"),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(source, marker):
    env = {**os.environ, 'GEOMETRY_TEST_FRAMING_SESSION': str(source)}
    command = ['node', '--test', '--test-reporter=spec', '--test-name-pattern=^' + marker, str(JUDGE)]
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        return {'command': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        return {'command': command, 'exit': None, 'stdout': str(error.stdout or ''), 'stderr': 'TIMEOUT'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    original = TARGET.read_bytes()
    records = []
    for identifier, marker, before, after in FAULTS:
        record = {'id': identifier, 'marker': marker, 'source': str(TARGET.relative_to(ROOT)),
                  'source_sha256': sha(original), 'judge_sha256': sha(JUDGE.read_bytes()), 'status': 'blocked'}
        text = original.decode('utf-8')
        if text.count(before) != 1:
            record['reason'] = 'source anchor must match exactly once'
            records.append(record)
            continue
        with tempfile.TemporaryDirectory(prefix='r03-host-withdrawal-') as directory:
            source = Path(directory) / TARGET.name
            shutil.copy2(ROOT / 'geometry-web/framing-recipes.js', Path(directory) / 'framing-recipes.js')
            source.write_bytes(original)
            baseline = run(source, marker)
            source.write_bytes(text.replace(before, after).encode('utf-8'))
            record['mutated_sha256'] = sha(source.read_bytes())
            mutant = run(source, marker)
            source.write_bytes(original)
            restored = run(source, marker)
            log = mutant['stdout'] + mutant['stderr']
            expected_failure = ('AssertionError [ERR_ASSERTION]' in log and marker in log
                                and not any(word in log for word in ['SyntaxError', 'ReferenceError', 'TypeError', 'MODULE_NOT_FOUND', 'TIMEOUT']))
            exits = [baseline['exit'], mutant['exit'], restored['exit']]
            record.update(exits=exits, restored_sha256=sha(source.read_bytes()),
                          assertion_failure=expected_failure,
                          status='killed' if exits == [0, 1, 0] and expected_failure and source.read_bytes() == original else 'blocked')
            for phase, result in [('baseline', baseline), ('mutant', mutant), ('restored', restored)]:
                (args.output / f'{identifier}-{phase}.log').write_text(result['stdout'] + result['stderr'], encoding='utf-8')
            record['runs'] = [{k: v for k, v in result.items() if k not in ('stdout', 'stderr')}
                              for result in (baseline, mutant, restored)]
        records.append(record)
    result = {'schema': 'framing-template-host-withdrawals/1', 'evidenceScope': 'Node Session + real project history/ZIP; browser and native geometry are separate gates',
              'counts': {name: sum(r['status'] == name for r in records) for name in ('killed', 'blocked')}, 'records': records}
    (args.output / 'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['counts']))
    return 0 if result['counts']['killed'] == len(FAULTS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
