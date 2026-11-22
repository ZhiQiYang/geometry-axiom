"""PF-6 / R443 exact-identity regression for R396 historical replay."""
from pathlib import Path
import json
import subprocess
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_unittest_runner as runner

R443_NAMES = frozenset({'node:engineering_override_display',
                        'node:face_length_overlay'})
R443_ORDERS = {
    'node:engineering_override_display': 'new/node__engineering_override_display',
    'node:face_length_overlay': 'new/node__face_length_overlay',
}
R443_COSTS = {name: 120000 for name in R443_NAMES}


class PF6HistoricalBudget(unittest.TestCase):
    def replay(self):
        runner.NativeShardCoverage('test_workspace_historical_budget').test_workspace_historical_budget()

    def test_R447_MERGE_NAMED_FRAGMENT_ALLOWLIST(self):
        self.assertEqual(R443_NAMES, getattr(runner, 'R443_ADDED_SUITES', frozenset()),
                         'R447_MERGE_NAMED_FRAGMENT_ALLOWLIST')
        self.assertEqual(R443_ORDERS, getattr(runner, 'R443_ADDED_ORDERS', {}),
                         'R447_R443_EXACT_ORDERS')
        self.assertEqual(R443_COSTS, getattr(runner, 'R443_ADDED_COSTS', {}),
                         'R447_R443_EXACT_COSTS')
        self.replay()

    def test_r443_current_registry_and_costs(self):
        rows = runner.native_registry.load_registry(runner.run_all.ROOT)
        selected = [row for row in rows if row['name'] in R443_NAMES]
        self.assertEqual(len(R443_NAMES), len(selected), 'R447_R443_REGISTERED_ONCE')
        self.assertEqual(R443_ORDERS, {row['name']: row['order'] for row in selected},
                         'R447_R443_EXACT_NEW_FRAGMENTS')
        costs = runner.native_shards.added_suite_costs()
        self.assertEqual(R443_COSTS, {name: costs.get(name) for name in R443_NAMES},
                         'R447_R443_EXACT_NATIVE_COSTS')
        self.replay()

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


WITHDRAWALS = {
    'R447_UNKNOWN_NEW_WITH_MATCHING_COST': 'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS',
    'R447_PF6_MISSING_COST': 'R396_REGISTERED_NEW_SUITES_HAVE_INDEPENDENT_COSTS',
    'R447_R443_WRONG_ORDER': 'R443_NEW_SUITES_REGISTERED_IN_NEW_FRAGMENT',
    'R447_R443_MISSING_ROW': 'R443_NEW_SUITES_REGISTERED_ONCE',
    'R447_R443_MISSING_COST': 'R443_REGISTERED_NEW_SUITES_HAVE_INDEPENDENT_COSTS',
}


def probe(name):
    case = PF6HistoricalBudget()
    if name == 'baseline':
        case.test_R447_MERGE_NAMED_FRAGMENT_ALLOWLIST()
        case.test_r443_current_registry_and_costs()
        return
    rows = runner.native_registry.load_registry(runner.run_all.ROOT)
    costs = dict(runner.native_shards.added_suite_costs())
    if name == 'R447_UNKNOWN_NEW_WITH_MATCHING_COST':
        extra = 'py:test_r447_unknown_control'
        template = next(row for row in rows if row['name'] == 'py:test_panel_fill_builder')
        forged = dict(template, name=extra, order='new/py__test_r447_unknown_control')
        with mock.patch.object(runner.native_registry, 'load_registry',
                               return_value=[*rows, forged]):
            with mock.patch.object(runner.native_shards, 'added_suite_costs',
                                   return_value={**costs, extra: 1000}):
                case.replay()
    elif name == 'R447_PF6_MISSING_COST':
        del costs['py:test_panel_fill_builder']
        with mock.patch.object(runner.native_shards, 'added_suite_costs', return_value=costs):
            case.replay()
    elif name == 'R447_R443_WRONG_ORDER':
        changed = [dict(row, order='new/node__wrong') if
                   row['name'] == 'node:face_length_overlay' else row for row in rows]
        with mock.patch.object(runner.native_registry, 'load_registry', return_value=changed):
            with mock.patch.object(runner.native_shards, 'added_suite_costs',
                                   return_value=costs):
                case.replay()
    elif name == 'R447_R443_MISSING_ROW':
        changed = [row for row in rows if row['name'] != 'node:face_length_overlay']
        with mock.patch.object(runner.native_registry, 'load_registry', return_value=changed):
            with mock.patch.object(runner.native_shards, 'added_suite_costs',
                                   return_value=costs):
                case.replay()
    elif name == 'R447_R443_MISSING_COST':
        del costs['node:face_length_overlay']
        with mock.patch.object(runner.native_shards, 'added_suite_costs', return_value=costs):
            case.replay()
    else:
        raise ValueError('unknown probe: ' + name)


def withdraw_checks():
    out = []
    for name, marker in WITHDRAWALS.items():
        cmd = [sys.executable, str(Path(__file__).resolve()), '--probe']
        calls = [subprocess.run([*cmd, variant], capture_output=True, text=True)
                 for variant in ('baseline', name, 'baseline')]
        exits = [call.returncode for call in calls]
        if exits != [0, 1, 0]:
            raise AssertionError(name + ' exits ' + repr(exits))
        if marker not in calls[1].stderr or 'AssertionError:' not in calls[1].stderr:
            raise AssertionError(name + ' wrong failure: ' + calls[1].stderr)
        out.append({'name': name, 'marker': marker, 'exits': exits})
    print(json.dumps({'withdrawals': out}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if '--probe' in sys.argv:
        probe(sys.argv[sys.argv.index('--probe') + 1])
    elif '--withdraw-checks' in sys.argv:
        withdraw_checks()
    else:
        unittest.main()
