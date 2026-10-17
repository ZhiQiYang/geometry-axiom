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
import types
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
    """Task 32: only a failed assertion kills a bridge mutant; a bridge that dies is `crashed` only by the core's rule
    (AGENTS.md: the same tests die of an access violation in RUN_RETRIES consecutive runs), otherwise `blocked`.

    The oracle-driven tests run the real tests/bridge_mutation_oracle.py through mutation_bridge._test (the same call
    run_pass makes, repeated by the real mutation_bridge.run_trials) on tiny unittest methods.  Each method talks to a
    throwaway Python child process through the real tests/_bridge.py BridgeSession, so no native bridge is built or
    started: the child plays "the mutated bridge"."""

    FAKE = 'bridge_crash_fake_cases'
    FAKE_SOURCE = r'''
import json
import subprocess
import sys
import unittest
from unittest import mock

from tests import _bridge

SEGFAULT = ("import os,sys; sys.stdin.readline(); "
            "(os._exit(-1073741819) if os.name == 'nt' else os.kill(os.getpid(), 11))")
EXIT_7 = "import os,sys; sys.stdin.readline(); os._exit(7)"
ANSWERS_WRONG = "import json,sys; [print(json.dumps({'ok': False}), flush=True) for _ in sys.stdin]"
ANSWERS_RIGHT = "import json,sys; [print(json.dumps({'ok': True}), flush=True) for _ in sys.stdin]"


def ask(child, kill_first=False):
    """One command through the real BridgeSession; `child` (a Python one-liner) plays the bridge."""
    real = subprocess.Popen
    with mock.patch.object(subprocess, 'Popen', lambda argv, **kw: real([sys.executable, '-c', child], **kw)):
        session = _bridge.BridgeSession(sys.executable)
    try:
        if kill_first:
            session.process.kill()      # an outside kill, not the bridge's own doing
            session.process.wait()
        return session.command('ping')
    finally:
        session.stop()


class Cases(unittest.TestCase):
    def test_mutant_segfaults_the_bridge(self):
        self.assertTrue(ask(SEGFAULT)['ok'])

    def test_mutant_exits_the_bridge_with_code_7(self):
        self.assertTrue(ask(EXIT_7)['ok'])

    def test_bridge_is_killed_from_outside(self):
        self.assertTrue(ask(ANSWERS_RIGHT, kill_first=True)['ok'])

    def test_mutant_changes_the_answer(self):
        self.assertTrue(ask(ANSWERS_WRONG)['ok'], 'the guard must still answer ok')

    def test_mutant_goes_unnoticed(self):
        self.assertTrue(ask(ANSWERS_RIGHT)['ok'])

    def test_mutant_fails_every_subtest(self):
        for axis in ('u', 'v'):
            with self.subTest(axis=axis):
                self.assertTrue(ask(ANSWERS_WRONG)['ok'], 'the guard must still answer ok')

    def test_mutant_exits_the_bridge_inside_a_subtest(self):
        with self.subTest(axis='u'):
            self.assertTrue(ask(EXIT_7)['ok'])
'''

    CASES = ('test_mutant_segfaults_the_bridge', 'test_mutant_exits_the_bridge_with_code_7',
             'test_bridge_is_killed_from_outside', 'test_mutant_changes_the_answer', 'test_mutant_goes_unnoticed',
             'test_mutant_fails_every_subtest', 'test_mutant_exits_the_bridge_inside_a_subtest')

    @classmethod
    def method(cls, case):
        return '%s.Cases.%s' % (cls.FAKE, case)

    @classmethod
    def setUpClass(cls):
        """Run the real oracle for every fake method, repeated by the real run_trials (in parallel across methods:
        each run is mostly Python start-up time)."""
        cls.temp = tempfile.TemporaryDirectory(prefix='bridge-crash-honesty-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.dir = Path(cls.temp.name)
        (cls.dir / (cls.FAKE + '.py')).write_text(cls.FAKE_SOURCE, encoding='utf-8')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GEOMETRY_', 'MUTATE_')) and k != 'PYTHONOPTIMIZE'}
        env.update(PYTHONPATH=os.pathsep.join(p for p in (str(cls.dir), os.environ.get('PYTHONPATH')) if p),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')

        def run(case):
            # exactly what run_pass does for a mutant: run the oracle, repeat only a run that died of a violation
            return mutation_bridge.run_trials(
                mutate, lambda n: mutation_bridge._test(ROOT, Path(__file__).resolve(), [cls.method(case)], env,
                                                        cls.dir / 'out', '%s-%d' % (case, n), ROOT, cls.dir),
                [cls.method(case)])
        with concurrent.futures.ThreadPoolExecutor(len(cls.CASES)) as pool:
            cls.trials = dict(zip(cls.CASES, pool.map(run, cls.CASES)))

    def oracle(self, case):
        """(oracle receipts of every run, method id) of one fake method as the real oracle reported them."""
        trials = self.trials[case]
        for receipt in trials:
            if receipt['result'] is None:
                stderr = (self.dir / 'out' / ('%s-%d.stderr' % (case, trials.index(receipt) + 1))).read_text('utf-8', 'replace')
                self.fail('the oracle printed no structured result: %r\n%s' % (receipt, stderr[-1500:]))
        return trials, self.method(case)

    def judge(self, trials, method):
        return mutation_bridge.judge_trials(mutate, trials, [method])[0]

    # ---- (a) (b) (c): the three verdicts through the real oracle ----

    def test_a_bridge_that_keeps_dying_of_an_access_violation_is_crashed_not_killed(self):
        trials, method = self.oracle('test_mutant_segfaults_the_bridge')
        self.assertEqual(mutate.RUN_RETRIES, len(trials), 'a run that dies of an access violation must be repeated')
        for trial in trials:
            failure = trial['result']['failures'][0]
            self.assertEqual('bridge_closed', failure.get('kind'),
                             'the oracle must label a dead bridge instead of leaving it looking like an assertion failure')
            self.assertTrue(mutate.is_access_violation_code(failure.get('bridge_returncode')), failure)
        verdict, why, killers, crashed_on = mutation_bridge.judge_trials(mutate, trials, [method])
        self.assertEqual('crashed', verdict,
                         'the bridge died of an access violation in %d consecutive runs yet the verdict is %r: '
                         'a crash was counted as an assertion kill or lost (崩潰被算成 killed)' % (len(trials), verdict))
        self.assertEqual(([], [method]), (killers, crashed_on))

    def test_a_single_access_violation_is_not_yet_a_crash(self):
        trials, method = self.oracle('test_mutant_segfaults_the_bridge')
        self.assertEqual('blocked', mutation_bridge.classify(trials[0], [method]))
        self.assertEqual((method,), mutation_bridge.access_violation_tests(trials[0], [method], mutate))
        for count in (1, 2):
            self.assertEqual('blocked', self.judge(trials[:count], method),
                             'fewer than %d runs that died of an access violation are not enough for crashed'
                             % mutate.RUN_RETRIES)

    def test_a_bridge_dying_with_an_ordinary_exit_code_is_blocked_and_not_repeated(self):
        trials, method = self.oracle('test_mutant_exits_the_bridge_with_code_7')
        self.assertEqual(1, len(trials), 'only an access violation is worth repeating')
        failure = trials[0]['result']['failures'][0]
        self.assertEqual(('bridge_closed', 7), (failure.get('kind'), failure.get('bridge_returncode')))
        self.assertIsNone(mutation_bridge.access_violation_tests(trials[0], [method], mutate))
        self.assertEqual('blocked', self.judge(trials, method),
                         'a bridge that merely exited (status 7) was judged %r: not an assertion, not an access '
                         'violation, so not a detection' % self.judge(trials, method))

    def test_a_bridge_killed_from_outside_is_blocked(self):
        trials, method = self.oracle('test_bridge_is_killed_from_outside')
        self.assertEqual(1, len(trials))
        failure = trials[0]['result']['failures'][0]
        self.assertEqual('bridge_closed', failure.get('kind'))
        self.assertIn(failure.get('bridge_returncode'), (1, -9), 'Popen.kill(): TerminateProcess is 1, SIGKILL is -9')
        self.assertEqual('blocked', self.judge(trials, method),
                         'an outside kill (OOM killer, SAC, a human) must never read as a detection')

    def test_b_a_failed_assertion_is_killed(self):
        trials, method = self.oracle('test_mutant_changes_the_answer')
        failure = trials[0]['result']['failures'][0]
        self.assertEqual('assertion', failure.get('kind'))
        self.assertNotIn('bridge_returncode', failure)
        self.assertEqual('killed', self.judge(trials, method),
                         'a real assertion failure caused by the mutant behaviour must stay a kill')

    def test_c_a_passing_run_survives(self):
        trials, method = self.oracle('test_mutant_goes_unnoticed')
        self.assertEqual([], trials[0]['result']['failures'])
        self.assertEqual('survived', self.judge(trials, method))

    # ---- failures inside self.subTest (M65 and M68 are killed that way) ----

    def test_assertion_failures_inside_subtests_are_labelled_and_kill(self):
        trials, method = self.oracle('test_mutant_fails_every_subtest')
        failures = trials[0]['result']['failures']
        self.assertEqual([method + " (axis='u')", method + " (axis='v')"], [f['test'] for f in failures])
        self.assertEqual(['assertion', 'assertion'], [f.get('kind') for f in failures],
                         'subTest failures must be labelled too, or the oracle cannot say what they are')
        self.assertEqual('killed', self.judge(trials, method))

    def test_a_death_inside_a_subtest_is_labelled_a_death_not_an_assertion(self):
        trials, method = self.oracle('test_mutant_exits_the_bridge_inside_a_subtest')
        failure = trials[0]['result']['failures'][0]
        self.assertEqual(method + " (axis='u')", failure['test'])
        self.assertEqual(('bridge_closed', 7), (failure.get('kind'), failure.get('bridge_returncode')))
        self.assertEqual('blocked', self.judge(trials, method))

    def test_the_oracle_refuses_a_failure_that_has_no_label(self):
        import bridge_mutation_oracle as oracle
        test = types.SimpleNamespace(id=lambda: 'tests.example.Case.test_guard')
        result = types.SimpleNamespace(failures=[(test, 'Traceback')], failure_labels=[])
        with self.assertRaises(RuntimeError, msg='an unlabelled failure must stop the run, not vanish from the report'):
            oracle.failure_rows(result)
        result.failure_labels = [{'kind': 'assertion'}]
        self.assertEqual([{'test': 'tests.example.Case.test_guard', 'detail': 'Traceback', 'kind': 'assertion'}],
                         oracle.failure_rows(result))

    # ---- the judging rule on structured receipts ----

    METHOD = 'tests.example.Case.test_guard'
    OTHER = 'tests.example.Case.test_other'

    def payload(self, failures, exit_code=1, methods=None, **extra):
        methods = methods or [self.METHOD]
        row = {"exit_code": exit_code, "result": {
            "schema": "geometry-bridge-mutation-tests/1", "requested": methods, "started": methods,
            "total": len(methods), "failures": failures, "errors": [], "skipped": [],
            "expected_failures": 0, "unexpected_successes": 0}}
        row.update(extra)
        return row

    def failure(self, kind, detail='Traceback ... tests._bridge.BridgeClosed', test=METHOD, **extra):
        out = {"test": test, "detail": detail}
        if kind is not None:
            out["kind"] = kind
        out.update(extra)
        return out

    def death(self, code, test=METHOD):
        return self.failure("bridge_closed", test=test, bridge_returncode=code)

    def test_the_access_violation_codes_are_the_cores(self):
        for code in (-11, 3221225477, -1073741819):
            with self.subTest(code=code):
                self.assertEqual((self.METHOD,), mutation_bridge.access_violation_tests(
                    self.payload([self.death(code)]), [self.METHOD], mutate))
        for code in (0, 1, 7, -9, -6, 3, 3221225725, 139):
            with self.subTest(code=code):
                self.assertIsNone(mutation_bridge.access_violation_tests(
                    self.payload([self.death(code)]), [self.METHOD], mutate))
        # The predicate is mutate.py's own, not a copy: if the core stops calling -11 an access violation, so does the bridge.
        with mock.patch.object(mutate, 'is_access_violation_code', return_value=False):
            self.assertIsNone(mutation_bridge.access_violation_tests(
                self.payload([self.death(-11)]), [self.METHOD], mutate))

    def test_only_repeated_access_violations_in_the_same_tests_make_a_crash(self):
        av, other = self.payload([self.death(-11)]), self.payload([self.death(7)])
        passed = self.payload([], exit_code=0)
        killed = self.payload([self.failure("assertion", detail="AssertionError: u")])
        both = [self.METHOD, self.OTHER]
        av_a = self.payload([self.death(-11)], methods=both)
        av_b = self.payload([self.death(-11, test=self.OTHER)], methods=both)
        for label, methods, receipts, runs, verdict in [
                ("three access violations in the same test", [self.METHOD], [av, av, av], 3, "crashed"),
                ("three, signed and unsigned spellings mixed", [self.METHOD],
                 [av, self.payload([self.death(3221225477)]), self.payload([self.death(-1073741819)])], 3, "crashed"),
                ("two access violations then a pass: the last completed run decides, never crashed",
                 [self.METHOD], [av, av, passed], 3, "survived"),
                ("two access violations then an ordinary death", [self.METHOD], [av, av, other], 3, "blocked"),
                ("two access violations then an external kill (1)", [self.METHOD],
                 [av, av, self.payload([self.death(1)])], 3, "blocked"),
                ("an access violation then an assertion kill", [self.METHOD], [av, killed], 2, "killed"),
                ("an access violation then an ordinary death: not repeated further", [self.METHOD], [av, other], 2, "blocked"),
                ("an ordinary death first: not repeated", [self.METHOD], [other], 1, "blocked"),
                ("a pass first", [self.METHOD], [passed], 1, "survived"),
                ("access violations in different tests", both, [av_a, av_a, av_b], 3, "blocked")]:
            with self.subTest(label):
                calls = []

                def run(n, receipts=receipts):
                    calls.append(n)
                    return receipts[n - 1]
                trials = mutation_bridge.run_trials(mutate, run, methods)
                self.assertEqual((runs, verdict), (len(calls), mutation_bridge.judge_trials(mutate, trials, methods)[0]))

    def test_a_death_without_an_exit_status_is_never_a_detection(self):
        for code in [None, "139", True, 1.5]:
            with self.subTest(bridge_returncode=code):
                row = self.payload([self.failure("bridge_closed", bridge_returncode=code)])
                self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))
                self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate))

    def test_an_unlabelled_closed_bridge_is_not_trusted_as_a_kill(self):
        # A receipt from before the oracle labelled failures: only the text says the bridge closed.
        row = self.payload([self.failure(None, detail="AssertionError: bridge closed: ")])
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]),
                         "text alone can make an entry less trusted, never a kill")
        self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate))
        row = self.payload([self.failure("surprise", detail="AssertionError")])
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))

    def test_an_assertion_failure_beside_a_death_is_blocked_like_the_core(self):
        # mutate.classify_test_run: infrastructure next to a failure is blocked; access_violation_scenes: a failure
        # next to the violation is not a pure crash.  The bridge follows both.
        methods = [self.METHOD, self.OTHER]
        for code in (-11, 7):
            with self.subTest(code=code):
                row = self.payload([self.death(code), self.failure("assertion", test=self.OTHER, detail="AssertionError: u")],
                                   methods=methods)
                self.assertEqual("blocked", mutation_bridge.classify(row, methods))
                self.assertIsNone(mutation_bridge.access_violation_tests(row, methods, mutate))

    def test_timeouts_and_exit_status_mismatches_are_blocked_never_crashed_or_killed(self):
        death = [self.death(-9)]
        assertion = [self.failure("assertion", detail="AssertionError: u")]
        for label, row in [
                ("timed out", dict(self.payload(death, exit_code=124), timed_out=True)),
                ("timed out with no result", {"exit_code": 124, "timed_out": True, "result": None}),
                # timed_out is its own signal: a report that looks complete is still not trusted after a timeout
                ("timed out yet the report says failed", dict(self.payload(assertion), timed_out=True)),
                ("timed out yet the report says passed", dict(self.payload([], exit_code=0), timed_out=True)),
                ("oracle says incomplete (2)", self.payload(death, exit_code=2)),
                ("oracle says clean (0)", self.payload(death, exit_code=0)),
                ("could not launch (127)", self.payload(death, exit_code=127))]:
            with self.subTest(label):
                self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))
                self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate))

    def test_build_launch_and_lookup_errors_stay_blocked(self):
        # Infrastructure the oracle reports under `errors` (unittest's error bucket) is never a detection,
        # not even next to a bridge death.
        row = self.payload([self.death(-11)])
        row["result"]["errors"] = [{"test": self.METHOD, "detail": "FileNotFoundError: bridge.exe"}]
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))
        self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate))

    # ---- the ledger side: --check accepts a crashed bridge record only on the core's evidence ----

    def test_check_accepts_a_crashed_bridge_record_only_on_repeated_access_violations(self):
        root = self.dir / 'repo'
        root.mkdir()
        (root / 'current_geometry.c').write_bytes(b'int anchor = 1;\n')
        m = dict(id='MB', desc='bridge ledger fixture', binary='bridge', file='current_geometry.c',
                 old='anchor = 1', new='anchor = 2', tests=[self.METHOD])
        src = mutate.Sources(root)
        judge = mutation_bridge.oracle_hash(m, root)
        sha = mutation_bridge.sha

        def receipt(methods, failures, exit_code):
            return {"exit_code": exit_code, "stdout_sha256": '1' * 64, "stderr_sha256": '2' * 64,
                    "command": ["<python>", "-B", "tests/bridge_mutation_oracle.py", "<bridge>", *methods],
                    "result": {"schema": "geometry-bridge-mutation-tests/1", "requested": methods, "started": methods,
                               "total": len(methods), "failures": failures, "errors": [], "skipped": [],
                               "expected_failures": 0, "unexpected_successes": 0}}

        def identity(text, exe):
            return {"freshness": "fresh", "exe_sha256": exe * 64, "sidecar_sha256": '3' * 64,
                    "sidecar": {"exe_sha256": exe * 64, "files": {"current_geometry.c": sha(text)}}}

        def evidence(attempts):
            build = {"exit_code": 0, "stdout_sha256": '4' * 64, "stderr_sha256": '5' * 64}
            out = {"schema": "geometry-bridge-mutation-execution/1", "head": 'a' * 40, "platform": os.name,
                   "tool_sha256": mutate.tool_hash(), "oracle_sha256": judge,
                   "methods": m["tests"], "restored_methods": mutation_bridge.RESTORED,
                   "baseline_build": build, "baseline_identity": identity(b'int anchor = 1;\n', 'b'),
                   "baseline": receipt(mutation_bridge.RESTORED, [], 0),
                   "mutant_build": build, "mutant_identity": identity(b'int anchor = 2;\n', 'c'), "mutant": attempts[-1],
                   "restored_build": build, "restored_identity": identity(b'int anchor = 1;\n', 'b'),
                   "restored": receipt(mutation_bridge.RESTORED, [], 0), "byte_restored": True}
            if len(attempts) > 1:
                out["mutant_attempts"] = attempts
            return out

        def check(verdict, attempts, **fields):
            rec = mutate.make_record(m, src, verdict, 'ledger fixture', '2026-10-17', judge,
                                     execution=evidence(attempts), **fields)
            results = self.dir / 'results.json'
            mutate.save_records(results, {m['id']: rec})
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch.object(mutate, 'MUT_ROOT', self.dir / 'cache'):
                code = mutate.check_pass([m], root=root, results_path=results, oracle=judge)
            return code, out.getvalue()

        av = receipt(m["tests"], [self.death(-11)], 1)
        exit7 = receipt(m["tests"], [self.death(7)], 1)
        killed = receipt(m["tests"], [self.failure("assertion", detail="AssertionError: u")], 1)

        code, text = check('crashed', [av, av, av], crashed_on=[self.METHOD])
        self.assertEqual(0, code, text)
        self.assertIn('crashed 1', text)
        self.assertNotIn('STALE', text)
        for label, verdict, attempts, fields, wanted in [
                ("a violation recorded as killed", 'killed', [av, av, av], dict(killed_by=[self.METHOD]), 'contradicts'),
                ("crashed_on naming other tests", 'crashed', [av, av, av], dict(crashed_on=[self.OTHER]), 'crashed_on'),
                ("crashed after a single run", 'crashed', [av], dict(crashed_on=[self.METHOD]), 'contradicts'),
                ("crashed after two runs", 'crashed', [av, av], dict(crashed_on=[self.METHOD]), 'contradicts'),
                ("crashed although the last run was an ordinary death", 'crashed', [av, av, exit7],
                 dict(crashed_on=[self.METHOD]), 'contradicts'),
                ("crashed on a single ordinary death", 'crashed', [exit7], dict(crashed_on=[self.METHOD]), 'contradicts'),
                ("runs padded after a kill", 'killed', [av, killed, killed], dict(killed_by=[self.METHOD]), 'repeated'),
                ("repeating a run that needed no repeat", 'crashed', [exit7, av, av], dict(crashed_on=[self.METHOD]), 'repeated')]:
            with self.subTest(label):
                code, text = check(verdict, attempts, **fields)
                self.assertEqual(1, code, text)
                self.assertIn(wanted, text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
