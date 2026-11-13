"""Actual W declaration policy, old diagnostic order and host replacement.

The product control deliberately changes only the first refusal: custom zero
still fails the constructor. A different message is the observable defect.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests.test_geo261_native_kernel import native

MODULE = ROOT / "geometry-templates/woodworking/native"


def function(source, name):
    match = re.search(r"\b" + re.escape(name) + r"\([^;]*?\)\s*\{", source)
    if not match:
        raise AssertionError("Missing function definition: " + name)
    begin = source.index("{", match.start())
    level = 1
    for end in range(begin + 1, len(source)):
        level += (source[end] == "{") - (source[end] == "}")
        if level == 0:
            return source[begin + 1:end]
    raise AssertionError("Unclosed function: " + name)


class MemberDeclarationBoundary(unittest.TestCase):
    def test_public_declaration_policy_uses_explicit_candidate_members_and_services(self):
        for name in ("member_declaration.h", "member_declaration.c"):
            source = (MODULE / name).read_text(encoding="utf-8")
            code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
            self.assertNotRegex(code, r"\b(?:World|TimberAnchor|ReferenceEval|EngDimensionSource|scene_error|tokens|world_replace_object)\b")
            self.assertNotIn("internal/", source)
            self.assertNotIn("geometry-app", source)
        source = (MODULE / "member_declaration.c").read_text(encoding="utf-8")
        self.assertIn("wood_member_construct(", source)
        self.assertNotIn("static bool wood_member_construct", source)

    def test_actual_parser_preserves_capacity_role_priority_decode_and_publication_order(self):
        source = (ROOT / "current_geometry.c").read_bytes().decode("utf-8").replace("\r\n", "\n")
        body = function(source, "apply_timber_line")
        names = ("wood_member_declaration_capacity(", "wood_member_declaration_role(",
                 "wood_member_declaration_priority(", "parse_u32(", "wood_member_declare(")
        positions = [body.index(name) for name in names]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(body.index("wood_member_declaration_capacity("), body.index("if(count<5"))
        self.assertIn("if(error)scene_error(", body)
        self.assertNotIn("wood_member_construct(", body)
        self.assertNotRegex(body, r"\b(?:for|while)\s*\(")
        self.assertIn("assembly_owned(user,id)", function(source, "app_member_declaration_owned"))
        self.assertIn("world_replace_object(user,current,updated,sizeof *updated)", function(source, "app_member_declaration_replace"))


REPLACE = "return context->replace(context->user,&context->members[i],&updated);"
CONTROLS = (
    ("capacity-first", "if(*context->count==context->capacity){", "if(false){", "capacity", "capacity-first-missing-id"),
    ("capacity-existing", "if(supplied)for(size_t i=0;", "if(false)for(size_t i=0;", "capacity", "capacity-existing-update-allowed"),
    ("custom-role", "else if(!strcmp(name,\"custom\"))*role=WOOD_MEMBER_ROLE_CUSTOM;", "else if(!strcmp(name,\"custom\"))*role=WOOD_MEMBER_ROLE_PRIMARY;", "roles", "four-exact-role-identities"),
    ("priority-supplied", "if(!supplied||!valid||priority<1)", "if(!valid||priority<1)", "roles", "custom-priority-must-be-supplied"),
    ("priority-valid", "if(!supplied||!valid||priority<1)", "if(!supplied||priority<1)", "roles", "custom-priority-must-parse"),
    ("priority-minimum", "priority<1", "priority<0", "roles", "custom-zero-priority-refused"),
    ("fixed-role-priority", "}else if(supplied)return declaration_refuse", "}else if(false)return declaration_refuse", "roles", "fixed-role-priority-forbidden"),
    ("assembly-owned", "if(context->owned&&context->owned(context->user,id))", "if(false)", "ownership", "assembly-owner-before-invalid-dimensions"),
    ("placed-preserved", "updated.placed=context->members[i].placed;", "updated.placed=false;", "updates", "update-retains-placed-state"),
    ("replace-called", REPLACE, "return true;", "updates", "update-calls-host-replacement"),
    ("replace-result", REPLACE, "context->replace(context->user,&context->members[i],&updated);return true;", "updates", "replacement-failure-propagates"),
    ("existing-invalid-diagnostic", "if(!wood_member_construct(id,0,size_a,size_b,true,role,priority,&updated))return false;", "if(!wood_member_construct(id,0,size_a,size_b,true,role,priority,&updated))return declaration_refuse(error,\"new diagnostic\");", "updates", "existing-invalid-keeps-old-diagnostic"),
    ("new-invalid-diagnostic", "return declaration_refuse(error,\"角材的長度與 A/B 尺寸都要大於 0\");", "return false;", "append", "new-invalid-dimension-diagnostic"),
    ("append-count", "++*context->count;return true;", "return true;", "append", "append-one-record-per-success"),
)


class WoodMemberDeclaration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "member-declaration-client.c"
        shutil.copy2(ROOT / "tests/geo261_member_declaration_harness.c", source)
        cls.client = build.compile(source, "member-declaration-client")
        cls.exe = build.link("member-declaration-client", cls.objects(build))

    @classmethod
    def objects(cls, build, changed=None):
        return [cls.client, changed or build.wood_member_declaration_object,
                build.wood_members_object, *build.kernel_objects()]

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.exe), name], capture_output=True,
                                text=True, encoding="utf-8", timeout=20)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a declaration verdict: " + result.stderr)
        if result.returncode:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_capacity_precedes_admission_and_existing_update_works_at_capacity(self):
        result = self.case("capacity")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_exact_four_roles_custom_priority_and_unchanged_source_text(self):
        result = self.case("roles")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_assembly_ownership_is_first_guard_without_candidate_writes(self):
        result = self.case("ownership")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_redeclaration_preserves_placed_host_replacement_and_old_invalid_diagnostic(self):
        result = self.case("updates")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_new_declaration_constructor_diagnostics_fields_and_append_atomicity(self):
        result = self.case("append")
        self.assertEqual(0, result.returncode, result.stderr)

    def mutant(self, control):
        name, before, after, _, _ = control
        build = native()
        source = (build.woodworking / "member_declaration.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Control must change one actual site: " + name)
        path = build.woodworking / ("member-declaration-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        return build.compile(path, "member-declaration-" + name)

    def test_fourteen_guards_fail_named_assertions_and_restore_baseline(self):
        build = native()
        for control in CONTROLS:
            with self.subTest(control=control[0]):
                baseline = self.case(control[3])
                self.assertEqual(0, baseline.returncode, baseline.stderr)
                changed = self.mutant(control)
                executable = build.link("member-declaration-mutant-" + control[0], self.objects(build, changed))
                result = self.case(control[3], executable)
                self.assertEqual(1, result.returncode, "Guard survived: " + control[0])
                self.assertIn("ASSERT:" + control[4], result.stderr)
                restored = self.case(control[3])
                self.assertEqual(0, restored.returncode, restored.stderr)

    def priority_transaction(self, executable, expected, absent):
        with _bridge.BridgeSession(executable) as bridge:
            self.assertTrue(bridge.command("reset")["ok"])
            before = bridge.command("dump")["text"]
            response = bridge.line("timber 17 27 33 role custom priority 0")
            self.assertFalse(response["ok"], response)
            self.assertIn(expected, response["error"])
            self.assertNotIn(absent, response["error"])
            self.assertEqual(before, bridge.command("dump")["text"])
            self.assertEqual([], bridge.command("objects")["timbers"])

    def test_same_priority_guard_changes_real_bridge_first_error_with_both_transactions_atomic(self):
        build = native()
        baseline = build.bridge()
        original = "custom 角色需要 priority N（N 是 ≥1 的整數）"
        changed_error = "角材的長度與 A/B 尺寸都要大於 0"
        self.priority_transaction(baseline, original, changed_error)
        control = next(item for item in CONTROLS if item[0] == "priority-minimum")
        changed = self.mutant(control)
        client = build.link("member-declaration-product-mutant-client", self.objects(build, changed))
        result = self.case("roles", client)
        self.assertEqual(1, result.returncode)
        self.assertIn("ASSERT:custom-zero-priority-refused", result.stderr)
        objects = build.product_objects()
        self.assertEqual(1, objects.count(build.wood_member_declaration_object))
        bridge = build.link("member-declaration-product-mutant-bridge", [build.bridge_object,
            *[changed if item == build.wood_member_declaration_object else item for item in objects]])
        self.priority_transaction(bridge, changed_error, original)
        self.priority_transaction(baseline, original, changed_error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
