"""Short lived immutable host scopes for one selected native context.

Logical project/frame fields are host observations, not server authentication.
This counter is independent of the A/B editor allocator and native history.
"""
from copy import deepcopy
import json
import threading
import time

from rule_case_workbench_adapter import (AdapterError, RuleCaseWorkbenchAdapter,
    SESSION_SECONDS, _context, _decode, _keys, validate_case_data)
from rule_cases.runtime import runtime_identity

PROTOCOL = "rule-case-binding/1"


class RuleCaseHost:
    def __init__(self, native, *, read_native, version, fresh, binary=None):
        self.native, self.read_native = native, read_native
        self.version, self.fresh, self.binary = version, fresh, binary
        self.lock = threading.RLock()
        self.sequence = 0
        self.requests = {}
        self.binding = None
        self.closed = False
        self.retired = []
        self.adapters = set()

    def _retire(self):
        if self.binding:
            self.retired.append(self.binding["adapter"])
            self.requests[self.binding["requestId"]]["closed"] = True
            self.binding = None

    def _drain(self):
        with self.lock:
            retired, self.retired = self.retired, []
        for adapter in retired:
            adapter.invalidate()
        # Keep active retired children reachable through native-context shutdown.
        # Inspect each adapter outside the host lock (adapter capture takes it).
        with self.lock:
            adapters = list(self.adapters)
        for adapter in adapters:
            with adapter.lock:
                idle = adapter.active is None
            if idle:
                with self.lock:
                    if not self.binding or self.binding['adapter'] is not adapter:
                        self.adapters.discard(adapter)

    def close(self):
        with self.lock:
            self.closed = True
            adapters = list(self.adapters)
            self._retire()
        self._drain()
        for adapter in adapters:
            adapter.close()

    def next_sequence(self):
        with self.lock:
            if self.closed or self.native.closed:
                raise AdapterError("RETIRED", "Native context is retired")
            return {"ok": True, "protocol": PROTOCOL, "sequence": self.sequence + 1,
                    "session": self.native.session, "runtime": self.version}

    def _capture(self, owner):
        with self.lock:
            if (self.closed or self.native.closed or self.binding is not owner
                    or time.monotonic() - owner["started"] > SESSION_SECONDS
                    or not self.fresh() or self.version != owner["runtime"]):
                raise AdapterError("RETIRED", "Original case binding retired")
            read = self.read_native()
            if read.get("ok") is not True or read.get("revision") != owner["revision"]:
                self._retire()
                raise AdapterError("RETIRED", "Native context changed")
            return deepcopy(owner["context"])

    def bind(self, raw):
        try:
            return self._bind(raw)
        finally:
            self._drain()

    def _bind(self, raw):
        data = _decode(raw)
        _keys(data, ("protocol", "action", "requestId", "sequence", "session", "runtime", "revision", "context"))
        if data["protocol"] != PROTOCOL or data["action"] not in ("create", "cancel", "close"):
            raise AdapterError("SCHEMA", "Unsupported binding action")
        import re
        if (type(data["requestId"]) is not str or not re.fullmatch(r"[a-f0-9]{32}", data["requestId"])
                or type(data["sequence"]) is not int or not 1 <= data["sequence"] <= 2**53-1
                or type(data["revision"]) is not int or not 0 <= data["revision"] <= 2**53-1):
            raise AdapterError("SCHEMA", "Invalid binding identity or revision")
        context = _context(data["context"])
        with self.lock:
            if self.closed or self.native.closed or data["session"] != self.native.session or data["runtime"] != self.version or not self.fresh():
                raise AdapterError("RETIRED", "Selected native session/runtime retired")
            previous = self.requests.get(data["requestId"])
            if previous and previous["data"] != {**data, "action": "create"}:
                raise AdapterError("SCOPE", "Binding request cannot be rebound")
            if not previous:
                if data["sequence"] != self.sequence + 1:
                    raise AdapterError("RETIRED", "Binding sequence is late or unknown")
                self.sequence = data["sequence"]
                previous = {"data": {**deepcopy(data), "action": "create"}, "closed": False}
                self.requests[data["requestId"]] = previous
                # High-water permanently rejects evicted old requests.
                while len(self.requests) > 64:
                    del self.requests[next(iter(self.requests))]
            if data["action"] != "create":
                previous["closed"] = True
                if self.binding and self.binding["requestId"] == data["requestId"]:
                    self._retire()
                return {"ok": True, "state": "retired", "sequence": self.sequence}
            if previous["closed"]:
                raise AdapterError("RETIRED", "Binding was cancelled before completion")
            if self.binding and self.binding["requestId"] == data["requestId"]:
                self._capture(self.binding)
                return {"ok": True, "context": deepcopy(context), "sequence": self.sequence}
            read = self.read_native()
            if read.get("ok") is not True or read.get("revision") != data["revision"]:
                previous["closed"] = True
                raise AdapterError("RETIRED", "Original native revision changed")
            self._retire()
            owner = {"requestId": data["requestId"], "context": context,
                     "revision": data["revision"], "runtime": self.version, "started": time.monotonic()}
            owner["adapter"] = RuleCaseWorkbenchAdapter(capture_context=lambda: self._capture(owner), binary=self.binary)
            self.adapters.add(owner['adapter'])
            self.binding = owner
            return {"ok": True, "context": deepcopy(context), "sequence": self.sequence}

    def dispatch(self, raw):
        with self.lock:
            owner = self.binding
            if not owner:
                return 409, {"ok": False, "code": "RETIRED", "error": "No active case binding"}
        # Never hold the host lock while waiting for a disposable native run.
        try:
            return owner["adapter"].dispatch("POST", "/rule-cases/workbench", raw)
        finally:
            self._drain()


def prepare_data(raw, binary=None):
    """Detached strict validation for every archive/retention path, no binding."""
    data = _decode(raw)
    context = {"projectId": "detached-archive-validation", "generation": 0,
               "contextToken": "detached"}
    identity, _ = runtime_identity(binary)
    validated = validate_case_data(data, identity, context)["data"]
    return {"ok": True, "data": validated, "trust": "historical-unverified"}
