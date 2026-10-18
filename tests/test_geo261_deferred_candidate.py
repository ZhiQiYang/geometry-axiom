"""單一 H opt-in 同時選 H/K deferred：真物件、獨立 SHA oracle 與精確負控。

不修改既有 eager suite、counts 或 instrumentation spec。只改隔離副本的
SHA 呼叫名稱、既有四個 optional caches、constructor 與 provider metadata 配置。
負控逐一指定第一個正常 ASSERT；編譯失敗、crash、timeout、skip 均非 killed。
四格來源使用同一個 client／API／功能期望；成本斷言獨立，不能放寬成任意失敗。
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_candidate_cache import CACHE_GATE, SPECS, instrument, preamble, replace_once
from tests.test_geo261_native_kernel import native

EXPECTED_METHODS = 52
EXTRA_PREAMBLE = "void *candidate_deferred_test_calloc(size_t,size_t,unsigned);\n"
CONSTRUCTOR_ALLOCATIONS = {
    "host": (("AppCandidate *candidate=calloc(1,sizeof *candidate);",
              "AppCandidate *candidate=candidate_deferred_test_calloc(1,sizeof *candidate,16);"),),
    "kernel": (("GeoCandidate *candidate=calloc(1,sizeof *candidate);",
                "GeoCandidate *candidate=candidate_deferred_test_calloc(1,sizeof *candidate,32);"),
               ("char *copy=malloc(length+1);",
                "char *copy=candidate_cache_test_alloc(length+1,64);"),
               ("unsigned char *bytes=malloc(size);",
                "unsigned char *bytes=candidate_cache_test_alloc(size,128);")),
}
CAPTURE_AFTER = (
    "app_candidate_capture_snapshot(candidate->after,candidate->snapshot_size,candidate->after_hash,\n"
    "            candidate->after_bytes,candidate->deferred_snapshot_sha);"
)
BEFORE_EVALUATE = (
    "if(candidate->sealed)return GEO_CANDIDATE_STATE;\n"
    "    if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash,candidate->before_bytes))return GEO_CANDIDATE_STATE_CHANGED;"
)
AFTER_SEAL = "if(!app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;"
FULL_CHECK = (
    "if(!app_candidate_hash_matches(candidate->before,candidate->snapshot_size,candidate->before_hash,candidate->before_bytes)||\n"
    "       !app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;"
)


def instrument_deferred(source: str, kind: str) -> str:
    # 原 spec 先檢查真正 SHA callsites 與 optional-cache anchors，沒有放寬。
    result = instrument(source, kind)
    for before, after in CONSTRUCTOR_ALLOCATIONS[kind]:
        result = replace_once(result, before, after)
    return result.replace(preamble(kind), preamble(kind) + EXTRA_PREAMBLE, 1)


# 每項都是 instrument 後的真 H source 上唯一錨點。值為：
# (case, mask, before, after, first normal ASSERT label)。
CONTROLS = {
    "saved-as-actual": (
        "before-check", None,
        "candidate_cache_test_host_sha(hashed_bytes,size,saved_expected);",
        "candidate_cache_test_host_sha(bytes,size,saved_expected);",
        "deferred-before-tamper-rejected"),
    "actual-as-saved": (
        "after-check", None,
        "candidate_cache_test_host_sha(bytes,size,actual);",
        "candidate_cache_test_host_sha(hashed_bytes?hashed_bytes:bytes,size,actual);",
        "deferred-after-tamper-rejected"),
    "skip-byte-key": (
        "before-check", None, CACHE_GATE, "if(hashed_bytes)return true;",
        "deferred-before-tamper-rejected"),
    "accept-pending-fallback": (
        "after-check", None, SPECS["host"]["fallback"], "return true;",
        "deferred-after-tamper-rejected"),
    "truncate-both-digests": (
        "last-byte", None, "char saved_expected[65];", "char saved_expected[65];--size;",
        "deferred-after-tamper-rejected"),
    "overwrite-saved-on-miss": (
        "before-check", None, "char saved_expected[65];",
        "if(hashed_bytes)memcpy((void*)hashed_bytes,bytes,size);char saved_expected[65];",
        "deferred-before-tamper-rejected"),
    "skip-after-capture": (
        "lifecycle", None, CAPTURE_AFTER,
        "if(candidate->after_bytes)candidate->after_hash[0]='\\0';",
        "lifecycle-current-valid-seal"),
    "keep-oom-digest-after-retry": (
        "retry", 8, "if(deferred&&saved){expected[0]='\\0';return;}",
        "if(deferred&&saved)return;", "retry-old-after-rejected"),
    "omit-before-oom-digest": (
        "oom", 4, "candidate_cache_test_host_sha(bytes,size,expected);",
        "if(saved)candidate_cache_test_host_sha(bytes,size,expected);",
        "deferred-oom-valid-evaluation"),
    "omit-after-oom-digest": (
        "oom", 8, "candidate_cache_test_host_sha(bytes,size,expected);",
        "if(saved)candidate_cache_test_host_sha(bytes,size,expected);",
        "deferred-oom-valid-seal"),
    "capture-failed-evaluation": (
        "failed-later", None, "if(status==GEO_CANDIDATE_OK){",
        "if(status==GEO_CANDIDATE_OK||status==GEO_CANDIDATE_EVALUATION_FAILED){",
        "failed-after-rejected-by-h"),
    "skip-before-evaluate": (
        "before-evaluate", None, BEFORE_EVALUATE,
        "if(candidate->sealed)return GEO_CANDIDATE_STATE;",
        "deferred-before-evaluator-rejected"),
    "skip-after-seal": (
        "after-seal", None, AFTER_SEAL, "/* 負控：略過已求值的 H after 守門。 */",
        "deferred-evaluated-after-rejected"),
    "skip-full-check": (
        "after-check", None, FULL_CHECK, "/* 負控：略過完整 H snapshot 守門。 */",
        "deferred-after-tamper-rejected"),
    "accept-oom-fallback": (
        "oom", 12, SPECS["host"]["fallback"], "return true;",
        "deferred-oom-tamper-rejected"),
    "write-back-pending-digest": (
        "before-check", None, "expected=saved_expected;",
        "memcpy((char*)expected,saved_expected,65);expected=saved_expected;",
        "tamper-publication-hashes-original-pair"),
    "old-constructor-selects-deferred": (
        "eager-create", None,
        "return app_candidate_create_with_deferred_sha(before,after,live,size,id,revision,stamp,false);",
        "return app_candidate_create_with_deferred_sha(before,after,live,size,id,revision,stamp,true);",
        "eager-create-real-sha"),
    "withdraw-new-constructor-policy": (
        "create", None,
        "return app_candidate_create_with_deferred_sha(before,after,live,size,id,revision,stamp,true);",
        "return app_candidate_create_with_deferred_sha(before,after,live,size,id,revision,stamp,false);",
        "deferred-create-no-sha"),
    "withdraw-host-policy": (
        "create", None, "candidate->deferred_snapshot_sha=deferred;",
        "candidate->deferred_snapshot_sha=false;", "deferred-create-no-sha"),
    "withdraw-kernel-selection": (
        "bind", None, "candidate->core=geo_candidate_create_deferred_sha(id,revision,stamp);",
        "candidate->core=geo_candidate_create(id,revision,stamp);", "deferred-bind-skips-state-sha"),
}
KERNEL_CONTROLS = {
    "accept-bound-state-fallback": (
        "bound-tamper", None, SPECS["kernel"]["fallback"], "return true;",
        "kernel-before-tamper-rejected"),
}
POLICY_CONTROLS = {"10": "withdraw-kernel-selection", "01": "withdraw-host-policy",
                   "00": "withdraw-new-constructor-policy"}


class DeferredCandidateInstrumentation(unittest.TestCase):
    def test_instrumentation_roundtrip_preserves_every_other_byte(self):
        for kind, spec in SPECS.items():
            with self.subTest(layer=kind):
                original = (ROOT / spec["path"]).read_text(encoding="utf-8")
                changed = instrument_deferred(original, kind)
                prefix = preamble(kind) + EXTRA_PREAMBLE
                self.assertTrue(changed.startswith(prefix))
                restored = changed[len(prefix):]
                for before, after in CONSTRUCTOR_ALLOCATIONS[kind]:
                    restored = replace_once(restored, after, before)
                for before, after in spec["allocations"]:
                    restored = replace_once(restored, after, before)
                restored = re.sub(rf"\bcandidate_cache_test_{kind}_sha\b", "geo_sha256", restored)
                self.assertEqual(original, restored)

    def test_each_control_changes_one_live_anchor(self):
        for kind, controls in (("host", CONTROLS), ("kernel", KERNEL_CONTROLS)):
            source = instrument_deferred((ROOT / SPECS[kind]["path"]).read_text(encoding="utf-8"), kind)
            for name, (_, _, before, after, marker) in controls.items():
                with self.subTest(layer=kind, control=name):
                    self.assertEqual(1, source.count(before))
                    self.assertNotEqual(before, after)
                    self.assertRegex(marker, r"^[a-z][a-z-]+$")
                    self.assertNotEqual(source, replace_once(source, before, after))

    def test_suite_census_and_control_methods_are_explicit(self):
        loader = unittest.TestLoader()
        names = loader.getTestCaseNames(DeferredCandidateInstrumentation) + loader.getTestCaseNames(NativeDeferredCandidate)
        self.assertEqual(EXPECTED_METHODS, len(names))
        self.assertEqual(20, len(CONTROLS))
        self.assertEqual(1, len(KERNEL_CONTROLS))
        self.assertEqual(21, sum(name.startswith("test_control_") for name in names))


class NativeDeferredCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        shutil.copy2(build.host / "app_candidate.h", build.work / "app_candidate.h")
        client = build.work / "deferred-candidate-client.c"
        shutil.copy2(ROOT / "tests/geo261_deferred_candidate_harness.c", client)
        cls.client = build.compile(client, "deferred-candidate-client")
        cls.sources = {
            "host": instrument_deferred((build.host / "app_candidate.c").read_text(encoding="utf-8"), "host"),
            "kernel": instrument_deferred((build.kernel / "candidate.c").read_text(encoding="utf-8"), "kernel"),
        }
        cls.objects = {}
        for kind, source in cls.sources.items():
            path = build.work / ("deferred-candidate-" + kind + ".c")
            path.write_text(source, encoding="utf-8")
            cls.objects[kind] = build.compile(path, "deferred-candidate-" + kind)
        cls.exe = cls.link("deferred-candidate-client", cls.objects)

    @classmethod
    def link(cls, name, objects):
        build = native()
        return build.link(name, [cls.client, objects["host"], objects["kernel"], build.source_object, build.codec_object])

    def run_case(self, case, mask=None, exe=None):
        command = [str(exe or self.exe), case]
        if mask is not None:
            command.append(str(mask))
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "crash/setup failure 不是候選判決：" + result.stdout + result.stderr)
        return result

    def pass_case(self, case, mask=None, exe=None):
        result = self.run_case(case, mask, exe)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)
        lines = result.stdout.splitlines()
        self.assertTrue(lines)
        self.assertEqual("PASS " + case, lines[-1])
        for index, line in enumerate(lines[:-1]):
            match = re.fullmatch(r"SHA ([HK]) (\d+) ([0-9a-f]*) ([0-9a-f]{64})", line)
            self.assertIsNotNone(match, "不合法 SHA 收據：" + line)
            layer, length, encoded, actual = match.groups()
            data = bytes.fromhex(encoded)
            if layer == "H":
                self.assertEqual(96, int(length), f"record {index} 必須保護完整 snapshot")
            else:
                self.assertIn(int(length), (16, 32, 68), f"record {index} 必須是確切 K range 或 provider metadata")
            self.assertEqual(int(length), len(data))
            self.assertEqual(hashlib.sha256(data).hexdigest(), actual, f"record {index} 的獨立 SHA oracle")
        self.assertTrue(result.stdout.endswith("\n"))

    def changed_object(self, name, kind, before, after):
        build = native()
        path = build.work / ("deferred-control-" + name + ".c")
        path.write_text(replace_once(self.sources[kind], before, after), encoding="utf-8")
        objects = dict(self.objects)
        objects[kind] = build.compile(path, "deferred-control-" + name)
        return self.link("deferred-control-" + name, objects)

    def control(self, name, kind="host"):
        case, mask, before, after, marker = (CONTROLS if kind == "host" else KERNEL_CONTROLS)[name]
        self.pass_case(case, mask)
        result = self.run_case(case, mask, self.changed_object(name, kind, before, after))
        self.assertEqual(1, result.returncode, "負控未正常失敗：" + result.stdout + result.stderr)
        self.assertRegex(result.stderr, rf"\AASSERT:{re.escape(marker)} line=\d+ expr=[^\n]+\n\Z")
        self.assertEqual("", result.stdout)
        self.pass_case(case, mask)

    def test_default_constructor_keeps_real_eager_calls(self):
        self.pass_case("eager")

    def test_deferred_normal_path_skips_both_state_sha_and_keeps_provider_sha(self):
        self.pass_case("normal")

    def test_every_host_only_before_byte_mirrors_live_and_rejects_two_misses(self):
        self.pass_case("before-check")

    def test_every_host_only_after_byte_rejects_two_misses_and_publication(self):
        self.pass_case("after-check")

    def test_last_snapshot_byte_is_in_both_real_sha_inputs(self):
        self.pass_case("last-byte")

    def test_every_host_only_before_byte_blocks_evaluator(self):
        self.pass_case("before-evaluate")

    def test_every_host_only_after_byte_blocks_seal(self):
        self.pass_case("after-seal")

    def test_before_modified_inside_evaluator_still_blocks_seal(self):
        self.pass_case("callback-before")

    def test_unevaluated_candidate_has_no_pending_after_or_null_sha(self):
        self.pass_case("unevaluated")

    def test_first_failed_evaluation_cannot_create_after_seal(self):
        self.pass_case("failed-first")

    def test_failed_evaluation_preserves_last_successful_saved_bytes(self):
        self.pass_case("failed-later")

    def test_reopen_and_repeated_host_only_evaluation_refresh_current_baseline(self):
        self.pass_case("lifecycle")

    def test_host_and_mixed_kernel_oom_preserve_immediate_hashes_and_verdicts(self):
        for mask in range(16):
            with self.subTest(failed_cache_mask=mask):
                self.pass_case("oom", mask)

    def test_after_oom_retry_clears_old_digest_without_retrying_before(self):
        for mask in (8, 12, 15):
            with self.subTest(failed_cache_mask=mask):
                self.pass_case("retry", mask)

    def test_publication_writes_complete_root_once_without_reevaluation(self):
        self.pass_case("publication")

    def test_presentation_only_live_equality_policy_remains_valid(self):
        self.pass_case("presentation")

    def test_discard_is_terminal_and_disposes_state_once(self):
        self.pass_case("discard")

    def test_new_constructor_keeps_invalid_range_overlap_and_stamp_guards(self):
        self.pass_case("invalid")

    def test_host_handle_core_handle_and_stamp_allocation_failures_are_atomic(self):
        for mask in (16, 32, 64):
            with self.subTest(failed_constructor_allocation=mask):
                self.pass_case("constructor-oom", mask)

    def test_two_candidates_cannot_use_each_others_saved_bytes(self):
        self.pass_case("isolation")

    def test_revision_provider_and_live_guards_keep_existing_order(self):
        self.pass_case("guard-priority")

    def test_create_and_bind_cost_assertions_are_separate(self):
        for case in ("create", "eager-create", "bind"):
            with self.subTest(case=case):
                self.pass_case(case)

    def test_every_bound_byte_uses_direct_kernel_verdict_before_host_guards(self):
        self.pass_case("bound-tamper")

    def test_each_current_cache_and_both_recover_without_stale_digest_authority(self):
        for mask in (2, 8, 10):
            with self.subTest(failed_cache_mask=mask):
                self.pass_case("cross-recovery", mask)

    def test_eager_and_deferred_handles_coexist_with_independent_policies(self):
        self.pass_case("coexist")

    def test_two_disjoint_bindings_hash_only_each_changed_range(self):
        self.pass_case("split-ranges")

    def test_provider_metadata_oom_preserves_unpublished_owner_and_seal(self):
        self.pass_case("metadata-oom")

    def test_same_client_preserves_correctness_for_all_four_fixed_policies(self):
        self.pass_case("policy-correctness")
        for mode, control in POLICY_CONTROLS.items():
            with self.subTest(policy=mode):
                _, _, before, after, _ = CONTROLS[control]
                exe = self.changed_object("correctness-" + mode, "host", before, after)
                self.pass_case("policy-correctness", exe=exe)
        self.pass_case("policy-correctness")

    def test_control_expected_cannot_hash_actual_instead_of_saved(self):
        self.control("saved-as-actual")

    def test_control_actual_cannot_hash_saved_instead_of_actual(self):
        self.control("actual-as-saved")

    def test_control_byte_key_must_compare_content(self):
        self.control("skip-byte-key")

    def test_control_pending_fallback_must_compare_real_digests(self):
        self.control("accept-pending-fallback")

    def test_control_both_digests_must_cover_last_byte(self):
        self.control("truncate-both-digests")

    def test_control_miss_must_not_replace_saved_authority(self):
        self.control("overwrite-saved-on-miss")

    def test_control_success_must_capture_after_bytes(self):
        self.control("skip-after-capture")

    def test_control_retry_must_clear_old_oom_digest(self):
        self.control("keep-oom-digest-after-retry")

    def test_control_before_oom_must_materialize_expected_immediately(self):
        self.control("omit-before-oom-digest")

    def test_control_after_oom_must_materialize_expected_immediately(self):
        self.control("omit-after-oom-digest")

    def test_control_failed_evaluation_must_not_capture_after(self):
        self.control("capture-failed-evaluation")

    def test_control_before_guard_precedes_evaluator(self):
        self.control("skip-before-evaluate")

    def test_control_after_guard_precedes_seal(self):
        self.control("skip-after-seal")

    def test_control_check_protects_complete_host_snapshot(self):
        self.control("skip-full-check")

    def test_control_oom_fallback_must_reject_tampering(self):
        self.control("accept-oom-fallback")

    def test_control_const_check_does_not_materialize_candidate_digest(self):
        self.control("write-back-pending-digest")

    def test_control_old_constructor_cannot_opt_in_implicitly(self):
        self.control("old-constructor-selects-deferred")

    def test_control_withdrawing_new_constructor_policy_restores_real_sha_cost(self):
        self.control("withdraw-new-constructor-policy")

    def test_control_withdrawing_only_host_policy_fails_before_binding(self):
        self.control("withdraw-host-policy")

    def test_control_withdrawing_only_kernel_selection_fails_at_binding(self):
        self.control("withdraw-kernel-selection")

    def test_control_kernel_fallback_cannot_hide_behind_host_rejection(self):
        self.control("accept-bound-state-fallback", kind="kernel")


if __name__ == "__main__":
    unittest.main(verbosity=2)
