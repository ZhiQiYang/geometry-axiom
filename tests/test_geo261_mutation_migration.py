"""Pure-Python checks for migrated mutation anchors and recursive injection.

No compiler, executable, scene oracle or mutation runner is launched here.
The fake compiler used for cache checks only writes inert fixture bytes.
"""
import inspect
import pathlib
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import mutate


class RecursiveMutationInjection(unittest.TestCase):
    MAIN = ('/* main-before */\n'
            ' #include "layer/unity.inc"\n'
            '#include "unrelated.c" // untouched\n'
            'int guard = 1;\n'
            'int main_guard = 1;\n'
            '/* main-after */\n')
    UNITY = ('#ifndef EXTERNAL\n/* unity-before */\n'
             '#include "target/guard.c" /* target suffix */\n'
             ' # include "../sibling.c" /* sibling suffix */\n#endif\n')
    TARGET = ('/* target-before */\n'
              ' # include "helper.h" /* helper suffix */\n'
              '#include <stddef.h>\nint guard = 1;\n/* target-after */')
    EXPECTED = ('/* main-before */\n#ifndef EXTERNAL\n/* unity-before */\n'
                '/* target-before */\n'
                ' # include "layer/target/helper.h" /* helper suffix */\n'
                '#include <stddef.h>\nint guard = 2;\n/* target-after */\n'
                ' /* target suffix */\n'
                ' # include "sibling.c" /* sibling suffix */\n#endif\n\n'
                '#include "unrelated.c" // untouched\n'
                'int guard = 1;\nint main_guard = 1;\n/* main-after */\n')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="geo261-mutation-injection-")
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name) / "repo"
        self.root.mkdir()
        self.write(mutate.MAIN_REL, self.MAIN)
        self.write("layer/unity.inc", self.UNITY)
        self.write("layer/target/guard.c", self.TARGET)
        self.write("layer/target/helper.h", "int helper_must_remain_in_header;\n")
        self.write("sibling.c", "int sibling_must_remain_in_include;\n")
        self.write("unrelated.c", "int guard = 1;\nint unrelated_must_remain_in_include;\n")
        self.m = dict(id="MF", desc="fixture", file="layer/target/guard.c",
                      old="int guard = 1;", new="int guard = 2;")
        no_command = mock.patch.object(mutate, "run_cmd", side_effect=AssertionError("native commands forbidden"))
        no_command.start()
        self.addCleanup(no_command.stop)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    def assert_nested_result(self, result):
        self.assertEqual(self.EXPECTED, result)
        self.assertEqual(1, result.count("int guard = 2;"))
        self.assertEqual(1, result.count("int guard = 1;"))  # same anchor in main is untouched
        for marker in ("helper_must_remain", "sibling_must_remain", "unrelated_must_remain"):
            self.assertNotIn(marker, result)

    def test_nested_target_exact_output_and_original_bytes_unchanged(self):
        src = mutate.Sources(self.root)
        disk = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        snapshot = (dict(src.texts), dict(src.hashes), src.closure)
        self.assert_nested_result(mutate.build_mutant_source(self.m, src))
        self.assertEqual(snapshot, (src.texts, src.hashes, src.closure))
        self.assertEqual(disk, {p.relative_to(self.root): p.read_bytes()
                                for p in self.root.rglob("*") if p.is_file()})

    def test_removing_injection_fails_the_exact_target_oracle(self):
        source = textwrap.dedent(inspect.getsource(mutate.build_mutant_source))
        guard = 'text = text.replace(m["old"], m["new"], 1)'
        self.assertEqual(1, source.count(guard))
        namespace = dict(vars(mutate))
        exec(source.replace(guard, "text = text", 1), namespace)
        removed = namespace["build_mutant_source"](self.m, mutate.Sources(self.root))
        with self.assertRaises(AssertionError):
            self.assert_nested_result(removed)
        self.assertEqual(2, removed.count("int guard = 1;"))

    def test_direct_main_target_leaves_all_includes_intact(self):
        m = dict(id="MAIN", desc="main", old="int main_guard = 1;", new="int main_guard = 0;")
        self.assertEqual(self.MAIN.replace(m["old"], m["new"]),
                         mutate.build_mutant_source(m, mutate.Sources(self.root)))

    def test_missing_or_duplicate_anchor_is_rejected_before_emission(self):
        for text in (self.TARGET.replace("int guard = 1;", "int changed = 1;"),
                     self.TARGET + "\nint guard = 1;\n"):
            with self.subTest(text=text):
                self.write("layer/target/guard.c", text)
                with self.assertRaisesRegex(ValueError, "錨點"):
                    mutate.build_mutant_source(self.m, mutate.Sources(self.root))

    def test_target_included_twice_is_rejected(self):
        for main, unity in ((self.MAIN, self.UNITY + '#include "target/guard.c"\n'),
                            (self.MAIN + '#include "layer/unity.inc"\n', self.UNITY)):
            with self.subTest(main=main, unity=unity):
                self.write(mutate.MAIN_REL, main)
                self.write("layer/unity.inc", unity)
                with self.assertRaisesRegex(ValueError, "included more than once"):
                    mutate.build_mutant_source(self.m, mutate.Sources(self.root))

    def test_two_distinct_include_paths_are_rejected(self):
        self.write(mutate.MAIN_REL, self.MAIN + '#include "layer/second.inc"\n')
        self.write("layer/second.inc", '#include "target/guard.c"\n')
        with self.assertRaisesRegex(ValueError, "included more than once"):
            mutate.build_mutant_source(self.m, mutate.Sources(self.root))

    def test_missing_target_and_unreachable_target_are_rejected(self):
        (self.root / self.m["file"]).unlink()
        src = mutate.Sources(self.root)
        with self.assertRaisesRegex(ValueError, "目標檔"):
            mutate.build_mutant_source(self.m, src)
        self.write("layer/unity.inc", "/* target no longer included */\n")
        src = mutate.Sources(self.root)
        src.texts[self.m["file"]] = self.TARGET
        with self.assertRaisesRegex(ValueError, "not reachable"):
            mutate.build_mutant_source(self.m, src)

    def test_missing_include_inside_emitted_target_is_rejected(self):
        self.write("layer/target/guard.c", self.TARGET + '\n#include "missing.h"\n')
        with self.assertRaisesRegex(ValueError, "include missing"):
            mutate.build_mutant_source(self.m, mutate.Sources(self.root))

    def test_repository_escape_is_rejected(self):
        outside = pathlib.Path(self.tmp.name) / "outside.h"
        outside.write_text("int must_not_be_read;\n", encoding="utf-8")
        for include in ("../../../outside.h", "..\\..\\..\\outside.h", "C:/outside.h"):
            with self.subTest(include=include):
                self.write("layer/target/guard.c", self.TARGET + '\n#include "' + include + '"\n')
                src = mutate.Sources(self.root)
                self.assertNotIn("outside.h", src.texts)
                with self.assertRaisesRegex(ValueError, "include escapes repository"):
                    mutate.build_mutant_source(self.m, src)

    def test_cycle_on_target_path_is_rejected(self):
        self.write("layer/unity.inc", self.UNITY + '#include "../current_geometry.c"\n')
        with self.assertRaisesRegex(ValueError, "include cycle"):
            mutate.build_mutant_source(self.m, mutate.Sources(self.root))

    def test_guarded_cycle_in_unexpanded_sibling_remains_an_include(self):
        self.write("sibling.c", '#ifndef SIBLING\n#define SIBLING\n#include "cycle.h"\n#endif\n')
        self.write("cycle.h", '#include "sibling.c"\n')
        self.assert_nested_result(mutate.build_mutant_source(self.m, mutate.Sources(self.root)))

    def test_nested_dependency_changes_original_closure_hash(self):
        before = mutate.Sources(self.root)
        self.write("layer/target/helper.h", "int helper_must_remain_in_header_changed;\n")
        after = mutate.Sources(self.root)
        self.assertNotEqual(before.closure, after.closure)
        self.assertEqual(before.hashes[self.m["file"]], after.hashes[self.m["file"]])
        self.assertEqual(before.texts[self.m["file"]], after.texts[self.m["file"]])

    def test_generated_source_fingerprint_invalidates_cache_when_emitter_changes(self):
        src = mutate.Sources(self.root)
        calls = []

        def fake_compile(m, exe):
            calls.append(m["id"])
            pathlib.Path(exe).write_bytes(b"inert fake executable fixture")
            return True, ""

        cache = pathlib.Path(self.tmp.name) / "cache"
        compile_sha = "c" * 64
        before = mutate.mutant_fingerprint(self.m, src, compile_sha)
        self.assertEqual("built", mutate.prepare_mutant_exe(self.m, src, cache, fake_compile,
                                                            compile_sha=compile_sha)[0])
        self.assertEqual("cached", mutate.prepare_mutant_exe(self.m, src, cache, fake_compile,
                                                             compile_sha=compile_sha)[0])
        real_emit = mutate.build_mutant_source
        with mock.patch.object(mutate, "build_mutant_source", side_effect=lambda m, s: real_emit(m, s) + "\n/* emitter changed */\n"):
            after = mutate.mutant_fingerprint(self.m, src, compile_sha)
            self.assertNotEqual(before["generated_source_sha256"], after["generated_source_sha256"])
            for key in ("mutant_sha256", "closure_sha256", "compile_sha256"):
                self.assertEqual(before[key], after[key])
            self.assertEqual("built", mutate.prepare_mutant_exe(self.m, src, cache, fake_compile,
                                                                compile_sha=compile_sha)[0])
        self.assertEqual(["MF", "MF"], calls)

    def test_invalid_injection_and_compile_failure_never_become_killed(self):
        self.write("layer/unity.inc", self.UNITY + '#include "target/guard.c"\n')
        compiler = mock.Mock(side_effect=AssertionError("must not compile invalid injection"))
        cache = pathlib.Path(self.tmp.name) / "invalid-cache"
        status, _, message = mutate.prepare_mutant_exe(self.m, mutate.Sources(self.root), cache,
                                                       compiler, compile_sha="c" * 64)
        self.assertEqual("invalid", status)
        self.assertIn("included more than once", message)
        compiler.assert_not_called()
        self.write("layer/unity.inc", self.UNITY)
        status, exe, _ = mutate.prepare_mutant_exe(
            self.m, mutate.Sources(self.root), cache,
            lambda m, p: (False, "編譯失敗: inert fixture"), compile_sha="c" * 64)
        self.assertEqual("invalid", status)
        self.assertFalse(exe.exists())
        self.assertFalse(mutate.sidecar_path(exe).exists())


