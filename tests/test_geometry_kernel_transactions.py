"""Candidate ownership, cancellation, freshness and atomic copied replacement."""
from copy import copy, deepcopy
import importlib.util
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock

if importlib.util.find_spec("geometry_kernel") is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))

from geometry_kernel import transactions
from geometry_kernel.transactions import CandidateCell, CandidateError


STAMP = ("evaluator", ("module.py", "content-hash"), ("adapter", 3), None)
CHANGED_STAMP = ("evaluator", ("module.py", "different-hash"), ("adapter", 3), None)


class CopyFailure:
    def __deepcopy__(self, memo):
        raise RuntimeError("copy failed")


class CopyHook:
    """Test a callback between validation and the final state replacement."""
    def __init__(self, hook):
        self.hook = hook

    def __deepcopy__(self, memo):
        self.hook()
        return {"copied": True}


class CandidateCellTests(unittest.TestCase):
    def sealed(self, cell, value=None, stamp=STAMP, digest="candidate-content"):
        return cell.seal_preview(cell.begin_preview(), {"next": [2]} if value is None else value,
                                 digest, stamp)

    def assert_code(self, code, operation, error_type=CandidateError):
        with self.assertRaises(error_type) as caught:
            operation()
        self.assertEqual(code, caught.exception.code)
        self.assertEqual("INVALID", caught.exception.status)

    def test_initial_and_returned_values_are_copies(self):
        original = {"items": [[1]]}
        cell = CandidateCell(original)
        original["items"][0].append(2)
        view = cell.value
        view["items"].clear()
        self.assertEqual({"items": [[1]]}, cell.value)
        self.assertEqual((0, 0), (cell.revision, cell.generation))

    def test_preview_and_claim_are_copies_and_do_not_commit(self):
        cell = CandidateCell({"old": [1]})
        candidate = {"next": [2]}
        token = self.sealed(cell, candidate)
        candidate["next"].append(99)
        receipt, claimed = cell.claim(token, STAMP)
        self.assertEqual({"next": [2]}, claimed)
        claimed["next"].append(3)
        self.assertEqual({"old": [1]}, cell.value)
        self.assertEqual(0, cell.revision)
        self.assertIsNotNone(receipt)

    def test_commit_uses_verified_value_and_copies_input_and_result(self):
        cell = CandidateCell({"old": [1]})
        receipt, candidate = cell.claim(self.sealed(cell), STAMP)
        candidate["verified"] = [True]
        result = cell.commit(receipt, candidate, STAMP)
        candidate["next"].clear()
        result["verified"].clear()
        self.assertEqual({"next": [2], "verified": [True]}, cell.value)
        self.assertEqual(1, cell.revision)
        self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, {}, STAMP))

    def test_begin_invalidates_previous_preview_before_evaluation_can_fail(self):
        cell = CandidateCell("committed")
        first = self.sealed(cell)
        generation = cell.begin_preview()
        with self.assertRaisesRegex(RuntimeError, "evaluation failed"):
            raise RuntimeError("evaluation failed")
        self.assertEqual(2, generation)
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(first, STAMP))
        self.assertEqual("committed", cell.value)
        self.assertEqual(0, cell.revision)

    def test_overlapping_evaluation_only_latest_generation_can_seal(self):
        cell = CandidateCell(0)
        older = cell.begin_preview()
        newer = cell.begin_preview()
        token = cell.seal_preview(newer, 2, "two", STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(older, 1, "one", STAMP))
        receipt, value = cell.claim(token, STAMP)
        self.assertEqual(2, cell.commit(receipt, value, STAMP))

    def test_seal_requires_begin_and_each_generation_can_seal_only_once(self):
        cell = CandidateCell(0)
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(0, 1, "one", STAMP))
        generation = cell.begin_preview()
        token = cell.seal_preview(generation, 1, "one", STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(generation, 2, "two", STAMP))
        receipt, value = cell.claim(token, STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(generation, 3, "three", STAMP))
        self.assertEqual(1, cell.commit(receipt, value, STAMP))

    def test_identical_preview_reopens_with_a_distinct_token(self):
        cell = CandidateCell(0)
        first = self.sealed(cell)
        second = self.sealed(cell)
        self.assertIs(type(first), str)
        self.assertNotEqual(first, second)
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(first, STAMP))
        receipt, value = cell.claim(second, STAMP)
        cell.commit(receipt, value, STAMP)
        third = self.sealed(cell)
        self.assertNotEqual(second, third)
        self.assertEqual(1, cell.revision)

    def test_session_nonce_separates_otherwise_identical_cells(self):
        left, right = CandidateCell(0), CandidateCell(0)
        left_token, right_token = self.sealed(left), self.sealed(right)
        self.assertNotEqual(left_token, right_token)
        self.assert_code("STALE_PREVIEW", lambda: right.claim(left_token, STAMP))
        receipt, value = right.claim(right_token, STAMP)
        self.assertEqual(value, right.commit(receipt, value, STAMP))

    def test_token_binds_opaque_content_digest_and_stamp(self):
        with mock.patch.object(transactions.secrets, "token_hex", return_value="fixed-test-session"):
            first, other_digest, other_stamp = CandidateCell(0), CandidateCell(0), CandidateCell(0)
        tokens = {self.sealed(first), self.sealed(other_digest, digest="other-content"),
                  self.sealed(other_stamp, stamp=CHANGED_STAMP)}
        self.assertEqual(3, len(tokens))

    def test_wrong_token_does_not_consume_current_preview(self):
        cell = CandidateCell(0)
        token = self.sealed(cell)
        for bad in ("wrong", None, 1, True, [token]):
            self.assert_code("STALE_PREVIEW", lambda: cell.claim(bad, STAMP))
        receipt, value = cell.claim(token, STAMP)
        self.assertEqual(value, cell.commit(receipt, value, STAMP))

    def test_claim_is_single_use_even_if_external_verification_fails(self):
        cell = CandidateCell({"old": 1})
        token = self.sealed(cell)
        cell.claim(token, STAMP)
        with self.assertRaisesRegex(ValueError, "verification failed"):
            raise ValueError("verification failed")
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(token, STAMP))
        self.assertEqual({"old": 1}, cell.value)
        self.assertEqual(0, cell.revision)

    def test_stamp_change_at_claim_consumes_matching_preview(self):
        cell = CandidateCell(0)
        token = self.sealed(cell)
        self.assert_code("EVALUATOR_CHANGED", lambda: cell.claim(token, CHANGED_STAMP))
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(token, STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def assert_commit_stamp_guard(self, cell_type=CandidateCell, error_type=CandidateError):
        cell = cell_type({"old": 1})
        receipt, candidate = cell.claim(self.sealed(cell), STAMP)
        self.assert_code("EVALUATOR_CHANGED", lambda: cell.commit(receipt, candidate, CHANGED_STAMP), error_type)
        self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, candidate, STAMP), error_type)
        self.assertEqual(({"old": 1}, 0), (cell.value, cell.revision))

    def test_stamp_change_after_claim_consumes_receipt_and_keeps_committed_value(self):
        self.assert_commit_stamp_guard()

    def test_receipt_identity_cannot_be_copied_or_fabricated(self):
        cell = CandidateCell(0)
        receipt, value = cell.claim(self.sealed(cell), STAMP)
        for bad in (object(), copy(receipt), deepcopy(receipt), None, "receipt"):
            self.assert_code("STALE_PREVIEW", lambda: cell.commit(bad, value, STAMP))
        self.assertEqual(value, cell.commit(receipt, value, STAMP))

    def assert_receipt_owner_guard(self, cell_type=CandidateCell, error_type=CandidateError):
        left, right = cell_type(0), cell_type(10)
        left_receipt, left_value = left.claim(self.sealed(left, {"left": 1}), STAMP)
        right_receipt, right_value = right.claim(self.sealed(right, {"right": 2}), STAMP)
        self.assert_code("STALE_PREVIEW", lambda: right.commit(left_receipt, left_value, STAMP), error_type)
        self.assertEqual((0, 10), (left.value, right.value))
        self.assertEqual(right_value, right.commit(right_receipt, right_value, STAMP))
        self.assertEqual(left_value, left.commit(left_receipt, left_value, STAMP))

    def test_receipts_are_bound_to_the_issuing_cell(self):
        self.assert_receipt_owner_guard()

    def test_cancel_matching_token_preserves_value_and_invalidates_preview(self):
        cell = CandidateCell(0)
        token = self.sealed(cell)
        cell.cancel(token)
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(token, STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))
        self.assertNotEqual(token, self.sealed(cell))

    def test_wrong_cancel_token_preserves_current_pending_and_claimed_work(self):
        cell = CandidateCell(0)
        token = self.sealed(cell)
        generation = cell.generation
        self.assert_code("STALE_PREVIEW", lambda: cell.cancel("other"))
        self.assertEqual(generation, cell.generation)
        receipt, value = cell.claim(token, STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.cancel(token))
        self.assertEqual(value, cell.commit(receipt, value, STAMP))

    def test_cancel_without_token_invalidates_evaluating_or_claimed_work(self):
        cell = CandidateCell(0)
        generation = cell.begin_preview()
        cell.cancel()
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(generation, 1, "one", STAMP))
        receipt, value = cell.claim(self.sealed(cell), STAMP)
        cell.cancel()
        self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, value, STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def test_begin_after_claim_invalidates_receipt_without_losing_new_preview(self):
        cell = CandidateCell(0)
        receipt, value = cell.claim(self.sealed(cell), STAMP)
        newer = self.sealed(cell, 3)
        self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, value, STAMP))
        receipt, value = cell.claim(newer, STAMP)
        self.assertEqual(3, cell.commit(receipt, value, STAMP))

    def test_mutable_or_ambiguous_stamp_values_cannot_be_sealed(self):
        cell = CandidateCell(0)
        for stamp in (["x"], ({"x": 1},), (True,), (1.0,), (("x", []),), (object(),)):
            with self.subTest(stamp=stamp), self.assertRaises(TypeError):
                self.sealed(cell, stamp=stamp)
        self.assertEqual((0, 0), (cell.value, cell.revision))
        with self.assertRaises(TypeError):
            self.sealed(cell, digest=123)

    def test_bad_stamp_shape_at_claim_or_commit_consumes_matching_authority(self):
        cell = CandidateCell(0)
        token = self.sealed(cell)
        self.assert_code("EVALUATOR_CHANGED", lambda: cell.claim(token, (True,)))
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(token, STAMP))
        receipt, value = cell.claim(self.sealed(cell), STAMP)
        self.assert_code("EVALUATOR_CHANGED", lambda: cell.commit(receipt, value, ["bad"]))
        self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, value, STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def test_failed_seal_copy_leaves_old_state_and_no_reusable_generation(self):
        cell = CandidateCell(0)
        previous = self.sealed(cell)
        generation = cell.begin_preview()
        with self.assertRaisesRegex(RuntimeError, "copy failed"):
            cell.seal_preview(generation, CopyFailure(), "bad-copy", STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(previous, STAMP))
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(generation, 1, "one", STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def test_failed_claim_copy_consumes_preview_without_committing(self):
        cell = CandidateCell(0)
        class FailsOnNextCopy:
            def __deepcopy__(self, memo):
                return CopyFailure()
        token = self.sealed(cell, FailsOnNextCopy())
        with self.assertRaisesRegex(RuntimeError, "copy failed"):
            cell.claim(token, STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(token, STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def test_failed_commit_storage_or_return_copy_consumes_receipt_atomically(self):
        class FailsOnReturnCopy:
            def __deepcopy__(self, memo):
                return CopyFailure()
        for failed_value in (CopyFailure(), FailsOnReturnCopy()):
            cell = CandidateCell(0)
            receipt, candidate = cell.claim(self.sealed(cell), STAMP)
            with self.assertRaisesRegex(RuntimeError, "copy failed"):
                cell.commit(receipt, failed_value, STAMP)
            self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, candidate, STAMP))
            self.assertEqual((0, 0), (cell.value, cell.revision))

    def test_new_preview_during_seal_copy_cannot_be_overwritten(self):
        cell = CandidateCell(0)
        generation = cell.begin_preview()
        created = []
        candidate = CopyHook(lambda: created.append(self.sealed(cell, 3)))
        self.assert_code("STALE_PREVIEW", lambda: cell.seal_preview(generation, candidate, "old", STAMP))
        receipt, value = cell.claim(created[0], STAMP)
        self.assertEqual(3, cell.commit(receipt, value, STAMP))

    def test_cancel_during_claim_copy_cannot_mint_a_receipt(self):
        cell = CandidateCell(0)
        class ClaimsWithHook:
            def __deepcopy__(self, memo):
                return CopyHook(cell.cancel)
        token = self.sealed(cell, ClaimsWithHook())
        self.assert_code("STALE_PREVIEW", lambda: cell.claim(token, STAMP))
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def assert_commit_generation_guard(self, cell_type=CandidateCell, error_type=CandidateError):
        cell = cell_type(0)
        receipt, value = cell.claim(self.sealed(cell), STAMP)
        self.assert_code("STALE_PREVIEW", lambda: cell.commit(receipt, CopyHook(cell.cancel), STAMP), error_type)
        self.assertEqual((0, 0), (cell.value, cell.revision))

    def test_cancel_during_commit_copy_is_checked_before_atomic_replacement(self):
        self.assert_commit_generation_guard()

    def test_concurrent_new_commit_wins_over_an_older_suspended_commit(self):
        cell = CandidateCell(0)
        receipt, candidate = cell.claim(self.sealed(cell), STAMP)
        copying, resume = threading.Event(), threading.Event()
        errors = []
        def suspend_copy():
            copying.set()
            if not resume.wait(5):
                raise RuntimeError("copy barrier timed out")
        def old_commit():
            try:
                cell.commit(receipt, CopyHook(suspend_copy), STAMP)
            except BaseException as exc:
                errors.append(exc)
        thread = threading.Thread(target=old_commit)
        thread.start()
        try:
            self.assertTrue(copying.wait(5), "older commit never reached its copy")
            newer, value = cell.claim(self.sealed(cell, 3), STAMP)
            self.assertEqual(3, cell.commit(newer, value, STAMP))
        finally:
            resume.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(1, len(errors), errors)
        self.assertIsInstance(errors[0], CandidateError)
        self.assertEqual("STALE_PREVIEW", errors[0].code)
        self.assertEqual((3, 1), (cell.value, cell.revision))

    def test_removed_guards_are_killed_by_the_same_behavioral_oracles(self):
        source = Path(transactions.__file__).read_text(encoding="utf-8")
        cases = (
            ("if evaluator_stamp != claimed.evaluator_stamp:", "if False:", self.assert_commit_stamp_guard),
            ("if claimed is None or claimed.receipt is not receipt:", "if claimed is None:", self.assert_receipt_owner_guard),
            ("        with self._lock:\n            if claimed.revision != self._revision or claimed.generation != self._generation:\n                raise _stale()\n            self._value = value",
             "        with self._lock:\n            self._value = value", self.assert_commit_generation_guard),
        )
        for index, (before, after, oracle) in enumerate(cases):
            with self.subTest(guard=index), tempfile.TemporaryDirectory(prefix="candidate-guard-") as directory:
                self.assertEqual(1, source.count(before), "mutation must hit exactly one production guard")
                oracle()
                path = Path(directory) / "transactions.py"
                path.write_text(source.replace(before, after), encoding="utf-8")
                name = "candidate_guard_mutant_" + str(index)
                spec = importlib.util.spec_from_file_location(name, path)
                mutated = importlib.util.module_from_spec(spec)
                sys.modules[name] = mutated
                try:
                    spec.loader.exec_module(mutated)  # Import errors never count as a killed mutant.
                    with self.assertRaises(AssertionError):
                        oracle(mutated.CandidateCell, mutated.CandidateError)
                finally:
                    sys.modules.pop(name, None)
                oracle()


if __name__ == "__main__":
    unittest.main(verbosity=2)
