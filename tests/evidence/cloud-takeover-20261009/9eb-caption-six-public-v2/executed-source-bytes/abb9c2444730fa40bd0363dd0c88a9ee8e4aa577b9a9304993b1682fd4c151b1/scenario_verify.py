"""#46 disposable native verification; never connects to a live bridge.

The JS closure validator owns the complete manifest, feature schemas and asset
bytes. This adapter independently verifies the scene's final native objects,
typed source inventory, capabilities and every saved model's derived data.
All files below are private temporary inputs, not project or runtime state.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import threading

import space_modeling
from modeling import ModelError, canonical_bytes, verify_package
from modeling.base import load_base
from modeling.common import scene_required_capabilities
from modeling import base as base_module

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import binaries
MAX_SCENE_BYTES = 1024 * 1024
MAX_INPUT_BYTES = 9 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_STDERR_BYTES = 64 * 1024
MAX_MODELS = 64
BRIDGE_TIMEOUT = 20
MODEL_TIMEOUT = 60
NATIVE_CAPABILITIES = frozenset(("engineering-spec/1", "parameters/1",
                               "assembly-rule-authoring/1", "assembly-timber-generation/1", "section-profile/1"))
# Scene capture follows the current portable reader. Model producer input
# retains its own narrower capability contract below.
BRIDGE_CAPABILITIES = NATIVE_CAPABILITIES | {"grid-subdivision-rules/1"}
OBJECT_KINDS = frozenset(("boundary", "placement", "space", "column", "beam", "spec", "parameter",
                          "datum", "guide", "grid-system", "grid-binding", "grid", "material", "method",
                          "application", "timber", "assembly-rule", "assembly-binding", "assembly-instance",
                          "section-profile", "profile-member", "profile-run", "panel-spec"))
STRING_ID_KINDS = frozenset(("spec", "material", "method", "application", "application-field", "panel-spec"))
FIELD_KINDS = frozenset(("parameter-field", "application-field", "assembly-member", "assembly-joint"))
HASH = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


def _fail(code, message, *, status="INVALID", path=()):
    raise ModelError(status, code, "I32" if status == "UNSUPPORTED" else "I31", message, path=list(path))


def _keys(value, required, optional=(), path=()):
    if type(value) is not dict or set(required) - set(value) or set(value) - set(required) - set(optional):
        _fail("SCENARIO_SHAPE", "Expected complete, explicit verification fields.", path=path)


def _uid(value, path=(), *, positive=False):
    if type(value) is not int or not int(positive) <= value <= 0xFFFFFFFF:
        _fail("SCENARIO_ID", "Expected a uint32 identity.", path=path)


def _json_bytes(value):
    """Bound plain JSON including the finite display floats used by sources."""
    count = 0

    def visit(item, depth):
        nonlocal count
        count += 1
        if count > 600000 or depth > 64:
            _fail("SCENARIO_CAPACITY", "Verification JSON exceeds nesting or item capacity.", status="UNSUPPORTED")
        if item is None or type(item) in (bool, int):
            return
        if type(item) is float and math.isfinite(item):
            return
        if type(item) is str:
            try:
                item.encode("utf-8")
            except UnicodeEncodeError:
                _fail("SCENARIO_JSON", "Verification JSON contains invalid Unicode.")
            if len(item) > MAX_INPUT_BYTES:
                _fail("SCENARIO_CAPACITY", "Verification string exceeds capacity.", status="UNSUPPORTED")
            return
        if type(item) is list:
            for child in item:
                visit(child, depth + 1)
            return
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str or len(key) > 200 or key in ("__proto__", "constructor", "prototype"):
                    _fail("SCENARIO_JSON", "Verification JSON has an unsafe or invalid key.")
                visit(key, depth + 1)
                visit(child, depth + 1)
            return
        _fail("SCENARIO_JSON", "Verification accepts only finite plain JSON.")

    visit(value, 0)
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, OverflowError, RecursionError):
        _fail("SCENARIO_JSON", "Verification JSON cannot be encoded.")
    if len(encoded) > MAX_INPUT_BYTES:
        _fail("SCENARIO_CAPACITY", "Verification input exceeds 9 MiB capacity.", status="UNSUPPORTED")
    return encoded


def _parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("SCENARIO_JSON", "Duplicate JSON key.")
            result[key] = value
        return result

    def constant(_):
        _fail("SCENARIO_JSON", "Non-finite JSON number.")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeDecodeError, RecursionError):
        _fail("SCENARIO_JSON", "Malformed verification JSON.")
    _json_bytes(value)
    return value


def _scene(value, path):
    if type(value) is not str:
        _fail("SCENARIO_SCENE", "Scene must be an explicit UTF-8 string.", path=path)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        _fail("SCENARIO_SCENE", "Scene contains invalid Unicode.", path=path)
    if len(encoded) > MAX_SCENE_BYTES:
        _fail("SCENARIO_CAPACITY", "Scene exceeds 1 MiB capacity.", status="UNSUPPORTED", path=path)
    if b"\0" in encoded:
        _fail("SCENARIO_SCENE", "Scene must not contain NUL.", path=path)
    return encoded


def _capabilities(value, path, *, supported=NATIVE_CAPABILITIES):
    if type(value) is not list or len(value) > len(supported) or any(type(item) is not str for item in value) or len(set(value)) != len(value):
        _fail("SCENARIO_CAPABILITY", "Native capability list is invalid.", status="UNSUPPORTED", path=path)
    if set(value) - supported:
        _fail("SCENARIO_CAPABILITY", "Required native capability is unsupported.", status="UNSUPPORTED", path=path)
    return set(value)


def _program(value, *, base=False):
    candidate = value or os.environ.get("GEOMETRY_SCENARIO_BASE" if base else "GEOMETRY_SCENARIO_BRIDGE")
    candidate = candidate or os.environ.get("GEOMETRY_MODEL_BASE" if base else "GEOMETRY_TEST_BRIDGE")
    binary = binaries.BY_NAME["model-base" if base else "bridge"]
    candidate = candidate or binary.path
    try:
        path = Path(candidate).resolve(strict=True)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise OSError()
        fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, TypeError, ValueError):
        _fail("SCENARIO_EXECUTABLE", "Cannot identify the isolated native executable.", status="UNSUPPORTED")
    info = binaries.inspect_one(binary, path=path)
    if info.state != "fresh":
        _fail("SCENARIO_RUNTIME_UNKNOWN", "Native executable lacks a matching current source and binary build receipt.", status="UNSUPPORTED")
    return str(path), fingerprint


def _validator_pins():
    paths = {Path(__file__).resolve(), ROOT / "geometry-web" / "space_modeling.py", ROOT / "tests" / "binaries.py"}
    paths.update((ROOT / "geometry-core" / "modeling").glob("*.py"))
    try:
        sources = [[path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()]
                   for path in sorted(paths)]
        return {"validator_sha256": hashlib.sha256(canonical_bytes(sources)).hexdigest(),
                "axiom_sha256": hashlib.sha256((ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
    except OSError:
        _fail("SCENARIO_RUNTIME", "Cannot fingerprint the complete model verifier and axiom sources.", status="UNSUPPORTED")


def _source_receipt(path, *, base=False):
    info = binaries.inspect_one(binaries.BY_NAME["model-base" if base else "bridge"], path=path)
    if info.state != "fresh":
        _fail("SCENARIO_RUNTIME_UNKNOWN", "Native build receipt is missing or stale.", status="UNSUPPORTED")
    return info.fingerprint


def _stop_owned_process(process, owns_process_group=True):
    """Stop only this verifier's child group, including model adapter children."""
    if not owns_process_group:
        if process.poll() is None:
            process.kill()
    elif os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        # Child trees belong to this call; never address an existing live bridge.
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()


