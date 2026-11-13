"""One parent test guards the reporter's synthetic outcome matrix (#118)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import argparse
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


R379_ADDED_SUITES = frozenset({'node:r14_app', 'node:r14_host', 'py:test_r14_browser_receipt'})
R380_ADDED_SUITES = frozenset({'py:test_panel_fill_grid_source', 'node:panel_fill_grid_read_compat'})


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
        self.assertEqual({
            'node:r14_app': {'mode': 'count', 'count': 7, 'unit': 'node test'},
            'node:r14_host': {'mode': 'count', 'count': 15, 'unit': 'node test'},
            'py:test_r14_browser_receipt': {'mode': 'count', 'count': 10, 'unit': 'test'},
        }, {name: expected['suites'].get(name) for name in R379_ADDED_SUITES},
                         'R379_COMPLETE_EXPECTED_REGISTRY')
        parts = run_all.partition_suites(suites, 3)
        actual = Counter(s.name for part in parts for s in part)
        self.assertEqual(actual, Counter({name:1 for name in expected['suites']}),
                         '分片必須完整涵蓋原套件清單，且每個suite恰好一次')
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
        self.assertEqual(R380_ADDED_SUITES, set(added) - R379_ADDED_SUITES,
                         'R380_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        self.assertEqual(R379_ADDED_SUITES, set(added) - R380_ADDED_SUITES,
                         'R379_NEW_SUITES_HAVE_INDEPENDENT_CI_RECEIPTS')
        historical_names = set(profiles[0]) - set(added)
        self.assertEqual({s.name for s in suites}, historical_names | set(added),
                         'R348_MEASURED_PROFILE_COVERS_REGISTRY')
        self.assertEqual(315, len(historical_names),
                         'R348_HISTORICAL_315_UNCHANGED')
        # Main's historical 317-suite proof retains its original universe.
        # R379's independent 318-suite proof has a separate test and mutation
        # target below. The live six-shard proof still covers all 320 suites.
        main_history = [s for s in suites if s.name not in R379_ADDED_SUITES]
        self.assertEqual(historical_names | R380_ADDED_SUITES,
                         {s.name for s in main_history}, 'R380_HISTORICAL_317_REGISTRY')
        with mock.patch.object(native_shards, 'measured_profiles', return_value=profiles[:2]):
            current_parts = partition_suites(main_history, 3)
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
                self.assertFalse(set(measured) & R379_ADDED_SUITES,
                                 'R379_NEW_SUITES_NOT_FORGED_IN_OLD_RUNS')
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
        # The current plan uses every scenario plus independent R379/R380 upper
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
        self.assertEqual(R379_ADDED_SUITES, set(added) - R380_ADDED_SUITES,
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
        self.assertEqual(R379_ADDED_SUITES | R380_ADDED_SUITES, set(bounds),
                         'R379_ADDED_SUITE_OBSERVED_UPPER_BOUNDS')
        source_bytes = [path.read_bytes().replace(b'\r\n', b'\n') for path in
                        (native_shards.TIMINGS, native_shards.ADDED_EVIDENCE, r14_path)]
        self.assertEqual(hashlib.sha256(b'\0'.join(source_bytes)).hexdigest(),
                         native_shards.profile_digest(), 'R379_PROFILE_DIGEST_BINDS_R14_SOURCE')

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
