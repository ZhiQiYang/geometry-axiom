"""Explicit K-only deferred state digests retain all candidate verdicts.

All runtime assertions remain unchanged. The shared count of five SHA call
sites, two optional allocation sites and exact fallback pin are reused. The new
client links only isolated K candidate/source/codec objects; proxies execute
the real codec and preserve each input, pointer, size and resulting digest.
Resource faults and guard mutations affect only isolated local source copies.
Only exit 1 at the required named assertion is a negative-control detection.
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
from tests.test_geo261_native_kernel import kernel_only_native
from tests.test_geo261_candidate_cache import CACHE_GATE, SPECS, instrument, preamble, replace_once


FAULTS = (
    ("char *copy=malloc(length+1);", "char *copy=candidate_cache_test_alloc(length+1,4);"),
    ("GeoCandidate *candidate=calloc(1,sizeof *candidate);",
     "GeoCandidate *candidate=candidate_deferred_test_calloc(1,sizeof *candidate);"),
    ("GeoCandidateBinding *bindings=realloc(candidate->bindings,(candidate->binding_count+1)*sizeof *bindings);",
     "GeoCandidateBinding *bindings=candidate_deferred_test_realloc(candidate->bindings,(candidate->binding_count+1)*sizeof *bindings);"),
    ("unsigned char *bytes=malloc(size);", "unsigned char *bytes=candidate_cache_test_alloc(size,32);"),
    ("GeoEvalContext *sources=geo_eval_create(candidate->candidate_id,candidate->base_revision);",
     "GeoEvalContext *sources=candidate_deferred_test_sources(candidate->candidate_id,candidate->base_revision);"),
)
FAULT_PREAMBLE = ('#include "source.h"\n'
                  'void *candidate_deferred_test_calloc(size_t,size_t);\n'
                  'void *candidate_deferred_test_realloc(void *,size_t);\n'
                  'GeoEvalContext *candidate_deferred_test_sources(uint64_t,uint64_t);\n')
LEGACY_CASES = ("ownership", "bindings", "before-seal", "tampering", "revision",
                "provider-stamp", "providers", "revalidation", "failure-discard",
                "soft-edges", "source-seal")


def instrument_deferred(source: str) -> str:
    changed = instrument(source, "kernel")
    for before, after in FAULTS:
        changed = replace_once(changed, before, after)
    return FAULT_PREAMBLE + changed


class DeferredInstrumentation(unittest.TestCase):
    def test_local_fault_proxies_preserve_every_other_production_byte(self):
        original = (ROOT / SPECS["kernel"]["path"]).read_text(encoding="utf-8")
        changed = instrument_deferred(original)
        self.assertTrue(changed.startswith(FAULT_PREAMBLE + preamble("kernel")))
        restored = changed[len(FAULT_PREAMBLE + preamble("kernel")):]
        for before, after in reversed(FAULTS):
            restored = replace_once(restored, after, before)
        for before, after in SPECS["kernel"]["allocations"]:
            restored = replace_once(restored, after, before)
        restored = re.sub(r"\bcandidate_cache_test_kernel_sha\b", "geo_sha256", restored)
        self.assertEqual(original, restored)
        self.assertEqual(1, original.count(CACHE_GATE))
        self.assertEqual(1, original.count(SPECS["kernel"]["fallback"]))


class NativeDeferredCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = kernel_only_native()
        client = build.work / "candidate-deferred-client.c"
        shutil.copy2(ROOT / "tests/geo261_candidate_deferred_sha_harness.c", client)
        cls.client = build.compile(client, "candidate-deferred-client")
        cls.original = (build.kernel / "candidate.c").read_text(encoding="utf-8")
        cls.exe = cls.compile_candidate("candidate-deferred", cls.original)
        legacy = (ROOT / "tests/geo261_candidate_harness.c").read_text(encoding="utf-8")
        if legacy.count("geo_candidate_create(") != 4:
            raise AssertionError("Expected all four original constructor calls, including NULL/empty stamp checks; no legacy assertion may change")
        legacy = legacy.replace("geo_candidate_create(", "geo_candidate_create_deferred_sha(")
        legacy_path = build.work / "candidate-deferred-legacy-client.c"
        legacy_path.write_text(legacy, encoding="utf-8")
        legacy_object = build.compile(legacy_path, "candidate-deferred-legacy-client")
        cls.legacy = build.link("candidate-deferred-legacy", [legacy_object, build.candidate_object,
                                                            build.source_object, build.codec_object])

    @classmethod
    def compile_candidate(cls, name, source):
        build = kernel_only_native()
        path = build.work / (name + ".c")
        path.write_text(instrument_deferred(source), encoding="utf-8")
        candidate = build.compile(path, name)
        return build.link(name, [cls.client, candidate, build.source_object, build.codec_object])

    def run_case(self, name, mask=None, exe=None):
        command = [str(exe or self.exe), name]
        if mask is not None:
            command.append(str(mask))
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1),
                      "Crash/setup failure is not a deferred-cache verdict: " + result.stdout + result.stderr)
        return result

    def pass_case(self, name, mask=None):
        result = self.run_case(name, mask)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)
        self.assertEqual("", result.stderr)

    def test_existing_native_guards_use_opt_in_without_changing_assertions(self):
        for name in LEGACY_CASES:
            with self.subTest(case=name):
                result = self.run_case(name, exe=self.legacy)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual("", result.stdout)
                self.assertEqual("", result.stderr)

    def test_constructor_zero_bindings_and_required_resource_failures(self):
        for name in ("constructors", "resources"):
            with self.subTest(case=name):
                self.pass_case(name)

    def test_exact_hits_skip_only_state_sha_and_retain_provider_sha(self):
        for name in ("hit", "coexist"):
            with self.subTest(case=name):
                self.pass_case(name)

    def test_each_byte_and_preseal_miss_hash_saved_then_actual(self):
        for name in ("tamper", "unsealed"):
            with self.subTest(case=name):
                self.pass_case(name)

    def test_lifecycle_failed_evaluation_recovery_and_generation(self):
        for name in ("lifecycle", "failed", "state-edges"):
            with self.subTest(case=name):
                self.pass_case(name)

    def test_each_cache_oom_mixed_bindings_and_old_digest_recovery(self):
        for mask in (1, 2, 3):
            with self.subTest(failed_cache_mask=mask):
                self.pass_case("oom", mask)
        for name in ("mixed", "recovery"):
            with self.subTest(case=name):
                self.pass_case(name)

    def test_provider_metadata_and_first_error_priority(self):
        for name in ("provider", "priority"):
            with self.subTest(case=name):
                self.pass_case(name)

    def test_generation_limit_uses_existing_guard_with_accelerated_local_counter(self):
        # Only the local fixture counter advances early; overflow/state guards
        # stay byte-for-byte production code. This is not a mutation kill.
        boundary = replace_once(self.original, "++candidate->evaluation_generation;",
                                "candidate->evaluation_generation=UINT64_MAX;")
        exe = self.compile_candidate("candidate-deferred-generation-limit", boundary)
        result = self.run_case("generation-limit", exe=exe)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS generation-limit\n", result.stdout)
        self.assertEqual("", result.stderr)

    def control(self, name, case, before, after, label, mask=None):
        self.pass_case(case, mask)
        mutated = replace_once(self.original, before, after)
        exe = self.compile_candidate("candidate-deferred-control-" + name, mutated)
        result = self.run_case(case, mask, exe)
        self.assertEqual(1, result.returncode, "Control must fail a normal named assertion: " + result.stdout + result.stderr)
        self.assertEqual("", result.stdout)
        self.assertRegex(result.stderr, rf"^ASSERT:{re.escape(label)} line=\d+ expr=[^\n]+\n$")
        self.pass_case(case, mask)

    def test_real_guard_mutations_fail_named_assertions(self):
        controls = (
            ("ignore-byte-key", "tamper", CACHE_GATE, "if(hashed_bytes)return true;",
             "deferred-before-tamper-rejected", None),
            ("hash-actual-twice", "tamper", "geo_sha256(hashed_bytes,size,saved_expected);",
             "geo_sha256(bytes,size,saved_expected);", "deferred-before-tamper-rejected", None),
            ("skip-before-oom-sha", "oom", "if(!candidate->deferred_state_sha||!binding->before_bytes)",
             "if(!candidate->deferred_state_sha)", "before-oom-captured", 1),
            ("skip-current-oom-sha", "oom", "if(!candidate->deferred_state_sha||!binding->current_bytes)",
             "if(!candidate->deferred_state_sha)", "current-oom-captured", 2),
            ("retain-old-current-digest", "recovery", "else binding->current_hash[0]='\\0';",
             "else (void)0;", "old-oom-digest-cannot-authorize", None),
            ("retain-first-current-copy", "lifecycle",
             "if(binding->current_bytes)memcpy(binding->current_bytes,binding->current,binding->size);",
             "if(binding->current_bytes&&candidate->evaluation_generation==1)memcpy(binding->current_bytes,binding->current,binding->size);",
             "prior-round-cannot-seal", None),
            ("ignore-provider-metadata", "provider",
             "if(strcmp(hash,candidate->providers_hash))return GEO_CANDIDATE_PROVIDER_CHANGED;",
             "(void)hash;", "provider-token-tamper-rejected", None),
            ("ignore-revision", "priority",
             "if(live_revision!=candidate->base_revision)return GEO_CANDIDATE_REVISION_CHANGED;",
             "(void)live_revision;", "revision-precedes-stamp-and-bytes", None),
            ("ignore-stamp", "priority",
             "if(strcmp(provider_stamp,candidate->provider_stamp))return GEO_CANDIDATE_PROVIDER_CHANGED;",
             "(void)provider_stamp;", "stamp-precedes-bytes", None),
            ("accept-sha-fallback", "oom", SPECS["kernel"]["fallback"],
             "return true;", "oom-tamper-rejected", 3),
            ("skip-before-integrity", "unsealed",
             "if(!geo_candidate_digest_matches(binding->before,binding->size,binding->before_hash,binding->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;",
             "/* isolated negative control: omit before check */", "before-tamper-blocks-evaluator", None),
            ("skip-current-integrity", "unsealed",
             "if(!geo_candidate_digest_matches(binding->current,binding->size,binding->current_hash,binding->current_bytes))return GEO_CANDIDATE_STATE_CHANGED;",
             "/* isolated negative control: omit current check */", "current-tamper-blocks-seal", None),
        )
        for args in controls:
            with self.subTest(control=args[0]):
                self.control(*args)

    def test_eager_policy_control_preserves_api_but_fails_optimization_assertion(self):
        self.control("eager-policy", "hit", "if(candidate)candidate->deferred_state_sha=true;",
                     "if(candidate)candidate->deferred_state_sha=false;", "deferred-bind-skips-state-sha")


if __name__ == "__main__":
    unittest.main(verbosity=2)
