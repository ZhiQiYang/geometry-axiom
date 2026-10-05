"""Unregistered, finite #49 HTTP seam. Host owns scope, binary and save routing.

No live bridge, assembly preview, native World or project store is accessed.
dispatch() is shared by the owner's future route and the independent harness.
"""
from copy import deepcopy
import json
import math
import re
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))
from rule_cases.catalog import cases
from rule_cases.definition import (CaseDefinitionError, MAX_CASE_BYTES, decode_case,
                                   canonical, definition_hash, digest, validate_cases, _operation, _ref)
from rule_cases.executor import ReceiptValidationError, refresh_receipt
from rule_cases.request import run_case_request
from rule_cases.runtime import runtime_identity

PROTOCOL = "rule-case-workbench/1"  # Transport only; no formal canvas format allocation.
DATA_SCHEMA = "rule-case-workbench-data/1"  # Proposal for host-owned attachment payload.
MAX_DATA_BYTES = 8 * 1024 * 1024
MAX_RECEIPTS = 24
MAX_SESSIONS = 16
MAX_RUNS_PER_SESSION = 64
SESSION_SECONDS = 300
_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


class AdapterError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _keys(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise AdapterError("SCHEMA", "Unknown or missing envelope fields")


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def _decode(body):
    if type(body) is not bytes or len(body) > MAX_DATA_BYTES:
        raise AdapterError("CAPACITY", "HTTP payload exceeds 8 MiB")
    # Bound nesting before decoder recursion, including retained native observations.
    try:
        text = body.decode("utf-8")
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 40:
                    raise AdapterError("CAPACITY", "HTTP JSON nesting limit exceeded")
            elif char in "]}":
                depth -= 1

        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise AdapterError("SCHEMA", "Duplicate JSON key")
                result[key] = value
            return result

        def invalid_constant(_):
            raise AdapterError("SCHEMA", "Nonfinite JSON number")

        return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        if isinstance(error, AdapterError):
            raise
        raise AdapterError("SCHEMA", "Invalid UTF-8 JSON") from error


def _definition(value):
    # Use the existing strict integer-only decoder, source closure and pins.
    return decode_case(_json(value))


def _context(value):
    _keys(value, ("projectId", "generation", "contextToken"))
    if (type(value["projectId"]) is not str or not 1 <= len(value["projectId"].encode()) <= 128
            or type(value["generation"]) is not int or not 0 <= value["generation"] <= 2**53 - 1
            or type(value["contextToken"]) is not str or not 1 <= len(value["contextToken"].encode()) <= 256):
        raise AdapterError("SCOPE", "Host supplied an invalid context")
    return deepcopy(value)


def _shape(value, required, optional=()):
    if (type(value) is not dict or not set(required) <= value.keys()
            or value.keys() - set(required) - set(optional)):
        raise AdapterError("RECEIPT", "Unknown or missing portable receipt fields")


def _text(value, maximum=4096):
    if type(value) is not str or len(value.encode()) > maximum:
        raise AdapterError("RECEIPT", "Invalid bounded receipt text")


def _integer(value, maximum=2**53 - 1):
    if type(value) is not int or not 0 <= value <= maximum:
        raise AdapterError("RECEIPT", "Invalid bounded receipt integer")


def _number(value, minimum, maximum):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise AdapterError("RECEIPT", "Invalid bounded receipt number")


def _hash(value):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise AdapterError("RECEIPT", "Invalid exact receipt hash")


def _array(value, maximum):
    if type(value) is not list or len(value) > maximum:
        raise AdapterError("RECEIPT", "Invalid bounded receipt array")


def _capabilities(value):
    _array(value, 32)
    for item in value:
        if type(item) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,95}", item):
            raise AdapterError("RECEIPT", "Invalid capability identity")
    if len(set(value)) != len(value):
        raise AdapterError("RECEIPT", "Duplicate receipt capabilities")


def _diagnostics(value):
    _array(value, 256)
    for item in value:
        # Preserve both typed authoring diagnostics and the native legacy I8
        # invariant detail. Human text never creates a typed reference.
        _shape(item, ("clause", "message"), ("code", "ref", "timber", "expected"))
        for key in ("clause", "message", "code", "expected"):
            if key in item:
                _text(item[key], 64 if key in {"clause", "code"} else 4096)
        if "timber" in item:
            _integer(item["timber"], 4294967295)
        if "ref" in item:
            _ref(item["ref"], "receipt.diagnostic.ref", diagnostic=True)