def _run_bounded(command, payload, *, cwd, timeout, output_limit=None, allowed_exit_codes=(0,),
                 with_returncode=False, owns_process_group=True):
    """Drain with bounded buffers; excessive output is stopped during execution."""
    output_limit = MAX_OUTPUT_BYTES if output_limit is None else output_limit
    output, errors = bytearray(), bytearray()
    overflow = threading.Event()
    flags = ({"start_new_session": True} if os.name == "posix" else
             {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}) if owns_process_group else {}
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=cwd, **flags)
    except OSError:
        _fail("SCENARIO_NATIVE_EXECUTABLE", "Cannot launch isolated verification.", status="UNSUPPORTED")

    def read(pipe, target, limit):
        try:
            while True:
                chunk = pipe.read1(65536)
                if not chunk:
                    break
                if len(target) + len(chunk) > limit:
                    overflow.set()
                    _stop_owned_process(process, owns_process_group)
                    break
                target.extend(chunk)
        finally:
            pipe.close()

    def write():
        try:
            process.stdin.write(payload)
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            process.stdin.close()

    readers = [threading.Thread(target=read, args=(process.stdout, output, output_limit), daemon=True),
               threading.Thread(target=read, args=(process.stderr, errors, MAX_STDERR_BYTES), daemon=True)]
    writer = threading.Thread(target=write, daemon=True)
    for thread in [*readers, writer]:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _stop_owned_process(process, owns_process_group)
        process.wait(timeout=5)
    finally:
        if owns_process_group and os.name == "posix":
            # The model adapter inherits the disposable worker's group. Even
            # an adapter that outlives its parent cannot survive this call.
            _stop_owned_process(process)
        for thread in [*readers, writer]:
            thread.join(timeout=1)
        if any(thread.is_alive() for thread in readers):
            _stop_owned_process(process, owns_process_group)
            for thread in readers:
                thread.join(timeout=1)
    if overflow.is_set():
        _fail("SCENARIO_NATIVE_CAPACITY", "Isolated verifier exceeded output capacity.", status="UNSUPPORTED")
    if timed_out:
        _fail("SCENARIO_NATIVE_TIMEOUT", "Isolated verification exceeded its execution budget.", status="UNSUPPORTED")
    if any(thread.is_alive() for thread in readers) or process.returncode not in allowed_exit_codes:
        _fail("SCENARIO_NATIVE_EXIT", "Isolated verifier exited abnormally.", status="UNSUPPORTED")
    return (bytes(output), process.returncode) if with_returncode else bytes(output)


