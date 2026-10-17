"""Non-destructive mutation receipts and preflight tests. All fixture launches are mocked."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import mutate
import run_all


class MutationFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mutation-freshness-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'current_geometry.c').write_text('int anchor = 1;\n')
        self.m = dict(id='MF', desc='public fixture', old='anchor = 1', new='anchor = 2')
        self.src = mutate.Sources(self.root)
        self.results = self.root / 'results.json'
        self.cache = self.root / 'cache'
        patcher = mock.patch.object(mutate, 'MUT_ROOT', self.cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.oracle = mutate.oracle_hash()

    def proc(self, fail=False, crash=False):
        cases = [dict(scene=t['scene'], status='pass', detail='OK') for t in mutate.TESTS]
        if fail:
            cases[0].update(status='fail', detail='FAIL public assertion')
        if crash:
            cases[0].update(status='infrastructure', detail='INFRA abnormal executable exit -11: public crash')
        counts = {k: sum(c['status'] == k for c in cases) for k in ('pass', 'fail', 'infrastructure')}
        result = dict(schema='geometry-native-tests/1', total=len(cases), counts=counts, cases=cases)
        return subprocess.CompletedProcess([], 2 if crash else 1 if fail else 0,
                                           'GEOMETRY_TEST_RESULT ' + json.dumps(result), '')

    def record(self, verdict='killed'):
        crash = verdict == 'crashed'
        p = self.proc(fail=verdict == 'killed', crash=crash)
        evidence = dict(schema='geometry-mutation-execution/1', head='a' * 40, platform=os.name,
                        tool_sha256=mutate.tool_hash(), compile_exit_code=0,
                        compile_sha256=mutate.compile_hash(), compile_command=mutate.portable_compile_command(),
                        test_command=['<python>', 'tests/run_tests.py', '<binary>'],
                        exe_sha256='b' * 64, baseline_exe_sha256='c' * 64,
                        baseline=mutate.attempt_receipt(self.proc(), self.root),
                        attempts=[mutate.attempt_receipt(p, self.root)] * (mutate.RUN_RETRIES if crash else 1))
        return mutate.make_record(self.m, self.src, verdict, self.m.get(verdict, 'public assertion'),
                                  '2026-10-04', self.oracle,
                                  killed_by=mutate.failed_scenes(p) if verdict == 'killed' else None,
                                  crashed_on=list(mutate.access_violation_scenes(p)) if crash else None,
                                  execution=evidence)

    def check(self, rec):
        mutate.save_records(self.results, {self.m['id']: rec})
        with contextlib.redirect_stdout(io.StringIO()):
            return mutate.check_pass([self.m], root=self.root, results_path=self.results, oracle=self.oracle)

    def seal(self, rec):
        rec['record_sha256'] = mutate.record_hash(rec)
        return rec

    def test_portable_receipt_accepts_clean_checkout_without_temp_binary(self):
        self.assertEqual(self.check(self.record()), 0)
        self.assertFalse(self.cache.exists())

    def test_source_change_and_restore(self):
        rec = self.record()
        source = self.root / 'current_geometry.c'
        source.write_text('int anchor = 1; /* changed */\n')
        self.assertEqual(self.check(rec), 1)
        source.write_text('int anchor = 1;\n')
        self.assertEqual(self.check(rec), 0)

    def test_missing_and_legacy_receipts_stay_stale(self):
        rec = self.record()
        rec.pop('execution')
        self.assertEqual(self.check(self.seal(rec)), 1)
        rec.pop('record_sha256')
        self.assertEqual(self.check(rec), 1)

    def test_result_edits_are_rejected(self):
        original = self.record()
        for field, value in [('why', 'edited'), ('verdict', 'equivalent'), ('killed_by', ['wrong.scene']),
                             ('execution', {})]:
            with self.subTest(field=field):
                rec = copy.deepcopy(original)
                rec[field] = value
                self.assertEqual(self.check(rec), 1)

    def test_resealed_contradictory_verdict_is_rejected(self):
        rec = self.record()
        rec['execution']['attempts'] = [mutate.attempt_receipt(self.proc(), self.root)]
        self.assertEqual(self.check(self.seal(rec)), 1)

    def test_incomplete_timeout_and_shell_failure_never_kill(self):
        for receipt in [dict(exit_code=1, result=None, stdout_sha256='a' * 64, stderr_sha256='b' * 64),
                        mutate.attempt_receipt(subprocess.CompletedProcess([], 2, 'Traceback', ''), self.root)]:
            rec = self.record()
            rec['execution']['attempts'] = [receipt]
            self.assertEqual(self.check(self.seal(rec)), 1)

    def test_compile_and_oracle_commands_must_match(self):
        for field, value in [('compile_command', ['wrong']), ('compile_sha256', 'a' * 64),
                             ('compile_exit_code', 1), ('test_command', ['other']),
                             ('tool_sha256', 'a' * 64), ('head', 'unknown')]:
            with self.subTest(field=field):
                rec = self.record()
                rec['execution'][field] = value
                self.assertEqual(self.check(self.seal(rec)), 1)

    def test_baseline_must_pass_before_mutant_verdict_counts(self):
        rec = self.record()
        rec['execution']['baseline'] = mutate.attempt_receipt(self.proc(fail=True), self.root)
        self.assertEqual(self.check(self.seal(rec)), 1)

    def test_binary_tamper_same_size_and_mtime_rejects_without_execution(self):
        rec = self.record()
        exe = self.cache / self.m['id'] / '_mut.exe'
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b'harmless fixture bytes')
        mutate.write_sidecar(exe, mutate.mutant_fingerprint(self.m, self.src))
        rec['execution']['exe_sha256'] = mutate._file_sha(exe)
        self.seal(rec)
        self.assertEqual(self.check(rec), 0)
        before = exe.stat()
        exe.write_bytes(b'Harmless fixture bytes')
        os.utime(exe, ns=(before.st_atime_ns, before.st_mtime_ns))
        with mock.patch.object(subprocess, 'run', side_effect=AssertionError('fixture must not execute')):
            self.assertEqual(self.check(rec), 1)
        self.assertEqual(exe.stat().st_size, before.st_size)
        self.assertEqual(exe.stat().st_mtime_ns, before.st_mtime_ns)

    def test_binary_replacement_with_valid_new_sidecar_still_rejects_old_result(self):
        rec = self.record()
        exe = self.cache / self.m['id'] / '_mut.exe'
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b'different harmless bytes')
        mutate.write_sidecar(exe, mutate.mutant_fingerprint(self.m, self.src))
        self.assertEqual(mutate.cache_state(exe, mutate.mutant_fingerprint(self.m, self.src)), 'hit')
        self.assertEqual(self.check(rec), 1)

    def test_bad_sidecar_and_atomic_failure_do_not_publish_identity(self):
        exe = self.root / 'fixture'
        exe.write_bytes(b'fixture')
        for data in [[], None, 'bad', {'fingerprint': {}}]:
            mutate.sidecar_path(exe).write_text(json.dumps(data))
            self.assertEqual(mutate.cache_state(exe, {}), 'stale')
        mutate.sidecar_path(exe).unlink()
        with mock.patch.object(mutate.binaries.os, 'replace', side_effect=OSError('public atomic failure')):
            with self.assertRaises(OSError):
                mutate.write_sidecar(exe, {})
        self.assertFalse(mutate.sidecar_path(exe).exists())
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_crashed_requires_all_retries_same_fixture_and_exit(self):
        rec = self.record('crashed')
        self.assertEqual(self.check(rec), 0)
        rec['execution']['attempts'].pop()
        self.assertEqual(self.check(self.seal(rec)), 1)

    def test_equivalence_proof_and_current_execution_both_required(self):
        self.m['equivalent'] = 'public redundancy proof'
        rec = self.record('equivalent')
        self.assertEqual(self.check(rec), 0)
        self.m['equivalent'] = 'changed proof'
        self.assertEqual(self.check(rec), 1)

    def test_existing_selftest_floor(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(mutate.selftest(), 0)
        self.assertIn('SELFTEST OK (113 checks)', out.getvalue())

    def test_full_runner_includes_strict_mutation_check(self):
        suite = next(s for s in run_all.build_suites() if s.name == 'mutation:check')
        self.assertEqual(suite.cmd, [run_all.sys.executable, str(run_all.HERE / 'mutate.py'), '--check'])
        self.assertFalse(suite.counted)

    def run_fixture(self, mode='killed'):
        oracle_calls = []
        tool_changed = False
        tool_sha = mutate.tool_hash()

        def command(cmd, cwd, timeout=120):
            nonlocal tool_changed
            if cmd[0] == 'git':
                return subprocess.CompletedProcess(cmd, 0, 'a' * 40 + '\n', '')
            if '-o' in cmd or (cmd[0] == 'cmd' and Path(cmd[2]).name == '_cl.bat'):
                target = Path(cmd[cmd.index('-o') + 1] if '-o' in cmd else cmd[-1])
                if mode == 'compilefail' and target.name == '_mut.exe':
                    return subprocess.CompletedProcess(cmd, 1, '', 'public compiler failure')
                target.write_bytes(b'harmless compiled fixture')
                return subprocess.CompletedProcess(cmd, 0, '', '')
            exe = Path(cmd[-1])
            oracle_calls.append(exe.name)
            if exe.name == 'baseline.exe':
                if mode == 'toolchange':
                    tool_changed = True
                return self.proc()
            if mode == 'retrytamper':
                return subprocess.CompletedProcess(cmd, 2, 'public infrastructure failure', '')
            if mode == 'sourcechange':
                (self.root / 'current_geometry.c').write_text('int anchor = 1; /* edit */\n')
            return self.proc(fail=True)

        def wait(_seconds):
            exe = self.cache / self.m['id'] / '_mut.exe'
            before = exe.stat()
            data = exe.read_bytes()
            exe.write_bytes(bytes([data[0] ^ 1]) + data[1:])
            os.utime(exe, ns=(before.st_atime_ns, before.st_mtime_ns))

        with mock.patch.object(mutate, 'run_cmd', side_effect=command), \
                mock.patch.object(mutate.time, 'sleep', side_effect=wait), \
                mock.patch.object(mutate, 'tool_hash', side_effect=lambda: 'd' * 64 if tool_changed else tool_sha), \
                contextlib.redirect_stdout(io.StringIO()):
            code = mutate.run_pass([self.m], set(), root=self.root, results_path=self.results, oracle=self.oracle)
        return code, mutate.load_records(self.results).get(self.m['id']), oracle_calls

    def test_real_run_pass_publishes_traceable_assertion_receipt(self):
        code, rec, launches = self.run_fixture()
        self.assertEqual(code, 0)
        self.assertEqual(rec['verdict'], 'killed')
        self.assertEqual(launches, ['baseline.exe', '_mut.exe'])
        self.assertEqual(self.check(rec), 0)

    def test_real_retry_rechecks_identity_before_second_launch(self):
        code, rec, launches = self.run_fixture('retrytamper')
        self.assertEqual(code, 2)
        self.assertEqual(rec['verdict'], 'blocked')
        self.assertEqual(launches, ['baseline.exe', '_mut.exe'])
        self.assertIn('changed before launch', rec['why'])

    def test_source_change_during_oracle_never_publishes_killed(self):
        code, rec, _ = self.run_fixture('sourcechange')
        self.assertEqual(code, 2)
        self.assertEqual(rec['verdict'], 'blocked')
        self.assertIn('changed during oracle', rec['why'])

    def test_compile_failure_is_invalid_without_mutant_launch(self):
        code, rec, launches = self.run_fixture('compilefail')
        self.assertEqual(code, 1)
        self.assertEqual(rec['verdict'], 'invalid')
        self.assertEqual(launches, ['baseline.exe'])

    def test_runner_rejects_missing_results_without_launching_mutants(self):
        suite = next(s for s in run_all.build_suites() if s.name == 'mutation:check')
        with mock.patch.object(run_all, 'LOG_DIR', self.root / 'logs'), mock.patch.object(run_all, 'HERE', self.root):
            row = run_all.run_suite(suite, dict(os.environ, MUTATE_RESULTS=str(self.results)), {})
        self.assertTrue(row.ran)
        self.assertEqual(row.failed, 1)
        self.assertEqual(row.total, 0)

    def test_runner_pins_versioned_results_instead_of_inherited_override(self):
        suite = next(s for s in run_all.build_suites() if s.name == 'mutation:check')
        probe = mock.Mock(return_value=run_all.ProcResult(1, 'STALE public probe', 0, False))
        with mock.patch.object(run_all, 'LOG_DIR', self.root / 'logs'), \
                mock.patch.object(run_all, 'run_process', probe):
            row = run_all.run_suite(suite, dict(os.environ, MUTATE_RESULTS='untrusted override'), {})
        self.assertEqual(probe.call_args.args[1]['MUTATE_RESULTS'], str(run_all.HERE / 'mutants_results.json'))
        self.assertEqual(row.failed, 1)
        probe.return_value = run_all.ProcResult(2, 'BLOCKED public environment probe', 0, False)
        with mock.patch.object(run_all, 'LOG_DIR', self.root / 'logs'), \
                mock.patch.object(run_all, 'run_process', probe):
            blocked = run_all.run_suite(suite, os.environ.copy(), {})
        self.assertEqual(blocked.failed, 0)
        self.assertTrue(blocked.env_problem)

    def test_failed_inventory_gate_cannot_update_census(self):
        suite = next(s for s in run_all.build_suites() if s.name == 'mutation:check')
        row = run_all.Row(suite.name, suite.counted)
        row.ran, row.failed = True, 1
        with mock.patch.object(run_all, 'EXPECTED_FILE', self.root / 'expected.json'), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(run_all.update_expected([row], [suite], []))
        self.assertFalse((self.root / 'expected.json').exists())

    def test_identity_publication_failure_is_blocked_not_compiler_invalid(self):
        def compile_fixture(_mutant, exe):
            exe.write_bytes(b'harmless fixture')
            return True, ''
        with mock.patch.object(mutate.binaries.os, 'replace', side_effect=OSError('public write failure')):
            status, exe, why = mutate.prepare_mutant_exe(self.m, self.src, self.cache / self.m['id'], compile_fixture)
        self.assertEqual(status, 'blocked')
        self.assertIn('identity', why)
        self.assertFalse(mutate.sidecar_path(exe).exists())

    def test_tool_change_during_baseline_cannot_certify_new_tool(self):
        code, rec, launches = self.run_fixture('toolchange')
        self.assertEqual(code, 2)
        self.assertIsNone(rec)
        self.assertEqual(launches, ['baseline.exe'])


class BridgeMutationHonestyTests(unittest.TestCase):
    def payload(self, failures=None):
        return {"exit_code": 1 if failures else 0, "result": {
            "schema": "geometry-bridge-mutation-tests/1", "requested": ["tests.example.Case.test_guard"],
            "started": ["tests.example.Case.test_guard"], "total": 1,
            "failures": failures or [], "errors": [], "skipped": [],
            "expected_failures": 0, "unexpected_successes": 0}}

    def classify(self, receipt):
        import mutation_bridge
        return mutation_bridge.classify(receipt, ["tests.example.Case.test_guard"])

    def test_two_real_failing_subtests_are_a_kill(self):
        row = self.payload([{"test": "tests.example.Case.test_guard (axis='u')", "detail": "AssertionError: u"},
                            {"test": "tests.example.Case.test_guard (axis='v')", "detail": "AssertionError: v"}])
        self.assertEqual("killed", self.classify(row))

    def test_infrastructure_error_never_counts_as_a_kill(self):
        row = self.payload([{"test": "tests.example.Case.test_guard", "detail": "AssertionError"}])
        row["result"]["errors"] = [{"test": "tests.example.Case.test_guard", "detail": "compiler unavailable"}]
        self.assertEqual("blocked", self.classify(row))

    def test_missing_method_or_skip_never_counts_as_success(self):
        for key, value in [("started", []), ("total", 0), ("skipped", [{"reason": "no bridge"}])]:
            with self.subTest(key=key):
                row = self.payload(); row["result"][key] = value
                self.assertEqual("blocked", self.classify(row))

    def test_assertion_result_and_actual_exit_must_agree(self):
        row = self.payload([{"test": "tests.example.Case.test_guard", "detail": "AssertionError"}])
        for code in [0, 2, -11, True]:
            with self.subTest(code=code):
                row["exit_code"] = code
                self.assertEqual("blocked", self.classify(row))

    def test_failure_must_name_the_requested_method(self):
        for failure in [{}, {"test": "tests.other.Case.test_other", "detail": "AssertionError"}]:
            self.assertEqual("blocked", self.classify(self.payload([failure])))

    def test_judge_hash_tracks_shared_python_harness_and_method_selection(self):
        import mutation_bridge
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "tests").mkdir()
            helper = root / "tests/_bridge.py"; helper.write_text("SOURCE = 1\n")
            m = {"tests": ["tests.example.Case.test_guard"]}
            before = mutation_bridge.oracle_hash(m, root)
            helper.write_text("SOURCE = 2\n")
            self.assertNotEqual(before, mutation_bridge.oracle_hash(m, root))
            after = mutation_bridge.oracle_hash(m, root)
            m["tests"] = ["tests.example.Case.test_other"]
            self.assertNotEqual(after, mutation_bridge.oracle_hash(m, root))

    def test_bridge_source_closure_includes_preview_serializer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "current_geometry.c").write_text("int core;\n")
            (root / "geometry-web").mkdir()
            (root / "geometry-web/web_bridge.c").write_text('#include "engineering_bridge.inc"\n')
            serializer = root / "geometry-web/engineering_bridge.inc"; serializer.write_text("int preview = 1;\n")
            before = mutate.Sources(root).closure
            serializer.write_text("int preview = 2;\n")
            self.assertNotEqual(before, mutate.Sources(root).closure)

    def test_bridge_method_selection_is_part_of_mutant_definition(self):
        m = dict(file="geometry-web/engineering_bridge.inc", old="a", new="b", binary="bridge", tests=["a"])
        before = mutate.mutant_key(m)
        m["tests"] = ["b"]
        self.assertNotEqual(before, mutate.mutant_key(m))


if __name__ == '__main__':
    unittest.main(verbosity=2)
