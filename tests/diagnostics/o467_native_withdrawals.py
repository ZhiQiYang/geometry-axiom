"""Directed O467 0/1/0 diagnostics over strict registered native fragments.

Uses the official binaries.py compiler/sidecar and bridge_mutation_oracle.py
classifier. This local dirty-tree diagnostic is not a Mutation evidence run:
no execution.head or official ledger is forged. Baseline/restored are actual
executions of the same reauthenticated baseline binary, after exact restoration.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import binaries
import mutation_bridge as backend
from mutation_fragments import load_fragments


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--only', action='append')
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    if os.name != 'nt':
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        resource.setrlimit(resource.RLIMIT_STACK, (max(soft, 16 * 1024 * 1024), hard))
    rows = load_fragments(ROOT)
    if args.only:
        if set(args.only) - {row['id'] for row in rows}:
            parser.error('unknown mutation ID')
        rows = [row for row in rows if row['id'] in args.only]
    _, closure, command = binaries.compute_fingerprint(binaries.BY_NAME['bridge'])
    source = {name: (ROOT / name).read_bytes() for name in closure}
    # _bridge.find_bridge deliberately validates against the oracle's ROOT.
    # Execute judges in the same source snapshot that was actually compiled;
    # pointing a mutated binary at the untouched live ROOT is correctly stale.
    oracle_files = [*ROOT.glob('tests/*.py'), *ROOT.glob('tests/*.c'),
        *ROOT.glob('tests/fixtures/**/*'), *ROOT.glob('*.scene'),
        *ROOT.glob('tests/mutants.d/*.json'),
        *ROOT.glob('geometry-core/framing-template/oracle/*')]
    for path in oracle_files:
        if path.is_file():
            source[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    report = {'schema': 'o467-directed-native-withdrawals/1', 'officialME': False,
              'baseHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'driverSha256': sha(Path(__file__).read_bytes()), 'compileCommand': command,
              'sourceSha256': {name: sha(raw) for name, raw in sorted(source.items())},
              'records': []}
    env = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix='o467-native-') as temporary:
        work = Path(temporary)
        for name, raw in source.items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        cache = work / '_binary'
        baseline = cache / 'baseline'
        build, baseline_identity = backend._build(work, baseline, env, args.out,
            'baseline-build', ROOT, cache)
        report['baselineBuild'] = build
        report['baselineIdentity'] = baseline_identity
        for row in rows:
            folder = args.out / row['id']
            folder.mkdir()
            record = {'id': row['id'], 'expectedAssertion': row['expected_assertion'],
                      'definitionSha256': sha((ROOT / 'tests/mutants.d' / (row['id'] + '.json')).read_bytes()),
                      'oracleSha256': backend.oracle_hash(row, ROOT), 'phases': [], 'status': 'blocked'}
            target = work / row['file']
            original = source[row['file']]
            old, new = row['old'].encode(), row['new'].encode()
            if original.count(old) != 1:
                raise RuntimeError('not one anchor: ' + row['id'])
            if backend.oracle_hash(row, work) != backend.oracle_hash(row, ROOT):
                raise RuntimeError('oracle snapshot is incomplete: ' + row['id'])
            def run_phase(phase, binary):
                phase_env = dict(env, GEOMETRY_FRAMING_RECEIPTS=str(folder / (phase + '-native-requests')))
                return backend._test(work, binary, row['tests'], phase_env, folder,
                                     phase, ROOT, cache)
            try:
                before = run_phase('baseline', baseline / binaries.BY_NAME['bridge'].exe)
                record['phases'].append({'phase': 'baseline', 'run': before,
                    'status': backend.classify(before, row['tests'])})
                target.write_bytes(original.replace(old, new, 1))
                mutant_dir = cache / row['id']
                build, identity = backend._build(work, mutant_dir, env, folder,
                    'mutant-build', ROOT, cache)
                record['mutantBuild'], record['mutantIdentity'] = build, identity
                mutated = run_phase('withdrawn', mutant_dir / binaries.BY_NAME['bridge'].exe)
                status = backend.classify(mutated, row['tests'])
                if status == 'killed' and not any(row['expected_assertion'] in item['detail']
                        for item in mutated.get('result', {}).get('failures', [])):
                    status = 'blocked'
                    record['reason'] = 'Only unrelated assertion failures; named semantic marker missing.'
                record['phases'].append({'phase': 'withdrawn', 'run': mutated, 'status': status})
            finally:
                target.write_bytes(original)
            record['sourceRestoredExactly'] = all((work / name).read_bytes() == raw for name, raw in source.items())
            record['restoredIdentity'] = backend._identity(work, baseline)
            after = run_phase('restored', baseline / binaries.BY_NAME['bridge'].exe)
            record['phases'].append({'phase': 'restored', 'run': after,
                                    'status': backend.classify(after, row['tests'])})
            record['exits'] = [phase['run']['exit_code'] for phase in record['phases']]
            statuses = [phase['status'] for phase in record['phases']]
            if (record['sourceRestoredExactly'] and record['restoredIdentity'] == baseline_identity
                    and statuses == ['survived', 'killed', 'survived'] and record['exits'] == [0, 1, 0]):
                record['status'] = 'killed'
            elif statuses == ['survived', 'survived', 'survived']:
                record['status'] = 'survived'
            report['records'].append(record)
            (args.out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(row['id'] + ': ' + record['status'] + ' ' + str(record['exits']), flush=True)
    for name, raw in source.items():
        if (ROOT / name).read_bytes() != raw:
            raise RuntimeError('working source changed during proof: ' + name)
    return 0 if all(row['status'] == 'killed' for row in report['records']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
