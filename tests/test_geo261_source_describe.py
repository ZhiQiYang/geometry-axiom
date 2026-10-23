"""Describe-only source metadata stays NEW until explicitly evaluated.

This standalone client is copied outside the repository and links only the
isolated K source object. Provider call counters distinguish describing a node
from evaluating it, including inside an active consumer and after sealing.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native


class SourceDescribe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "source-describe-client.c"
        shutil.copy2(ROOT / "tests/geo261_source_describe_harness.c", source)
        client = build.compile(source, "source-describe-client")
        cls.exe = build.link("source-describe-client", [client, build.source_object])

    def case(self, name):
        result = subprocess.run([str(self.exe), name], capture_output=True,
                                text=True, encoding="utf-8", timeout=10)
        self.assertIn(result.returncode, (0, 1),
                      "Native crash/setup failure is not a describe-only verdict: " + result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_scalar_and_length_metadata_remain_new_without_values_or_edges(self):
        self.case("quantities")

    def test_axis_metadata_keeps_global_and_placed_coordinate_context(self):
        self.case("axes")

    def test_describing_active_consumers_children_keeps_only_explicit_definition_edge(self):
        self.case("definition-edge")

    def test_describe_then_evaluate_calls_each_provider_operation_once(self):
        self.case("transition")

    def test_sealed_reads_existing_metadata_but_cannot_backfill_or_create_nodes(self):
        self.case("sealed")

    def test_missing_invalid_and_malformed_descriptions_preserve_output_bytes(self):
        self.case("failures")

    def test_definition_values_preserve_binary_content_schema_and_sealed_cache(self):
        self.case("definitions")


if __name__ == "__main__":
    unittest.main(verbosity=2)
