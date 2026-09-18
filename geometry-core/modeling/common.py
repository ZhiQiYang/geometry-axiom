"""Errors and canonical encoding shared by the deterministic modeling executor."""
from __future__ import annotations

import hashlib
import json


class ModelError(ValueError):
    def __init__(self, status, code, clause, message, path=None, root=None,
                 missing=None, diagnostics=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.clause = clause
        self.message = message
        self.path = list(path or [])
        self.root = root
        self.missing = missing
        self.diagnostics = diagnostics

    def diagnostic(self):
        result = {"root": self.root, "path": self.path, "code": self.code,
                  "clause": self.clause, "message": self.message}
        if self.missing is not None:
            result["missing"] = self.missing
        return result

    def as_dict(self):
        return {"status": self.status,
                "diagnostics": self.diagnostics or [self.diagnostic()]}


def canonical_bytes(value):
    """The integer-only canonical JSON specified in MODELING-CONTRACT §5."""
    def check(item):
        if item is None or type(item) in (bool, int):
            return
        if isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ModelError("INVALID", "UNICODE", "D25", "Unpaired Unicode surrogate") from exc
            return
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            for key, child in item.items():
                check(key)
                check(child)
            return
        raise ModelError("INVALID", "JSON_TYPE", "D25", "Only JSON objects, arrays, strings, booleans, null and integers are supported")
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def strict_json_loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ModelError("INVALID", "DUPLICATE_KEY", "D25", "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def forbidden(value):
        raise ModelError("INVALID", "JSON_TYPE", "D25", "Non-integer JSON number: " + value)
    try:
        result = json.loads(text, object_pairs_hook=pairs,
                            parse_float=forbidden, parse_constant=forbidden)
        canonical_bytes(result)
        return result
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ModelError("INVALID", "JSON_PARSE", "D25", str(exc)) from exc
