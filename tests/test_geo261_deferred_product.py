"""真 World factory 與真 preview/confirm 採用 HK deferred 的有限接線見證。

重用既有 product lifecycle 的全部斷言；真 K verdict 直接從同一候選讀取，
避免 H 完整 snapshot 守門掩蓋 K 負控。SHA/bind proxies 都轉呼原實作。
"""
from __future__ import annotations

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
        client_path = build.work / 'deferred-product-client.c'
        client_path.write_text(client, encoding='utf-8')
        cls.client = build.compile(client_path, 'deferred-product-client', DEFINES)
        cls.original = {
            'host': (build.host / 'app_candidate.c').read_text(encoding='utf-8'),
            'kernel': (build.kernel / 'candidate.c').read_text(encoding='utf-8'),
        }
        cls.observed = {}
        for kind, source in cls.original.items():
            # Keep the H copy beside its public header; preserve the isolated includes.
            directory = build.host if kind == 'host' else build.kernel
            path = directory / ('deferred-product-' + kind + '.c')
            path.write_text(observe(source, kind), encoding='utf-8')
            cls.observed[kind] = build.compile(path, 'deferred-product-' + kind)
        cls.exe = cls.link('deferred-product', cls.observed)

    @classmethod
    def link(cls, name, observed):
        build = native()
        objects = build.product_objects()
        replacements = {build.host_candidate_object: observed['host'],
                        build.candidate_object: observed['kernel']}
        if any(objects.count(old) != 1 for old in replacements):
            raise AssertionError('真產品閉包必須各連結一個 H/K candidate object')
        return build.link(name, [cls.client, *[replacements.get(obj, obj) for obj in objects]])

    def run_case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name, str(self.scene)],
                                capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), 'crash/setup failure 不是負控：' + result.stdout + result.stderr)
        return result

    def pass_case(self, name):
        result = self.run_case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('', result.stderr)
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
        path.write_text(observe(changed, 'kernel'), encoding='utf-8')
        objects = dict(self.observed)
        objects['kernel'] = build.compile(path, 'deferred-product-kernel-accept-fallback')
        result = self.run_case('core-first', self.link('deferred-product-accept-fallback', objects))
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual('ASSERT:product-core-first-rejects-bound-byte\n', result.stderr)
        self.assertNotIn('PASS core-first\n', result.stdout)
        self.pass_case('core-first')


if __name__ == '__main__':
    unittest.main(verbosity=2)
