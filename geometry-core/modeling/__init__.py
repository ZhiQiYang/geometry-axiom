"""Deterministic orthogonal models, backed by the authoritative C scene parser.

The Python executor is a reference implementation; it does not add new DSL
commands to the existing C World or advertise that the canvas supports them.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import secrets

from .common import (ModelError, canonical_bytes, digest, strict_json_loads,
                     ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, SECTION_PROFILE_CAPABILITY,
                     scene_required_capabilities)

# The source commit contains the adopted axiom bytes identified by this digest.
# Update only after committing the corresponding SSOT change (MODELING-CONTRACT).
AXIOM_REVISION = "6cd7c22680f37c95330ed8f9eac0427108bd0a61"
AXIOM_SHA256 = "5f95dee8d901619a0098e269d2283f60c6b5d9aa7a00057cf24c4fd42fdba253"
# The P-046 amendment (2026-10-11: I68 flag sentence aligned with R54's in-window undo)
# replaced the ff18cb6 text before it reached main; that interim digest was never
# declared by a main executor, so it is deliberately not listed as a compatible version.
# The P-045 amendment (2026-10-11: D51 wording, D54 fail-closed sentence) replaced
# the ee7c441 text before it reached main; that interim digest was never declared
# by a main executor, so it is deliberately not listed as a compatible version.
# The D48 label-format fix (P-044, 2026-10-11) replaced the c24ec08 and 2818289
# texts before they reached main; those interim digests were never declared by a
# main executor, so they are deliberately not listed as compatible versions.
# The R43 amendment (PF-0 r2.1, 2026-10-11) replaced the a93bb34 text before it
# reached main; that interim digest was never declared by a main executor, so it
# is deliberately not listed as a compatible version.
# D56-D58 / I68-I69 / R54-R55 (K2a) only add editor drafts (grid-editor-drafts/1) and
# repeated-bay assembly instances (assembly-bay-repeat/1), and amend D34 / I42 / R35 and the
# first sentence of D53 for them; this executor implements neither capability, so packages
# built under the previous adopted text (K2b incl. P-045) stay valid.
PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS = frozenset({
    ("a2f8c89f74930cf9b88a6bb79e5897c9046f442c", "839250e3366b8019ae1aae5d3799f3f93c768820bf7e4856d571634d32ddff6a"),
})
# D51-D55 / I63-I67 / R51-R53 (K2b) only add project-level data, room-candidate-drafts/1
# and definition-import/1, which this executor does not implement; packages built
# under the previous adopted text (K1) stay valid.
PRE_ZERO_ROOM_AXIOM_VERSIONS = frozenset({
    ("7c5485bba1a1e0d9b95009bd80dfc4114af1d942", "d9ccdd38e31219a4eea4c0f75dc09963a60504e6e3fd80fdf9ed4df1952f94a8"),
})
# D46-D50 / I58-I62 / R47-R50 only add cutting-plan/1, which this executor does
# not implement; packages built under the previous adopted text stay valid.
PRE_CUTTING_PLAN_AXIOM_VERSIONS = frozenset({
    ("8a8b56424407bb758de0d16e66c94e21eb79aa41", "d8a0b4a1c108197f4abb5c67d73fa22aa7fa4288769f605a5a9372fd93aa7b52"),
})
# D41-D45 / I52-I57 / R41-R46 only add panel-fill/1, which this executor does
# not implement; packages built under the previous adopted text stay valid.
PRE_PANEL_FILL_AXIOM_VERSIONS = frozenset({
    ("3ad8012b6f01f9f46795a28a410ee444c5cce1a0", "29ad0c657e53d364347862fddac23ba26a248a4fd8f83487d86f9e648bd1eaf2"),
})
# The Q38 extension is additive; packages under the prior text remain supported
# only when they do not claim or contain section-profile/1 definitions.
PRE_SECTION_PROFILE_AXIOM_VERSIONS = frozenset({
    ("73b9ba1d417c1b6c9885951b24139b67f8550312", "d4bd69cd3dcbcef10802dd401a66b293afdaa09abccc6853d7a39f478cefe29a"),
})
PRE_SUBDIVISION_AXIOM_VERSIONS = frozenset({
    ("cc6adff4c9c783ce78bcbd849754b69254690cab", "d5eb43d077e7408fb032ee09f552795215fbf5fb7b097b57f7ac7ef6f2ed08f7"),
})
PRE_GENERATION_AXIOM_VERSIONS = frozenset({
    ("ccbec5fe9e4b056bcd5673fb9f69a54e888ea4e6", "264d8c5d2fa4e513418fbd611f2ef6f8d597def51d89805a75e9e21d0d24e8fe"),
})
PARAMETER_AXIOM_VERSIONS = frozenset({
    ("802f9bda1b1b8ab046f059e115dbf05a44da10df", "b19009682ba5b3e7150341ae1b5190629cb03985d500d382aa918438fb548c0b"),
    ("82074011fabdccb5918a580eef737aa227536d01", "8b3afe498b0050a50b020a3a6fc3018abfecf9f9502fccf742a32e0bc499cc03"),
})
# Known pre-engineering specification. These exact sources remain supported by
# the additive executor; arbitrary old hashes or engineering definitions do not.
LEGACY_AXIOM_VERSIONS = frozenset({
    ("494660068ceb884c1a96884a2b704e3bcf5d24ca", "bc01cf0db266f97255156e28e40fb235833031fb95f1f234ad6d90a9f08240f8"),
})
# The previous engineering release supports D26-D28, but not D29 grid systems.
# Keep it separate: adding this tuple must not grant engineering to LEGACY.
ENGINEERING_AXIOM_VERSIONS = frozenset({
    ("5698f8501d539ed3a6f0644dab854e62e3bafb1a", "1843e3e9f6a3a6db07ceaa8f62fad693039296d519791af98c2a433554308bcf"),
})
FINITE_GRID_AXIOM_VERSIONS = frozenset({
    ("b4fe75f7f03ed81b4bc9f85a044282f91bd27cb6", "2d31868524cb2776c2c405367fa69087b8f43371f320f12f3405fb14ce9fdf28"),
})
INFINITE_GRID_AXIOM_VERSIONS = frozenset({
    ("f34c0aeb56a4d2c639be924b289e3572756807d8", "b2b3ebde32f693e3853ace3d39a8618e5717d42e437019510505b3453ae87c75"),
})
SCHEMA = "geometry-model-package/1"
PROFILE = "orthogonal-model/1"
GENERATOR = {"name": "geometry-axiom-reference", "version": "1.4.0"}
CAPABILITIES = ("extrusion/1", "shell/1", "composite-space/1",
                "solid-composition/1", "model-export/1", ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY,
                SECTION_PROFILE_CAPABILITY)
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


def _scene_uses_grid_system(scene):
    """Gate new source syntax before rebuilding a package claiming older axioms."""
    for index, raw in enumerate(scene.splitlines()):
        if not index:
            raw = raw.removeprefix("\ufeff")
        tokens = raw.split("#", 1)[0].split()
        if tokens and (tokens[0] == "grid-system" or
                       tokens[0] == "grid" and "from-system" in tokens[1:] or
                       tokens[:2] == ["canvas-pos", "grid-system"]):
            return True
    return False


def _scene_uses_infinite_grid(scene):
    """Old finite-grid snapshots cannot claim the new lattice/key contract."""
    for raw in scene.removeprefix("\ufeff").splitlines():
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        if (tokens[0] in {"grid-binding", "boundary-vertex-keys", "boundary-keyed"} or
                tokens[0] == "grid-system" and any(t in {"repeat", "repeat-panel"} for t in tokens[1:]) or
                tokens[0] == "grid" and "from-binding" in tokens[1:] or
                tokens[0] == "subgrid" and "lattice-cell" in tokens[1:] or
                tokens[:2] in (["canvas-pos", "grid-binding"], ["delete", "grid-binding"])):
            return True
    return False


def _scene_uses_stagger(scene):
    """D10b axis sources and band identities cannot claim pre-stagger axioms."""
    for raw in scene.removeprefix("\ufeff").splitlines():
        tokens = raw.split("#", 1)[0].split()
        if tokens and ((tokens[0] == "grid-system" and "stagger" in tokens[1:]) or
                       (tokens[0] == "place" and "at-line" in tokens[1:] and "band" in tokens[1:])):
            return True
    return False


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
    active = [c for c in CAPABILITIES if c in available and
              (c not in (ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, SECTION_PROFILE_CAPABILITY) or c in result["required_capabilities"])]
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
    current_version = (AXIOM_REVISION, _axiom_hash())
    supplied_version = (manifest["axiom_revision"], manifest["axiom_sha256"])
    if not all(type(part) is str for part in supplied_version) or supplied_version not in {
            current_version, *LEGACY_AXIOM_VERSIONS, *ENGINEERING_AXIOM_VERSIONS,
            *FINITE_GRID_AXIOM_VERSIONS, *INFINITE_GRID_AXIOM_VERSIONS, *PARAMETER_AXIOM_VERSIONS, *PRE_GENERATION_AXIOM_VERSIONS, *PRE_SUBDIVISION_AXIOM_VERSIONS,
            *PRE_SECTION_PROFILE_AXIOM_VERSIONS, *PRE_PANEL_FILL_AXIOM_VERSIONS,
            *PRE_CUTTING_PLAN_AXIOM_VERSIONS, *PRE_ZERO_ROOM_AXIOM_VERSIONS,
            *PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS}:
        raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "This executor does not implement the supplied axiom revision")
    if supplied_version != current_version:
        definitions = package["definitions"]
        if (not isinstance(definitions, dict) or type(definitions.get("base_scene")) is not str):
            raise ModelError("INVALID", "PACKAGE_SCHEMA", "D25", "Expected complete source definitions")
        if supplied_version not in PRE_PANEL_FILL_AXIOM_VERSIONS | PRE_CUTTING_PLAN_AXIOM_VERSIONS | PRE_ZERO_ROOM_AXIOM_VERSIONS | PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS and (
                SECTION_PROFILE_CAPABILITY in scene_required_capabilities(definitions["base_scene"]) or
                isinstance(manifest["capabilities"], list) and SECTION_PROFILE_CAPABILITY in manifest["capabilities"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Section profiles require the adopted Q38 axiom revision")
        if supplied_version not in PRE_SECTION_PROFILE_AXIOM_VERSIONS | PRE_PANEL_FILL_AXIOM_VERSIONS | PRE_CUTTING_PLAN_AXIOM_VERSIONS | PRE_ZERO_ROOM_AXIOM_VERSIONS | PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS and "grid-subdivision-rules/1" in scene_required_capabilities(definitions["base_scene"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Source subdivision requires its adopted axiom revision")
        if supplied_version not in PRE_GENERATION_AXIOM_VERSIONS | PRE_SUBDIVISION_AXIOM_VERSIONS | PRE_SECTION_PROFILE_AXIOM_VERSIONS | PRE_PANEL_FILL_AXIOM_VERSIONS | PRE_CUTTING_PLAN_AXIOM_VERSIONS | PRE_ZERO_ROOM_AXIOM_VERSIONS | PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS and _scene_uses_stagger(definitions["base_scene"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Stagger sources and band anchors require the stagger axiom revision")
        if supplied_version not in PARAMETER_AXIOM_VERSIONS | PRE_GENERATION_AXIOM_VERSIONS | PRE_SUBDIVISION_AXIOM_VERSIONS | PRE_SECTION_PROFILE_AXIOM_VERSIONS | PRE_PANEL_FILL_AXIOM_VERSIONS | PRE_CUTTING_PLAN_AXIOM_VERSIONS | PRE_ZERO_ROOM_AXIOM_VERSIONS | PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS and (PARAMETER_CAPABILITY in scene_required_capabilities(definitions["base_scene"]) or PARAMETER_CAPABILITY in manifest["capabilities"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Parameter sources require the parameter axiom revision")
        if supplied_version not in INFINITE_GRID_AXIOM_VERSIONS | PARAMETER_AXIOM_VERSIONS | PRE_GENERATION_AXIOM_VERSIONS | PRE_SUBDIVISION_AXIOM_VERSIONS | PRE_SECTION_PROFILE_AXIOM_VERSIONS | PRE_PANEL_FILL_AXIOM_VERSIONS | PRE_CUTTING_PLAN_AXIOM_VERSIONS | PRE_ZERO_ROOM_AXIOM_VERSIONS | PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS and _scene_uses_infinite_grid(definitions["base_scene"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Infinite-grid sources require the infinite-grid axiom revision")
        if supplied_version not in FINITE_GRID_AXIOM_VERSIONS | INFINITE_GRID_AXIOM_VERSIONS | PARAMETER_AXIOM_VERSIONS | PRE_GENERATION_AXIOM_VERSIONS | PRE_SUBDIVISION_AXIOM_VERSIONS | PRE_SECTION_PROFILE_AXIOM_VERSIONS | PRE_PANEL_FILL_AXIOM_VERSIONS | PRE_CUTTING_PLAN_AXIOM_VERSIONS | PRE_ZERO_ROOM_AXIOM_VERSIONS | PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS and _scene_uses_grid_system(definitions["base_scene"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Grid-system sources require the grid-system axiom revision")
        if supplied_version in LEGACY_AXIOM_VERSIONS and (
                scene_required_capabilities(definitions["base_scene"]) or
                isinstance(manifest["capabilities"], list) and ENGINEERING_CAPABILITY in manifest["capabilities"]):
            raise ModelError("UNSUPPORTED", "AXIOM_VERSION", "I32", "Engineering sources require the engineering axiom revision")
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
