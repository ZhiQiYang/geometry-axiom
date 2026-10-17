"""Non-destructive mutation receipts and preflight tests. All fixture launches are mocked."""
import concurrent.futures
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
import mutation_bridge
import run_all

ROOT = Path(__file__).resolve().parents[1]


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


class BridgeCrashHonestyTests(unittest.TestCase):
    """Task 32: a bridge process that dies under a mutant is `crashed`; only a failed assertion is `killed`.

    The oracle-driven tests run the real tests/bridge_mutation_oracle.py through mutation_bridge._test (the same call
    run_pass makes) on tiny unittest methods.  Each method talks to a throwaway Python child process through the real
    tests/_bridge.py BridgeSession, so no native bridge is built or started: the child plays "the mutated bridge"."""

    FAKE = 'bridge_crash_fake_cases'
    FAKE_SOURCE = r'''
import json
import subprocess
import sys
import unittest
from unittest import mock

from tests import _bridge

DIES = "import os,sys; sys.stdin.readline(); os._exit(7)"
DEAD_ON_ARRIVAL = "import os; os._exit(9)"
ANSWERS_WRONG = "import json,sys; [print(json.dumps({'ok': False}), flush=True) for _ in sys.stdin]"
ANSWERS_RIGHT = "import json,sys; [print(json.dumps({'ok': True}), flush=True) for _ in sys.stdin]"


def ask(child, wait_for_exit=False):
    """One command through the real BridgeSession; `child` (a Python one-liner) plays the bridge."""
    real = subprocess.Popen
    with mock.patch.object(subprocess, 'Popen', lambda argv, **kw: real([sys.executable, '-c', child], **kw)):
        session = _bridge.BridgeSession(sys.executable)
    try:
        if wait_for_exit:
            session.process.wait()
        return session.command('ping')
    finally:
        session.stop()


class Cases(unittest.TestCase):
    def test_mutant_kills_the_bridge(self):
        self.assertTrue(ask(DIES)['ok'])

    def test_mutant_kills_the_bridge_before_the_next_command(self):
        self.assertTrue(ask(DEAD_ON_ARRIVAL, wait_for_exit=True)['ok'])

    def test_mutant_changes_the_answer(self):
        self.assertTrue(ask(ANSWERS_WRONG)['ok'], 'the guard must still answer ok')

    def test_mutant_goes_unnoticed(self):
        self.assertTrue(ask(ANSWERS_RIGHT)['ok'])
'''

    CASES = ('test_mutant_kills_the_bridge', 'test_mutant_kills_the_bridge_before_the_next_command',
             'test_mutant_changes_the_answer', 'test_mutant_goes_unnoticed')

    @classmethod
    def setUpClass(cls):
        """Run the real oracle once per fake method (in parallel: each run is mostly Python start-up time)."""
        cls.temp = tempfile.TemporaryDirectory(prefix='bridge-crash-honesty-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.dir = Path(cls.temp.name)
        (cls.dir / (cls.FAKE + '.py')).write_text(cls.FAKE_SOURCE, encoding='utf-8')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GEOMETRY_', 'MUTATE_')) and k != 'PYTHONOPTIMIZE'}
        env.update(PYTHONPATH=os.pathsep.join(p for p in (str(cls.dir), os.environ.get('PYTHONPATH')) if p),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')

        def run(case):
            # exactly the call run_pass makes for a mutant trial
            return mutation_bridge._test(ROOT, Path(__file__).resolve(), ['%s.Cases.%s' % (cls.FAKE, case)], env,
                                         cls.dir / 'out', case, ROOT, cls.dir)
        with concurrent.futures.ThreadPoolExecutor(len(cls.CASES)) as pool:
            cls.receipts = dict(zip(cls.CASES, pool.map(run, cls.CASES)))

    def oracle(self, case):
        """(receipt, method id) of one fake method as the real oracle reported it."""
        receipt = self.receipts[case]
        self.assertIsNotNone(receipt['result'], 'the oracle printed no structured result: %r' % receipt)
        return receipt, '%s.Cases.%s' % (self.FAKE, case)

    # ---- (a) (b) (c): the three verdicts through the real oracle ----

    def test_a_bridge_that_dies_is_crashed_not_killed(self):
        receipt, method = self.oracle('test_mutant_kills_the_bridge')
        failure = receipt['result']['failures'][0]
        self.assertEqual(('bridge_closed', 7), (failure.get('kind'), failure.get('bridge_returncode')),
                         'the oracle must label a dead bridge with its exit status instead of leaving it looking '
                         'like an assertion failure')
        verdict = mutation_bridge.classify(receipt, [method])
        self.assertEqual('crashed', verdict,
                         'the bridge process died (exit status 7) yet the verdict is %r: a crash was counted as an '
                         'assertion kill (崩潰被算成 killed), which makes an undetected mutant look toothed' % verdict)

    def test_a_bridge_already_dead_when_the_command_is_written_is_crashed_too(self):
        receipt, method = self.oracle('test_mutant_kills_the_bridge_before_the_next_command')
        self.assertEqual('crashed', mutation_bridge.classify(receipt, [method]),
                         'a write to an already-dead bridge (BrokenPipe) must be judged as a bridge death, '
                         'not as an assertion kill or an unexplained error')
        self.assertEqual(9, receipt['result']['failures'][0].get('bridge_returncode'))

    def test_b_a_failed_assertion_is_killed(self):
        receipt, method = self.oracle('test_mutant_changes_the_answer')
        failure = receipt['result']['failures'][0]
        self.assertEqual('assertion', failure.get('kind'))
        self.assertNotIn('bridge_returncode', failure)
        self.assertEqual('killed', mutation_bridge.classify(receipt, [method]),
                         'a real assertion failure caused by the mutant behaviour must stay a kill')

    def test_c_a_passing_run_survives(self):
        receipt, method = self.oracle('test_mutant_goes_unnoticed')
        self.assertEqual([], receipt['result']['failures'])
        self.assertEqual('survived', mutation_bridge.classify(receipt, [method]))

    # ---- classify on structured receipts: what is and is not a detection ----

    METHOD = 'tests.example.Case.test_guard'

    def payload(self, failures, exit_code=1, **extra):
        row = {"exit_code": exit_code, "result": {
            "schema": "geometry-bridge-mutation-tests/1", "requested": [self.METHOD], "started": [self.METHOD],
            "total": 1, "failures": failures, "errors": [], "skipped": [],
            "expected_failures": 0, "unexpected_successes": 0}}
        row.update(extra)
        return row

    def failure(self, kind, detail='Traceback ... tests._bridge.BridgeClosed', test=METHOD, **extra):
        out = {"test": test, "detail": detail}
        if kind is not None:
            out["kind"] = kind
        out.update(extra)
        return out

    def test_a_death_without_an_exit_status_is_never_a_detection(self):
        for code in [None, "139", True, 1.5]:
            with self.subTest(bridge_returncode=code):
                row = self.payload([self.failure("bridge_closed", bridge_returncode=code)])
                self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))

    def test_an_unlabelled_closed_bridge_is_not_trusted_as_a_kill(self):
        # A receipt from before the oracle labelled failures: only the text says the bridge closed.
        row = self.payload([self.failure(None, detail="AssertionError: bridge closed: ")])
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]),
                         "text alone can make an entry less trusted, never a kill")
        row = self.payload([self.failure("surprise", detail="AssertionError")])
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))

    def test_an_assertion_failure_beside_a_crash_is_still_a_kill_and_only_it_is_credited(self):
        other = 'tests.example.Case.test_other'
        methods = [self.METHOD, other]
        row = self.payload([self.failure("bridge_closed", test=self.METHOD, bridge_returncode=-11),
                            self.failure("assertion", test=other, detail="AssertionError: u")])
        row["result"].update(requested=methods, started=methods, total=2)
        self.assertEqual("killed", mutation_bridge.classify(row, methods))
        self.assertEqual([other], mutation_bridge.failure_tests(row, "assertion"))
        self.assertEqual([self.METHOD], mutation_bridge.failure_tests(row, "crash"))

    def test_timeouts_and_exit_status_mismatches_are_blocked_never_crashed_or_killed(self):
        crash = [self.failure("bridge_closed", bridge_returncode=-9)]
        for label, row in [
                ("timed out", dict(self.payload(crash, exit_code=124), timed_out=True)),
                ("timed out with no result", {"exit_code": 124, "timed_out": True, "result": None}),
                ("oracle says incomplete (2)", self.payload(crash, exit_code=2)),
                ("oracle says clean (0)", self.payload(crash, exit_code=0)),
                ("could not launch (127)", self.payload(crash, exit_code=127))]:
            with self.subTest(label):
                self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))

    def test_build_launch_and_lookup_errors_stay_blocked(self):
        # Infrastructure the oracle reports under `errors` (unittest's error bucket) is never a detection,
        # not even next to a bridge death.
        row = self.payload([self.failure("bridge_closed", bridge_returncode=-11)])
        row["result"]["errors"] = [{"test": self.METHOD, "detail": "FileNotFoundError: bridge.exe"}]
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))

    # ---- the ledger side: --check accepts a crashed bridge record and refuses a mislabelled one ----

    def test_check_accepts_a_crashed_bridge_record_and_refuses_it_relabelled_as_killed(self):
        root = self.dir / 'repo'
        root.mkdir()
        (root / 'current_geometry.c').write_bytes(b'int anchor = 1;\n')
        m = dict(id='MB', desc='bridge ledger fixture', binary='bridge', file='current_geometry.c',
                 old='anchor = 1', new='anchor = 2', tests=[self.METHOD])
        src = mutate.Sources(root)
        judge = mutation_bridge.oracle_hash(m, root)
        sha = mutation_bridge.sha

        def survived_row(methods):
            return {"exit_code": 0, "stdout_sha256": '1' * 64, "stderr_sha256": '2' * 64,
                    "command": ["<python>", "-B", "tests/bridge_mutation_oracle.py", "<bridge>", *methods],
                    "result": {"schema": "geometry-bridge-mutation-tests/1", "requested": methods, "started": methods,
                               "total": len(methods), "failures": [], "errors": [], "skipped": [],
                               "expected_failures": 0, "unexpected_successes": 0}}

        def identity(text, exe):
            return {"freshness": "fresh", "exe_sha256": exe * 64, "sidecar_sha256": '3' * 64,
                    "sidecar": {"exe_sha256": exe * 64, "files": {"current_geometry.c": sha(text)}}}

        build = {"exit_code": 0, "stdout_sha256": '4' * 64, "stderr_sha256": '5' * 64}
        crash = survived_row(m["tests"])
        crash.update(exit_code=1)
        crash["result"]["failures"] = [self.failure("bridge_closed", test=self.METHOD, bridge_returncode=-11)]
        evidence = {"schema": "geometry-bridge-mutation-execution/1", "head": 'a' * 40, "platform": os.name,
                    "tool_sha256": mutate.tool_hash(), "oracle_sha256": judge,
                    "methods": m["tests"], "restored_methods": mutation_bridge.RESTORED,
                    "baseline_build": build, "baseline_identity": identity(b'int anchor = 1;\n', 'b'),
                    "baseline": survived_row(mutation_bridge.RESTORED),
                    "mutant_build": build, "mutant_identity": identity(b'int anchor = 2;\n', 'c'), "mutant": crash,
                    "restored_build": build, "restored_identity": identity(b'int anchor = 1;\n', 'b'),
                    "restored": survived_row(mutation_bridge.RESTORED), "byte_restored": True}

        def check(verdict, **fields):
            rec = mutate.make_record(m, src, verdict, 'ledger fixture', '2026-10-17', judge, execution=evidence, **fields)
            results = self.dir / 'results.json'
            mutate.save_records(results, {m['id']: rec})
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch.object(mutate, 'MUT_ROOT', self.dir / 'cache'):
                code = mutate.check_pass([m], root=root, results_path=results, oracle=judge)
            return code, out.getvalue()

        code, text = check('crashed', crashed_on=[self.METHOD])
        self.assertEqual(0, code, text)
        self.assertIn('crashed 1', text)
        self.assertNotIn('STALE', text)
        code, text = check('killed', killed_by=[self.METHOD])
        self.assertEqual(1, code, 'a bridge death recorded as killed must not pass --check')
        self.assertIn('contradicts', text)
        code, text = check('crashed', crashed_on=['tests.example.Case.test_other'])
        self.assertEqual(1, code, 'crashed_on must name the tests whose bridge really died')
        self.assertIn('crashed_on', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
