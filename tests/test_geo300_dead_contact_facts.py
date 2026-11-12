"""H contact consumers skip only unobserved eager facts, retaining real K/W flow.

The two work withdrawals must exit normally at distinct named assertions.
Independent fresh candidates compare all ordered source nodes/edges and values
against the frozen eager callsites. This suite does not replace N512/H7 gates.
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
REFERENCE = "geometry-app/native/reference_sources.inc"
EAGER = "{app_contact_facts_prepare(world,placement,boundary,facts,NULL);}"
CALLBACK = (
    "static bool reference_contact_facts(void *opaque,GeoEvalContext *evaluation,\n"
    "    const WoodContactSourceRequest *request,WoodContactSourceFacts *out)\n{"
)
FAST_COLLECT = (
    "    size_t count=0;bool handled=false;\n"
    "    bool source_ok=app_contact_sources_collect(world,placement->id,along_v,exclude,out,out_cap,&handled,&count);\n"
    "    if(handled)return source_ok?count:0;"
)
DOMAIN_ONLY = "AppContactFacts facts;app_contact_domain_only(placement,boundary,&facts);"


class DeadContactFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = native()
        cls.sequence = 0
        cls.harness = ROOT / "tests/geo300_dead_contact_facts_harness.c"
        cls.exe = cls.compile_variant("baseline", ())

    @classmethod
    def compile_variant(cls, name, changes):
        destination = cls.build.work / ("dead-contact-facts-source-" + name)
        harness = copy_product_closure(cls.harness, destination)
        instruments = (
            (HOST, EAGER, EAGER.replace("{", "{++dead_facts_eager_calls;", 1)),
            (REFERENCE, CALLBACK, CALLBACK + "\n    ++dead_facts_callback_calls;"),
        )
        for relative, before, after in (*instruments, *changes):
            path = destination / relative
            source = path.read_text(encoding="utf-8")
            if source.count(before) != 1:
                raise AssertionError("Expected one production anchor: " + name + " / " + relative)
            path.write_text(source.replace(before, after), encoding="utf-8")
        obj = cls.build.compile(harness, "dead-contact-facts-" + name, PRODUCT_DEFINES)
        return cls.build.link("dead-contact-facts-" + name, [obj, *cls.build.product_objects()])

    def case(self, name, exe=None, marker=None):
        command = [str(exe or self.exe), name]
        result = subprocess.run(command, capture_output=True, timeout=30)
        if directory := os.environ.get("GEO300_DEAD_FACTS_LOG"):
            type(self).sequence += 1
            out = Path(directory) / (f"{self.sequence:03d}-" + name + ("-red" if marker else "-green"))
            out.mkdir(parents=True, exist_ok=False)
            (out / "stdout.bin").write_bytes(result.stdout)
            (out / "stderr.bin").write_bytes(result.stderr)
            sources = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                       for path in (HOST, REFERENCE, "tests/geo300_dead_contact_facts_harness.c", "tests/test_geo300_dead_contact_facts.py")}
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

    def test_source_collect_skips_unused_work_and_preserves_all_graph_values(self):
        self.case("collect")

    def test_handled_failure_keeps_original_error_and_untouched_output(self):
        self.case("collect-failure")

    def test_absent_context_and_snapshot_context_keep_real_raw_fallback(self):
        self.case("fallback")

    def test_end_source_refresh_is_at_original_point_with_identical_graph(self):
        self.case("ends")

    def test_end_source_failure_keeps_original_error_position(self):
        self.case("end-failure")

    def test_span_extension_error_precedes_failing_provider(self):
        self.case("extension")

    def test_rectangle_boundary_and_derived_domain_views_have_valid_storage(self):
        self.case("domain")

    def test_restore_collect_eager_work_is_named_red_then_restored_green(self):
        self.case("collect")
        mutant = self.compile_variant("restore-collect", ((HOST, FAST_COLLECT, "    size_t count=0;"),))
        self.case("collect", mutant, "dead-collect-skips-unused-eager-facts")
        self.case("collect")

    def test_restore_end_eager_work_is_different_named_red_then_restored_green(self):
        self.case("ends")
        mutant = self.compile_variant("restore-end", ((REFERENCE, DOMAIN_ONLY,
            "AppContactFacts facts;app_contact_facts(world,placement,boundary,&facts);"),))
        self.case("ends", mutant, "dead-end-skips-unused-eager-members")
        self.case("ends")


if __name__ == "__main__":
    unittest.main(verbosity=2)
