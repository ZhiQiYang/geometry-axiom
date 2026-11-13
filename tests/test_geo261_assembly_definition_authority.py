"""Returned W assembly definitions control policy, values and write targets.

Portable checks never build. Native fixtures and exact named negative controls
are dispatched only by the serialized validation lane.
"""
from copy import deepcopy
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_assembly_sources import fixture as original_fixture
from tests.test_geo261_wood_assembly import canonical, record
from tests.test_geo261_parameter_definition_sources import definition

MODULE = ROOT / "geometry-templates/woodworking/native"


def fixture():
    value = original_fixture()
    changed_binding = deepcopy(value["binding"])
    changed_binding["slots"][1]["A"] = {"kind": "literal", "value": 35}
    slot = deepcopy(changed_binding["slots"][1])
    slot["A"]["value"] = 37
    policy = deepcopy(slot)
    policy["contactFace"] = "B"
    changed_rule = deepcopy(value["rule"])
    changed_rule["slots"].append({"id": 59, "name": "returned unused slot"})
    instance = record()
    instance["source"]["members"][1]["guideId"] = 99
    mapping = record()["mapping"]
    mapping[0]["timberId"] = 4
    generated_instance = record()
    generated_instance["mapping"] = mapping
    dormant = deepcopy(value["incomplete"])
    dormant["name"] = "returned unfinished"
    value["authority"] = {
        "binding": changed_binding, "slot": slot, "slotPolicy": policy,
        "rule": changed_rule, "instance": instance, "mapping": mapping,
        "dormant": dormant,
        "bindingResult": {"id": 9, "complete": False},
        "checkResult": {"id": 2, "valid": False},
        "result": {"width": 43, "depth": 47, "surfaceId": 1, "guideId": 2,
                   "between": [91, 90], "direction": 2, "role": 1, "timberId": 4},
        **{"generated" + str(member): {"instance": deepcopy(generated_instance), "memberId": member}
           for member in (11, 37, 89)},
    }
    return value


# Scoped replacements are intentional: each removed use has an independent
# behavioral oracle. A compiler error, crash, timeout, or other ASSERT is not a kill.
CONTROLS = (
    ("rule-authority", "wood_assembly_load_rule", "*(AsmRuleVersion *)slot=decoded;", "(void)decoded;", "rule", "returned-rule-controls-original-binding-policy"),
    ("binding-authority", "wood_assembly_definition", 'wood_assembly_read_json(s,&value,"wood.assembly.binding/1",authored,sizeof authored,&j)',
     's->context.json_parse(s->context.user,&j,wood_assembly_binding(&s->base,id)->content)', "binding", "returned-binding-controls-dimensions"),
    ("slot-authority", "wood_assembly_slot_text", "memcpy(out,canonical,strlen(canonical)+1);",
     "if(sub==17){strcpy(canonical,\"{\\\"A\\\":{\\\"field\\\":\\\"A\\\",\\\"id\\\":\\\"wood\\\",\\\"kind\\\":\\\"material\\\",\\\"version\\\":1},\\\"B\\\":{\\\"field\\\":\\\"B\\\",\\\"id\\\":\\\"wood\\\",\\\"kind\\\":\\\"material\\\",\\\"version\\\":1},\\\"contactFace\\\":\\\"A\\\",\\\"orientation\\\":\\\"A\\\",\\\"slotId\\\":17}\");}memcpy(out,canonical,strlen(canonical)+1);", "slot", "returned-slot-controls-dimensions"),
    ("instance-authority", "wood_assembly_load_generated", "r->instance=decoded;", "r->instance=decoded;memcpy(r->instance.guide,wood_assembly_instance(&s->base,id)->guide,sizeof r->instance.guide);", "instance", "returned-instance-controls-guide-and-partial-order"),
    ("mapping-authority", "wood_assembly_generated_record", "*out=&r->instance;return true;", "memcpy(r->instance.timber,wood_assembly_instance(&s->base,id)->timber,sizeof r->instance.timber);*out=&r->instance;return true;", "mapping", "returned-mapping-controls-definition-only-ownership"),
    ("generated-authority", "wood_assembly_load_generated", "r->instance=decoded;", "r->instance=*wood_assembly_instance(&s->base,id);", "generated", "returned-generated-definition-controls-write-target"),
    ("result-authority", "wood_assembly_sources_generated", "return wood_assembly_generated_read(s,&value,out);",
     "WoodAssemblySourceResult *r=wood_assembly_record(s,WOOD_ASSEMBLY_SOURCE_GENERATED,id,0,member);if(!r)return false;*out=r->generated;return true;", "result", "returned-generated-result-controls-every-field"),
    ("binding-result-authority", "wood_assembly_binding_hook", "out->complete=complete;", "out->complete=true;", "check", "returned-binding-result-controls-complete-cache"),
    ("check-result-authority", "wood_assembly_check_hook", "&&valid;}", ";}", "check", "returned-check-result-controls-validation"),
    ("schema-validation", "wood_assembly_read_json", "strcmp(value->as.definition.schema,schema)", "false", "malformed", "malformed-returned-definition-is-atomic"),
    ("canonical-validation", "wood_assembly_read_json", "strlen(canonical)!=value->as.definition.content_size||memcmp(canonical,text,value->as.definition.content_size)", "false", "malformed", "malformed-returned-definition-is-atomic"),
    ("width-bound", "wood_assembly_generated_read", "geo_coord_in_range(d.width)", "true", "malformed", "returned-result-rejects-overflow-atomically"),
    ("depth-bound", "wood_assembly_generated_read", "geo_coord_in_range(d.depth)", "true", "malformed", "returned-result-rejects-overflow-atomically"),
)


