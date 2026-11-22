"""One parent test guards the reporter's synthetic outcome matrix (#118)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import argparse
import ast
from collections import Counter
from copy import deepcopy
import contextlib
import io
import json
import hashlib
import re
import random
import shutil
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import run_all
import native_shards
import native_registry
import native_score_reference
from native_shards import parse_shard, partition_suites, timing_weights, validate_partition
import native_shard_receipts
from native_shard_receipts import validate_rows

# Exact native job blocks from f3ee80cf: frozen four-shard regression fixture.
# Historical mutants change this fixture, never the live six-shard workflow.
HISTORICAL_FOUR_NATIVE_WORKFLOW = r'''
  native:
    name: native (${{ matrix.shard }}/4)
    runs-on: ubuntu-latest
    # R348: retain all measured runs; four native shards, still 35 minutes each.
    timeout-minutes: 35
    strategy:
      fail-fast: false
      max-parallel: 4
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4
        with:
          node-version: '24'
      - name: Build and run assigned non-browser suites
        run: |
          ulimit -s 16384
          python3 tests/run_all.py --build --shard '${{ matrix.shard }}/4' --report '${{ runner.temp }}/native-shard-${{ matrix.shard }}/shard-${{ matrix.shard }}.json'
      - name: Preserve original shard receipts
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: native-shard-${{ matrix.shard }}
          path: ${{ runner.temp }}/native-shard-${{ matrix.shard }}/
          if-no-files-found: error
          retention-days: 14
      - name: Preserve original suite logs
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: native-logs-${{ matrix.shard }}
          path: /tmp/geometry-tests/run_all-logs/
          if-no-files-found: error
          retention-days: 14

  native-complete:
    name: native complete coverage
    runs-on: ubuntu-latest
    needs: native
    if: always()
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false
      - name: Prove real coverage test kills a removed suite
        run: python3 -B tests/native_sharding_mutation_check.py --output '${{ runner.temp }}/native-sharding-proof'
      - name: Prove archive capability guards with the original mutation judge
        run: python3 geometry-core/card-reference/run_archive_mutations.py --output '${{ runner.temp }}/archive-mutations'
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093 # v4
        with:
          pattern: native-shard-*
          path: ${{ runner.temp }}/native-shards
          merge-multiple: true
      - name: Verify complete disjoint actual execution
        run: python3 -B tests/native_shard_receipts.py --input '${{ runner.temp }}/native-shards' --parts 4 --output '${{ runner.temp }}/native-complete.json'
      - name: Preserve coverage and mutation proof
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: native-complete-coverage
          path: |
            ${{ runner.temp }}/native-sharding-proof/
            ${{ runner.temp }}/native-complete.json
            ${{ runner.temp }}/archive-mutations/
          if-no-files-found: error
          retention-days: 14


'''



class RunnerClassification(unittest.TestCase):
    def test_synthetic_parent_outcomes(self):
        verifier = Path(__file__).parent / 'runner_classification' / 'verify.py'
        env = {key: value for key, value in os.environ.items() if not key.startswith('GEOMETRY_')}
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        with tempfile.TemporaryDirectory(prefix='geometry-runner-classification-') as temp:
            result = subprocess.run([sys.executable, str(verifier), '--out', str(Path(temp) / 'receipts')],
                                    env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


R379_ADDED_SUITES = frozenset({'node:r14_app', 'node:r14_host', 'py:test_r14_browser_receipt'})
R380_ADDED_SUITES = frozenset({'py:test_panel_fill_grid_source', 'node:panel_fill_grid_read_compat'})
R396_ADDED_SUITES = frozenset({'node:workspace_view_state', 'py:test_workspace_view_server',
                              'py:test_workspace_view', 'node:workspace_context_menu_state'})
R17_ADDED_SUITES = frozenset({'py:test_boundary_pair_host', 'node:boundary_pair_ui',
                              'node:boundary_pair_project', 'node:boundary_pair_browser_scope'})
R12_ADDED_SUITES = frozenset({'py:test_space_profile_runs', 'py:test_space_profile_update',
                              'py:test_r12_browser_evidence', 'node:space_profile_ui',
                              'node:space_profile_view', 'node:space_profile_update_ui',
                              'node:profile_space_browser_contract'})
PF4A_ADDED_SUITES = frozenset({'py:test_panel_fill_grid_transaction', 'node:panel_fill_grid_ui'})
R03_ADDED_SUITES = frozenset({'py:test_framing_template', 'node:framing_recipe_project_store',
                            'node:framing_template_session', 'node:framing_template_browser_scope'})
PF6_ADDED_SUITES = frozenset({'py:test_panel_fill_builder', 'py:test_builder_token_owners'})


class BrowserPathScopeWiring(unittest.TestCase):
    """#391 審查 F2：釘住「文件／測試類 PR 只跑 native」的 workflow 接線。

    browser 只能在 path-scope 明確輸出 false 時略過（任何其他值、包含空字串都全跑）；
    browser-canvas-complete 用同一支分類器重算，略過時只接受 skipped，否則照舊要求 success
    並核對收據。具名撤回見 tests/native_sharding_mutation_check.py 的 R391_*。"""

    MARKER = 'R391_BROWSER_PATH_SCOPE_WIRING'

    @staticmethod
    def _job(workflow, job):
        match = re.search(r'^  ' + re.escape(job) + r':\n(.*?)(?=^  \S|\Z)', workflow, re.M | re.S)
        return match[1] if match else None

    @staticmethod
    def _steps(block):
        return ['      - ' + step for step in re.split(r'^      - ', block, flags=re.M)[1:]]

    def _assert_lines(self, block, lines):
        for line in lines:
            self.assertIn('\n' + line + '\n', '\n' + block, self.MARKER + ': missing ' + line.strip())

    def test_browser_jobs_skip_only_on_explicit_path_scope_false(self):
        marker = self.MARKER
        workflow = (Path(__file__).parent.parent / '.github/workflows/integration-tests.yml').read_text(
            encoding='utf-8')
        scope, browser, complete = (self._job(workflow, job)
                                    for job in ('path-scope', 'browser', 'browser-canvas-complete'))
        for name, block in (('path-scope', scope), ('browser', browser), ('browser-canvas-complete', complete)):
            self.assertIsNotNone(block, marker + ': missing job ' + name)

        self._assert_lines(scope, ('    outputs:', '      browser: ${{ steps.scope.outputs.browser }}',
                                   '        run: python3 -B .github/scripts/ci_path_scope.py --selftest'))
        classify = ('python3 -B .github/scripts/ci_path_scope.py --event "$EVENT_NAME" '
                    '--pr-head "$PR_HEAD" --github-output "$GITHUB_OUTPUT"')
        self.assertIn(classify, scope, marker)

        # browser：需要 path-scope，且只有輸出恰為 'false' 才略過。
        self._assert_lines(browser, ('    needs: path-scope',
                                     "    if: needs.path-scope.outputs.browser != 'false'"))
        self.assertNotIn("browser == 'true'", browser, marker)

        # canvas-complete：仍然 needs browser + always()，並以同一分類器重算範圍。
        self._assert_lines(complete, ('    needs: browser', '    if: always()'))
        steps = self._steps(complete)
        index = {}
        for position, step in enumerate(steps):
            if '        id: scope\n' in step:
                self.assertIn(classify, step, marker)
                index['scope'] = position
            if 'run: test "$BROWSER_RESULT" = skipped' in step:
                self._assert_lines(step, ("        if: steps.scope.outputs.browser == 'false'",
                                          '          BROWSER_RESULT: ${{ needs.browser.result }}'))
                index['skipped'] = position
            if 'run: test "$BROWSER_RESULT" = success' in step:
                self._assert_lines(step, ("        if: steps.scope.outputs.browser != 'false'",
                                          '          BROWSER_RESULT: ${{ needs.browser.result }}'))
                index['success'] = position
            if 'canvas_evidence.py verify' in step or 'pattern: canvas-shard-*' in step:
                self.assertIn("        if: steps.scope.outputs.browser != 'false'\n", step, marker)
                index.setdefault('evidence', position)
        for key in ('scope', 'skipped', 'success', 'evidence'):
            self.assertIn(key, index, marker + ': missing canvas-complete step ' + key)
        self.assertLess(index['scope'], min(index['skipped'], index['success'], index['evidence']), marker)
        self.assertNotIn("browser == 'true'", complete, marker)


class NativeShardCoverage(unittest.TestCase):
    def _native_workflow(self, workflow=None, marker='R378_SIX_NATIVE_WORKFLOW'):
        if workflow is None:
            workflow = (Path(__file__).parent.parent / '.github/workflows/integration-tests.yml').read_text(
                encoding='utf-8')
        blocks = []
        for job in ('native', 'native-complete'):
            match = re.search(r'^  ' + job + r':\n(.*?)(?=^  \S|\Z)', workflow, re.M | re.S)
            self.assertIsNotNone(match, marker + ': missing ' + job)
            blocks.append(match[1])
        match = re.search(r'^        shard: \[([0-9, ]+)\]$', blocks[0], re.M)
        self.assertIsNotNone(match, marker + ': missing native matrix')
        return blocks[0], blocks[1], [int(value) for value in match[1].split(',')]

    def _assert_four_native_workflow(self):
        native, complete, matrix = self._native_workflow(
            HISTORICAL_FOUR_NATIVE_WORKFLOW, 'R348_FOUR_NATIVE_WORKFLOW')
        marker = 'R348_FOUR_NATIVE_WORKFLOW'
        self.assertEqual(matrix, [1, 2, 3, 4], marker)
        for line in ('    name: native (${{ matrix.shard }}/4)',
                     '    timeout-minutes: 35', '      fail-fast: false', '      max-parallel: 4'):
            self.assertIn('\n' + line + '\n', '\n' + native, marker)
        command = next((line.strip() for line in native.splitlines()
                        if line.strip().startswith('python3 tests/run_all.py ')), '')
        self.assertIn("--build --shard '${{ matrix.shard }}/4' --report ", command, marker)
        for flag in ('--only', '--extra-py', '--allow-skip', '--simulate-missing', '--update-expected'):
            self.assertNotIn(flag, command, marker)
        self.assertNotIn('continue-on-error:', native + complete, marker)
        for line in ('    name: native complete coverage', '    needs: native', '    if: always()'):
            self.assertIn('\n' + line + '\n', '\n' + complete, marker)
        command = next((line.strip() for line in complete.splitlines()
                        if line.strip().startswith('run: python3 -B tests/native_shard_receipts.py ')), '')
        self.assertIn("--parts 4 --output ", command, marker)

    def _assert_six_native_workflow(self):
        native, complete, matrix = self._native_workflow()
        marker = 'R378_SIX_NATIVE_WORKFLOW'
        self.assertEqual(matrix, [1, 2, 3, 4, 5, 6], marker)
        for line in ('    name: native (${{ matrix.shard }}/6)',
                     '    timeout-minutes: 35', '      fail-fast: false', '      max-parallel: 6'):
            self.assertIn('\n' + line + '\n', '\n' + native, marker)
        command = next((line.strip() for line in native.splitlines()
                        if line.strip().startswith('python3 tests/run_all.py ')), '')
        self.assertIn("--build --shard '${{ matrix.shard }}/6' --report ", command, marker)
        for flag in ('--only', '--extra-py', '--allow-skip', '--simulate-missing', '--update-expected'):
            self.assertNotIn(flag, command, marker)
        self.assertNotIn('continue-on-error:', native + complete, marker)
        for line in ('    name: native complete coverage',
                     '    needs: [native, registry-contract]', '    if: always()'):
            self.assertIn('\n' + line + '\n', '\n' + complete, marker)
        command = next((line.strip() for line in complete.splitlines()
                        if line.strip().startswith('run: python3 -B tests/native_shard_receipts.py ')), '')
        self.assertIn("--parts 6 --output ", command, marker)
        # This verification job needs the current source tree, not archived
        # root evidence bundles. Keep its original five-minute contract.
        self.assertIn('\n    timeout-minutes: 5\n', '\n' + complete,
                      'R379_NATIVE_COVERAGE_SPARSE_CHECKOUT')
        self.assertIn('          filter: blob:none\n'
                      '          sparse-checkout-cone-mode: false\n'
                      '          sparse-checkout: |\n'
                      '            /*\n'
                      '            !/evidence/\n', complete,
                      'R379_NATIVE_COVERAGE_SPARSE_CHECKOUT')
        # The new registry proof has its own five-minute budget. An always()
        # coverage job must propagate a failed, cancelled or skipped proof.
        registry_marker = 'R386_REGISTRY_SEPARATE_JOB'
        workflow = (Path(__file__).parent.parent / '.github/workflows/integration-tests.yml').read_text(
            encoding='utf-8')
        registry = BrowserPathScopeWiring._job(workflow, 'registry-contract')
        self.assertIsNotNone(registry, registry_marker)
        for line in ('    name: registry contract', '    timeout-minutes: 5',
                     '          fetch-depth: 2', '          filter: blob:none',
                     '          sparse-checkout-cone-mode: false', '          sparse-checkout: |',
                     '            /*', '            !/evidence/', "          node-version: '24'",
                     '          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}',
                     '          EVENT_NAME: ${{ github.event_name }}',
                     '          PR_HEAD: ${{ github.event.pull_request.head.sha }}',
                     "        run: python3 -B tests/registry_migrate.py check --self-test --report '${{ runner.temp }}/registry-contract.json'",
                     '          name: registry-contract',
                     '          path: ${{ runner.temp }}/registry-contract.json',
                     '          if-no-files-found: error', '          retention-days: 14'):
            self.assertIn('\n' + line + '\n', '\n' + registry, registry_marker)
        self.assertNotIn('continue-on-error:', registry, registry_marker)
        self.assertNotIn('registry_migrate.py', complete, registry_marker)
        for line in ('      - name: Require registry contract success',
                     '          REGISTRY_RESULT: ${{ needs.registry-contract.result }}',
                     '        run: test "$REGISTRY_RESULT" = success'):
            self.assertIn('\n' + line + '\n', '\n' + complete, registry_marker)

    def test_partition_covers_actual_suite_registry_once(self):
        suites = run_all.build_suites()
        expected, error = run_all.load_expected()
        self.assertFalse(error)
        self.assertEqual({
            'node:r14_app': {'mode': 'count', 'count': 7, 'unit': 'node test'},
            'node:r14_host': {'mode': 'count', 'count': 15, 'unit': 'node test'},
            'py:test_r14_browser_receipt': {'mode': 'count', 'count': 10, 'unit': 'test'},
        }, {name: expected['suites'].get(name) for name in R379_ADDED_SUITES},
                         'R379_COMPLETE_EXPECTED_REGISTRY')
        self.assertEqual({
            'node:workspace_view_state': {'mode': 'count', 'count': 15, 'unit': 'node test'},
            'py:test_workspace_view_server': {'mode': 'count', 'count': 2, 'unit': 'test'},
            'py:test_workspace_view': {'mode': 'count', 'count': 10, 'unit': 'test'},
            'node:workspace_context_menu_state': {'mode': 'exit-code-only'},
        }, {name: expected['suites'].get(name) for name in R396_ADDED_SUITES},
                         'R396_COMPLETE_EXPECTED_REGISTRY')
        self.assertEqual({
            'py:test_boundary_pair_host': {'mode': 'count', 'count': 19, 'unit': 'test'},
            'node:boundary_pair_ui': {'mode': 'count', 'count': 12, 'unit': 'node test'},
            'node:boundary_pair_project': {'mode': 'count', 'count': 8, 'unit': 'node test'},
            'node:boundary_pair_browser_scope': {'mode': 'count', 'count': 7, 'unit': 'node test'},
        }, {name: expected['suites'].get(name) for name in R17_ADDED_SUITES},
                         'R17_COMPLETE_EXPECTED_REGISTRY')
        self.assertEqual(R12_ADDED_SUITES, R12_ADDED_SUITES & expected['suites'].keys(),
                         'R12_COMPLETE_EXPECTED_REGISTRY')
        self.assertEqual({
            'py:test_panel_fill_grid_transaction': {'mode': 'count', 'count': 13, 'unit': 'test'},
            'node:panel_fill_grid_ui': {'mode': 'count', 'count': 13, 'unit': 'node test'},
        }, {name: expected['suites'].get(name) for name in PF4A_ADDED_SUITES},
                         'PF4A_COMPLETE_EXPECTED_REGISTRY')
        # R03 second slice adds 7 native, 10 Session and 4 browser-contract
        # tests to the same suites. Project only those explicit additions;
        # the original 15/9/12/4 census assertion and its named kill stay live.
        # The expected file itself must still come from run_all's full census.
        r03_before_jig = deepcopy({name: expected['suites'].get(name)
                                  for name in R03_ADDED_SUITES})
        for name, added in (('py:test_framing_template', 7),
                            ('node:framing_template_session', 10),
                            ('node:framing_template_browser_scope', 4)):
            entry = r03_before_jig.get(name)
            if isinstance(entry, dict) and type(entry.get('count')) is int:
                entry['count'] -= added
        self.assertEqual({
            'py:test_framing_template': {'mode': 'count', 'count': 15, 'unit': 'test'},
            'node:framing_recipe_project_store': {'mode': 'count', 'count': 9, 'unit': 'node test'},
            'node:framing_template_session': {'mode': 'count', 'count': 12, 'unit': 'node test'},
            'node:framing_template_browser_scope': {'mode': 'count', 'count': 4, 'unit': 'node test'},
        }, r03_before_jig,
                         'R03_COMPLETE_EXPECTED_REGISTRY')
        parts = run_all.partition_suites(suites, 3)
        actual = Counter(s.name for part in parts for s in part)
        self.assertEqual(actual, Counter({name:1 for name in expected['suites']}),
                         '分片必須完整涵蓋原套件清單，且每個suite恰好一次；R396_COMPLETE_EXPECTED_REGISTRY')
        self.assertEqual(sum(map(len, parts)), len(suites))
        four = run_all.partition_suites(suites, 4)
        self.assertEqual(Counter(s.name for part in four for s in part),
                         Counter({name: 1 for name in expected['suites']}),
                         'R348_FOUR_SHARDS_COVER_FULL_REGISTRY')
        self.assertEqual(sum(map(len, four)), len(suites))
        self._assert_four_native_workflow()
        _, _, matrix = self._native_workflow()
        six = run_all.partition_suites(suites, len(matrix))
        self.assertEqual(Counter(s.name for part in six for s in part),
                         Counter({name: 1 for name in expected['suites']}),
                         'R378_SIX_SHARDS_COVER_FULL_REGISTRY')
        self.assertEqual(sum(map(len, six)), len(suites))
        self._assert_six_native_workflow()
        self._assert_rejected_trial_capacity_and_ties()

    def _assert_rejected_trial_capacity_and_ties(self):
        # Count actual scoring work, not runner seconds. Every shard is
        # balanced at [100, 100], while every cross-shard swap or two-for-one
        # exchange exceeds 100 in at least one scenario. Such a trial cannot
        # improve the descending score and must not sort its full score.
        for count in (2, 4, 6):
            parts = [{'s-%d-a' % i, 's-%d-b' % i} for i in range(count)]
            costs = {name: ([i + 1, 99 - i] if name.endswith('-a')
                            else [99 - i, i + 1])
                     for i, part in enumerate(parts) for name in part}
            loads = [[100, 100] for _ in parts]
            for method, kind in (('_swap_scenarios', 'SWAP'),
                                 ('_exchange_scenarios', 'EXCHANGE')):
                marker = 'R443_NATIVE_' + kind + '_REJECTED_TRIAL_CAPACITY'
                with self.subTest(method=method, capacity_parts=count):
                    wanted_parts, wanted_loads = [set(p) for p in parts], [p[:] for p in loads]
                    getattr(native_score_reference, method)(wanted_parts, wanted_loads, costs)
                    scalar_inputs = 0
                    def counted_sorted(values, *args, **kwargs):
                        nonlocal scalar_inputs
                        values = list(values)
                        if values and all(type(value) is int for value in values):
                            scalar_inputs += len(values)
                        return sorted(values, *args, **kwargs)
                    actual_parts, actual_loads = [set(p) for p in parts], [p[:] for p in loads]
                    with mock.patch.object(native_shards, 'sorted', counted_sorted, create=True):
                        getattr(native_shards, method)(actual_parts, actual_loads, costs)
                    self.assertEqual(actual_parts, wanted_parts, marker + ': owners')
                    self.assertEqual(actual_loads, wanted_loads, marker + ': loads')
                    # Only the initial pair scores remain; exchange also
                    # compares one initial complete score. No trial is accepted.
                    bound = (4 * (count * (count - 1) // 2) if kind == 'SWAP'
                             else 2 * count + 4 * count * (count - 1))
                    self.assertLessEqual(scalar_inputs, bound, marker)
        # Equal maxima are not grounds for rejection: lower score components
        # can still improve. Pin both the owners and every resulting load, and
        # independently compare the frozen full-score oracle. Using >= instead
        # of > for the early rejection leaves these candidates wrongly untouched.
        fixtures = (
            ('_swap_scenarios', 'SWAP',
             {'a': [1, 3], 'b': [5, 3], 'c': [1, 1], 'd': [3, 1]},
             [{'b', 'c'}, {'a', 'd'}], [[6, 4], [4, 4]]),
            ('_exchange_scenarios', 'EXCHANGE',
             {'a': [2, 1], 'b': [6, 6], 'c': [3, 3], 'd': [3, 1]},
             [{'a', 'c', 'd'}, {'b'}], [[8, 5], [6, 6]]),
        )
        for method, kind, costs, pinned_parts, pinned_loads in fixtures:
            marker = 'R443_NATIVE_' + kind + '_EQUAL_PEAK_REMAINS_ELIGIBLE'
            with self.subTest(method=method, equal_peak=True):
                parts = [{'a', 'b'}, {'c', 'd'}]
                loads = [[sum(costs[name][r] for name in part) for r in range(2)]
                         for part in parts]
                wanted_parts, wanted_loads = [set(p) for p in parts], [p[:] for p in loads]
                getattr(native_score_reference, method)(wanted_parts, wanted_loads, costs)
                self.assertEqual(wanted_parts, pinned_parts, marker + ': oracle owners')
                self.assertEqual(wanted_loads, pinned_loads, marker + ': oracle loads')
                actual_parts, actual_loads = [set(p) for p in parts], [p[:] for p in loads]
                getattr(native_shards, method)(actual_parts, actual_loads, costs)
                self.assertEqual(actual_parts, wanted_parts, marker + ': owners')
                self.assertEqual(actual_loads, wanted_loads, marker + ': loads')


    def test_partition_is_deterministic(self):
        suites = run_all.build_suites()
        first = partition_suites(suites, 3)
        second = partition_suites(suites, 3)
        self.assertEqual([[s.name for s in p] for p in first], [[s.name for s in p] for p in second])
        reverse = partition_suites(list(reversed(suites)), 3)
        self.assertEqual([set(s.name for s in p) for p in first], [set(s.name for s in p) for p in reverse])
        four = partition_suites(suites, 4)
        reverse = partition_suites(list(reversed(suites)), 4)
        self.assertEqual([set(s.name for s in p) for p in four], [set(s.name for s in p) for p in reverse])
        for part in four:
            self.assertEqual(part, [suite for suite in suites if suite in part])
        six = partition_suites(suites, 6)
        reverse = partition_suites(list(reversed(suites)), 6)
        self.assertEqual([set(s.name for s in p) for p in six], [set(s.name for s in p) for p in reverse])
        for part in six:
            self.assertEqual(part, [suite for suite in suites if suite in part])

        self._assert_score_sweeps_match_full_reference()

    def _assert_score_sweeps_match_full_reference(self):
        # Compare the complete resulting partitions and load vectors with the
        # pre-optimization implementation, including ties and varied scenarios.
        randomizer = random.Random(379)
        sweeps = (('_swap_scenarios', 'R379_NATIVE_SWAP_LOCAL_SCORE'),
                  ('_exchange_scenarios', 'R379_NATIVE_EXCHANGE_LOCAL_SCORE'))
        for count in (2, 3, 4, 6, 12):
            for scenarios in (1, 2, 4):
                for case in range(4):
                    parts, costs = [], {}
                    for part in range(count):
                        names = {'s-%02d-%02d' % (part, n)
                                 for n in range(1 + randomizer.randrange(4))}
                        parts.append(names)
                        for name in sorted(names):
                            costs[name] = [randomizer.randrange(1, 10)
                                           for _ in range(scenarios)]
                    loads = [[sum(costs[name][r] for name in part)
                              for r in range(scenarios)] for part in parts]
                    for method, marker in sweeps:
                        with self.subTest(method=method, parts=count,
                                          scenarios=scenarios, case=case):
                            wanted_parts, wanted_loads = [set(p) for p in parts], [p[:] for p in loads]
                            actual_parts, actual_loads = [set(p) for p in parts], [p[:] for p in loads]
                            getattr(native_score_reference, method)(wanted_parts, wanted_loads, costs)
                            getattr(native_shards, method)(actual_parts, actual_loads, costs)
                            self.assertEqual(actual_parts, wanted_parts, marker + ': owners/tie order')
                            self.assertEqual(actual_loads, wanted_loads, marker + ': load vectors')
        # On an already balanced fixture every trial is rejected. Sorting
        # unchanged shards once per trial adds a needless factor of shard count.
        # Count scalar score inputs, not wall time, so a slow runner cannot mask
        # or invent this complexity regression. Suite-name sorting is excluded.
        count, members, scenarios = 12, 4, 4
        parts = [{'s-%02d-%02d' % (part, n) for n in range(members)}
                 for part in range(count)]
        costs = {name: [1] * scenarios for part in parts for name in part}
        loads = [[members] * scenarios for _ in parts]
        for method, marker in sweeps:
            with self.subTest(method=method, complexity='balanced-rejected-trials'):
                scalar_inputs = 0
                def counted_sorted(values, *args, **kwargs):
                    nonlocal scalar_inputs
                    values = list(values)
                    if values and all(type(value) is int for value in values):
                        scalar_inputs += len(values)
                    return sorted(values, *args, **kwargs)
                actual_parts, actual_loads = [set(p) for p in parts], [p[:] for p in loads]
                with mock.patch.object(native_shards, 'sorted', counted_sorted, create=True):
                    getattr(native_shards, method)(actual_parts, actual_loads, costs)
                self.assertEqual(actual_parts, parts, marker + ': no change on ties')
                self.assertEqual(actual_loads, loads, marker + ': no change on ties')
                if method == '_swap_scenarios':
                    pairs = count * (count - 1) // 2
                    trials = pairs * members * members
                else:
                    pairs = count * (count - 1)
                    trials = pairs * (members * (members - 1) // 2) * members
                bound = count * scenarios + 2 * scenarios * (pairs + trials)
                self.assertLessEqual(scalar_inputs, bound, marker + ': unaffected score work')

    def test_profile_balances_measured_work(self):
        suites = run_all.build_suites()
        # Keep even max(weights.values()) at the historical 129900ms bound;
        # R12's 300000ms costs belong only to the current six-shard proof.
        # R386: later fragment-only suites are likewise outside this replay.
        # Merge (R03 × main): R03's four suites are likewise outside this history
        # (they are in later_added, exactly as main excludes them by name).
        pre_r12_known = R380_ADDED_SUITES | R379_ADDED_SUITES | R396_ADDED_SUITES | R17_ADDED_SUITES
        later_added = set(native_shards.added_suite_costs()) - pre_r12_known
        weights = {name: ms for name, ms in timing_weights().items()
                   if name not in later_added}
        self.assertEqual(129900, max(weights.values()), 'R12_HISTORICAL_BALANCE_BOUND_UNCHANGED')
        # Keep the historical 224-row and supplemental relative-weight checks.
        # Freeze the original two-run/three-shard regression and its two
        # mutation proofs. It is historical coverage, not the current CI plan.
        added = native_shards.added_suite_costs()
        known_added = (R380_ADDED_SUITES | R379_ADDED_SUITES | R396_ADDED_SUITES
                       | R17_ADDED_SUITES | R12_ADDED_SUITES | PF4A_ADDED_SUITES | R03_ADDED_SUITES)
        retained_added = set(added) & known_added
        legacy_added = {row['name']: row['planning_upper_ms'] for row in json.loads(
            native_shards.ADDED_EVIDENCE.read_text(encoding='utf-8'))['observations']}
        self.assertEqual(R380_ADDED_SUITES, set(legacy_added),
                         'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual({'py:test_panel_fill_grid_source': 65000,
                          'node:panel_fill_grid_read_compat': 2000},
                         {name: added.get(name) for name in legacy_added},
                         'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R380_ADDED_SUITES, retained_added - R379_ADDED_SUITES - R396_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R379_ADDED_SUITES, retained_added - R380_ADDED_SUITES - R396_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R379_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R396_ADDED_SUITES, retained_added - R380_ADDED_SUITES - R379_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R17_ADDED_SUITES, retained_added - R380_ADDED_SUITES - R379_ADDED_SUITES - R396_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R17_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R12_ADDED_SUITES, retained_added - R380_ADDED_SUITES - R379_ADDED_SUITES - R396_ADDED_SUITES - R17_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R12_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(PF4A_ADDED_SUITES, retained_added - R380_ADDED_SUITES - R379_ADDED_SUITES - R396_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - R03_ADDED_SUITES,
                         'PF4A_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R03_ADDED_SUITES, retained_added - R380_ADDED_SUITES - R379_ADDED_SUITES - R396_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES,
                         'R03_NEW_SUITES_HAVE_SOURCE_BOUND_WORKSPACE_RECEIPTS')
        profiles = native_shards.measured_profiles()
        historical_names = set(profiles[0]) - set(added)
        self.assertEqual({s.name for s in suites}, historical_names | set(added),
                         'R348_MEASURED_PROFILE_COVERS_REGISTRY')
        self.assertEqual(315, len(historical_names),
                         'R348_HISTORICAL_315_UNCHANGED')
        # Main's historical 317-suite proof retains its original universe.
        # R379's 318-suite and R396's 321-suite proofs have independent
        # tests below; R17's four suites are likewise outside main's history.
        # The live six-shard proof covers all suites, including R12's seven
        # and PF-4A's two plus R03's four; no new source belongs to historical replays.
        main_history = [s for s in suites if s.name in historical_names | R380_ADDED_SUITES]
        self.assertEqual(historical_names | R380_ADDED_SUITES,
                         {s.name for s in main_history}, 'R380_HISTORICAL_317_REGISTRY')
        self.assertEqual(317, len(main_history), 'R380_HISTORICAL_317_UNCHANGED')
        # The retired three-shard relative-weight guard retains the exact
        # pre-R12/PF-4A registry. Current capacity below covers all suites on six
        # shards with the receipt-backed R12 planning costs, never 1000ms guesses.
        pre_r12_suites = [s for s in suites
                          if s.name in historical_names | (retained_added & pre_r12_known)]
        self.assertEqual(328, len(pre_r12_suites), 'R12_PREVIOUS_328_REGISTRY_RETAINED')
        # R03's base main (fa83e6ad) universe is the 324 suites before R03,
        # #427's R396 four, R12 and PF-4A; preserve that exact scope as well.
        prior_suites = [s for s in suites if s.name in historical_names
                        | (retained_added & (R380_ADDED_SUITES | R379_ADDED_SUITES | R17_ADDED_SUITES))]
        self.assertEqual(len(prior_suites), 324, 'R03_PRIOR_324_REGISTRY_UNCHANGED')
        parts = partition_suites(pre_r12_suites, 3, weights)
        self.assertEqual(Counter(s.name for part in parts for s in part),
                         Counter(s.name for s in pre_r12_suites), 'R03_HISTORICAL_WEIGHT_UNIVERSE')
        loads = [sum(weights.get(s.name, 1000) for s in part) for part in parts]
        self.assertLess(max(loads), 600000, '固定main實測配置應低於每片10分鐘，留建置與新套件餘量')
        self.assertLessEqual(max(loads)-min(loads), max(weights.values()))
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:2]):
            current_parts = partition_suites(main_history, 3)
        owners = {s.name: i for i, part in enumerate(current_parts) for s in part}
        self.assertNotEqual(owners['py:test_geo261_timber_capacity_host'],
                            owners['py:test_axiom_reader'], 'R348_SHARD_H7_READER_SEPARATION')
        profile = json.loads((Path(__file__).parent / 'native_shard_timings.json').read_text(encoding='utf-8'))
        current_weights = dict(weights)
        current_weights.update({name: row['planning_weight_ms']
                                for name, row in profile.get('supplemental', {}).items()})
        historical_parts = partition_suites(pre_r12_suites, 3, current_weights)
        self.assertEqual(Counter(s.name for part in historical_parts for s in part),
                         Counter(s.name for s in pre_r12_suites), 'R03_HISTORICAL_WEIGHT_UNIVERSE')
        current_loads = [sum(current_weights.get(s.name, 1000) for s in p) for p in historical_parts]
        self.assertLess(max(current_loads), 650000, 'R348_SHARD_SUPPLEMENTAL_PROFILE_CEILING')
        # Preserve both original measurements and the original 100s + 30s
        # historical assertion; append the failed d7515daf run without relabeling.
        runs = profile['measured_runs']
        self.assertEqual([r['source_run'].rsplit('/', 1)[-1] for r in runs[:3]],
                         ['43162989157', '43150038015', '43177620127'],
                         'R348_RETAINED_MEASURED_EVIDENCE')
        retained = json.dumps(runs[:2], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.assertEqual(hashlib.sha256(retained).hexdigest(),
                         'd62190050069eb18657d8444421d763396b253ebf226dba3e81894a4d9e88e39',
                         'R348_RETAINED_MEASURED_EVIDENCE')
        latest = json.dumps(runs[2], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.assertEqual(hashlib.sha256(latest).hexdigest(),
                         '7a232306cd33de36c7a7bf4e729e3338261cfca2d07112e8be26d771557c5963',
                         'R348_RETAINED_MEASURED_EVIDENCE')
        self.assertEqual(len(runs), 4, 'R378_RETAINED_MEASURED_EVIDENCE')
        newest = json.dumps(runs[3], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.assertEqual(hashlib.sha256(newest).hexdigest(),
                         '0152b8cb82ddb720670243c7c5f468a64a719cc4b7d6b34807d57eb20f28e5e2',
                         'R378_RETAINED_MEASURED_EVIDENCE')
        for run in runs:
            with self.subTest(source_run=run['source_run']):
                measured = {name: ms for shard in run['shards']
                            for name, ms in shard['timings_ms'].items()}
                self.assertEqual(sum(len(s['timings_ms']) for s in run['shards']), len(measured))
                self.assertEqual(len(measured), run['suite_count'])
                self.assertEqual(set(measured), historical_names,
                                 'R348_HISTORICAL_MEASURED_REGISTRY_EXACT')
                self.assertFalse(set(measured) & set(added),
                                 'R380_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertFalse(set(measured) & R379_ADDED_SUITES,
                                 'R379_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertFalse(set(measured) & R396_ADDED_SUITES,
                                 'R396_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertFalse(set(measured) & R17_ADDED_SUITES,
                                 'R17_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertFalse(set(measured) & R12_ADDED_SUITES,
                                 'R12_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertFalse(set(measured) & PF4A_ADDED_SUITES,
                                 'PF4A_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertFalse(set(measured) & R03_ADDED_SUITES,
                                 'R03_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
                self.assertEqual(set(measured) | set(added), {s.name for s in suites},
                                 'R348_MEASURED_PROFILE_COVERS_REGISTRY')
                if run in runs[:2]:
                    combined = {**measured, **added}
                    replay = [sum(combined[s.name] for s in part) for part in current_parts]
                    self.assertLess(max(replay) + 100000 + 30000, 1200000,
                                    'R348_MEASURED_RECEIPT_BUDGET')
        # Retain the original three-scenario/four-shard proof and its named
        # mutants against the frozen workflow. Do not present it as current CI.
        _, _, old_matrix = self._native_workflow(
            HISTORICAL_FOUR_NATIVE_WORKFLOW, 'R348_FOUR_NATIVE_WORKFLOW')
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:3]):
            four = partition_suites(main_history, len(old_matrix))
        for measured in profiles[:3]:
            replay = [sum(measured[s.name] for s in part) for part in four]
            self.assertLess(max(replay) + 120000 + 30000, 1200000,
                            'R348_MEASURED_RECEIPT_BUDGET: four-shard observed run')
        envelope = {s.name: max(measured[s.name] for measured in profiles[:3]) for s in main_history}
        replay = [sum(envelope[s.name] for s in part) for part in four]
        self.assertLess(max(replay) + 120000 + 30000, 1200000,
                        'R348_MEASURED_RECEIPT_BUDGET: per-suite maximum across all runs')
        self._assert_four_native_workflow()
        # The current plan uses every scenario plus independent R379/R380/R396 upper
        # bounds. Keep the strict 1200s ceiling, 120s overhead and 30s margin.
        _, _, matrix = self._native_workflow()
        six = partition_suites(suites, len(matrix))
        for measured in profiles:
            replay = [sum(measured[s.name] for s in part) for part in six]
            self.assertLess(max(replay) + 120000 + 30000, 1200000,
                            'R378_MEASURED_RECEIPT_BUDGET: six-shard observed run')
        envelope = {s.name: max(measured[s.name] for measured in profiles) for s in suites}
        replay = [sum(envelope[s.name] for s in part) for part in six]
        self.assertLess(max(replay) + 120000 + 30000, 1200000,
                        'R378_MEASURED_RECEIPT_BUDGET: per-suite maximum across all runs')
        self._assert_six_native_workflow()

    def test_r14_historical_budget(self):
        # Preserve R379's original 318-suite regression independently of the
        # current six-shard plan and main's R380 history. Every assertion is
        # executed here; the dedicated target avoids recomputing this proof
        # for unrelated main mutants, without sharing any 0/1/0 result.
        profiles = native_shards.measured_profiles()
        added = native_shards.added_suite_costs()
        self.assertEqual(R379_ADDED_SUITES,
                         set(added) & (R379_ADDED_SUITES | R380_ADDED_SUITES | R396_ADDED_SUITES | R17_ADDED_SUITES | R12_ADDED_SUITES | PF4A_ADDED_SUITES | R03_ADDED_SUITES)
                         - R380_ADDED_SUITES - R396_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R379_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        historical_names = set(profiles[0]) - set(added)
        self.assertEqual(315, len(historical_names), 'R348_HISTORICAL_315_UNCHANGED')
        selected_names = historical_names | R379_ADDED_SUITES
        suites = [s for s in run_all.build_suites() if s.name in selected_names]
        self.assertEqual(selected_names, {s.name for s in suites}, 'R379_HISTORICAL_318_REGISTRY')
        self.assertEqual(len(suites), 318, 'R379_HISTORICAL_318_REGISTRY')
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:2]):
            three = partition_suites(suites, 3)
        owners = {s.name: i for i, part in enumerate(three) for s in part}
        self.assertNotEqual(owners['py:test_geo261_timber_capacity_host'],
                            owners['py:test_axiom_reader'], 'R348_SHARD_H7_READER_SEPARATION')
        for measured in profiles[:2]:
            with self.subTest(scenario=profiles.index(measured)):
                replay = [sum(measured[s.name] for s in part) for part in three]
                self.assertLess(max(replay) + 100000 + 30000, 1200000,
                                'R348_MEASURED_RECEIPT_BUDGET: R379 historical three-shard run')
        _, _, matrix = self._native_workflow(
            HISTORICAL_FOUR_NATIVE_WORKFLOW, 'R348_FOUR_NATIVE_WORKFLOW')
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:3]):
            four = partition_suites(suites, len(matrix))
        for measured in profiles[:3]:
            replay = [sum(measured[s.name] for s in part) for part in four]
            self.assertLess(max(replay) + 120000 + 30000, 1200000,
                            'R348_MEASURED_RECEIPT_BUDGET: R379 historical four-shard run')
        envelope = {s.name: max(measured[s.name] for measured in profiles[:3]) for s in suites}
        replay = [sum(envelope[s.name] for s in part) for part in four]
        self.assertLess(max(replay) + 120000 + 30000, 1200000,
                        'R348_MEASURED_RECEIPT_BUDGET: R379 historical per-suite envelope')
        self._assert_four_native_workflow()

    def test_added_suite_provenance_rejects_named_mutations(self):
        r14_path = Path(__file__).with_name('native_shard_added_evidence_r14.json')
        self.assertTrue(r14_path.is_file(), 'R379_INDEPENDENT_SOURCE_FILE_REQUIRED')
        self.assertEqual(native_shards.ADDED_R14_EVIDENCE, r14_path)
        sources = (
            ('R380', 'ADDED_EVIDENCE', (0, 61900), (0, 12)),
            ('R379', 'ADDED_R14_EVIDENCE', (1, 4900), (2, 9)),
        )
        for label, attribute, understated, failed in sources:
            path = getattr(native_shards, attribute)
            original = json.loads(path.read_text(encoding='utf-8'))
            for mutation in ('duplicate', 'missing-job', 'understated-upper',
                             'unverified-source', 'failed-suite'):
                with self.subTest(source=label, mutation=mutation):
                    mutant = json.loads(json.dumps(original))
                    if mutation == 'duplicate':
                        mutant['observations'].append(dict(mutant['observations'][0]))
                    elif mutation == 'missing-job':
                        mutant['observations'][0]['source_job'] = ''
                    elif mutation == 'understated-upper':
                        mutant['observations'][understated[0]]['planning_upper_ms'] = understated[1]
                    elif mutation == 'unverified-source':
                        mutant['source_run'] = 'unverified'
                    else:
                        mutant['observations'][failed[0]]['passed'] = failed[1]
                    with tempfile.TemporaryDirectory(prefix='native-added-mutation-') as directory:
                        test_path = Path(directory) / 'added.json'
                        test_path.write_text(json.dumps(mutant), encoding='utf-8')
                        with mock.patch.object(native_shards, attribute, test_path):
                            with self.assertRaises(ValueError, msg=label + '_ADDED_SUITE_MUTATION_' + mutation):
                                native_shards.added_suite_costs()
        with tempfile.TemporaryDirectory(prefix='native-added-cross-source-') as directory:
            duplicate = Path(directory) / 'duplicate.json'
            duplicate.write_bytes(native_shards.ADDED_EVIDENCE.read_bytes())
            with mock.patch.object(native_shards, 'ADDED_R14_EVIDENCE', duplicate):
                with self.assertRaises(ValueError, msg='R379_ADDED_SUITE_MUTATION_cross-source-duplicate'):
                    native_shards.added_suite_costs()
        bounds = native_shards.added_suite_costs()
        self.assertEqual({'py:test_panel_fill_grid_source': 65000,
                          'node:panel_fill_grid_read_compat': 2000},
                         {name: bounds.get(name) for name in R380_ADDED_SUITES},
                         'R380_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        self.assertEqual({'node:r14_app': 2000, 'node:r14_host': 7000,
                          'py:test_r14_browser_receipt': 2000},
                         {name: bounds.get(name) for name in R379_ADDED_SUITES},
                         'R379_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        self.assertEqual(R379_ADDED_SUITES | R380_ADDED_SUITES | R396_ADDED_SUITES | R17_ADDED_SUITES | R12_ADDED_SUITES | PF4A_ADDED_SUITES | R03_ADDED_SUITES,
                         set(bounds) & (R379_ADDED_SUITES | R380_ADDED_SUITES | R396_ADDED_SUITES | R17_ADDED_SUITES | R12_ADDED_SUITES | PF4A_ADDED_SUITES | R03_ADDED_SUITES),
                         'R379_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        # R17 (PR #419) is a third independent /1 source. It passes the same
        # field, provenance, all-passed and margin checks, and must not repeat a
        # suite already supplied by R380 or R379.
        r17_path = Path(__file__).with_name('native_shard_added_evidence_r17.json')
        self.assertTrue(r17_path.is_file(), 'R17_INDEPENDENT_SOURCE_FILE_REQUIRED')
        self.assertEqual(native_shards.ADDED_R17_EVIDENCE, r17_path)
        original = json.loads(r17_path.read_text(encoding='utf-8'))
        for mutation in ('duplicate', 'missing-job', 'understated-upper',
                         'unverified-source', 'failed-suite'):
            with self.subTest(source='R17', mutation=mutation):
                mutant = json.loads(json.dumps(original))
                if mutation == 'duplicate':
                    mutant['observations'].append(dict(mutant['observations'][0]))
                elif mutation == 'missing-job':
                    mutant['observations'][0]['source_job'] = ''
                elif mutation == 'understated-upper':
                    mutant['observations'][0]['planning_upper_ms'] = 4600
                elif mutation == 'unverified-source':
                    mutant['source_run'] = 'unverified'
                else:
                    mutant['observations'][0]['passed'] = 18
                with tempfile.TemporaryDirectory(prefix='native-added-mutation-') as directory:
                    test_path = Path(directory) / 'added.json'
                    test_path.write_text(json.dumps(mutant), encoding='utf-8')
                    with mock.patch.object(native_shards, 'ADDED_R17_EVIDENCE', test_path):
                        with self.assertRaises(ValueError, msg='R17_ADDED_SUITE_MUTATION_' + mutation):
                            native_shards.added_suite_costs()
        for attribute in ('ADDED_EVIDENCE', 'ADDED_R14_EVIDENCE'):
            with tempfile.TemporaryDirectory(prefix='native-added-cross-source-') as directory:
                duplicate = Path(directory) / 'duplicate.json'
                duplicate.write_bytes(getattr(native_shards, attribute).read_bytes())
                with mock.patch.object(native_shards, 'ADDED_R17_EVIDENCE', duplicate):
                    with self.assertRaises(ValueError,
                                           msg='R17_ADDED_SUITE_MUTATION_cross-source-duplicate ' + attribute):
                        native_shards.added_suite_costs()
        self.assertEqual({'py:test_boundary_pair_host': 7000, 'node:boundary_pair_ui': 2000,
                          'node:boundary_pair_project': 2000, 'node:boundary_pair_browser_scope': 2000},
                         {name: bounds.get(name) for name in R17_ADDED_SUITES},
                         'R17_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        # PF-4A (PR #429) is a fourth independent /1 source, from the first
        # exact-head CI run whose two new suites passed but were unregistered.
        # Same field, provenance, all-passed and margin checks; no repeats.
        pf4a_path = Path(__file__).with_name('native_shard_added_evidence_pf4a.json')
        self.assertTrue(pf4a_path.is_file(), 'PF4A_INDEPENDENT_SOURCE_FILE_REQUIRED')
        self.assertEqual(native_shards.ADDED_PF4A_EVIDENCE, pf4a_path)
        original = json.loads(pf4a_path.read_text(encoding='utf-8'))
        self.assertEqual((original['source_run'], original['source_head'], original['source_checkout']),
                         ('https://github.com/ZhiQiYang/geometry-axiom/actions/runs/44014636612',
                          'ba9d4fa3424a947ffd2fc6a8904029c497f76a6e',
                          'd7c314b2bd9f37be14fe630fc2da09fcdf3b4443'), 'PF4A_SOURCE_IDENTITY')
        self.assertEqual({row['name']: (row['source_job'].rsplit('/', 1)[-1], row['discovered'],
                                        row['passed'], row['seconds_rounded'])
                          for row in original['observations']},
                         {'py:test_panel_fill_grid_transaction': ('133809508770', 13, 13, 6.4),
                          'node:panel_fill_grid_ui': ('133809508659', 13, 13, 0.1)},
                         'PF4A_SOURCE_OBSERVATIONS')
        for mutation in ('duplicate', 'missing-job', 'understated-upper',
                         'unverified-source', 'failed-suite', 'missing-suite'):
            with self.subTest(source='PF4A', mutation=mutation):
                mutant = json.loads(json.dumps(original))
                if mutation == 'duplicate':
                    mutant['observations'].append(dict(mutant['observations'][0]))
                elif mutation == 'missing-job':
                    mutant['observations'][0]['source_job'] = ''
                elif mutation == 'understated-upper':
                    mutant['observations'][0]['planning_upper_ms'] = 6400
                elif mutation == 'unverified-source':
                    mutant['source_run'] = 'unverified'
                elif mutation == 'failed-suite':
                    mutant['observations'][0]['passed'] = 12
                else:
                    mutant['observations'] = []
                with tempfile.TemporaryDirectory(prefix='native-added-mutation-') as directory:
                    test_path = Path(directory) / 'added.json'
                    test_path.write_text(json.dumps(mutant), encoding='utf-8')
                    with mock.patch.object(native_shards, 'ADDED_PF4A_EVIDENCE', test_path):
                        with self.assertRaises(ValueError, msg='PF4A_ADDED_SUITE_MUTATION_' + mutation):
                            native_shards.added_suite_costs()
        for attribute in ('ADDED_EVIDENCE', 'ADDED_R14_EVIDENCE', 'ADDED_R17_EVIDENCE'):
            with tempfile.TemporaryDirectory(prefix='native-added-cross-source-') as directory:
                duplicate = Path(directory) / 'duplicate.json'
                duplicate.write_bytes(getattr(native_shards, attribute).read_bytes())
                with mock.patch.object(native_shards, 'ADDED_PF4A_EVIDENCE', duplicate):
                    with self.assertRaises(ValueError,
                                           msg='PF4A_ADDED_SUITE_MUTATION_cross-source-duplicate ' + attribute):
                        native_shards.added_suite_costs()
        # Keep the PF-4A schema valid: a receipt-format file would be rejected
        # before the cross-source guard, so merely swapping file paths is not proof.
        mutant = json.loads(json.dumps(original))
        mutant['observations'][0]['name'] = 'py:test_space_profile_runs'
        with tempfile.TemporaryDirectory(prefix='native-pf4a-r12-duplicate-') as directory:
            changed = Path(directory) / pf4a_path.name
            changed.write_text(json.dumps(mutant), encoding='utf-8')
            with mock.patch.object(native_shards, 'ADDED_PF4A_EVIDENCE', changed):
                self.assertEqual(native_shards.added_pf4a_suite_costs()['py:test_space_profile_runs'],
                                 mutant['observations'][0]['planning_upper_ms'],
                                 'PF4A_R12_DUPLICATE_FIXTURE_VALID')
                self.assertIn('py:test_space_profile_runs', native_shards.added_r12_suite_costs(),
                              'PF4A_R12_DUPLICATE_FIXTURE_VALID')
                with self.assertRaisesRegex(ValueError, 'PF4A_NEW_SUITE_UNIQUE_ACROSS_SOURCES',
                                            msg='PF4A_ADDED_SUITE_MUTATION_cross-r12-duplicate'):
                    native_shards.added_suite_costs()
        self.assertEqual({'py:test_panel_fill_grid_transaction': 10000, 'node:panel_fill_grid_ui': 2000},
                         {name: bounds.get(name) for name in PF4A_ADDED_SUITES},
                         'PF4A_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        # Each independent source must actually change the digest that six
        # shard receipts bind; check R14 first, then R17, then the exact bytes.
        digest = native_shards.profile_digest()
        for attribute, path, marker in (('ADDED_R14_EVIDENCE', r14_path, 'R379_PROFILE_DIGEST_BINDS_R14_SOURCE'),
                                        ('ADDED_R17_EVIDENCE', r17_path, 'R17_PROFILE_DIGEST_BINDS_R17_SOURCE'),
                                        ('ADDED_PF4A_EVIDENCE', pf4a_path, 'PF4A_PROFILE_DIGEST_BINDS_PF4A_SOURCE')):
            with tempfile.TemporaryDirectory(prefix='native-digest-source-') as directory:
                changed = Path(directory) / path.name
                changed.write_bytes(path.read_bytes() + b' ')
                with mock.patch.object(native_shards, attribute, changed):
                    self.assertNotEqual(native_shards.profile_digest(), digest, marker)
        source_bytes = [path.read_bytes().replace(b'\r\n', b'\n') for path in
                        (native_shards.TIMINGS, native_shards.ADDED_EVIDENCE,
                         r14_path, native_shards.ADDED_RECEIPTS, r17_path,
                         native_shards.ADDED_R12_RECEIPTS, pf4a_path)]
        source_bytes.append(native_shards.native_shard_workspace.material(native_shards.ADDED_R03_EVIDENCE))
        if native_registry.active(run_all.ROOT):
            source_bytes.append(native_registry.source_digest(run_all.ROOT).encode('ascii'))
        self.assertEqual(hashlib.sha256(b'\0'.join(source_bytes)).hexdigest(),
                         digest, 'R379_PROFILE_DIGEST_BINDS_R14_SOURCE')

    def test_workspace_historical_budget(self):
        # Keep the PR's 321-suite/four-shard proof separate from R379's
        # 318-suite history and the current 324-suite/six-shard plan.
        profiles = native_shards.measured_profiles()
        added = native_shards.added_suite_costs()
        # Project only validated post-migration identities out of this history.
        # An unknown cost without a new/ declaration must still fail equality.
        fragment_additions = ({row['name'] for row in native_registry.load_registry(run_all.ROOT)
                               if row['order'].startswith('new/')}
                              if native_registry.active(run_all.ROOT) else set())
        self.assertEqual(R396_ADDED_SUITES, set(added) - fragment_additions - R380_ADDED_SUITES - R379_ADDED_SUITES - R17_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES - R03_ADDED_SUITES,
                         'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        historical_names = set(profiles[0]) - set(added)
        self.assertEqual(315, len(historical_names), 'R348_HISTORICAL_315_UNCHANGED')
        selected_names = historical_names | R380_ADDED_SUITES | R396_ADDED_SUITES
        suites = [s for s in run_all.build_suites() if s.name in selected_names]
        self.assertEqual(selected_names, {s.name for s in suites}, 'R396_HISTORICAL_321_REGISTRY')
        self.assertEqual(321, len(suites), 'R396_HISTORICAL_321_REGISTRY')
        _, _, matrix = self._native_workflow(
            HISTORICAL_FOUR_NATIVE_WORKFLOW, 'R348_FOUR_NATIVE_WORKFLOW')
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:3]):
            four = partition_suites(suites, len(matrix))
        for measured in profiles[:3]:
            replay = [sum(measured[s.name] for s in part) for part in four]
            self.assertLess(max(replay) + 120000 + 30000, 1200000,
                            'R348_MEASURED_RECEIPT_BUDGET: R396 historical four-shard run')
        envelope = {s.name: max(measured[s.name] for measured in profiles[:3]) for s in suites}
        replay = [sum(envelope[s.name] for s in part) for part in four]
        self.assertLess(max(replay) + 120000 + 30000, 1200000,
                        'R348_MEASURED_RECEIPT_BUDGET: R396 historical per-suite envelope')
        self._assert_four_native_workflow()

    def test_workspace_receipt_provenance_rejects_named_mutations(self):
        bounds = native_shards.added_suite_costs()
        self.assertEqual({'node:workspace_view_state': 1000,
                          'py:test_workspace_view_server': 2000,
                          'py:test_workspace_view': 3000,
                          'node:workspace_context_menu_state': 1000},
                         {name: bounds.get(name) for name in R396_ADDED_SUITES},
                         'R396_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        receipt_path = native_shards.ADDED_RECEIPTS
        receipt_bytes = receipt_path.read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(hashlib.sha256(receipt_bytes).hexdigest(),
                         '55c6c00be8984fad5bf475993e55b1808fc67c96716a46d9630e9c411ea70ff4',
                         'R396_RETAINED_ADDED_RECEIPTS')
        receipts = json.loads(receipt_bytes)
        observed = {entry['row']['name']: entry['row']
                    for source in receipts['runs'] for shard in source['shards']
                    for entry in shard['observations']}
        expected, error = run_all.load_expected()
        self.assertFalse(error)
        for name, row in observed.items():
            # The original missing-census diagnosis remains in the evidence;
            # this projection checks the new registration, never rewrites it.
            validate_rows([name], [dict(row, expected_problem='')], expected['suites'])
        modes = ('duplicate', 'duplicate-legacy', 'duplicate-r14', 'missing-job', 'wrong-run',
                 'missing-receipt-hash',
                 'understated-upper', 'failed-child', 'bool-exit', 'not-run',
                 'skipped', 'crashed', 'env-problem', 'failed-count',
                 'fake-exit-only-count', 'bool-counter', 'nan-time')
        for mutation in modes:
            with self.subTest(receipt_mutation=mutation):
                mutant = json.loads(receipt_bytes)
                source = mutant['runs'][0]
                shard = source['shards'][0]
                entry = shard['observations'][1]  # actual exit-only suite
                row = entry['row']
                if mutation == 'duplicate':
                    shard['observations'].append(dict(entry))
                elif mutation == 'duplicate-legacy':
                    row['name'] = 'py:test_panel_fill_grid_source'
                elif mutation == 'duplicate-r14':
                    row['name'] = 'node:r14_app'
                elif mutation == 'missing-job':
                    shard['source_job'] = ''
                elif mutation == 'wrong-run':
                    source['source_run'] = source['source_run'].replace('43336972629', '43336972628')
                elif mutation == 'missing-receipt-hash':
                    shard['receipt_sha256'] = ''
                elif mutation == 'understated-upper':
                    entry['planning_upper_ms'] = 1
                elif mutation == 'failed-child':
                    row['process_exit_code'] = 1
                elif mutation == 'bool-exit':
                    row['process_exit_code'] = False
                elif mutation == 'not-run':
                    row['ran'] = False
                elif mutation == 'skipped':
                    row['skipped'] = row['allowed_skips'] = 1
                elif mutation == 'crashed':
                    row['crashed'] = True
                elif mutation == 'env-problem':
                    row['env_problem'] = True
                elif mutation == 'failed-count':
                    row['failed'] = 1
                elif mutation == 'fake-exit-only-count':
                    row['total'] = 1
                elif mutation == 'bool-counter':
                    row['passed'] = True
                else:
                    row['seconds'] = float('nan')
                with tempfile.TemporaryDirectory(prefix='native-receipt-mutation-') as directory:
                    test_path = Path(directory) / 'receipts.json'
                    test_path.write_text(json.dumps(mutant), encoding='utf-8')
                    with mock.patch.object(native_shards, 'ADDED_RECEIPTS', test_path):
                        with self.assertRaisesRegex(ValueError, 'R396_',
                                                    msg='R396_ADDED_RECEIPT_' + mutation):
                            native_shards.added_suite_costs()
        wanted_digest = hashlib.sha256(
            native_shards.TIMINGS.read_bytes().replace(b'\r\n', b'\n') + b'\0' +
            native_shards.ADDED_EVIDENCE.read_bytes().replace(b'\r\n', b'\n') + b'\0' +
            native_shards.ADDED_R14_EVIDENCE.read_bytes().replace(b'\r\n', b'\n') + b'\0' +
            receipt_bytes + b'\0' +
            native_shards.ADDED_R17_EVIDENCE.read_bytes().replace(b'\r\n', b'\n') + b'\0' +
            native_shards.ADDED_R12_RECEIPTS.read_bytes().replace(b'\r\n', b'\n') + b'\0' +
            native_shards.ADDED_PF4A_EVIDENCE.read_bytes().replace(b'\r\n', b'\n') + b'\0' +
            native_shards.native_shard_workspace.material(native_shards.ADDED_R03_EVIDENCE)
            + ((b'\0' + native_registry.source_digest(run_all.ROOT).encode('ascii'))
               if native_registry.active(run_all.ROOT) else b'')).hexdigest()
        self.assertEqual(wanted_digest, native_shards.profile_digest(),
                         'R396_PROFILE_DIGEST_BINDS_ADDED_RECEIPTS')
        # A conflict resolution must not silently drop the original R396
        # withdrawals while leaving every ordinary unit test green.
        proof_source = Path(__file__).with_name('native_sharding_mutation_check.py').read_text(
            encoding='utf-8')
        proof_main = next(node for node in ast.parse(proof_source).body
                          if isinstance(node, ast.FunctionDef) and node.name == 'main')
        catalogs = [node.value for node in ast.walk(proof_main)
                    if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'mutations'
                            for target in node.targets)]
        self.assertEqual(len(catalogs), 1, 'R396_NAMED_WITHDRAWALS_RETAINED')
        catalog = ast.literal_eval(catalogs[0])
        required = {
            'R396_DROP_WORKSPACE_COSTS': ('measured-baseline', 'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS'),
            'R396_DROP_WORKSPACE_EXPECTED_ENTRIES': ('baseline', 'R396_COMPLETE_EXPECTED_REGISTRY'),
            'R396_IGNORE_EXIT_ONLY_PROCESS_FAILURE': ('workspace-provenance-baseline', 'R396_ADDED_RECEIPT_failed-child'),
            'R396_ACCEPT_BOOLEAN_EXIT_CODE': ('workspace-provenance-baseline', 'R396_ADDED_RECEIPT_bool-exit'),
            'R396_ACCEPT_EXIT_ONLY_FAKE_COUNT': ('workspace-provenance-baseline', 'R396_ADDED_RECEIPT_fake-exit-only-count'),
            'R396_ALLOW_DUPLICATE_LEGACY_COST': ('workspace-provenance-baseline', 'R396_ADDED_RECEIPT_duplicate-legacy'),
            'R396_OMIT_ADDED_RECEIPTS_FROM_DIGEST': ('workspace-provenance-baseline', 'R396_PROFILE_DIGEST_BINDS_ADDED_RECEIPTS'),
        }
        self.assertEqual({name: catalog.get(name) for name in required}, required,
                         'R396_NAMED_WITHDRAWALS_RETAINED')

    def test_r12_receipt_provenance_rejects_named_mutations(self):
        path = Path(__file__).with_name('native_shard_added_receipts_r12.json')
        self.assertEqual(getattr(native_shards, 'ADDED_R12_RECEIPTS', None), path,
                         'R12_INDEPENDENT_RECEIPT_SOURCE_REQUIRED')
        raw = path.read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'cac85f68a1eba8f5ceac2a55f740cf25b03eb54840eca93dca79d8e9d3de07cf',
                         'R12_RETAINED_ORIGINAL_CI_RECEIPTS')
        original = json.loads(raw)
        rows = [entry['row'] for shard in original['runs'][0]['shards']
                for entry in shard['observations']]
        self.assertEqual({row['name'] for row in rows}, R12_ADDED_SUITES,
                         'R12_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        bounds = native_shards.added_r12_suite_costs()
        wanted = {name: 1000 for name in R12_ADDED_SUITES}
        wanted.update({'py:test_space_profile_runs': 300000,
                       'py:test_space_profile_update': 300000})
        self.assertEqual(bounds, wanted, 'R12_ADDED_SUITE_PLANNING_UPPER_BOUNDS')
        for mutation in ('duplicate', 'missing-job', 'understated-upper',
                         'failed-child', 'bool-exit', 'not-run', 'failed-count'):
            with self.subTest(receipt_mutation=mutation):
                mutant = json.loads(raw)
                shard = mutant['runs'][0]['shards'][0]
                entry = shard['observations'][0]
                row = entry['row']
                if mutation == 'duplicate':
                    shard['observations'].append(dict(entry))
                elif mutation == 'missing-job':
                    shard['source_job'] = ''
                elif mutation == 'understated-upper':
                    entry['planning_upper_ms'] = 1
                elif mutation == 'failed-child':
                    row['process_exit_code'] = 1
                elif mutation == 'bool-exit':
                    row['process_exit_code'] = False
                elif mutation == 'not-run':
                    row['ran'] = False
                else:
                    row['failed'] = 1
                with tempfile.TemporaryDirectory(prefix='native-r12-receipt-') as directory:
                    changed = Path(directory) / path.name
                    changed.write_text(json.dumps(mutant), encoding='utf-8')
                    with mock.patch.object(native_shards, 'ADDED_R12_RECEIPTS', changed):
                        with self.assertRaises(ValueError, msg='R12_ADDED_RECEIPT_' + mutation):
                            native_shards.added_r12_suite_costs()
        with mock.patch.object(native_shards, 'ADDED_R12_RECEIPTS', native_shards.ADDED_RECEIPTS):
            with self.assertRaisesRegex(ValueError, 'R12_NEW_SUITE_UNIQUE_ACROSS_SOURCES',
                                        msg='R12_ADDED_RECEIPT_cross-source-duplicate'):
                native_shards.added_suite_costs()
        # The reciprocal collision must also reach the uniqueness guard with
        # a valid R12 receipt; the later PF-4A source owns the duplicate marker.
        mutant = json.loads(raw)
        entry = mutant['runs'][0]['shards'][0]['observations'][0]
        entry['row']['name'] = 'py:test_panel_fill_grid_transaction'
        with tempfile.TemporaryDirectory(prefix='native-r12-pf4a-duplicate-') as directory:
            changed = Path(directory) / path.name
            changed.write_text(json.dumps(mutant), encoding='utf-8')
            with mock.patch.object(native_shards, 'ADDED_R12_RECEIPTS', changed):
                self.assertEqual(
                    native_shards.added_r12_suite_costs()['py:test_panel_fill_grid_transaction'],
                    entry['planning_upper_ms'], 'R12_PF4A_DUPLICATE_FIXTURE_VALID')
                self.assertIn('py:test_panel_fill_grid_transaction', native_shards.added_pf4a_suite_costs(),
                              'R12_PF4A_DUPLICATE_FIXTURE_VALID')
                with self.assertRaisesRegex(ValueError, 'PF4A_NEW_SUITE_UNIQUE_ACROSS_SOURCES',
                                            msg='R12_ADDED_RECEIPT_cross-pf4a-duplicate'):
                    native_shards.added_suite_costs()
        digest = native_shards.profile_digest()
        with tempfile.TemporaryDirectory(prefix='native-r12-digest-') as directory:
            changed = Path(directory) / path.name
            changed.write_bytes(path.read_bytes() + b' ')
            with mock.patch.object(native_shards, 'ADDED_R12_RECEIPTS', changed):
                self.assertNotEqual(native_shards.profile_digest(), digest,
                                    'R12_PROFILE_DIGEST_BINDS_ORIGINAL_RECEIPTS')

    def test_r03_workspace_cost_provenance(self):
        self.assertTrue(hasattr(native_shards, 'ADDED_R03_EVIDENCE'), 'R03_CI_GUARD_SOURCE_REQUIRED')
        path = native_shards.ADDED_R03_EVIDENCE
        self.assertTrue(path.is_file(), 'R03_CI_GUARD_SOURCE_REQUIRED')
        import native_shard_workspace as W
        original, bounds = W.load(path)
        self.assertEqual(set(bounds), R03_ADDED_SUITES, 'R03_CI_GUARD_SOURCE_REQUIRED')
        self.assertEqual(original['source']['kind'], 'workspace', 'R03_CI_GUARD_SOURCE_REQUIRED')
        # This former main universe is immutable: its 324 suites are still
        # covered, independently of the complete current six-shard universe.
        suites = run_all.build_suites()
        # Merge with main: #427 (R396), #430 (R12) and #429 (PF-4A) entered main
        # after R03's base fa83e6ad, so they are outside that former universe.
        prior_added = R379_ADDED_SUITES | R380_ADDED_SUITES | R17_ADDED_SUITES
        historical = set(native_shards.measured_profiles()[0]) - set(native_shards.added_suite_costs())
        # R386: later fragment-only suites are outside this former universe too.
        known = (historical | prior_added | R03_ADDED_SUITES | R396_ADDED_SUITES
                 | R12_ADDED_SUITES | PF4A_ADDED_SUITES)
        former = ({s.name for s in suites} & known) - R03_ADDED_SUITES - R396_ADDED_SUITES - R12_ADDED_SUITES - PF4A_ADDED_SUITES
        self.assertEqual(former, historical | prior_added, 'R03_PRIOR_324_REGISTRY_UNCHANGED')
        self.assertEqual(len(former), 324, 'R03_PRIOR_324_REGISTRY_UNCHANGED')

        def encode(value):
            return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')

        def pin(directory, record, value):
            payload = encode(value)
            (directory / record['path']).write_bytes(payload)
            record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())

        cases = (
            ('source-pin', 'R03_CI_ARTIFACT_SHA256:source', 'R03_CI_GUARD_SOURCE_PIN'),
            ('missing-stdout', 'R03_CI_ARTIFACT_EXISTS:stdout', 'R03_CI_GUARD_STDOUT'),
            ('stdout-pin', 'R03_CI_ARTIFACT_SHA256:stdout', 'R03_CI_GUARD_STDOUT'),
            ('failed-child', 'R03_CI_ROW_PASS', 'R03_CI_GUARD_PASS'),
            ('bool-exit', 'R03_CI_ROW_PASS', 'R03_CI_GUARD_PASS'),
            ('bad-count', 'R03_CI_ROW_COUNT', 'R03_CI_GUARD_COUNT'),
            ('fake-exit-only-count', 'R03_CI_ROW_COUNT', 'R03_CI_GUARD_COUNT'),
            ('bool-time', 'R03_CI_ROW_TIME', 'R03_CI_GUARD_TIME'),
            ('nan-time', None, 'R03_CI_GUARD_TIME'),
            ('understated-upper', 'R03_CI_PLANNING_MARGIN', 'R03_CI_GUARD_MARGIN'),
            ('duplicate', 'R03_CI_DUPLICATE_OBSERVATION', 'R03_CI_GUARD_DUPLICATE'),
            ('fake-ci', 'R03_CI_WORKSPACE_SOURCE', 'R03_CI_GUARD_SOURCE_REQUIRED'),
            ('missing-native-source', 'R03_CI_BINARY_SOURCE_PIN', 'R03_CI_GUARD_BINARY_SOURCE'),
            ('missing-runtime-source', 'R03_CI_SOURCE_CLOSURE', 'R03_CI_GUARD_RUNTIME_SOURCE'),
            ('wrong-binary-fingerprint', 'R03_CI_BINARY_FINGERPRINT', 'R03_CI_GUARD_BINARY_SOURCE'),
            ('mismatched-row', 'R03_CI_ORIGINAL_ROW_BINDING', 'R03_CI_GUARD_ORIGINAL_ROW'),
            ('bool-nproc', 'R03_CI_RUNNER_IDENTITY', 'R03_CI_GUARD_RUNNER'),
            ('missing-child-report', 'R03_CI_ARTIFACT_EXISTS:child-report', 'R03_CI_GUARD_CHILD_REPORT'),
            ('missing-child-log', 'R03_CI_ARTIFACT_EXISTS:child-log', 'R03_CI_GUARD_CHILD_REPORT'),
            ('child-count-drift', 'R03_CI_CHILD_REPORT', 'R03_CI_GUARD_CHILD_REPORT'),
        )
        for mutation, error, marker in cases:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix='r03-cost-guard-') as directory:
                directory = Path(directory)
                data = json.loads(json.dumps(original))
                descriptions = [data['source']['manifest']]
                for entry in data['observations']:
                    descriptions += [entry['stdout'], entry['receipt']]
                    descriptions += [entry[key] for key in ('child_report', 'child_log') if entry[key] is not None]
                for record in descriptions:
                    target = directory / record['path']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path.parent / record['path'], target)
                entry = data['observations'][0]
                row = entry['row']
                if mutation == 'source-pin':
                    record = data['source']['manifest']
                    target = directory / record['path']
                    manifest = json.loads(target.read_text())
                    item = next(item for item in manifest['files'] if item['path'] == 'geometry-web/framing-recipes.js')
                    value = item['sha256']
                    changed = ('0' if value[0] != '0' else '1') + value[1:]
                    target.write_bytes(target.read_bytes().replace(value.encode(), changed.encode(), 1))
                elif mutation == 'missing-stdout':
                    (directory / entry['stdout']['path']).unlink()
                elif mutation == 'stdout-pin':
                    node = next(observation for observation in data['observations']
                                if observation['row']['name'].startswith('node:'))
                    target = directory / node['stdout']['path']
                    raw = target.read_bytes()
                    target.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                elif mutation == 'failed-child': row['process_exit_code'] = 1
                elif mutation == 'bool-exit': row['process_exit_code'] = False
                elif mutation == 'bad-count': row['total'] += 1
                elif mutation == 'fake-exit-only-count': row['counted'] = False
                elif mutation == 'bool-time': row['seconds'] = True
                elif mutation == 'nan-time': row['seconds'] = float('nan')
                elif mutation == 'understated-upper': entry['planning_upper_ms'] = int(row['seconds'] * 1000)
                elif mutation == 'duplicate':
                    duplicate = json.loads(json.dumps(entry))
                    for key in ('stdout', 'receipt', 'child_report', 'child_log'):
                        if duplicate[key] is None:
                            continue
                        old_path = directory / duplicate[key]['path']
                        duplicate[key]['path'] += '.duplicate'
                        shutil.copyfile(old_path, directory / duplicate[key]['path'])
                    data['observations'].append(duplicate)
                elif mutation == 'fake-ci': data['source']['kind'] = 'github-actions'
                elif mutation in ('missing-native-source', 'missing-runtime-source', 'wrong-binary-fingerprint'):
                    manifest = json.loads((directory / data['source']['manifest']['path']).read_text())
                    if mutation == 'missing-native-source':
                        manifest['files'] = [item for item in manifest['files'] if item['path'] != 'current_geometry.c']
                    elif mutation == 'missing-runtime-source':
                        manifest['files'] = [item for item in manifest['files'] if item['path'] != '公理層.md']
                    else:
                        manifest['binary']['fingerprint'] = '0' * 64
                    pin(directory, data['source']['manifest'], manifest)
                    for observation in data['observations']:
                        receipt = json.loads((directory / observation['receipt']['path']).read_text())
                        receipt['source_manifest_sha256'] = data['source']['manifest']['sha256']
                        pin(directory, observation['receipt'], receipt)
                elif mutation == 'mismatched-row':
                    receipt = json.loads((directory / entry['receipt']['path']).read_text())
                    receipt['row']['passed'] = 0
                    pin(directory, entry['receipt'], receipt)
                elif mutation == 'bool-nproc': data['source']['runner']['nproc'] = True
                elif mutation in ('missing-child-report', 'missing-child-log'):
                    key = 'child_report' if mutation == 'missing-child-report' else 'child_log'
                    (directory / entry[key]['path']).unlink()
                elif mutation == 'child-count-drift':
                    child = json.loads((directory / entry['child_report']['path']).read_text())
                    child['total'] += 1
                    pin(directory, entry['child_report'], child)
                    receipt = json.loads((directory / entry['receipt']['path']).read_text())
                    receipt['child_report_sha256'] = entry['child_report']['sha256']
                    pin(directory, entry['receipt'], receipt)
                if mutation in ('failed-child', 'bool-exit', 'bad-count', 'fake-exit-only-count', 'bool-time', 'nan-time'):
                    # Re-pin the original row deliberately: the row guard,
                    # not an unrelated stale artifact hash, must kill it.
                    receipt = json.loads((directory / entry['receipt']['path']).read_text())
                    receipt['row'] = row
                    child = json.loads((directory / entry['child_report']['path']).read_text())
                    for key in ('total', 'passed', 'failed', 'skipped'):
                        child[key] = row[key]
                    child['run'] = row['total']
                    pin(directory, entry['child_report'], child)
                    receipt['child_report_sha256'] = entry['child_report']['sha256']
                    pin(directory, entry['receipt'], receipt)
                changed = directory / path.name
                changed.write_bytes(encode(data))
                context = (self.assertRaisesRegex(ValueError, error, msg=marker) if error
                           else self.assertRaises(ValueError, msg=marker))
                with context:
                    W.costs(changed)
        for source in (native_shards._legacy_added_suite_costs, native_shards.added_r14_suite_costs,
                       native_shards.added_receipt_costs, native_shards.added_r17_suite_costs,
                       native_shards.added_r12_suite_costs, native_shards.added_pf4a_suite_costs):
            with mock.patch.object(native_shards, 'added_r03_suite_costs', return_value=source()):
                with self.assertRaisesRegex(ValueError, 'R03_CI_UNIQUE_ACROSS_SOURCES',
                                            msg='R03_CI_GUARD_CROSS_SOURCE'):
                    native_shards.added_suite_costs()
        source_bytes = [p.read_bytes().replace(b'\r\n', b'\n') for p in
                        (native_shards.TIMINGS, native_shards.ADDED_EVIDENCE,
                         native_shards.ADDED_R14_EVIDENCE, native_shards.ADDED_RECEIPTS,
                         native_shards.ADDED_R17_EVIDENCE, native_shards.ADDED_R12_RECEIPTS,
                         native_shards.ADDED_PF4A_EVIDENCE)]
        source_bytes.append(W.material(path))
        if native_registry.active(run_all.ROOT):
            source_bytes.append(native_registry.source_digest(run_all.ROOT).encode('ascii'))
        self.assertEqual(native_shards.profile_digest(), hashlib.sha256(b'\0'.join(source_bytes)).hexdigest(),
                         'R03_CI_GUARD_PROFILE_DIGEST')

    def test_invalid_shards_are_rejected(self):
        for value in ['0/2', '1/0', '4/3', '5/4', '7/6', 'a/2', '1/2/3', '-1/3']:
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                parse_shard(value)
        self.assertEqual(parse_shard('2/3'), (2, 3))
        self.assertEqual(parse_shard('4/4'), (4, 4))
        self.assertEqual(parse_shard('6/6'), (6, 6))

    def test_shards_cannot_update_or_filter_expected(self):
        for shard in ('1/3', '1/4', '1/6', '6/6'):
            for extra in [['--only', 'bridge'], ['--extra-py', 'unused.py'],
                          ['--simulate-missing', 'GEOMETRY_MODEL_BASE'], ['--update-expected']]:
                with self.subTest(shard=shard, extra=extra), mock.patch.object(run_all, 'run') as child, contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(run_all.main(['--shard', shard, *extra]), 2)
                    child.assert_not_called()

    def test_partition_rejects_missing_duplicate_and_unknown(self):
        suites = [SimpleNamespace(name=n) for n in ['a', 'b', 'c']]
        for parts in [[suites[:1], suites[2:]], [suites, suites[:1]],
                      [suites, [SimpleNamespace(name='unknown')]]]:
            with self.subTest(parts=parts), self.assertRaisesRegex(ValueError, '分片聯集'):
                validate_partition(suites, parts)

    def test_orphan_expected_entry_is_rejected_for_shard(self):
        selected = [run_all.Suite('a', 'unittest', [])]
        universe = selected + [run_all.Suite('b', 'unittest', [])]
        expected = {'suites': {n:{'mode':'count', 'count':1} for n in ['a', 'b', 'orphan']}}
        row = run_all.Row('a'); row.ran = True; row.total = row.passed = 1
        problems = run_all.compare_expected([row], selected, expected, '', False, universe=universe)
        self.assertEqual([name for name, _ in problems], ['orphan'])

    def test_selected_count_mismatch_is_rejected(self):
        suites = [run_all.Suite('a', 'unittest', [])]
        row = run_all.Row('a'); row.ran = True; row.total = row.passed = 1
        problems = run_all.compare_expected([row], suites, {'suites':{'a':{'mode':'count','count':2}}},
                                            '', False, universe=suites)
        self.assertEqual([name for name, _ in problems], ['a'])
        self.assertTrue(row.expected_problem)

    def test_cross_shard_report_requires_all_rows(self):
        row = vars(run_all.Row('a')); row.update(ran=True, total=1, passed=1, process_exit_code=0)
        expected = {'a':{'mode':'count','count':1}, 'b':{'mode':'count','count':1}}
        with self.assertRaisesRegex(ValueError, '缺少或重複suite'):
            validate_rows(['a','b'], [row], expected)
        # These are synthetic validator fixtures, not execution/timing evidence.
        suites = [run_all.Suite('fixture-%d' % i, 'unittest', []) for i in range(1, 7)]
        expected = {'suites': {s.name: {'mode': 'count', 'count': 1} for s in suites}}
        with tempfile.TemporaryDirectory(prefix='native-six-receipt-fixture-') as temp:
            directory = Path(temp)
            expected_file = directory / 'expected.json'
            expected_file.write_text(json.dumps(expected), encoding='utf-8')
            expected_sha = hashlib.sha256(expected_file.read_bytes()).hexdigest()
            # Explicit synthetic fixture weights are not production CI costs.
            fixture_profiles = [{s.name: 1 for s in suites}] * 2
            with mock.patch.object(native_shards, 'measured_profiles', return_value=fixture_profiles):
                plans = partition_suites(suites, 6)
            reports = []
            for i, part in enumerate(plans, 1):
                rows = []
                for suite in part:
                    row = vars(run_all.Row(suite.name))
                    row.update(ran=True, total=1, passed=1, process_exit_code=0)
                    rows.append(row)
                reports.append(dict(schema='geometry-native-shard/1', shard=[i, 6],
                    commit_sha='f' * 40, universe=[s.name for s in suites],
                    selected=[s.name for s in part], rows=rows, exit_code=0, seconds=1.0,
                    registry_errors=[], expected_problems=[], expected_sha256=expected_sha,
                    timings_sha256=native_shards.profile_digest()))
            def write_reports():
                for i, report in enumerate(reports, 1):
                    (directory / ('shard-%d.json' % i)).write_text(json.dumps(report), encoding='utf-8')
            def verify():
                with mock.patch.object(sys, 'argv', ['receipts', '--input', str(directory),
                        '--parts', '6', '--output', str(directory / 'complete.json')]), \
                        mock.patch.object(run_all, 'check_registry', return_value=[]), \
                        mock.patch.object(run_all, 'build_suites', return_value=suites), \
                        mock.patch.object(run_all, 'load_expected', return_value=(expected, '')), \
                        mock.patch.object(run_all, 'EXPECTED_FILE', expected_file), \
                        mock.patch.object(native_shards, 'measured_profiles', return_value=fixture_profiles), \
                        mock.patch.object(native_shard_receipts.subprocess, 'check_output', return_value='f' * 40), \
                        contextlib.redirect_stdout(io.StringIO()):
                    native_shard_receipts.main()
            write_reports()
            verify()
            self.assertEqual(json.loads((directory / 'complete.json').read_text())['executed_suites'], 6)
            for missing in (5, 6):
                (directory / ('shard-%d.json' % missing)).unlink()
                with self.assertRaisesRegex(ValueError, '缺少原始分片收據',
                                            msg='R378_SIX_NATIVE_RECEIPTS_REQUIRED'):
                    verify()
                write_reports()
            for seconds in (1200, 1200.001, float('nan'), float('inf'), -1):
                reports[5]['seconds'] = seconds
                write_reports()
                with self.assertRaisesRegex(ValueError, '分片身分／規劃／真實退出不符',
                                            msg='R378_SIX_NATIVE_RECEIPT_LIMIT'):
                    verify()
            reports[5]['seconds'] = 1199.999
            write_reports()
            verify()

    def test_cross_shard_report_rejects_inconsistent_counters(self):
        row = vars(run_all.Row('a')); row.update(ran=True, total=1, passed=0, process_exit_code=0)
        with self.assertRaisesRegex(ValueError, '計數不守恆'):
            validate_rows(['a'], [row], {'a':{'mode':'count','count':1}})

    def test_inventory_keeps_zero_assertions_and_requires_real_child_exit(self):
        suite = next(s for s in run_all.build_suites() if s.name == 'mutation:check')
        expected = {suite.name:{'mode':'exit-code-only'}}
        with tempfile.TemporaryDirectory(prefix='geometry-inventory-exit-') as temp:
            with mock.patch.object(run_all, 'LOG_DIR', Path(temp)):
                for code in [0, 1, 2, -11, None, False]:
                    with mock.patch.object(run_all, 'run_process',
                                           return_value=run_all.ProcResult(code, '', 0.0, False)):
                        observed = json.loads(json.dumps(run_all.report_row(run_all.run_suite(suite, {}, {}))))
                    self.assertEqual(observed['process_exit_code'], code)
                    self.assertIs(type(observed['process_exit_code']), type(code))
                    if type(code) is int and code == 0:
                        row = observed
                    else:
                        with self.assertRaisesRegex(ValueError, '子行程退出碼'):
                            validate_rows([suite.name], [observed], expected)
        self.assertEqual(row['process_exit_code'], 0)
        self.assertEqual([row[k] for k in ['total', 'passed', 'failed', 'skipped']], [0, 0, 0, 0])
        validate_rows([suite.name], [row], expected)
        for code in [1, 2, -11, None, False]:
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, '子行程退出碼'):
                validate_rows([suite.name], [dict(row, process_exit_code=code)], expected)
        missing = dict(row); missing.pop('process_exit_code')
        with self.assertRaisesRegex(ValueError, '子行程退出碼'):
            validate_rows([suite.name], [missing], expected)
        with self.assertRaisesRegex(ValueError, '僅退出碼'):
            validate_rows([suite.name], [dict(row, passed=1)], expected)
        script = dict(row, name='oracle:framing-selftest')
        with self.assertRaisesRegex(ValueError, '僅退出碼'):
            validate_rows([script['name']], [script], {script['name']:{'mode':'exit-code-only'}})
        validate_rows([script['name']], [dict(script, passed=1)],
                      {script['name']:{'mode':'exit-code-only'}})


if __name__ == '__main__':
    unittest.main()
