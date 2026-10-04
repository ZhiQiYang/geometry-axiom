"""Read-only bridge to the authoritative C scene parser (D1–D19)."""

from __future__ import annotations

import atexit
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from .common import ModelError, ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY, scene_required_capabilities

_BUILD_DIRS: list[tempfile.TemporaryDirectory] = []
_MAX_SCENE_BYTES = 1024 * 1024


@atexit.register
def _cleanup_builds() -> None:
    for directory in _BUILD_DIRS:
        directory.cleanup()


@lru_cache(maxsize=1)
def _build_adapter() -> str:
    """Compile once per process in a private temporary cache, never in the repo."""
    source = Path(__file__).resolve().parents[1] / "model_base.c"
    try:
        compiler = shlex.split(os.environ.get("CC", "cc"))
    except ValueError as exc:
        raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "Compiler configuration is invalid.") from exc
    if not compiler or not shutil.which(compiler[0]):
        raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "C compiler is unavailable; set GEOMETRY_MODEL_BASE to a built adapter.")
    try:
        directory = tempfile.TemporaryDirectory(prefix="geometry-model-base-")
        _BUILD_DIRS.append(directory)
        target = Path(directory.name) / ("model-base.exe" if os.name == "nt" else "model-base")
        result = subprocess.run(
            [*compiler, "-std=c11", "-O2", str(source), "-lm", "-o", str(target)],
            capture_output=True, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "Could not build C scene adapter.") from exc
    if result.returncode:
        # Do not expose absolute checkout/temp paths in model diagnostics or hashes.
        raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "C scene adapter compilation failed.")
    return str(target)


def startup_base_transport() -> str:
    """Select startup transport without replacing an explicit update runtime.

    An update bridge alone uses the existing native compiler fallback, whose
    executable can be resolved and fingerprinted by the update producer.
    """
    if os.environ.get("GEOMETRY_MODEL_BASE"):
        return "configured"
    if os.environ.get("GEOMETRY_MODEL_UPDATE_BRIDGE"):
        return "native"
    return "wsl"


def _adapter_command(program, source, *, wsl_distro=None):
    """Keep native overrides literal; translate only an explicitly WSL adapter."""
    if wsl_distro is None:
        return [os.fspath(program), str(source)]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", wsl_distro) or not os.fspath(program).startswith("/"):
        raise ModelError("UNSUPPORTED", "BASE_EXECUTABLE", "I32", "Invalid WSL scene adapter configuration.")
    prefix = ["wsl.exe", "-d", wsl_distro, "--user", "root", "--exec"]
    converted = subprocess.run(
        [*prefix, "wslpath", "-u", str(source).replace("\\", "/")],
        capture_output=True, timeout=10, check=False,
    )
    try:
        path = converted.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ModelError("UNSUPPORTED", "BASE_EXECUTABLE", "I32", "Cannot resolve the scene input in WSL.") from exc
    if converted.returncode or not path.startswith("/") or any(c in path for c in "\r\n\0"):
        raise ModelError("UNSUPPORTED", "BASE_EXECUTABLE", "I32", "Cannot resolve the scene input in WSL.")
    return [*prefix, os.fspath(program), path]


def load_base(scene_text: str, executable=None) -> dict:
    """Validate the whole scene atomically and return geometry-base-snapshot/1.

    Explicit executable wins over GEOMETRY_MODEL_BASE. The override is a trusted
    local program path, not a shell command. New extension commands must never
    be hidden inside base_scene; the C adapter rejects non-definition commands.
    """
    if not isinstance(scene_text, str):
        raise ModelError("INVALID", "BASE_TYPE", "D25", "base_scene must be a string.")
    try:
        encoded = scene_text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ModelError("INVALID", "BASE_ENCODING", "D25", "base_scene must contain valid Unicode.") from exc
    if len(encoded) > _MAX_SCENE_BYTES:
        raise ModelError("UNSUPPORTED", "BASE_CAPACITY", "I33", "Scene exceeds adapter 1 MiB capacity.")
    source_capabilities = scene_required_capabilities(scene_text)
    if source_capabilities - {ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY}:
        raise ModelError("UNSUPPORTED", "CAPABILITY", "I32", "Unsupported required scene capability")
    program = executable or os.environ.get("GEOMETRY_MODEL_BASE") or _build_adapter()
    wsl_distro = (os.environ.get("GEOMETRY_MODEL_BASE_WSL_DISTRO")
                  if sys.platform == "win32" and executable is None else None)
    try:
        with tempfile.TemporaryDirectory(prefix="geometry-model-scene-") as directory:
            source = Path(directory) / "input.scene"
            source.write_bytes(encoded)
            result = subprocess.run(
                _adapter_command(program, source, wsl_distro=wsl_distro), capture_output=True,
                timeout=20, check=False,
            )
    except subprocess.TimeoutExpired as exc:
        raise ModelError("UNSUPPORTED", "BASE_TIMEOUT", "I33", "C scene validation exceeded its execution budget.") from exc
    except OSError as exc:
        raise ModelError("UNSUPPORTED", "BASE_EXECUTABLE", "I32", "Cannot execute the C scene adapter or create its input file.") from exc
    try:
        snapshot = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter did not return a valid snapshot.") from exc
    if not isinstance(snapshot, dict):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned an invalid snapshot shape.")
    if not snapshot.get("ok"):
        status = snapshot.get("status")
        if status not in {"INVALID", "UNSUPPORTED"}:
            raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned an unknown error status.")
        raise ModelError(status, snapshot.get("code", "BASE_INVALID"), snapshot.get("clause", "I9"), snapshot.get("message", "Scene rejected."))
    if result.returncode or snapshot.get("schema") != "geometry-base-snapshot/1":
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter failed or returned an unsupported schema.")
    required = {"base_scene", "specs", "placements", "solids", "unplaced_timbers", "dependencies"}
    if not required.issubset(snapshot) or not isinstance(snapshot["base_scene"], str) or any(
        not isinstance(snapshot[name], list) for name in required - {"base_scene"}
    ):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned an incomplete snapshot.")
    capabilities = snapshot.get("required_capabilities", [])
    if (not isinstance(capabilities, list) or any(type(item) is not str for item in capabilities)
            or len(capabilities) != len(set(capabilities)) or set(capabilities) - {ENGINEERING_CAPABILITY, PARAMETER_CAPABILITY}):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned unsupported source capabilities.")
    canonical_capabilities = scene_required_capabilities(snapshot["base_scene"])
    if source_capabilities != set(capabilities) or canonical_capabilities != set(capabilities):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I36", "C scene adapter did not preserve engineering source definitions and capability.")
    return snapshot