def _observed_state(value):
    _shape(value, ("capabilities", "rules", "bindings", "instances"))
    _capabilities(value["capabilities"])
    # These six authoring cases cannot create construction instances.
    if value["instances"] != []:
        raise AdapterError("RECEIPT", "Authoring case observation contains unsupported instances")
    for kind, operation in (("rules", "publish-rule"), ("bindings", "create-binding")):
        _array(value[kind], 64)
        for record in value[kind]:
            required = ("value", "fingerprint") + (("complete", "effective") if kind == "bindings" else ())
            _shape(record, required)
            _hash(record["fingerprint"])
            # Reuse the core's existing typed RECORD schema, without executing
            # operations or inventing a second geometry/diagnostic validator.
            _operation({"op": operation, "value": record["value"]}, "receipt.observation", [], set())
            if kind == "bindings":
                if type(record["complete"]) is not bool:
                    raise AdapterError("RECEIPT", "Invalid native completeness flag")
                _array(record["effective"], 8)
                for slot in record["effective"]:
                    _shape(slot, ("slotId", "A", "B"))
                    _integer(slot["slotId"], 4294967295)
                    for axis in ("A", "B"):
                        effective = slot[axis]
                        if effective is not None:
                            _shape(effective, ("value", "path"))
                            _number(effective["value"], -100000000, 100000000)
                            # This is native source-description text, not an OS
                            # path/assetref accepted at arbitrary receipt keys.
                            _text(effective["path"], 2047)


def _portable_receipt(receipt, original, identity):
    # Existing core guard bounds bytes/nodes/depth and native pass evidence for
    # EVERY receipt before this finite transport schema traverses nested data.
    refresh_receipt(receipt, original, identity)
    required = ("caseId", "definitionHash", "sourceHash", "executor", "context", "status",
                "authorExpected", "actualOutcome", "actualDiagnostics", "assertionResults", "conditions")
    _shape(receipt, required, ("reason", "detail", "recordedStatus", "staleReasons",
                               "setupDiagnostics", "observations", "missingCapabilities"))
    if (receipt["caseId"] != original["caseId"]
            or receipt["definitionHash"] != definition_hash(original)
            or receipt["sourceHash"] != digest(original["sourcePins"])
            or canonical(receipt["authorExpected"]) != canonical(original["expect"])):
        raise AdapterError("OWNERSHIP", "Receipt does not belong to its recorded original definition/pins")
    _shape(receipt["context"], ("projectId", "generation"))
    executor = receipt["executor"]
    runtime_fields = ("nativeBinaryHash", "nativeSourceHash", "validatorVersion", "axiomHash", "assertionSchemaHash")
    _shape(executor, ("known",) + (runtime_fields if executor["known"] else ("reason",)))
    if executor["known"]:
        for field in runtime_fields:
            _hash(executor[field])
    else:
        _text(executor["reason"])
    conditions = receipt["conditions"]
    _shape(conditions, ("timeoutSeconds", "maxOutputBytes", "isolated", "nativePid", "privateDirectoryRemoved"),
           ("capabilities", "elapsedSeconds"))
    _number(conditions["timeoutSeconds"], .01, 30)
    _integer(conditions["maxOutputBytes"], 2 * 1024 * 1024)
    if conditions["maxOutputBytes"] < 1 or conditions["isolated"] is not True or type(conditions["privateDirectoryRemoved"]) is not bool:
        raise AdapterError("RECEIPT", "Invalid isolated execution conditions")
    if conditions["nativePid"] is not None:
        _integer(conditions["nativePid"], 2**32 - 1)
    if "elapsedSeconds" in conditions:
        _number(conditions["elapsedSeconds"], 0, 60)
    if "capabilities" in conditions:
        _capabilities(conditions["capabilities"])
    if receipt["actualOutcome"] not in (None, "accepted", "rejected"):
        raise AdapterError("RECEIPT", "Unknown actual outcome")
    _diagnostics(receipt["actualDiagnostics"])
    if "setupDiagnostics" in receipt:
        _diagnostics(receipt["setupDiagnostics"])
    if "missingCapabilities" in receipt:
        _capabilities(receipt["missingCapabilities"])
    for key in ("reason", "detail"):
        if key in receipt:
            _text(receipt[key])
    _array(receipt["assertionResults"], len(original["assertions"]))
    for index, assertion in enumerate(receipt["assertionResults"]):
        _shape(assertion, ("kind", "passed", "predicate"))
        if (type(assertion["passed"]) is not bool or assertion["kind"] != original["assertions"][index]["kind"]
                or canonical(assertion["predicate"]) != canonical(original["assertions"][index])):
            raise AdapterError("RECEIPT", "Assertion differs from its original finite predicate")
    if "observations" in receipt:
        observed = receipt["observations"]
        _shape(observed, ("before", "after", "beforeRevision", "afterRevision", "beforeDumpHash", "afterDumpHash"))
        for key in ("before", "after"):
            _observed_state(observed[key])
        for key in ("beforeRevision", "afterRevision"):
            _integer(observed[key])
        for key in ("beforeDumpHash", "afterDumpHash"):
            _hash(observed[key])


