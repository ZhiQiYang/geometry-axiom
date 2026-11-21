"""Deterministic native-suite fragments; legacy files are bootstrap inputs only.

The checked-in fragments are the source. No generated aggregate is required at
runtime. A marker, or even one fragment directory, disables legacy fallback.
Historical CI bytes are retained verbatim under content-addressed filenames.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import urllib.request
import urllib.parse
import zipfile

SUITES = Path('tests/suites.d')
COSTS = Path('tests/native-costs.d')
SOURCES = Path('tests/registry-evidence/native')
LEGACY = Path('tests/registry-evidence/native-legacy.json')
MARKER = Path('tests/registry-layout.json')
SCHEMA = 'geometry-native-suite/1'
COST_SCHEMA = 'geometry-native-cost/1'
RUN_URL = 'https://github.com/ZhiQiYang/geometry-axiom/actions/runs/'
BUILTINS = frozenset(('c:integrity', 'core:run_tests', 'mutation:check',
                      'oracle:framing-selftest', 'node:polydraft', 'node:canvas_direct'))
KINDS = frozenset(('integrity', 'run_tests', 'mutation-check', 'python-script',
                   'unittest', 'node-test', 'node-script', 'node-canvas'))
EXIT_ONLY = frozenset(('mutation-check', 'python-script', 'node-script'))


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def measurement_binding(root, record):
    """Bind the measured suite itself, without invalidating unrelated product edits."""
    root = Path(root)
    declaration = {field: record[field] for field in ('name', 'execution', 'files')}
    files = {}
    for relative in record['files']:
        path = root / relative
        _safe_path(root, path)
        raw = path.read_bytes()
        files[relative] = {'bytes': len(raw), 'sha256': _sha(raw),
                           'lf_sha256': _sha(raw.replace(b'\r\n', b'\n'))}
    return {'name': record['name'], 'declaration_sha256': _sha(canonical_bytes(declaration)), 'files': files}


def key(name):
    if type(name) is not str or not re.fullmatch(r'[a-z][a-z0-9-]*:[A-Za-z0-9_-]+', name):
        raise ValueError('R386_NATIVE_SUITE_NAME: ' + repr(name))
    return name.replace(':', '__')


def active(root):
    root = Path(root)
    if (root / 'tests/.registry-migration-pending').exists():
        raise ValueError('R386_INTERRUPTED_MIGRATION: recover the pending transaction first')
    for relative in (MARKER, SUITES, COSTS, SOURCES, LEGACY):
        _safe_path(root, root / relative)
    return any((root / p).exists() for p in (MARKER, SUITES, COSTS, SOURCES, LEGACY))


def _read(path):
    try:
        data = path.read_bytes()
        if b'\r' in data or not data.endswith(b'\n'):
            raise ValueError('R386_NATIVE_PURE_LF: ' + str(path))
        return json.loads(data.decode('utf-8'), object_pairs_hook=_unique_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('R386_NATIVE_FRAGMENT_READ: ' + str(path)) from exc


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('R386_NATIVE_DUPLICATE_JSON_KEY: ' + key)
        result[key] = value
    return result


def _safe_path(root, path):
    # Keep every ancestor check on every read. Avoid Path.relative_to's
    # repeated parent-object construction across hundreds of fragments;
    # this is not a cached filesystem verdict.
    root_parts, path_parts = Path(root).parts, Path(path).parts
    if path_parts[:len(root_parts)] != root_parts:
        raise ValueError('R386_NATIVE_PATH_OUTSIDE_ROOT: ' + str(path))
    current = os.fspath(root)
    for part in path_parts[len(root_parts):]:
        current = os.path.join(current, part)
        try:
            mode = os.lstat(current).st_mode
        except (FileNotFoundError, NotADirectoryError):
            continue
        if stat.S_ISLNK(mode):
            raise ValueError('R386_NATIVE_SYMLINK: ' + str(current))


def _paths(root, folder):
    path = Path(root) / folder
    _safe_path(root, path)
    if not path.is_dir():
        raise ValueError('R386_NATIVE_DIRECTORY_REQUIRED: ' + str(folder))
    result = []
    for child in sorted(path.iterdir()):
        _safe_path(root, child)
        if not child.is_file() or child.suffix != '.json':
            raise ValueError('R386_NATIVE_UNEXPECTED_FRAGMENT_PATH: ' + str(child))
        result.append(child)
    return result


def _relative(value):
    return (isinstance(value, str) and bool(value) and '\\' not in value
            and not PurePosixPath(value).is_absolute()
            and all(p not in ('', '.', '..') for p in value.split('/')))


def _expected(entry, kind):
    if kind in EXIT_ONLY:
        return entry == {'mode': 'exit-code-only'}
    return (type(entry) is dict and set(entry) == {'mode', 'count', 'unit'}
            and entry['mode'] == 'count' and type(entry['count']) is int
            and entry['count'] > 0 and type(entry['unit']) is str and bool(entry['unit']))


def load_registry(root, *, allow_pending=False):
    """Read every fragment, reject partial migration, duplicates and missing files.

    Disk census against the explicit browser/fixture exclusions remains in
    run_all.check_registry; this function also guards the non-test built-ins.
    """
    root = Path(root).resolve()
    active(root)  # Fail closed while the deterministic writer is interrupted.
    paths = _paths(root, SUITES)
    if not paths:
        raise ValueError('R386_NATIVE_SUITE_FRAGMENTS_REQUIRED')
    records, names, orders, owners = [], set(), set(), {}
    for path in paths:
        row = _read(path)
        if type(row) is not dict or set(row) != {'schema', 'name', 'order', 'execution', 'files', 'expected'}:
            raise ValueError('R386_NATIVE_SUITE_SHAPE: ' + str(path))
        name = row['name']
        if row['schema'] != SCHEMA or path.name != key(name) + '.json' or name in names:
            raise ValueError('R386_NATIVE_UNIQUE_SUITE: ' + str(path))
        order = row['order']
        if (not isinstance(order, str) or not re.fullmatch(r'(?:legacy/[0-9]{6}|new/[A-Za-z0-9_-]+)', order)
                or order in orders):
            raise ValueError('R386_NATIVE_STABLE_ORDER: ' + name)
        execution = row['execution']
        if (type(execution) is not dict or set(execution) != {
                'kind', 'cmd', 'needs', 'timeout', 'needs_node', 'extra_env', 'label'}
                or execution['kind'] not in KINDS
                or type(execution['timeout']) is not int or not 0 < execution['timeout'] <= 1200
                or type(execution['needs_node']) is not bool
                or type(execution['needs']) is not list
                or any(type(n) is not str or not n for n in execution['needs'])
                or len(set(execution['needs'])) != len(execution['needs'])
                or type(execution['extra_env']) is not dict
                or any(type(k) is not str or type(v) is not str for k, v in execution['extra_env'].items())
                or type(execution['label']) is not str):
            raise ValueError('R386_NATIVE_EXECUTION_SHAPE: ' + name)
        cmd = execution['cmd']
        if cmd is not None and (type(cmd) is not list or not cmd or any(type(c) is not str for c in cmd)):
            raise ValueError('R386_NATIVE_COMMAND: ' + name)
        if execution['kind'] not in ('integrity', 'run_tests') and cmd is None:
            raise ValueError('R386_NATIVE_COMMAND_REQUIRED: ' + name)
        files = row['files']
        if (type(files) is not list or not files or len(set(files)) != len(files)
                or any(not _relative(f) or not (root / f).is_file() for f in files)):
            raise ValueError('R386_NATIVE_FILE_COVERAGE: ' + name)
        for file in files:
            _safe_path(root, root / file)
            if file in owners:
                raise ValueError('R386_NATIVE_DUPLICATE_FILE_OWNER: ' + file)
            owners[file] = name
        if execution['kind'] == 'unittest' and (
                len(files) != 1 or name != 'py:' + Path(files[0]).stem
                or cmd != ['{python}', '{root}/tests/_unittest_runner.py', '{root}/' + files[0]]):
            raise ValueError('R386_NATIVE_EXECUTION_FILE_BINDING: ' + name)
        if execution['kind'] == 'node-test' and cmd != ['--test', '--test-reporter=spec', *files]:
            raise ValueError('R386_NATIVE_EXECUTION_FILE_BINDING: ' + name)
        pending = (allow_pending and order.startswith('new/')
                   and row['expected'] == {'mode': 'pending-ci-census'})
        if not pending and not _expected(row['expected'], execution['kind']):
            raise ValueError('R386_NATIVE_EXACT_EXPECTED: ' + name)
        names.add(name)
        orders.add(order)
        records.append(row)
    if not BUILTINS <= names:
        raise ValueError('R386_NATIVE_BUILTIN_COVERAGE: ' + repr(sorted(BUILTINS - names)))
    return sorted(records, key=lambda row: (row['order'], row['name']))


def expected(root, *, allow_pending=False):
    return {'suites': {r['name']: r['expected'] for r in load_registry(root, allow_pending=allow_pending)}}


def expected_bytes(root, *, allow_pending=False):
    return canonical_bytes(expected(root, allow_pending=allow_pending))


def expected_digest(root, *, allow_pending=False):
    return _sha(expected_bytes(root, allow_pending=allow_pending))


def init_suite(root, *, name, file, kind, needs=()):
    """Declare one new suite without guessing a count or a duration.

    Only measurement mode accepts pending-ci-census. Formal CI refuses until
    import_ci_cost derives the exact count from the original CI artifact.
    """
    root = Path(root)
    records = load_registry(root, allow_pending=True)
    if name in {row['name'] for row in records} or kind not in ('unittest', 'node-test'):
        raise ValueError('R386_NATIVE_INIT_NEW_COUNTED_SUITE_ONLY')
    if not _relative(file) or not (root / file).is_file() or not file.startswith('tests/'):
        raise ValueError('R386_NATIVE_INIT_FILE_REQUIRED')
    if any(file in row['files'] for row in records):
        raise ValueError('R386_NATIVE_INIT_FILE_ALREADY_OWNED')
    if kind == 'unittest':
        if name != 'py:' + Path(file).stem or not file.endswith('.py'):
            raise ValueError('R386_NATIVE_INIT_PYTHON_IDENTITY')
        cmd, timeout = ['{python}', '{root}/tests/_unittest_runner.py', '{root}/' + file], 1200
    else:
        if not name.startswith('node:') or Path(file).suffix not in ('.js', '.cjs', '.mjs'):
            raise ValueError('R386_NATIVE_INIT_NODE_IDENTITY')
        cmd, timeout = ['--test', '--test-reporter=spec', file], 300
    record = {'schema': SCHEMA, 'name': name, 'order': 'new/' + key(name), 'files': [file],
              'execution': {'kind': kind, 'cmd': cmd, 'needs': list(needs), 'timeout': timeout,
                            'needs_node': kind == 'node-test', 'extra_env': {}, 'label': file},
              'expected': {'mode': 'pending-ci-census'}}
    path = root / SUITES / (key(name) + '.json')
    if path.exists():
        raise ValueError('R386_NATIVE_INIT_REFUSES_OVERWRITE')
    path.write_bytes(canonical_bytes(record))
    try:
        load_registry(root, allow_pending=True)
    except Exception:
        path.unlink()
        raise
    return {'path': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size,
            'sha256': _sha(path.read_bytes()), 'acceptance': False}


def update_expected(root, entries):
    """Only run_all's existing complete-census gate may call this writer."""
    root = Path(root)
    records = load_registry(root)
    if set(entries) != {r['name'] for r in records}:
        raise ValueError('R386_NATIVE_CENSUS_MUST_BE_COMPLETE')
    for row in records:
        value = entries[row['name']]
        if not _expected(value, row['execution']['kind']):
            raise ValueError('R386_NATIVE_EXACT_EXPECTED: ' + row['name'])
    for row in records:
        if row['expected'] != entries[row['name']]:
            row['expected'] = entries[row['name']]
            (root / SUITES / (key(row['name']) + '.json')).write_bytes(canonical_bytes(row))


