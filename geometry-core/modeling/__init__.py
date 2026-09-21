"""Deterministic orthogonal models, backed by the authoritative C scene parser.

The Python executor is a reference implementation; it does not add new DSL
commands to the existing C World or advertise that the canvas supports them.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import secrets

from .common import ModelError, canonical_bytes, digest, strict_json_loads

AXIOM_REVISION = "cd197fa6537dfdd53feae7179d2a426b2f23d25e"
AXIOM_SHA256 = "00a12fea0367717cdd49d6708683b9c9a7162385a6232ef42fb14ba5a028b8ae"
SCHEMA = "geometry-model-package/1"
PROFILE = "orthogonal-model/1"
GENERATOR = {"name": "geometry-axiom-reference", "version": "1.0.0"}
CAPABILITIES = ("extrusion/1", "shell/1", "composite-space/1",
                "solid-composition/1", "model-export/1")
_AXIOM_PATH = Path(__file__).resolve().parents[2] / "公理層.md"


def _axiom_hash():
    """條文的雜湊。行尾先正規化——CRLF/LF 是簽出方式,不是條文內容。

    GEO-153:公理層.md 在 git 裡存 LF,`.gitattributes` 沒把它標成 `-text`,
    所以 Windows 簽出來是 CRLF;直接雜湊原始 bytes 的話,AXIOM_SHA256
    (在 LF bytes 上算出來的)永遠對不上,**每一次建模都被擋成「公理變了」**。
    正規化之後這個值才是跨平台同一個,manifest 裡的 axiom_sha256 才談得上可重現。
    與 `geometry-guide/witness.py::_sha` 同一個判斷。
    """
    try:
        raw = _AXIOM_PATH.read_bytes()
    except OSError as exc:
        raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "The supported axiom source is unavailable") from exc
    actual = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if actual != AXIOM_SHA256:
        raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Axiom source changed without a corresponding executor version")
    return actual


def build_package(definitions, request, *, capabilities=None, max_cells=200000,
                  base_executable=None, presentation=None):
    """Validate and evaluate sources; return a complete, empty or explicit partial package.

    Invalid or unsupported input, and incomplete requests without allow_partial,
    raise ModelError. Input dictionaries are never modified.
    """
    from .engine import evaluate
    canonical_bytes(definitions)
    canonical_bytes(request)
    if type(max_cells) is not int or max_cells < 1:
        raise ModelError("INVALID", "CONFIG", "I33", "max_cells must be a positive integer")
    available = list(CAPABILITIES) if capabilities is None else capabilities
    result = evaluate(copy.deepcopy(definitions), copy.deepcopy(request),
                      capabilities=available, max_cells=max_cells,
                      base_executable=base_executable)
    # evaluate checks known definition contradictions before capability errors.
    active = [c for c in CAPABILITIES if c in available]
    package = {
        "manifest": {"schema": SCHEMA, "profile": PROFILE,
                     "axiom_revision": AXIOM_REVISION,
                     "axiom_sha256": _axiom_hash(),
                     "generator": dict(GENERATOR), "capabilities": active,
                     "units": "mm",
                     "coordinate_system": {"handedness": "right", "up": "+Z"},
                     "source_sha256": digest(result["definitions"]),
                     "geometry_sha256": digest(result["derived"])},
        "definitions": result["definitions"], "request": result["request"],
        "derived": result["derived"], "diagnostics": result["diagnostics"],
    }
    if presentation is not None:
        canonical_bytes(presentation)
        package["presentation"] = copy.deepcopy(presentation)
    canonical_bytes(package)
    return package


def verify_package(package, *, max_cells=200000, base_executable=None):
    """Rebuild from definitions and reject any altered or incompatible snapshot."""
    canonical_bytes(package)
    keys = {"manifest", "definitions", "request", "derived", "diagnostics"}
    if not isinstance(package, dict) or not keys <= package.keys() or set(package) - keys - {"presentation"}:
        raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Unexpected or missing package fields")
    manifest = package["manifest"]
    required = {"schema", "profile", "axiom_revision", "axiom_sha256", "generator",
                "capabilities", "units", "coordinate_system", "source_sha256", "geometry_sha256"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Unexpected or missing manifest fields")
    if manifest["schema"] != SCHEMA or manifest["profile"] != PROFILE:
        raise ModelError("UNSUPPORTED", "VERSION", "I32", "Unsupported package schema or modeling profile")
    if manifest["axiom_revision"] != AXIOM_REVISION or manifest["axiom_sha256"] != _axiom_hash():
        raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "This executor does not implement the supplied axiom revision")
    generator = manifest["generator"]
    if not isinstance(generator, dict) or set(generator) != {"name", "version"} or any(
            not isinstance(value, str) or not value.strip() for value in generator.values()):
        raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Generator requires nonempty name and version strings")
    if manifest["units"] != "mm" or manifest["coordinate_system"] != {"handedness": "right", "up": "+Z"}:
        raise ModelError("INVALID", "COORDINATE_SYSTEM", "D25", "An explicit adapter is required for other units or axes")
    if type(manifest["capabilities"]) is not list:
        raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Manifest capabilities must be an ordered array")
    if manifest["source_sha256"] != digest(package["definitions"]) or manifest["geometry_sha256"] != digest(package["derived"]):
        raise ModelError("INVALID", "HASH_MISMATCH", "I31", "Package definitions or geometry digest differs")
    rebuilt = build_package(package["definitions"], package["request"],
                            capabilities=manifest["capabilities"], max_cells=max_cells,
                            base_executable=base_executable,
                            presentation=package.get("presentation"))
    for key in ("definitions", "request", "derived"):
        if canonical_bytes(rebuilt[key]) != canonical_bytes(package[key]):
            raise ModelError("INVALID", "SNAPSHOT_MISMATCH", "I31", "Rebuilt package differs in " + key, path=[key])
    if manifest["capabilities"] != rebuilt["manifest"]["capabilities"]:
        raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Capabilities must be unique and canonically ordered")
    # Another conforming generator can use different diagnostic wording/codes.
    # Validate its records and required root coverage, then return our rebuilt
    # package with our own generator and diagnostic evidence.
    diagnostics = package["diagnostics"]
    if not isinstance(diagnostics, list):
        raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Diagnostics must be an array")
    diagnostic_keys = {"root", "path", "code", "clause", "message"}
    roots = {(r["kind"], r["id"]) for r in rebuilt["request"]["roots"]}
    for item in diagnostics:
        if (not isinstance(item, dict) or not diagnostic_keys <= item.keys()
                or set(item) - diagnostic_keys - {"missing"}
                or any(not isinstance(item[k], str) or not item[k] for k in ("code", "clause", "message"))
                or not isinstance(item["path"], list) or any(not isinstance(p, str) for p in item["path"])):
            raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Unexpected diagnostic fields")
        ref = item["root"]
        if (not isinstance(ref, dict) or set(ref) != {"kind", "id"}
                or not isinstance(ref["kind"], str) or type(ref["id"]) is not int
                or (ref["kind"], ref["id"]) not in roots):
            raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Diagnostic must identify a requested root")
        if "missing" in item:
            missing = item["missing"]
            valid_ref = (isinstance(missing, dict) and set(missing) == {"kind", "id"}
                         and isinstance(missing["kind"], str) and type(missing["id"]) is int
                         and 0 <= missing["id"] <= 0xFFFFFFFF)
            if not isinstance(missing, str) and not valid_ref:
                raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "missing must name a specification or typed reference")
    diagnosed = {(d["root"]["kind"], d["root"]["id"]) for d in diagnostics}
    present = {(o["root"]["kind"], o["root"]["id"]) for o in rebuilt["derived"]["objects"]}
    if not (roots - present) <= diagnosed:
        raise ModelError("INVALID", "SNAPSHOT_MISMATCH", "I31", "Omitted roots require explicit diagnostics")
    for obj in rebuilt["derived"]["objects"]:
        if obj["status"] == "EMPTY" and not any(d["root"] == obj["root"] and d["code"] == "EMPTY_RESULT" for d in diagnostics):
            raise ModelError("INVALID", "SNAPSHOT_MISMATCH", "I31", "Empty roots require EMPTY_RESULT evidence")
    return rebuilt


class ModelWorld:
    """Atomic source replacement with an explicit preview/confirmation boundary.

    The entire candidate is revalidated, including old C rules. No mutation,
    partial root or stale preview can leave half a model committed.
    """
    def __init__(self, definitions, request, **options):
        self._options = copy.deepcopy(options)
        self._package = build_package(definitions, request, **self._options)
        self._revision = 0
        self._preview_revision = 0
        self._nonce = secrets.token_hex(16)
        self._pending = None

    @property
    def package(self):
        return copy.deepcopy(self._package)

    @property
    def definitions(self):
        return copy.deepcopy(self._package["definitions"])

    def export(self, request=None):
        return build_package(self._package["definitions"],
                             self._package["request"] if request is None else request,
                             **self._options)

    def preview(self, definitions, request=None):
        self._pending = None
        self._preview_revision += 1
        candidate = build_package(definitions,
                                  self._package["request"] if request is None else request,
                                  **self._options)
        token = digest({"session": self._nonce, "revision": self._revision,
                        "preview_revision": self._preview_revision,
                        "candidate": candidate})
        self._pending = (token, self._revision, candidate)
        return {"token": token, "status": candidate["derived"]["status"],
                "diagnostics": copy.deepcopy(candidate["diagnostics"]),
                "package": copy.deepcopy(candidate)}

    def confirm(self, token):
        pending = self._pending
        if pending is None or pending[0] != token or pending[1] != self._revision:
            raise ModelError("INVALID", "STALE_PREVIEW", "I30", "Preview is absent, cancelled, replaced or stale")
        self._pending = None
        candidate = verify_package(pending[2], max_cells=self._options.get("max_cells", 200000),
                                   base_executable=self._options.get("base_executable"))
        self._package = candidate
        self._revision += 1
        return self.package

    commit = confirm

    def cancel(self, token=None):
        if token is not None and (self._pending is None or token != self._pending[0]):
            raise ModelError("INVALID", "STALE_PREVIEW", "I30", "Preview token does not match")
        self._pending = None


__all__ = ["build_package", "verify_package", "ModelWorld", "ModelError",
           "canonical_bytes", "strict_json_loads", "CAPABILITIES", "PROFILE"]
