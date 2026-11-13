#!/usr/bin/env python3
"""Run unchanged edge assertions and capture actual, non-inverted outcomes."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import unittest

source, out = map(Path, sys.argv[1:3])
mode = sys.argv[3]
sys.path.insert(0, str(source))
module = importlib.import_module('tests.test_geo261_region_edges')
names = unittest.defaultTestLoader.getTestCaseNames(module.RegionEdges)
if mode == 'old':
    names = [name for name in names if not name.startswith('test_removing_')]
suite = unittest.TestSuite(module.RegionEdges(name) for name in names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
build = importlib.import_module('tests.test_geo261_native_kernel')._BUILD
artifacts = {}
if build is not None:
    for path in sorted(build.work.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(build.work)
        artifacts[str(relative)] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
        if path.suffix in ('.json', '.c', '.h', '.cmd', '.scene'):
            target = out / 'native-build-inputs' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
(out / 'native-build-artifacts.json').write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
summary = {'selected_tests': names, 'tests_run': result.testsRun, 'failures': len(result.failures),
           'failed_tests': [test.id() for test, _ in result.failures], 'errors': len(result.errors),
           'errored_tests': [test.id() for test, _ in result.errors], 'skipped': result.skipped,
           'expected_failures': len(result.expectedFailures), 'unexpected_successes': len(result.unexpectedSuccesses),
           'successful': result.wasSuccessful(), 'compiler_commands': len(build.logs) if build is not None else 0,
           'build_artifact_count': len(artifacts)}
(out / 'test-result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