def _final_objects(value):
    if type(value) is not dict or set(value) not in ({"boundaries", "placements"}, {"boundaries", "placements", "boundaryFingerprints"}):
        _fail("SCENARIO_NATIVE_PROTOCOL", "Native final object receipt is incomplete.", status="UNSUPPORTED")
    boundaries, placements = value["boundaries"], value["placements"]
    if type(boundaries) is not list or type(placements) is not list or len(boundaries) > 2048 or len(placements) > 2048:
        _fail("SCENARIO_NATIVE_CAPACITY", "Native final object receipt exceeds capacity.", status="UNSUPPORTED")
    for identifier in boundaries:
        _uid(identifier, positive=True)
    if len(set(boundaries)) != len(boundaries):
        _fail("SCENARIO_NATIVE_PROTOCOL", "Native boundary identity is duplicated.", status="UNSUPPORTED")
    ids = set()
    for item in placements:
        _keys(item, ("id", "bid", "horizontal"))
        _uid(item["id"]); _uid(item["bid"])
        if type(item["horizontal"]) is not bool or item["id"] in ids or (item["bid"] and item["bid"] not in boundaries):
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native placement identity or boundary is invalid.", status="UNSUPPORTED")
        ids.add(item["id"])
    # A load candidate may include the existing native geometry hashes. Keep
    # the old receipt valid, but never accept a partial or untyped new summary.
    if "boundaryFingerprints" in value:
        entries = value["boundaryFingerprints"]
        if type(entries) is not list or len(entries) != len(boundaries):
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native candidate boundary fingerprints are incomplete.", status="UNSUPPORTED")
        seen = set()
        for entry in entries:
            if (type(entry) is not dict or set(entry) != {"id", "geometryFingerprint"} or
                    type(entry["id"]) is not int or entry["id"] not in boundaries or entry["id"] in seen or
                    type(entry["geometryFingerprint"]) is not str or not HASH.fullmatch(entry["geometryFingerprint"])):
                _fail("SCENARIO_NATIVE_PROTOCOL", "Native candidate boundary fingerprint identity is invalid.", status="UNSUPPORTED")
            seen.add(entry["id"])
    return value


