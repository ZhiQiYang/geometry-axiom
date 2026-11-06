"""L25: actual serve.py process, loopback HTTP and the fresh native bridge.

No Popen/NativeContext/HTTP-handler/allocator substitute is installed. Named
mutants execute one changed copy of the real host source from a private TEMP
file, with the product __file__ retained for its real runtime/assets/imports.
"""
from __future__ import annotations

import http.client
import json
import os
from pathlib import Path
import queue
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid

from tests import _bridge

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "geometry-web" / "serve.py"
MUTATIONS = {
    "L25-STARTUP": ("        install_epoch(root_context)\n        host =", "        host ="),
    "L25-REPLACE": (
        "                if _command_replaces_world(cmd, response):\n                    _write_epoch(native)",
        "                if _command_replaces_world(cmd, response):\n                    pass"),
    "L25-PUBLIC-EPOCH": ('if cmd.split(" ", 1)[0] == "identity-epoch":',
                         'if False and cmd.split(" ", 1)[0] == "identity-epoch":'),
    "L25-FAILED-LOAD": ('return isinstance(data, dict) and data.get("ok") is True',
                         'return isinstance(data, dict) and data.get("ok") is not None'),
    "L25-PREPARE": ('_REPLACE_HEADS = {"reset", "default", "loadfile", "load-confirm"}',
                     '_REPLACE_HEADS = {"reset", "default", "loadfile", "load-confirm", "load-prepare"}'),
    "L25-CANCEL": ('_REPLACE_HEADS = {"reset", "default", "loadfile", "load-confirm"}',
                    '_REPLACE_HEADS = {"reset", "default", "loadfile", "load-confirm", "load-cancel"}'),
}


class IdentityHostRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = _bridge.find_bridge()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="identity-host-runtime-")
        self.addCleanup(self.directory.cleanup)
        self.errors = tempfile.TemporaryFile()
        self.addCleanup(self.errors.close)
        # Reserve an unused loopback port, then let the unchanged production
        # main construct its own PreviewHTTPServer and install the startup epoch.
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            self.port = reservation.getsockname()[1]
        command = [sys.executable, str(HOST), str(self.port)]
        mutant = os.environ.get("IDENTITY_HOST_MUTANT", "")
        if mutant:
            self.assertIn(mutant, MUTATIONS)
            source = HOST.read_text(encoding="utf-8")
            before, after = MUTATIONS[mutant]
            self.assertEqual(source.count(before), 1, "host mutation anchor must be unique")
            edited = Path(self.directory.name) / "serve-mutant.py"
            edited.write_text(source.replace(before, after), encoding="utf-8", newline="\n")
            runner = ("import pathlib,sys; product,edited,port=sys.argv[1:]; "
                      "sys.argv=[product,port]; "
                      "exec(compile(pathlib.Path(edited).read_text(encoding='utf-8'),product,'exec'),"
                      "{'__name__':'__main__','__file__':product})")
            command = [sys.executable, "-c", runner, str(HOST), str(edited), str(self.port)]
        env = dict(os.environ, GEOMETRY_BRIDGE_EXECUTABLE=self.binary, PYTHONUNBUFFERED="1")
        for name in ("GEOMETRY_BRIDGE_WSL", "GEOMETRY_MANAGED_PREVIEW", "GEOMETRY_WAIT_TRACE"):
            env.pop(name, None)
        self.process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                        stderr=self.errors, start_new_session=os.name != "nt")
        self.addCleanup(self.stop)
        started = queue.Queue()
        threading.Thread(target=lambda: started.put(self.process.stdout.readline()), daemon=True).start()
        try:
            line = started.get(timeout=20).decode("utf-8")
        except queue.Empty:
            self.fail("actual host failed to announce startup: " + self.stderr())
        self.assertIn(f"http://localhost:{self.port}", line, self.stderr())
        status, runtime, headers = self.request("GET", "/runtime")
        self.assertEqual(status, 200, runtime)
        self.assertEqual(runtime["schema"], "geometry-runtime/1")
        self.assertEqual(runtime["pid"], self.process.pid)
        self.assertEqual(Path(runtime["root"]).resolve(), ROOT)
        self.assertTrue(runtime["fresh"], runtime)
        self.session = headers["x-geometry-session"]
        self.assertEqual(self.session, runtime["session"])

    def stderr(self):
        self.errors.seek(0)
        return self.errors.read().decode("utf-8", errors="replace")

    def stop(self):
        if self.process.poll() is None:
            # SIGINT runs the production finally block, which retires all native
            # contexts. Kill the entire private process group only on timeout.
            if os.name != "nt":
                self.process.send_signal(signal.SIGINT)
            else:
                subprocess.run(["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=6, check=False)
            try:
                self.process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(self.process.pid, signal.SIGKILL)
                else:
                    self.process.kill()
                self.process.wait(timeout=3)
        self.process.stdout.close()

    def request(self, method, route, body=None, scenario=None):
        headers = {"Content-Type": "application/json"}
        if scenario:
            headers["X-Geometry-Scenario"] = scenario
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        try:
            connection.request(method, route, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            return response.status, json.loads(payload), dict(response.getheaders()) | {
                key.lower(): value for key, value in response.getheaders()}
        finally:
            connection.close()

    def post(self, route, value, scenario=None, raw=False):
        body = value.encode("utf-8") if raw else json.dumps(value).encode("utf-8")
        status, result, _ = self.request("POST", route, body, scenario)
        self.assertEqual(status, 200, result)
        return result

    def api(self, command, scenario=None, success=True):
        result = self.post("/api", {"cmd": command}, scenario)
        self.assertEqual(result.get("ok"), success, (command, result))
        return result

    def read(self, scenario=None):
        return self.api("identity-read", scenario)

    def mark(self, number, scenario=None):
        before = self.read(scenario)
        self.assertTrue(before["epochSet"], "host must reseed before accepting a new native identity")
        self.api(f"line boundary {number} outline 0,0 800,0 800,700 0,700", scenario)
        after = self.read(scenario)
        mark = next(item["mark"] for item in after["marks"]
                    if item["kind"] == "boundary" and item["id"] == number)
        self.assertRegex(mark, r"^[a-f0-9]{32}:[1-9][0-9]*$")
        epoch, serial = mark.split(":")
        self.assertEqual(int(serial), before["nextSerial"], "HTTP mutation must use the process-wide serial")
        self.assertEqual(after["nextSerial"], before["nextSerial"] + 1)
        return epoch, mark

    def bootstrap(self, scenario=None):
        # Interactive reset is not a whole-world replacement and cannot install
        # an epoch to accidentally hide a missing production startup install.
        self.assertTrue(self.read(scenario)["epochSet"], "startup host epoch is absent")
        self.api("line reset", scenario)
        self.api("line identity-ledger activate", scenario)
        return self.mark(801, scenario)[0]

    def test_L25_startup_public_rejection_and_interactive_history_keep_host_epoch(self):
        epoch = self.bootstrap()
        before = self.read()
        rejected = self.api("identity-epoch " + "f" * 32, success=False)
        self.assertIn("只由宿主設定", rejected["error"])
        self.assertEqual(self.read(), before, "rejected page command must not alter native allocator state")
        second_epoch, second_mark = self.mark(802)
        self.assertEqual(second_epoch, epoch)
        serial = self.read()["nextSerial"]
        self.api("line undo")
        self.assertNotIn(second_mark, [row["mark"] for row in self.read()["marks"]])
        self.assertEqual(self.read()["nextSerial"], serial)
        self.api("line redo")
        self.assertIn(second_mark, [row["mark"] for row in self.read()["marks"]])
        self.assertEqual(self.read()["nextSerial"], serial)
        self.assertEqual(self.mark(803)[0], epoch, "undo/redo must not reseed the host")
        before_reset = self.read()["nextSerial"]
        self.api("line reset")
        after_reset = self.read()
        self.assertTrue(after_reset["active"])
        self.assertEqual(after_reset["marks"], [])
        self.assertEqual(after_reset["nextSerial"], before_reset)
        self.assertEqual(self.mark(804)[0], epoch, "interactive reset must keep the current epoch")

    def test_L25_every_successful_http_whole_world_replacement_reseeds_without_rewinding(self):
        epoch = self.bootstrap()
        used = {epoch}
        for index, route in enumerate(("reset", "default", "loadfile", "upload", "confirm"), start=901):
            with self.subTest(route=route):
                scene = self.api("dump")["text"]
                original = self.read()
                if route in ("reset", "default"):
                    self.api(route)
                elif route == "loadfile":
                    file = Path(self.directory.name) / "reopen.scene"
                    file.write_text(scene, encoding="utf-8", newline="\n")
                    self.api("loadfile " + str(file))
                elif route == "upload":
                    self.assertTrue(self.post("/upload", scene, raw=True)["ok"])
                else:
                    prepared = self.post("/upload/prepare", scene, raw=True)
                    self.assertTrue(prepared["ok"], prepared)
                    self.assertEqual(self.read(), original, "prepare must leave native identity unchanged")
                    committed = self.post("/upload/confirm", prepared["token"])
                    self.assertTrue(committed["ok"], committed)
                    self.assertEqual(committed["state"], "committed")
                replaced = self.read()
                self.assertTrue(replaced["epochSet"], route)
                self.assertEqual(replaced["nextSerial"], original["nextSerial"], route)
                if route in ("loadfile", "upload", "confirm"):
                    self.assertEqual(replaced["marks"], original["marks"], "load restores existing marks without issuing")
                    self.assertEqual(self.api("dump")["text"], scene)
                if not replaced["active"]:
                    self.api("line identity-ledger activate")
                new_epoch, _ = self.mark(index)
                self.assertNotIn(new_epoch, used, route + " must install a fresh host-generated epoch")
                used.add(new_epoch)

    def test_L25_prepare_cancel_and_failed_loads_keep_epoch_world_and_serial(self):
        epoch = self.bootstrap()
        scene = self.api("dump")["text"]
        before = self.read()
        prepared = self.post("/upload/prepare", scene, raw=True)
        self.assertTrue(prepared["ok"], prepared)
        self.assertEqual(self.read(), before)
        self.assertEqual(self.api("dump")["text"], scene)
        self.assertEqual(self.mark(811)[0], epoch, "prepare must not reseed")
        before_cancel = self.read()
        cancelled = self.post("/upload/cancel", prepared["token"])
        self.assertTrue(cancelled["ok"], cancelled)
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertEqual(self.read(), before_cancel)
        self.assertEqual(self.mark(812)[0], epoch, "cancel must not reseed")
        invalid = "this-is-not-a-scene\n"
        file = Path(self.directory.name) / "invalid.scene"
        file.write_text(invalid, encoding="utf-8", newline="\n")
        for index, route in enumerate(("loadfile", "upload", "prepare"), start=821):
            with self.subTest(route=route):
                before = self.read()
                saved = self.api("dump")["text"]
                if route == "loadfile":
                    self.api("loadfile " + str(file), success=False)
                else:
                    endpoint = "/upload/prepare" if route == "prepare" else "/upload"
                    rejected = self.post(endpoint, invalid, raw=True)
                    self.assertFalse(rejected["ok"], rejected)
                self.assertEqual(self.read(), before, "failed load must not consume native serials or replace marks")
                self.assertEqual(self.api("dump")["text"], saved)
                self.assertEqual(self.mark(index)[0], epoch, "failed load must not reseed")

    def test_L25_real_scenario_native_context_gets_a_distinct_host_epoch(self):
        root_epoch = self.bootstrap()
        request = {"action": "create", "requestId": str(uuid.uuid4()), "sequence": 1, "session": self.session}
        created = self.post("/scenarios/editor", request)
        self.assertTrue(created["ok"], created)
        context = created["context"]
        self.assertNotEqual(context, self.session)
        child_epoch = self.bootstrap(context)
        self.assertNotEqual(child_epoch, root_epoch, "separate native processes require distinct host epoch draws")
        self.assertEqual(self.mark(831)[0], root_epoch, "scenario startup must not reseed root")
        self.assertEqual(self.mark(831, context)[0], child_epoch)
        retired = self.post("/scenarios/editor", dict(request, action="close"))
        self.assertTrue(retired["ok"], retired)
        self.assertEqual(retired["state"], "retired")


if __name__ == "__main__":
    unittest.main()
