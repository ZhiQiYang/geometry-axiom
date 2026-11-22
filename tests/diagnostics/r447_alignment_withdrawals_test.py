"""T: require independent source-withdrawal proof for the PF-6 alignments."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests/diagnostics/r447_alignment_withdrawals.py"
EXPECTED = {
    "R447_PF6_OWNER_REGISTRATION_OMITTED": "PF6_NATIVE_IDS_IN_DECLARATION_ORDER",
    "R447_PF6_CAPABILITY_WRONG_POSITION": "R14_NATIVE_CAPABILITY_EXPLICIT_AND_ORDERED",
    "R447_PF6_LEGACY_CAPABILITY_REMOVED": "R14_NATIVE_CAPABILITY_EXPLICIT_AND_ORDERED",
}


class PF6AlignmentWithdrawalContract(unittest.TestCase):
    def test_independent_source_withdrawals_are_replayable(self):
        self.assertTrue(RUNNER.is_file(), "R447_ALIGNMENT_WITHDRAWAL_RUNNER_PRESENT")
        result = subprocess.run(
            [sys.executable, "-B", str(RUNNER)], cwd=ROOT,
            text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
        )
        self.assertEqual(0, result.returncode,
                         "R447_ALIGNMENT_WITHDRAWAL_RUNNER_GREEN\n" + result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual("r447-pf6-alignment-withdrawals/1", receipt.get("schema"),
                         "R447_ALIGNMENT_WITHDRAWAL_SCHEMA")
        rows = {row["id"]: row for row in receipt.get("withdrawals", [])}
        self.assertEqual(EXPECTED, {key: rows.get(key, {}).get("assertion") for key in EXPECTED},
                         "R447_ALIGNMENT_WITHDRAWAL_EXACT_SET")
        for identifier in EXPECTED:
            self.assertEqual([0, 1, 0], rows[identifier].get("baselineMutantRestoredExit"),
                             "R447_ALIGNMENT_WITHDRAWAL_0_1_0 " + identifier)
            self.assertTrue(rows[identifier].get("sourceRestoredExactly"),
                            "R447_ALIGNMENT_WITHDRAWAL_BYTES " + identifier)


if __name__ == "__main__":
    unittest.main(verbosity=2)
