"""Real H warm placement/contact hints avoid K node hashing, keep every edge.

Reuses the existing load-residual harness without changing its assertions.
Two H-only withdrawals keep K's new API and all real providers intact. No
elapsed-time threshold and no dependency on a K test's private helpers.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_world_validation import copy_product_closure, PRODUCT_DEFINES

REFERENCE = "geometry-app/native/reference_sources.inc"
PLACEMENT_HINT = (
    "geo_eval_depend_hint(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&key),\n"
    "            GEO_DEPENDENCY_DEFINITION_REQUIRED,&ctx->member_reads[i].placement_node_hint)"
)
PLACEMENT_OLD = (
    "geo_eval_depend(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&key),\n"
    "            GEO_DEPENDENCY_DEFINITION_REQUIRED)"
)
FOOTPRINT_HINT = "geo_eval_depend_hint(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&ctx->member_reads[i].footprint_node_hint)"
FOOTPRINT_OLD = "geo_eval_depend(ctx->sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED)"
PLACEMENT_ENTRY = "static bool reference_member_placement_depend(ReferenceEval *ctx,size_t i,uint32_t id)\n{"
FOOTPRINT_ENTRY = "        if(!ctx->use_current_values&&!geo_eval_is_sealed(ctx->sources)&&ctx->member_reads[i].footprint_valid&&ctx->member_reads[i].placement==request->placement_id){"
HASH_ENTRY = "static uint64_t geo_source_node_hash(GeoSourceRef source)\n{"


def once(source, before, after):
    if source.count(before) != 1:
        raise AssertionError("Expected one production/test instrumentation anchor: " + before)
    return source.replace(before, after)


class HostDependHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = native()
        cls.sequence = 0
        kernel = (cls.build.kernel / "source.c").read_text(encoding="utf-8")
        kernel = once(kernel, HASH_ENTRY, HASH_ENTRY + "\n    h_hint_observe_hash(source);")
        kernel = once(kernel, '#include "source.h"',
                      '#include "source.h"\nextern void h_hint_observe_hash(GeoSourceRef source);')
        source = cls.build.work / "host-depend-hint-kernel.c"
        source.write_text(kernel, encoding="utf-8")
        cls.source_object = cls.build.compile(source, "host-depend-hint-kernel")
        cls.exe = cls.compile_variant("baseline")

    @classmethod
    def compile_variant(cls, name):
        destination = cls.build.work / ("host-depend-hint-source-" + name)
        harness = copy_product_closure(ROOT / "tests/geo300_host_depend_hint_harness.c", destination)
        legacy = destination / "tests/geo261_load_residual_harness.c"
        text = legacy.read_text(encoding="utf-8")
        # Only rename the old executable entry point in the private copy.
        text = once(text, "int main(int argc,char **argv)", "int residual_original_main(int argc,char **argv)")
        legacy.write_text(text, encoding="utf-8")
        path = destination / REFERENCE
        source = path.read_text(encoding="utf-8")
        if name == "withdraw-placement":
            source = once(source, PLACEMENT_HINT, PLACEMENT_OLD)
        elif name == "withdraw-footprint":
            source = once(source, FOOTPRINT_HINT, FOOTPRINT_OLD)
        elif name != "baseline":
            raise AssertionError("Unknown variant " + name)
        source = once(source, PLACEMENT_ENTRY, PLACEMENT_ENTRY +
                      "\n    if(residual_second_consumer)++h_hint_placement_calls;")
        source = once(source, FOOTPRINT_ENTRY, FOOTPRINT_ENTRY +
                      "\n            if(residual_second_consumer)++h_hint_footprint_calls;")
        path.write_text(source, encoding="utf-8")
        obj = cls.build.compile(harness, "host-depend-hint-" + name, PRODUCT_DEFINES)
        objects = cls.build.product_objects()
        if objects.count(cls.build.source_object) != 1:
            raise AssertionError("Expected exactly one original K source object")
        objects = [cls.source_object if item == cls.build.source_object else item for item in objects]
        return cls.build.link("host-depend-hint-" + name, [obj, *objects])

    def case(self, name, exe=None, marker=None):
        command = [str(exe or self.exe), name]
        result = subprocess.run(command, capture_output=True, timeout=30)
        if directory := os.environ.get("GEO300_HOST_HINT_LOG"):
            type(self).sequence += 1
            out = Path(directory) / (f"{self.sequence:03d}-" + name + ("-red" if marker else "-green"))
            out.mkdir(parents=True, exist_ok=False)
            (out / "stdout.bin").write_bytes(result.stdout)
            (out / "stderr.bin").write_bytes(result.stderr)
            paths = (REFERENCE, "geometry-core/references.inc", "geometry-core/kernel/source.c", "geometry-core/kernel/source.h",
                     "tests/geo261_load_residual_harness.c", "tests/geo300_host_depend_hint_harness.c", "tests/test_geo300_host_depend_hint.py")
            (out / "RESULT.json").write_text(json.dumps({
                "source_sha": os.environ.get("GITHUB_SHA"),
                "source_hashes": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
                "command": command, "cwd": str(ROOT), "timeout_seconds": 30,
                "exit": result.returncode, "expected_assertion": marker,
                "binary_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
            }, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(1 if marker else 0, result.returncode, result.stdout + result.stderr)
        lines = result.stdout.decode().splitlines()
        self.assertEqual(1 if marker else 2, len(lines), result.stdout + result.stderr)
        observed = json.loads(lines[0])
        expected = {"placement_calls": 2, "placement_hashes": 0,
                    "footprint_calls": 0 if name == "cache-anchor" else 2, "footprint_hashes": 0}
        if marker:
            target = "placement_hashes" if "placement" in marker else "footprint_hashes"
            expected[target] = 2
            self.assertRegex(result.stderr.decode(), r"^ASSERT:" + re.escape(marker) + r" line=\d+ expr=[^\n]+\n$")
        else:
            self.assertEqual("PASS " + name, lines[1])
            self.assertEqual(b"", result.stderr)
        self.assertEqual(expected, observed)

    def test_real_anchor_warm_reads_keep_original_edges_and_avoid_hash(self):
        self.case("cache-anchor")

    def test_real_contact_warm_reads_keep_five_ordered_edges_and_values(self):
        self.case("cache-contact")

    def test_warm_source_footprint_wins_over_stale_raw_uv(self):
        self.case("cache-footprint-source")

    def test_withdraw_placement_hint_is_named_red_then_restore(self):
        self.case("cache-contact")
        mutant = self.compile_variant("withdraw-placement")
        self.case("cache-contact", mutant, "host-placement-hint-warm-reads-skip-node-hash")
        self.case("cache-contact")

    def test_withdraw_footprint_hint_is_different_named_red_then_restore(self):
        self.case("cache-footprint-source")
        mutant = self.compile_variant("withdraw-footprint")
        self.case("cache-footprint-source", mutant, "host-footprint-hint-warm-reads-skip-node-hash")
        self.case("cache-footprint-source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
