"""Exact byte-keyed K/H candidate SHA caches, including allocation fallback.

The shared NativeBuild supplies an isolated source closure. Local copies keep
the real candidate bodies and replace only SHA call names with counting proxies
(which call the real codec) and the four optional cache malloc expressions.
No production headers, implementation, unity include or build registry changes.

Every negative control must fail a named tamper-verdict assertion with exit 1.
Compilation errors, native crashes, timeouts and unavailable tools are never
accepted as detection. Static instrumentation checks need no native compiler.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native


SPECS = {
    "kernel": {
        "path": "geometry-core/kernel/candidate.c",
        "sha_calls": 5,
        "allocations": (
            ("binding->before_bytes=malloc(size);", "binding->before_bytes=candidate_cache_test_alloc(size,1);"),
            ("binding->current_bytes=malloc(binding->size);", "binding->current_bytes=candidate_cache_test_alloc(binding->size,2);"),
        ),
        "fallback": "return !strcmp(hash,expected);",
    },
    "host": {
        "path": "geometry-app/native/app_candidate.c",
        "sha_calls": 3,
        "allocations": (
            ("candidate->before_bytes=malloc(size);", "candidate->before_bytes=candidate_cache_test_alloc(size,4);"),
            ("candidate->after_bytes=malloc(candidate->snapshot_size);", "candidate->after_bytes=candidate_cache_test_alloc(candidate->snapshot_size,8);"),
        ),
        "fallback": "return !strcmp(actual,expected);",
    },
}
CACHE_GATE = "if(hashed_bytes&&!memcmp(bytes,hashed_bytes,size))return true;"


def replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise AssertionError("Instrumentation/control must hit exactly one expression: " + before)
    return source.replace(before, after)


def preamble(kind: str) -> str:
    return ("#include <stddef.h>\n"
            f"void candidate_cache_test_{kind}_sha(const void *,size_t,char [65]);\n"
            "void *candidate_cache_test_alloc(size_t,unsigned);\n")


def instrument(source: str, kind: str) -> str:
    spec = SPECS[kind]
    if len(re.findall(r"\bgeo_sha256\b", source)) != spec["sha_calls"]:
        raise AssertionError("Unexpected SHA call sites in " + kind)
    source = re.sub(r"\bgeo_sha256\b", f"candidate_cache_test_{kind}_sha", source)
    for before, after in spec["allocations"]:
        source = replace_once(source, before, after)
    return preamble(kind) + source


class CandidateCacheInstrumentation(unittest.TestCase):
    def test_local_instrumentation_preserves_every_other_production_byte(self):
        for kind, spec in SPECS.items():
            with self.subTest(layer=kind):
                original = (ROOT / spec["path"]).read_text(encoding="utf-8")
                changed = instrument(original, kind)
                self.assertTrue(changed.startswith(preamble(kind)))
                restored = changed[len(preamble(kind)):]
                for before, after in spec["allocations"]:
                    restored = replace_once(restored, after, before)
                restored = re.sub(rf"\bcandidate_cache_test_{kind}_sha\b", "geo_sha256", restored)
                self.assertEqual(original, restored)

    def test_each_negative_control_targets_one_real_byte_or_sha_guard(self):
        for kind, spec in SPECS.items():
            with self.subTest(layer=kind):
                source = instrument((ROOT / spec["path"]).read_text(encoding="utf-8"), kind)
                self.assertEqual(1, source.count(CACHE_GATE))
                self.assertEqual(1, source.count(spec["fallback"]))


class NativeCandidateCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        shutil.copy2(build.host / "app_candidate.h", build.work / "app_candidate.h")
        client = build.work / "candidate-cache-client.c"
        shutil.copy2(ROOT / "tests/geo261_candidate_cache_harness.c", client)
        cls.client = build.compile(client, "candidate-cache-client")
        cls.sources = {
            "kernel": instrument((build.kernel / "candidate.c").read_text(encoding="utf-8"), "kernel"),
            "host": instrument((build.host / "app_candidate.c").read_text(encoding="utf-8"), "host"),
        }
        cls.objects = {}
        for kind, source in cls.sources.items():
            name = "candidate-cache-" + kind
            path = build.work / (name + ".c")
            path.write_text(source, encoding="utf-8")
            cls.objects[kind] = build.compile(path, name)
        cls.exe = cls.link("candidate-cache-client", cls.objects)

    @classmethod
    def link(cls, name, objects):
        build = native()
        return build.link(name, [cls.client, objects["host"], objects["kernel"],
                                 build.source_object, build.codec_object])

    def run_case(self, name, mask=None, exe=None):
        command = [str(exe or self.exe), name]
        if mask is not None:
            command.append(str(mask))
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1),
                      "Native crash/setup failure is not a cache verdict: " + result.stdout + result.stderr)
        return result

    def pass_case(self, name, mask=None):
        result = self.run_case(name, mask)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_kernel_unchanged_before_and_current_reuse_exact_sha(self):
        self.pass_case("kernel-unchanged")

    def test_host_unchanged_full_snapshots_reuse_exact_sha(self):
        self.pass_case("host-unchanged")

    def test_kernel_every_byte_tamper_hashes_and_restoration_preserves_seal(self):
        self.pass_case("kernel-tampering")

    def test_host_every_byte_including_unbound_snapshot_tamper_is_rejected(self):
        self.pass_case("host-tampering")

    def test_kernel_unsealed_and_evaluated_tampering_still_uses_sha(self):
        self.pass_case("kernel-unsealed")

    def test_host_unsealed_and_evaluated_tampering_still_uses_sha(self):
        self.pass_case("host-unsealed")

    def test_kernel_repeated_evaluate_and_reopen_refreshes_current_cache(self):
        self.pass_case("kernel-lifecycle")

    def test_host_repeated_evaluate_and_reopen_refreshes_full_after_cache(self):
        self.pass_case("host-lifecycle")

    def test_kernel_each_or_both_cache_allocation_failures_preserve_verdicts(self):
        for mask in (1, 2, 3):
            with self.subTest(failed_cache_mask=mask):
                self.pass_case("kernel-fallback", mask)

    def test_host_each_cache_and_all_four_allocation_failures_preserve_verdicts(self):
        for mask in (1, 2, 4, 8, 12, 15):
            with self.subTest(failed_cache_mask=mask):
                self.pass_case("host-fallback", mask)

    def test_kernel_current_allocation_retries_without_replacing_before_seal(self):
        self.pass_case("kernel-retry")

    def test_host_current_allocation_retries_without_replacing_before_seal(self):
        self.pass_case("host-retry")

    def control(self, kind, mutation, case, before, after, mask=None):
        self.pass_case(case, mask)
        source = replace_once(self.sources[kind], before, after)
        build = native()
        name = "candidate-cache-" + kind + "-" + mutation
        path = build.work / (name + ".c")
        path.write_text(source, encoding="utf-8")
        objects = dict(self.objects)
        objects[kind] = build.compile(path, name)
        result = self.run_case(case, mask, self.link(name, objects))
        self.assertEqual(1, result.returncode, "Control did not fail a normal assertion: " + result.stdout + result.stderr)
        self.assertRegex(result.stderr, rf"^ASSERT:{kind}-tamper-rejected line=\d+ expr=check\(&fixture\)==GEO_CANDIDATE_STATE_CHANGED\n$")
        self.assertEqual("", result.stdout)
        self.pass_case(case, mask)

    def test_kernel_memcmp_bypass_is_caught_by_named_tamper_assertion(self):
        self.control("kernel", "skip-byte-key", "kernel-tampering", CACHE_GATE,
                     "if(hashed_bytes)return true;")

    def test_host_memcmp_bypass_is_caught_by_named_tamper_assertion(self):
        self.control("host", "skip-byte-key", "host-tampering", CACHE_GATE,
                     "if(hashed_bytes)return true;")

    def test_kernel_sha_fallback_acceptance_is_caught_after_allocation_failure(self):
        self.control("kernel", "accept-fallback", "kernel-fallback", SPECS["kernel"]["fallback"],
                     "return true;", 3)

    def test_host_sha_fallback_acceptance_is_caught_after_allocation_failure(self):
        self.control("host", "accept-fallback", "host-fallback", SPECS["host"]["fallback"],
                     "return true;", 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
