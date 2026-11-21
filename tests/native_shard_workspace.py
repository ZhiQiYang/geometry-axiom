"""Strict local measurement provenance; never label workspace runs as GitHub CI.

The /2 format is independent of the immutable GitHub /1 observations.  Source
manifests and original child logs are retained alongside the complete runner
rows.  Planning costs are conservative bounds, not observed CI durations.
"""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


def require(condition, marker):
    if not condition:
        raise ValueError(marker)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def is_hash(value, size=64):
    return type(value) is str and re.fullmatch('[a-f0-9]{%d}' % size, value) is not None


def safe_path(value):
    if type(value) is not str or not value or '\\' in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and path.as_posix() == value and '..' not in path.parts


def blob(record, directory, role):
    require(type(record) is dict and set(record) == {'path', 'bytes', 'sha256'}
            and safe_path(record['path']) and type(record['bytes']) is int
            and record['bytes'] >= 0 and (role == 'stdout' or record['bytes'] > 0)
            and is_hash(record['sha256']), 'R03_CI_ARTIFACT_DESCRIPTOR')
    path = directory / record['path']
    require(path.resolve().is_relative_to(directory.resolve()) and path.is_file(),
            'R03_CI_ARTIFACT_EXISTS:' + role)
    data = path.read_bytes()
    require(len(data) == record['bytes'], 'R03_CI_ARTIFACT_BYTES:' + role)
    require(digest(data) == record['sha256'], 'R03_CI_ARTIFACT_SHA256:' + role)
    return data


def validate_stdout(record, directory):
    blob(record, directory, 'stdout')


def validate_child(entry, directory):
    if not entry['test_file'].endswith('.py'):
        require(entry['child_report'] is None and entry['child_log'] is None, 'R03_CI_CHILD_REPORT')
        return
    child = json.loads(blob(entry['child_report'], directory, 'child-report'))
    blob(entry['child_log'], directory, 'child-log')
    row = entry['row']
    require(type(child) is dict and child.get('file') == entry['test_file']
            and all(type(child.get(key)) is int and child[key] == row[key]
                    for key in ('total', 'passed', 'failed', 'skipped'))
            and type(child.get('run')) is int and child['run'] == row['total']
            and child.get('import_error') is None and child.get('failures') == []
            and child.get('skip_items') == [] and child.get('expected_failures') == []
            and child.get('expected_failed') == 0, 'R03_CI_CHILD_REPORT')


def validate_row(row, upper):
    require(type(row) is dict and set(row) == {
        'name', 'counted', 'total', 'passed', 'failed', 'skipped', 'seconds', 'ran',
        'process_exit_code', 'allowed_skips', 'env_problem', 'crashed', 'expected_problem'},
        'R03_CI_ROW_FIELDS')
    require(type(row['name']) is str and bool(row['name'])
            and all(type(row[key]) is int and row[key] >= 0 for key in
                    ('total', 'passed', 'failed', 'skipped', 'allowed_skips'))
            and all(type(row[key]) is bool for key in ('counted', 'ran', 'env_problem', 'crashed')),
            'R03_CI_ROW_TYPES')
    require(type(row['process_exit_code']) is int and row['process_exit_code'] == 0
            and row['ran'] and not row['failed'] and not row['skipped']
            and not row['allowed_skips'] and not row['env_problem'] and not row['crashed']
            and row['expected_problem'] == '', 'R03_CI_ROW_PASS')
    require((row['counted'] and row['total'] > 0 and row['passed'] == row['total'])
            or (not row['counted'] and row['total'] == 0 and row['passed'] == 1),
            'R03_CI_ROW_COUNT')
    require(type(row['seconds']) in (int, float) and math.isfinite(row['seconds'])
            and 0 < row['seconds'] < 1200, 'R03_CI_ROW_TIME')
    require(type(upper) is int and row['seconds'] * 1000 < upper < 1200000,
            'R03_CI_PLANNING_MARGIN')


