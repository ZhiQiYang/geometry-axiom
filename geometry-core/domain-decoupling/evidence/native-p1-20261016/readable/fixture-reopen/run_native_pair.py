#!/usr/bin/env python3
"""Compare unchanged historical scenes through two real, fresh native versions."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BASELINE = 'a898ad6e12707104568679591fe1b21804bfc3df'
SNAPSHOT_COMMANDS = ('dump', 'render', 'objects', 'references', 'engineering-read')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def differences(left, right, path='', limit=100):
    """Exact structural comparison: no field or diagnostic normalization."""
    result = []
    def visit(a, b, location):
        if len(result) >= limit:
            return
        if type(a) is not type(b):
            result.append({'path': location, 'kind': 'type', 'left': type(a).__name__, 'right': type(b).__name__})
        elif isinstance(a, dict):
            for key in sorted(set(a) | set(b)):
                child = location + '/' + str(key).replace('~', '~0').replace('/', '~1')
                if key not in a or key not in b:
                    result.append({'path': child, 'kind': 'missing', 'leftPresent': key in a, 'rightPresent': key in b})
                else:
                    visit(a[key], b[key], child)
        elif isinstance(a, list):
            if len(a) != len(b):
                result.append({'path': location, 'kind': 'length', 'left': len(a), 'right': len(b)})
            for index, (aa, bb) in enumerate(zip(a, b)):
                visit(aa, bb, location + '/' + str(index))
        elif a != b:
            result.append({'path': location, 'kind': 'value', 'left': a, 'right': b})
    visit(left, right, path)
    return result[:limit]

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

def source_manifest(root):
    names = git(root, 'ls-files', '-z').decode('utf-8').strip('\0').split('\0')
    return {name: sha(root / name) for name in sorted(names)}

def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def registry_info(root, source, bridge, core, key):
    if git(root, 'rev-parse', 'HEAD').decode().strip() != source:
        raise RuntimeError(key + ' checkout is not the declared fixed SHA')
    if git(root, 'status', '--porcelain'):
        raise RuntimeError(key + ' checkout is dirty before execution')
    registry = import_file('fixture_binaries_' + key, root / 'tests/binaries.py')
    result = {'source': source, 'root': str(root), 'registrySourceSha256': sha(root / 'tests/binaries.py'), 'binaries': {}}
    for name, executable in (('bridge', bridge), ('core', core)):
        inspected = registry.inspect_one(registry.BY_NAME[name], str(executable))
        if inspected.state != 'fresh':
            raise RuntimeError(key + ' ' + name + ' is not fresh: ' + inspected.reason)
        sidecar = Path(str(executable) + registry.SIDECAR_SUFFIX)
        result['binaries'][name] = {'path': str(executable), 'sha256': sha(executable),
                                    'sidecarSha256': sha(sidecar), 'sidecar': json.loads(sidecar.read_text())}
    return registry, result

def process(command, directory, stem, *, input_bytes=None, timeout=45):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith('GEOMETRY_')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'command': list(map(str, command)), 'cwd': str(directory), 'startedUtc': start, 'timeoutSeconds': timeout}
    try:
        run = subprocess.run(command, input=input_bytes, cwd=directory, env=env, capture_output=True, timeout=timeout)
        stdout, stderr = run.stdout, run.stderr
        record.update(returncode=run.returncode, timedOut=False)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b'', error.stderr or b''
        record.update(returncode=None, timedOut=True)
    except OSError as error:
        stdout, stderr = b'', str(error).encode('utf-8')
        record.update(returncode=None, timedOut=False, launchError=type(error).__name__ + ': ' + str(error))
    (directory / (stem + '.stdout')).write_bytes(stdout)
    (directory / (stem + '.stderr')).write_bytes(stderr)
    record.update(finishedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  stdoutSha256=hashlib.sha256(stdout).hexdigest(), stderrSha256=hashlib.sha256(stderr).hexdigest())
    save(directory / (stem + '.command.json'), record)
    return record, stdout, stderr

def bridge_round(bridge, scene_path, directory, stem):
    if '\n' in str(scene_path) or '\r' in str(scene_path):
        raise RuntimeError('A scene path cannot be sent as one bridge command')
    commands = ['default', *SNAPSHOT_COMMANDS, 'loadfile ' + str(scene_path), *SNAPSHOT_COMMANDS]
    (directory / (stem + '.commands.txt')).write_text('\n'.join(commands) + '\n', encoding='utf-8')
    proc, stdout, stderr = process([str(bridge)], directory, stem, input_bytes=('\n'.join(commands) + '\n').encode('utf-8'))
    result = {'process': proc, 'protocolOk': False, 'worldAtomic': None}
    if proc['returncode'] != 0 or proc['timedOut'] or proc.get('launchError'):
        result['failureKind'] = 'process-failure-not-domain-rejection'
        return result
    try:
        rows = [json.loads(line) for line in stdout.decode('utf-8').splitlines()]
        if len(rows) != len(commands) or any(not isinstance(row, dict) for row in rows):
            raise ValueError('bridge response cardinality or type differs')
        before = dict(zip(SNAPSHOT_COMMANDS, rows[1:1+len(SNAPSHOT_COMMANDS)]))
        response = rows[1+len(SNAPSHOT_COMMANDS)]
        after = dict(zip(SNAPSHOT_COMMANDS, rows[2+len(SNAPSHOT_COMMANDS):]))
        if rows[0].get('ok') is not True or not before['dump'].get('text', '').strip():
            raise ValueError('the nonempty sentinel world did not load')
        if any(row.get('ok') is not True for row in (*before.values(), *after.values())):
            raise ValueError('a state inspection failed')
        if type(response.get('ok')) is not bool:
            raise ValueError('load response lacks a boolean domain verdict')
        if response['ok'] is False and (not isinstance(response.get('error'), str) or not response['error']):
            raise ValueError('domain rejection did not give a diagnostic')
    except (ValueError, UnicodeError) as error:
        result.update(failureKind='protocol-failure-not-domain-rejection', protocolError=str(error))
        return result
    result.update(protocolOk=True, accepted=response['ok'], loadResponse=response, before=before, after=after,
                  worldAtomic=not differences(before, after) if not response['ok'] else None)
    if not response['ok']:
        result['atomicityDifferences'] = differences(before, after)
    return result

def run_backend(name, bridge, core, input_path, case, directory, baseline_root):
    directory.mkdir(parents=True, exist_ok=False)
    loaded = bridge_round(bridge, input_path, directory, 'original-load')
    result = {'backend': name, 'original': loaded, 'reopen': None, 'knownOracles': [], 'ok': False}
    if not loaded['protocolOk']:
        save(directory / 'result.json', result)
        return result
    valid = loaded['worldAtomic'] if not loaded['accepted'] else True
    if loaded['accepted']:
        canonical = loaded['after']['dump'].get('text')
        if not isinstance(canonical, str):
            valid = False
            result['canonicalDumpError'] = 'dump text is not a string'
        else:
            canonical_path = directory / 'canonical.scene'
            canonical_path.write_bytes(canonical.encode('utf-8'))
            reopened = bridge_round(bridge, canonical_path, directory, 'fresh-canonical-reopen')
            result['reopen'] = reopened
            same = reopened['protocolOk'] and reopened.get('accepted') is True
            if same:
                result['reopenDifferences'] = differences(loaded['after'], reopened['after'])
                same = not result['reopenDifferences']
            valid = valid and same
    known = [owner for owner in case['owners'] if 'oracle' in owner['expectation']]
    if known:
        # This raw CLI run is retained separately from the unchanged baseline judge below.
        proc, _, _ = process([str(core), '--scene', str(input_path), '--no-window'], directory, 'raw-cli', timeout=30)
        valid = valid and proc['returncode'] in (0, 1) and not proc['timedOut']
        for index, owner in enumerate(known):
            spec = dict(owner['expectation']['oracle'])
            original_scene = spec['scene']
            spec['scene'] = str(input_path)  # Absolute path overrides ROOT, with the original bytes and unchanged oracle.
            spec_path = directory / ('oracle-' + str(index) + '.json')
            save(spec_path, spec)
            judge_process, judge_stdout, _ = process(
                [sys.executable, str(Path(__file__).with_name('exercise_original_oracle.py')),
                 str(baseline_root), str(core), str(spec_path)], directory, 'oracle-' + str(index), timeout=40)
            try:
                judge_result = json.loads(judge_stdout)
                verdict = judge_result['verdict']
            except (ValueError, KeyError, TypeError):
                verdict = 'INFRA original judge produced no structured verdict'
            if judge_process['returncode'] not in (0, 1) or judge_process['timedOut']:
                verdict = 'INFRA original judge process failed: ' + str(judge_process['returncode'])
            record = {'owner': owner, 'originalScene': original_scene, 'actualInputPath': str(input_path),
                      'unchangedOracle': owner['expectation']['oracle'], 'originalJudgeVerdict': verdict}
            result['knownOracles'].append(record)
            valid = valid and verdict == 'ok'
    result['ok'] = bool(valid)
    save(directory / 'result.json', result)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--baseline-root', required=True, type=Path)
    parser.add_argument('--candidate-root', required=True, type=Path)
    parser.add_argument('--candidate-sha', required=True)
    for side in ('baseline', 'candidate'):
        parser.add_argument('--' + side + '-bridge', required=True, type=Path)
        parser.add_argument('--' + side + '-core', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if sha(args.manifest) != args.manifest_sha256:
        raise RuntimeError('The input manifest does not match its predeclared SHA-256')
    lock = Path('/run/lock/ga-wsl-v3.lock')
    held = os.fstat(7)
    if (held.st_dev, held.st_ino) != (lock.stat().st_dev, lock.stat().st_ino):
        raise RuntimeError('The existing shared lock is not inherited')
    source = json.loads(args.manifest.read_text(encoding='utf-8'))
    if source['baselineSource'] != BASELINE or source.get('runtimeExecuted') is not False:
        raise RuntimeError('The immutable baseline input manifest is not the declared static source')
    cases = source['nativeInputs']
    if not cases or len({case['sha256'] for case in cases}) != len(cases):
        raise RuntimeError('Native input coverage is empty or contains duplicate case identities')
    if len(cases) != source['summary']['nativeUniqueInputs'] or sum(len(case['owners']) for case in cases) != source['summary']['nativeOwnerRows']:
        raise RuntimeError('Native input coverage differs from its declared counts')
    args.out.mkdir(parents=True, exist_ok=False)
    roots = {'baseline': args.baseline_root, 'candidate': args.candidate_root}
    revisions = {'baseline': BASELINE, 'candidate': args.candidate_sha}
    registries, identities, before = {}, {}, {}
    runner_before = sha(Path(__file__))
    manifest_before = sha(args.manifest)
    for side in roots:
        registries[side], identities[side] = registry_info(roots[side], revisions[side], getattr(args, side+'_bridge'), getattr(args, side+'_core'), side)
        before[side] = source_manifest(roots[side])
        save(args.out / (side + '-source-before.json'), before[side])
    if sha(args.baseline_root / 'tests/run_tests.py') != source['nativeOracleRawSha256']:
        raise RuntimeError('The original native referee does not match the fixture manifest')
    oracle_runner_before = sha(Path(__file__).with_name('exercise_original_oracle.py'))
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []
    for case in source['nativeInputs']:
        input_path = (args.manifest.parent / case['blob']).resolve()
        if sha(input_path) != case['sha256'] or input_path.stat().st_size != case['bytes']:
            raise RuntimeError('Immutable input hash differs: ' + case['sha256'])
        case_dir = args.out / 'cases' / case['sha256']
        backends = {side: run_backend(side, getattr(args, side+'_bridge'), getattr(args, side+'_core'), input_path,
                                      case, case_dir / side, args.baseline_root) for side in roots}
        left, right = backends['baseline']['original'], backends['candidate']['original']
        mismatch = []
        if left['protocolOk'] and right['protocolOk']:
            mismatch = differences(left['loadResponse'], right['loadResponse'], '/loadResponse')
            mismatch += differences(left['after'], right['after'], '/after')
        matched = all(item['ok'] for item in backends.values()) and not mismatch
        row = {'sha256': case['sha256'], 'owners': case['owners'], 'inputBytesUnchanged': sha(input_path) == case['sha256'],
               'baselineAccepted': left.get('accepted'), 'candidateAccepted': right.get('accepted'),
               'backendValid': {side: backends[side]['ok'] for side in roots},
               'differences': mismatch[:100], 'exactDifferentialMatch': bool(matched),
               'classification': 'observed-behavior-match' if matched else 'difference-or-invalid-execution'}
        rows.append(row)
        save(case_dir / 'comparison.json', row)
        save(args.out / 'case-results.json', rows)
        print(json.dumps({'completed': len(rows), 'total': len(source['nativeInputs']), 'sha256': case['sha256'],
                          'baselineAccepted': left.get('accepted'), 'candidateAccepted': right.get('accepted'),
                          'matched': bool(matched)}, ensure_ascii=False), flush=True)
    after = {}
    fresh_after = {}
    for side in roots:
        after[side] = source_manifest(roots[side])
        save(args.out / (side + '-source-after.json'), after[side])
        fresh_after[side] = {name: registries[side].inspect_one(registries[side].BY_NAME[name], str(getattr(args, side+'_'+name))).state
                             for name in ('bridge', 'core')}
    summary = {'schema': 'geo261-native-fixture-pair/1', 'baselineSource': BASELINE, 'candidateSource': args.candidate_sha,
               'startedUtc': start, 'finishedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'identity': identities, 'freshAfter': fresh_after, 'sourceUnchanged': {side: before[side] == after[side] for side in roots},
               'manifestSha256': manifest_before, 'manifestUnchanged': manifest_before == sha(args.manifest),
               'runnerSha256': runner_before, 'runnerUnchanged': runner_before == sha(Path(__file__)),
               'oracleRunnerSha256': oracle_runner_before,
               'oracleRunnerUnchanged': oracle_runner_before == sha(Path(__file__).with_name('exercise_original_oracle.py')),
               'uniqueNativeInputs': len(rows), 'ownerRows': sum(len(row['owners']) for row in rows),
               'matched': sum(row['exactDifferentialMatch'] for row in rows), 'failed': sum(not row['exactDifferentialMatch'] for row in rows),
               'scope': 'All manifest native scene bytes, including archive/JSON scenes. Full archive/UI/model-package closure is a separate gate.',
               'unclassifiedInputPolicy': 'Report observed baseline/candidate behavior; matching is not an independent claim of SSOT validity.',
               'sharedLockHolder': Path('/run/lock/ga-wsl-v3.holder').read_text(),
               'exit': 0 if all(row['exactDifferentialMatch'] and row['inputBytesUnchanged'] for row in rows)
                       and all(before[side] == after[side] for side in roots)
                       and all(state == 'fresh' for data in fresh_after.values() for state in data.values())
                       and runner_before == sha(Path(__file__)) and manifest_before == sha(args.manifest)
                       and oracle_runner_before == sha(Path(__file__).with_name('exercise_original_oracle.py')) else 1}
    save(args.out / 'summary.json', summary)
    (args.out / 'exit.txt').write_text(str(summary['exit']) + '\n', encoding='ascii')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary['exit']

if __name__ == '__main__':
    sys.exit(main())
