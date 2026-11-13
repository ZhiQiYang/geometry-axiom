"""Bounded W grid codecs preserve authored definitions and evaluated values.

Portable checks never call native(). The native client links only the public
codec object; a control kill must be exit 1 with exactly its named ASSERT.
Compilation errors, crashes and unavailable compilers never count as kills.
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
from tests.test_geo261_native_kernel import native

WOOD = ROOT / "geometry-templates/woodworking/native"
HARNESS = ROOT / "tests/geo261_grid_definition_codec_harness.c"


def code(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def definition(source, name):
    source = code(source)
    match = re.search(
        r"^[\w *]+\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{",
        source, re.M | re.S,
    )
    if match is None:
        raise AssertionError("Missing function " + name)
    depth, end = 1, match.end()
    while depth:
        if end == len(source):
            raise AssertionError("Unclosed function " + name)
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


CONTROLS = (
    ("schema", "wood_grid_codec_begin", "strcmp(value->schema,schema)||",
     "false||", "malformed", "schema-mismatch-rejected"),
    ("system-id", "wood_grid_codec_system", "||system.id!=expected_id",
     "", "malformed", "system-identity-mismatch-rejected"),
    ("rule-key", "wood_grid_decode_rule", "||rule.key!=expected_rule_key",
     "", "malformed", "rule-key-mismatch-rejected"),
    ("u32", "wood_grid_codec_u32", "||value>UINT32_MAX",
     "", "scalars", "u32-overflow-rejected"),
    ("unsigned", "wood_grid_codec_unsigned", "||value>UINT_MAX",
     "", "scalars", "unsigned-overflow-rejected"),
    ("int", "wood_grid_codec_int", "||value<INT_MIN||value>INT_MAX",
     "", "scalars", "int-overflow-rejected"),
    ("bool", "wood_grid_codec_bool", "||value>1",
     "", "scalars", "boolean-overflow-rejected"),
    ("utf8", "wood_grid_codec_utf8", "(value>=0xd800&&value<=0xdfff)",
     "false", "malformed", "utf8-surrogate-rejected"),
    ("masked", "wood_grid_codec_axis", "if(number)return false;",
     "(void)number;", "malformed", "masked-number-nonzero-rejected"),
    ("cache", "wood_grid_codec_axis", "*values[i]=cache[i];",
     "*values[i]=0;", "authored", "authored-system-uses-cache-and-bytes"),
    ("bound", "wood_grid_codec_axis",
     "if(bound&&(!direct_application||evaluated||(i!=2&&i!=3)))return false;",
     "if(false)return false;", "malformed", "engineering-bound-slot-rejected"),
    ("trailing", "wood_grid_decode_binding", "if(reader.offset!=reader.size)return false;",
     "if(false)return false;", "malformed", "authored-trailing-data-rejected"),
    ("system-write", "wood_grid_encode_system_value", "system->next_rule_key",
     "0", "system-value", "system-value-independent-bytes"),
    ("app-lattice", "wood_grid_encode_application_value", "application->lattice_step[axis]",
     "0", "application-value", "application-value-independent-bytes"),
    ("logical-capacity", "wood_grid_codec_finish", "||writer->size>capacity",
     "", "atomic", "writer-capacity-failure-is-atomic"),
)


class GridDefinitionCodecBoundary(unittest.TestCase):
    def test_public_header_and_client_use_only_public_dependencies(self):
        header = (WOOD / "grid_definition_codec.h").read_text(encoding="utf-8")
        source = (WOOD / "grid_definition_codec.c").read_text(encoding="utf-8")
        harness = HARNESS.read_text(encoding="utf-8")
        for text in (header, source, harness):
            self.assertNotRegex(
                code(text), r"\b(?:World|App\w*|Timber|ReferenceEval)\b|geometry-app|current_geometry",
            )
            self.assertNotIn("internal/", text)
        self.assertEqual(
            ["grid_application.h", "source.h"],
            re.findall(r'^#include "([^"]+)"', header, re.M),
        )
        self.assertEqual(
            ["grid_definition_codec.h"],
            re.findall(r'^#include "([^"]+)"', source, re.M),
        )
        self.assertEqual(
            ["grid_definition_codec.h"],
            re.findall(r'^#include "([^"]+)"', harness, re.M),
        )
        self.assertNotRegex(code(harness), r'#\s*include\s*[<"][^>"\n]*\.c[>"]')

    def test_codec_owns_no_sourcegraph_or_grid_policy_calls(self):
        source = code((WOOD / "grid_definition_codec.c").read_text(encoding="utf-8"))
        public = {
            "wood_grid_decode_system", "wood_grid_decode_binding",
            "wood_grid_decode_application", "wood_grid_decode_rule",
            "wood_grid_encode_system_value", "wood_grid_decode_system_value",
            "wood_grid_encode_application_value", "wood_grid_decode_application_value",
        }
        calls = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", source))
        local = {name for name in calls if name.startswith("wood_grid_codec_")}
        self.assertEqual(set(), calls - local - public - {"if", "for", "while", "sizeof", "strcmp", "memcpy"})
        for name in public:
            self.assertIn(name, calls)
        self.assertNotRegex(source, r"\bgeo_(?:eval|source|grid|parameter)\w*\s*\(")

    def test_controls_target_one_live_expression_and_one_exact_named_assertion(self):
        source = (WOOD / "grid_definition_codec.c").read_text(encoding="utf-8")
        harness = code(HARNESS.read_text(encoding="utf-8"))
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                body = definition(source, function)
                self.assertEqual(1, body.count(before))
                self.assertEqual(1, code(source).count(body))
                self.assertNotEqual(before, after)
                self.assertEqual(1, harness.count('"' + marker + '"'))
                self.assertIn('"' + case + '"', harness)
        self.assertEqual(15, len(CONTROLS))
        self.assertEqual(15, len({row[0] for row in CONTROLS}))
        self.assertEqual(15, len({row[5] for row in CONTROLS}))


class NativeGridDefinitionCodec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "grid-definition-codec-client.c"
        shutil.copy2(HARNESS, source)
        cls.client = build.compile(source, "grid-definition-codec-client")
        cls.provider = build.wood_grid_definition_codec_object
        cls.objects = [cls.client, cls.provider]
        cls.exe = build.link("grid-definition-codec-client", cls.objects)

    def case(self, name, exe=None, marker=None):
        run = subprocess.run(
            [str(exe or self.exe), name], capture_output=True, text=True,
            encoding="utf-8", timeout=30,
        )
        self.assertEqual(1 if marker else 0, run.returncode, run.stderr)
        self.assertEqual("ASSERT:" + marker + "\n" if marker else "", run.stderr)
        self.assertEqual("", run.stdout)

    def test_authored_system_binding_application_and_rule_preserve_authored_bytes_and_caches(self):
        self.case("authored")

    def test_derived_applications_preserve_omitted_axes_main_and_lattice_caches(self):
        self.case("derived")

    def test_signed_endpoints_unsigned_ranges_and_booleans_are_checked_before_narrowing(self):
        self.case("scalars")

    def test_schema_identity_utf8_masked_slots_bound_flags_and_trailing_data_are_rejected(self):
        self.case("malformed")

    def test_array_string_and_payload_bounds_accept_the_largest_supported_values(self):
        self.case("bounds")

    def test_system_value_matches_independent_bytes_and_preserves_resolved_parameter_caches(self):
        self.case("system-value")

    def test_application_value_matches_independent_bytes_and_preserves_axes_main_and_lattice(self):
        self.case("application-value")

    def test_failed_decoders_and_writers_leave_all_outputs_unchanged(self):
        self.case("atomic")

    def test_client_links_only_the_actual_codec_object(self):
        build = native()
        self.assertEqual([self.client, build.wood_grid_definition_codec_object], self.objects)
        links = [
            row for row in build.logs
            if str(self.exe) in row["arguments"] or "/Fe:" + str(self.exe) in row["arguments"]
        ]
        self.assertEqual(1, len(links))
        self.assertEqual(0, links[0]["exit"])
        linked_objects = [Path(arg) for arg in links[0]["arguments"] if Path(arg).suffix in (".o", ".obj")]
        self.assertEqual(self.objects, linked_objects)

    def test_fifteen_controls_fail_exact_named_assertions_between_passing_baselines(self):
        build = native()
        original_path = build.woodworking / "grid_definition_codec.c"
        original_bytes = original_path.read_bytes()
        original = original_bytes.decode("utf-8")
        source = code(original)
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case)
                body = definition(original, function)
                self.assertEqual(1, body.count(before))
                self.assertEqual(1, source.count(body))
                path = build.woodworking / ("grid-definition-control-" + name + ".c")
                changed_source = source.replace(body, body.replace(before, after, 1), 1)
                self.assertNotEqual(source, changed_source)
                path.write_bytes(changed_source.encode("utf-8"))
                try:
                    changed = build.compile(path, "grid-definition-control-" + name)
                    exe = build.link("grid-definition-control-" + name, [self.client, changed])
                    self.case(case, exe, marker)
                finally:
                    self.assertEqual(original_bytes, original_path.read_bytes())
                    self.case(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