def load(path):
    path = Path(path)
    directory = path.parent
    data = json.loads(path.read_text(encoding='utf-8'))
    require(type(data) is dict and set(data) == {'schema', 'source', 'observations'}
            and data['schema'] == 'native-shard-workspace-suite-evidence/2', 'R03_CI_SCHEMA')
    source = data['source']
    require(type(source) is dict and set(source) == {
        'kind', 'base_sha', 'recorded_at', 'note', 'runner', 'manifest'}
        and source['kind'] == 'workspace' and is_hash(source['base_sha'], 40)
        and type(source['recorded_at']) is str and bool(source['recorded_at'])
        and type(source['note']) is str and bool(source['note']), 'R03_CI_WORKSPACE_SOURCE')
    runner = source['runner']
    require(type(runner) is dict and set(runner) == {
        'cpu_model', 'nproc', 'cgroup_cpu_max', 'platform', 'python', 'node'}
        and type(runner['nproc']) is int and runner['nproc'] > 0
        and all(type(runner[key]) is str and bool(runner[key]) for key in
                ('cpu_model', 'cgroup_cpu_max', 'platform', 'python', 'node')),
        'R03_CI_RUNNER_IDENTITY')
    manifest = json.loads(blob(source['manifest'], directory, 'source'))
    require(type(manifest) is dict and set(manifest) == {'schema', 'base_sha', 'files', 'binary'}
            and manifest['schema'] == 'native-shard-workspace-source/1'
            and manifest['base_sha'] == source['base_sha']
            and type(manifest['files']) is list and bool(manifest['files']),
            'R03_CI_SOURCE_MANIFEST')
    files = {}
    for item in manifest['files']:
        require(type(item) is dict and set(item) == {'path', 'bytes', 'sha256', 'lf_sha256'}
                and safe_path(item['path']) and item['path'] not in files
                and type(item['bytes']) is int and item['bytes'] >= 0
                and is_hash(item['sha256']) and is_hash(item['lf_sha256']), 'R03_CI_SOURCE_FILES')
        files[item['path']] = item
    required = {'tests/run_all.py', 'tests/run_all.expected.json', 'tests/_unittest_runner.py', 'tests/binaries.py',
                'tests/native_shards.py', 'tests/native_shard_workspace.py',
                'tests/generate_r03_shard_costs.py', 'tests/test_timber_edit.py',
                'tests/fixtures/reference_workspace_vm.cjs',
                'tests/diagnostics/r03_framing_canvas_extension.cjs',
                'geometry-web/project-store.js', 'geometry-web/framing-recipes.js',
                'geometry-web/framing-template-session.js', 'geometry-web/serve.py',
                'geometry-web/runtime_version.py', 'geometry-app/application.js',
                'geometry-templates/woodworking/frontend.js', '公理層.md',
                'geometry-core/framing-template/oracle/framing_oracle.py',
                'geometry-core/framing-template/oracle/oracle-golden.json'}
    require(required <= files.keys(), 'R03_CI_SOURCE_CLOSURE')
    binary = manifest['binary']
    require(type(binary) is dict and set(binary) == {
        'name', 'bytes', 'sha256', 'fingerprint', 'command', 'source_sha256'}
        and binary['name'] == 'bridge' and type(binary['bytes']) is int and binary['bytes'] > 0
        and is_hash(binary['sha256']) and is_hash(binary['fingerprint'])
        and type(binary['command']) is str and bool(binary['command'])
        and type(binary['source_sha256']) is dict and bool(binary['source_sha256']),
        'R03_CI_BINARY_IDENTITY')
    h = hashlib.sha256(binary['command'].encode('utf-8') + b'\0')
    for name, value in sorted(binary['source_sha256'].items()):
        require(name in files and is_hash(value) and files[name]['lf_sha256'] == value,
                'R03_CI_BINARY_SOURCE_PIN')
        h.update(('%s\0%s\n' % (name, value)).encode('utf-8'))
    require(h.hexdigest() == binary['fingerprint'], 'R03_CI_BINARY_FINGERPRINT')
    require(type(data['observations']) is list and bool(data['observations']), 'R03_CI_OBSERVATIONS')
    bounds, seen_artifacts = {}, {source['manifest']['path']}
    for entry in data['observations']:
        require(type(entry) is dict and set(entry) == {
            'row', 'test_file', 'command', 'timeout_seconds', 'planning_upper_ms', 'stdout', 'receipt',
            'child_report', 'child_log'},
            'R03_CI_OBSERVATION_FIELDS')
        row = entry['row']
        validate_row(row, entry['planning_upper_ms'])
        require(row['name'] not in bounds, 'R03_CI_DUPLICATE_OBSERVATION')
        require(safe_path(entry['test_file']) and entry['test_file'] in files
                and type(entry['command']) is list and bool(entry['command'])
                and all(type(x) is str and x for x in entry['command'])
                and entry['test_file'] in entry['command']
                and type(entry['timeout_seconds']) is int and 0 < entry['timeout_seconds'] <= 1200,
                'R03_CI_COMMAND_SOURCE')
        minimum = 60000 if entry['test_file'].endswith('.py') else 5000
        require(entry['planning_upper_ms'] >= max(minimum, math.ceil(row['seconds'] * 3) * 1000 + 1000),
                'R03_CI_PLANNING_MARGIN')
        for key in ('stdout', 'receipt', 'child_report', 'child_log'):
            if key.startswith('child_') and entry[key] is None:
                continue
            require(type(entry[key]) is dict and entry[key].get('path') not in seen_artifacts,
                    'R03_CI_DUPLICATE_ARTIFACT')
            seen_artifacts.add(entry[key].get('path'))
        validate_stdout(entry['stdout'], directory)
        validate_child(entry, directory)
        receipt = json.loads(blob(entry['receipt'], directory, 'receipt'))
        require(type(receipt) is dict and set(receipt) == {
            'schema', 'source_manifest_sha256', 'source_base_sha', 'row', 'command',
            'timeout_seconds', 'stdout_sha256', 'child_report_sha256', 'child_log_sha256'}
            and receipt['schema'] == 'native-shard-workspace-row/2'
            and receipt['source_manifest_sha256'] == source['manifest']['sha256']
            and receipt['source_base_sha'] == source['base_sha']
            and receipt['row'] == row and receipt['command'] == entry['command']
            and receipt['timeout_seconds'] == entry['timeout_seconds']
            and receipt['stdout_sha256'] == entry['stdout']['sha256']
            and receipt['child_report_sha256'] == (entry['child_report']['sha256'] if entry['child_report'] else None)
            and receipt['child_log_sha256'] == (entry['child_log']['sha256'] if entry['child_log'] else None),
            'R03_CI_ORIGINAL_ROW_BINDING')
        bounds[row['name']] = entry['planning_upper_ms']
    return data, bounds


def costs(path):
    return load(path)[1]


def material(path):
    """Bind original stdout and source manifests as well as the top-level data."""
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    descriptors = [data['source']['manifest']]
    for entry in data['observations']:
        descriptors.extend((entry['stdout'], entry['receipt']))
        descriptors.extend(entry[key] for key in ('child_report', 'child_log') if entry[key] is not None)
    return b'\0'.join([path.read_bytes().replace(b'\r\n', b'\n')] +
                      [(path.parent / item['path']).read_bytes() for item in descriptors])
