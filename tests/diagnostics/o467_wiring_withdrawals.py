"""Named fail-closed withdrawal controls for O467 registration and hash wiring.

Copies native source bytes and the narrow Python tool closure into a temporary
directory; never edits the working checkout and never invokes a native build.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import binaries

CASES = [
    ('O467_APPEND_OMITTED', 'tests/mutate.py',
     'MUTANTS = [*LEGACY_MUTANTS, *load_fragments(ROOT, LEGACY_MUTANTS)]',
     'MUTANTS = list(LEGACY_MUTANTS)',
     'test_original_152_and_new_16_form_exact_complete_union', 'O467_NATIVE_COUNTS'),
    ('O467_RESTORED_OMITTED', 'tests/mutation_bridge.py',
     "RESTORED = list(dict.fromkeys([*LEGACY_RESTORED, *(method for row in\n    load_fragments(Path(__file__).resolve().parents[1]) for method in row['tests'])]))",
     'RESTORED = list(LEGACY_RESTORED)',
     'test_restored_preserves_original_methods_and_includes_every_new_judge', 'O467_RESTORED_ALL_FRAGMENT_JUDGES'),
    ('O467_TOOL_FRAGMENT_HASH_OMITTED', 'tests/mutate.py',
     '    body += fragment_material(HERE.parent)', '    pass  # missing fragment hash',
     'test_tool_hash_includes_loader_and_every_fragment_byte', 'O467_TOOL_CLOSURE_BINDS_'),
    ('O467_ORACLE_FRAGMENT_HASH_OMITTED', 'tests/mutation_bridge.py',
     '    return sha(body + fragment_material(root))', '    return sha(body)',
     'test_bridge_oracle_hash_includes_fragment_bytes_without_dropping_old_sources', 'O467_ORACLE_CLOSURE_BINDS_'),
    ('O467_DUPLICATE_GUARD_OMITTED', 'tests/mutation_fragments.py',
     '        if folded in seen:', '        if False:',
     'test_duplicate_and_casefold_ids_fail_closed', 'O467_DUPLICATE_ID_MUST_REJECT'),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    _, closure, _ = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
    files = set(closure) | {'.github/scripts/evidence_records.py',
        'tests/mutate.py', 'tests/mutation_bridge.py', 'tests/mutation_fragments.py',
        'tests/test_mutation_fragments.py', 'tests/run_tests.py', 'tests/binaries.py'}
    files.update(path.relative_to(ROOT).as_posix() for path in (ROOT / 'tests/mutants.d').glob('*.json'))
    source = {name: (ROOT / name).read_bytes() for name in files}
    report = {'schema': 'o467-wiring-withdrawals/1', 'nativeExecuted': False,
              'sourceSha256': {name: sha(raw) for name, raw in sorted(source.items())}, 'records': []}
    with tempfile.TemporaryDirectory(prefix='o467-wiring-') as directory:
        work = Path(directory)
        for name, raw in source.items():
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        for identifier, file, old, new, method, marker in CASES:
            original = source[file]
            if original.count(old.encode()) != 1:
                raise ValueError('one wiring anchor required: ' + identifier)
            record = {'id': identifier, 'marker': marker, 'runs': []}
            for phase, raw in [('baseline', original),
                               ('withdrawn', original.replace(old.encode(), new.encode(), 1)),
                               ('restored', original)]:
                (work / file).write_bytes(raw)
                command = [sys.executable, '-B', 'tests/test_mutation_fragments.py',
                           'MutationFragments.' + method, '-v']
                run = subprocess.run(command, cwd=work, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                     capture_output=True, text=True, timeout=60)
                (args.out / (identifier + '-' + phase + '.stdout')).write_text(run.stdout, encoding='utf-8')
                (args.out / (identifier + '-' + phase + '.stderr')).write_text(run.stderr, encoding='utf-8')
                passed = (run.returncode == 0 and re.search(r'^Ran 1 test in ', run.stderr, re.MULTILINE)
                          and re.search(r'^OK\s*$', run.stderr, re.MULTILINE))
                killed = (run.returncode == 1 and marker in run.stderr and 'AssertionError:' in run.stderr
                          and re.search(r'^FAILED \(failures=[1-9][0-9]*\)\s*$', run.stderr, re.MULTILINE)
                          and not re.search(r'^ERROR:|\berrors=|\bskipped=', run.stderr, re.MULTILINE))
                record['runs'].append({'phase': phase, 'command': command, 'exit': run.returncode,
                    'sourceSha256': sha(raw), 'expected': bool(killed if phase == 'withdrawn' else passed)})
            record['restoredExactly'] = (work / file).read_bytes() == original
            record['exits'] = [row['exit'] for row in record['runs']]
            record['passed'] = all(row['expected'] for row in record['runs']) and record['restoredExactly']
            report['records'].append(record)
            print(identifier + ': ' + str(record['exits']) + ' passed=' + str(record['passed']), flush=True)
    (args.out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if all(row['passed'] for row in report['records']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
