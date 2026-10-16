"""Complete immutable K versions, separate W metadata, and actual field values.

The same real provider serves isolated W and the product candidate. Controls
must reach one exact named assertion with ordinary exit 1; setup/build failures
and crashes never count. Native execution is scheduled by the serialized P1
runner. Portable codec vectors do not claim native execution.
"""
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_engineering_sources import engineering_product_scene


class VersionFieldSourceVectors(unittest.TestCase):
    def test_version_key_vector_is_independently_big_endian_and_binary_safe(self):
        source = (ROOT / "tests/geo261_version_field_sources_harness.c").read_text(encoding="utf-8")
        body = re.search(r"static const unsigned char expected\[\]=\{([^}]+)\}", source).group(1)
        actual = bytes(map(int, re.findall(r"\d+", body)))
        self.assertEqual(struct.pack(">BIII", 2, 3, 0x01020304, 4) + b"\x00\xffx", actual)

    def test_archive_metadata_vector_keeps_kind_version_identity_and_flag(self):
        source = (ROOT / "tests/geo261_version_field_sources_harness.c").read_text(encoding="utf-8")
        body = re.search(r"static const unsigned char meta_expected\[\]=\{([^}]+)\}", source).group(1)
        actual = bytes(map(int, re.findall(r"\d+", body)))
        self.assertEqual(struct.pack(">BII", 1, 0x01020304, 1) + b"a\x01", actual)


class VersionFieldSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "version-field-sources-client.c"
        shutil.copy2(ROOT / "tests/geo261_version_field_sources_harness.c", client)
        cls.client = build.compile(client, "version-field-sources-client")
        cls.objects = [build.wood_engineering_object, build.wood_engineering_sources_object, *build.kernel_objects()]
        cls.exe = build.link("version-field-sources-client", [cls.client, *cls.objects])
        cls.product_client = build.compile(ROOT / "tests/geo261_version_field_sources_harness.c", "version-field-sources-product-client",
            ["GEO261_VERSION_FIELD_PRODUCT=1", "GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
             "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
        cls.product = build.link("version-field-sources-product-client", [cls.product_client, *build.product_objects()])
        cls.scene = build.work / "version-field-sources-product.scene"
        cls.scene.write_text(engineering_product_scene(), encoding="utf-8")

    def case(self, case, *, exe=None, product=False, failure=None):
        command = [str(exe or (self.product if product else self.exe)), case]
        if product:
            command.append(str(self.scene))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a version-field verdict: " + result.stderr)
        self.assertEqual(1 if failure else 0, result.returncode, result.stdout + "\n" + result.stderr)
        if failure:
            self.assertRegex(result.stderr, r"^ASSERT:" + re.escape(failure) + r":\d+\n$")
        return result

    def test_canonical_complete_version_codec_and_metadata_fail_without_partial_writes(self):
        self.case("codec")

    def test_all_unused_versions_metadata_and_huge_decimal_descriptions_do_zero_value_work(self):
        self.case("inventory")

    def test_actual_selected_width_length_a_b_and_gap_have_exact_typed_edges(self):
        self.case("selected")

    def test_override_keeps_inactive_gap_unevaluated_and_preserves_type_error_order(self):
        self.case("override")

    def test_actual_returned_complete_definition_controls_field_without_changing_store(self):
        self.case("definition-tamper")

    def test_actual_returned_field_controls_wood_value_without_raw_fallback(self):
        self.case("field-tamper")

    def test_actual_returned_method_slots_and_axis_choose_the_consumed_material_field(self):
        self.case("slot-tamper")
        self.case("axis-tamper")

    def test_actual_returned_material_kind_controls_original_type_policy(self):
        self.case("kind-tamper")

    def test_actual_returned_application_controls_override_and_complete_shadow_fields(self):
        self.case("application-tamper")

    def test_malformed_returned_schema_unit_and_missing_field_fail_without_raw_quantity(self):
        self.case("schema-tamper")
        self.case("unit-tamper")
        self.case("missing-field-tamper")

    def test_archive_only_changes_metadata_and_other_candidate_survives_destroy(self):
        self.case("archive")

    def test_real_product_preview_confirm_and_undo_retain_version_provider_candidate(self):
        self.product_inventory_control()

    def product_inventory_control(self):
        build = native()
        source = ROOT / "geometry-app/native/reference_sources.inc"
        harness = ROOT / "tests/geo261_version_field_sources_harness.c"
        originals = [ROOT / "current_geometry.c", ROOT / "geometry-core/references.inc", source,
                     ROOT / "geometry-web/web_bridge.c", harness]
        saved = {path: path.read_bytes() for path in originals}
        texts = {path: data.replace(b"\r\n", b"\n").decode("utf-8") for path, data in saved.items()}
        before = "return app_world_candidate_version_inventory(g_active_app_candidate,ctx);"
        self.assertEqual(1, texts[source].count(before), "Product inventory control must hit exactly once")
        texts[source] = texts[source].replace(before, "return true;")
        copies = {path.resolve(): build.work / ("version-product-inventory-" + path.name) for path in originals}
        try:
            for original in originals:
                def include(match):
                    path = (original.parent / match.group(1)).resolve()
                    return '#include "' + str(copies.get(path, path)).replace("\\", "/") + '"'
                copies[original.resolve()].write_text(
                    re.sub(r'^#include "([^"]+)"', include, texts[original], flags=re.MULTILINE), encoding="utf-8")
            client = build.compile(copies[harness.resolve()], "version-product-inventory-control",
                ["GEO261_VERSION_FIELD_PRODUCT=1", "GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1",
                 "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
            exe = build.link("version-product-inventory-control", [client, *build.product_objects()])
            self.case("product", product=True)
            self.case("product", exe=exe, product=True, failure="product-complete-version-and-metadata-inventory")
            self.case("product", product=True)
        finally:
            for original, data in saved.items():
                self.assertEqual(data, original.read_bytes(), "Inventory control changed repository source: " + str(original))

    def control(self, module, before, after, case, marker, *, product=False):
        build = native()
        source_dir = build.kernel if module == "version_sources" else build.woodworking
        original = source_dir / (module + ".c")
        original_bytes = original.read_bytes()
        source = original_bytes.decode("utf-8")
        self.assertEqual(1, source.count(before), "Control must hit exactly once: " + marker)
        path = source_dir / ("version-field-control-" + marker + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "version-field-control-" + marker)
        target = {"version_sources": build.version_sources_object, "engineering": build.wood_engineering_object,
                  "engineering_sources": build.wood_engineering_sources_object}[module]
        self.assertEqual(1, self.objects.count(target))
        exe = build.link("version-field-control-" + marker, [self.client, *[changed if obj == target else obj for obj in self.objects]])
        self.case(case)
        self.case(case, exe=exe, failure=marker)
        self.case(case)
        if product:
            objects = build.product_objects()
            self.assertEqual(1, objects.count(target))
            product_exe = build.link("version-field-product-control-" + marker,
                [self.product_client, *[changed if obj == target else obj for obj in objects]])
            self.case("product", product=True)
            self.case("product", exe=product_exe, product=True, failure=marker)
            self.case("product", product=True)
        self.assertEqual(original_bytes, original.read_bytes(), "Control must leave baseline source intact")

    def test_wrong_field_and_definition_relations_fail_exact_named_edges(self):
        self.control("version_sources", "geo_eval_source(ctx,upstream,GEO_DEPENDENCY_DEFINITION_REQUIRED,&definition)",
                     "geo_eval_source(ctx,upstream,GEO_DEPENDENCY_VALUE_REQUIRED,&definition)", "selected", "version-field-definition-edge")
        self.control("engineering_sources", "GeoSourceStatus status=geo_eval_source(s->evaluation,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value);",
                     "GeoSourceStatus status=geo_eval_source(s->evaluation,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);",
                     "selected", "version-field-value-edge")

    def test_same_w_field_hook_bypass_fails_isolated_and_actual_product_edges(self):
        self.control("engineering", "if(w->source_version_field&&!w->source_version_field(w->sources,0,&m->ref,(uint32_t)s->field,value))",
                     "if(false&&w->source_version_field&&!w->source_version_field(w->sources,0,&m->ref,(uint32_t)s->field,value))",
                     "selected", "version-field-value-edge", product=True)

    def test_returned_definition_and_quantity_discard_controls_fail_actual_value_oracles(self):
        self.control("version_sources",
                     "if(!geo_version_definition_decode(definition.as.definition.content,definition.as.definition.content_size,&version,fields)||!geo_vs_identity(identity,version.identity))return false;",
                     "if(geo_versions_find(s->store,identity,&version)!=GEO_VERSION_OK)return false;memcpy(fields,version.fields,version.field_count*sizeof *fields);",
                     "definition-tamper", "actual-returned-definition-controls-field")
        self.control("engineering_sources",
                     'return wood_eng_fail(&s->context,"I35: effective dimension violates its positive/nonnegative integer mm range");\n    *out=value.as.quantity.num;return true;',
                     'return wood_eng_fail(&s->context,"I35: effective dimension violates its positive/nonnegative integer mm range");\n    (void)out;return true;',
                     "field-tamper", "actual-returned-field-controls-wood-value")

    def test_missing_metadata_inventory_fails_exact_unused_metadata_oracle(self):
        self.control("engineering_sources", "for(int kind=0;kind<2;++kind){", "for(int kind=2;kind<2;++kind){",
                     "inventory", "inventory-includes-all-unused-metadata-and-versions")

    def test_raw_policy_lookup_bypasses_fail_exact_slot_axis_kind_and_application_oracles(self):
        for case, marker in (("slot-tamper", "actual-returned-method-slot-controls-selection"),
                             ("axis-tamper", "actual-returned-method-axis-controls-selection"),
                             ("kind-tamper", "actual-returned-material-kind-controls-policy")):
            with self.subTest(case=case):
                self.control("engineering", "if(w->source_version_definition){", "if(false&&w->source_version_definition){", case, marker)
        self.control("engineering", "return w->source_application?w->source_application(w->sources,id):wood_eng_application_direct(w,id);",
                     "return wood_eng_application_direct(w,id);", "application-tamper", "actual-returned-application-controls-selection")
        self.control("engineering", "EngApplication *existing=wood_eng_application_direct(w,a.id);",
                     "EngApplication *existing=wood_eng_application(w,a.id);", "application-tamper", "application-put-updates-authored-record-not-shadow")


if __name__ == "__main__":
    unittest.main(verbosity=2)
