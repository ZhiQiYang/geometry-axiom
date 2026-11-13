"""Errors and canonical encoding shared by the deterministic modeling executor."""
from __future__ import annotations

import hashlib
import json

ENGINEERING_CAPABILITY = "engineering-spec/1"
PARAMETER_CAPABILITY = "parameters/1"
GRID_CARD_CAPABILITY = "grid-card-reference/1"
GRID_SUBDIVISION_CAPABILITY = "grid-subdivision-rules/1"
SECTION_PROFILE_CAPABILITY = "section-profile/1"
PANEL_FILL_CAPABILITY = "panel-fill/1"


def scene_required_capabilities(scene):
    """Identify required source syntax, without evaluating any engineering values.

    The C parser remains authoritative. Detecting bindings as well as the marker
    prevents a stripped marker or a legacy adapter from flattening new sources.
    """
    result = set()
    for raw in scene.splitlines():
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        if tokens[0] == "grid-system" and ("card-reference" in tokens or "card" in tokens):
            result.update({GRID_CARD_CAPABILITY, PARAMETER_CAPABILITY})
        if tokens[0] == "requires":
            if len(tokens) != 2:
                raise ModelError("INVALID", "CAPABILITY_DECLARATION", "I32", "Expected one required capability")
            result.add(tokens[1])
        if tokens[0] in ("grid-source-rule", "grid-source-rule-highwater") or any("gridrule:" in token for token in tokens) or "at-line rule" in " ".join(tokens):
            result.add(GRID_SUBDIVISION_CAPABILITY)
        if tokens[0] == "engineering" or any(token.startswith("eng:") for token in tokens):
            result.add(ENGINEERING_CAPABILITY)
        if tokens[0] == "owned":
            result.add("assembly-timber-generation/1")
        if tokens[0] == "assembly":
            result.add("assembly-rule-authoring/1")
        if tokens[0] == "section-profile":
            result.add(SECTION_PROFILE_CAPABILITY)
        if tokens[0] in ("finish-surface", "panel-fill"):
            result.add(PANEL_FILL_CAPABILITY)
        if tokens[0] == "parameters" or "param:" in " ".join(tokens):
            result.add(PARAMETER_CAPABILITY)
    return result


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


def _canonical_call(function, *args):
    from geometry_kernel.errors import EvaluationError
    from .kernel_errors import translate
    try:
        return function(*args)
    except EvaluationError as error:
        raise translate(error) from error


def canonical_bytes(value):
    from geometry_kernel.canonical import canonical_bytes as encode
    return _canonical_call(encode, value)


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def strict_json_loads(text):
    from geometry_kernel.canonical import strict_json_loads as decode
    return _canonical_call(decode, text)
