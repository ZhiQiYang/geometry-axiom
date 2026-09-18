"""Read-only bridge to the authoritative C legacy-scene parser (D1–D18)."""

from __future__ import annotations

import atexit
from functools import lru_cache
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

from .common import ModelError

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
    program = executable or os.environ.get("GEOMETRY_MODEL_BASE") or _build_adapter()
    try:
        with tempfile.TemporaryDirectory(prefix="geometry-model-scene-") as directory:
            source = Path(directory) / "input.scene"
            source.write_bytes(encoded)
            result = subprocess.run(
                [os.fspath(program), str(source)], capture_output=True,
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
    return snapshot
