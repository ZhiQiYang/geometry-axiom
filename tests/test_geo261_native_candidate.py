"""Candidate lifecycle uses only isolated K source, codec and candidate objects.

The host owns complete publication and the before/current buffers. These tests
exercise the authorization boundary without linking any host or template code.
Negative controls remove real checks; only a normal harness assertion (exit 1)
counts as detection, never a build error, unavailable tool or native crash.
"""
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


class CandidateBoundary(unittest.TestCase):
    def test_candidate_has_only_public_neutral_dependencies(self):
        source = "\n".join((ROOT / "geometry-core/kernel" / name).read_text(encoding="utf-8")
                           for name in ("candidate.h", "candidate.c"))
        source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertEqual(["source.h", "candidate.h", "codec.h"],
                         re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))
        self.assertNotRegex(source, r"\b(?:World|AppWorld|Timber|woodworking|reference_rebuild|world_revalidate)\b")


class NativeCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.work / "candidate-client.c"
        shutil.copy2(ROOT / "tests/geo261_candidate_harness.c", source)
        cls.client = build.compile(source, "candidate-client")
        cls.exe = build.link("candidate-client", [cls.client, build.candidate_object,
                                                 build.source_object, build.codec_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a candidate verdict: " + result.stderr)
        return result.returncode

    def test_stamp_copy_candidate_isolation_and_callback_copy_binding(self):
        self.assertEqual(0, self.case("ownership"))

    def test_named_bindings_reject_aliases_and_pointer_or_size_overflow(self):
        self.assertEqual(0, self.case("bindings"))

    def test_bind_time_before_hash_and_successful_evaluation_bytes_are_fixed(self):
        self.assertEqual(0, self.case("before-seal"))

    def test_all_bound_bytes_are_rechecked_at_publication_without_copying(self):
        self.assertEqual(0, self.case("tampering"))

    def test_revision_change_blocks_check_reopen_and_publication(self):
        self.assertEqual(0, self.case("revision"))

    def test_provider_stamp_is_exact_even_beyond_short_digest_buffers(self):
        self.assertEqual(0, self.case("provider-stamp"))

    def test_actual_provider_tokens_names_and_fingerprints_are_frozen(self):
        self.assertEqual(0, self.case("providers"))

    def test_revalidation_uses_fresh_resolver_and_preserves_identity_and_bindings(self):
        self.assertEqual(0, self.case("revalidation"))

    def test_failed_or_discarded_candidates_never_authorize_publication(self):
        self.assertEqual(0, self.case("failure-discard"))

    def test_soft_ordering_failures_and_definition_only_nodes_do_not_globally_reject(self):
        self.assertEqual(0, self.case("soft-edges"))

    def test_sealed_resolver_cannot_add_providers_nodes_or_edges(self):
        self.assertEqual(0, self.case("source-seal"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.kernel / "candidate.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one gate")
        path = build.work / ("candidate-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "candidate-" + name)
        return build.link("candidate-" + name, [self.client, changed, build.source_object, build.codec_object])

    def control(self, name, case, before, after):
        self.assertEqual(0, self.case(case))
        self.assertEqual(1, self.case(case, self.mutant(name, before, after)))
        self.assertEqual(0, self.case(case))

    def test_revision_gate_negative_control_fails_normal_assertion(self):
        self.control("revision-gate", "revision",
                     "if(live_revision!=candidate->base_revision)return GEO_CANDIDATE_REVISION_CHANGED;", "(void)live_revision;")

    def test_stamp_gate_negative_control_fails_normal_assertion(self):
        self.control("stamp-gate", "provider-stamp",
                     "if(strcmp(provider_stamp,candidate->provider_stamp))return GEO_CANDIDATE_PROVIDER_CHANGED;", "(void)provider_stamp;")

    def test_before_integrity_gate_negative_control_fails_normal_assertion(self):
        self.control("before-gate", "before-seal",
                     "if(!geo_candidate_digest_matches(binding->before,binding->size,binding->before_hash,binding->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;", "/* negative control: omit integrity gate */")

    def test_current_integrity_gate_negative_control_fails_normal_assertion(self):
        self.control("current-gate", "tampering",
                     "if(!geo_candidate_digest_matches(binding->current,binding->size,binding->current_hash,binding->current_bytes))return GEO_CANDIDATE_STATE_CHANGED;", "/* negative control: omit integrity gate */")

    def test_actual_provider_gate_negative_control_fails_normal_assertion(self):
        self.control("provider-gate", "providers",
                     "if(strcmp(hash,candidate->providers_hash))return GEO_CANDIDATE_PROVIDER_CHANGED;", "/* negative control: omit integrity gate */")


if __name__ == "__main__":
    unittest.main(verbosity=2)
