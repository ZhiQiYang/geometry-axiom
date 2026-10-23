"""Canonical neutral placement definitions and actual returned-value authority.

Portable checks never initialize NativeBuild. Native methods run only in the
serialized validation lane. Every mutation must exit 1 with its exact named
ASSERT; compile failure, timeout, crash or unavailable compiler is not a kill.
"""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import kernel_only_native

KERNEL = ROOT / "geometry-core/kernel"
HARNESS = ROOT / "tests/geo261_placement_definition_harness.c"


def code(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def definition(source, name):
    source = code(source)
    match = re.search(r"^[\w *]+\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", source, re.M | re.S)
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
    ("key-endian", "geo_source_u32", "id>>(24-8*i)", "id>>(8*i)", "keys", "definition-key-fixed-big-endian"),
    ("frame-axis", "geo_placement_definition_encode", "geo_pd_vector_write(&p,definition->frame.axis_u)", "geo_pd_vector_write(&p,definition->frame.axis_v)", "codec", "rect-exact-canonical-wire"),
    ("rect-endpoint", "geo_placement_definition_encode", "geo_pd_put64(&p,definition->rect.max_u)", "geo_pd_put64(&p,definition->rect.min_u)", "codec", "rect-exact-canonical-wire"),
    ("region-id", "geo_placement_definition_encode", "geo_pd_put32(&p,definition->region_id)", "geo_pd_put32(&p,0)", "codec", "reference-exact-canonical-wire"),
    ("component-order", "geo_placement_definition_encode", "&definition->components[c]", "&definition->components[definition->component_count-1-c]", "codec", "ordered-components-exact-canonical-wire"),
    ("loop-order", "geo_pd_loop_write", "loop->v[v].u", "loop->v[loop->count-1-v].u", "codec", "ordered-components-exact-canonical-wire"),
    ("encode-capacity", "geo_placement_definition_encode", "if(size>capacity)", "if(false)", "bounds", "short-encode-capacity-is-atomic"),
    ("decode-full-capacity", "geo_placement_definition_decode", "size>GEO_PLACEMENT_DEFINITION_MAX_BYTES", "size>=GEO_PLACEMENT_DEFINITION_MAX_BYTES", "bounds", "maximal-definition-decodes-exactly"),
    ("domain-tag", "geo_placement_definition_decode", "||domain>GEO_PLACEMENT_REGION_SET", "||false", "malformed", "unknown-domain-output-is-atomic"),
    ("trailing", "geo_placement_definition_decode", "if(r.p!=r.end)", "if(false)", "malformed", "trailing-definition-output-is-atomic"),
    ("atomic-decode", "geo_placement_definition_decode", "GeoPDReader r={content,", "memset(out,0,sizeof *out);GeoPDReader r={content,", "malformed", "truncated-definition-output-is-atomic"),
    ("raw-accessor", "geo_placement_sources_definition", "memcpy(out,&result,sizeof result)", "*out=*geo_placements_find(s->placements,id)", "typed", "returned-definition-overrides-raw-placement"),
    ("identity", "geo_placement_sources_definition", "||result.id!=id", "", "typed-invalid", "replacement-id-mismatch-is-atomic"),
    ("schema", "geo_placement_sources_definition", "strcmp(value.as.definition.schema,GEO_PLACEMENT_DEFINITION_SCHEMA)", "false", "typed-invalid", "replacement-schema-mismatch-is-atomic"),
    ("definition-edge", "geo_placement_sources_evaluate", "kind==GEO_PLACEMENT_SOURCE_DEFINITION?GEO_DEPENDENCY_DEFINITION_REQUIRED:GEO_DEPENDENCY_VALUE_REQUIRED", "GEO_DEPENDENCY_VALUE_REQUIRED", "typed", "replacement-edge-requires-definition"),
    ("early-frame", "geo_placement_sources_definition", "GEO_PLACEMENT_SOURCE_DEFINITION,id,&key", "GEO_PLACEMENT_SOURCE_FRAME,id,&key", "definition", "definition-only-reads-staged-invalid-geometry"),
    ("local-frame-raw", "geo_placement_sources_evaluate", "out->as.frame=p->frame", "out->as.frame=geo_placements_find(s->placements,id)->frame", "local-geometry", "local-frame-uses-actual-definition"),
    ("local-rect-raw", "geo_placement_sources_evaluate", "geo_placement_domain_view(p,s->regions", "geo_placement_domain_view(geo_placements_find(s->placements,id),s->regions", "local-geometry", "local-rect-uses-actual-definition"),
    ("local-region-ref-raw", "geo_placement_sources_evaluate", "s->region_token,p->region_id,&key", "s->region_token,geo_placements_find(s->placements,id)->region_id,&key", "local-geometry", "local-region-reference-uses-actual-definition"),
    ("local-components", "geo_placement_sources_evaluate", "memcpy(&record->decoded,&decoded,sizeof decoded)", "memcpy(&record->decoded,&decoded,sizeof decoded);record->decoded.components[0].outline.v[1].u=0", "local-geometry", "local-components-use-actual-definition"),
)