def validate_case_data(data, identity, context):
    """Validate all before replacement; preserve raw receipt and its old definition.

An internally consistent import is still historical-unverified. Hashes are
freshness facts, never signatures or evidence that this adapter executed it.
"""
    _keys(data, ("schema", "definitions", "receipts"))
    if data["schema"] != DATA_SCHEMA:
        raise AdapterError("FORMAT", "Unsupported case data schema")
    if len(_json(data)) > MAX_DATA_BYTES:
        raise AdapterError("CAPACITY", "Case data exceeds 8 MiB")
    definitions = validate_cases(data["definitions"])
    by_id = {d["caseId"]: d for d in definitions}
    if set(by_id) != {d["caseId"] for d in cases()}:
        raise AdapterError("SCHEMA", "Workbench data must contain the six adopted case identities")
    if type(data["receipts"]) is not list or len(data["receipts"]) > MAX_RECEIPTS:
        raise AdapterError("CAPACITY", "At most 24 receipts are permitted")
    views = []
    for entry in data["receipts"]:
        _keys(entry, ("definition", "receipt"))
        original = _definition(entry["definition"])
        receipt = entry["receipt"]
        case_id = original["caseId"]
        if case_id not in by_id or type(receipt) is not dict or receipt.get("caseId") != case_id:
            raise AdapterError("SCHEMA", "Receipt is outside the definition set")
        # Validate evidence against the recorded contract first, then assess drift.
        _portable_receipt(receipt, original, identity)
        view = refresh_receipt(receipt, by_id[case_id], identity,
                               project_id=context["projectId"], generation=context["generation"])
        views.append({"trust": "historical-unverified", "receipt": view})
    return {"data": deepcopy(data), "views": views, "runtime": deepcopy(identity),
            "definitionHashes": {d["caseId"]: definition_hash(d) for d in definitions}}


