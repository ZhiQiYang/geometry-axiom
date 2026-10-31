"""Bounded B2 follow-up: original command roles and preprocessor dependency subset."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
report = json.loads((ROOT / 'B2_CLOSURE.json').read_text())
ids = report['execution_identities']
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda path: json.loads(path.read_text())
out = ROOT / 'supplement'
out.mkdir(exist_ok=True)
result = {'schema': 'pr338-b2-command-binding/1', 'performance': [], 'abc': [], 'preprocessor': {}}

raw = (ROOT / 'selected/r8-perf-commands.json').read_bytes()
reference = next(v for k, v in report['r8']['invocation_manifests'].items() if '064908' in k)
assert sha(raw) == reference['sha256']
commands = [c for c in json.loads(raw) if c['command'][0].endswith('/bridge')]
assert len(commands) == 36
for sample, command in zip(report['r8']['samples_unchanged'], commands):
    role = sample['version']
    expected_sha = {'base': ids['base'], 'fix': ids['R8'], 'main': ids['main']}[role]
    label = {'base': 'base', 'fix': 'fix-or-orchestration', 'main': 'main'}[role]
    assert command['command'] == ['/tmp/g337323R8/work/' + role + '/bridge']
    assert command['acceptance_sha'] == ids['R8']
    assert command['source_sha'] == expected_sha
    assert command['source_role'] == {'label': label, 'sha': expected_sha}
    expected_stdin = 'loadfile /tmp/g337323R8/evidence/scenes/s%d.scene\n' % sample['n']
    assert sample['command'] == expected_stdin
    assert command['stdin_provided'] is True and command['stdin_sha256'] == sha(expected_stdin.encode())
    assert command['stdout_sha256'] == sample['stdout_sha256']
    assert command['actual_process_returncode'] == sample['exit'] == 0
    assert command['timeout_expired'] is False
    result['performance'].append({'N': sample['n'], 'round': sample['round'], 'version': role,
                                  'command': command['command'], 'stdin': expected_stdin,
                                  'stdin_sha256': command['stdin_sha256'], 'acceptance_sha': ids['R8'],
                                  'source_and_build_sha': expected_sha,
                                  'original_command_directory': command['directory']})

raw = (ROOT / 'selected/comparison/invocation/commands/commands.json').read_bytes()
assert sha(raw) == report['f9']['invocation_manifest']['sha256']
commands = [c for c in json.loads(raw) if c['command'][0].endswith('/bridge')]
equivalence_raw = (ROOT / 'selected/comparison/evidence/equivalence.json').read_bytes()
assert sha(equivalence_raw) == report['f9']['equivalence']['sha256']
rows = json.loads(equivalence_raw)['runs']
assert len(rows) == 350 and len(commands) == 700
for index, row in enumerate(rows):
    version = row['version']
    expected_source = ids['base'] if version == 'base' else ids['F9_ABC']
    expected_build = ids['base'] if version == 'base' else ids['R8']
    for trace, command in zip((False, True), commands[2 * index:2 * index + 2]):
        role = version + ('-trace' if trace else '')
        assert command['command'] == ['/workspace/geo323-F9-owner-compare-once-20261025-r1/work/' + role + '/bridge']
        assert command['acceptance_sha'] == ids['F9_ABC']
        assert command['source_sha'] == expected_source
        assert command['source_role'] == {
            'label': role + '-execution-with-pinned-reused-binary', 'sha': expected_source,
            'binary_build_sha': expected_build, 'fix_execution_closure_verified_equal_to_F8': version == 'fix'}
        assert command['stdin_provided'] is True
        assert command['stdin_sha256'] == sha(row['command'].encode())
        assert row['command'] == 'loadfile ' + row['path'] + '\ndump\n'
        assert command['actual_process_returncode'] == 0 and command['timeout_expired'] is False
        for stream in ('stdout', 'stderr'):
            assert command[stream + '_sha256'] == row[stream + '_sha256']
        result['abc'].append({'scene': row['scene'], 'role': role, 'command': command['command'],
                              'stdin': row['command'], 'stdin_sha256': command['stdin_sha256'],
                              'acceptance_sha': ids['F9_ABC'], 'source_sha': expected_source,
                              'binary_build_sha': expected_build,
                              'original_command_directory': command['directory']})

# These are dependency-only commands, not product compilation or a rerun of R8.
env = os.environ.copy()
for key in ('CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'OBJC_INCLUDE_PATH', 'DEPENDENCIES_OUTPUT',
            'SUNPRO_DEPENDENCIES', 'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LIBRARY_PATH', 'LD_PRELOAD', 'LD_LIBRARY_PATH'):
    env.pop(key, None)
for name, ref in (('base', ids['base']), ('F8', ids['R8'])):
    thin = ROOT / ('include-source-' + name)
    closure = report['source_closures'][ref]
    for path, expected in closure['files'].items():
        data = subprocess.check_output(['git', '--no-optional-locks', '-C', '/tmp/r02-ui1', 'show', ref + ':' + path])
        assert sha(data) == expected['sha256'] and len(data) == expected['bytes']
        dest = thin / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    command = ['gcc', '-std=c11', '-O2', '-MM', str(thin / 'geometry-web/web_bridge.c')]
    process = subprocess.run(command, cwd=thin, env=env, capture_output=True, timeout=60)
    (out / (name + '-dependencies.stdout')).write_bytes(process.stdout)
    (out / (name + '-dependencies.stderr')).write_bytes(process.stderr)
    (out / (name + '-dependencies.exit')).write_text(str(process.returncode) + '\n')
    assert process.returncode == 0, process.stderr.decode(errors='replace')
    deps = process.stdout.decode().replace('\\\n', '').split(':', 1)[1].split()
    relative = sorted({Path(path).resolve().relative_to(thin).as_posix() for path in deps})
    assert set(relative) <= set(closure['files'])
    assert not any(item['resolved'] in relative for item in closure['missing_quoted_includes'])
    result['preprocessor'][name] = {'source_sha': ref, 'command': command, 'exit': process.returncode,
                                     'repo_dependency_count': len(relative), 'repo_dependencies': relative,
                                     'all_in_original_frozen_closure': True, 'missing_fallbacks_active': 0,
                                     'stdout_sha256': sha(process.stdout), 'stderr_sha256': sha(process.stderr),
                                     'gcc_version': subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
                                     'purpose': 'Current dependency-only corroboration; not an original R8 build or replacement ELF'}
result['actual_exit'] = 0
path = ROOT / 'B2_COMMAND_BINDINGS.json'
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('PASS: R8 36 original samples bind role, execution/build SHA, exact stdin, stdout and exit')
print('PASS: F9 700 original commands bind role, execution/build SHA, exact stdin, stdout/stderr and exit')
print('PASS: base/F8 gcc -MM exit 0; active repo dependencies are within pinned closure; 0 active missing fallbacks')
print('Output SHA-256:', sha(path.read_bytes()))
