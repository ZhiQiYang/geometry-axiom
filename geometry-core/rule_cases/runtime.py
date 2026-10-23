"""Reuse the native test registry's exact source/binary verification, never build here."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import binaries
from modeling import _host  # Initialize the explicitly assembled host sources.
from geometry_app import source_closure


def _sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _module_hashes():
    paths = dict(source_closure.source_paths(ROOT))
    directory = Path(__file__).parent
    paths.update((path.relative_to(ROOT).as_posix(), path)
                 for path in directory.rglob("*")
                 if path.is_file() and path.suffix in {".py", ".json"})
    return {name: _sha(path) for name, path in sorted(paths.items())}


_LOADED_MODULES = _module_hashes()
_REGISTRY_PATH = ROOT / "tests" / "binaries.py"
_LOADED_REGISTRY = _sha(_REGISTRY_PATH)


def runtime_identity(binary=None):
    """Return verified facts or an explicit unknown identity; no executable fallback."""
    binary = binary or os.environ.get("GEOMETRY_TEST_BRIDGE") or binaries.BY_NAME["bridge"].path
    info = binaries.inspect_one(binaries.BY_NAME["bridge"], path=binary)
    if info.state != "fresh":
        return {"known": False, "reason": info.reason}, info.path
    try:
        binary_hash = binaries._binary_identity(info.path)["exe_sha256"]
        module_hashes = _module_hashes()
        registry_hash = _sha(_REGISTRY_PATH)
        if (not source_closure.current_identity()["fresh"]
                or module_hashes != _LOADED_MODULES or registry_hash != _LOADED_REGISTRY):
            return {"known": False, "reason": "Validator changed; reload the Python process"}, info.path
        validator = hashlib.sha256()
        for name, module_hash in sorted(module_hashes.items()):
            validator.update(name.encode() + b"\0" + bytes.fromhex(module_hash))
        validator.update(b"tests/binaries.py\0" + bytes.fromhex(registry_hash))
        identity = {"known": True, "nativeBinaryHash": binary_hash,
                    "nativeSourceHash": info.fingerprint,
                    "validatorVersion": validator.hexdigest(),
                    "axiomHash": _sha(ROOT / "公理層.md"),
                    "assertionSchemaHash": _sha(Path(__file__).with_name("definition.py"))}
        # A source/binary replacement between the two reads is never trusted.
        final = binaries.inspect_one(binaries.BY_NAME["bridge"], path=info.path)
        if (final.state != "fresh" or final.fingerprint != info.fingerprint
                or binaries._binary_identity(info.path)["exe_sha256"] != binary_hash
                or _module_hashes() != module_hashes
                or not source_closure.current_identity()["fresh"]
                or _sha(_REGISTRY_PATH) != registry_hash
                or _sha(ROOT / "公理層.md") != identity["axiomHash"]):
            return {"known": False, "reason": "Runtime changed during verification"}, info.path
        return identity, info.path
    except (OSError, ValueError) as error:
        return {"known": False, "reason": str(error)}, info.path
