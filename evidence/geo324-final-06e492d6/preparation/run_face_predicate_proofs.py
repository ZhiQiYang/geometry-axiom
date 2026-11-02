#!/usr/bin/env python3
"""補錄原三 predicate 各自 0/1/0；只在 repo 外複製樹撤回產品 guard。"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys

SOURCE_PATH = 'geometry-templates/woodworking/geometry_woodworking/model_sources.py'
PACKAGES = ('geometry-core/geometry_kernel', 'geometry-core/modeling',
            'geometry-app/geometry_app',
            'geometry-templates/woodworking/geometry_woodworking')
TEST_FILES = ('test_geometry_host_sources.py', 'test_geometry_kernel_runtime.py',
              'test_geometry_source_runtime.py')
CASES = (
    ('list', b'type(legacy_faces) is not list\n                or ', b'',
     'test_public_default_rejects_non_list_snapshot_faces'),
    ('dict', b'type(face) is not dict or ', b'',
     'test_public_default_rejects_non_dict_snapshot_faces'),
    ('feature', b' or type(face.get("feature")) is not str', b'',
     'test_public_default_rejects_non_string_feature_snapshot_faces'),
)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if not re.fullmatch('[0-9a-f]{40}', args.expected_head):
        parser.error('expected-head must be the exact published 40-hex source SHA')
    if out.exists() or out.is_relative_to(repo) or not out.is_relative_to(Path('/tmp')):
        parser.error('out must be new, outside repo, beneath /tmp')
    if os.environ.get('PYTHONOPTIMIZE') not in (None, '', '0'):
        parser.error('unset PYTHONOPTIMIZE before launching')
    out.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('capture', '/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
    capture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(capture)
    env = os.environ.copy()
    for name in ('PYTHONPATH', 'PYTHONSTARTUP', 'PYTHONOPTIMIZE', 'NODE_OPTIONS'):
        env.pop(name, None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    rec = capture.Recorder(out, env, args.expected_head)
    report = {'schema': 'geo324.original-predicate-proofs.v1', 'sourceSHA': args.expected_head,
              'repo': str(repo), 'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'proofAccepted': False, 'exitCode': None, 'rows': [], 'errors': [],
              'scope': 'three existing public behavioral test methods; supplementary independent 0/1/0; not full 45-test module, aggregate or workflow'}
    def run(command, *, cwd=repo, variant='unchanged-published-source', timeout=60):
        return rec.run(command, cwd=cwd, source_variant=variant, timeout=timeout, check=False)
    def clean_state(label):
        row, head, _ = run(['git', 'rev-parse', 'HEAD'])
        statusrow, status, _ = run(['git', 'status', '--porcelain=v1', '--untracked-files=all'])
        state = {'head': head.decode().strip(), 'status': status.decode(),
                 'headExit': row['actual_process_returncode'], 'statusExit': statusrow['actual_process_returncode']}
        report[label] = state
        if state['headExit'] != 0 or state['statusExit'] != 0 or state['head'] != args.expected_head or state['status']:
            raise RuntimeError('fixed source or clean checkout guard failed')
    try:
        clean_state('checkoutBefore')
        row, original, _ = run(['git', 'show', args.expected_head+':'+SOURCE_PATH])
        if row['actual_process_returncode'] != 0 or (repo/SOURCE_PATH).read_bytes() != original:
            raise RuntimeError('product source bytes differ from committed source')
        report['sourceOriginalSHA256'] = digest(original)
        row, inventory, _ = run(['git', 'ls-tree', '-r', '-z', args.expected_head, '--', *PACKAGES,
                                *('tests/'+name for name in TEST_FILES)])
        if row['actual_process_returncode'] != 0:
            raise RuntimeError('cannot preserve input Git inventory')
        (out/'input-git-tree.bin').write_bytes(inventory)
        report['inputGitTreeSHA256'] = digest(inventory)
        for key, before, after, method in CASES:
            if original.count(before) != 1:
                raise RuntimeError('original single predicate anchor is not unique: '+key)
            isolated = out/('isolated-'+key)
            for package in PACKAGES:
                shutil.copytree(repo/package, isolated/package,
                                ignore=shutil.ignore_patterns('__pycache__'))
            (isolated/'tests').mkdir()
            (isolated/'tests/__init__.py').write_bytes(b'')
            for name in TEST_FILES:
                shutil.copyfile(repo/'tests'/name, isolated/'tests'/name)
            source = isolated/SOURCE_PATH
            if source.read_bytes() != original:
                raise RuntimeError('copied source differs')
            case = 'tests.test_geometry_host_sources.NativeCandidateTransportTests.'+method
            runner = 'import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)'
            command = [sys.executable, '-I', '-B', '-c', runner, str(isolated), case]
            proof = {'predicate': key, 'test': case, 'anchorCount': original.count(before),
                     'mutantSHA256': digest(original.replace(before, after, 1)), 'phases': [],
                     'proofAccepted': False}
            report['rows'].append(proof)
            try:
                for phase, raw in (('baseline', original), ('withdraw', original.replace(before, after, 1)), ('restored', original)):
                    source.write_bytes(raw)
                    row, stdout, stderr = run(command, cwd=isolated,
                                             variant=key+':'+phase, timeout=60)
                    details = stdout+stderr
                    proof['phases'].append({'phase': phase, 'commandResult': row,
                        'sourceSHA256': digest(source.read_bytes()),
                        'ranOneExistingMethod': b'Ran 1 test' in details,
                        'normalUnittestFailure': (b'FAILED (failures=' in details and b'FAIL: '+method.encode() in details
                                                 and b'ERROR:' not in details and b'ImportError' not in details
                                                 and b'SyntaxError' not in details and b'errors=' not in details)})
            finally:
                source.write_bytes(original)
                proof['byteRestored'] = source.read_bytes() == original
            phases = proof['phases']
            proof['originalExitCodes'] = [phase['commandResult']['actual_process_returncode'] for phase in phases]
            proof['proofAccepted'] = (len(phases) == 3 and proof['originalExitCodes'] == [0, 1, 0]
                and all(not phase['commandResult']['timeout_expired'] and phase['ranOneExistingMethod'] for phase in phases)
                and phases[1]['normalUnittestFailure'] and proof['byteRestored'])
        clean_state('checkoutAfter')
        report['proofAccepted'] = len(report['rows']) == 3 and all(row['proofAccepted'] for row in report['rows'])
        report['exitCode'] = 0 if report['proofAccepted'] else 1
    except BaseException as error:
        report['errors'].append(repr(error))
        report['exitCode'] = 2
    finally:
        report['endedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['commandCount'] = len(rec.rows)
        capture.dump(out/'receipt.json', report)
        print(json.dumps({'sourceSHA': report['sourceSHA'], 'exitCode': report['exitCode'],
                          'proofAccepted': report['proofAccepted'], 'errors': report['errors']}, ensure_ascii=False))
    return report['exitCode']

if __name__ == '__main__':
    raise SystemExit(main())
