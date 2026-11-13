"""真 World factory 與真 preview/confirm 採用 HK deferred 的有限接線見證。

重用既有 product lifecycle 的全部斷言；真 K verdict 直接從同一候選讀取，
避免 H 完整 snapshot 守門掩蓋 K 負控。SHA/bind proxies 都轉呼原實作。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_candidate_cache import SPECS, replace_once
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_product import SCENE

DEFINES = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
           'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
HOST_PREFIX = ('#include "app_candidate.h"\n'
               'void hk_product_host_sha(const void *,size_t,char [65]);\n'
               'GeoCandidateStatus hk_product_bind(GeoCandidate *,const char *,const void *,void *,size_t);\n')
KERNEL_PREFIX = ('#include <stddef.h>\n'
                 'void hk_product_state_sha(const void *,size_t,char [65]);\n'
                 'void hk_product_provider_sha(const void *,size_t,char [65]);\n')
# The original product fixture previews spec x from 500 to 600. I8a reports
# that valid preview on stderr; accepting it must not hide any extra output.
PREVIEW_STDERR = (
    'I8a preview 1: valid; confirm token to apply\n'
    ' timber 1 center 20 -> 20 length 1000 -> 1000\n'
    '  surface 1 origin [0,0,0] axes [1,0,0]/[0,1,0]/[0,0,1] -> '
    'surface 1 origin [0,0,0] axes [1,0,0]/[0,1,0]/[0,0,1]\n'
    ' guide 1: surface 1 u=500 world [500,0,0] direction [0,1,0] -> '
    'surface 1 u=600 world [600,0,0] direction [0,1,0]\n'
    ' visible: {[500,0]-[500,1000]} -> {[600,0]-[600,1000]}\n'
)
EXPECTED_STDERR = {'factory': '', 'lifecycle': PREVIEW_STDERR, 'core-first': PREVIEW_STDERR}


def observe(source, kind):
    if len(re.findall(r'\bgeo_sha256\b', source)) != SPECS[kind]['sha_calls']:
        raise AssertionError('原 SHA 呼叫位置數改變：' + kind)
    if kind == 'host':
        source = re.sub(r'\bgeo_sha256\b', 'hk_product_host_sha', source)
        source = replace_once(source, 'return geo_candidate_bind_state(candidate->core,name,',
                              'return hk_product_bind(candidate->core,name,')
        return HOST_PREFIX + source
    source = re.sub(r'\bgeo_sha256\b', 'hk_product_state_sha', source)
    source = replace_once(source, 'hk_product_state_sha(bytes,size,out);free(bytes);return GEO_CANDIDATE_OK;',
                          'hk_product_provider_sha(bytes,size,out);free(bytes);return GEO_CANDIDATE_OK;')
    return KERNEL_PREFIX + source


# D observers enter the original bodies; provider faults touch only its one
# temporary metadata allocation. They never synthesize a candidate verdict.
D_OBSERVATIONS = {
    'host': ((
        '    if(!candidate||!live||!equal)return GEO_CANDIDATE_INVALID;',
        '    d_seen_host_check();\n    if(!candidate||!live||!equal)return GEO_CANDIDATE_INVALID;'),),
    'kernel': (
        ('    if(!candidate||!provider_stamp)return GEO_CANDIDATE_INVALID;',
         '    d_seen_kernel_check();\n    if(!candidate||!provider_stamp)return GEO_CANDIDATE_INVALID;'),
        ('unsigned char *bytes=malloc(size);', 'unsigned char *bytes=d_metadata_alloc(size);')),
    'source': (
        ('if(!provider->describe(provider->candidate_state,&node->source,&descriptor))',
         'if(!(d_seen_callback(),provider->describe(provider->candidate_state,&node->source,&descriptor)))'),
        ('node->described=provider->describe(provider->candidate_state,&node->source,&node->descriptor);',
         'node->described=(d_seen_callback(),provider->describe(provider->candidate_state,&node->source,&node->descriptor));'),
        ('bool ok=provider->evaluate(provider->candidate_state,ctx,&node->source,&value);',
         'bool ok=(d_seen_callback(),provider->evaluate(provider->candidate_state,ctx,&node->source,&value));')),
}
D_PREFIX = '#include <stddef.h>\nvoid d_seen_host_check(void);\nvoid d_seen_kernel_check(void);\nvoid d_seen_callback(void);\nvoid *d_metadata_alloc(size_t);\n'
D_SUFFIX = {
    'host': '',
    'kernel': '\nvoid d_flip_core_stamp(GeoCandidate *candidate){candidate->provider_stamp[0]^=1;}\n',
    'source': '\nvoid d_flip_source_seal(GeoEvalContext *sources){sources->sealed=!sources->sealed;}\n',
}
WORLD_PUBLISH_SIGNATURE = 'static bool app_world_candidate_publish(AppWorldCandidate *candidate,World *live,bool preserve_canvas)\n'
D_OPERATION_GUARD = '    if(strcmp(hash,candidate->operation_seal))return false;'
D_PUBLISH_PROLOGUE = ('    if(!candidate)return false;\n'
                      '    char hash[65];geo_sha256(&candidate->operation,sizeof candidate->operation,hash);\n'
                      + D_OPERATION_GUARD)
HOST_PUBLISH_GUARD = ('    if(!publish)return GEO_CANDIDATE_INVALID;\n'
                      '    GeoCandidateStatus status=app_candidate_check(candidate,live,revision,stamp,equal,opaque);')
DIRECT_CASES = (
    'direct-keep', 'direct-replace', 'direct-null',
    *('direct-' + name for name in ('operation-keyed', 'operation-id', 'operation-seal',
                                   'host-before', 'host-after', 'bound', 'live', 'revision',
                                   'provider', 'stamp', 'source-seal')),
    'direct-unsealed', 'direct-discarded', 'direct-reopened',
    'direct-oom1', 'direct-oom2', 'direct-oom-persistent',
)
EXPECTED_STDERR.update({case: PREVIEW_STDERR for case in (*DIRECT_CASES, 'direct-cost')})


def observe_d(source, kind):
    source = source if kind == 'source' else observe(source, kind)
    for before, after in D_OBSERVATIONS[kind]:
        source = replace_once(source, before, after)
    return D_PREFIX + source + D_SUFFIX[kind]


def actual_world_publish(source):
    if source.count(WORLD_PUBLISH_SIGNATURE) != 1:
        raise AssertionError('World publish 必須是唯一末尾函式')
    body = WORLD_PUBLISH_SIGNATURE + source.split(WORLD_PUBLISH_SIGNATURE, 1)[1]
    # This source ends in the function: fail closed if future trailing code
    # would silently enlarge the copied body. No implementation is retyped.
    if body.count('{') != 1 or body.count('}') != 1 or not body.endswith('}\n'):
        raise AssertionError('World publish 末尾邊界已改變')
    return body


class DeferredProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.scene = build.work / 'deferred-product.scene'
        cls.scene.write_text(SCENE, encoding='utf-8')
        # web_bridge.c itself defines/undefines main, so an outer #define main
        # cannot rename the old harness entry point. Change its one declaration.
        original_client = (ROOT / 'tests/geo261_candidate_product_harness.c').read_text(encoding='utf-8')
        original_client = replace_once(original_client, 'int main(int argc,char **argv)',
                                       'int original_candidate_product_main(int argc,char **argv)')
        original_client = replace_once(original_client, '#include "../geometry-web/web_bridge.c"',
                                       '#include "' + (ROOT / 'geometry-web/web_bridge.c').as_posix() + '"')
        client = (ROOT / 'tests/geo261_deferred_product_harness.c').read_text(encoding='utf-8')
        client = replace_once(client, '#include "geo261_candidate_product_harness.c"', original_client)
        cls.client_template = client
        cls.world_publish = actual_world_publish((ROOT / 'geometry-app/native/world_candidate.inc').read_text(encoding='utf-8'))
        cls.client = cls.compile_client('deferred-product-client', cls.world_publish)
        cls.original = {
            'host': (build.host / 'app_candidate.c').read_text(encoding='utf-8'),
            'kernel': (build.kernel / 'candidate.c').read_text(encoding='utf-8'),
            'source': (build.kernel / 'source.c').read_text(encoding='utf-8'),
        }
        cls.observed = {}
        for kind, source in cls.original.items():
            # Keep the H copy beside its public header; preserve the isolated includes.
            directory = build.host if kind == 'host' else build.kernel
            path = directory / ('deferred-product-' + kind + '.c')
            path.write_text(observe_d(source, kind), encoding='utf-8')
            cls.observed[kind] = build.compile(path, 'deferred-product-' + kind)
        cls.exe = cls.link('deferred-product', cls.observed)

    @classmethod
    def link(cls, name, observed, client=None):
        build = native()
        objects = build.product_objects()
        replacements = {build.host_candidate_object: observed['host'],
                        build.candidate_object: observed['kernel'],
                        build.source_object: observed['source']}
        if any(objects.count(old) != 1 for old in replacements):
            raise AssertionError('真產品閉包必須各連結一個 H/K candidate 及 source object')
        return build.link(name, [client or cls.client, *[replacements.get(obj, obj) for obj in objects]])

    def run_case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name, str(self.scene)],
                                capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), 'crash/setup failure 不是負控：' + result.stdout + result.stderr)
        return result

    def pass_case(self, name):
        result = self.run_case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(EXPECTED_STDERR[name], result.stderr)
        # 真 parser/preview 可能輸出原有 protocol 行，成功標記固定在最後。
        self.assertTrue(result.stdout.endswith('PASS ' + name + '\n'), result.stdout)

    def test_actual_factory_uses_deferred_snapshots_and_nine_exact_core_ranges(self):
        self.pass_case('factory')

    def test_real_preview_confirm_retains_all_original_lifecycle_assertions(self):
        self.pass_case('lifecycle')

    def test_actual_candidate_core_rejects_bound_byte_before_host_can_mask_it(self):
        self.pass_case('core-first')

    def test_actual_kernel_fallback_is_required_by_core_first_verdict(self):
        self.pass_case('core-first')
        build = native()
        changed = replace_once(self.original['kernel'], SPECS['kernel']['fallback'], 'return true;')
        path = build.kernel / 'deferred-product-kernel-accept-fallback.c'
        path.write_text(observe_d(changed, 'kernel'), encoding='utf-8')
        objects = dict(self.observed)
        objects['kernel'] = build.compile(path, 'deferred-product-kernel-accept-fallback')
        result = self.run_case('core-first', self.link('deferred-product-accept-fallback', objects))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(PREVIEW_STDERR + 'ASSERT:product-core-first-rejects-bound-byte\n', result.stderr)
        self.assertNotIn('PASS core-first\n', result.stdout)
        self.pass_case('core-first')


    @classmethod
    def compile_client(cls, name, world_publish):
        build = native()
        path = build.work / (name + '.c')
        path.write_text(replace_once(cls.client_template, '/* D_DIRECT_WORLD_PUBLISH */', world_publish), encoding='utf-8')
        return build.compile(path, name, DEFINES)

    def test_direct_world_observers_preserve_all_other_source_bytes(self):
        for kind, source in self.original.items():
            with self.subTest(kind=kind):
                observed = observe_d(source, kind)
                self.assertTrue(observed.startswith(D_PREFIX))
                restored = observed[len(D_PREFIX):]
                if D_SUFFIX[kind]:
                    self.assertTrue(restored.endswith(D_SUFFIX[kind]))
                    restored = restored[:-len(D_SUFFIX[kind])]
                for before, after in reversed(D_OBSERVATIONS[kind]):
                    restored = replace_once(restored, after, before)
                self.assertEqual(source if kind == 'source' else observe(source, kind), restored)
        world = (ROOT / 'geometry-app/native/world_candidate.inc').read_text(encoding='utf-8')
        self.assertTrue(world.endswith(self.world_publish))
        self.assertEqual(1, self.world_publish.count(D_PUBLISH_PROLOGUE))

    def test_direct_world_publish_has_one_host_two_kernel_and_two_metadata_checks(self):
        self.pass_case('direct-cost')

    def test_direct_world_guards_and_presentation_match_original_publish(self):
        # Restore only D; HK stays adopted. The same independent verdict cases
        # must pass through both real World function bodies.
        restored = replace_once(self.world_publish, D_PUBLISH_PROLOGUE,
                                '    if(!app_world_candidate_current(candidate,live))return false;')
        before_client = self.compile_client('direct-world-before-d', restored)
        before_exe = self.link('direct-world-before-d', self.observed, before_client)
        for case in DIRECT_CASES:
            with self.subTest(case=case):
                self.pass_case(case)
                result = self.run_case(case, before_exe)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(EXPECTED_STDERR[case], result.stderr)
                self.assertTrue(result.stdout.endswith('PASS ' + case + '\n'), result.stdout)

    def test_withdrawing_only_d_is_red_at_exact_direct_world_cost(self):
        self.pass_case('direct-cost')
        restored = replace_once(self.world_publish, D_PUBLISH_PROLOGUE,
                                '    if(!app_world_candidate_current(candidate,live))return false;')
        client = self.compile_client('direct-world-withdraw-d', restored)
        result = self.run_case('direct-cost', self.link('direct-world-withdraw-d', self.observed, client))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(PREVIEW_STDERR + 'ASSERT:publish-single-host-check\n', result.stderr)
        print('D_CONTROL_JSON ' + json.dumps({'assertion': 'publish-single-host-check', 'argv': result.args,
                                              'exit_code': result.returncode, 'stdout': result.stdout,
                                              'stderr': result.stderr}, ensure_ascii=False), flush=True)
        self.assertNotIn('PASS direct-cost\n', result.stdout)
        self.pass_case('direct-cost')

    def test_removing_world_operation_guard_is_red_at_direct_publish(self):
        case = 'direct-operation-keyed'
        self.pass_case(case)
        changed = replace_once(self.world_publish, D_OPERATION_GUARD, '    /* local control: operation guard removed */')
        client = self.compile_client('direct-world-no-operation-guard', changed)
        result = self.run_case(case, self.link('direct-world-no-operation-guard', self.observed, client))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(PREVIEW_STDERR + 'ASSERT:publish-operation-tamper-rejected\n', result.stderr)
        print('D_CONTROL_JSON ' + json.dumps({'assertion': 'publish-operation-tamper-rejected', 'argv': result.args,
                                              'exit_code': result.returncode, 'stdout': result.stdout,
                                              'stderr': result.stderr}, ensure_ascii=False), flush=True)
        self.assertNotIn('PASS ' + case + '\n', result.stdout)
        self.pass_case(case)

    def test_removing_host_publish_guard_is_red_for_unbound_after_byte(self):
        case = 'direct-host-after'
        self.pass_case(case)
        changed = replace_once(self.original['host'], HOST_PUBLISH_GUARD,
                               '    if(!publish)return GEO_CANDIDATE_INVALID;\n'
                               '    GeoCandidateStatus status=GEO_CANDIDATE_OK;')
        build = native()
        path = build.host / 'direct-world-no-host-publish-guard.c'
        path.write_text(observe_d(changed, 'host'), encoding='utf-8')
        observed = dict(self.observed)
        observed['host'] = build.compile(path, 'direct-world-no-host-publish-guard')
        result = self.run_case(case, self.link('direct-world-no-host-publish-guard', observed))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(PREVIEW_STDERR + 'ASSERT:publish-host-after-tamper-rejected\n', result.stderr)
        print('D_CONTROL_JSON ' + json.dumps({'assertion': 'publish-host-after-tamper-rejected', 'argv': result.args,
                                              'exit_code': result.returncode, 'stdout': result.stdout,
                                              'stderr': result.stderr}, ensure_ascii=False), flush=True)
        self.assertNotIn('PASS ' + case + '\n', result.stdout)
        self.pass_case(case)


if __name__ == '__main__':
    unittest.main(verbosity=2)
