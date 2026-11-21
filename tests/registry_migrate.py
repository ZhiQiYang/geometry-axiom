#!/usr/bin/env python3
"""R386: reproducible migration of reviewed registries, without running browsers.

The input is the selected checkout's actual registries, not a table copied from
the implementation's original base. A plan contains LF bytes and content
identities only. Its report is an external receipt, never an append-only source
manifest. Runtime consumers assemble fragments themselves.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MARKER = 'tests/registry-layout.json'
LAYOUT = {'schema': 'geometry-test-registries/1'}
SCHEMA = 'geometry-test-registry-migration/1'
PENDING = 'tests/.registry-migration-pending'
ARCHITECTURE = 'geometry-core/domain-decoupling/product-architecture.json'
NATIVE_CATALOG = 'tests/registry-evidence/native-legacy.json'
FRAGMENT_ROOTS = (
    'tests/suites.d', 'tests/native-costs.d', 'tests/registry-evidence/native',
    'geometry-web/cdp_sections.d', 'geometry-web/canvas-registry',
    'geometry-core/domain-decoupling/product-architecture.d',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def digest(raw):
    return {
        'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'blob': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
    }


def pairs(rows):
    result = {}
    for name, value in rows:
        require(name not in result, 'R386_DUPLICATE_JSON_KEY: ' + name)
        result[name] = value
    return result


def read_json(path):
    raw = Path(path).read_bytes()
    require(b'\r' not in raw and raw.endswith(b'\n'), 'R386_SOURCE_MUST_BE_LF: ' + str(path))
    return json.loads(raw, object_pairs_hook=pairs)


def safe_path(root, relative):
    require(isinstance(relative, str) and relative and '\\' not in relative,
            'R386_UNSAFE_PATH: ' + repr(relative))
    path = PurePosixPath(relative)
    require(not path.is_absolute() and all(p not in ('', '.', '..') for p in relative.split('/')),
            'R386_UNSAFE_PATH: ' + relative)
    target = Path(root)
    for part in path.parts:
        target /= part
        require(not target.is_symlink(), 'R386_SYMLINK_NOT_ALLOWED: ' + relative)
    require(not target.exists() or target.is_file(), 'R386_ORDINARY_FILE_REQUIRED: ' + relative)
    return target


def run(argv, *, cwd, timeout=60):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=False)
    require(result.returncode == 0,
            'R386_CHILD_FAILED: ' + ' '.join(map(str, argv)) + '\n' +
            result.stdout[-12000:] + result.stderr[-12000:])
    return result.stdout


def git_head(root):
    value = run(['git', 'rev-parse', 'HEAD'], cwd=root).strip()
    require(re.fullmatch('[0-9a-f]{40}', value), 'R386_COMPLETE_BASE_SHA_REQUIRED')
    return value


def trusted_base(root, explicit=None):
    """Only an independently designated base can authenticate retained receipts.

    In Actions the relationship is checked against the actual test-merge
    parents, never a value inside a submitted cost receipt. Local explicit
    trust is recorded as such; it is not a claim of Actions authentication.
    """
    if explicit:
        require(re.fullmatch('[0-9a-f]{40}', explicit), 'R386_TRUSTED_BASE_FULL_SHA_REQUIRED')
        require(run(['git', 'rev-parse', '--verify', explicit + '^{commit}'], cwd=root).strip() == explicit,
                'R386_TRUSTED_BASE_COMMIT_REQUIRED')
        return {'sha': explicit, 'source': 'explicit-local-trust'}
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return {'sha': None, 'source': 'none; new receipts require online verification'}
    event = os.environ.get('EVENT_NAME') or os.environ.get('GITHUB_EVENT_NAME')
    actual = git_head(root)
    require(actual == os.environ.get('GITHUB_SHA'), 'R386_CI_CHECKOUT_DIFFERS_FROM_EVENT')
    if event == 'pull_request':
        head = os.environ.get('PR_HEAD', '')
        require(re.fullmatch('[0-9a-f]{40}', head), 'R386_CI_PR_HEAD_REQUIRED')
        second = run(['git', 'rev-parse', '--verify', 'HEAD^2'], cwd=root).strip()
        require(second == head, 'R386_CI_TEST_MERGE_SECOND_PARENT')
        parent = run(['git', 'rev-parse', '--verify', 'HEAD^1'], cwd=root).strip()
        return {'sha': parent, 'source': 'verified-test-merge-first-parent'}
    if event == 'push' and os.environ.get('GITHUB_REF') == 'refs/heads/main':
        parent = run(['git', 'rev-parse', '--verify', 'HEAD^1'], cwd=root).strip()
        return {'sha': parent, 'source': 'main-push-first-parent'}
    return {'sha': None, 'source': 'no trusted CI base; new receipts require online verification'}


def module(name):
    path = HERE / (name + '.py')
    spec = importlib.util.spec_from_file_location('r386_' + name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def component_command(root, *args):
    return ['node', str(ROOT / 'geometry-web/canvas_registry.js'), *args, '--root', str(root)]


def source_paths(root):
    """Files interpreted by migration; product sources are independently scanned.

    The base commit is also recorded. Additions never update a global inventory:
    this list is recomputed for each external migration receipt.
    """
    names = {
        'tests/run_all.py', 'tests/run_all.expected.json', 'tests/native_shards.py',
        'tests/native_shard_timings.json', ARCHITECTURE,
        'geometry-web/canvas_shards.json', 'geometry-web/cdp_sections.golden.json',
        'geometry-web/canvas_shards.js', 'geometry-web/cdp_test.js',
        'geometry-core/card-reference/run_mutations.py', MARKER, NATIVE_CATALOG,
    }
    names.update(p.relative_to(root).as_posix()
                 for pattern in ('native_shard_added_evidence*.json', 'native_shard_added_receipts*.json')
                 for p in (root / 'tests').glob(pattern))
    for directory in (*FRAGMENT_ROOTS, 'tests/registry-source-reviews'):
        folder = root / directory
        require(not folder.is_symlink(), 'R386_SYMLINK_NOT_ALLOWED: ' + directory)
        if folder.exists():
            for path in sorted(folder.rglob('*')):
                require(not path.is_symlink(), 'R386_SYMLINK_NOT_ALLOWED: ' + str(path))
                if path.is_file():
                    names.add(path.relative_to(root).as_posix())
    return {name: digest(safe_path(root, name).read_bytes()) for name in sorted(names)
            if (root / name).exists()}


def tool_identity():
    names = (
        'tests/registry_migrate.py', 'tests/native_registry.py',
        'tests/architecture_contract.py', 'geometry-web/canvas_registry.js',
    )
    return {name: digest((ROOT / name).read_bytes()) for name in names}


def immutable_architecture_boundary(root):
    """Never silently replace #418's deliberately frozen generator contract.

    A receipt-format adapter must be reviewed in the immutable-evidence owner.
    The old reader only hashes the root JSON and cannot certify fragments. A
    later supported reader exposes a storage protocol explicitly and still
    validates its own generator version and fresh original receipts.
    """
    helper = root / '.github/scripts/evidence_architecture.py'
    if not helper.exists():
        return {'present': False}
    declarations = {}
    for node in ast.parse(helper.read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                declarations[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    require(declarations.get('MANIFEST_STORAGE_PROTOCOL') == 'geometry-architecture-manifest-closure/1',
            'R386_IMMUTABLE_ARCHITECTURE_ADAPTER_REQUIRED: #418 must bind every fragment, '
            'version its generator, and require fresh originals; this migration does not rewrite its frozen pins')
    return {'present': True, 'storage_protocol': declarations['MANIFEST_STORAGE_PROTOCOL'],
            'reader_sha256': digest(helper.read_bytes())['sha256']}


def make_plan(root, base_sha):
    root = Path(root).resolve()
    require(re.fullmatch('[0-9a-f]{40}', base_sha or ''), 'R386_COMPLETE_BASE_SHA_REQUIRED')
    require(git_head(root) == base_sha, 'R386_BASE_DIFFERS_FROM_CHECKOUT')
    require(not (root / PENDING).exists(), 'R386_INTERRUPTED_MIGRATION: use recover first')
    immutable_boundary = immutable_architecture_boundary(root)
    # Migration is not a way to reconstruct a missing immutable archive from
    # reintroduced aggregate tables. Once any new-layout evidence exists, the
    # actual new canvas contract must pass before components may emit output.
    if any((root / relative).exists() for relative in (
            MARKER, 'geometry-web/canvas-registry', 'geometry-web/cdp_sections.d',
            'geometry-web/canvas_sections')):
        run(component_command(root, 'check'), cwd=root)
    inputs = source_paths(root)
    tool_inputs = tool_identity()
    native = module('native_registry')
    architecture = module('architecture_contract')
    payloads = {}
    with tempfile.TemporaryDirectory(prefix='geometry-registry-plan-') as temporary:
        stage = Path(temporary)
        native.migrate(root, stage, base_sha=base_sha)
        run(component_command(root, 'migrate', '--base-sha', base_sha,
                              '--outdir', str(stage)), cwd=root)
        logical = architecture.load_manifest(root / ARCHITECTURE)
        logical, source_reviews = architecture.apply_reviewed_source_updates(logical, root)
        files = architecture.fragment_manifest_files(logical)
        prefix = PurePosixPath(ARCHITECTURE).parent
        for relative, raw in files.items():
            target = safe_path(stage, (prefix / relative).as_posix())
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.exists(), 'R386_COMPONENT_PATH_COLLISION: ' + relative)
            target.write_bytes(raw)
        for path in sorted(stage.rglob('*')):
            require(not path.is_symlink(), 'R386_COMPONENT_SYMLINK')
            if not path.is_file():
                continue
            rel = path.relative_to(stage).as_posix()
            require(any(rel.startswith(directory + '/') for directory in FRAGMENT_ROOTS)
                    or rel in (ARCHITECTURE, NATIVE_CATALOG),
                    'R386_COMPONENT_OUTPUT_OUTSIDE_REGISTRY: ' + rel)
            raw = path.read_bytes()
            if path.suffix == '.json':
                require(b'\r' not in raw and raw.endswith(b'\n'), 'R386_OUTPUT_MUST_BE_LF: ' + rel)
            payloads[rel] = raw
    payloads[MARKER] = canonical(LAYOUT)
    # These are materialized views after migration. The original canvas bytes
    # are sealed in canvas-registry and are still used by historical guards.
    retired = ['tests/run_all.expected.json', 'geometry-web/canvas_shards.json',
               'geometry-web/cdp_sections.golden.json']
    retired = sorted(path for path in retired if (root / path).is_file())
    require(source_paths(root) == inputs, 'R386_SOURCE_CHANGED_DURING_PLAN')
    require(tool_identity() == tool_inputs, 'R386_TOOL_CHANGED_DURING_PLAN')
    rows = []
    for rel, raw in sorted(payloads.items()):
        path = safe_path(root, rel)
        before = digest(path.read_bytes()) if path.exists() else None
        rows.append({'path': rel, 'before': before, 'after': digest(raw)})
    for rel in retired:
        rows.append({'path': rel, 'before': digest(safe_path(root, rel).read_bytes()), 'after': None})
    report = {
        'schema': SCHEMA, 'base_sha': base_sha, 'tools': tool_inputs, 'acceptance': False,
        'inputs': inputs, 'files': sorted(rows, key=lambda row: row['path']),
        'reviewed_source_updates': source_reviews,
        'immutable_architecture_boundary': immutable_boundary,
    }
    report['payload_sha256'] = hashlib.sha256(canonical({
        rel: digest(raw) for rel, raw in sorted(payloads.items())})).hexdigest()
    return payloads, retired, report


def export_plan(payloads, report, out):
    out = Path(out).resolve()
    require(not out.exists() or not any(out.iterdir()), 'R386_OUTPUT_DIRECTORY_MUST_BE_EMPTY')
    out.mkdir(parents=True, exist_ok=True)
    for rel, raw in sorted(payloads.items()):
        path = safe_path(out / 'files', rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (out / 'manifest.json').write_bytes(canonical(report))


def _replace(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.registry-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def recover(root):
    """Restore a failed/interrupted apply; never overwrite subsequent edits."""
    root = Path(root).resolve()
    journal = root / PENDING
    require(journal.is_dir() and not journal.is_symlink(), 'R386_NO_RECOVERABLE_JOURNAL')
    if not (journal / 'journal.json').exists():
        # No source write is allowed before the final journal is installed.
        # A killed preparation therefore only leaves disposable backups.
        require(all(p.name in {'prepare.json', 'before'} or p.name.startswith('.registry-write-')
                    for p in journal.iterdir()),
                'R386_UNKNOWN_PREPARATION_CONTENT')
        for path in journal.rglob('*'):
            require(not path.is_symlink(), 'R386_RECOVERY_BACKUP_SYMLINK')
        if (journal / 'prepare.json').exists():
            preparation = read_json(journal / 'prepare.json')
            require(preparation.get('schema') == SCHEMA and preparation.get('state') == 'preparing',
                    'R386_INVALID_PREPARATION')
        shutil.rmtree(journal)
        return
    metadata = read_json(journal / 'journal.json')
    require(metadata.get('schema') == SCHEMA, 'R386_INVALID_JOURNAL')
    for row in metadata['files']:
        path = safe_path(root, row['path'])
        actual = digest(path.read_bytes()) if path.exists() else None
        require(actual in (row['before'], row['after']),
                'R386_RECOVERY_REFUSES_LATER_EDIT: ' + row['path'])
        if row['before'] is not None:
            backup = safe_path(journal / 'before', row['path'])
            require(digest(backup.read_bytes()) == row['before'], 'R386_RECOVERY_BACKUP_CHANGED')
    for row in reversed(metadata['files']):
        path = safe_path(root, row['path'])
        if row['before'] is None:
            path.unlink(missing_ok=True)
        else:
            _replace(path, (journal / 'before' / row['path']).read_bytes())
        for temporary in path.parent.glob('.registry-write-*'):
            require(temporary.is_file() and not temporary.is_symlink(), 'R386_RECOVERY_TEMP_NOT_REGULAR')
            temporary.unlink()
    shutil.rmtree(journal)
    for rel in FRAGMENT_ROOTS:
        folder = root / rel
        if folder.is_dir():
            for child in sorted(folder.rglob('*'), reverse=True):
                if child.is_dir() and not any(child.iterdir()):
                    child.rmdir()
            if not any(folder.iterdir()):
                folder.rmdir()


def apply_plan(root, payloads, retired, report, validate=True, trusted=None):
    """Validate an overlay before writing; retain a recoverable write-ahead log.

    Filesystem-wide atomicity is not claimed. Readers reject an unfinished
    journal. A normal exception rolls back; after process termination, recover
    performs the same rollback and refuses to destroy later user edits.
    """
    root = Path(root).resolve()
    changes = [row for row in report['files'] if row['before'] != row['after']]

    def destination_unchanged(row):
        path = safe_path(root, row['path'])
        actual = digest(path.read_bytes()) if path.exists() else None
        require(actual == row['before'], 'R386_DESTINATION_CHANGED: ' + row['path'])

    def inputs_unchanged():
        require(source_paths(root) == report['inputs'], 'R386_SOURCE_CHANGED_BEFORE_APPLY')
        require(git_head(root) == report['base_sha'], 'R386_BASE_CHANGED_BEFORE_APPLY')
        if 'tools' in report:
            require(tool_identity() == report['tools'], 'R386_TOOL_CHANGED_BEFORE_APPLY')
        for row in changes:
            destination_unchanged(row)

    inputs_unchanged()
    if validate:
        validate_overlay(root, payloads, retired, trusted=trusted)
    inputs_unchanged()
    if not changes:
        return
    journal = root / PENDING
    require(not journal.exists(), 'R386_MIGRATION_ALREADY_IN_PROGRESS')
    journal.mkdir(parents=True)
    # Backups are complete before the first source write; the journal itself is
    # installed last. A preparation failure therefore leaves sources untouched.
    try:
        _replace(journal / 'prepare.json', canonical({'schema': SCHEMA, 'state': 'preparing'}))
        for row in changes:
            if row['before'] is not None:
                backup = safe_path(journal / 'before', row['path'])
                backup.parent.mkdir(parents=True, exist_ok=True)
                raw = (root / row['path']).read_bytes()
                require(digest(raw) == row['before'], 'R386_SOURCE_CHANGED_DURING_BACKUP: ' + row['path'])
                backup.write_bytes(raw)
        inputs_unchanged()
        _replace(journal / 'journal.json', canonical({'schema': SCHEMA, 'files': changes}))
    except BaseException:
        shutil.rmtree(journal)
        raise
    try:
        for row in changes:
            rel = row['path']
            if rel == MARKER:
                continue
            destination_unchanged(row)
            path = safe_path(root, rel)
            if row['after'] is None:
                path.unlink()
            else:
                _replace(path, payloads[rel])
        marker_changes = [row for row in changes if row['path'] == MARKER]
        if marker_changes:
            destination_unchanged(marker_changes[0])
            _replace(root / MARKER, payloads[MARKER])
    except BaseException:
        recover(root)
        raise
    shutil.rmtree(journal)


def validate_overlay(root, payloads, retired, trusted=None):
    with tempfile.TemporaryDirectory(prefix='geometry-registry-validate-') as temporary:
        checkout = Path(temporary) / 'checkout'
        def ignore(directory, names):
            omitted = {name for name in names if name in
                       {'.git', 'node_modules', '__pycache__', '.registry-migration-pending'}}
            relative = Path(directory).relative_to(root).as_posix()
            if relative == '.':
                omitted.update({'evidence'} & set(names))
            elif relative == 'tests':
                omitted.update({'evidence', 'release-evidence'} & set(names))
            return omitted
        shutil.copytree(root, checkout, ignore=ignore)
        # Read-only access to the selected base's Git objects lets the guard
        # authenticate retained immutable receipts even after Actions expiry.
        gitdir = run(['git', 'rev-parse', '--absolute-git-dir'], cwd=root).strip()
        (checkout / '.git').write_text('gitdir: ' + gitdir + '\n', encoding='utf-8')
        for rel in retired:
            (checkout / rel).unlink(missing_ok=True)
        for rel, raw in payloads.items():
            path = safe_path(checkout, rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        command = [sys.executable, '-B', str(checkout / 'tests/registry_migrate.py'),
                   'check', '--root', str(checkout)]
        if trusted and trusted['sha'] and os.environ.get('GITHUB_ACTIONS') != 'true':
            command.extend(['--trusted-base', trusted['sha']])
        run(command, cwd=checkout, timeout=60)


def check(root, trusted=None):
    root = Path(root).resolve()
    require(not (root / PENDING).exists(), 'R386_INTERRUPTED_MIGRATION: use recover first')
    require(read_json(safe_path(root, MARKER)) == LAYOUT, 'R386_LAYOUT_REQUIRED')
    immutable_boundary = immutable_architecture_boundary(root)
    native = module('native_registry')
    rows = native.load_registry(root)
    costs = native.timing_profile(root)
    trust = trusted or trusted_base(root)
    verified_costs = native.verify_ci_sources(root, trusted_ref=trust['sha'])
    require(len(costs['profiles']) >= 2, 'R386_NATIVE_REAL_PROFILES_REQUIRED')
    program = (
        "import json,sys;sys.path.insert(0,'tests');import run_all;"
        "problems=run_all.check_registry();assert not problems,problems;"
        "data,errors=run_all.load_expected();assert not errors,errors;"
        "assert set(data['suites'])=={s.name for s in run_all.build_suites()};"
        "print(json.dumps({'suites':len(data['suites'])}))")
    census = json.loads(run([sys.executable, '-B', '-c', program], cwd=root))
    canvas_args = ['check', '--verify-ci', 'true']
    if trust['sha']:
        canvas_args += ['--trusted-ref', trust['sha']]
    canvas = json.loads(run(component_command(root, *canvas_args), cwd=root))
    architecture = module('architecture_contract')
    logical = architecture.load_manifest(root / ARCHITECTURE)
    # The existing scanner, not the migration code, remains the authority for
    # complete/exclusive product inventory, exclusion bytes, routes and layers.
    scan = architecture.scan(root, logical)
    require(not scan.diagnostics, 'R386_ARCHITECTURE_GATE: ' +
            '; '.join(str(d) for d in scan.diagnostics[:20]))
    require(census['suites'] == len(rows), 'R386_NATIVE_REGISTRY_CENSUS')
    return {
        'schema': 'geometry-test-registry-check/1', 'native_suites': len(rows),
        'native_profiles': len(costs['profiles']), 'native_cost_source_verification': verified_costs,
        'trusted_base': trust,
        'immutable_architecture_boundary': immutable_boundary,
        'native_expected_sha256': native.expected_digest(root),
        'native_sources_sha256': native.source_digest(root), 'canvas': canvas,
        'architecture_sources': len(logical['sources']),
        'architecture_exclusions': len(logical['exclusions']),
        'architecture_inputs_sha256': hashlib.sha256(architecture.manifest_input_bytes(root / ARCHITECTURE)).hexdigest(),
    }


def self_test(root):
    commands = (
        ([sys.executable, '-B', 'tests/diagnostics/native_registry_contract_check.py'], 18),
        (['node', '--test', '--test-reporter=tap', 'tests/diagnostics/canvas_registry_contract_check.cjs'], 1),
        ([sys.executable, '-B', 'tests/diagnostics/architecture_registry_contract_check.py'], 35),
        ([sys.executable, '-B', 'tests/diagnostics/registry_migration_contract_check.py'], 19),
        ([sys.executable, '-B', '.github/scripts/test_canvas_slot_proof.py'], 21),
    )
    receipts = []
    for command, expected in commands:
        child = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60, check=False)
        output = child.stdout + child.stderr
        require(child.returncode == 0, 'R386_SELFTEST_FAILED: ' + ' '.join(command) + '\n' + output[-16000:])
        if command[0] == 'node':
            match = re.search(r'^# tests ([0-9]+)$', output, re.M)
            require(all(re.search(r'^# ' + label + r' 0$', output, re.M)
                        for label in ('fail', 'cancelled', 'skipped', 'todo')),
                    'R386_SELFTEST_NO_FAILURE_OR_SKIP: ' + ' '.join(command))
            require(re.search(r'^# pass ' + str(expected) + r'$', output, re.M), 'R386_SELFTEST_EXACT_PASSES')
        else:
            match = re.search(r'Ran ([0-9]+) tests? in ', output)
            require(re.search(r'^OK\s*$', output, re.M) and not re.search(r'skipped=[1-9]', output),
                    'R386_SELFTEST_NO_FAILURE_OR_SKIP: ' + ' '.join(command))
        require(match and int(match[1]) == expected, 'R386_SELFTEST_EXACT_COUNT: ' + ' '.join(command))
        receipts.append({'command': command, 'tests': expected, 'exit_code': child.returncode,
                         'stdout': child.stdout, 'stderr': child.stderr})
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'apply', 'check', 'recover', 'self-test'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--base-sha')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--trusted-base', help='Explicit local trust anchor; CI derives its own parent')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        require(not (os.environ.get('GITHUB_ACTIONS') == 'true' and args.trusted_base),
                'R386_CI_TRUST_MUST_COME_FROM_EVENT')
        if args.command in ('plan', 'apply'):
            base = args.base_sha or git_head(args.root)
            payloads, retired, result = make_plan(args.root, base)
            if args.out:
                require(not args.out.resolve().is_relative_to(args.root.resolve()),
                        'R386_EXPORT_OUTSIDE_CHECKOUT_REQUIRED')
                export_plan(payloads, result, args.out)
            if args.command == 'apply':
                trust = trusted_base(args.root, args.trusted_base)
                if not trust['sha'] and os.environ.get('GITHUB_ACTIONS') != 'true':
                    trust = {'sha': base, 'source': 'explicit-migration-input-base'}
                apply_plan(args.root, payloads, retired, result, trusted=trust)
                result['validation'] = check(args.root, trust)
        elif args.command == 'check':
            result = check(args.root, trusted_base(args.root, args.trusted_base))
        elif args.command == 'recover':
            recover(args.root)
            result = {'recovered': True}
        else:
            result = {'self_test': self_test(args.root)}
        if args.self_test and args.command != 'self-test':
            result['self_test'] = self_test(args.root)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_bytes(canonical(result))
        # Full per-file bytes/blob/source inventory belongs in the report.
        summary = {k: v for k, v in result.items() if k not in ('inputs', 'tools', 'files', 'self_test')}
        if 'files' in result:
            summary['files'] = len(result['files'])
        if 'self_test' in result:
            summary['self_test_commands'] = len(result['self_test'])
        print(canonical(summary).decode(), end='')
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print('registry migration rejected: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