HEADER_CONTROLS = (('header-domain',
  'geo_placement_sources_definition_header',
  '*out=result;return true;',
  'result.domain=(GeoPlacementDomain)(result.domain+1);*out=result;return true;',
  'header-values',
  'header-domain-matches-full-projection'),
 ('header-region',
  'geo_pd_definition_header',
  'next.region_id=(uint32_t)count;',
  'next.region_id=(uint32_t)(count+1);',
  'header-values',
  'header-region-matches-full-projection'),
 ('header-tail',
  'geo_pd_definition_header',
  'r.p!=r.end||actual!=id',
  'actual!=id',
  'header-malformed',
  'header-tail-matches-full'),
 ('header-id',
  'geo_pd_definition_header',
  'r.p!=r.end||actual!=id',
  'r.p!=r.end',
  'header-authority',
  'header-id-rejection-matches-full'),
 ('header-domain-bound',
  'geo_pd_definition_header',
  '||domain>GEO_PLACEMENT_REGION_SET',
  '||false',
  'header-malformed',
  'header-domain-bound-matches-full'),
 ('header-component-bound',
  'geo_pd_definition_header',
  '||count>GEO_PLACEMENT_COMPONENT_CAPACITY',
  '||false',
  'header-malformed',
  'header-component-bound-matches-full'),
 ('header-hole-bound',
  'geo_pd_definition_header',
  '||count>GEO_REGION_MAX_HOLES',
  '||false',
  'header-malformed',
  'header-hole-bound-matches-full'),
 ('header-vertex-bound',
  'geo_pd_loop_skip',
  '||count>GEO_LOOP_MAX_VERTICES',
  '||false',
  'header-malformed',
  'header-vertex-bound-matches-full'),
 ('header-schema',
  'geo_placement_sources_definition_header',
  'strcmp(value.as.definition.schema,GEO_PLACEMENT_DEFINITION_SCHEMA)',
  'false',
  'header-authority',
  'header-schema-rejection-matches-full'),
 ('header-atomic',
  'geo_placement_sources_definition_header',
  'if(!s||!out)return false;',
  'if(!s||!out)return false;memset(out,0,sizeof *out);',
  'header-authority',
  'header-failure-preserves-all-output-bytes'),
 ('header-edge-kind',
  'geo_placement_sources_definition_header',
  'GEO_DEPENDENCY_DEFINITION_REQUIRED',
  'GEO_DEPENDENCY_VALUE_REQUIRED',
  'header-values',
  'header-consumer-edge-requires-definition'),
 ('header-binding',
  'geo_placement_sources_definition_header',
  '*out=result;return true;',
  'const GeoPlacementDefinition *raw=geo_placements_find(s->placements,id);if(!raw)return '
  'false;*out=(GeoPlacementDefinitionHeader){raw->domain,raw->region_id};return true;',
  'header-values',
  'header-domain-matches-full-projection'))