class RuleCaseWorkbenchAdapter:
    """One serial case writer; short-lived sessions fence close/reopen and late runs.

capture_context is a synchronous host port returning the ORIGINAL projectId,
generation and contextToken. These never come from HTTP JSON. Host must call
invalidate() on undo/reopen/project/generation changes; the final equality gate
also catches a change occurring while the native child is working.
"""
    def __init__(self, *, capture_context, binary=None, timeout_seconds=5,
                 max_output_bytes=2 * 1024 * 1024):
        self.capture_context = capture_context
        self.binary = binary
        # Validate host limits with the existing executor without starting it.
        from rule_cases.executor import NativeExecutor
        NativeExecutor(binary, timeout_seconds=timeout_seconds, max_output_bytes=max_output_bytes)
        self.timeout = timeout_seconds
        self.output_limit = max_output_bytes
        self.lock = threading.RLock()
        self.sessions = {}
        self.active = None
        self.closed = False

    def invalidate(self):
        with self.lock:
            for session in self.sessions.values():
                session["closed"] = True
                for event in session["runs"].values():
                    event.set()

    def close(self):
        with self.lock:
            self.closed = True
            self.invalidate()

    def _scope(self):
        return _context(self.capture_context())

    def _prune(self):
        now = time.monotonic()
        for key, session in list(self.sessions.items()):
            if session["closed"] or now - session["started"] > SESSION_SECONDS:
                session["closed"] = True
                for event in session["runs"].values():
                    event.set()
                if not self.active or self.active[0] != key:
                    del self.sessions[key]

    def _session(self, session_id):
        self._prune()
        session = self.sessions.get(session_id) if type(session_id) is str else None
        if (self.closed or session is None or session["closed"]
                or session["context"] != self._scope()):
            if session:
                session["closed"] = True
                for event in session["runs"].values():
                    event.set()
            raise AdapterError("RETIRED", "Case session is closed, expired or belongs to an old context")
        return session

    def dispatch(self, method, path, body=b""):
        """Return (HTTP status, JSON object); no route is installed by importing."""
        try:
            if path != "/rule-cases/workbench" or method != "POST":
                return 404, {"ok": False, "code": "ROUTE", "error": "Unknown case route"}
            payload = _decode(body)
            if type(payload) is not dict or payload.get("protocol") != PROTOCOL:
                raise AdapterError("FORMAT", "Unsupported case transport protocol")
            action = payload.get("action")
            fields = {
                "open": (), "close": ("sessionId",),
                "cancel": ("sessionId", "runId"),
                "validate": ("sessionId", "definition"),
                "run": ("sessionId", "runId", "definition"),
                "import": ("sessionId", "data"),
                "assess": ("sessionId", "data"),
            }
            if type(action) is not str or action not in fields:
                raise AdapterError("SCHEMA", "Unknown case action")
            _keys(payload, ("protocol", "action") + fields[action])
            if action == "open":
                with self.lock:
                    self._prune()
                    if self.closed or len(self.sessions) >= MAX_SESSIONS:
                        raise AdapterError("CAPACITY", "Case session capacity exhausted")
                    session_id = uuid.uuid4().hex
                    context = self._scope()
                    self.sessions[session_id] = {"context": context, "started": time.monotonic(),
                                                 "closed": False, "runs": {}}
                identity, _ = runtime_identity(self.binary)
                definitions = cases()
                return 200, {"ok": True, "sessionId": session_id, "context": context,
                             "runtime": identity, "definitions": definitions,
                             "definitionHashes": {d["caseId"]: definition_hash(d) for d in definitions}}
            if action == "close":
                with self.lock:
                    session = self.sessions.get(payload["sessionId"]) if type(payload["sessionId"]) is str else None
                    if session:
                        session["closed"] = True
                        for event in session["runs"].values():
                            event.set()
                return 200, {"ok": True, "state": "retired"}
            with self.lock:
                session = self._session(payload["sessionId"])
                captured = deepcopy(session["context"])
                if action in {"cancel", "run"}:
                    run_id = payload["runId"]
                    if type(run_id) is not str or not _ID.fullmatch(run_id):
                        raise AdapterError("SCHEMA", "Invalid case run identity")
                    event = session["runs"].get(run_id)
                    if action == "run" and event is not None:
                        raise AdapterError("RETIRED", "Case run identity already used or cancelled")
                    if event is None:
                        if len(session["runs"]) >= MAX_RUNS_PER_SESSION:
                            raise AdapterError("CAPACITY", "Reopen the case panel after 64 run identities")
                        event = threading.Event()
                        session["runs"][run_id] = event
                    if action == "cancel":
                        event.set()
                        return 200, {"ok": True, "state": "cancelled"}
                    if self.active is not None:
                        event.set()
                        raise AdapterError("BUSY", "One selected case is already running")
                    # Reserve before definition validation: cancel/close cannot be revived.
                    self.active = (payload["sessionId"], run_id)
            if action in {"import", "assess"}:
                identity, _ = runtime_identity(self.binary)
                result = validate_case_data(payload["data"], identity, captured)
            elif action == "validate":
                definition = _definition(payload["definition"])
                result = {"definition": definition, "definitionHash": definition_hash(definition)}
            else:
                try:
                    definition = _definition(payload["definition"])
                    receipt = run_case_request(_json(definition), project_id=captured["projectId"],
                                               generation=captured["generation"], binary=self.binary,
                                               cancel=event, timeout_seconds=self.timeout,
                                               max_output_bytes=self.output_limit)
                    result = {"runId": run_id, "definitionHash": definition_hash(definition),
                              "receipt": receipt, "trust": "controlled-run"}
                finally:
                    with self.lock:
                        if self.active == (payload["sessionId"], run_id):
                            self.active = None
            with self.lock:
                self._session(payload["sessionId"])
                if captured != self._scope() or (action == "run" and event.is_set()):
                    raise AdapterError("RETIRED", "Late result discarded from its original context")
            return 200, {"ok": True, "context": captured, **result}
        except (AdapterError, CaseDefinitionError, ReceiptValidationError, ValueError,
                TypeError, RecursionError, OverflowError) as error:
            return 409 if getattr(error, "code", "") in {"RETIRED", "BUSY"} else 400, {
                "ok": False, "code": getattr(error, "code", "RECEIPT"), "error": str(error)}