def _object_refs(manifest, final, path=()):
    boundaries = set(final["boundaries"])
    placements = {item["id"]: item for item in final["placements"]}
    for name in ("faces", "reconstructionReviews", "faceProjections"):
        records = manifest.get(name, [])
        if type(records) is not list or len(records) > 10000:
            _fail("SCENARIO_SHAPE", "Invalid metadata reference list.", path=(*path, name))
        for index, record in enumerate(records):
            here = (*path, name, index)
            if type(record) is not dict or type(record.get("bid")) is not int or record["bid"] not in boundaries:
                _fail("SCENARIO_REFERENCE", "Metadata boundary is absent from the final native scene.", path=here)
            if name == "faceProjections":
                _uid(record.get("placement_id"), (*here, "placement_id"))
                placement = placements.get(record.get("placement_id"))
                if not placement or placement["bid"] != record["bid"] or not placement["horizontal"]:
                    _fail("SCENARIO_REFERENCE", "Projection must refer to its actual final horizontal placement.", path=here)


def _inventory(graph, final):
    if (type(graph) is not dict or graph.get("ok") is not True or graph.get("schema") != "source-inspector/1" or
            graph.get("live") is not False or graph.get("complete") is not True or
            graph.get("identityContinuity") != "unknown" or type(graph.get("sourceFingerprint")) is not str or
            not HASH.fullmatch(graph["sourceFingerprint"]) or
            type(graph.get("nodes")) is not list or type(graph.get("edges")) is not list or
            len(graph["nodes"]) > 2048 or len(graph["edges"]) > 8192):
        _fail("SCENARIO_NATIVE_PROTOCOL", "Native typed inventory is incomplete or unsupported.", status="UNSUPPORTED")
    nodes, objects, seen, omitted = {}, [], set(), set()
    for raw in graph["nodes"]:
        if (type(raw) is not dict or any(type(raw.get(name)) is not str for name in ("key", "kind", "id")) or
                raw["key"] in nodes or raw["kind"] not in OBJECT_KINDS | FIELD_KINDS or
                any(type(raw.get(name)) is not int or not 0 <= raw[name] <= 0xFFFFFFFF for name in ("version", "fieldId")) or
                any(type(raw.get(name)) is not str or not HASH.fullmatch(raw[name]) for name in ("definitionFingerprint", "valueFingerprint"))):
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native inventory node cannot be identified exactly.", status="UNSUPPORTED")
        identifier = raw["id"]
        version, field = raw["version"], raw["fieldId"]
        versioned = raw["kind"] in ("material", "method", "assembly-rule", "assembly-member", "assembly-joint")
        if (bool(version) != versioned or (raw["kind"] not in FIELD_KINDS and field != 0)):
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native node version or field does not match its kind.", status="UNSUPPORTED")
        key = raw["kind"] + ":" + identifier
        if version:
            key += ":v" + str(version)
        if field or raw["kind"] == "parameter-field":
            key += ":f" + str(field)
        if key != raw["key"]:
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native graph key disagrees with its typed identity.", status="UNSUPPORTED")
        if raw["kind"] not in STRING_ID_KINDS:
            if not re.fullmatch(r"0|[1-9][0-9]{0,9}", identifier):
                _fail("SCENARIO_NATIVE_PROTOCOL", "Native inventory ID is invalid.", status="UNSUPPORTED")
            identifier = int(identifier)
            _uid(identifier)
        elif not identifier or len(identifier) > 100:
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native string identity is invalid.", status="UNSUPPORTED")
        node = {name: deepcopy(raw[name]) for name in ("key", "kind", "version", "fieldId", "definitionFingerprint", "valueFingerprint")}
        node["id"] = identifier
        if "nativeOwner" in raw:
            node["nativeOwner"] = deepcopy(raw["nativeOwner"])
        nodes[raw["key"]] = node
        if raw["kind"] in FIELD_KINDS:
            omitted.add(raw["kind"])
        else:
            identity = (raw["kind"], identifier, raw["version"] or None)
            if identity in seen:
                _fail("SCENARIO_NATIVE_PROTOCOL", "Native object identity is duplicated.", status="UNSUPPORTED")
            seen.add(identity)
            objects.append({"kind": identity[0], "id": identity[1], "version": identity[2]})
    for kind, expected in (("boundary", set(final["boundaries"])), ("placement", {p["id"] for p in final["placements"]})):
        if {item["id"] for item in objects if item["kind"] == kind} != expected:
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native typed inventory disagrees with final objects.", status="UNSUPPORTED")
    edges = []
    for edge in graph["edges"]:
        if (type(edge) is not dict or type(edge.get("active")) is not bool or
                any(type(edge.get(name)) is not str for name in ("from", "to", "relation", "field")) or
                edge["from"] not in nodes or edge["to"] not in nodes):
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native inventory has a dangling or untyped reference.", status="UNSUPPORTED")
        edges.append(deepcopy(edge))
    return objects, {"nodes": list(nodes.values()), "references": edges,
                     "omittedObjectKinds": sorted(omitted), "sourceFingerprint": graph["sourceFingerprint"]}


