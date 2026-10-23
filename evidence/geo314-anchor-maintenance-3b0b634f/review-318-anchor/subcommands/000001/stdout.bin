"""W grid admission and mutation guards, including the real bridge path."""
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native
from tests.test_grid_system_contract import rejection_reason


class GridApplicationBoundary(unittest.TestCase):
    def test_policy_has_no_host_world_or_ambient_candidate_dependency(self):
        code = (ROOT / "geometry-templates/woodworking/native/grid_application.c").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)
        self.assertNotRegex(code, r"\b(?:World|Coord|scene_error|world_find_placement|g_subgrid_before|g_parsing_scene_file)\b")
        self.assertIn("wood_eng_object_bound(", code)
        self.assertIn("geo_grid_systems_redeclare(", code)


class WoodGridApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "grid-application-client.c"
        shutil.copy2(ROOT / "tests/geo261_grid_application_harness.c", source)
        cls.client = build.compile(source, "grid-application-client")
        cls.exe = build.link("grid-application-client", [cls.client, *build.product_objects()])

    def case(self, name, exe=None, marker=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a grid-policy verdict: " + result.stderr)
        self.assertEqual(1 if marker else 0, result.returncode, name + ": " + result.stderr)
        if marker:
            self.assertEqual("ASSERT:" + marker + "\n", result.stderr, "Wrong assertion cannot count as a killed guard: " + result.stderr)
        self._last_case = result
        return result.returncode

    def test_roles_follow_source_identity_across_kernel_remove_and_reinsert(self):
        self.assertEqual(0, self.case("roles"))

    def test_direct_source_identity_lock_declarations_and_capacity(self):
        self.assertEqual(0, self.case("direct"))

    def test_source_application_admission_engineering_locks_and_unchanged_rejections(self):
        self.assertEqual(0, self.case("admission"))

    def test_child_parent_type_index_space_and_stagger_order(self):
        self.assertEqual(0, self.case("child"))

    def test_delete_child_guide_timber_order_and_source_binding_closure(self):
        self.assertEqual(0, self.case("deletion"))

    def test_callback_facts_belong_to_candidate_and_original_stays_unchanged(self):
        self.assertEqual(0, self.case("candidate"))

    def mutant(self, name, before, after, bridge=False):
        build = native()
        source = (build.woodworking / "grid_application.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change one production guard")
        path = build.woodworking / ("grid-application-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        obj = build.compile(path, "grid-application-" + name)
        self.assertEqual(1, build.product_objects().count(build.wood_grid_application_object))
        objects = [obj if old == build.wood_grid_application_object else old for old in build.product_objects()]
        client = build.link("grid-application-" + name, [self.client, *objects])
        if not bridge:
            return client
        build.bridge()
        product = build.link("grid-application-" + name + "-bridge", [build.bridge_object, *objects])
        return client, product

    def test_removed_engineering_guard_fails_admission_assertion(self):
        self.assertEqual(0, self.case("admission"))
        before = 'if(wood_eng_object_bound(&c->engineering,0,g.id))return wood_grid_error(error,cap,"D29/I37:'
        after = 'if(false)return wood_grid_error(error,cap,"D29/I37:'
        exe = self.mutant("engineering-lock", before, after)
        self.assertEqual(1, self.case("admission", exe, "grid-engineering-source-lock"))
        self.assertEqual(0, self.case("admission"))

    def test_removed_child_identity_guard_fails_parent_change_assertion(self):
        self.assertEqual(0, self.case("child"))
        before = '(old&&(!old->is_subgrid||old->parent_id!=g->parent_id||old->lattice_cell!=lattice))'
        exe = self.mutant("child-identity", before, "false")
        self.assertEqual(1, self.case("child", exe, "grid-child-parent-lock"))
        self.assertEqual(0, self.case("child"))

    def test_removed_guide_delete_guard_fails_ordered_rejection_assertion(self):
        self.assertEqual(0, self.case("deletion"))
        exe = self.mutant("guide-delete", "if(used)return wood_grid_error", "if(false)return wood_grid_error")
        self.assertEqual(1, self.case("deletion", exe, "grid-guide-delete-before-timber"))
        self.assertEqual(0, self.case("deletion"))

    def test_stagger_commit_decision_table_and_ordered_sources(self):
        self.assertEqual(0, self.case("stagger-commit"))

    def stagger_control(self, name, case, marker, before, after):
        """A real removed product guard must fail the named normal assertion."""
        self.assertEqual(0, self.case(case))
        baseline = self._last_case
        exe = self.mutant("stagger-" + name, before, after)
        self.assertEqual(1, self.case(case, exe, marker))
        withdrawn = self._last_case
        self.assertEqual(0, self.case(case))
        restored = self._last_case
        def row(result):
            return {"command": result.args, "exit_code": result.returncode,
                    "stdout": result.stdout, "stderr": result.stderr}
        print("GEO314_W_CONTROL_JSON " + json.dumps({"control": name,
            "baseline": row(baseline), "withdrawn": row(withdrawn), "restored": row(restored)},
            ensure_ascii=False), flush=True)

    def test_stagger_removed_new_two_axis_guard_fails_new_system_assertion(self):
        self.stagger_control("new-two-axis", "stagger-w01", "stagger-new-two-axis",
            "if(!old||!(old->axis[0].stagger_set&&old->axis[1].stagger_set))", "if(0)")

    def test_stagger_removed_legacy_value_guard_fails_changed_axis_assertion(self):
        self.stagger_control("legacy-value", "stagger-w06", "stagger-legacy-u-changed",
            "if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis]))", "if(0)")

    def test_stagger_removed_same_reference_exception_fails_card_edit_assertion(self):
        self.stagger_control("same-reference", "stagger-w11", "stagger-ref-card-edit-is-not-an-edit",
            "if(prior->set&&current->set&&prior->parameter_id==current->parameter_id&&prior->field_id==current->field_id)return false;",
            "if(0)return false;")

    def test_stagger_treating_one_axis_as_two_fails_switch_direction_assertion(self):
        self.stagger_control("single-is-dual", "stagger-w04", "stagger-switch-axis",
            "if(!(now->axis[0].stagger_set&&now->axis[1].stagger_set))continue;",
            "if(!(now->axis[0].stagger_set||now->axis[1].stagger_set))continue;")

    def test_stagger_ignoring_v_axis_fails_v_change_assertion(self):
        self.stagger_control("ignores-v", "stagger-w07", "stagger-legacy-v-changed",
            "for(int axis=0;axis<2;++axis)if(wood_grid_stagger_value_changed",
            "for(int axis=0;axis<1;++axis)if(wood_grid_stagger_value_changed")

    def test_stagger_ignoring_source_value_fails_unbind_assertion(self):
        self.stagger_control("ignores-source-value", "stagger-w13", "stagger-unbind-different-value",
            "return old->stagger!=now->stagger;", "return 0;")

    def test_stagger_removed_missing_store_guard_fails_assertion_without_crash(self):
        self.stagger_control("missing-store", "stagger-w17", "stagger-missing-store-fails-closed",
            "if(!after||!before||(!facts&&count))return wood_grid_error",
            "if(0)return wood_grid_error")

    def test_stagger_source_switch_blanket_exemption_fails_present_value_assertion(self):
        self.stagger_control("blanket-source-exemption", "stagger-o02",
            "stagger-ordered-unbind-must-preserve-present-value",
            "if(!card_edit&&prior->value!=f->after.value)return false;", "if(0)return false;")

    def test_stagger_missing_contiguity_fails_ordered_chain_assertion(self):
        self.stagger_control("missing-chain", "stagger-o11", "stagger-ordered-chain-is-contiguous",
            "if(f->order<=order||!wood_grid_stagger_same_point(&state,&f->before))return false;",
            "if(f->order<=order)return false;")

    def test_stagger_missing_order_fails_sequence_assertion(self):
        self.stagger_control("missing-order", "stagger-o08", "stagger-ordered-sequence-is-increasing",
            "if(f->order<=order||!wood_grid_stagger_same_point(&state,&f->before))return false;",
            "if(!wood_grid_stagger_same_point(&state,&f->before))return false;")

    def test_stagger_missing_final_source_binding_fails_endpoint_assertion(self):
        self.stagger_control("missing-endpoint", "stagger-o05", "stagger-ordered-final-source-is-bound",
            "return found&&wood_grid_stagger_same_point(&state,&final);", "return found;")

    def commit(self, session, command):
        result = session.command("line " + command)
        if "preview" in result:
            self.assertTrue(result["preview"]["valid"], result)
            result = session.command("line confirm " + str(result["preview"]["token"]))
        self.assertTrue(result["ok"], (command, result))

    def direct_edit(self, exe):
        with _bridge.BridgeSession(exe) as session:
            self.assertTrue(session.command("reset")["ok"])
            self.commit(session, "surface 10 origin 0 0 0 u +x v +y outline 0,0 200,0 200,200 0,200")
            self.commit(session, "grid-system 5 name-hex 67726964 main-along none u series 0 100 3 v series 0 100 3")
            self.commit(session, "grid 1 on 10 from-system 5 origin 0 0")
            original = session.command("dump")["text"]
            response = session.command("line grid 1 on 10 u 50 150")
            if "preview" in response:
                self.assertEqual(original, session.command("dump")["text"])
                accepted = bool(response["preview"]["valid"])
                if accepted:
                    self.assertTrue(session.command("line confirm " + str(response["preview"]["token"]))["ok"])
            else:
                accepted = bool(response.get("ok"))
            if not accepted:
                self.assertEqual(original, session.command("dump")["text"])
            return accepted, response

    def test_removed_direct_lock_fails_public_client_and_actual_bridge(self):
        build = native()
        self.assertEqual(0, self.case("direct"))
        accepted, response = self.direct_edit(build.bridge())
        self.assertFalse(accepted, response)
        self.assertIn("direct axis edits are not allowed", rejection_reason(response))
        exe, bridge = self.mutant("direct-source-lock", "if(old&&(old->from_system||old->from_binding))", "if(false)", bridge=True)
        self.assertEqual(1, self.case("direct", exe, "grid-direct-source-lock"))
        accepted, response = self.direct_edit(bridge)
        self.assertTrue(accepted, response)
        self.assertEqual(0, self.case("direct"))
        self.assertFalse(self.direct_edit(build.bridge())[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
