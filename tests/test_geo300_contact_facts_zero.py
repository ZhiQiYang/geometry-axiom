"""H facts initialization scales with live members, preserving original bytes.

Frozen baseline: 1cff9d8c3deab815d5ae6562f3163c95e6f82ac9. Only local
prepare memset calls are instrumented. Existing callback prefix/graph tests
remain unmodified; this suite is not a replacement for those tests or H7.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_world_validation import copy_product_closure, PRODUCT_DEFINES

HOST = "current_geometry.c"
START = "static void app_contact_facts_prepare("
END = "\nstatic void app_contact_facts("
WORLD_ZERO = "    memset(&facts->world,0,sizeof facts->world);\n"
LIVE_ZERO = "    memset(facts->members,0,world->wood.timber_count*sizeof *facts->members);"
WHOLE_ZERO = "    memset(facts,0,sizeof *facts);"


class ContactFactsZero(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = native()
        cls.sequence = 0
        cls.exe = cls.compile_variant("baseline")

    @classmethod
    def compile_variant(cls, name):
        destination = cls.build.work / ("contact-facts-zero-source-" + name)
        harness = copy_product_closure(ROOT / "tests/geo300_contact_facts_zero_harness.c", destination)
        path = destination / HOST
        source = path.read_text(encoding="utf-8")
        if source.count(START) != 1 or source.count(END) != 1:
            raise AssertionError("Expected one facts preparation function")
        start = source.index(START)
        end = source.index(END, start)
        body = source[start:end]
        if body.count(WORLD_ZERO) != 1 or body.count(LIVE_ZERO) != 1:
            raise AssertionError("Expected one header and one live-prefix initializer")
        if name == "restore-whole":
            body = body.replace(WORLD_ZERO + LIVE_ZERO, WHOLE_ZERO)
            if WHOLE_ZERO not in body:
                raise AssertionError("Whole memset withdrawal did not apply")
        elif name == "omit-live":
            body = body.replace(LIVE_ZERO, "    ")
        elif name != "baseline":
            raise AssertionError("Unknown variant: " + name)
        body = body.replace("memset(", "facts_counted_memset(")
        path.write_text(source[:start] + body + source[end:], encoding="utf-8")
        obj = cls.build.compile(harness, "contact-facts-zero-" + name, PRODUCT_DEFINES)
        return cls.build.link("contact-facts-zero-" + name, [obj, *cls.build.product_objects()])

    def case(self, name, exe=None, marker=None):
        command = [str(exe or self.exe), name]
        result = subprocess.run(command, capture_output=True, timeout=30)
        if directory := os.environ.get("GEO300_FACTS_ZERO_LOG"):
            type(self).sequence += 1
            out = Path(directory) / (f"{self.sequence:03d}-" + name + ("-red" if marker else "-green"))
            out.mkdir(parents=True, exist_ok=False)
            (out / "stdout.bin").write_bytes(result.stdout)
            (out / "stderr.bin").write_bytes(result.stderr)
            sources = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                       for path in (HOST, "geometry-app/native/reference_sources.inc",
                                    "tests/geo300_contact_facts_zero_harness.c", "tests/test_geo300_contact_facts_zero.py")}
            (out / "RESULT.json").write_text(json.dumps({
                "source_sha": os.environ.get("GITHUB_SHA"), "source_hashes": sources,
                "command": command, "cwd": str(ROOT), "timeout_seconds": 30,
                "exit": result.returncode, "expected_assertion": marker,
                "binary_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
            }, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(1 if marker else 0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(("ASSERT:" + marker + "\n").encode() if marker else b"", result.stderr)
        self.assertEqual(b"", result.stdout)

    def test_zero_one_128_512_work_follows_live_count(self):
        self.case("work")

    def test_deferred_live_members_match_original_including_invalid_bytes(self):
        self.case("live")

    def test_eager_raw_footprints_match_original(self):
        self.case("raw")

    def test_rectangle_boundary_derived_and_empty_derived_keep_original_storage(self):
        self.case("domains")

    def test_withdraw_whole_clear_is_named_red_then_restore(self):
        self.case("work")
        mutant = self.compile_variant("restore-whole")
        self.case("work", mutant, "facts-zero-work-scales-with-live-members")
        self.case("work")

    def test_omit_live_clear_is_different_named_red_then_restore(self):
        self.case("live")
        mutant = self.compile_variant("omit-live")
        self.case("live", mutant, "facts-zero-live-member-bytes-match-original")
        self.case("live")


if __name__ == "__main__":
    unittest.main(verbosity=2)