class PlacementDefinitionBoundary(unittest.TestCase):
    def test_provider_and_client_depend_only_on_public_kernel(self):
        header = (KERNEL / "placement_sources.h").read_text(encoding="utf-8")
        source = (KERNEL / "placement_sources.c").read_text(encoding="utf-8")
        harness = HARNESS.read_text(encoding="utf-8")
        for text in (header, source, harness):
            self.assertNotRegex(code(text), r"\b(?:World|App\w*|Wood\w*|Timber|ReferenceEval)\b|internal/|geometry-app|geometry-templates")
            self.assertNotRegex(code(text), r'#\s*include\s*[<"][^>"\n]*\.c[>"]')
        self.assertEqual(["placements.h", "source.h"], re.findall(r'^#include "([^"]+)"', header, re.M))
        self.assertEqual(["placement_sources.h"], re.findall(r'^#include "([^"]+)"', source, re.M))
        self.assertEqual(["placement_sources.h"], re.findall(r'^#include "([^"]+)"', harness, re.M))

    def test_definition_access_does_not_force_geometry_or_apply_geometry_validation(self):
        source = (KERNEL / "placement_sources.c").read_text(encoding="utf-8")
        for name in ("geo_placement_definition_encode", "geo_placement_definition_decode", "geo_placement_sources_register", "geo_placement_sources_describe"):
            self.assertNotRegex(definition(source, name), r"geo_(?:eval_(?:source|depend|describe)|frame_is_valid|placement_is_valid|region_is_valid)\(")
        for name in ("geo_placement_sources_definition", "geo_placement_sources_definition_header"):
            accessor = definition(source, name)
            self.assertIn("GEO_DEPENDENCY_DEFINITION_REQUIRED", accessor)
            self.assertNotRegex(accessor, r"GEO_PLACEMENT_SOURCE_(?:FRAME|REGIONS)|geo_placements_find\(")
        self.assertNotIn("geo_eval_", definition(source, "geo_placement_sources_destroy"))

    def test_controls_have_exactly_one_live_anchor_and_named_assertion(self):
        source = (KERNEL / "placement_sources.c").read_text(encoding="utf-8")
        harness = HARNESS.read_text(encoding="utf-8")
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                body = definition(source, function)
                self.assertEqual(1, body.count(before))
                self.assertEqual(1, code(source).count(body))
                self.assertNotEqual(before, after)
                self.assertEqual(1, harness.count('"' + marker + '"'))
                self.assertIn('"' + case + '"', harness)
        self.assertEqual(20, len(CONTROLS))
        self.assertEqual(20, len({row[0] for row in CONTROLS}))


