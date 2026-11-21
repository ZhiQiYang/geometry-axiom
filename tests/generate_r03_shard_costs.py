#!/usr/bin/env python3
"""Measure the registered R03 children and retain honest workspace cost evidence.

Run after product sources and the registered tests are stable.  Builds use the
unchanged binaries.py registry; only these new suites run.  A source change,
skip, failed test, incomplete count, or stale binary refuses publication.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

import binaries
import native_shard_workspace as W
import run_all

ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    'py:test_framing_template': 'tests/test_framing_template.py',
    'node:framing_recipe_project_store': 'tests/test_framing_recipe_project_store.js',
    'node:framing_template_session': 'tests/test_framing_template_session.js',
    'node:framing_template_browser_scope': 'tests/test_framing_template_browser_scope.js',
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def descriptor(path, parent):
    data = path.read_bytes()
    return {'path': path.relative_to(parent).as_posix(), 'bytes': len(data), 'sha256': W.digest(data)}


def source_manifest(base):
    binary = binaries.BY_NAME['bridge']
    info = binaries.inspect_one(binary)
    if info.state != 'fresh':
        raise RuntimeError('R03 measurement requires the current source-bound bridge: ' + info.reason)
    fingerprint, native, command = binaries.compute_fingerprint(binary)
    paths = {ROOT / name for name in native}
    # The HTTP child starts a real server. Its runtime identity also reads the
    # SSOT, app/template modules and the explicit public static catalog. Use
    # the production enumerator so those original bytes cannot drift unseen.
    spec = importlib.util.spec_from_file_location('r03_cost_runtime', ROOT / 'geometry-web/runtime_version.py')
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    paths.update(runtime.source_files(ROOT))
    # Include the whole JS owner surface, not just directly imported modules:
    # the ZIP/VM fixture reads production scripts dynamically.  No node_modules.
    for top in ('geometry-web',):
        for extension in ('*.js', '*.cjs', '*.mjs', '*.json', '*.py', '*.html', '*.css'):
            paths.update(p for p in (ROOT / top).rglob(extension)
                         if not {'node_modules', '.git'} & set(p.parts))
    paths.update(ROOT / path for path in SUITES.values())
    paths.update(ROOT / path for path in (
        'tests/run_all.py', 'tests/run_all.expected.json', 'tests/_unittest_runner.py', 'tests/binaries.py',
        'tests/native_shards.py', 'tests/native_shard_workspace.py',
        'tests/generate_r03_shard_costs.py', 'tests/test_timber_edit.py',
        'tests/fixtures/reference_workspace_vm.cjs',
        'tests/diagnostics/r03_framing_canvas_extension.cjs',
        'geometry-core/framing-template/oracle/framing_oracle.py',
        'geometry-core/framing-template/oracle/rooms.json',
        'geometry-core/framing-template/oracle/oracle-golden.json'))
    files = []
    for path in sorted(paths):
        data = path.read_bytes()
        files.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data),
                      'sha256': W.digest(data), 'lf_sha256': W.digest(data.replace(b'\r\n', b'\n'))})
    raw = info.path.read_bytes()
    return {'schema': 'native-shard-workspace-source/1', 'base_sha': base, 'files': files,
            'binary': {'name': 'bridge', 'bytes': len(raw), 'sha256': W.digest(raw),
                       'fingerprint': fingerprint, 'command': command, 'source_sha256': native}}


def runner_identity():
    cpu = 'unavailable'
    cpuinfo = Path('/proc/cpuinfo')
    if cpuinfo.is_file():
        cpu = next((line.split(':', 1)[1].strip() for line in cpuinfo.read_text().splitlines()
                    if line.startswith('model name') and ':' in line), cpu)
    nproc = (int(subprocess.check_output(['nproc'], text=True).strip()) if shutil.which('nproc')
             else os.cpu_count() or 1)
    cgroup = Path('/sys/fs/cgroup/cpu.max')
    return {'cpu_model': cpu, 'nproc': nproc,
            'cgroup_cpu_max': cgroup.read_text().strip() if cgroup.is_file() else 'unavailable',
            'platform': platform.platform(), 'python': sys.version,
            'node': subprocess.check_output([run_all.node_exe(), '--version'], text=True).strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'tests/native_shard_added_evidence_r03.json')
    parser.add_argument('--artifacts', type=Path, default=ROOT / 'tests/native_shard_evidence/r03')
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    if not W.is_hash(args.base, 40):
        parser.error('--base must be the complete commit SHA')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != args.base:
        raise RuntimeError('workspace HEAD differs from --base; do not mislabel the measurement')
    output, artifacts = args.output.resolve(), args.artifacts.resolve()
    if not artifacts.is_relative_to(output.parent):
        parser.error('--artifacts must be inside the output parent')
    if args.build:
        result = subprocess.run([sys.executable, str(ROOT / 'tests/binaries.py'), 'build', 'bridge'])
        if result.returncode:
            raise SystemExit(result.returncode)
    before = source_manifest(args.base)
    suites = [s for s in run_all.build_suites() if s.name in SUITES]
    if {s.name for s in suites} != set(SUITES):
        raise RuntimeError('R03 suite registry is incomplete')
    infos = binaries.inspect_all(['bridge'])
    env = run_all.child_env(infos, [])
    observations = []
    expected, expected_error = run_all.load_expected()
    if expected_error:
        raise RuntimeError(expected_error)
    with tempfile.TemporaryDirectory(prefix='r03-cost-originals-') as directory:
        temporary = Path(directory)
        run_all.LOG_DIR = temporary
        for suite in suites:
            actual = run_all.run_suite(suite, env, infos)
            problems = run_all.compare_expected([actual], [suite], expected, '', False)
            if problems:
                raise RuntimeError('R03 measurement count differs from the exact registry: ' + repr(problems))
            row = run_all.report_row(actual)
            upper = max(60000 if suite.needs else 5000, math.ceil(row['seconds'] * 3) * 1000 + 1000)
            W.validate_row(row, upper)
            command = (["{python}", 'tests/_unittest_runner.py', SUITES[suite.name]]
                       if suite.kind == 'unittest'
                       else ["{node}", '--test', '--test-reporter=spec', SUITES[suite.name]])
            observations.append({'row': row, 'test_file': SUITES[suite.name], 'command': command,
                                 'timeout_seconds': suite.timeout, 'planning_upper_ms': upper})
            print(json.dumps({'name': suite.name, 'row': row, 'planning_upper_ms': upper}, ensure_ascii=False))
        after = source_manifest(args.base)
        if after != before:
            raise RuntimeError('sources or binary changed during the measurement; no evidence published')
        # Preserve originals only after every selected child really passed.
        artifacts.mkdir(parents=True, exist_ok=True)
        manifest_path = artifacts / 'source-manifest.json'
        manifest_path.write_bytes(encoded(before))
        manifest_ref = descriptor(manifest_path, output.parent)
        for entry in observations:
            stem = entry['row']['name'].replace(':', '_')
            stdout = artifacts / (stem + '.log')
            stdout.write_bytes((temporary / (stem + '.log')).read_bytes())
            entry['stdout'] = descriptor(stdout, output.parent)
            for key, original_suffix, suffix in (
                    ('child_report', '.json', '.child.json'), ('child_log', '.unittest.log', '.unittest.log')):
                entry[key] = None
                if entry['test_file'].endswith('.py'):
                    target = artifacts / (stem + suffix)
                    target.write_bytes((temporary / (stem + original_suffix)).read_bytes())
                    entry[key] = descriptor(target, output.parent)
            receipt = {'schema': 'native-shard-workspace-row/2',
                       'source_manifest_sha256': manifest_ref['sha256'], 'source_base_sha': args.base,
                       'row': entry['row'], 'command': entry['command'],
                       'timeout_seconds': entry['timeout_seconds'], 'stdout_sha256': entry['stdout']['sha256'],
                       'child_report_sha256': entry['child_report']['sha256'] if entry['child_report'] else None,
                       'child_log_sha256': entry['child_log']['sha256'] if entry['child_log'] else None}
            receipt_path = artifacts / (stem + '.json')
            receipt_path.write_bytes(encoded(receipt))
            entry['receipt'] = descriptor(receipt_path, output.parent)
        data = {'schema': 'native-shard-workspace-suite-evidence/2',
                'source': {'kind': 'workspace', 'base_sha': args.base,
                           'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           'note': 'Local exact-workspace passing children; not GitHub CI. Bounds use at least 3x observed seconds plus 1s, floor 60s for native and 5s for Node. Historical CI receipts are unchanged; formal six-shard wall-clock acceptance remains required.',
                           'runner': runner_identity(), 'manifest': manifest_ref},
                'observations': observations}
        staging = output.with_suffix('.new.json')
        staging.write_bytes(encoded(data))
        W.load(staging)
        staging.replace(output)
    print(json.dumps({'evidence': str(output), 'bytes': output.stat().st_size,
                      'sha256': W.digest(output.read_bytes())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
