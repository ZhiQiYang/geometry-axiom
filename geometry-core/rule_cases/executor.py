"""Bounded fresh native Worlds and finite typed observations for #49.

The host supplies a binary path, project identity and generation. Case JSON supplies
only typed authoring operations: it cannot choose a path, command or program.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import shutil
import signal
import subprocess
import tempfile
import threading
import time

from .definition import canonical, definition_hash, digest, validate_case
from .runtime import runtime_identity

MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_CONCURRENT_RUNS = 2
_SLOTS = threading.BoundedSemaphore(MAX_CONCURRENT_RUNS)


class _Stop(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


class _Child:
    """One trusted bridge, private cwd; capped pipe readers avoid unbounded readline."""
    def __init__(self, binary, directory, deadline, cancel, output_limit):
        self.deadline, self.cancel, self.output_limit = deadline, cancel, output_limit
        self.responses = queue.Queue(maxsize=32)
        self.halt = threading.Event()
        self.lock = threading.Lock()
        self.output_bytes = 0
        self.failure = None
        self.stderr = bytearray()
        self.process = subprocess.Popen([str(binary)], cwd=directory, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=os.name != "nt")
        self.readers = [threading.Thread(target=self._read, args=(stream, err), daemon=True)
                        for stream, err in ((self.process.stdout, False), (self.process.stderr, True))]
        for reader in self.readers:
            reader.start()

    def _read(self, stream, is_error):
        try:
            while not self.halt.is_set():
                data = stream.read1(4096) if is_error else stream.readline(self.output_limit + 1)
                if not data:
                    if not is_error:
                        self.responses.put_nowait(None)
                    return
                with self.lock:
                    self.output_bytes += len(data)
                    if self.output_bytes > self.output_limit:
                        self.failure = _Stop("blocked", "output-capacity")
                        return
                if is_error:
                    if len(self.stderr) < 4096:
                        self.stderr.extend(data[:4096 - len(self.stderr)])
                else:
                    self.responses.put_nowait(data)
        except (OSError, ValueError, queue.Full):
            self.failure = _Stop("blocked", "native-protocol-capacity")

    def _check(self):
        if self.failure:
            raise self.failure
        if self.cancel is not None and self.cancel.is_set():
            raise _Stop("blocked", "cancelled")
        if time.monotonic() >= self.deadline:
            raise _Stop("timeout", "wall-time-limit")

    def command(self, command):
        self._check()
        try:
            self.process.stdin.write((command + "\n").encode())
            self.process.stdin.flush()
        except (OSError, ValueError):
            self._exit()
        while True:
            self._check()
            try:
                data = self.responses.get(timeout=min(.05, max(.001, self.deadline - time.monotonic())))
            except queue.Empty:
                if self.process.poll() is not None:
                    self._exit()
                continue
            if data is None:
                self._exit()
            try:
                value = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeError):
                raise _Stop("failed", "invalid-native-json")
            if not isinstance(value, dict):
                raise _Stop("failed", "invalid-native-response")
            self._check()
            return value

    def _exit(self):
        try:
            code = self.process.wait(timeout=min(.1, max(.001, self.deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            raise _Stop("failed", "native-protocol-closed")
        crashed = code < 0 or code in (0xC0000005, -1073741819)
        raise _Stop("crashed" if crashed else "failed", "native-exit:" + str(code))

    def stop(self):
        self.halt.set()
        if os.name != "nt":
            # Descendants can retain pipes after their leader exits. Reap the
            # whole private group before joining readers or closing streams.
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=2)
        for reader in self.readers:
            reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()

    def finish(self):
        """A completed verdict still requires a clean native exit and bounded output."""
        self._check()
        self.process.stdin.close()
        try:
            code = self.process.wait(timeout=max(.001, self.deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            raise _Stop("timeout", "wall-time-limit")
        for reader in self.readers:
            reader.join(timeout=max(.001, self.deadline - time.monotonic()))
        self._check()
        if code:
            crashed = code < 0 or code in (0xC0000005, -1073741819)
            raise _Stop("crashed" if crashed else "failed", "native-exit:" + str(code))


def _record(state, ref):
    collection = "rules" if ref["kind"] == "rule" else "bindings"
    matches = [r for r in state.get(collection, []) if r["value"]["id"] == ref["id"]
               and (ref["kind"] != "rule" or r["value"]["version"] == ref["version"])]
    return matches[0] if len(matches) == 1 else None


def _joint(state, selector):
    record = _record(state, selector["ref"])
    if not record:
        return None
    matches = [j for j in record["value"].get("joints", []) if j["id"] == selector["jointId"]]
    return matches[0] if len(matches) == 1 else None


def _assert(predicate, before, after, unchanged):
    kind = predicate["kind"]
    record = _record(after, predicate["ref"]) if "ref" in predicate else None
    if kind == "record_exists":
        passed = record is not None
    elif kind == "member_slot":
        members = record["value"].get("members", []) if record else []
        matches = [m for m in members if m["id"] == predicate["memberId"]]
        passed = len(matches) == 1 and matches[0]["slotId"] == predicate["slotId"]
    elif kind == "joint_tuple":
        actual = _joint(after, predicate)
        passed = actual is not None and actual == predicate["value"]
    elif kind == "joint_tuple_equal":
        left, right = _joint(before, predicate["before"]), _joint(after, predicate["after"])
        passed = left is not None and right is not None and left == right
    elif kind == "complete_flag":
        passed = record is not None and record.get("complete") is predicate["value"]
    elif kind == "exact_typed_ref":
        slots = record["value"].get("slots", []) if record else []
        matches = [s for s in slots if s["slotId"] == predicate["slotId"]]
        passed = len(matches) == 1 and matches[0][predicate["axis"]] == predicate["value"]
    elif kind == "record_pin_unchanged":
        old = _record(before, predicate["ref"])
        passed = old is not None and record is not None and old == record
    elif kind == "rejection_world_unchanged":
        passed = unchanged
    else:
        passed = False  # validate_case rejects this; still fail closed.
    return {"kind": kind, "passed": passed, "predicate": deepcopy(predicate)}


def _diagnostic_matches(actual, expected):
    # Human messages are preserved as evidence but never influence verdicts.
    return all(actual.get(key) == expected[key] for key in ("code", "clause", "ref"))


def refresh_receipt(receipt, definition, identity, *, project_id=None, generation=None):
    """Copy a retained receipt; changed exact domains become stale without losing evidence."""
    definition = validate_case(definition)
    result = deepcopy(receipt)
    reasons = []
    if result.get("caseId") != definition["caseId"] or result.get("definitionHash") != definition_hash(definition):
        reasons.append("definition")
    if result.get("sourceHash") != digest(definition["sourcePins"]):
        reasons.append("source")
    if not identity.get("known"):
        reasons.append("unknown-runtime")
    elif result.get("executor") != identity:
        reasons.append("runtime")
    scope = result.get("context", {})
    if project_id is not None and scope.get("projectId") != project_id:
        reasons.append("project-context")
    if generation is not None and scope.get("generation") != generation:
        reasons.append("generation")
    if reasons:
        result.setdefault("recordedStatus", result.get("status"))
        result["status"], result["staleReasons"] = "stale", reasons
    return result


class NativeExecutor:
    def __init__(self, binary=None, *, timeout_seconds=5, max_output_bytes=MAX_OUTPUT_BYTES):
        if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
                or not .01 <= timeout_seconds <= 30):
            raise ValueError("timeout_seconds must be .01–30")
        if type(max_output_bytes) is not int or not 1 <= max_output_bytes <= MAX_OUTPUT_BYTES:
            raise ValueError("max_output_bytes must be 1–2097152")
        self.binary, self.timeout, self.output_limit = binary, timeout_seconds, max_output_bytes

    def run(self, definition, *, project_id, generation, cancel=None):
        definition = validate_case(definition)
        if not isinstance(project_id, str) or not 1 <= len(project_id.encode()) <= 128:
            raise ValueError("project_id must be a nonempty bounded string")
        if type(generation) is not int or not 0 <= generation <= 2**53 - 1:
            raise ValueError("generation must be a bounded nonnegative integer")
        started = time.monotonic()
        identity, binary = runtime_identity(self.binary)
        receipt = {"caseId": definition["caseId"], "definitionHash": definition_hash(definition),
                   "sourceHash": digest(definition["sourcePins"]), "executor": identity,
                   "context": {"projectId": project_id, "generation": generation},
                   "status": "not-run", "authorExpected": deepcopy(definition["expect"]),
                   "actualOutcome": None, "actualDiagnostics": [], "assertionResults": [],
                   "conditions": {"timeoutSeconds": self.timeout, "maxOutputBytes": self.output_limit,
                                  "isolated": True, "nativePid": None, "privateDirectoryRemoved": True}}
        if not identity["known"]:
            receipt.update(status="unknown-runtime", reason=identity["reason"])
            return receipt
        if not _SLOTS.acquire(blocking=False):
            receipt.update(status="blocked", reason="concurrency-capacity")
            return receipt
        child = None
        directory = None
        try:
            with tempfile.TemporaryDirectory(prefix="geometry-rule-case-") as name:
                directory = Path(name)
                snapshot = directory / ("bridge.exe" if os.name == "nt" else "bridge")
                shutil.copy2(binary, snapshot)
                if hashlib.sha256(snapshot.read_bytes()).hexdigest() != identity["nativeBinaryHash"]:
                    raise _Stop("unknown-runtime", "binary-changed-before-start")
                child = _Child(snapshot, directory, time.monotonic() + self.timeout, cancel, self.output_limit)
                receipt["conditions"]["nativePid"] = child.process.pid
                try:
                    self._execute(child, directory, definition, receipt)
                    child.finish()
                finally:
                    child.stop()
        except _Stop as stop:
            receipt.update(status=stop.status, reason=stop.reason)
        except (OSError, subprocess.SubprocessError) as error:
            receipt.update(status="blocked", reason="native-environment", detail=str(error))
        except (KeyError, TypeError, ValueError) as error:
            receipt.update(status="failed", reason="native-contract", detail=str(error))
        finally:
            _SLOTS.release()
            receipt["conditions"].update(elapsedSeconds=round(time.monotonic() - started, 6),
                                          privateDirectoryRemoved=directory is None or not directory.exists())
        final_identity, _ = runtime_identity(self.binary)
        return refresh_receipt(receipt, definition, final_identity)

    def _execute(self, child, directory, definition, receipt):
        def command(text):
            reply = child.command(text)
            if reply.get("ok") is not True:
                raise _Stop("failed", "native-command-rejected")
            return reply

        def read():
            return command("assembly-read")

        def preview(operations, filename):
            payload = {"schema": "assembly-transaction/1", "expectedRevision": read()["revision"],
                       "operations": operations}
            path = directory / filename
            path.write_bytes(canonical(payload))
            return command("assembly-preview " + str(path))["preview"]

        command("reset")  # This is exclusively the newly spawned private World.
        caps = command("engineering-read")["state"]["capabilities"]
        missing = sorted(set(definition["requiredCapabilities"]) - set(caps))
        receipt["conditions"]["capabilities"] = caps
        if missing:
            receipt["missingCapabilities"] = missing
            raise _Stop("missing-capability", "required-capability")
        if definition["input"]["setup"]:
            seeded = preview(definition["input"]["setup"], "setup.json")
            if seeded.get("valid") is not True:
                receipt["setupDiagnostics"] = seeded.get("violations", [])
                raise _Stop("failed", "invalid-source-closure")
            command("assembly-confirm " + str(seeded["token"]))
        before, before_dump = read(), command("dump")["text"]
        candidate = preview(definition["input"]["transaction"], "case.json")
        valid = candidate.get("valid")
        if type(valid) is not bool:
            raise _Stop("failed", "missing-native-verdict")
        receipt["actualOutcome"] = "accepted" if valid else "rejected"
        receipt["actualDiagnostics"] = candidate["violations"]
        if valid:
            command("assembly-confirm " + str(candidate["token"]))
        else:
            # Exercise the invalid token guard too; only this private process is touched.
            rejected = child.command("assembly-confirm " + str(candidate["token"]))
            if rejected.get("ok") is not False:
                raise _Stop("failed", "invalid-candidate-confirmed")
        after, after_dump = read(), command("dump")["text"]
        unchanged = not valid and before == after and before_dump == after_dump
        receipt["observations"] = {"before": before["state"], "after": after["state"],
                                   "beforeRevision": before["revision"], "afterRevision": after["revision"],
                                   "beforeDumpHash": hashlib.sha256(before_dump.encode()).hexdigest(),
                                   "afterDumpHash": hashlib.sha256(after_dump.encode()).hexdigest()}
        receipt["assertionResults"] = [_assert(p, before["state"], after["state"], unchanged)
                                       for p in definition["assertions"]]
        if receipt["actualOutcome"] != definition["expect"]["outcome"]:
            raise _Stop("failed", "outcome-mismatch")
        if not valid and not unchanged:
            raise _Stop("failed", "rejected-world-changed")
        if not all(a["passed"] for a in receipt["assertionResults"]):
            raise _Stop("failed", "assertion-mismatch")
        if not valid:
            expected = definition["expect"]["diagnostic"]
            if not any(_diagnostic_matches(d, expected) for d in receipt["actualDiagnostics"]):
                generic = any(d.get("code") == "ASSEMBLY_INVALID" and "ref" not in d
                              for d in receipt["actualDiagnostics"])
                raise _Stop("blocked" if generic else "failed",
                            "diagnostic-unavailable" if generic else "diagnostic-mismatch")
        receipt["status"] = "passed"