class NativePlacementDefinition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = kernel_only_native()
        source = build.work / "placement-definition-client.c"
        shutil.copy2(HARNESS, source)
        cls.client = build.compile(source, "placement-definition-client")
        cls.objects = [cls.client, build.placement_sources_object, build.placements_object,
                       build.regions_object, build.source_object, build.geometry_object]
        cls.exe = build.link("placement-definition-client", cls.objects)

    def case(self, name, exe=None, marker=None, *, control=None, phase=None):
        command = [str(exe or self.exe), name]
        try:
            run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=15)
        except subprocess.TimeoutExpired as error:
            if control is not None:
                def captured(value):
                    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
                print(json.dumps({"schema": "geometry-placement-header-control-execution/1",
                    "control": control, "phase": phase, "command": command, "exitCode": None,
                    "timedOut": True, "timeoutSeconds": 15, "stdout": captured(error.stdout),
                    "stderr": captured(error.stderr)}, ensure_ascii=False), flush=True)
            raise
        if control is not None:
            print(json.dumps({"schema": "geometry-placement-header-control-execution/1",
                "control": control, "phase": phase, "command": command, "exitCode": run.returncode,
                "timedOut": False, "stdout": run.stdout, "stderr": run.stderr}, ensure_ascii=False), flush=True)
        self.assertEqual(1 if marker else 0, run.returncode, run.stderr)
        self.assertEqual("ASSERT:" + marker + "\n" if marker else "", run.stderr)
        self.assertEqual("", run.stdout)

    def test_fixed_kind_three_and_legacy_source_keys(self): self.case("keys")
    def test_independent_vectors_cover_all_active_fields_and_invalid_geometry(self): self.case("codec")
    def test_capacity_edges_and_encode_failures_preserve_output(self): self.case("bounds")
    def test_all_truncations_trailing_tags_and_counts_preserve_output(self): self.case("malformed")
    def test_definition_description_reads_and_owned_bytes_do_not_evaluate_geometry(self): self.case("definition")
    def test_actual_returned_definition_overrides_raw_and_uses_definition_edge(self): self.case("typed")
    def test_accessor_rejects_wrong_identity_schema_wire_and_value_kind_atomically(self): self.case("typed-invalid")
    def test_candidate_isolation_reset_teardown_and_existing_frame_regions(self): self.case("lifecycle")
    def test_local_frame_rect_reference_components_consume_actual_definition(self): self.case("local-geometry")
    def test_bound_geometry_retains_priority_and_failure_without_definition_forcing(self): self.case("bound-geometry")

    def test_linked_client_has_only_the_six_public_kernel_objects(self):
        build = kernel_only_native()
        self.assertTrue(build.kernel_only)
        self.assertFalse((build.work / "isolated-host").exists())
        self.assertFalse((build.work / "isolated-woodworking").exists())
        links = [row for row in build.logs if str(self.exe) in row["arguments"] or "/Fe:" + str(self.exe) in row["arguments"]]
        self.assertEqual(1, len(links))
        self.assertEqual(0, links[0]["exit"])
        linked = [Path(arg) for arg in links[0]["arguments"] if Path(arg).suffix in (".o", ".obj")]
        self.assertEqual(self.objects, linked)

    def test_twenty_controls_fail_exact_assertions_between_restored_baselines(self):
        build = kernel_only_native()
        original_path = build.kernel / "placement_sources.c"
        original_bytes = original_path.read_bytes()
        original = original_bytes.decode("utf-8")
        source = code(original)
        for name, function, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.case(case)
                body = definition(original, function)
                self.assertEqual(1, body.count(before))
                self.assertEqual(1, source.count(body))
                path = build.kernel / ("placement-definition-control-" + name + ".c")
                path.write_bytes(source.replace(body, body.replace(before, after, 1), 1).encode("utf-8"))
                try:
                    changed = build.compile(path, "placement-definition-control-" + name)
                    objects = [changed if obj == build.placement_sources_object else obj for obj in self.objects]
                    exe = build.link("placement-definition-control-" + name, objects)
                    self.case(case, exe, marker)
                finally:
                    self.assertEqual(original_bytes, original_path.read_bytes())
                    self.case(case)


    def test_header_projection_matches_full_public_api_for_all_canonical_domains_and_maximum(self):
        self.case("header-values")

    def test_header_full_wire_bounds_truncations_and_tail_match_original_decoder(self):
        self.case("header-malformed")

    def test_header_binding_values_active_dependencies_failures_reset_and_isolation(self):
        self.case("header-authority")

    def test_twelve_header_controls_fail_named_oracles_between_restored_baselines(self):
        build = kernel_only_native()
        original_path = build.kernel / "placement_sources.c"
        original_bytes = original_path.read_bytes()
        original = original_bytes.decode("utf-8")
        source = code(original)
        for name, function, before, after, case, marker in HEADER_CONTROLS:
            with self.subTest(control=name):
                self.case(case, control=name, phase="baseline")
                body = definition(original, function)
                self.assertEqual(1, body.count(before))
                self.assertEqual(1, source.count(body))
                path = build.kernel / ("placement-header-control-" + name + ".c")
                path.write_bytes(source.replace(body, body.replace(before, after, 1), 1).encode("utf-8"))
                try:
                    changed = build.compile(path, "placement-header-control-" + name)
                    objects = [changed if obj == build.placement_sources_object else obj for obj in self.objects]
                    exe = build.link("placement-header-control-" + name, objects)
                    self.case(case, exe, marker, control=name, phase="mutant")
                finally:
                    self.assertEqual(original_bytes, original_path.read_bytes())
                    self.case(case, control=name, phase="restored")


if __name__ == "__main__":
    unittest.main(verbosity=2)
