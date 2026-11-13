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
import contextlib
import io
import json
import hashlib
import re
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import run_all
import native_shards
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
        for line in ('    name: native complete coverage', '    needs: native', '    if: always()'):
            self.assertIn('\n' + line + '\n', '\n' + complete, marker)
        command = next((line.strip() for line in complete.splitlines()
                        if line.strip().startswith('run: python3 -B tests/native_shard_receipts.py ')), '')
        self.assertIn("--parts 6 --output ", command, marker)

    def test_partition_covers_actual_suite_registry_once(self):
        suites = run_all.build_suites()
        expected, error = run_all.load_expected()
        self.assertFalse(error)
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

    def test_profile_balances_measured_work(self):
        suites = run_all.build_suites()
        weights = timing_weights()
        parts = partition_suites(suites, 3, weights)
        loads = [sum(weights.get(s.name, 1000) for s in part) for part in parts]
        self.assertLess(max(loads), 600000, '固定main實測配置應低於每片10分鐘，留建置與新套件餘量')
        self.assertLessEqual(max(loads)-min(loads), max(weights.values()))
        # Keep the historical 224-row and supplemental relative-weight checks.
        # Freeze the original two-run/three-shard regression and its two
        # mutation proofs. It is historical coverage, not the current CI plan.
        profiles = native_shards.measured_profiles()
        added = native_shards.added_suite_costs()
        legacy_added = {row['name']: row['planning_upper_ms'] for row in json.loads(
            native_shards.ADDED_EVIDENCE.read_text(encoding='utf-8'))['observations']}
        self.assertEqual({'py:test_panel_fill_grid_source',
                          'node:panel_fill_grid_read_compat'}, set(legacy_added),
                         'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual({'py:test_panel_fill_grid_source': 65000,
                          'node:panel_fill_grid_read_compat': 2000},
                         {name: added.get(name) for name in legacy_added},
                         'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual({'node:workspace_view_state', 'py:test_workspace_view_server',
                          'py:test_workspace_view', 'node:workspace_context_menu_state'},
                         set(added) - set(legacy_added),
                         'R396_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        historical_names = set(profiles[0]) - set(added)
        self.assertEqual({s.name for s in suites}, historical_names | set(added),
                         'R348_MEASURED_PROFILE_COVERS_REGISTRY')
        self.assertEqual(315, len(historical_names),
                         'R348_HISTORICAL_315_UNCHANGED')
        # Freeze the original 317-suite historical regression: later suites
        # were not present in its evidence. All 321 suites are budgeted below
        # in the current four-shard plan with independently sourced costs.
        historical_suites = [suite for suite in suites
                             if suite.name in historical_names | set(legacy_added)]
        self.assertEqual(317, len(historical_suites), 'R380_HISTORICAL_317_UNCHANGED')
        historical_profiles = [{name: ms for name, ms in measured.items()
                                if name in historical_names | set(legacy_added)}
                               for measured in profiles[:2]]
        with mock.patch.object(native_shards, 'measured_profiles', return_value=historical_profiles):
            current_parts = partition_suites(historical_suites, 3)
        owners = {s.name: i for i, part in enumerate(current_parts) for s in part}
        self.assertNotEqual(owners['py:test_geo261_timber_capacity_host'],
                            owners['py:test_axiom_reader'], 'R348_SHARD_H7_READER_SEPARATION')
        profile = json.loads((Path(__file__).parent / 'native_shard_timings.json').read_text(encoding='utf-8'))
        current_weights = dict(weights)
        current_weights.update({name: row['planning_weight_ms']
                                for name, row in profile.get('supplemental', {}).items()})
        historical_parts = partition_suites(suites, 3, current_weights)
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
                self.assertEqual(set(measured) | set(added), {s.name for s in suites},
                                 'R348_MEASURED_PROFILE_COVERS_REGISTRY')
                if run in runs[:2]:
                    combined = {**measured, **legacy_added}
                    replay = [sum(combined[s.name] for s in part) for part in current_parts]
                    self.assertLess(max(replay) + 100000 + 30000, 1200000,
                                    'R348_MEASURED_RECEIPT_BUDGET')
        # Retain the original three-scenario/four-shard proof and its named
        # mutants against the frozen workflow. Do not present it as current CI.
        _, _, old_matrix = self._native_workflow(
            HISTORICAL_FOUR_NATIVE_WORKFLOW, 'R348_FOUR_NATIVE_WORKFLOW')
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:3]):
            four = partition_suites(suites, len(old_matrix))
        for measured in profiles[:3]:
            replay = [sum(measured[s.name] for s in part) for part in four]
            self.assertLess(max(replay) + 120000 + 30000, 1200000,
                            'R348_MEASURED_RECEIPT_BUDGET: four-shard observed run')
        envelope = {s.name: max(measured[s.name] for measured in profiles[:3]) for s in suites}
        replay = [sum(envelope[s.name] for s in part) for part in four]
        self.assertLess(max(replay) + 120000 + 30000, 1200000,
                        'R348_MEASURED_RECEIPT_BUDGET: per-suite maximum across all runs')
        self._assert_four_native_workflow()
        # The current plan uses every scenario plus the independent R380 upper
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

    def test_added_suite_provenance_rejects_named_mutations(self):
        path = native_shards.ADDED_EVIDENCE
        original = json.loads(path.read_text(encoding='utf-8'))
        for mutation in ('duplicate', 'missing-job', 'understated-upper',
                         'unverified-source', 'failed-suite'):
            with self.subTest(mutation=mutation):
                mutant = json.loads(json.dumps(original))
                if mutation == 'duplicate':
                    mutant['observations'].append(dict(mutant['observations'][0]))
                elif mutation == 'missing-job':
                    mutant['observations'][0]['source_job'] = ''
                elif mutation == 'understated-upper':
                    mutant['observations'][0]['planning_upper_ms'] = 61900
                elif mutation == 'unverified-source':
                    mutant['source_run'] = 'unverified'
                else:
                    mutant['observations'][0]['passed'] = 12
                with tempfile.TemporaryDirectory(prefix='native-added-mutation-') as directory:
                    test_path = Path(directory) / 'added.json'
                    test_path.write_text(json.dumps(mutant), encoding='utf-8')
                    with mock.patch.object(native_shards, 'ADDED_EVIDENCE', test_path):
                        with self.assertRaises(ValueError, msg='R380_ADDED_SUITE_MUTATION_' + mutation):
                            native_shards.added_suite_costs()
        self.assertEqual({'py:test_panel_fill_grid_source': 65000,
                          'node:panel_fill_grid_read_compat': 2000,
                          'node:workspace_view_state': 1000,
                          'py:test_workspace_view_server': 2000,
                          'py:test_workspace_view': 3000,
                          'node:workspace_context_menu_state': 1000},
                         native_shards.added_suite_costs(),
                         'R380_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
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
        modes = ('duplicate', 'duplicate-legacy', 'missing-job', 'wrong-run', 'missing-receipt-hash',
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
            receipt_bytes).hexdigest()
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
            'R396_IGNORE_EXIT_ONLY_PROCESS_FAILURE': ('provenance-baseline', 'R396_ADDED_RECEIPT_failed-child'),
            'R396_ACCEPT_BOOLEAN_EXIT_CODE': ('provenance-baseline', 'R396_ADDED_RECEIPT_bool-exit'),
            'R396_ACCEPT_EXIT_ONLY_FAKE_COUNT': ('provenance-baseline', 'R396_ADDED_RECEIPT_fake-exit-only-count'),
            'R396_ALLOW_DUPLICATE_LEGACY_COST': ('provenance-baseline', 'R396_ADDED_RECEIPT_duplicate-legacy'),
            'R396_OMIT_ADDED_RECEIPTS_FROM_DIGEST': ('provenance-baseline', 'R396_PROFILE_DIGEST_BINDS_ADDED_RECEIPTS'),
        }
        self.assertEqual({name: catalog.get(name) for name in required}, required,
                         'R396_NAMED_WITHDRAWALS_RETAINED')

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
