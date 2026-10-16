"""W source-rule policy uses explicit candidate facts and actual K arithmetic."""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native


class GridRulesBoundary(unittest.TestCase):
    def test_policy_has_no_world_parser_or_global_baseline_dependency(self):
        code = (ROOT / "geometry-templates/woodworking/native/grid_rules.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|scene_error|app_grid_context|g_subgrid_before|g_parsing_scene_file|reference_capture_trial)\b")
        self.assertIn("geo_interval_subdivide(", code)
        self.assertIn("ctx->before", code)


class NativeGridRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "grid-rules-client.c"
        shutil.copy2(ROOT / "tests/geo261_grid_rules_harness.c", source)
        cls.client = build.compile(source, "grid-rules-client")
        cls.exe = build.link("grid-rules-client", [cls.client, *build.product_objects()])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a rule-policy verdict: " + result.stderr)
        return result.returncode

    def test_signed_cell_expression_references_and_active_timber_facts(self):
        self.assertEqual(0, self.case("references"))

    def test_referenced_edit_guards_rename_and_nonreused_highwater(self):
        self.assertEqual(0, self.case("edits"))

    def test_explicit_before_context_precedes_manual_cell_conflict(self):
        self.assertEqual(0, self.case("world"))

    def test_exact_source_binding_and_grid_lines_with_zero_placement_id(self):
        self.assertEqual(0, self.case("geometry"))

    def test_rule_definition_diagnostics_keep_first_error_order(self):
        self.assertEqual(0, self.case("validation"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.woodworking / "grid_rules.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one guard")
        path = build.woodworking / ("grid-rules-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "grid-rules-" + name)
        objects = [obj if old == build.wood_grid_rules_object else old for old in build.product_objects()]
        return build.link("grid-rules-" + name, [self.client, *objects])

    def test_removing_referenced_edit_guard_fails_independent_rejection_assertion(self):
        self.assertEqual(0, self.case("edits"))
        exe = self.mutant("referenced-edit", "if(old && wood_grid_rule_used(ctx,sid,key)", "if(false && wood_grid_rule_used(ctx,sid,key)")
        self.assertEqual(1, self.case("edits", exe))
        self.assertEqual(0, self.case("edits"))

    def test_removing_before_context_guard_fails_first_error_assertion(self):
        self.assertEqual(0, self.case("world"))
        exe = self.mutant("before-context", "if(ctx->before)for", "if(false)for")
        self.assertEqual(1, self.case("world", exe))
        self.assertEqual(0, self.case("world"))

    def test_removing_manual_conflict_guard_fails_rejection_assertion(self):
        self.assertEqual(0, self.case("world"))
        exe = self.mutant("manual-conflict", "if(s)for(size_t j=0;j<s->rule_count;++j)", "if(false)for(size_t j=0;j<s->rule_count;++j)")
        self.assertEqual(1, self.case("world", exe))
        self.assertEqual(0, self.case("world"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
