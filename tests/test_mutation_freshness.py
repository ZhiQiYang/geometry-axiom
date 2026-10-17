"""Non-destructive mutation receipts and preflight tests. All fixture launches are mocked."""
import concurrent.futures
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
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
    throwaway Python child process (real signals, real exit statuses) through the real tests/_bridge.py BridgeSession,
    the real _bridge.run_once, or a hand-written copy of the line protocol, so no native bridge is built or started:
    the child plays "the mutated bridge"."""

    FAKE = 'bridge_crash_fake_cases'
    FAKE_SOURCE = r'''
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests import _bridge

SEGFAULT = ("import os,sys; sys.stdin.readline(); "
            "(os._exit(-1073741819) if os.name == 'nt' else os.kill(os.getpid(), 11))")
EXIT_7 = "import os,sys; sys.stdin.readline(); os._exit(7)"
SEGFAULT_AFTER_ALL = ("import os,sys; sys.stdin.read(); "
                      "(os._exit(-1073741819) if os.name == 'nt' else os.kill(os.getpid(), 11))")
EXIT_7_AFTER_ALL = "import os,sys; sys.stdin.read(); os._exit(7)"
# stdout closes first, the death comes a moment later: the OS reports the exit status after the test already failed.
# SIGKILL / STATUS_STACK_BUFFER_OVERRUN: a crash status that writes no core dump, so its timing is the sleep alone.
CLOSE_THEN_KILLED = ("import os,sys,time; sys.stdin.readline(); os.close(1); time.sleep(0.2); "
                     "(os._exit(-1073740791) if os.name == 'nt' else os.kill(os.getpid(), 9))")
LONG_STDERR_EXIT_0 = ("import os,sys; sys.stdin.readline(); sys.stderr.write('x' * 5000); sys.stderr.flush(); "
                      "os._exit(0)")
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


def run_once(child, data='reset\n'):
    """The real _bridge.run_once; `child` (a Python one-liner) plays the bridge."""
    real = subprocess.run
    with mock.patch.object(subprocess, 'run', lambda argv, **kw: real([sys.executable, '-c', child], **kw)):
        return _bridge.run_once(data, bridge=sys.executable)


def private_ask(child, program=sys.executable):
    """A hand-written copy of the line protocol, as tests/integration/assembly_ownership_probe.py has: one command
    in, one raw line out, tests/_bridge.py not involved.  Returns (raw line, process, stderr file)."""
    err = tempfile.TemporaryFile()
    p = subprocess.Popen([program, '-c', child], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True)
    p.stdin.write('ping\n')
    p.stdin.flush()
    return p.stdout.readline(), p, err


def stderr_text(err):
    err.seek(0)
    return err.read().decode('utf-8', 'replace')


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

    # ---- other ways a test meets a dead bridge (review of PR #294) ----

    def test_run_once_segfaults_the_bridge(self):
        p = run_once(SEGFAULT_AFTER_ALL)
        self.assertEqual(p.returncode, 0, p.stderr)       # what tests/test_bridge_integrity.py asserts

    def test_run_once_exits_the_bridge_with_code_7(self):
        p = run_once(EXIT_7_AFTER_ALL)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_closed_bridge_caught_and_refailed(self):
        try:
            ask(SEGFAULT)
        except AssertionError as exc:
            self.fail('bridge did not answer: %s' % exc)

    def test_exit_7_caught_and_refailed_without_its_text(self):
        try:
            ask(EXIT_7)
        except AssertionError:
            self.fail('the bridge did not answer')

    def test_private_copy_raises_bridge_closed(self):
        raw, p, err = private_ask(SEGFAULT)
        p.wait()
        if not raw:
            raise AssertionError('bridge closed: ' + stderr_text(err))

    def test_private_copy_asserts_on_silence(self):
        raw, p, err = private_ask(SEGFAULT)
        self.assertTrue(raw, 'the bridge must answer')

    def test_private_copy_bridge_dies_after_closing_stdout(self):
        raw, p, err = private_ask(CLOSE_THEN_KILLED)
        self.assertTrue(raw, 'the bridge must answer')

    def test_private_copy_of_the_oracle_bridge_exits_7(self):
        # the oracle for this case is given sys.executable as its bridge binary (BridgeCrashHonestyTests.BINARY)
        raw, p, err = private_ask(EXIT_7, program=os.environ['GEOMETRY_TEST_BRIDGE'])
        p.wait()
        self.assertTrue(raw, 'the bridge must answer')

    def test_private_copy_says_bridge_closed_before_a_long_stderr(self):
        raw, p, err = private_ask(LONG_STDERR_EXIT_0)
        p.wait()
        if not raw:
            raise AssertionError('bridge closed: ' + stderr_text(err))
'''

    CASES = ('test_mutant_segfaults_the_bridge', 'test_mutant_exits_the_bridge_with_code_7',
             'test_bridge_is_killed_from_outside', 'test_mutant_changes_the_answer', 'test_mutant_goes_unnoticed',
             'test_mutant_fails_every_subtest', 'test_mutant_exits_the_bridge_inside_a_subtest',
             'test_run_once_segfaults_the_bridge', 'test_run_once_exits_the_bridge_with_code_7',
             'test_closed_bridge_caught_and_refailed', 'test_exit_7_caught_and_refailed_without_its_text',
             'test_private_copy_raises_bridge_closed', 'test_private_copy_asserts_on_silence',
             'test_private_copy_bridge_dies_after_closing_stdout', 'test_private_copy_of_the_oracle_bridge_exits_7',
             'test_private_copy_says_bridge_closed_before_a_long_stderr')
    # The oracle's bridge binary per case (default: this file, which no fake child runs).  With sys.executable the
    # fake child IS the oracle's bridge binary, so ChildWatch holds it to "exit status 0 or it died".
    BINARY = {'test_private_copy_of_the_oracle_bridge_exits_7': Path(sys.executable)}

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
            binary = cls.BINARY.get(case, Path(__file__).resolve())
            return mutation_bridge.run_trials(
                mutate, lambda n: mutation_bridge._test(ROOT, binary, [cls.method(case)], env,
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

    def first_failure(self, trial, case):
        """The first entry of an oracle run's `failures`; fails with what the run reported instead when there is none
        (a dead bridge that surfaced as an unittest error, a skip, or a run that printed no result)."""
        failures = (trial.get('result') or {}).get('failures')
        self.assertTrue(failures, 'the oracle reported no failure for %s although the fake bridge died or answered '
                        'wrong; the run reported exit status %r, errors %r, skipped %r' % (
                            case, trial.get('exit_code'),
                            [(e.get('detail', '').strip().splitlines() or [''])[-1]
                             for e in (trial.get('result') or {}).get('errors', [])],
                            (trial.get('result') or {}).get('skipped')))
        return failures[0]

    # ---- (a) (b) (c): the three verdicts through the real oracle ----

    def test_a_bridge_that_keeps_dying_of_an_access_violation_is_crashed_not_killed(self):
        trials, method = self.oracle('test_mutant_segfaults_the_bridge')
        self.assertEqual(mutate.RUN_RETRIES, len(trials), 'a run that dies of an access violation must be repeated')
        for trial in trials:
            failure = self.first_failure(trial, 'test_mutant_segfaults_the_bridge')
            self.assertIn('BridgeClosed', failure.get('death_seen_by', []),
                          "the session's own BridgeClosed must label the death, not only the child watch: %r" % failure)
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
        failure = self.first_failure(trials[0], 'test_mutant_exits_the_bridge_with_code_7')
        self.assertEqual(('bridge_closed', 7), (failure.get('kind'), failure.get('bridge_returncode')))
        self.assertIsNone(mutation_bridge.access_violation_tests(trials[0], [method], mutate))
        verdict, why = mutation_bridge.judge_trials(mutate, trials, [method])[:2]
        self.assertEqual('blocked', verdict,
                         'a bridge that merely exited (status 7) was judged %r: not an assertion, not an access '
                         'violation, so not a detection' % verdict)
        for words in ('blocked after 1 oracle run(s)', 'run 1: bridge died in %s with exit status 7 '
                      '(not an access violation)' % method):
            self.assertIn(words, why, 'the blocked reason must name the run count and the actual exit status')

    def test_a_bridge_killed_from_outside_is_blocked(self):
        trials, method = self.oracle('test_bridge_is_killed_from_outside')
        self.assertEqual(1, len(trials))
        failure = self.first_failure(trials[0], 'test_bridge_is_killed_from_outside')
        self.assertEqual('bridge_closed', failure.get('kind'))
        self.assertIn(failure.get('bridge_returncode'), (1, -9), 'Popen.kill(): TerminateProcess is 1, SIGKILL is -9')
        self.assertEqual('blocked', self.judge(trials, method),
                         'an outside kill (OOM killer, SAC, a human) must never read as a detection')

    def test_b_a_failed_assertion_is_killed(self):
        trials, method = self.oracle('test_mutant_changes_the_answer')
        failure = self.first_failure(trials[0], 'test_mutant_changes_the_answer')
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
        failure = self.first_failure(trials[0], 'test_mutant_exits_the_bridge_inside_a_subtest')
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

    # ---- every other way a test meets a dead bridge (review of PR #294): never killed ----

    def assert_crashed(self, case, seen_by, how):
        """`case` died of an access violation in RUN_RETRIES runs: labelled a death (seen by `seen_by`), crashed."""
        trials, method = self.oracle(case)
        failures = [self.first_failure(trial, case) for trial in trials]
        self.assertEqual(['bridge_closed'] * len(trials), [f.get('kind') for f in failures],
                         '%s: the bridge segfaulted, yet the oracle labelled the failure %r (死亡被當成斷言)'
                         % (how, [f.get('kind') for f in failures]))
        for failure in failures:
            self.assertTrue(mutate.is_access_violation_code(failure.get('bridge_returncode')),
                            '%s: the exit status of the dead bridge was not carried out: %r' % (how, failure))
            self.assertIn(seen_by, failure.get('death_seen_by', []), failure)
        verdict, why, killers, crashed_on = mutation_bridge.judge_trials(mutate, trials, [method])
        self.assertEqual((mutate.RUN_RETRIES, 'crashed', [method]), (len(trials), verdict, crashed_on),
                         '%s: a bridge that segfaulted in every run must be crashed (detected, not killed): %s'
                         % (how, why))

    def test_run_once_on_a_segfaulting_bridge_is_crashed_not_killed(self):
        self.assert_crashed('test_run_once_segfaults_the_bridge', 'BridgeClosed',
                            'a test asserting on _bridge.run_once() of a dead bridge')

    def test_run_once_on_a_bridge_exiting_7_is_a_death_not_an_assertion(self):
        trials, method = self.oracle('test_run_once_exits_the_bridge_with_code_7')
        failure = self.first_failure(trials[0], 'test_run_once_exits_the_bridge_with_code_7')
        self.assertEqual(('bridge_closed', 7, ['BridgeClosed']),
                         (failure.get('kind'), failure.get('bridge_returncode'), failure.get('death_seen_by')),
                         'run_once() must raise BridgeClosed with the exit status of a bridge that did not end with 0, '
                         'or `assertEqual(p.returncode, 0)` turns its death into an assertion kill')
        self.assertEqual((1, 'blocked'), (len(trials), self.judge(trials, method)))

    def test_a_death_caught_and_refailed_is_crashed_not_killed(self):
        self.assert_crashed('test_closed_bridge_caught_and_refailed', 'BridgeClosed',
                            'a test that catches BridgeClosed and calls self.fail(...)')

    def test_the_whole_exception_chain_is_read_for_a_death(self):
        trials, method = self.oracle('test_exit_7_caught_and_refailed_without_its_text')
        failure = self.first_failure(trials[0], 'test_exit_7_caught_and_refailed_without_its_text')
        self.assertEqual(('bridge_closed', 7, ['BridgeClosed']),
                         (failure.get('kind'), failure.get('bridge_returncode'), failure.get('death_seen_by')),
                         'BridgeClosed was the __context__ of the self.fail(...) that reached unittest: the oracle '
                         'must follow __cause__/__context__, not only read the outermost exception')
        self.assertEqual('blocked', self.judge(trials, method))

    def test_a_private_copy_of_the_protocol_that_raises_bridge_closed_is_crashed(self):
        self.assert_crashed('test_private_copy_raises_bridge_closed', 'child exit status',
                            "a test with its own copy of the line protocol raising AssertionError('bridge closed: ')")

    def test_a_private_copy_asserting_on_the_silence_of_a_dead_bridge_is_crashed(self):
        self.assert_crashed('test_private_copy_asserts_on_silence', 'child exit status',
                            'a test asserting that a segfaulted bridge it started itself answered')

    def test_a_death_the_os_reports_after_the_failure_is_still_seen(self):
        import bridge_mutation_oracle as oracle
        trials, method = self.oracle('test_private_copy_bridge_dies_after_closing_stdout')
        failure = self.first_failure(trials[0], 'test_private_copy_bridge_dies_after_closing_stdout')
        self.assertEqual(('bridge_closed', ['child exit status']), (failure.get('kind'), failure.get('death_seen_by')),
                         'the bridge closed stdout and was killed 0.2 s after the test failed: ChildWatch.GRACE must '
                         'wait for the exit status instead of calling the failure an assertion')
        self.assertTrue(oracle.is_crash_status(failure.get('bridge_returncode')), failure)
        self.assertEqual((1, 'blocked'), (len(trials), self.judge(trials, method)))

    def test_the_oracle_bridge_binary_ending_with_any_status_but_0_is_a_death(self):
        trials, method = self.oracle('test_private_copy_of_the_oracle_bridge_exits_7')
        failure = self.first_failure(trials[0], 'test_private_copy_of_the_oracle_bridge_exits_7')
        self.assertEqual(('bridge_closed', 7, ['child exit status']),
                         (failure.get('kind'), failure.get('bridge_returncode'), failure.get('death_seen_by')),
                         "the oracle's own bridge binary exited 7 under the test (its only orderly end is 0): a death")
        self.assertEqual((1, 'blocked'), (len(trials), self.judge(trials, method)))

    def test_bridge_closed_text_cut_from_the_kept_detail_still_blocks(self):
        trials, method = self.oracle('test_private_copy_says_bridge_closed_before_a_long_stderr')
        failure = self.first_failure(trials[0], 'test_private_copy_says_bridge_closed_before_a_long_stderr')
        self.assertNotIn('bridge closed:', failure['detail'], 'the fixture must push the text out of the kept detail')
        self.assertEqual(('bridge_closed', None, ['message text']),
                         (failure.get('kind'), failure.get('bridge_returncode'), failure.get('death_seen_by')),
                         'the message says the bridge closed (beyond the last 3000 characters the receipt keeps): '
                         'the oracle must read the exception, not the kept detail, and must not call it an assertion')
        self.assertEqual('blocked', self.judge(trials, method),
                         'text alone is no exit status: never killed, never crashed')

    def test_failure_label_needs_one_agreed_exit_status(self):
        import bridge_mutation_oracle as oracle

        class Closed(AssertionError):           # what the oracle recognises: the class flag, not tests._bridge itself
            bridge_closed = True

            def __init__(self, returncode):
                super().__init__('bridge closed: ')
                self.returncode = returncode
        both = ['BridgeClosed', 'child exit status']
        for label, exc, deaths, wanted in [
                ("no sign of a dead bridge", AssertionError('1 != 2'), [], {'kind': 'assertion'}),
                ("BridgeClosed and the child agree", Closed(-11), [-11],
                 {'kind': 'bridge_closed', 'bridge_returncode': -11, 'death_seen_by': both}),
                ("BridgeClosed without a status, the child has one", Closed(None), [-11],
                 {'kind': 'bridge_closed', 'bridge_returncode': -11, 'death_seen_by': both}),
                ("two deaths that disagree: no single status", Closed(-11), [7],
                 {'kind': 'bridge_closed', 'bridge_returncode': None, 'death_seen_by': both}),
                ("a dead child under a plain assertion", AssertionError('1 != 2'), [-9],
                 {'kind': 'bridge_closed', 'bridge_returncode': -9, 'death_seen_by': ['child exit status']}),
                ("text only", AssertionError('bridge closed: '), [],
                 {'kind': 'bridge_closed', 'bridge_returncode': None, 'death_seen_by': ['message text']})]:
            with self.subTest(label):
                self.assertEqual(wanted, oracle.failure_label(exc, deaths),
                                 '%s: a death needs the one exit status all the evidence agrees on' % label)

    def test_crash_statuses_are_signals_and_windows_ntstatus_errors(self):
        import bridge_mutation_oracle as oracle
        for code in (-11, -9, -6, 3221225477, -1073741819, 0xC0000409):
            self.assertTrue(oracle.is_crash_status(code), code)
        for code in (0, 1, 3, 7, 139, 255, None, True, '-11'):
            self.assertFalse(oracle.is_crash_status(code), code)

    def test_child_watch_counts_only_children_that_die_under_the_current_test(self):
        import bridge_mutation_oracle as oracle
        segfault = ("import os; (os._exit(-1073741819) if os.name == 'nt' else os.kill(os.getpid(), 11))")

        def child(watch, code):
            proc = subprocess.Popen([sys.executable, '-c', code])
            watch.children.append(proc)
            proc.wait()
            return proc

        watch = oracle.ChildWatch(bridge=sys.executable)    # here every `python -c` child is "the bridge binary"
        child(watch, segfault)
        self.assertEqual(1, len(watch.deaths()))
        self.assertTrue(mutate.is_access_violation_code(watch.deaths()[0]), watch.deaths())
        watch.mark()                                         # a new test starts: that death belongs to the last one
        self.assertEqual([], watch.deaths(), 'a child that died before this test started is not a death under it')
        child(watch, 'import os; os._exit(0)')
        self.assertEqual([], watch.deaths(), "exit status 0 is the bridge's orderly end")
        child(watch, 'import os; os._exit(7)')
        self.assertEqual([7], watch.deaths(), 'the bridge binary ending with 7 died under the test')
        other = oracle.ChildWatch(bridge=Path(__file__))       # the same children, but not the bridge binary
        other.children = list(watch.children)
        other.mark()
        child(other, 'import os; os._exit(7)')
        self.assertEqual([], other.deaths(), 'another program ending with 7 is not a crash')
        child(other, segfault)
        self.assertEqual(1, len(other.deaths()), 'any child that crashes under the test is a death')

    def test_child_watch_gives_a_live_child_its_grace_once_per_test(self):
        import bridge_mutation_oracle as oracle
        watch = oracle.ChildWatch(bridge=sys.executable)
        watch.GRACE = 0.2
        alive = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        self.addCleanup(alive.wait)
        self.addCleanup(alive.kill)
        watch.children.append(alive)
        watch.mark()
        with mock.patch.object(alive, 'wait', wraps=alive.wait) as wait:
            self.assertEqual([], watch.deaths())
            self.assertEqual([], watch.deaths(), 'a second failing subtest of the same test')
            self.assertEqual(1, wait.call_count, 'a live session must not cost GRACE again for every failing subtest')
            watch.mark()                             # the next test gets its own grace
            self.assertEqual([], watch.deaths())
            self.assertEqual(2, wait.call_count)

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

                def run(n, receipts=receipts, label=label):
                    calls.append(n)
                    self.assertLessEqual(n, len(receipts), '%s: run_trials asked for run %d after %d scripted runs; '
                                         'only a run that died of an access violation is repeated'
                                         % (label, n, len(receipts)))
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

    def test_an_assertion_label_whose_text_says_the_bridge_closed_is_not_a_kill(self):
        # A receipt from an oracle that missed the death (or some other oracle): labelled "assertion", but the text
        # is the closed bridge's.  Text cannot prove a death, but it is enough to refuse calling it a kill.
        for detail in ("AssertionError: bridge closed: ", "AssertionError: bridge did not answer: bridge closed: x"):
            with self.subTest(detail=detail):
                row = self.payload([self.failure("assertion", detail=detail)])
                self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]),
                                 "a failure labelled assertion whose text says the bridge closed was judged a kill")
                self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate))
                self.assertEqual("blocked", mutation_bridge.judge_trials(mutate, [row], [self.METHOD])[0])

    def test_blocked_reasons_name_every_run_and_its_exit_status(self):
        av, exit7 = self.payload([self.death(-11)]), self.payload([self.death(7)])
        for label, trials, wanted in [
                ("two access violations then an exit 7", [av, av, exit7],
                 ["blocked after 3 oracle run(s)",
                  "run 1: bridge died in %s with exit status -11 (an access violation)" % self.METHOD,
                  "run 2: bridge died in %s with exit status -11 (an access violation)" % self.METHOD,
                  "run 3: bridge died in %s with exit status 7 (not an access violation)" % self.METHOD,
                  "crashed needs %d such runs" % mutate.RUN_RETRIES]),
                ("a single exit 7", [exit7],
                 ["blocked after 1 oracle run(s)", "exit status 7 (not an access violation)", "(oracle exit status 1)"]),
                ("an access violation then a timeout", [av, dict(self.payload([]), exit_code=124, timed_out=True)],
                 ["blocked after 2 oracle run(s)", "run 2: oracle timed out (exit status 124)"]),
                ("no structured result", [{"exit_code": 2, "result": None}],
                 ["run 1: oracle printed no structured result (exit status 2)"]),
                ("text only", [self.payload([self.failure("assertion", detail="AssertionError: bridge closed: ")])],
                 ["says the bridge closed, with no exit status (text only)"])]:
            with self.subTest(label):
                verdict, why = mutation_bridge.judge_trials(mutate, trials, [self.METHOD])[:2]
                self.assertEqual("blocked", verdict)
                for words in wanted:
                    self.assertIn(words, why)

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
        # An access-violation death (-11): everything about it would make a crash, except what is under test here.
        death = [self.death(-11)]
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
                self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate),
                                  "an oracle run that did not end with exit status 1 is not a complete report of "
                                  "access-violation deaths, whatever its failures say")
                verdict, why = mutation_bridge.judge_trials(mutate, [row] * mutate.RUN_RETRIES, [self.METHOD])[:2]
                self.assertEqual("blocked", verdict, why)

    def test_build_launch_and_lookup_errors_stay_blocked(self):
        # Infrastructure the oracle reports under `errors` (unittest's error bucket) is never a detection,
        # not even next to a bridge death.
        row = self.payload([self.death(-11)])
        row["result"]["errors"] = [{"test": self.METHOD, "detail": "FileNotFoundError: bridge.exe"}]
        self.assertEqual("blocked", mutation_bridge.classify(row, [self.METHOD]))
        self.assertIsNone(mutation_bridge.access_violation_tests(row, [self.METHOD], mutate))

    # ---- the ledger side: --check accepts a crashed bridge record only on the core's evidence ----

    def receipt(self, methods, failures, exit_code, label='mutant'):
        """An oracle receipt shaped like mutation_bridge._run's: its own output file and its own output hash per run."""
        return {"exit_code": exit_code, "stdout_file": label + ".stdout",
                "stdout_sha256": mutation_bridge.sha(label.encode()), "stderr_sha256": '2' * 64,
                "command": ["<python>", "-B", "tests/bridge_mutation_oracle.py", "<bridge>", *methods],
                "result": {"schema": "geometry-bridge-mutation-tests/1", "requested": methods, "started": methods,
                           "total": len(methods), "failures": failures, "errors": [], "skipped": [],
                           "expected_failures": 0, "unexpected_successes": 0}}

    def fixture_mutant(self):
        """A bridge mutant over a method the baseline runs (mutate.definition_kind requires a RESTORED method)."""
        return dict(id='MB', desc='bridge ledger fixture', binary='bridge', file='current_geometry.c',
                    old='anchor = 1', new='anchor = 2', tests=[mutation_bridge.RESTORED[1]])

    def test_check_accepts_a_crashed_bridge_record_only_on_repeated_access_violations(self):
        # The mutant's own method must be one the baseline ran and passed, i.e. a RESTORED method
        # (mutate.definition_kind); the baseline and the restoration must pass all of RESTORED.
        method, other = mutation_bridge.RESTORED[1], mutation_bridge.RESTORED[2]
        outside = 'tests.example.Case.test_guard'           # well-formed, but the baseline never runs it
        root = self.dir / 'repo'
        root.mkdir()
        (root / 'current_geometry.c').write_bytes(b'int anchor = 1;\n')
        src = mutate.Sources(root)
        sha = mutation_bridge.sha

        def identity(text, exe):
            return {"freshness": "fresh", "exe_sha256": exe * 64, "sidecar_sha256": '3' * 64,
                    "sidecar": {"exe_sha256": exe * 64, "files": {"current_geometry.c": sha(text)}}}

        passed_restored = self.receipt(mutation_bridge.RESTORED, [], 0, 'baseline')
        failed_restored = self.receipt(mutation_bridge.RESTORED, [self.failure(
            "assertion", test=mutation_bridge.RESTORED[0], detail="AssertionError: baseline")], 1, 'baseline')

        def check(verdict, attempts, tests=(method,), baseline=passed_restored, restored=passed_restored, mutant=None,
                  **fields):
            m = dict(id='MB', desc='bridge ledger fixture', binary='bridge', file='current_geometry.c',
                     old='anchor = 1', new='anchor = 2', tests=list(tests))
            judge = mutation_bridge.oracle_hash(m, root)
            build = {"exit_code": 0, "stdout_sha256": '4' * 64, "stderr_sha256": '5' * 64}
            evidence = {"schema": "geometry-bridge-mutation-execution/1", "head": 'a' * 40, "platform": os.name,
                        "tool_sha256": mutate.tool_hash(), "oracle_sha256": judge,
                        "methods": m["tests"], "restored_methods": mutation_bridge.RESTORED,
                        "baseline_build": build, "baseline_identity": identity(b'int anchor = 1;\n', 'b'),
                        "baseline": baseline,
                        "mutant_build": build, "mutant_identity": identity(b'int anchor = 2;\n', 'c'),
                        "mutant": mutant or attempts[-1],
                        "restored_build": build, "restored_identity": identity(b'int anchor = 1;\n', 'b'),
                        "restored": restored, "byte_restored": True}
            if len(attempts) > 1:
                evidence["mutant_attempts"] = attempts
            rec = mutate.make_record(m, src, verdict, 'ledger fixture', '2026-10-17', judge,
                                     execution=evidence, **fields)
            results = self.dir / 'results.json'
            mutate.save_records(results, {m['id']: rec})
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch.object(mutate, 'MUT_ROOT', self.dir / 'cache'):
                code = mutate.check_pass([m], root=root, results_path=results, oracle=judge)
            return code, out.getvalue()

        def run(n, failures, test=method):
            """Run number n (1-based) of the mutant, labelled the way run_pass labels it: its own output file and hash."""
            return self.receipt([test], failures, 1, 'mutant' if n == 1 else 'mutant-%d' % n)

        def av(n, test=method):
            return run(n, [self.death(-11, test=test)], test)

        def avs(count=3, test=method):
            return [av(n, test) for n in range(1, count + 1)]

        def exit7(n):
            return run(n, [self.death(7, test=method)])

        def killed(n, test=method):
            return run(n, [self.failure("assertion", test=test, detail="AssertionError: u")], test)

        for label, verdict, attempts, fields in [
                ("three access violations in the mutant's own RESTORED method", 'crashed', avs(),
                 dict(crashed_on=[method])),
                ("an assertion kill in the mutant's own RESTORED method", 'killed', [killed(1)],
                 dict(killed_by=[method]))]:
            with self.subTest(label):
                code, text = check(verdict, attempts, **fields)
                self.assertEqual(0, code, text)
                self.assertIn('%s 1' % verdict, text)
                self.assertNotIn('STALE', text)

        verdict_contradicts = 'bridge verdict contradicts actual unittest results'
        crashed_on_contradicts = 'bridge crashed_on contradicts repeated access violations'
        repeated = 'bridge mutant runs were repeated for a reason the rule does not allow'
        too_many = 'more bridge mutant runs than the repeat rule allows'
        not_the_mutant_run = 'bridge mutant_attempts must end with the recorded mutant run'
        not_in_order = 'bridge mutant runs are not the outputs run_pass wrote, in order'
        one_output = 'bridge mutant runs repeat one recorded output'
        baseline_failed = 'bridge baseline/restoration did not pass every declared method'
        not_in_baseline = 'bridge 變異的測試方法不在基準線 mutation_bridge.RESTORED 內'
        first, second, third = avs()
        same_output = dict(second, stdout_sha256=first['stdout_sha256'])
        for label, verdict, attempts, fields, extra, wanted in [
                ("a violation recorded as killed", 'killed', avs(), dict(killed_by=[method]), {}, verdict_contradicts),
                ("crashed_on naming other tests", 'crashed', avs(), dict(crashed_on=[other]), {}, crashed_on_contradicts),
                ("crashed after a single run", 'crashed', avs(1), dict(crashed_on=[method]), {}, verdict_contradicts),
                ("crashed after two runs", 'crashed', avs(2), dict(crashed_on=[method]), {}, verdict_contradicts),
                ("crashed although the last run was an ordinary death", 'crashed', avs(2) + [exit7(3)],
                 dict(crashed_on=[method]), {}, verdict_contradicts),
                ("crashed on a single ordinary death", 'crashed', [exit7(1)], dict(crashed_on=[method]), {},
                 verdict_contradicts),
                ("runs padded after a kill", 'killed', [av(1), killed(2), killed(3)], dict(killed_by=[method]), {},
                 repeated),
                ("repeating a run that needed no repeat", 'crashed', [exit7(1), av(2), av(3)],
                 dict(crashed_on=[method]), {}, repeated),
                ("a fourth run after three access violations (rerun until it kills)", 'killed', avs() + [killed(4)],
                 dict(killed_by=[method]), {}, too_many),
                # one recorded violation copied three times must not pass for three consecutive crashes
                ("one receipt copied three times", 'crashed', [first] * 3, dict(crashed_on=[method]), {}, not_in_order),
                ("right outputs in the wrong order", 'crashed', [second, first, third], dict(crashed_on=[method]), {},
                 not_in_order),
                ("one output hash recorded for two runs", 'crashed', [first, same_output, third],
                 dict(crashed_on=[method]), {}, one_output),
                ("attempts that do not end with the recorded mutant run", 'crashed', avs(), dict(crashed_on=[method]),
                 dict(mutant=self.receipt([method], [], 0, 'mutant-3')), not_the_mutant_run),
                ("crashed although the baseline failed a RESTORED method", 'crashed', avs(),
                 dict(crashed_on=[method]), dict(baseline=failed_restored), baseline_failed),
                ("crashed although the restoration failed a RESTORED method", 'crashed', avs(),
                 dict(crashed_on=[method]), dict(restored=failed_restored), baseline_failed),
                ("killed although the baseline failed a RESTORED method", 'killed', [killed(1)],
                 dict(killed_by=[method]), dict(baseline=failed_restored), baseline_failed),
                ("crashed in a method the baseline never ran", 'crashed', avs(3, outside),
                 dict(crashed_on=[outside]), dict(tests=[outside]), not_in_baseline),
                ("killed in a method the baseline never ran", 'killed', [killed(1, outside)],
                 dict(killed_by=[outside]), dict(tests=[outside]), not_in_baseline)]:
            with self.subTest(label):
                code, text = check(verdict, attempts, **extra, **fields)
                self.assertEqual(1, code, '%s: --check accepted the record:\n%s' % (label, text))
                self.assertIn(wanted, text, '%s: refused, but not for the reason under test' % label)

    def test_run_pass_repeats_a_dying_run_and_records_every_attempt(self):
        """run_pass with stand-ins for the build and the oracle (real git checkout, real judging and recording)."""
        repo = self.dir / 'passrepo'
        (repo / 'tests').mkdir(parents=True)
        (repo / 'current_geometry.c').write_bytes(b'int anchor = 1;\n')
        (repo / 'tests' / 'keep.py').write_bytes(b'X = 1\n')

        def git(*args):
            subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid',
                            *args], cwd=repo, check=True, capture_output=True)
        git('init', '-q')
        git('add', '-A')
        git('commit', '-q', '-m', 'fixture')
        m = self.fixture_mutant()
        method = m['tests'][0]
        results = self.dir / 'pass-results.json'
        sha = mutation_bridge.sha

        def run_pass(script):
            """script: (failures, exit_code) of each successive run of the mutant; returns (record, mutant run labels)."""
            labels = []

            def identity(work, out=None):
                raw = (Path(work) / m['file']).read_bytes().replace(b'\r\n', b'\n')
                return {"freshness": "fresh", "exe_sha256": sha(raw), "sidecar_sha256": '3' * 64,
                        "sidecar": {"exe_sha256": sha(raw), "files": {m['file']: sha(raw)}}}

            def build(work, out, env, folder, label, root, cache):
                return {"exit_code": 0, "stdout_sha256": sha(label.encode()), "stderr_sha256": '5' * 64}, identity(work)

            def oracle(work, binary, methods, env, folder, label, root, cache):
                if methods == mutation_bridge.RESTORED:
                    return self.receipt(methods, [], 0, label)
                labels.append(label)
                failures, code = script[len(labels) - 1]
                return self.receipt(methods, failures, code, label)
            real_run = subprocess.run     # keep git's own progress text out of the test output

            def quiet_run(*args, **kwargs):
                return real_run(*args, **{'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL, **kwargs})
            with contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.object(subprocess, 'run', quiet_run), \
                    mock.patch.object(mutate, 'MUT_ROOT', self.dir / 'pass-cache'), \
                    mock.patch.object(mutation_bridge, '_build', build), \
                    mock.patch.object(mutation_bridge, '_identity', identity), \
                    mock.patch.object(mutation_bridge, '_test', oracle):
                mutation_bridge.run_pass(mutate, [m], repo, results, today='2026-10-17')
            return mutate.load_records(results)[m['id']], labels

        violation = ([self.death(-11, test=method)], 1)
        record, labels = run_pass([violation, violation, violation])
        self.assertEqual(['mutant', 'mutant-2', 'mutant-3'], labels, 'a run that dies of an access violation is repeated')
        self.assertEqual(('crashed', [method]), (record['verdict'], record.get('crashed_on')), record.get('why'))
        self.assertNotIn('killed_by', record)
        attempts = record['execution']['mutant_attempts']
        self.assertEqual(['mutant.stdout', 'mutant-2.stdout', 'mutant-3.stdout'], [a['stdout_file'] for a in attempts])
        self.assertEqual(attempts[-1], record['execution']['mutant'])
        # the saved record passes the same --check the ledger is read with
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(mutate, 'MUT_ROOT', self.dir / 'pass-cache'):
            code = mutate.check_pass([m], root=repo, results_path=results, oracle=mutation_bridge.oracle_hash(m, repo))
        self.assertEqual(0, code, out.getvalue())
        self.assertIn('crashed 1', out.getvalue())

        record, labels = run_pass([([self.death(7, test=method)], 1), violation, violation])
        self.assertEqual(['mutant'], labels, 'only an access violation is worth repeating')
        self.assertEqual('blocked', record['verdict'])
        self.assertNotIn('mutant_attempts', record['execution'])

        record, labels = run_pass([violation, violation, ([self.failure("assertion", test=method, detail="AssertionError: u")], 1)])
        self.assertEqual(('killed', ['mutant', 'mutant-2', 'mutant-3']), (record['verdict'], labels))
        self.assertEqual([method], record['killed_by'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
