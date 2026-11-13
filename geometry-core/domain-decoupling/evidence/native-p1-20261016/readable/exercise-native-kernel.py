#!/usr/bin/env python3
"""Run the original unittest suite; retain artifacts before its atexit cleanup."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import unittest

source, out = map(Path, sys.argv[1:])
sys.path.insert(0, str(source))
module = importlib.import_module("tests.test_geo261_native_kernel")
suite = unittest.defaultTestLoader.loadTestsFromModule(module)
result = unittest.TextTestRunner(verbosity=2).run(suite)
build = module._BUILD
artifacts = {}
if build is not None:
    for path in sorted(build.work.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(build.work)
        artifacts[str(relative)] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
        # Preserve original compiler logs and the exact source/client/mutant inputs.
        if path.suffix in (".json", ".c", ".h", ".cmd"):
            target = out / "native-build-inputs" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    (out / "native-build-artifacts.json").write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
summary = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
           "skipped": result.skipped, "expected_failures": len(result.expectedFailures),
           "unexpected_successes": len(result.unexpectedSuccesses), "successful": result.wasSuccessful(),
           "compiler_commands": len(build.logs) if build is not None else 0,
           "build_artifact_count": len(artifacts)}
(out / "test-result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
sys.exit(0 if result.wasSuccessful() and result.testsRun == 13 and not result.skipped else 1)
