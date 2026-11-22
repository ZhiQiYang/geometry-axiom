"""PF-6 regression for R396's four-shard historical replay."""
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_unittest_runner as runner


class PF6HistoricalBudget(unittest.TestCase):
    def replay(self):
        runner.NativeShardCoverage('test_workspace_historical_budget').test_workspace_historical_budget()

    def test_pf6_suites_with_independent_costs_allow_historical_replay(self):
        costs = runner.native_shards.added_suite_costs()
        self.assertIn('py:test_builder_token_owners', costs)
        self.assertIn('py:test_panel_fill_builder', costs)
        self.replay()

    def test_unregistered_cost_still_fails_r396(self):
        costs = runner.native_shards.added_suite_costs()
        sentinel = 'py:undeclared_pf6_control'
        self.assertNotIn(sentinel, costs)
        with mock.patch.object(runner.native_shards, 'added_suite_costs',
                               return_value={**costs, sentinel: 1000}):
            with self.assertRaisesRegex(AssertionError, 'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS'):
                self.replay()

    def test_PF6_R396_UNKNOWN_NEW_ROW_WITH_MATCHING_COST_REJECTED(self):
        # The old set-comprehension silently excluded every new/ row, even
        # when the exact same unauthorized name had a positive cost.
        rows = runner.native_registry.load_registry(runner.run_all.ROOT)
        costs = runner.native_shards.added_suite_costs()
        extra = 'py:test_r447_unlisted_control'
        self.assertNotIn(extra, costs)
        self.assertFalse(any(row['name'] == extra for row in rows))
        template = next(row for row in rows if row['name'] == 'py:test_panel_fill_builder')
        forged = dict(template, name=extra, order='new/py__test_r447_unlisted_control')
        with mock.patch.object(runner.native_registry, 'load_registry',
                               return_value=[*rows, forged]):
            with mock.patch.object(runner.native_shards, 'added_suite_costs',
                                   return_value={**costs, extra: 1000}):
                with self.assertRaisesRegex(AssertionError,
                                            'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS'):
                    self.replay()

    def test_PF6_R396_DROP_REGISTERED_COST(self):
        costs = runner.native_shards.added_suite_costs()
        incomplete = dict(costs)
        del incomplete['py:test_panel_fill_builder']
        with mock.patch.object(runner.native_shards, 'added_suite_costs', return_value=incomplete):
            with self.assertRaisesRegex(AssertionError, 'R396_REGISTERED_NEW_SUITES_HAVE_INDEPENDENT_COSTS'):
                self.replay()


if __name__ == '__main__':
    unittest.main()
