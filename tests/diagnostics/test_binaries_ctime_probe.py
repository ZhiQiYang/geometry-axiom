"""Pure probe plumbing tests. No original target loop or native binary is run."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import binaries_ctime_probe as probe


def synthetic_case(outcome='pass', complete=True):
    class Synthetic(unittest.TestCase):
        def setUp(self):
            self.temp = tempfile.TemporaryDirectory(prefix='ctime-probe-selftest-')
            self.addCleanup(self.temp.cleanup)
            self.root = Path(self.temp.name)
            # The actual target registers this too. It must not remove an
            # observation context before its caller restores os.utime.
            self.addCleanup(patch.stopall)

        def runTest(self):
            path = self.root / 'neutral.bin'
            path.write_bytes(probe.EXPECTED_PAYLOAD)
            first = path.stat()
            os.utime(path, ns=(first.st_atime_ns, first.st_mtime_ns + 2_000_000_000))
            held = path.stat()
            path.write_bytes(bytes([probe.EXPECTED_PAYLOAD[0] ^ 0xff]) + probe.EXPECTED_PAYLOAD[1:])
            if complete:
                os.utime(path, ns=(held.st_atime_ns, held.st_mtime_ns))
            unrelated = self.root / 'other.bin'
            unrelated.write_bytes(b'other')
            os.utime(unrelated, None)
            if outcome == 'failure':
                self.fail('OSError not raised')
            if outcome == 'error':
                raise RuntimeError('synthetic error')
            if outcome == 'skip':
                self.skipTest('synthetic skip')
    return Synthetic()


def fake_report(records, requested=1):
    return {'iterations': records, 'summary': probe.summarize(records, requested),
            'infrastructure_errors': []}


class ProbePlumbingTests(unittest.TestCase):
    def test_observer_survives_cleanup_and_restores_patch_across_iterations(self):
        original = os.utime
        for _ in range(2):
            record = probe.run_case(synthetic_case(), observed=True)
            self.assertIs(os.utime, original)
            self.assertEqual(record['status'], 'pass')
            self.assertTrue(record['telemetry']['complete'])
            self.assertEqual(record['telemetry']['utime_calls'], 2)
            snapshots = record['telemetry']['snapshots']
            self.assertEqual(list(snapshots), list(probe.STAGES))
            self.assertEqual(snapshots['before']['st_mtime_ns'], snapshots['after_restore']['st_mtime_ns'])
            self.assertEqual(snapshots['before']['st_size'], snapshots['after_rewrite']['st_size'])
            self.assertIn('Ran 1 test', record['unittest_output'])
            self.assertTrue(record['telemetry']['payload_readback']['matches_expected_rewrite'])
            self.assertFalse(Path(record['fixture_root']).exists())

    def test_uninstrumented_control_never_constructs_observer(self):
        with patch.object(probe, 'UtimesObserver', side_effect=AssertionError('instrumented control')):
            record = probe.run_case(synthetic_case(), observed=False)
        self.assertEqual(record['status'], 'pass')
        self.assertIsNone(record['telemetry'])

    def test_failures_errors_and_skips_remain_distinct(self):
        for status in ('failure', 'error', 'skip'):
            with self.subTest(status=status):
                record = probe.run_case(synthetic_case(status), observed=True)
                self.assertEqual(record['status'], status)
                self.assertTrue(record['telemetry']['complete'])
                self.assertIn('synthetic' if status != 'failure' else 'OSError not raised',
                              record['unittest_output'])
                self.assertEqual(record['oserror_not_raised'], status == 'failure')
                self.assertTrue(record['telemetry']['payload_readback']['changed_vs_expected_original'])
                self.assertTrue(record['telemetry']['payload_readback']['matches_expected_rewrite'])

    def test_evidence_exit_codes_and_failure_rate(self):
        records = []
        for mode in ('control', 'observed'):
            record = probe.run_case(synthetic_case(), observed=mode == 'observed')
            records.append({'mode': mode, 'iteration': 1, **record})
        report = fake_report(records)
        self.assertEqual(probe.evidence_exit_code(report), 0)
        for status, code in (('failure', 1), ('error', 1), ('skip', 2)):
            records[1] = {'mode': 'observed', 'iteration': 1,
                          **probe.run_case(synthetic_case(status), observed=True)}
            report = fake_report(records)
            self.assertEqual(probe.evidence_exit_code(report), code)
            self.assertEqual(report['summary']['observed']['failure_rate'], float(status == 'failure'))
        records[1] = {'mode': 'observed', 'iteration': 1,
                      **probe.run_case(synthetic_case(complete=False), observed=True)}
        report = fake_report(records)
        self.assertEqual(probe.evidence_exit_code(report), 2)
        self.assertEqual(report['summary']['observed']['incomplete_telemetry'], 1)
        self.assertEqual(probe.evidence_exit_code(fake_report(records[:1])), 2)

    def test_raw_outputs_and_nonzero_status_are_saved(self):
        records = [{'mode': mode, 'iteration': 1,
                    **probe.run_case(synthetic_case('failure'), observed=mode == 'observed')}
                   for mode in ('control', 'observed')]
        report = fake_report(records)
        report['exit_code'] = probe.evidence_exit_code(report)
        with tempfile.TemporaryDirectory(prefix='ctime-probe-output-selftest-') as directory:
            probe.save_evidence(Path(directory), report)
            loaded = json.loads((Path(directory) / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(loaded['exit_code'], 1)
            self.assertEqual(loaded['summary']['observed']['oserror_not_raised'], 1)
            self.assertIn('AssertionError: OSError not raised',
                          (Path(directory) / 'unittest.log').read_text(encoding='utf-8'))
            self.assertIn('before_st_ctime_ns',
                          (Path(directory) / 'iterations.csv').read_text(encoding='utf-8'))

    def test_delta_distribution_never_invents_positive_resolution(self):
        self.assertEqual(probe.delta_summary([0, 0, -2])['min_positive_delta_ns_observed'], None)
        result = probe.delta_summary([0, 5, 3, -1])
        self.assertEqual((result['zero'], result['positive'], result['negative']), (1, 2, 1))
        self.assertEqual(result['min_positive_delta_ns_observed'], 3)

    def test_source_guard_matches_current_method_without_running_it(self):
        self.assertEqual(probe.target_source_metadata()['method_sha256'], probe.EXPECTED_METHOD_SHA256)

    def test_bounds(self):
        for value in ('0', '-1', '100001'):
            with self.assertRaises(argparse.ArgumentTypeError):
                probe.bounded_positive(value)
        with self.assertRaises(argparse.ArgumentTypeError):
            probe.bounded_samples('1')

    def test_cli_refuses_non_linux_and_nonempty_output_before_loading_target(self):
        with tempfile.TemporaryDirectory(prefix='ctime-probe-cli-selftest-') as directory:
            output = Path(directory) / 'evidence'
            with patch.object(probe.sys, 'platform', 'not-linux'), \
                    patch.object(probe, 'load_target') as load, \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(['--output', str(output)])
                self.assertEqual(caught.exception.code, 2)
                load.assert_not_called()
                self.assertFalse(output.exists())
            output.mkdir()
            sentinel = output / 'sentinel.txt'
            sentinel.write_text('preserve evidence')
            with patch.object(probe, 'load_target') as load, \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(['--allow-non-linux', '--output', str(output)])
                self.assertEqual(caught.exception.code, 2)
                load.assert_not_called()
                self.assertEqual(sentinel.read_text(), 'preserve evidence')

    def test_cli_source_guard_saves_error_and_never_loads_target(self):
        with tempfile.TemporaryDirectory(prefix='ctime-probe-source-selftest-') as directory:
            output = Path(directory) / 'evidence'
            with patch.object(probe, 'environment_metadata', return_value={}), \
                    patch.object(probe, 'target_source_metadata', return_value={'method_sha256': 'changed'}), \
                    patch.object(probe, 'load_target') as load, \
                    contextlib.redirect_stdout(io.StringIO()):
                code = probe.main(['--allow-non-linux', '--output', str(output), '--iterations', '1'])
            self.assertEqual(code, 2)
            load.assert_not_called()
            report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
            self.assertIn('Target method changed', report['infrastructure_errors'][0])
            self.assertEqual(report['summary']['control']['completed'], 0)

    def test_cli_synthetic_failure_saves_nonzero_and_restores_temp_base(self):
        original_tempdir = tempfile.tempdir
        module = types.SimpleNamespace(__file__=str(probe.TARGET_FILE),
                                       binaries=types.SimpleNamespace(__file__=str(probe.ROOT / 'tests' / 'binaries.py')))
        factory = lambda _name: synthetic_case('failure')
        with tempfile.TemporaryDirectory(prefix='ctime-probe-main-selftest-') as directory:
            output = Path(directory) / 'evidence'
            with patch.object(probe, 'environment_metadata', return_value={}), \
                    patch.object(probe, 'load_target', return_value=(factory, module)), \
                    contextlib.redirect_stdout(io.StringIO()):
                code = probe.main(['--allow-non-linux', '--output', str(output), '--iterations', '1',
                                   '--samples', '2', '--temp-root', directory])
            self.assertEqual(code, 1)
            self.assertEqual(tempfile.tempdir, original_tempdir)
            report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['exit_code'], 1)
            self.assertEqual(report['source_files_before'], report['source_files_after'])
            self.assertEqual(report['summary']['observed']['oserror_not_raised'], 1)
            self.assertEqual(report['ctime_measurement']['summary']['count'], 2)
            self.assertTrue((output / 'ctime-readings.csv').is_file())

    def test_cli_output_directory_error_returns_infrastructure_exit(self):
        with tempfile.TemporaryDirectory(prefix='ctime-probe-mkdir-selftest-') as directory:
            output = Path(directory) / 'evidence'
            diagnostic = io.StringIO()
            with patch.object(Path, 'mkdir', side_effect=OSError('synthetic output unavailable')), \
                    patch.object(probe, 'load_target') as load, \
                    contextlib.redirect_stderr(diagnostic):
                code = probe.main(['--allow-non-linux', '--output', str(output)])
            self.assertEqual(code, 2)
            load.assert_not_called()
            self.assertIn('Evidence incomplete', diagnostic.getvalue())

    def test_cli_save_error_returns_infrastructure_exit_and_preserves_partial(self):
        with tempfile.TemporaryDirectory(prefix='ctime-probe-save-selftest-') as directory:
            output = Path(directory) / 'evidence'
            diagnostic = io.StringIO()

            def partial_save(destination, _report):
                (destination / 'partial.txt').write_text('partial evidence')
                raise OSError('synthetic disk full')

            with patch.object(probe, 'environment_metadata', side_effect=RuntimeError('synthetic setup')), \
                    patch.object(probe, 'save_evidence', side_effect=partial_save), \
                    patch.object(probe, 'load_target') as load, \
                    contextlib.redirect_stderr(diagnostic):
                code = probe.main(['--allow-non-linux', '--output', str(output)])
            self.assertEqual(code, 2)
            load.assert_not_called()
            self.assertEqual((output / 'partial.txt').read_text(), 'partial evidence')
            self.assertIn('partial artifacts are preserved', diagnostic.getvalue())

    def test_cli_summary_output_error_returns_infrastructure_exit(self):
        class BrokenStdout(io.StringIO):
            def write(self, _text):
                raise OSError('synthetic stdout closed')

        with tempfile.TemporaryDirectory(prefix='ctime-probe-stdout-selftest-') as directory:
            output = Path(directory) / 'evidence'
            diagnostic = io.StringIO()
            module = types.SimpleNamespace(__file__=str(probe.TARGET_FILE),
                                           binaries=types.SimpleNamespace(__file__=str(probe.ROOT / 'tests' / 'binaries.py')))
            factory = lambda _name: synthetic_case()
            with patch.object(probe, 'environment_metadata', return_value={}), \
                    patch.object(probe, 'load_target', return_value=(factory, module)), \
                    contextlib.redirect_stdout(BrokenStdout()), \
                    contextlib.redirect_stderr(diagnostic):
                code = probe.main(['--allow-non-linux', '--output', str(output),
                                   '--iterations', '1', '--samples', '2'])
            self.assertEqual(code, 2)
            report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['exit_code'], 2)
            self.assertEqual(report['summary']['control']['pass'], 1)
            self.assertEqual(report['summary']['observed']['pass'], 1)
            self.assertEqual(len(report['infrastructure_errors']), 1)
            self.assertIn('Final stdout summary failed', report['infrastructure_errors'][-1])
            self.assertIn('Evidence incomplete', diagnostic.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