def _model(record, base, index):
    path = ("manifest", "models", index)
    _keys(record, ("id", "name", "created_at", "source", "input", "result"), path=path)
    if (type(record["id"]) is not str or not IDENTIFIER.fullmatch(record["id"]) or
            type(record["name"]) is not str or not record["name"].strip() or len(record["name"]) > 200):
        _fail("SCENARIO_MODEL", "Saved model identity is invalid.", path=path)
    try:
        if type(record["created_at"]) is not str or len(record["created_at"]) > 100:
            raise ValueError()
        datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
    except ValueError:
        _fail("SCENARIO_MODEL", "Saved model creation time is invalid.", path=path)
    source, inputs, saved = record["source"], record["input"], record["result"]
    _keys(source, ("kind", "placement_id", "boundary_id", "scene_hash"), ("projection",), (*path, "source"))
    if source["kind"] not in ("scene", "example") or not HASH.fullmatch(str(source["scene_hash"])):
        _fail("SCENARIO_MODEL", "Saved model source metadata is invalid.", path=path)
    for name in ("placement_id", "boundary_id"):
        if source[name] is not None:
            _uid(source[name], (*path, "source", name))
    if type(inputs) is not dict or inputs.get("mode") not in ("plan", "faces"):
        _fail("SCENARIO_MODEL", "Saved model mode is unsupported.", status="UNSUPPORTED", path=path)
    _scene(inputs.get("base_scene"), (*path, "input", "base_scene"))
    model_base = load_base(inputs["base_scene"], executable=base)
    required = scene_required_capabilities(inputs["base_scene"])
    if inputs["mode"] == "plan":
        placement = next((p for p in model_base["placements"] if p["id"] == inputs.get("placement_id")), None)
        if (placement is None or source["placement_id"] != inputs.get("placement_id") or
                (source["boundary_id"] != placement["boundary_id"] and
                 not (source["boundary_id"] is None and placement["boundary_id"] == 0))):
            _fail("SCENARIO_MODEL_REPLAY", "Saved model source identity disagrees with its native input.", path=path)
    elif source["placement_id"] is not None:
        placement = next((p for p in model_base["placements"] if p["id"] == source["placement_id"]), None)
        if placement is None or (source["boundary_id"] != placement["boundary_id"] and
                                 not (source["boundary_id"] is None and placement["boundary_id"] == 0)):
            _fail("SCENARIO_MODEL_REPLAY", "Faces model provenance disagrees with its native input.", path=path)
    elif source["boundary_id"] is not None and not any(p["boundary_id"] == source["boundary_id"] for p in model_base["placements"]):
        _fail("SCENARIO_MODEL_REPLAY", "Faces model provenance has no matching native boundary.", path=path)
    if "projection" in source:
        projection = source["projection"]
        _keys(projection, ("kind", "view", "region", "wallSide"), path=(*path, "source", "projection"))
        if (inputs["mode"] != "plan" or not source["boundary_id"] or
                projection["kind"] != "space-boundary-plan" or projection["view"] not in ("top", "bottom") or
                projection["region"] != "interior" or projection["wallSide"] != "outside" or
                placement["n"][:2] != [0, 0] or abs(placement["n"][2]) != 1):
            _fail("SCENARIO_MODEL_REPLAY", "Saved model projection disagrees with its native source.", path=path)
    rebuilt = space_modeling.preview(inputs, base_executable=base, max_cells=200000)
    # Conforming older packages may retain supported axiom pins, another
    # generator, presentation and diagnostic wording. Verify each ORIGINAL
    # package before comparing its exact geometric semantics to saved input.
    # Neither verification result is written back to the original record.
    result_required = set(rebuilt) - {"ok", "diagnostics"}
    if (type(saved) is not dict or result_required - set(saved) or
            set(saved) - result_required - {"ok", "diagnostics"} or
            ("ok" in saved and saved["ok"] is not True) or
            ("diagnostics" in saved and type(saved["diagnostics"]) is not list)):
        _fail("SCENARIO_MODEL_REPLAY", "Saved model result has missing or unknown fields.", path=(*path, "result"))
    if (saved["schema"] != rebuilt["schema"] or saved["source_sha256"] != rebuilt["source_sha256"] or
            source["scene_hash"] != rebuilt["source_sha256"]):
        _fail("SCENARIO_MODEL_REPLAY", "Saved model source or schema differs from independent replay.", path=path)
    for key in ("space", "volume", "clearance", "walls", *(("timbers",) if "timbers" in inputs else ())):
        original, replayed = saved[key], rebuilt[key]
        if (original is None) != (replayed is None):
            _fail("SCENARIO_MODEL_REPLAY", "Saved model package presence differs from independent replay.",
                  path=(*path, "result", key))
        if original is None:
            continue
        try:
            verify_package(original, base_executable=base, max_cells=200000)
        except ModelError as exc:
            _fail("SCENARIO_MODEL_REPLAY", "Original model package failed verification: " + exc.code + ".",
                  status=exc.status, path=(*path, "result", key, *exc.path))
        if any(canonical_bytes(original[field]) != canonical_bytes(replayed[field])
               for field in ("definitions", "request", "derived")):
            _fail("SCENARIO_MODEL_REPLAY", "Saved model geometry or provenance differs from independent replay.",
                  path=(*path, "result", key))
    summary = saved["summary"]
    if (type(summary) is not dict or set(summary) != set(rebuilt["summary"]) or
            type(summary["wall_diagnostics"]) is not list):
        _fail("SCENARIO_MODEL_REPLAY", "Saved model summary has missing or unknown fields.", path=(*path, "result", "summary"))
    # Wall diagnostics are evidence from the original conforming producer;
    # their text need not equal this executor's current wording.
    original_summary = {key: value for key, value in summary.items() if key != "wall_diagnostics"}
    replayed_summary = {key: value for key, value in rebuilt["summary"].items() if key != "wall_diagnostics"}
    if canonical_bytes(original_summary) != canonical_bytes(replayed_summary):
        _fail("SCENARIO_MODEL_REPLAY", "Saved model summary differs from independent replay.", path=(*path, "result", "summary"))
    return required


