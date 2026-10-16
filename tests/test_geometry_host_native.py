"""Native host cache and publication checks without running a native program."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from modeling import base as base_facade
from geometry_app import model_native as native
from geometry_app import source_closure
from geometry_app.model_common import ModelError


def digest(path):
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def valid_result(command):
    snapshot = {"ok": True, "schema": "geometry-base-snapshot/1", "base_scene": "",
                "specs": [], "placements": [], "solids": [], "unplaced_timbers": [],
                "dependencies": [], "required_capabilities": []}
    return subprocess.CompletedProcess(command, 0, json.dumps(snapshot).encode(), b"")


class NativeBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="geo261-native-cache-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "adapter.c"
        self.header = self.root / "nested.h"
        self.compiler = self.root / "compiler with spaces.exe"
        self.source.write_bytes(b'#include "nested.h"\r\nint value = VALUE;\r\n')
        self.header.write_bytes(b"#define VALUE 1\r\n")
        self.compiler.write_bytes(b"compiler-v1")
        self.compiler.chmod(0o700)
        self.build_dirs = []
        self.addCleanup(lambda: [entry.cleanup() for entry in self.build_dirs])
        self.enterContext(mock.patch.object(native, "_SOURCE", self.source))
        self.enterContext(mock.patch.object(native, "_BUILD_CACHE", {}))
        self.enterContext(mock.patch.object(native, "_BUILD_DIRS", self.build_dirs))
        self.compiler_command = self.enterContext(mock.patch.object(
            native, "_compiler_command", return_value=(str(self.compiler),)))
        self.compile = self.enterContext(mock.patch.object(native.subprocess, "run", side_effect=self.fake_compile))

    def fake_compile(self, command, **options):
        target = Path(command[command.index("-o") + 1])
        target.write_bytes(b"compiled-adapter-" + str(self.compile.call_count).encode())
        return subprocess.CompletedProcess(command, 0, b"", b"")

    def assert_recompiled_after(self, change):
        first = Path(native._build_adapter())
        self.assertTrue(first.is_file())
        self.assertEqual(str(first), native._build_adapter())
        self.assertEqual(1, self.compile.call_count)
        change(first)
        second = Path(native._build_adapter())
        self.assertTrue(second.is_file())
        self.assertEqual(2, self.compile.call_count)
        self.assertEqual(str(second), native._build_adapter())
        self.assertEqual(2, self.compile.call_count)

    def test_unchanged_inputs_and_target_reuse_compilation(self):
        first = native._build_adapter()
        self.assertEqual(first, native._build_adapter())
        self.assertEqual(1, self.compile.call_count)
        self.assertEqual(str(self.compiler), self.compile.call_args.args[0][0])

    def test_source_bytes_invalidate_cache(self):
        self.assert_recompiled_after(lambda _: self.source.write_bytes(
            b'#include "nested.h"\nint other = VALUE;\n'))

    def test_recursive_include_bytes_invalidate_cache(self):
        self.assert_recompiled_after(lambda _: self.header.write_bytes(b"#define VALUE 2\n"))

    def test_compiler_bytes_invalidate_cache(self):
        self.assert_recompiled_after(lambda _: self.compiler.write_bytes(b"compiler-v2"))

    def test_compiler_arguments_invalidate_cache(self):
        def change(_):
            self.compiler_command.return_value = (str(self.compiler), "-DFIXTURE=2")
        self.assert_recompiled_after(change)

    def test_environment_change_invalidates_cache(self):
        with mock.patch.dict(os.environ, {"GEOMETRY_TEST_BUILD_ENV": "first"}):
            self.assert_recompiled_after(lambda _: os.environ.__setitem__("GEOMETRY_TEST_BUILD_ENV", "other"))

    def test_target_byte_replacement_invalidates_cache(self):
        self.assert_recompiled_after(lambda target: target.write_bytes(b"replaced-adapter"))

    def test_missing_target_invalidates_cache(self):
        self.assert_recompiled_after(lambda target: target.unlink())

    def test_include_cycle_is_finite_sorted_and_normalizes_line_endings(self):
        self.header.write_bytes(b'#include "adapter.c"\r\n#define VALUE 1\r\n')
        expected = tuple(sorted((str(path.resolve()), digest(path)) for path in (self.source, self.header)))
        self.assertEqual(expected, native._project_source_closure(self.source))
        self.header.write_bytes(self.header.read_bytes().replace(b"\r\n", b"\n"))
        self.assertEqual(expected, native._project_source_closure(self.source))

    def test_missing_quoted_include_rejects_build_before_compiling(self):
        self.header.unlink()
        with self.assertRaises(ModelError) as caught:
            native._build_adapter()
        self.assertEqual(("UNSUPPORTED", "BASE_COMPILER", "I32"),
                         (caught.exception.status, caught.exception.code, caught.exception.clause))
        self.compile.assert_not_called()

    def test_nonliteral_project_include_cannot_hide_a_cache_dependency(self):
        self.source.write_bytes(b'#define EXTRA "nested.h"\n#include EXTRA\n')
        with self.assertRaises(ModelError) as caught:
            native._build_adapter()
        self.assertEqual("BASE_COMPILER", caught.exception.code)
        self.compile.assert_not_called()

    def test_source_changed_during_compilation_is_not_cached(self):
        def changing_compile(command, **options):
            result = self.fake_compile(command, **options)
            self.header.write_bytes(b"#define VALUE 2\n")
            return result
        self.compile.side_effect = changing_compile
        with self.assertRaises(ModelError) as caught:
            native._build_adapter()
        self.assertEqual(("UNSUPPORTED", "BASE_COMPILER", "I32"),
                         (caught.exception.status, caught.exception.code, caught.exception.clause))
        self.compile.side_effect = self.fake_compile
        self.assertTrue(Path(native._build_adapter()).is_file())
        self.assertEqual(2, self.compile.call_count)
        native._BUILD_CACHE.clear()
        self.compile.side_effect = lambda command, **options: subprocess.CompletedProcess(command, 1, b"", b"fixture failure")
        with self.assertRaises(ModelError) as failed:
            native._build_adapter()
        self.assertEqual("C scene adapter compilation failed.", failed.exception.message)
        self.assertEqual({}, native._BUILD_CACHE)


class NativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="geo261-native-runtime-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.program = self.root / "literal adapter.bin"
        self.runtime_source = self.root / "provider.py"
        self.program.write_bytes(b"adapter-v1")
        self.runtime_source.write_bytes(b"value = 1\n")
        self.enterContext(mock.patch.object(source_closure, "source_inventory", side_effect=self.inventory))
        self.enterContext(mock.patch.object(source_closure, "_LOADED", self.inventory()))
        self.execute = self.enterContext(mock.patch.object(native.subprocess, "run", side_effect=
            lambda command, **options: valid_result(command)))

    def inventory(self):
        return (("provider.py", digest(self.runtime_source)),)

    def assert_runtime_changed(self):
        with self.assertRaises(ModelError) as caught:
            native.load_base("", executable=self.program)
        self.assertEqual(("UNSUPPORTED", "BASE_RUNTIME_CHANGED", "I32"),
                         (caught.exception.status, caught.exception.code, caught.exception.clause))

    def test_explicit_executable_beats_environment_and_wsl(self):
        with (mock.patch.dict(os.environ, {"GEOMETRY_MODEL_BASE": "/not/the/adapter",
                                          "GEOMETRY_MODEL_BASE_WSL_DISTRO": "FixtureDistro"}),
              mock.patch.object(native.sys, "platform", "win32")):
            self.assertEqual("geometry-base-snapshot/1", native.load_base("", executable=self.program)["schema"])
        self.assertEqual(1, self.execute.call_count)
        self.assertEqual(str(self.program), self.execute.call_args.args[0][0])

    def test_binary_change_during_execution_prevents_publication(self):
        def change(command, **options):
            self.program.write_bytes(b"adapter-v2")
            return valid_result(command)
        self.execute.side_effect = change
        self.assert_runtime_changed()
        self.assertEqual(1, self.execute.call_count)

    def test_source_change_during_execution_prevents_publication(self):
        def change(command, **options):
            self.runtime_source.write_bytes(b"value = 2\n")
            return valid_result(command)
        self.execute.side_effect = change
        self.assert_runtime_changed()
        self.assertEqual(1, self.execute.call_count)

    def test_unreadable_binary_after_execution_prevents_publication(self):
        def remove(command, **options):
            self.program.unlink()
            return valid_result(command)
        self.execute.side_effect = remove
        self.assert_runtime_changed()

    def test_stale_loaded_source_rejects_before_execution(self):
        self.runtime_source.write_bytes(b"value = 2\n")
        self.assert_runtime_changed()
        self.execute.assert_not_called()

    def test_invalid_executable_initial_read_keeps_executable_error(self):
        self.program.unlink()
        with self.assertRaises(ModelError) as caught:
            native.load_base("", executable=self.program)
        self.assertEqual(("UNSUPPORTED", "BASE_EXECUTABLE", "I32"),
                         (caught.exception.status, caught.exception.code, caught.exception.clause))
        self.execute.assert_not_called()

    def test_scene_validation_precedes_runtime_reads(self):
        with mock.patch.object(native, "_execution_identity", side_effect=AssertionError("runtime read")):
            for scene, code in ((None, "BASE_TYPE"), ("\ud800", "BASE_ENCODING"),
                                ("x" * (1024 * 1024 + 1), "BASE_CAPACITY")):
                with self.subTest(code=code):
                    with self.assertRaises(ModelError) as caught:
                        native.load_base(scene, executable=self.program)
                    self.assertEqual(code, caught.exception.code)
        self.execute.assert_not_called()

    def test_native_source_admission_comes_from_explicit_provider(self):
        class NoSourceCapabilities:
            source_capabilities = frozenset()
        with self.assertRaises(ModelError) as caught:
            native.load_base("requires parameters/1\n", executable=self.program,
                             provider=NoSourceCapabilities())
        self.assertEqual(("UNSUPPORTED", "CAPABILITY"),
                         (caught.exception.status, caught.exception.code))
        self.execute.assert_not_called()

    def test_compatibility_facade_honors_build_adapter_monkeypatch(self):
        with (mock.patch.dict(os.environ, {}, clear=True),
              mock.patch.object(base_facade, "_build_adapter", return_value=str(self.program)) as build):
            self.assertEqual("geometry-base-snapshot/1", base_facade.load_base("")["schema"])
        build.assert_called_once_with()
        self.assertEqual(str(self.program), self.execute.call_args.args[0][0])


class NativeGuardControls(unittest.TestCase):
    def test_removed_guards_are_detected_by_the_same_behavioral_oracles(self):
        with tempfile.TemporaryDirectory(prefix="geo261-native-guards-") as directory:
            copied = Path(directory)
            for package in ("geometry-core/geometry_kernel", "geometry-core/modeling",
                            "geometry-app/geometry_app",
                            "geometry-templates/woodworking/geometry_woodworking"):
                shutil.copytree(ROOT / package, copied / package,
                                ignore=shutil.ignore_patterns("__pycache__"))
            (copied / "tests").mkdir()
            (copied / "tests/__init__.py").write_text("", encoding="utf-8")
            shutil.copyfile(__file__, copied / "tests/test_geometry_host_native.py")
            source = copied / "geometry-app/geometry_app/model_native.py"
            original = source.read_text(encoding="utf-8")
            runner = ("import sys,unittest;sys.path.insert(0,sys.argv.pop(1));"
                      "unittest.main(module=None)")

            def execute(*names):
                return subprocess.run([sys.executable, "-I", "-B", "-c", runner,
                                       str(copied), *("tests.test_geometry_host_native." + name for name in names)],
                                      cwd=copied, capture_output=True, text=True, timeout=30)

            baseline = execute("NativeBuildTests", "NativeRuntimeTests")
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
            self.assertIn("Ran 21 tests", baseline.stderr)
            mutants = (
                ("if sha256(Path(target).read_bytes()).hexdigest() == binary_hash:",
                 "if True:", "NativeBuildTests.test_target_byte_replacement_invalidates_cache"),
                ("if current != identity:", "if False:",
                 "NativeRuntimeTests.test_binary_change_during_execution_prevents_publication"),
                ('if not sources["fresh"]:', "if False:",
                 "NativeRuntimeTests.test_stale_loaded_source_rejects_before_execution"),
                ("if _build_inputs(source, compiler) != inputs:",
                 "if False:", "NativeBuildTests.test_source_changed_during_compilation_is_not_cached"),
                ("_project_source_closure(source), sha256(environment).hexdigest())",
                 "(), sha256(environment).hexdigest())", "NativeBuildTests.test_recursive_include_bytes_invalidate_cache"),
            )
            for before, after, case in mutants:
                with self.subTest(case=case):
                    self.assertEqual(1, original.count(before))
                    source.write_text(original.replace(before, after), encoding="utf-8")
                    result = execute(case)
                    details = result.stdout + result.stderr
                    self.assertEqual(1, result.returncode, details)
                    self.assertIn("Ran 1 test", details)
                    self.assertIn("FAILED (failures=1)", details)
                    self.assertNotIn("ImportError", details)
                    self.assertNotIn("SyntaxError", details)
            source.write_text(original, encoding="utf-8")
            restored = execute("NativeBuildTests", "NativeRuntimeTests")
            self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)


if __name__ == "__main__":
    unittest.main()
