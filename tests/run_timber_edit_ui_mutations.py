#!/usr/bin/env python3
"""Execute named adapter mutations on isolated files; never edit the worktree.

This is a Node VM boundary check. Native and real Chrome mutation gates remain
separate. Every mutant must be syntactically valid, fail its named assertion,
and pass again with the identical original bytes restored.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / 'geometry-web/timber-edit.js'
    tests = root / 'tests/test_timber_edit_ui.js'
    definitions = root / 'tests/timber_edit_ui_mutations.json'
    original = source.read_bytes()
    if args.output and args.output.exists():
        parser.error('--output must not already exist; previous receipts are immutable')
    output = args.output or Path(tempfile.mkdtemp(prefix='r11-ui-mutations-'))
    output.mkdir(parents=True, exist_ok=args.output is None)
    command = ['node', '--test-reporter=tap', str(tests)]
    receipt = {'kind': 'adapter-functions', 'source_sha256': sha(original),
               'test_sha256': sha(tests.read_bytes()), 'mutations_sha256': sha(definitions.read_bytes()),
               'runner_sha256': sha(Path(__file__).read_bytes()), 'command': command, 'mutations': []}
    try:
        for definition in json.loads(definitions.read_text(encoding='utf-8')):
            case = output / definition['name']
            target = case / 'source/geometry-web/timber-edit.js'
            target.parent.mkdir(parents=True, exist_ok=True)
            anchor = definition['anchor'].encode('utf-8')
            assert original.count(anchor) == 1, definition['name'] + ': anchor must occur once'
            mutant = original.replace(anchor, definition['replacement'].encode('utf-8'))
            env = dict(os.environ, GEOMETRY_TIMBER_UI_ROOT=str(target.parent.parent))
            record = {'name': definition['name'], 'case': definition['case'], 'runs': []}
            receipt['mutations'].append(record)
            baseline_count = None
            for phase, data in [('baseline', original), ('mutant', mutant), ('restored', original)]:
                target.write_bytes(data)
                syntax = subprocess.run(['node', '--check', str(target)], capture_output=True, text=True, timeout=30)
                assert syntax.returncode == 0, definition['name'] + ': invalid syntax is not a kill'
                run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=60)
                (case / (phase + '.log')).write_bytes((run.stdout + run.stderr).encode('utf-8'))
                summary = {key: int(count) for key, count in re.findall(r'^# (tests|pass|fail|cancelled|skipped) (\d+)$', run.stdout, re.M)}
                failures = re.findall(r'^not ok \d+ - ([^\n]+)\n(.*?)(?=^# Subtest:|^\d+\.\.\d+|\Z)', run.stdout, re.M | re.S)
                record['runs'].append({'phase': phase, 'exit_code': run.returncode, 'source_sha256': sha(data), 'syntax_exit': syntax.returncode, 'summary': summary})
                assert summary.get('cancelled') == 0 and summary.get('skipped') == 0, definition['name'] + ': cancelled/skipped cases cannot count'
                if phase == 'mutant':
                    assert run.returncode == 1 and len(failures) == 1 and failures[0][0].startswith(definition['case'] + ':'), definition['name'] + ': only the named case may fail'
                    assert re.search(r"^\s+code: ['\"]ERR_ASSERTION['\"]$", failures[0][1], re.M), definition['name'] + ': named failure was not an assertion'
                    assert summary.get('fail') == 1 and summary.get('tests') == baseline_count and summary.get('pass') == baseline_count - 1, definition['name'] + ': all other cases must pass'
                else:
                    assert run.returncode == 0 and not failures and summary.get('fail') == 0 and summary.get('pass', 0) > 0 and summary.get('tests') == summary.get('pass'), definition['name'] + ': baseline/restore failed'
                    if baseline_count is None:
                        baseline_count = summary['tests']
                    else:
                        assert summary['tests'] == baseline_count, definition['name'] + ': restored case count changed'
            record['status'] = 'killed-and-restored'
        assert source.read_bytes() == original, 'worktree source was modified'
        receipt['status'] = 'pass'
    except BaseException as error:
        receipt['status'] = 'failed'
        receipt['error'] = str(error)
        raise
    finally:
        (output / 'receipt.json').write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        print(output / 'receipt.json')


if __name__ == '__main__':
    main()
