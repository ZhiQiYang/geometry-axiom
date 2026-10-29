"""GEO-300: direct validation reads reuse successful anchors in one scope.

The real host translation unit is linked to the original O0 K/W/H objects.
The only diagnostic instrumentation is a counter at the original reader entry.
Real placed fixtures exercise both production callsites; provider source reads
are not replaced. These controls do not replace the 512-member formal tests or
ordered-source-graph equivalence checks.
"""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.geo300_scene_generator import build as scene
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_world_validation import copy_product_closure, PRODUCT_DEFINES

READER_ENTRY = (
    "static bool app_reference_member_anchor(const World *world,size_t i,WoodMemberPlacement *out)\n{"
)
MEMO_HIT = "if(memo->valid[i]){*out=memo->value[i];return true;}"
MEMO_BEGIN = (
    "static void app_anchor_memo_begin(AppAnchorMemo *memo,const World *world)\n"
    "{\n    memo->world=world;\n    memset(memo->valid,0,sizeof memo->valid);\n}"
)
MEMO_READ = "if(!app_reference_member_anchor(memo->world,i,out))return false;"
HOST_CALL = "app_anchor_memo_read(&((AppValidationInputs *)user)->anchors,i,&actual)"
REFERENCE_CALLS = (
    ("app_anchor_memo_read(&anchors,i,&actual_anchor)", "app_reference_member_anchor(w,i,&actual_anchor)"),
    ("app_anchor_memo_read(&anchors,j,&other_anchor)", "app_reference_member_anchor(w,j,&other_anchor)"),
)


class ValidationAnchorMemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = native()
        cls.harness = ROOT / "tests/geo300_validation_memo_harness.c"
        cls.fixture = cls.build.work / "validation-memo-eight-placed.scene"
        text, _ = scene(8, "single")
        cls.fixture.write_bytes(text.encode("utf-8"))
        cls.exe = cls.compile_variant("baseline", ())

    @classmethod
    def compile_variant(cls, name, changes):
        destination = cls.build.work / ("validation-anchor-source-" + name)
        harness = copy_product_closure(cls.harness, destination)
        source = destination / "geometry-app/native/reference_sources.inc"
        data = source.read_text(encoding="utf-8")
        if data.count(READER_ENTRY) != 1:
            raise AssertionError("Diagnostic counter must instrument exactly one real reader")
        source.write_text(data.replace(READER_ENTRY, READER_ENTRY + "\n    ++validation_test_anchor_reads;"), encoding="utf-8")
        for relative, before, after in changes:
            path = destination / relative
            data = path.read_text(encoding="utf-8")
            if data.count(before) != 1:
                raise AssertionError("Control must replace one production site: " + name)
            path.write_text(data.replace(before, after), encoding="utf-8")
        obj = cls.build.compile(harness, "validation-anchor-" + name, PRODUCT_DEFINES)
        return cls.build.link("validation-anchor-" + name, [obj, *cls.build.product_objects()])

    def case(self, name, exe=None, marker=None):
        command = [str(exe or self.exe), name]
        if name in ("reference", "world", "domain"):
            command.append(str(self.fixture))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(1 if marker else 0, result.returncode, result.stderr)
        self.assertEqual("ASSERT:" + marker + "\n" if marker else "", result.stderr)
        self.assertEqual("", result.stdout)

    def test_successful_reads_are_local_to_one_world_and_validation_scope(self):
        self.case("scope")

    def test_missing_and_out_of_range_members_retain_original_rejection(self):
        self.case("errors")

    def test_reference_check_uses_memo_on_actual_placed_world(self):
        self.case("reference")

    def test_world_validation_uses_memo_on_actual_placed_world(self):
        self.case("world")

    def test_host_view_borrows_scope_storage_and_preserves_failed_read(self):
        self.case("domain")

    def test_withdrawals_are_killed_by_distinct_original_assertions(self):
        adapter = "geometry-app/native/world_validation.inc"
        reference = "geometry-core/references.inc"
        controls = [
            ("hit", [(adapter, MEMO_HIT, MEMO_HIT.replace("if(memo->valid[i])", "if(false)"))],
             "scope", "anchor-memo-single-read-per-scope"),
            ("scope", [(adapter, MEMO_BEGIN, MEMO_BEGIN.replace("    memset(memo->valid,0,sizeof memo->valid);\n", ""))],
             "scope", "anchor-memo-new-scope-reloads-slot"),
            ("failure", [(adapter, MEMO_READ, MEMO_READ.replace("return false;", "{memo->valid[i]=true;return false;}"))],
             "errors", "anchor-memo-failure-not-cached"),
            ("reference", [(reference, before, after) for before, after in REFERENCE_CALLS],
             "reference", "anchor-memo-reference-callsite-linear-reads"),
            ("world", [(adapter, HOST_CALL, "app_reference_member_anchor(world,i,&actual)")],
             "world", "anchor-memo-world-callsite-linear-reads"),
            ("domain", [
                (adapter, "    const PlacementSurface *p;", "    PlacementSurface placement;\n    SpaceBoundarySurface boundary;\n    const PlacementSurface *p;"),
                (adapter, "    out->b=inputs->has_boundary?&inputs->boundary:NULL;\n    out->p=&inputs->host;",
                 "    out->placement=inputs->host;out->boundary=inputs->boundary;\n    out->b=inputs->has_boundary?&out->boundary:NULL;\n    out->p=&out->placement;")],
             "domain", "domain-borrow-no-host-copy"),
        ]
        for name, changes, case, marker in controls:
            with self.subTest(control=name):
                self.case(case)
                exe = self.compile_variant(name, changes)
                self.case(case, exe, marker)
                self.case(case)


if __name__ == "__main__":
    unittest.main()
