"""Authored W facts consumed through K source values; native execution is serialized."""
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
MODULE = ROOT / 'geometry-templates/woodworking/native'


class DefinitionSourceBoundary(unittest.TestCase):
    def test_public_module_has_no_host_or_private_kernel_access(self):
        for name in ('definition_sources.h', 'definition_sources.c'):
            text = (MODULE / name).read_text(encoding='utf-8')
            code = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
            self.assertNotRegex(code, r'\b(?:World|ReferenceEval|TimberAnchor|PlacementSurface)\b')
            self.assertNotIn('internal/', text)
            self.assertNotIn('geometry-app', text)

    def test_registration_and_description_do_not_evaluate(self):
        code = (MODULE / 'definition_sources.c').read_text(encoding='utf-8')
        describe = code[code.index('static bool wd_describe'):code.index('static bool wd_evaluate')]
        self.assertNotIn('geo_eval_', describe)
        create = code[code.index('WoodDefinitionSources *wood_definition_sources_create'):code.index('void wood_definition_sources_destroy')]
        self.assertIn('geo_eval_register', create)
        self.assertNotIn('geo_eval_source', create)
        self.assertNotIn('sizeof(WoodMember)', code)
        self.assertNotIn('sizeof(WoodMemberPlacement)', code)


CONTROLS = (
    ('literal-value', '*out=v.as.quantity.num;', '*out=v.as.quantity.num+1;', 'codec', 'literal-actual-quantity'),
    ('literal-edge', 'wd_get(s,kind,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)', 'wd_get(s,kind,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)', 'graph', 'literal-declaration-identity-edge'),
    ('RC-room-edge', 'if(space){GeoEnclosureSourceKey key;', 'if(false){GeoEnclosureSourceKey key;', 'graph', 'RC-room-definition-only-edge'),
    ('UV-cache', 'bool input_uv=a->anchor_kind==WOOD_ANCHOR_AT||a->anchor_kind==WOOD_ANCHOR_AT_GUIDES;', 'bool input_uv=true;', 'canonical', 'rebuilt-caches-excluded-from-definitions'),
    ('fixity-value', 'b.fixity[l][i]=(WoodEdgeFixity)(int32_t)wd_read(&r,4);', 'b.fixity[l][i]=(WoodEdgeFixity)((int32_t)wd_read(&r,4)+1);', 'codec', 'actual-boundary-fixity'),
)


class DefinitionSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        path = build.woodworking / 'definition-sources-client.c'
        shutil.copy2(ROOT / 'tests/geo261_definition_sources_harness.c', path)
        cls.client = build.compile(path, 'definition-sources-client')
        cls.exe = build.link('definition-sources-client', cls.objects(build))

    @classmethod
    def objects(cls, build, changed=None):
        return [cls.client, changed or build.wood_definition_sources_object, *build.kernel_objects()]

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), 'Crash or setup failure is not a verdict: ' + result.stderr)
        return result

    def test_canonical_codec_and_actual_returned_values(self):
        result = self.case('codec')
        self.assertEqual(0, result.returncode, result.stderr)

    def test_real_dependency_kinds_and_unused_definition_enumeration(self):
        result = self.case('graph')
        self.assertEqual(0, result.returncode, result.stderr)

    def test_cache_exclusion_candidate_identity_and_both_teardown_orders(self):
        result = self.case('canonical')
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_bound_owned_outputs_and_readonly_description(self):
        result = self.case('failure')
        self.assertEqual(0, result.returncode, result.stderr)

    def test_five_negative_controls_fail_named_assertions(self):
        build = native()
        original = build.woodworking / 'definition_sources.c'
        baseline = original.read_bytes()
        text = baseline.decode('utf-8')
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(0, self.case(case).returncode)
                self.assertEqual(1, text.count(before))
                path = build.woodworking / ('definition-control-' + name + '.c')
                path.write_text(text.replace(before, after), encoding='utf-8')
                changed = build.compile(path, 'definition-control-' + name)
                exe = build.link('definition-control-' + name, self.objects(build, changed))
                result = self.case(case, exe)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn('ASSERT:' + marker + ':', result.stderr)
                self.assertEqual(baseline, original.read_bytes())
                self.assertEqual(0, self.case(case).returncode)


if __name__ == '__main__':
    unittest.main(verbosity=2)