def _models(records, base):
    required, identifiers = set(), set()
    for index, record in enumerate(records):
        required.update(_model(record, base, index))
        if record["id"] in identifiers:
            _fail("SCENARIO_MODEL", "Saved model identity is duplicated.", path=("manifest", "models", index))
        identifiers.add(record["id"])
    return sorted(required)


class _BoundedModelAdapter:
    """A scoped subprocess adapter inside the disposable model worker only.

    Existing model replay remains authoritative. Its adapter output is drained
    with the same byte and process limits, before load_base parses that output.
    No shared source file or long-lived imported module is modified.
    """
    TimeoutExpired = subprocess.TimeoutExpired

    @staticmethod
    def run(command, *, capture_output, timeout, check):
        output, code = _run_bounded(command, b"", cwd=os.getcwd(), timeout=timeout,
                                    allowed_exit_codes=(0, 1, 2), with_returncode=True,
                                    owns_process_group=False)
        return subprocess.CompletedProcess(command, code, output, b"")


def verify_project(data, *, bridge_executable=None, base_executable=None):
    """Return evidence only, without installing the candidate or moving undo.

    requiredCapabilities contains native requirements. Frontend feature caps
    must first be validated by their registered JS adapter, outside this API.
    """
    _json_bytes(data)
    _keys(data, ("manifest", "scene"))
    manifest = data["manifest"]
    if type(manifest) is not dict:
        _fail("SCENARIO_SHAPE", "Manifest must be a plain JSON object.")
    encoded = _scene(data["scene"], ("scene",))
    scene_hash = hashlib.sha256(encoded).hexdigest()
    if "sceneHash" in manifest and manifest["sceneHash"] != scene_hash:
        _fail("SCENARIO_SCENE_HASH", "Manifest scene hash differs from the original scene bytes.")
    required = _capabilities(manifest.get("requiredCapabilities", []), ("manifest", "requiredCapabilities"), supported=BRIDGE_CAPABILITIES)
    scene_required = scene_required_capabilities(data["scene"])
    if scene_required - BRIDGE_CAPABILITIES or ("requiredCapabilities" in manifest and scene_required - required):
        _fail("SCENARIO_CAPABILITY", "Scene requires an unsupported or omitted native capability.", status="UNSUPPORTED")
    required.update(scene_required)
    records = manifest.get("models", [])
    if type(records) is not list or len(records) > MAX_MODELS:
        _fail("SCENARIO_CAPACITY", "Saved model list exceeds capacity.", status="UNSUPPORTED")
    bridge, bridge_hash = _program(bridge_executable)
    base, base_hash = _program(base_executable, base=True) if records else (None, None)
    pins = _validator_pins()
    source_pins = {"bridge_source_sha256": _source_receipt(bridge),
                   "base_source_sha256": _source_receipt(base, base=True) if base else None}
    with tempfile.TemporaryDirectory(prefix="geometry-scenario-verify-") as directory:
        source = Path(directory) / "input.scene"
        source.write_bytes(encoded)
        payload = ("load-prepare " + str(source) + "\nsource-inspect-file " + str(source) + "\n").encode("utf-8")
        raw = _run_bounded([bridge], payload, cwd=directory, timeout=BRIDGE_TIMEOUT)
        try:
            rows = [_parse_json(line) for line in raw.splitlines() if line.strip()]
        except ModelError:
            _fail("SCENARIO_NATIVE_PROTOCOL", "Isolated native verifier returned malformed JSON.", status="UNSUPPORTED")
        if len(rows) != 2 or type(rows[0]) is not dict:
            _fail("SCENARIO_NATIVE_PROTOCOL", "Isolated native verifier omitted its receipt.", status="UNSUPPORTED")
        receipt, graph = rows
        if receipt.get("ok") is not True:
            _fail("SCENARIO_SCENE_INVALID", "Native parser rejected the scene.")
        available = _capabilities(receipt.get("capabilities"), ("native", "capabilities"), supported=BRIDGE_CAPABILITIES)
        native_required = _capabilities(receipt.get("required_capabilities"), ("native", "required_capabilities"), supported=BRIDGE_CAPABILITIES)
        # Native receipts report capabilities used by actual objects; an empty
        # scene may still explicitly require a supported capability. Preserve
        # that requirement from the original bytes without inventing objects.
        if required - available or native_required - scene_required:
            _fail("SCENARIO_CAPABILITY", "Native receipt does not support the original source requirements.", status="UNSUPPORTED")
        final = _final_objects(receipt.get("final_objects"))
        final_scene = receipt.get("final_scene")
        if type(final_scene) is not str or "\0" in final_scene or len(final_scene.encode("utf-8")) > MAX_OUTPUT_BYTES:
            _fail("SCENARIO_NATIVE_PROTOCOL", "Native final definition receipt is missing or exceeds output capacity.", status="UNSUPPORTED")
        _object_refs(manifest, final)
        objects, inventory = _inventory(graph, final)
        if records:
            raw = _run_bounded([sys.executable, str(Path(__file__).resolve()), "--model-worker", "--base", base],
                               _json_bytes({"models": records}), cwd=directory, timeout=MODEL_TIMEOUT,
                               allowed_exit_codes=(0, 2))
            worker = _parse_json(raw)
            if type(worker) is not dict or type(worker.get("ok")) is not bool:
                _fail("SCENARIO_NATIVE_PROTOCOL", "Model verifier returned no honest receipt.", status="UNSUPPORTED")
            if worker["ok"] is not True:
                if worker.get("status") not in ("INVALID", "UNSUPPORTED", "INCOMPLETE"):
                    _fail("SCENARIO_NATIVE_PROTOCOL", "Model verifier returned unknown failure.", status="UNSUPPORTED")
                raise ModelError(worker["status"], worker.get("code", "SCENARIO_MODEL_REPLAY"), "I31",
                                 worker.get("message", "Model replay failed."), path=worker.get("path", []))
            model_required = _capabilities(worker.get("requiredCapabilities"), ("models", "requiredCapabilities"))
            if model_required - available or ("requiredCapabilities" in manifest and model_required - required):
                _fail("SCENARIO_CAPABILITY", "Manifest omits a saved model's required source capability.", status="UNSUPPORTED")
            required.update(model_required)
    if (bridge_hash != _program(bridge)[1] or (base is not None and base_hash != _program(base, base=True)[1]) or
            pins != _validator_pins() or source_pins["bridge_source_sha256"] != _source_receipt(bridge) or
            (base and source_pins["base_source_sha256"] != _source_receipt(base, base=True))):
        _fail("SCENARIO_RUNTIME_CHANGED", "Executable, verifier or axiom changed during verification.", status="UNSUPPORTED")
    return {"ok": True, "final_objects": deepcopy(final), "final_scene": final_scene, "objects": objects, "inventory": inventory,
            "capabilities": sorted(available), "requiredCapabilities": sorted(required), "scene_sha256": scene_hash,
            "runtime": {"bridge_sha256": bridge_hash, "base_sha256": base_hash, **source_pins, **pins}}


