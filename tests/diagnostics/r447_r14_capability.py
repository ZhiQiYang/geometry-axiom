"""Exercise the R14 acceptance judge up to its first geometry mutation."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.test_r14_repeat_panel import R14RepeatPanelNative


class CapabilitiesAccepted(Exception):
    """The original guard finished checking engineering-read and reached seed()."""


class PF6CapabilityOrder(unittest.TestCase):
    def test_exact_native_sequence_and_named_withdrawals(self):
        method = "test_13_host_capability_includes_panel_rules_without_changing_native_identity"
        judge = R14RepeatPanelNative(method)
        host = ["engineering-spec/1", "parameters/1", "assembly-rule-authoring/1",
                "assembly-timber-generation/1", "assembly-bay-repeat/1", "grid-subdivision-rules/1",
                "grid-subdivision-rules/2", "section-profile/1", "grid-card-reference/1",
                "identity-ledger/1", "definition-import/1"]
        native = ["section-profile-native/1", "panel-fill-native/1", "grid-subdivision-native/2",
                  "panel-fill-builder-native/1"]

        def exercise(sequence):
            def read(command):
                self.assertEqual(command, "engineering-read")
                return {"state": {"capabilities": host, "native_capabilities": sequence}}
            with patch.object(judge, "command", read), patch.object(judge, "seed", side_effect=CapabilitiesAccepted):
                getattr(judge, method)()

        with self.assertRaises(CapabilitiesAccepted):
            exercise(native)
        withdrawals = {
            "PF6_R14_MISSING_FINAL_CAPABILITY": native[:-1],
            "PF6_R14_SWAPPED_FINAL_PAIR": native[:2] + list(reversed(native[2:])),
            "PF6_R14_DUPLICATE_FINAL_CAPABILITY": native + native[-1:],
        }
        for name, sequence in withdrawals.items():
            with self.subTest(name=name), self.assertRaisesRegex(AssertionError, "R14_NATIVE_CAPABILITY_EXPLICIT_AND_ORDERED"):
                exercise(sequence)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PF6CapabilityOrder)
    raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
