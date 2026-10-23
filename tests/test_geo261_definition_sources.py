"""Authored W facts consumed through K source values; native execution is serialized."""
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

CONTACT_VIEW_CONTROLS = (
    ('contact-host-offset', 'contact.placement_id=(uint32_t)wd_read(&r,4);',
     'contact.placement_id=(uint32_t)wd_read(&r,4)+1;', 'contact-view-placement-id-value'),
    ('contact-direction-offset', 'contact.length_direction=(int32_t)wd_read(&r,4);',
     'contact.length_direction=(int32_t)wd_read(&r,4)+1;', 'contact-view-direction-value'),
    ('contact-order-offset', 'contact.order=wd_read(&r,8);',
     'contact.order=wd_read(&r,8)+1;', 'contact-view-order-value'),
    ('contact-trailing', 'if(!r.ok||r.at!=r.size||actual!=id)return false;*out=contact;return true;',
     'if(!r.ok||actual!=id)return false;*out=contact;return true;', 'contact-view-trailing-rejected'),
    ('contact-text0-bound', 'wd_skip_text(&r,sizeof ((WoodMemberPlacement *)0)->ref_derived_key);',
     'wd_skip(&r,(size_t)wd_read(&r,4));', 'contact-view-text0-capacity'),
    ('contact-text1-bound', 'wd_skip_text(&r,sizeof ((WoodMemberReferenceFace *)0)->key);',
     'if(i==0){wd_skip(&r,(size_t)wd_read(&r,4));}else{wd_skip_text(&r,sizeof ((WoodMemberReferenceFace *)0)->key);}',
     'contact-view-text1-capacity'),
    ('contact-text2-bound', 'wd_skip_text(&r,sizeof ((WoodMemberReferenceFace *)0)->key);',
     'if(i==1){wd_skip(&r,(size_t)wd_read(&r,4));}else{wd_skip_text(&r,sizeof ((WoodMemberReferenceFace *)0)->key);}',
     'contact-view-text2-capacity'),
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

    def case(self, name, exe=None, *, control=None, phase=None):
        command = [str(exe or self.exe), name]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            if control is not None:
                def captured(value):
                    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''
                print(json.dumps({
                    'schema': 'geometry-definition-control-execution/1',
                    'control': control, 'phase': phase, 'command': command,
                    'exitCode': None, 'timedOut': True, 'timeoutSeconds': 30,
                    'stdout': captured(error.stdout), 'stderr': captured(error.stderr),
                }, ensure_ascii=False), flush=True)
            raise
        if control is not None:
            print(json.dumps({
                'schema': 'geometry-definition-control-execution/1',
                'control': control, 'phase': phase, 'command': command,
                'exitCode': result.returncode, 'timedOut': False,
                'stdout': result.stdout, 'stderr': result.stderr,
            }, ensure_ascii=False), flush=True)
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

    def test_contact_view_matches_full_cached_canonical_definition_and_format_rejections(self):
        result = self.case('contact-view')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('', result.stdout)
        self.assertEqual('', result.stderr)

    def test_contact_view_controls_fail_exact_offset_trailing_and_three_text_assertions(self):
        build = native()
        original = build.woodworking / 'definition_sources.c'
        baseline = original.read_bytes()
        text = baseline.decode('utf-8')
        for name, before, after, marker in CONTACT_VIEW_CONTROLS:
            with self.subTest(control=name):
                before_result = self.case('contact-view', control=name, phase='baseline')
                self.assertEqual(0, before_result.returncode, before_result.stdout + before_result.stderr)
                self.assertEqual(1, text.count(before), 'Control must hit once: ' + name)
                path = build.woodworking / ('definition-control-' + name + '.c')
                path.write_text(text.replace(before, after), encoding='utf-8')
                changed = build.compile(path, 'definition-control-' + name)
                exe = build.link('definition-control-' + name, self.objects(build, changed))
                result = self.case('contact-view', exe, control=name, phase='mutant')
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertRegex(result.stderr, r'^ASSERT:' + re.escape(marker) + r':\d+\n$')
                self.assertEqual('', result.stdout)
                self.assertEqual(baseline, original.read_bytes(), 'Control changed production bytes')
                restored = self.case('contact-view', control=name, phase='restored')
                self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)

    def test_five_negative_controls_fail_named_assertions(self):
        build = native()
        original = build.woodworking / 'definition_sources.c'
        baseline = original.read_bytes()
        text = baseline.decode('utf-8')
        for name, before, after, case, marker in CONTROLS:
            with self.subTest(control=name):
                self.assertEqual(0, self.case(case, control=name, phase='baseline').returncode)
                self.assertEqual(1, text.count(before))
                path = build.woodworking / ('definition-control-' + name + '.c')
                path.write_text(text.replace(before, after), encoding='utf-8')
                changed = build.compile(path, 'definition-control-' + name)
                exe = build.link('definition-control-' + name, self.objects(build, changed))
                result = self.case(case, exe, control=name, phase='mutant')
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn('ASSERT:' + marker + ':', result.stderr)
                self.assertEqual(baseline, original.read_bytes())
                self.assertEqual(0, self.case(case, control=name, phase='restored').returncode)


if __name__ == '__main__':
    unittest.main(verbosity=2)
