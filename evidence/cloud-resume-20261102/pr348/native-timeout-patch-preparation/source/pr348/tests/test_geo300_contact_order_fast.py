"""GEO-300 W sort fast path: original per-face bytes and named work withdrawal.

The oracle in the C client is the original insertion-order/immediate-deletion
collector. No elapsed-time threshold or product/test exemption is introduced.
Instrumentation is confined to copied actual W source; compiler errors,
crashes, missing compiler and timeout never count as a killed control.
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
from tests.test_geo261_wood_contacts import record_native_execution


class ContactOrderFastPath(unittest.TestCase):
    @staticmethod
    def replace_one(source, before, after):
        if source.count(before) != 1:
            raise AssertionError("Expected one actual W anchor: " + before)
        return source.replace(before, after)

    @classmethod
    def instrument(cls, source):
        source = cls.replace_one(source, "#include <string.h>",
                                 "#include <string.h>\nstatic uint64_t geo300_member_sort_comparisons;")
        source = cls.replace_one(source,
            "    uint64_t left=order[a],right=order[b];",
            "    ++geo300_member_sort_comparisons;\n    uint64_t left=order[a],right=order[b];")
        return source + """
void geo300_sort_work_reset(void){geo300_member_sort_comparisons=0;}
uint64_t geo300_sort_comparisons(void){return geo300_member_sort_comparisons;}
"""

    @classmethod
    def setUpClass(cls):
        build = native()
        cls.source = (build.woodworking / "contact_world.c").read_text(encoding="utf-8")
        harness = build.woodworking / "geo300-contact-order-fast-client.c"
        shutil.copy2(ROOT / "tests/geo300_contact_order_fast_harness.c", harness)
        cls.client = build.compile(harness, "geo300-contact-order-fast-client")
        cls.baseline = cls.executable(cls.source, "baseline")

    @classmethod
    def executable(cls, source, phase):
        build = native()
        path = build.woodworking / ("geo300-contact-order-fast-" + phase + ".c")
        path.write_text(cls.instrument(source), encoding="utf-8")
        changed = build.compile(path, "geo300-contact-order-fast-" + phase)
        return build.link("geo300-contact-order-fast-" + phase,
                          [cls.client, changed, build.wood_contacts_object,
                           build.wood_supports_object, *build.kernel_objects()])

    def case(self, mode, executable=None, *, phase="positive", assertion=None):
        command = [str(executable or self.baseline), mode]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", timeout=20)
        record_native_execution(self.id(), command, result, case=mode, phase=phase,
                                control=assertion, assertion=assertion)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a control kill: " + result.stderr)
        return result

    def test_sorted_full_uint64_fields_match_original_without_merge(self):
        result = self.case("sorted")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_equal_order_retains_declaration_and_side_stability(self):
        result = self.case("ties")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_inversions_keep_original_full_width_stable_sort(self):
        result = self.case("unsorted")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_boundary_capacity_filter_duplicate_and_degenerate_cases(self):
        result = self.case("edges")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_full_member_capacity_matches_original_collector(self):
        result = self.case("capacity")
        self.assertEqual(0, result.returncode, result.stderr)

    def control(self, source, mode, assertion):
        baseline = self.case(mode, phase="baseline", assertion=assertion)
        self.assertEqual(0, baseline.returncode, baseline.stderr)
        mutant = self.executable(source, assertion)
        withdrawn = self.case(mode, mutant, phase="mutant", assertion=assertion)
        self.assertEqual(1, withdrawn.returncode, "Control survived: " + assertion)
        self.assertIn("ASSERT:" + assertion, withdrawn.stderr)
        restored = self.case(mode, phase="restored", assertion=assertion)
        self.assertEqual(0, restored.returncode, restored.stderr)

    def test_withdrawal_preserves_bytes_but_fails_named_work_assertion(self):
        source = self.replace_one(self.source, "    if(ordered)return;", "    if(false&&ordered)return;")
        self.control(source, "sorted", "contact-order-sorted-no-merge")

    def test_unconditional_skip_fails_named_unsorted_bytes_assertion(self):
        source = self.replace_one(self.source, "    if(ordered)return;", "    if(true)return;")
        self.control(source, "unsorted", "contact-order-unsorted-byte-oracle")


if __name__ == "__main__":
    unittest.main()
