"""H owns complete candidate snapshots; isolated K sees explicit stores only.

The neutral harness links the actual H AppCandidate object with K candidate,
source and codec objects. Four negative controls relink changed H objects.
Only a normal harness assertion (exit 1) counts as detection, never a compiler
failure, process crash, timeout or unavailable tool.
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


class HostCandidateBoundary(unittest.TestCase):
    def test_host_coordinator_knows_only_public_kernel_and_opaque_snapshot_bytes(self):
        source = "\n".join((ROOT / "geometry-app/native" / name).read_text(encoding="utf-8")
                           for name in ("app_candidate.h", "app_candidate.c"))
        source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
        self.assertEqual(["candidate.h", "app_candidate.h", "codec.h"],
                         re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))
        self.assertNotRegex(source, r"\b(?:World|AppWorld|Timber|woodworking|reference_rebuild|world_revalidate)\b")


class NativeHostCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        # Keep the client outside the host directory and expose its public header only.
        shutil.copy2(build.host / "app_candidate.h", build.work / "app_candidate.h")
        source = build.work / "app-candidate-client.c"
        shutil.copy2(ROOT / "tests/geo261_app_candidate_harness.c", source)
        cls.client = build.compile(source, "app-candidate-client")
        cls.exe = build.link("app-candidate-client", [cls.client, build.host_candidate_object,
            build.candidate_object, build.source_object, build.codec_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a candidate verdict: " + result.stderr)
        return result.returncode

    def test_full_snapshot_copy_and_providers_stay_with_their_candidate(self):
        self.assertEqual(0, self.case("ownership"))

    def test_core_receives_only_explicit_nonoverlapping_ranges(self):
        self.assertEqual(0, self.case("bindings"))

    def test_failed_validation_never_changes_live_root(self):
        self.assertEqual(0, self.case("failed-evaluation"))

    def test_full_before_is_fixed_before_any_provider_runs(self):
        self.assertEqual(0, self.case("before-evaluation"))

    def test_template_and_host_before_changes_block_sealing(self):
        self.assertEqual(0, self.case("before-seal"))

    def test_successful_evaluation_freezes_template_and_host_after_before_seal(self):
        self.assertEqual(0, self.case("after-before-seal"))

    def test_sealed_full_before_blocks_check_and_publication(self):
        self.assertEqual(0, self.case("sealed-before"))

    def test_sealed_full_after_blocks_check_and_publication(self):
        self.assertEqual(0, self.case("sealed-after"))

    def test_live_equality_policy_can_preserve_presentation_only(self):
        self.assertEqual(0, self.case("live-policy"))

    def test_one_full_publication_reuses_resolver_and_never_reevaluates(self):
        self.assertEqual(0, self.case("publication"))

    def test_revision_stamp_and_actual_provider_changes_prevent_publication(self):
        self.assertEqual(0, self.case("revision-provider"))

    def test_owned_provider_state_is_disposed_once_before_its_resolver_dies(self):
        self.assertEqual(0, self.case("state-lifetime"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.host / "app_candidate.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must change exactly one H gate")
        path = build.work / ("app-candidate-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        changed = build.compile(path, "app-candidate-" + name)
        return build.link("app-candidate-" + name, [self.client, changed,
            build.candidate_object, build.source_object, build.codec_object])

    def control(self, name, case, before, after):
        self.assertEqual(0, self.case(case))
        self.assertEqual(1, self.case(case, self.mutant(name, before, after)))
        self.assertEqual(0, self.case(case))

    def test_before_evaluation_hash_negative_control_fails_normal_assertion(self):
        self.control("before-evaluation-gate", "before-evaluation",
            "if(candidate->sealed)return GEO_CANDIDATE_STATE;\n"
            "    if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash,candidate->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;",
            "if(candidate->sealed)return GEO_CANDIDATE_STATE;")

    def test_evaluated_after_hash_negative_control_fails_normal_assertion(self):
        self.control("evaluated-after-gate", "after-before-seal",
            "if(!app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;",
            "/* negative control: no evaluated full-after seal */")

    def test_full_snapshot_hash_negative_control_fails_normal_assertion(self):
        self.control("full-snapshot-gate", "sealed-after",
            "if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash)||\n"
            "       !app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;",
            "/* negative control: bound K stores alone cannot guard W/H bytes */")

    def test_live_equality_negative_control_fails_normal_assertion(self):
        self.control("live-equality-gate", "live-policy",
            "return equal(live,candidate->before,opaque)?GEO_CANDIDATE_OK:GEO_CANDIDATE_STATE_CHANGED;",
            "return GEO_CANDIDATE_OK;")


if __name__ == "__main__":
    unittest.main(verbosity=2)