class AssemblyDefinitionAuthorityBoundary(unittest.TestCase):
    def test_consumers_read_returned_authored_records_and_results(self):
        text = (MODULE / "assembly_sources.c").read_text(encoding="utf-8")
        for name in ("wood_assembly_load_rule", "wood_assembly_load_binding", "wood_assembly_slot_text", "wood_assembly_load_instance", "wood_assembly_load_generated", "wood_assembly_generated_read", "wood_assembly_check_read"):
            self.assertIn("wood_assembly_read_json(", definition(text, name))
        self.assertNotIn("r->generated", definition(text, "wood_assembly_sources_generated"))
        self.assertNotIn("r->binding", definition(text, "wood_assembly_binding_hook"))
        self.assertNotIn("loaded", text)
        self.assertIn("s->context.state=s->shadow", text)
        for hook in ("source_version_field", "source_version_definition", "source_application"):
            self.assertIn("e->" + hook + "!=a->" + hook, definition(text, "wood_assembly_sources_bind"))

    def test_definition_only_ownership_and_registration_are_lazy(self):
        text = (MODULE / "assembly_sources.c").read_text(encoding="utf-8")
        for name in ("wood_assembly_sources_owned", "wood_assembly_sources_definitions"):
            body = definition(text, name)
            self.assertNotRegex(body, r"wood_assembly_quantity\(|footprint\(|wood_assembly_member_definition_direct\(")
        self.assertNotIn("geo_eval_source(", definition(text, "wood_assembly_sources_create"))
        self.assertNotIn("geo_eval_", definition(text, "wood_assembly_sources_destroy"))
        self.assertNotRegex(text, r"\b(?:World|ReferenceEval|TimberAnchor)\b|internal/|geometry-app")

    def test_controls_have_unique_scoped_anchors_and_declared_cases(self):
        text = (MODULE / "assembly_sources.c").read_text(encoding="utf-8")
        harness = (ROOT / "tests/geo261_assembly_definition_authority_harness.c").read_text(encoding="utf-8")
        self.assertEqual(len(CONTROLS), len({item[0] for item in CONTROLS}))
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(1, definition(text, function).count(before))
                self.assertNotEqual(before, after)
                self.assertIn('"' + case + '"', harness)
                self.assertIn('"' + marker + '"', harness)
        self.assertIn("#define geo_eval_source authority_source", harness)


class AssemblyDefinitionAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.directory = build.woodworking / "assembly-definition-authority"
        cls.directory.mkdir(exist_ok=True)
        for path in build.woodworking.glob("*.h"):
            shutil.copy2(path, cls.directory / path.name)
        for name in ("assembly.h", "assembly.c", "assembly_sources.h", "assembly_sources.c"):
            shutil.copy2(MODULE / name, cls.directory / name)
        for name in ("geo261_assembly_sources_harness.c", "geo261_assembly_definition_authority_harness.c"):
            shutil.copy2(ROOT / "tests" / name, cls.directory / name)
        cls.policy = build.compile(cls.directory / "assembly.c", "assembly-definition-authority-policy")
        cls.client = build.compile(cls.directory / "geo261_assembly_definition_authority_harness.c", "assembly-definition-authority-client")
        cls.exe = build.link("assembly-definition-authority-client", cls.objects(build, cls.client))
        cls.fixture_path = build.work / "assembly-definition-authority-fixture.json"
        cls.fixture_path.write_text(canonical(fixture()), encoding="utf-8")

    @classmethod
    def objects(cls, build, client):
        return [client, cls.policy, build.wood_engineering_object, build.wood_engineering_sources_object,
                build.wood_members_object, *build.kernel_objects()]

    def case(self, name, executable=None, marker=None):
        result = subprocess.run([str(executable or self.exe), name, str(self.fixture_path)], capture_output=True, text=True, timeout=40)
        self.assertEqual(1 if marker else 0, result.returncode, "Native crash/setup failure is not a verdict:\n" + result.stderr)
        if marker:
            self.assertRegex(result.stderr, r"\AASSERT:" + re.escape(marker) + r":[0-9]+\r?\n\Z")
        else:
            self.assertEqual("", result.stderr)
        return result

    def test_plain_differential_original_errors_partial_writes_and_lifetimes(self): self.case("baseline")
    def test_returned_binding_controls_actual_dimensions(self): self.case("binding")
    def test_returned_slot_controls_dimensions_and_contact_policy(self): self.case("slot")
    def test_returned_rule_controls_original_slot_coverage_policy(self): self.case("rule")
    def test_returned_instance_controls_guide_and_partial_write_order(self): self.case("instance")
    def test_returned_mapping_controls_ownership_targets_supports_and_dimensions(self): self.case("mapping")
    def test_returned_generated_definition_controls_actual_write_target(self): self.case("generated")
    def test_returned_generated_result_controls_all_result_fields(self): self.case("result")
    def test_returned_binding_and_instance_check_results_are_consumed(self): self.case("check")
    def test_malformed_returned_definitions_leave_outputs_and_authoring_unchanged(self): self.case("malformed")
    def test_dormant_definitions_do_not_evaluate_quantities_or_geometry(self): self.case("dormant")

    def test_thirteen_controls_require_exact_named_failures(self):
        build = native()
        original = self.directory / "assembly_sources.c"
        original_bytes = original.read_bytes()
        text = original_bytes.decode("utf-8")
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case)
                body = definition(text, function)
                self.assertEqual(1, body.count(before))
                # The extracted body omits comments; source functions used here
                # contain no interior comments in their replacement anchors.
                start = text.index(before, text.index(function + "("))
                mutant = text[:start] + after + text[start + len(before):]
                control_dir = self.directory / name
                control_dir.mkdir(exist_ok=True)
                for path in self.directory.glob("*.h"):
                    shutil.copy2(path, control_dir / path.name)
                for filename in ("geo261_assembly_sources_harness.c", "geo261_assembly_definition_authority_harness.c"):
                    shutil.copy2(self.directory / filename, control_dir / filename)
                (control_dir / "assembly_sources.c").write_text(mutant, encoding="utf-8")
                changed = build.compile(control_dir / "geo261_assembly_definition_authority_harness.c", "assembly-authority-control-" + name)
                executable = build.link("assembly-authority-control-" + name, self.objects(build, changed))
                self.case(case, executable, marker)
                self.assertEqual(original_bytes, original.read_bytes())
                self.case(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