def _error(exc):
    return {"ok": False, "status": exc.status, "code": exc.code, "message": exc.message, "path": exc.path}


def verify_bytes(raw, **native):
    """Read-only HTTP adapter seam: bounded strict JSON bytes, no live bridge."""
    if type(raw) is not bytes:
        _fail("SCENARIO_JSON", "Verification request must be raw JSON bytes.")
    if len(raw) > MAX_INPUT_BYTES:
        _fail("SCENARIO_CAPACITY", "Verification request exceeds input capacity.", status="UNSUPPORTED")
    return verify_project(_parse_json(raw), **native)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify a project using disposable native processes.")
    parser.add_argument("--bridge")
    parser.add_argument("--base")
    parser.add_argument("--model-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            _fail("SCENARIO_CAPACITY", "Verification stdin exceeds capacity.", status="UNSUPPORTED")
        data = _parse_json(raw)
        if args.model_worker:
            _keys(data, ("models",))
            base, _ = _program(args.base, base=True)
            previous = base_module.subprocess
            try:
                base_module.subprocess = _BoundedModelAdapter
                result = {"ok": True, "requiredCapabilities": _models(data["models"], base)}
            finally:
                base_module.subprocess = previous
        else:
            result = verify_project(data, bridge_executable=args.bridge, base_executable=args.base)
    except ModelError as exc:
        result = _error(exc)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
