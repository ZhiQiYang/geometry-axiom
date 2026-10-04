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
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
_STATUSES = {"not-run", "missing-capability", "blocked", "timeout", "crashed",
             "failed", "passed", "stale", "unknown-runtime"}


class ReceiptValidationError(ValueError):
    """Malformed retained host data; preserve its original blob outside this module."""


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
            except (ValueError, UnicodeError, RecursionError):
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
        while self.process.poll() is None:
            self._check()
            try:
                self.process.wait(timeout=min(.05, max(.001, self.deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                continue
        code = self.process.returncode
        for reader in self.readers:
            while reader.is_alive():
                self._check()
                reader.join(timeout=.01)
        self._check()
        if code:
            crashed = code < 0 or code in (0xC0000005, -1073741819)
            raise _Stop("crashed" if crashed else "failed", "native-exit:" + str(code))
        while not self.responses.empty():
            if self.responses.get_nowait() is not None:
                raise _Stop("failed", "unsolicited-native-response")


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
        passed = actual is not None and canonical(actual) == canonical(predicate["value"])
    elif kind == "joint_tuple_equal":
        left, right = _joint(before, predicate["before"]), _joint(after, predicate["after"])
        passed = left is not None and right is not None and canonical(left) == canonical(right)
    elif kind == "complete_flag":
        passed = record is not None and record.get("complete") is predicate["value"]
    elif kind == "exact_typed_ref":
        slots = record["value"].get("slots", []) if record else []
        matches = [s for s in slots if s["slotId"] == predicate["slotId"]]
        passed = (len(matches) == 1
                  and canonical(matches[0][predicate["axis"]]) == canonical(predicate["value"]))
    elif kind == "record_pin_unchanged":
        old = _record(before, predicate["ref"])
        passed = old is not None and record is not None and canonical(old) == canonical(record)
    elif kind == "rejection_world_unchanged":
        passed = unchanged
    else:
        passed = False  # validate_case rejects this; still fail closed.
    return {"kind": kind, "passed": passed, "predicate": deepcopy(predicate)}


def _diagnostic_matches(actual, expected):
    # Human messages are preserved as evidence but never influence verdicts.
    if type(actual) is not dict or type(expected) is not dict:
        return False
    if any(type(actual.get(key)) is not str or actual[key] != expected.get(key)
           for key in ("code", "clause")):
        return False
    if type(actual.get("ref")) is not dict:
        return False
    try:
        return canonical(actual["ref"]) == canonical(expected["ref"])
    except ValueError:
        return False


def _verify_record_pins(state, operations):
    """Native rule/binding definitions must preserve the full typed submitted value.

Parameter input is intentionally normalized into a native AST, so it is not
compared with the input spelling. No effective-value cache substitutes for pins.
"""
    def normalized(value, kind):
        value = deepcopy(value)
        # Native authoring canonicalizes these finite identity arrays. Reordering
        # is permitted by D32 and must not look like a changed member definition.
        keys = {"slots": "id", "members": "id", "joints": "id"} if kind == "rule" else {"slots": "slotId"}
        for field, key in keys.items():
            value[field].sort(key=lambda item: item[key])
        return value

    expected = {}
    for operation in operations:
        if operation["op"] not in ("publish-rule", "create-binding", "put-binding"):
            continue
        value = operation["value"]
        ref = {"kind": "rule" if operation["op"] == "publish-rule" else "binding", "id": value["id"]}
        if ref["kind"] == "rule":
            ref["version"] = value["version"]
        expected[digest(ref)] = ref, value
    for ref, value in expected.values():
        actual = _record(state, ref)
        if (actual is None or digest(normalized(actual["value"], ref["kind"]))
                != digest(normalized(value, ref["kind"]))):
            raise _Stop("failed", "native-record-pin-mismatch")


def _validate_receipt(receipt, definition):
    """Bound retained JSON before copying, and require actual evidence for green.

This is a local host-data guard, not an archive schema or proof of authenticity.
An import policy remains the shared integration owner's responsibility.
"""
    pending, nodes, text_bytes = [(receipt, 0)], 0, 0
    while pending:
        value, depth = pending.pop()
        nodes += 1
        if nodes > 65536 or depth > 32:
            raise ReceiptValidationError("Receipt exceeds node/depth limit")
        if type(value) is dict:
            if len(value) * 2 + nodes + len(pending) > 65536 or any(type(k) is not str for k in value):
                raise ReceiptValidationError("Invalid or oversized receipt object")
            pending.extend((v, depth + 1) for v in value.values())
            pending.extend((k, depth + 1) for k in value)
        elif type(value) is list:
            if len(value) + nodes + len(pending) > 65536:
                raise ReceiptValidationError("Receipt array exceeds node limit")
            pending.extend((v, depth + 1) for v in value)
        elif type(value) is str:
            if len(value) > MAX_RECEIPT_BYTES:
                raise ReceiptValidationError("Receipt string exceeds byte limit")
            try:
                text_bytes += len(value.encode("utf-8"))
            except UnicodeEncodeError as error:
                raise ReceiptValidationError("Receipt is not UTF-8 JSON") from error
            if text_bytes > MAX_RECEIPT_BYTES:
                raise ReceiptValidationError("Receipt exceeds byte limit")
        elif type(value) in (int, float):
            if (type(value) is float and not math.isfinite(value)
                    or type(value) is int and not -(2**63 - 1) <= value <= 2**63 - 1):
                raise ReceiptValidationError("Invalid receipt number")
        elif value is not None and type(value) is not bool:
            raise ReceiptValidationError("Receipt contains a non-JSON value")
    if len(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")).encode()) > MAX_RECEIPT_BYTES:
        raise ReceiptValidationError("Receipt exceeds encoded byte limit")
    if (type(receipt) is not dict or type(receipt.get("status")) is not str
            or receipt["status"] not in _STATUSES):
        raise ReceiptValidationError("Receipt needs a known nonpass/pass status")
    if "recordedStatus" in receipt and (type(receipt["recordedStatus"]) is not str
            or receipt["recordedStatus"] not in _STATUSES - {"stale"}):
        raise ReceiptValidationError("Unknown recorded receipt status")
    if receipt["status"] != "passed" and receipt.get("recordedStatus") != "passed":
        return
    try:
        expected, observed = receipt["authorExpected"], receipt["observations"]
        conditions, identity = receipt["conditions"], receipt["executor"]
        assertions = receipt["assertionResults"]
        diagnostics, scope = receipt["actualDiagnostics"], receipt["context"]
        if (expected["outcome"] not in ("accepted", "rejected")
                or receipt["actualOutcome"] != expected["outcome"]
                or conditions["isolated"] is not True or conditions["privateDirectoryRemoved"] is not True
                or type(conditions["nativePid"]) is not int or conditions["nativePid"] <= 0
                or identity["known"] is not True or type(assertions) is not list
                or not 1 <= len(assertions) <= 32 or type(diagnostics) is not list
                or any(type(d) is not dict for d in diagnostics)
                or type(scope["projectId"]) is not str or not 1 <= len(scope["projectId"].encode()) <= 128
                or type(scope["generation"]) is not int or not 0 <= scope["generation"] <= 2**53 - 1
                or type(conditions["timeoutSeconds"]) not in (int, float)
                or not .01 <= conditions["timeoutSeconds"] <= 30
                or type(conditions["maxOutputBytes"]) is not int
                or not 1 <= conditions["maxOutputBytes"] <= MAX_OUTPUT_BYTES
                or type(conditions["capabilities"]) is not list
                or any(type(c) is not str for c in conditions["capabilities"])
                or type(conditions["elapsedSeconds"]) not in (int, float) or conditions["elapsedSeconds"] < 0):
            raise ReceiptValidationError("Passed receipt lacks native evidence")
        for key in ("nativeBinaryHash", "nativeSourceHash", "validatorVersion", "axiomHash", "assertionSchemaHash"):
            value = identity[key]
            if type(value) is not str or len(value) != 64 or set(value) - set("0123456789abcdef"):
                raise ReceiptValidationError("Passed receipt lacks exact runtime identity")
        for key in ("beforeDumpHash", "afterDumpHash"):
            value = observed[key]
            if type(value) is not str or len(value) != 64 or set(value) - set("0123456789abcdef"):
                raise ReceiptValidationError("Passed receipt lacks dump evidence")
        for key in ("beforeRevision", "afterRevision"):
            if type(observed[key]) is not int or observed[key] < 0:
                raise ReceiptValidationError("Passed receipt lacks native revisions")
        if type(observed["before"]) is not dict or type(observed["after"]) is not dict:
            raise ReceiptValidationError("Passed receipt lacks native states")
        unchanged = (receipt["actualOutcome"] == "rejected" and observed["before"] == observed["after"]
                     and observed["beforeRevision"] == observed["afterRevision"]
                     and observed["beforeDumpHash"] == observed["afterDumpHash"])
        if expected["outcome"] == "rejected" and (not unchanged or expected["diagnostic"] is None
                or not any(_diagnostic_matches(d, expected["diagnostic"]) for d in receipt["actualDiagnostics"])):
            raise ReceiptValidationError("Passed negative receipt lacks exact rejection evidence")
        predicates = []
        for assertion in assertions:
            predicate = assertion["predicate"]
            if (assertion["passed"] is not True or assertion["kind"] != predicate["kind"]
                    or not _assert(predicate, observed["before"], observed["after"], unchanged)["passed"]):
                raise ReceiptValidationError("Passed receipt contains an invalid assertion")
            predicates.append(predicate)
        if receipt.get("definitionHash") == definition_hash(definition):
            if (canonical(predicates) != canonical(definition["assertions"])
                    or canonical(expected) != canonical(definition["expect"])):
                raise ReceiptValidationError("Passed receipt differs from the exact case contract")
            if not set(definition["requiredCapabilities"]) <= set(conditions["capabilities"]):
                raise ReceiptValidationError("Passed receipt lacks required native capabilities")
            _verify_record_pins(observed["before"], definition["input"]["setup"])
            if expected["outcome"] == "accepted":
                _verify_record_pins(observed["after"], definition["input"]["transaction"])
    except _Stop as error:
        raise ReceiptValidationError("Passed receipt changed exact native record pins") from error
    except ValueError as error:
        if isinstance(error, ReceiptValidationError):
            raise
        raise ReceiptValidationError("Passed receipt has invalid typed evidence") from error
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ReceiptValidationError("Passed receipt has malformed native evidence") from error


def refresh_receipt(receipt, definition, identity, *, project_id=None, generation=None):
    """Copy a retained receipt; changed exact domains become stale without losing evidence."""
    definition = validate_case(definition)
    _validate_receipt(receipt, definition)
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
        except (KeyError, TypeError, ValueError, AttributeError, RecursionError, IndexError) as error:
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
        _verify_record_pins(before["state"], definition["input"]["setup"])
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
        if valid:
            _verify_record_pins(after["state"], definition["input"]["transaction"])
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
