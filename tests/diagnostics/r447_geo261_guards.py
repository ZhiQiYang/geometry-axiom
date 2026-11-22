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

    def assert_withdrawal(self, name, mutation, marker):
        original = [dict(row) for row in self.rows]
        mutant = [dict(row) for row in original]
        mutation(mutant)

        def verdict(rows):
            try:
                check_inventory(rows)
            except AssertionError as error:
                self.assertIn(marker, str(error))
                return 1
            return 0

        self.assertEqual([0, 1, 0], [verdict(original), verdict(mutant), verdict(original)], name)

    def test_PF6_INVENTORY_OMIT_REGISTRATION(self):
        def mutation(rows):
            rows.pop(self.second)
        self.assert_withdrawal("PF6_INVENTORY_OMIT_REGISTRATION", mutation,
                               "PF6_NATIVE_IDS_IN_DECLARATION_ORDER")

    def test_PF6_INVENTORY_SWAP_ORDER(self):
        def mutation(rows):
            rows[self.first], rows[self.second] = rows[self.second], rows[self.first]
        self.assert_withdrawal("PF6_INVENTORY_SWAP_ORDER", mutation,
                               "PF6_NATIVE_IDS_IN_DECLARATION_ORDER")

    def test_PF6_INVENTORY_WRONG_OWNER(self):
        def mutation(rows):
            rows[self.first]["file"] = rows[self.second]["file"]
        self.assert_withdrawal("PF6_INVENTORY_WRONG_OWNER", mutation,
                               "R360_ORIGINAL_123_OWNERS_UNCHANGED")

    def test_PF6_INVENTORY_WRONG_BINARY(self):
        def mutation(rows):
            rows[self.first].pop("binary")
        self.assert_withdrawal("PF6_INVENTORY_WRONG_BINARY", mutation,
                               "NATIVE_BRIDGE_IDS_EXACT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
