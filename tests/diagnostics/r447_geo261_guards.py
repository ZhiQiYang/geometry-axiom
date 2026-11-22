"""PF-6 registry withdrawals. Invoke the existing full native inventory oracle."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_geo261_mutation_migration as migration


def check_inventory(rows):
    method = "test_all_fifty_definitions_keep_live_or_retired_targets"
    case = migration.LiveMutationAnchorMigration(method)
    with patch.object(migration.mutate, "MUTANTS", rows):
        getattr(case, method)()


class PF6InventoryWithdrawals(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(row) for row in migration.mutate.MUTANTS]
        self.first = next(i for i, row in enumerate(self.rows)
                          if row["id"] == "PF6_PARTIAL_SUCCESS_WRITES")
        self.second = next(i for i, row in enumerate(self.rows)
                           if row["id"] == "PF6_UNSELECTED_CREATES")

    def test_original_registry_passes(self):
        check_inventory(self.rows)

    def test_PF6_INVENTORY_SWAP_ORDER(self):
        self.rows[self.first], self.rows[self.second] = self.rows[self.second], self.rows[self.first]
        with self.assertRaisesRegex(AssertionError, "PF6_NATIVE_IDS_IN_DECLARATION_ORDER"):
            check_inventory(self.rows)

    def test_PF6_INVENTORY_WRONG_OWNER(self):
        self.rows[self.first]["file"] = self.rows[self.second]["file"]
        with self.assertRaisesRegex(AssertionError, "R360_ORIGINAL_123_OWNERS_UNCHANGED"):
            check_inventory(self.rows)

    def test_PF6_INVENTORY_WRONG_BINARY(self):
        self.rows[self.first].pop("binary")
        with self.assertRaisesRegex(AssertionError, "NATIVE_BRIDGE_IDS_EXACT"):
            check_inventory(self.rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