class LiveMutationAnchorMigration(unittest.TestCase):
    def test_all_fifty_definitions_keep_live_or_retired_targets(self):
        groups = {
            "geometry-core/kernel/geometry.c": ["M%02d" % n for n in range(1, 13)] + ["M39", "M40", "M59", "M60"],
            "geometry-core/kernel/grid.c": ["M31", "M32", "M53", "M54"],
            "geometry-templates/woodworking/native/contact_world.c": ["M13", "M14", "M15"],
            "geometry-templates/woodworking/native/supports.c": ["M16", "M17", "M18", "M57"],
            "geometry-templates/woodworking/native/member_reference.c": ["M%02d" % n for n in range(19, 27)] + ["M28", "M29", "M30", "M33", "M34", "M58"],
            "geometry-templates/woodworking/native/world_validation.c": ["M36", "M37", "M56"],
            "current_geometry.c": ["M27", "M35", "M38", "M51", "M52", "M55"],
        }
        expected = {mid: path for path, ids in groups.items() for mid in ids}
        self.assertEqual(50, len(expected))
        # main 02baea2c (train 17/18) adds M61-M77; they stay at their current owners.
        added = {"M%02d" % n: "current_geometry.c" for n in range(71, 78)}
        added.update({mid: "geometry-core/parameters.inc" for mid in ("M61", "M62", "M63", "M64", "M65", "M68", "M69", "M70")})
        added.update({mid: "geometry-web/engineering_bridge.inc" for mid in ("M66", "M67")})
        self.assertEqual(17, len(added))
        self.assertEqual({**expected, **added}, {m["id"]: mutate.mutant_file(m) for m in mutate.MUTANTS})
        # Exactly the ten preview-only guards run on the actual bridge (P-135/P-141).
        self.assertEqual({"M%02d" % n for n in range(61, 71)},
                         {m["id"] for m in mutate.MUTANTS if m.get("binary") == "bridge"})
        self.assertEqual({"M35", "M51", "M55"}, {m["id"] for m in mutate.MUTANTS if m.get("retired")})
        self.assertEqual({"M09", "M23", "M36", "M56"}, {m["id"] for m in mutate.MUTANTS if m.get("equivalent")})
        src = mutate.Sources(mutate.ROOT)
        snapshot = (dict(src.texts), dict(src.hashes), src.closure)
        with mock.patch.object(mutate, "run_cmd", side_effect=AssertionError("native commands forbidden")):
            for m in mutate.MUTANTS:
                with self.subTest(mid=m["id"]):
                    kind, _ = mutate.definition_kind(m, src)
                    if m.get("retired"):
                        self.assertEqual("retired", kind)
                        continue
                    self.assertEqual("equivalent" if m.get("equivalent") else "run", kind)
                    if m.get("binary") == "bridge":
                        # Executed in place by tests/mutation_bridge.py on the actual bridge;
                        # the core pass never expands them from current_geometry.c.
                        continue
                    marker = "/* exact-mutation-target:" + m["id"] + " */"
                    marked = dict(m, new=marker + m["new"] + marker)
                    emitted = mutate.build_mutant_source(marked, src)
                    self.assertEqual(2, emitted.count(marker))
                    self.assertTrue(marked["new"] in emitted, m["id"] + " exact injected body missing")
                    for name in mutate.INCLUDE_RE.findall(emitted):
                        self.assertTrue((mutate.ROOT / name).is_file(), name)
                    untouched = ("geometry-app/native/woodworking_unity.inc"
                                 if mutate.mutant_file(m).startswith("geometry-core/kernel/")
                                 else "geometry-core/kernel/kernel_unity.inc")
                    self.assertTrue('#include "' + untouched + '"' in emitted,
                                    m["id"] + " unrelated unity include must remain: " + untouched)
        self.assertEqual(snapshot, (src.texts, src.hashes, src.closure))


if __name__ == "__main__":
    unittest.main()