def _source(root, digest):
    if not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
        raise ValueError('R386_NATIVE_COST_SOURCE_HASH')
    path = Path(root) / SOURCES / (digest + '.json')
    _safe_path(root, path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError('R386_NATIVE_COST_RECEIPT_REQUIRED: ' + digest) from exc
    if _sha(raw) != digest:
        raise ValueError('R386_NATIVE_COST_SOURCE_BYTES: ' + digest)
    return _read(path)


def _added(data):
    if (type(data) is not dict or set(data) != {'schema', 'source_run', 'source_head',
            'source_checkout', 'note', 'observations'}
            or data['schema'] != 'native-shard-added-suite-evidence/1'
            or not re.fullmatch(re.escape(RUN_URL) + r'[0-9]+', data['source_run'])
            or not re.fullmatch(r'[a-f0-9]{40}', data['source_head'])
            or not re.fullmatch(r'[a-f0-9]{40}', data['source_checkout'])
            or type(data['note']) is not str or not data['note']
            or type(data['observations']) is not list or not data['observations']):
        raise ValueError('R386_NATIVE_LEGACY_COST_PROVENANCE')
    result = {}
    for row in data['observations']:
        if type(row) is not dict or set(row) != {'name', 'source_job', 'discovered', 'passed',
                                                'seconds_rounded', 'planning_upper_ms'}:
            raise ValueError('R386_NATIVE_LEGACY_COST_ROW')
        name, seconds, upper = row['name'], row['seconds_rounded'], row['planning_upper_ms']
        if (type(name) is not str or not name or name in result
                or not re.fullmatch(re.escape(data['source_run']) + r'/job/[0-9]+', row['source_job'])
                or type(row['discovered']) is not int or row['discovered'] < 1
                or type(row['passed']) is not int or row['passed'] != row['discovered']
                or type(seconds) not in (int, float) or not 0 < seconds < 1200
                or type(upper) is not int or not seconds * 1000 < upper < 1200000):
            raise ValueError('R386_NATIVE_LEGACY_COST_PASSED_AND_MARGIN')
        result[name] = upper
    return result


def _added_receipts(data):
    """Use source-bound, passing child rows without relabeling a failed CI job.

    Keep exit-only rows as exit-only. Their passed=1 is the runner's success
    sentinel, not an independently discovered test. Bounds are planning costs.
    """
    def matches(pattern, value):
        return type(value) is str and re.fullmatch(pattern, value) is not None

    if (type(data) is not dict or set(data) != {'schema', 'runs'}
            or data['schema'] != 'native-shard-added-receipts/1'
            or type(data['runs']) is not list or not data['runs']):
        raise ValueError('R396_ADDED_RECEIPT_SCHEMA')
    bounds, seen_runs = {}, set()
    for source in data['runs']:
        if (type(source) is not dict or set(source) != {
                'source_run', 'source_head', 'source_checkout', 'note', 'shards'}
                or not matches(r'https://github\.com/ZhiQiYang/geometry-axiom/actions/runs/[0-9]+',
                               source['source_run'])
                or source['source_run'] in seen_runs
                or not matches(r'[a-f0-9]{40}', source['source_head'])
                or not matches(r'[a-f0-9]{40}', source['source_checkout'])
                or type(source['note']) is not str or not source['note']
                or type(source['shards']) is not list or not source['shards']):
            raise ValueError('R396_ADDED_RECEIPT_SOURCE')
        seen_runs.add(source['source_run'])
        seen_shards = set()
        for shard in source['shards']:
            if (type(shard) is not dict or set(shard) != {
                    'source_job', 'shard', 'artifact_id', 'artifact_sha256',
                    'receipt_file', 'receipt_sha256', 'observations'}
                    or not matches(re.escape(source['source_run']) + r'/job/[0-9]+',
                                   shard['source_job'])
                    or type(shard['shard']) is not list or len(shard['shard']) != 2
                    or any(type(n) is not int for n in shard['shard'])
                    or not 1 <= shard['shard'][0] <= shard['shard'][1]
                    or tuple(shard['shard']) in seen_shards
                    or type(shard['artifact_id']) is not int or shard['artifact_id'] <= 0
                    or not matches(r'[a-f0-9]{64}', shard['artifact_sha256'])
                    or not matches(r'[a-f0-9]{64}', shard['receipt_sha256'])
                    or shard['receipt_file'] != 'shard-%s.json' % shard['shard'][0]
                    or type(shard['observations']) is not list or not shard['observations']):
                raise ValueError('R396_ADDED_RECEIPT_SHARD')
            seen_shards.add(tuple(shard['shard']))
            for entry in shard['observations']:
                if type(entry) is not dict or set(entry) != {'row', 'planning_upper_ms'}:
                    raise ValueError('R396_ADDED_RECEIPT_ENTRY')
                row, upper = entry['row'], entry['planning_upper_ms']
                if (type(row) is not dict or set(row) != {
                        'name', 'counted', 'total', 'passed', 'failed', 'skipped',
                        'seconds', 'ran', 'process_exit_code', 'allowed_skips',
                        'env_problem', 'crashed', 'expected_problem'}
                        or type(row['name']) is not str or not row['name']
                        or row['name'] in bounds
                        or any(type(row[key]) is not int or row[key] < 0 for key in
                               ('total', 'passed', 'failed', 'skipped', 'allowed_skips'))
                        or any(type(row[key]) is not bool for key in
                               ('counted', 'ran', 'env_problem', 'crashed'))
                        or type(row['process_exit_code']) is not int or row['process_exit_code'] != 0
                        or not row['ran'] or row['failed'] or row['skipped'] or row['allowed_skips']
                        or row['env_problem'] or row['crashed']
                        or type(row['expected_problem']) is not str
                        or type(row['seconds']) not in (int, float)
                        or not math.isfinite(row['seconds']) or not 0 < row['seconds'] < 1200
                        or type(upper) is not int or not row['seconds'] * 1000 < upper < 1200000):
                    raise ValueError('R396_ADDED_RECEIPT_PASS_AND_MARGIN')
                if row['counted']:
                    valid = row['total'] > 0 and row['passed'] == row['total']
                else:
                    valid = row['total'] == 0 and row['passed'] == 1
                if not valid:
                    raise ValueError('R396_ADDED_RECEIPT_COUNT_MODE')
                bounds[row['name']] = upper
    return bounds


def _historical(data):
    if data.get('schema') != 'native-ci-timings/1':
        raise ValueError('R386_NATIVE_HISTORICAL_COST_SCHEMA')
    runs = data['measured_runs']
    if len(runs) < 2:
        raise ValueError('R386_NATIVE_TWO_REAL_MEASUREMENTS_REQUIRED')
    profiles = []
    for run in runs:
        merged = {}
        for shard in run['shards']:
            values = shard['timings_ms']
            if merged.keys() & values.keys() or any(
                    type(name) is not str or not name or type(ms) is not int or ms <= 0
                    for name, ms in values.items()):
                raise ValueError('R386_NATIVE_HISTORICAL_OVERLAP_OR_COST')
            merged.update(values)
        if (not merged or len(merged) != run['suite_count']
                or profiles and merged.keys() != profiles[0].keys()):
            raise ValueError('R386_NATIVE_HISTORICAL_COVERAGE')
        profiles.append(merged)
    weights = data['timings_ms']
    if any(type(v) is not int or v <= 0 for v in weights.values()):
        raise ValueError('R386_NATIVE_HISTORICAL_POSITIVE_COST')
    return weights, profiles


def _git_bytes(root, revision, path):
    result = subprocess.run(['git', '-C', str(root), 'show', revision + ':' + path],
                            capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise ValueError('R386_NATIVE_BASE_ORIGINAL_REQUIRED: ' + path)
    return result.stdout


def _legacy_base_sources(root, base_sha):
    if not re.fullmatch(r'[a-f0-9]{40}', base_sha or ''):
        raise ValueError('R386_NATIVE_LEGACY_BASE_FULL_SHA_REQUIRED')
    result = subprocess.run(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', base_sha, '--', 'tests'],
                            capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        raise ValueError('R386_NATIVE_LEGACY_BASE_GIT_TREE_REQUIRED')
    paths = [path for path in result.stdout.splitlines()
             if path == 'tests/native_shard_timings.json'
             or path == 'tests/native_shard_added_receipts.json'
             or re.fullmatch(r'tests/native_shard_added_evidence[A-Za-z0-9_]*\.json', path)]
    if 'tests/native_shard_timings.json' not in paths:
        raise ValueError('R386_NATIVE_LEGACY_TIMINGS_ORIGINAL_REQUIRED')
    sources, originals, names = [], {}, set()
    for path in sorted(paths):
        raw = _git_bytes(root, base_sha, path)
        data = json.loads(raw, object_pairs_hook=_unique_keys)
        if path.endswith('/native_shard_timings.json'):
            _, profiles = _historical(data)
            kind, suites = 'historical-timings', sorted(profiles[0])
        elif path.endswith('/native_shard_added_receipts.json'):
            kind, suites = 'historical-receipts', sorted(_added_receipts(data))
        else:
            kind, suites = 'historical-added', sorted(_added(data))
        if names & set(suites):
            raise ValueError('R386_NATIVE_LEGACY_BASE_DUPLICATE_SUITE')
        names.update(suites)
        sources.append({'path': path, 'sha256': _sha(raw), 'kind': kind, 'suites': suites})
        originals[path] = raw
    return {'schema': 'geometry-native-legacy/1', 'base_sha': base_sha, 'sources': sources}, originals


def _legacy_catalog(root):
    root = Path(root)
    _safe_path(root, root / LEGACY)
    catalog = _read(root / LEGACY)
    if (type(catalog) is not dict or set(catalog) != {'schema', 'base_sha', 'sources'}
            or catalog['schema'] != 'geometry-native-legacy/1'
            or not re.fullmatch(r'[a-f0-9]{40}', str(catalog['base_sha']))
            or type(catalog['sources']) is not list or not catalog['sources']):
        raise ValueError('R386_NATIVE_LEGACY_CATALOG_SHAPE')
    paths, names, hashes = set(), set(), set()
    for source in catalog['sources']:
        if (type(source) is not dict or set(source) != {'path', 'sha256', 'kind', 'suites'}
                or source['kind'] not in ('historical-timings', 'historical-added', 'historical-receipts')
                or source['path'] in paths or not re.fullmatch(
                    r'tests/native_shard_(?:timings|added_receipts|added_evidence[A-Za-z0-9_]*)\.json', str(source['path']))
                or not re.fullmatch(r'[a-f0-9]{64}', str(source['sha256']))
                or source['sha256'] in hashes or type(source['suites']) is not list
                or not source['suites'] or source['suites'] != sorted(set(source['suites']))
                or names & set(source['suites'])):
            raise ValueError('R386_NATIVE_LEGACY_CATALOG_UNIQUE_SOURCES_AND_SUITES')
        data = _source(root, source['sha256'])
        suites = (sorted(_historical(data)[1][0]) if source['kind'] == 'historical-timings'
                  else sorted(_added_receipts(data)) if source['kind'] == 'historical-receipts'
                  else sorted(_added(data)))
        if suites != source['suites']:
            raise ValueError('R386_NATIVE_LEGACY_CATALOG_REAL_OBSERVATIONS')
        paths.add(source['path'])
        hashes.add(source['sha256'])
        names.update(suites)
    return catalog


def _verify_legacy_catalog(root, trusted_ref):
    root = Path(root)
    catalog = _legacy_catalog(root)
    if trusted_ref is None:
        raise ValueError('R386_NATIVE_LEGACY_REQUIRES_EXPLICIT_TRUSTED_BASE')
    try:
        before = _git_bytes(root, trusted_ref, LEGACY.as_posix())
    except ValueError:
        before = None
    if before is not None:
        if before != (root / LEGACY).read_bytes():
            raise ValueError('R386_NATIVE_LEGACY_CATALOG_IS_IMMUTABLE')
        return {'source': 'trusted-base-catalog-blob', 'sha': trusted_ref}
    original, _ = _legacy_base_sources(root, trusted_ref)
    if catalog['sources'] != original['sources']:
        raise ValueError('R386_NATIVE_LEGACY_NOT_IN_TRUSTED_BASE')
    return {'source': 'trusted-base-original-files', 'sha': trusted_ref}


def _receipt_original(data):
    """Validate original API metadata + report, never a user-entered duration.

    The importer must fetch these originals from GitHub. This offline guard
    binds their identities and exact bytes; it does not label fixture JSON as
    independently authenticated evidence.
    """
    if (type(data) is not dict or set(data) != {'schema', 'run', 'job', 'checkout', 'artifact',
                                              'report', 'archive_base64', 'member', 'api_originals'}
            or data['schema'] != 'geometry-native-ci-receipt/1'):
        raise ValueError('R386_NATIVE_REAL_CI_RECEIPT_REQUIRED')
    run, job, checkout, report = (data[k] for k in ('run', 'job', 'checkout', 'report'))
    artifact = data['artifact']
    if any(type(value) is not dict for value in (run, job, checkout, artifact, report)):
        raise ValueError('R386_NATIVE_ORIGINAL_CI_OBJECT_SHAPE')
    binding = report.get('suite_binding')
    if (report.get('source_stable') is not True or type(binding) is not dict
            or set(binding) != {'name', 'declaration_sha256', 'files'}
            or type(binding['name']) is not str
            or not re.fullmatch(r'[a-f0-9]{64}', str(binding['declaration_sha256']))
            or type(binding['files']) is not dict or not binding['files']):
        raise ValueError('R386_NATIVE_ORIGINAL_SUITE_BINDING_REQUIRED')
    for path, fingerprint in binding['files'].items():
        if (not _relative(path) or type(fingerprint) is not dict
                or set(fingerprint) != {'bytes', 'sha256', 'lf_sha256'}
                or type(fingerprint['bytes']) is not int or fingerprint['bytes'] < 0
                or any(not re.fullmatch(r'[a-f0-9]{64}', str(fingerprint[field]))
                       for field in ('sha256', 'lf_sha256'))):
            raise ValueError('R386_NATIVE_ORIGINAL_SUITE_FILE_HASHES')
    try:
        for field in ('run', 'job', 'checkout', 'artifact'):
            if json.loads(data['api_originals'][field], object_pairs_hook=_unique_keys) != data[field]:
                raise ValueError('R386_NATIVE_ORIGINAL_API_BYTES: ' + field)
        archive = base64.b64decode(data['archive_base64'], validate=True)
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            members = [entry for entry in bundle.infolist() if entry.filename == data['member']]
            if len(members) != 1 or not _relative(data['member']) or members[0].file_size > 16000000:
                raise ValueError('R386_NATIVE_ORIGINAL_REPORT_MEMBER')
            raw_report = bundle.read(members[0])
        if json.loads(raw_report.decode('utf-8'), object_pairs_hook=_unique_keys) != report:
            raise ValueError('R386_NATIVE_ORIGINAL_REPORT_BYTES')
        if artifact.get('digest') and artifact['digest'] != 'sha256:' + _sha(archive):
            raise ValueError('R386_NATIVE_ORIGINAL_ARTIFACT_DIGEST')
    except (KeyError, TypeError, UnicodeError, zipfile.BadZipFile, ValueError) as exc:
        raise ValueError('R386_NATIVE_ORIGINAL_CI_ARTIFACT_REQUIRED') from exc
    run_id, job_id = run.get('id'), job.get('id')
    if (type(run_id) is not int or type(job_id) is not int
            or type(run.get('run_attempt')) is not int or run['run_attempt'] < 1
            or run.get('html_url') != RUN_URL + str(run_id)
            or job.get('html_url') != RUN_URL + str(run_id) + '/job/' + str(job_id)
            or job.get('run_id') != run_id or job.get('head_sha') != run.get('head_sha')
            or job.get('run_attempt') != run['run_attempt']
            or artifact.get('workflow_run', {}).get('id') != run_id
            or artifact.get('workflow_run', {}).get('head_sha') != run.get('head_sha')
            or not re.fullmatch(r'[a-f0-9]{40}', str(run.get('head_sha')))
            or run.get('status') != 'completed' or job.get('status') != 'completed'
            or checkout.get('sha') != report.get('commit_sha')
            or run['head_sha'] not in {checkout.get('sha'), *(p.get('sha') for p in checkout.get('parents', []))}
            or report.get('schema') != 'geometry-native-measurement/1'):
        raise ValueError('R386_NATIVE_CI_RUN_JOB_CHECKOUT_BINDING')
    if report['schema'] == 'geometry-native-measurement/1' and (
            report.get('acceptance') is not False or report.get('ci_run_id') != str(run_id)
            or report.get('ci_run_attempt') != str(run.get('run_attempt'))):
        raise ValueError('R386_NATIVE_MEASUREMENT_IS_NOT_ACCEPTANCE')
    from native_shard_receipts import validate_rows
    selected, rows = report.get('selected'), report.get('rows')
    if (selected != [binding['name']] or type(rows) is not list or len(rows) != 1
            or rows[0].get('name') != binding['name']):
        raise ValueError('R386_NATIVE_ORIGINAL_NAMED_MEASUREMENT')
    row = rows[0]
    original_expected = ({'mode': 'count', 'count': row['total']} if row.get('counted')
                         else {'mode': 'exit-code-only'})
    validate_rows(selected, rows, {binding['name']: original_expected})
    if (row['counted'] and row['total'] <= 0 or type(row.get('seconds')) not in (int, float)
            or not math.isfinite(row['seconds']) or not 0 < row['seconds'] < 1200):
        raise ValueError('R386_NATIVE_ORIGINAL_MEASURED_COUNT_AND_SECONDS')
    return report


def _new_receipt(data, row, expected_entry, *, root, record):
    report = _receipt_original(data)
    if report['suite_binding'] != measurement_binding(root, record):
        raise ValueError('R386_NATIVE_STALE_SUITE_SOURCE_OR_EXECUTION: ' + row['name'])
    rows = [r for r in report.get('rows', []) if r.get('name') == row['name']]
    if len(rows) != 1 or report.get('selected', []).count(row['name']) != 1:
        raise ValueError('R386_NATIVE_CI_NAMED_SUITE_REQUIRED')
    measured = rows[0]
    from native_shard_receipts import validate_rows
    validate_rows([row['name']], [measured], {row['name']: expected_entry})
    seconds, upper = measured.get('seconds'), row.get('planning_upper_ms')
    if (type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds < 1200
            or type(upper) is not int or not seconds * 1000 < upper < 1200000):
        raise ValueError('R386_NATIVE_CI_OBSERVED_COST_AND_MARGIN')
    return upper


class _GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        destination = urllib.parse.urlparse(new_url)
        if destination.scheme != 'https':
            raise ValueError('R386_NATIVE_CI_REDIRECT_REQUIRES_HTTPS')
        redirected = super().redirect_request(request, fp, code, message, headers, new_url)
        if redirected is not None and (destination.hostname != 'api.github.com' or destination.port not in (None, 443)):
            redirected.remove_header('Authorization')
        return redirected


def _github_bytes(endpoint):
    if not endpoint.startswith('/') or '..' in endpoint:
        raise ValueError('R386_NATIVE_GITHUB_ENDPOINT')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'geometry-axiom-registry',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    url = 'https://api.github.com/repos/ZhiQiYang/geometry-axiom' + endpoint
    opener = urllib.request.build_opener(_GitHubRedirect())
    with opener.open(urllib.request.Request(url, headers=headers), timeout=30) as response:
        raw = response.read(32000001)
    if len(raw) > 32000000:
        raise ValueError('R386_NATIVE_CI_ARTIFACT_TOO_LARGE')
    return raw


def import_ci_cost(root, out_root, *, name, run_id, job_id, artifact_id, member, planning_upper_ms,
                   fetch=None):
    """Fetch real GitHub originals. The only caller-selected cost is a strict upper margin."""
    root, out_root = Path(root), Path(out_root)
    fetch = fetch or _github_bytes
    records = {row['name']: row for row in load_registry(root, allow_pending=True)}
    if name not in records:
        raise ValueError('R386_NATIVE_IMPORT_SUITE_MUST_BE_REGISTERED')
    if any(type(value) is not int or value <= 0 for value in (run_id, job_id, artifact_id)):
        raise ValueError('R386_NATIVE_IMPORT_CI_IDENTIFIERS')
    raw = {'job': fetch('/actions/jobs/%d' % job_id),
           'artifact': fetch('/actions/artifacts/%d' % artifact_id)}
    data = {field: json.loads(value, object_pairs_hook=_unique_keys) for field, value in raw.items()}
    archive = fetch('/actions/artifacts/%d/zip' % artifact_id)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        matches = [entry for entry in bundle.infolist() if entry.filename == member]
        if len(matches) != 1 or not _relative(member) or matches[0].file_size > 16000000:
            raise ValueError('R386_NATIVE_IMPORT_REPORT_MEMBER')
        report = json.loads(bundle.read(matches[0]), object_pairs_hook=_unique_keys)
    attempt = report.get('ci_run_attempt')
    if type(attempt) is not str or not re.fullmatch(r'[1-9][0-9]*', attempt):
        raise ValueError('R386_NATIVE_IMPORT_RUN_ATTEMPT_REQUIRED')
    # A later rerun must not relabel the original artifact as a newer attempt.
    raw['run'] = fetch('/actions/runs/%d/attempts/%s' % (run_id, attempt))
    data['run'] = json.loads(raw['run'], object_pairs_hook=_unique_keys)
    checkout_sha = report.get('commit_sha', '')
    if not re.fullmatch('[a-f0-9]{40}', checkout_sha):
        raise ValueError('R386_NATIVE_IMPORT_CHECKOUT')
    raw['checkout'] = fetch('/git/commits/' + checkout_sha)
    data['checkout'] = json.loads(raw['checkout'], object_pairs_hook=_unique_keys)
    source = dict(schema='geometry-native-ci-receipt/1', **data, report=report,
                  archive_base64=base64.b64encode(archive).decode('ascii'), member=member,
                  api_originals={field: value.decode('utf-8') for field, value in raw.items()})
    cost = {'schema': COST_SCHEMA, 'name': name, 'kind': 'ci-report',
            'planning_upper_ms': planning_upper_ms, 'source_sha256': _sha(canonical_bytes(source))}
    declaration = records[name]
    pending = declaration['expected'] == {'mode': 'pending-ci-census'}
    if pending:
        measured = [r for r in report.get('rows', []) if r.get('name') == name]
        if (len(measured) != 1 or type(measured[0].get('total')) is not int or measured[0]['total'] <= 0
                or report.get('schema') != 'geometry-native-measurement/1'
                or report.get('census_pending') is not True):
            raise ValueError('R386_NATIVE_PENDING_REQUIRES_REAL_CENSUS')
        declaration = dict(declaration, expected={'mode': 'count', 'count': measured[0]['total'],
            'unit': 'test' if declaration['execution']['kind'] == 'unittest' else 'node test'})
        if report.get('expected_candidate') != declaration['expected']:
            raise ValueError('R386_NATIVE_PENDING_CANDIDATE_MUST_MATCH_ACTUAL_COUNT')
    _new_receipt(source, cost, declaration['expected'], root=root, record=declaration)
    payloads = {SOURCES / (cost['source_sha256'] + '.json'): canonical_bytes(source),
                COSTS / (key(name) + '.json'): canonical_bytes(cost)}
    if pending:
        payloads[SUITES / (key(name) + '.json')] = canonical_bytes(declaration)
    for rel, value in payloads.items():
        target = out_root / rel
        pending_target = pending and rel == SUITES / (key(name) + '.json')
        if target.exists() and target.read_bytes() != value and not (
                pending_target and target.read_bytes() == canonical_bytes(records[name])):
            raise ValueError('R386_NATIVE_IMPORT_REFUSES_OVERWRITE: ' + str(rel))
    for rel, value in payloads.items():
        target = out_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    return [{'path': rel.as_posix(), 'bytes': len(value), 'sha256': _sha(value)}
            for rel, value in sorted(payloads.items())]


def verify_ci_sources(root, fetch=None, *, trusted_ref=None):
    """Reauthenticate all new CI sources against GitHub; unavailable is an error."""
    root = Path(root)
    fetch = fetch or _github_bytes
    if trusted_ref is not None and not re.fullmatch(r'[a-f0-9]{40}', trusted_ref):
        raise ValueError('R386_NATIVE_TRUSTED_BASE_FULL_SHA_REQUIRED')
    timing_profile(root)
    legacy_anchor = _verify_legacy_catalog(root, trusted_ref)
    legacy_count = len(_legacy_catalog(root)['sources'])
    # Retired original receipts remain immutable history. They are still
    # authenticated; only active cost pointers contribute planning weights.
    digests = {path.stem for path in _paths(root, SOURCES)
               if _read(path).get('schema') == 'geometry-native-ci-receipt/1'}
    inherited, verified = 0, 0
    for digest in sorted(digests):
        if trusted_ref is not None:
            relative = (SOURCES / (digest + '.json')).as_posix()
            before = subprocess.run(['git', '-C', str(root), 'show', trusted_ref + ':' + relative],
                                    capture_output=True, timeout=30, check=False)
            current = (root / relative).read_bytes()
            if before.returncode == 0 and before.stdout == current and _sha(before.stdout) == digest:
                inherited += 1
                continue
        source = _source(root, digest)
        run, job, artifact = source['run'], source['job'], source['artifact']
        fresh_run = json.loads(fetch('/actions/runs/%d/attempts/%d' % (run['id'], run['run_attempt'])))
        fresh_job = json.loads(fetch('/actions/jobs/%d' % job['id']))
        fresh_artifact = json.loads(fetch('/actions/artifacts/%d' % artifact['id']))
        fresh_checkout = json.loads(fetch('/git/commits/' + source['checkout']['sha']))
        for before, after, fields in (
                (run, fresh_run, ('id', 'head_sha', 'run_attempt', 'html_url')),
                (job, fresh_job, ('id', 'run_id', 'head_sha', 'html_url')),
                (artifact, fresh_artifact, ('id', 'name', 'workflow_run', 'size_in_bytes')),
                (source['checkout'], fresh_checkout, ('sha', 'parents'))):
            if any(before.get(field) != after.get(field) for field in fields):
                raise ValueError('R386_NATIVE_LIVE_CI_IDENTITY: ' + digest)
        archive = fetch('/actions/artifacts/%d/zip' % artifact['id'])
        if archive != base64.b64decode(source['archive_base64'], validate=True):
            raise ValueError('R386_NATIVE_LIVE_CI_BYTES: ' + digest)
        verified += 1
    return {'verified_online': verified, 'inherited_from_base': inherited,
            'trusted_base': trusted_ref, 'legacy_inherited': legacy_count,
            'legacy_anchor': legacy_anchor, 'status': 'verified'}


def timing_profile(root):
    """Return real measured scenarios and added upper bounds, with exact coverage."""
    root = Path(root)
    registry = {r['name']: r for r in load_registry(root)}
    catalog = _legacy_catalog(root)
    allowed_legacy = {s['sha256']: s for s in catalog['sources']}
    records = {}
    for path in _paths(root, COSTS):
        row = _read(path)
        if (type(row) is not dict or row.get('schema') != COST_SCHEMA
                or set(row) not in ({'schema', 'name', 'kind', 'source_sha256'},
                                    {'schema', 'name', 'kind', 'source_sha256', 'planning_upper_ms'})
                or path.name != key(row['name']) + '.json' or row['name'] in records):
            raise ValueError('R386_NATIVE_UNIQUE_COST: ' + str(path))
        records[row['name']] = row
    if records.keys() != registry.keys():
        raise ValueError('R386_NATIVE_EXACT_COST_COVERAGE: missing=%r extra=%r' %
                         (sorted(registry.keys() - records.keys()), sorted(records.keys() - registry.keys())))
    sources = {path.stem: _source(root, path.stem) for path in _paths(root, SOURCES)}
    for source_hash, data in sources.items():
        schema = data.get('schema')
        if schema == 'native-ci-timings/1':
            if source_hash not in allowed_legacy:
                raise ValueError('R386_NATIVE_NEW_SOURCE_CANNOT_CLAIM_LEGACY')
            _historical(data)
        elif schema == 'native-shard-added-suite-evidence/1':
            if source_hash not in allowed_legacy:
                raise ValueError('R386_NATIVE_NEW_SOURCE_CANNOT_CLAIM_LEGACY')
            _added(data)
        elif schema == 'native-shard-added-receipts/1':
            if source_hash not in allowed_legacy:
                raise ValueError('R386_NATIVE_NEW_SOURCE_CANNOT_CLAIM_LEGACY')
            _added_receipts(data)
        elif schema == 'geometry-native-ci-receipt/1':
            _receipt_original(data)
        else:
            raise ValueError('R386_NATIVE_UNKNOWN_COST_SOURCE_SCHEMA')
    for row in records.values():
        if row['source_sha256'] not in sources:
            raise ValueError('R386_NATIVE_COST_RECEIPT_REQUIRED: ' + row['source_sha256'])
    historical = {r['source_sha256'] for r in records.values() if r['kind'] == 'historical-timings'}
    if len(historical) != 1:
        raise ValueError('R386_NATIVE_HISTORICAL_SCENARIOS_REQUIRED')
    history = next(iter(historical))
    weights, profiles = _historical(sources[history])
    profiles = [dict(p) for p in profiles]
    added, legacy_names = {}, set()
    for name, row in records.items():
        if row['kind'].startswith('historical-') and (
                row['source_sha256'] not in allowed_legacy
                or allowed_legacy[row['source_sha256']]['kind'] != row['kind']
                or name not in allowed_legacy[row['source_sha256']]['suites']):
            raise ValueError('R386_NATIVE_NEW_SUITE_CANNOT_CLAIM_LEGACY')
        if row['kind'] == 'historical-timings':
            if row['source_sha256'] != history or name not in profiles[0] or 'planning_upper_ms' in row:
                raise ValueError('R386_NATIVE_HISTORICAL_NAMED_OBSERVATION: ' + name)
            legacy_names.add(name)
        elif row['kind'] == 'historical-added':
            bounds = _added(sources[row['source_sha256']])
            if name not in bounds or 'planning_upper_ms' in row:
                raise ValueError('R386_NATIVE_ADDED_NAMED_OBSERVATION: ' + name)
            added[name] = bounds[name]
        elif row['kind'] == 'historical-receipts':
            bounds = _added_receipts(sources[row['source_sha256']])
            if name not in bounds or 'planning_upper_ms' in row:
                raise ValueError('R386_NATIVE_ADDED_NAMED_OBSERVATION: ' + name)
            added[name] = bounds[name]
        elif row['kind'] == 'ci-report':
            added[name] = _new_receipt(sources[row['source_sha256']], row, registry[name]['expected'],
                                       root=root, record=registry[name])
        else:
            raise ValueError('R386_NATIVE_COST_KIND: ' + name)
    if legacy_names != profiles[0].keys() or legacy_names & added.keys():
        raise ValueError('R386_NATIVE_NO_REWRITE_HISTORICAL_UNIVERSE')
    for profile in profiles:
        profile.update(added)
        if profile.keys() != registry.keys():
            raise ValueError('R386_NATIVE_NO_UNMEASURED_COST')
    return {'weights': {**weights, **added}, 'profiles': profiles, 'added': added,
            'sources': sorted(sources), 'historical_source': history}


def source_digest(root):
    """Bind names AND bytes of execution, counts, costs and original evidence."""
    root = Path(root)
    load_registry(root)
    profile = timing_profile(root)
    paths = sorted([root / LEGACY, *(root / SUITES).glob('*.json'), *(root / COSTS).glob('*.json'),
                    *(root / SOURCES / (h + '.json') for h in profile['sources'])])
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        digest.update(path.read_bytes() + b'\0')
    return digest.hexdigest()


def resolved_execution(record, root):
    execution = dict(record['execution'])
    if execution['cmd'] is not None:
        execution['cmd'] = [
            sys.executable if c == '{python}' else str(Path(root).resolve()) + c[len('{root}'):] if c.startswith('{root}/') else c
            for c in execution['cmd']]
    return execution


def _legacy_export(root):
    # Load the specified base's actual registry, not a suite table frozen in
    # this migrator. Subprocess isolation also avoids reusing another checkout's
    # already-imported run_all/binaries modules.
    program = (
        "import json,sys;sys.path.insert(0,'tests');import run_all;"
        "data=run_all.load_expected();assert not data[1],data[1];"
        "print(json.dumps({'suites':[vars(s) for s in run_all.build_suites()],"
        "'expected':data[0]},ensure_ascii=False))"
    )
    result = subprocess.run([sys.executable, '-c', program], cwd=root,
                            capture_output=True, text=True, check=False, timeout=60)
    if result.returncode:
        raise ValueError('R386_NATIVE_LEGACY_EXPORT: ' + result.stderr[-2000:])
    return json.loads(result.stdout)


def migrate(root, out_root, *, base_sha=None):
    """Copy canonical fragments and byte-identical evidence; never edit root.

    Returns a sorted relative-path inventory. When already migrated, copying
    the validated sources is idempotent and never reverts to stale aggregates.
    """
    root, out_root = Path(root).resolve(), Path(out_root).resolve()
    payloads = {}
    if active(root):
        load_registry(root)
        timing_profile(root)
        for folder in (SUITES, COSTS, SOURCES):
            for path in _paths(root, folder):
                payloads[path.relative_to(root).as_posix()] = path.read_bytes()
        payloads[LEGACY.as_posix()] = (root / LEGACY).read_bytes()
    else:
        # Do not let the legacy reader silently accept duplicate JSON keys.
        _read(root / 'tests/run_all.expected.json')
        export = _legacy_export(root)
        suites = export['suites']
        expected_entries = export['expected']['suites']
        if {s['name'] for s in suites} != expected_entries.keys():
            raise ValueError('R386_NATIVE_LEGACY_EXPECTED_COVERAGE')
        if base_sha is None:
            base_sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        catalog, originals = _legacy_base_sources(root, base_sha)
        payloads[LEGACY.as_posix()] = canonical_bytes(catalog)
        cost_sources = {}
        for source in catalog['sources']:
            raw = originals[source['path']]
            if (root / source['path']).read_bytes() != raw:
                raise ValueError('R386_NATIVE_BOOTSTRAP_ORIGINAL_DIFFERS_FROM_BASE: ' + source['path'])
            cost_sources.update({name: (source['kind'], source['sha256']) for name in source['suites']})
            payloads[(SOURCES / (source['sha256'] + '.json')).as_posix()] = raw
        if cost_sources.keys() != expected_entries.keys():
            raise ValueError('R386_NATIVE_MIGRATION_REAL_COST_COVERAGE: missing=%r extra=%r' %
                (sorted(expected_entries.keys() - cost_sources.keys()), sorted(cost_sources.keys() - expected_entries.keys())))
        for index, suite in enumerate(suites):
            name = suite.pop('name')
            cmd = suite['cmd']
            files = []
            if cmd is not None:
                normalized = []
                for arg in cmd:
                    if arg == sys.executable:
                        normalized.append('{python}')
                    elif arg.startswith(str(root) + '/'):
                        normalized.append('{root}/' + Path(arg).relative_to(root).as_posix())
                    else:
                        normalized.append(arg)
                    target = Path(arg) if Path(arg).is_absolute() else root / arg
                    if (target.is_file() and target.suffix in ('.py', '.js', '.cjs', '.mjs')
                            and target.is_relative_to(root) and target.name != '_unittest_runner.py'):
                        files.append(target.relative_to(root).as_posix())
                suite['cmd'] = normalized
            if not files:
                files = [suite['label'].split()[0]]
            record = {'schema': SCHEMA, 'name': name, 'order': 'legacy/%06d' % index,
                      'execution': suite, 'files': sorted(set(files)), 'expected': expected_entries[name]}
            payloads[(SUITES / (key(name) + '.json')).as_posix()] = canonical_bytes(record)
            kind, digest = cost_sources[name]
            cost = {'schema': COST_SCHEMA, 'name': name, 'kind': kind, 'source_sha256': digest}
            payloads[(COSTS / (key(name) + '.json')).as_posix()] = canonical_bytes(cost)
    for rel, raw in sorted(payloads.items()):
        path = out_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != raw:
            raise ValueError('R386_NATIVE_MIGRATION_REFUSES_OVERWRITE: ' + rel)
        path.write_bytes(raw)
    return [{'path': rel, 'bytes': len(raw), 'sha256': _sha(raw)} for rel, raw in sorted(payloads.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--init-suite', metavar='NAME')
    action.add_argument('--import-suite', metavar='NAME')
    action.add_argument('--verify-ci', action='store_true')
    parser.add_argument('--file')
    parser.add_argument('--kind', choices=('unittest', 'node-test'))
    parser.add_argument('--needs', action='append', default=[])
    parser.add_argument('--run-id', type=int)
    parser.add_argument('--job-id', type=int)
    parser.add_argument('--artifact-id', type=int)
    parser.add_argument('--member')
    parser.add_argument('--planning-upper-ms', type=int)
    parser.add_argument('--trusted-base')
    parser.add_argument('--base-sha')
    args = parser.parse_args()
    if args.init_suite:
        if not args.file or not args.kind:
            parser.error('--init-suite requires --file and --kind')
        result = init_suite(args.root, name=args.init_suite, file=args.file, kind=args.kind, needs=args.needs)
    elif args.verify_ci:
        result = {'ci_source_verification': verify_ci_sources(args.root, trusted_ref=args.trusted_base)}
    else:
        if args.out is None:
            parser.error('migration / import requires --out')
        if args.import_suite:
            if any(value is None for value in (args.run_id, args.job_id, args.artifact_id,
                                               args.member, args.planning_upper_ms)):
                parser.error('--import-suite requires run/job/artifact IDs, member and planning upper milliseconds')
            paths = import_ci_cost(args.root, args.out, name=args.import_suite, run_id=args.run_id,
                                   job_id=args.job_id, artifact_id=args.artifact_id, member=args.member,
                                   planning_upper_ms=args.planning_upper_ms)
        else:
            paths = migrate(args.root, args.out, base_sha=args.base_sha)
        result = {'files': paths}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
