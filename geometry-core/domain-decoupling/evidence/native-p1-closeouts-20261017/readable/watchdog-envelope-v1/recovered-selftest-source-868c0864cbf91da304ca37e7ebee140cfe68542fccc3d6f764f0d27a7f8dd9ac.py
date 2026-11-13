#!/usr/bin/env python3
"""No-C synthetic watchdog verification. No product modules or shared lock."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest


HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("watchdog", HERE / "watchdog.py")
watchdog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchdog)
RUN = HERE / ("selftest-" + str(time.time_ns()))
RUN.mkdir()
EXPECTED = ["synthetic.C.test_" + name for name in ("ok", "fail", "error", "skip", "started", "unrun", "subtest", "ambiguous")]


def line(name, status="ok", newline=True):
    return "test_" + name + " (synthetic.C.test_" + name + ") ... " + status + ("\n" if newline else "")


class ParserTests(unittest.TestCase):
    def test_complete_known_statuses_only(self):
        text = "".join([line("ok"), line("fail", "FAIL"), line("error", "ERROR"),
                        line("skip", "skipped 'deliberate'"), line("ambiguous"), line("ambiguous"),
                        "test_subtest (synthetic.C.test_subtest) ... \n",
                        "  test_subtest (synthetic.C.test_subtest) (item=1) ... FAIL\n",
                        line("foreign"), line("started", "ok", newline=False)])
        result = watchdog.parse_partial(text.encode(), EXPECTED)
        self.assertEqual(result["counts"], {"ok": 1, "FAIL": 1, "ERROR": 1, "skipped": 1,
                                           "STARTED_INCOMPLETE": 2, "UNRUN": 1, "AMBIGUOUS": 1})
        self.assertEqual(result["actual_completed_methods"], 4)
        self.assertEqual(len(result["unknown_identity_lines"]), 1)
        self.assertEqual(len(result["methods"]["synthetic.C.test_subtest"]["subtest_lines"]), 1)
        self.assertEqual(result["trailing_unterminated_line"], line("started", newline=False))

    def test_indented_ok_wrong_method_and_nonstandard_status_are_not_pass(self):
        text = ("  " + line("ok") + "test_other (synthetic.C.test_fail) ... ok\n" +
                line("error", "unexpected success") + line("skip", "expected failure") +
                "test_started (synthetic.C.test_started) ... diagnostic ok\n")
        result = watchdog.parse_partial(text.encode(), EXPECTED)
        self.assertEqual(result["actual_ok_methods"], 0)
        self.assertEqual(result["counts"]["STARTED_INCOMPLETE"], 4)

    def test_group_and_execution_kind_counts(self):
        result = watchdog.parse_partial((line("ok") + line("fail", "FAIL")).encode(), EXPECTED,
                    {name: "portable" if name.endswith("_ok") else "native" for name in EXPECTED},
                    ["synthetic"], {"sample": ["synthetic"]})
        self.assertEqual(result["by_execution_kind"]["portable"]["ok"], 1)
        self.assertEqual(result["by_execution_kind"]["native"]["ok"], 0)
        self.assertEqual(result["by_group"]["sample"], result["counts"])
        self.assertEqual(result["by_module"]["synthetic"], result["counts"])

    def test_real_unittest_subtest_failure_never_becomes_method_success(self):
        class SyntheticCase(unittest.TestCase):
            def test_pass(self):
                pass
            def test_subtest(self):
                for number in range(2):
                    with self.subTest(number=number):
                        self.assertEqual(number, 0)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticCase)
        names = [test.id() for test in suite]
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        self.assertEqual(result.testsRun, 2)
        receipt = watchdog.parse_partial(stream.getvalue().encode(), names)
        # Local classes contain <locals>, which intentionally fail the strict
        # production identity grammar. Use a module-level synthetic unittest
        # below for actual standard-format identity verification.
        self.assertEqual(receipt["actual_ok_methods"], 0)
        self.assertEqual(len(result.failures), 1)


class ProcessTests(unittest.TestCase):
    def run_wrapper(self, name, script, seconds=5):
        output = RUN / name
        output.mkdir()
        recipe = output / "recipe.json"
        recipe.write_text(json.dumps({"source": "synthetic-no-c", "expected_tests": len(EXPECTED),
                         "modules": ["synthetic"], "execution_kind_by_method": {test: "synthetic" for test in EXPECTED}}))
        command_path = output / "child.py"
        command_path.write_text(script)
        log = output / "unittest.log"
        command = [sys.executable, str(HERE / "watchdog.py"), "--seconds", str(seconds),
                   "--metadata", str(output / "watchdog.json"), "--log", str(log), "--recipe", str(recipe),
                   "--", sys.executable, "-u", str(command_path)]
        with log.open("wb") as stream:
            proc = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=20,
                                  cwd=output, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        metadata = json.loads((output / "watchdog.json").read_bytes())
        self.assertTrue(metadata["termination"]["complete"])
        self.assertEqual(metadata["termination"]["remaining_group"], [])
        self.assertEqual(metadata["termination"]["escaped_adopted_children"], [])
        self.assertEqual(metadata["watchdog_sha256"], metadata["watchdog_sha256_after"])
        self.assertEqual(metadata["recipe_sha256"], metadata["recipe_sha256_after"])
        self.assertFalse(metadata["per_test_and_compiler_timeouts_modified"])
        return proc, metadata, output

    def test_success_preserves_exit_and_inherited_output(self):
        proc, metadata, output = self.run_wrapper("success", "print('inherited stdout'); import sys; print('inherited stderr',file=sys.stderr)")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(metadata["status"], "COMPLETED")
        self.assertEqual(metadata["termination"]["signals"], [])
        self.assertIn("inherited stdout", (output / "unittest.log").read_text())
        self.assertIn("inherited stderr", (output / "unittest.log").read_text())
        self.assertFalse((output / "partial-results.json").exists())

    def test_nonzero_child_exit_is_unchanged(self):
        proc, metadata, output = self.run_wrapper("error", "import sys; print('synthetic error'); sys.exit(7)")
        self.assertEqual(proc.returncode, 7)
        self.assertEqual(metadata["child_returncode"], 7)
        self.assertEqual(metadata["status"], "COMPLETED")

    def test_timeout_reaps_python_descendant_and_never_signals_sentinel(self):
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"], start_new_session=True)
        try:
            script = ("import os,signal,subprocess,sys,time\n"
                      "from pathlib import Path\n"
                      "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                      "code=\"import os,signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);Path('grandchild.pid').write_text(str(os.getpid()));time.sleep(25)\"\n"
                      "subprocess.Popen([sys.executable,'-c',code])\n"
                      "while not Path('grandchild.pid').exists(): time.sleep(0.01)\n"
                      "print(" + repr(line("ok").rstrip("\n")) + ", flush=True)\n"
                      "print(" + repr(line("started", "", False)) + ", end='', flush=True)\n"
                      "time.sleep(25)\n")
            proc, metadata, output = self.run_wrapper("timeout-tree", script, seconds=1)
            self.assertEqual(proc.returncode, 124)
            self.assertEqual(metadata["status"], "BLOCKED")
            self.assertEqual(metadata["classification"], "infrastructure")
            self.assertEqual(metadata["reason"], "whole-batch-timeout")
            self.assertEqual([row["signal"] for row in metadata["termination"]["signals"]], ["SIGTERM", "SIGKILL"])
            grandchild = int((output / "grandchild.pid").read_text())
            self.assertIn(grandchild, [row["pid"] for row in metadata["termination"]["reaped"]])
            self.assertFalse(Path("/proc", str(grandchild)).exists())
            self.assertFalse(Path("/proc", str(metadata["child_pid"])).exists())
            partial = json.loads((output / "partial-results.json").read_bytes())
            self.assertEqual(partial["counts"]["ok"], 1)
            self.assertEqual(partial["counts"]["STARTED_INCOMPLETE"], 1)
            self.assertEqual(partial["counts"]["UNRUN"], 6)
            self.assertIsNone(sentinel.poll(), "Unrelated sentinel must survive")
            for event in metadata["termination"]["signals"]:
                self.assertTrue(all(row["pgid"] == metadata["child_pid"] and row["sid"] == metadata["child_pid"]
                                    for row in event["members_before"]))
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=5)

    def test_normal_exit_waits_for_owned_leftover_cleanup(self):
        script = ("import subprocess,sys,time\n"
                  "from pathlib import Path\n"
                  "subprocess.Popen([sys.executable,'-c',\"import os,signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);Path('leftover.pid').write_text(str(os.getpid()));time.sleep(25)\"])\n"
                  "while not Path('leftover.pid').exists(): time.sleep(0.01)\n")
        proc, metadata, output = self.run_wrapper("leftover", script)
        self.assertEqual(proc.returncode, 125)  # Infrastructure BLOCKED cannot report success.
        self.assertEqual(metadata["status"], "BLOCKED")
        self.assertEqual(metadata["reason"], "child-exited-with-live-descendants")
        self.assertFalse(Path("/proc", (output / "leftover.pid").read_text()).exists())

    def test_child_signal_returncode_is_preserved(self):
        proc, metadata, output = self.run_wrapper("signal", "import os,signal;os.kill(os.getpid(), signal.SIGTERM)")
        self.assertEqual(proc.returncode, -signal.SIGTERM)
        self.assertEqual(metadata["child_returncode"], -signal.SIGTERM)


if __name__ == "__main__":
    started = watchdog.utc()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    evidence = {"kind": "no-c-synthetic-watchdog-selftest", "started_utc": started,
                "finished_utc": watchdog.utc(), "tests_run": result.testsRun,
                "failures": len(result.failures), "errors": len(result.errors),
                "passed": result.wasSuccessful(), "output": str(RUN),
                "watchdog_sha256": watchdog.sha((HERE / "watchdog.py").read_bytes()),
                "selftest_sha256": watchdog.sha(Path(__file__).read_bytes()),
                "compiled_c": False, "imported_product_tests": False, "shared_lock_acquired": False,
                "python": sys.version, "platform": sys.platform}
    watchdog.atomic_json(RUN / "selftest-summary.json", evidence)
    print(json.dumps(evidence, indent=2), flush=True)
    sys.exit(0 if result.wasSuccessful() else 1)
