"""Read-only bridge to the authoritative C scene parser (D1–D19)."""

from __future__ import annotations

import atexit
from hashlib import sha256
from threading import RLock
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from .model_common import ModelError, SECTION_PROFILE_CAPABILITY, scene_required_capabilities
from . import source_closure

_BUILD_DIRS: list[tempfile.TemporaryDirectory] = []
_BUILD_CACHE = {}
_BUILD_LOCK = RLock()
_SOURCE = Path(__file__).resolve().parents[2] / "geometry-core/model_base.c"
_MAX_SCENE_BYTES = 1024 * 1024


@atexit.register
def _cleanup_builds() -> None:
    for directory in _BUILD_DIRS:
        directory.cleanup()


def _compiler_command() -> tuple[str, ...]:
    try:
        compiler = shlex.split(os.environ.get("CC", "cc"))
    except ValueError as exc:
        raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "Compiler configuration is invalid.") from exc
    if not compiler or not shutil.which(compiler[0]):
        raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "C compiler is unavailable; set GEOMETRY_MODEL_BASE to a built adapter.")
    return tuple(compiler)


def _project_include_dirs(source):
    # model_base.c lives beside K. Conservative discovery also visits guarded
    # standalone header includes in inactive unity arms; hash their real owner.
    return (Path(source).resolve().parent / "kernel",)


def _project_source_closure(source):
    """Hash every recursively quoted project include, retaining stable path order.

    Search the referring directory first, then the explicit K include root.
    A missing dependency fails closed;
    it cannot silently become an untracked compiler search-path dependency.
    System headers are provided by the selected compiler installation.
    """
    pending = [Path(source).resolve()]
    include_dirs = _project_include_dirs(source)
    entries = {}
    while pending:
        path = pending.pop()
        name = str(path)
        if name in entries:
            continue
        data = path.read_bytes().replace(b"\r\n", b"\n")
        entries[name] = sha256(data).hexdigest()
        for directive in re.findall(rb'^\s*#\s*include\b([^\n]*)', data, re.M):
            relative = re.match(rb'\s*"([^"\r\n]+)"', directive)
            if relative is not None:
                quoted = relative.group(1).decode("utf-8")
                for directory in (path.parent, *include_dirs):
                    dependency = (directory / quoted).resolve()
                    if dependency.is_file():
                        pending.append(dependency)
                        break
                else:
                    raise FileNotFoundError(path.parent / quoted)
            elif not re.match(rb'\s*<[^>\r\n]+>', directive):
                raise ValueError("Project include is not a literal file")
    return tuple(sorted(entries.items()))


def _build_inputs(source, compiler):
    compiler_path = shutil.which(compiler[0])
    if compiler_path is None:
        raise OSError("Compiler disappeared")
    # The environment is hashed, never returned in diagnostics or receipts.
    # Compiler search paths and helper-tool selection therefore invalidate cache.
    environment = json.dumps(sorted(os.environ.items()), ensure_ascii=True,
                             separators=(",", ":")).encode("ascii")
    return (tuple(compiler), str(Path(compiler_path).resolve()),
            sha256(Path(compiler_path).read_bytes()).hexdigest(),
            _project_source_closure(source), sha256(environment).hexdigest())


def _build_adapter() -> str:
    """Reuse a build only while inputs and actual executable bytes still match."""
    with _BUILD_LOCK:
        compiler = _compiler_command()
        source = _SOURCE.resolve()
        try:
            inputs = _build_inputs(source, compiler)
            cached = _BUILD_CACHE.get(inputs)
            if cached is not None:
                target, binary_hash = cached
                try:
                    if sha256(Path(target).read_bytes()).hexdigest() == binary_hash:
                        return target
                except OSError:
                    pass
                del _BUILD_CACHE[inputs]
            directory = tempfile.TemporaryDirectory(prefix="geometry-model-base-")
            _BUILD_DIRS.append(directory)
            target = Path(directory.name) / ("model-base.exe" if os.name == "nt" else "model-base")
            result = subprocess.run(
                [*compiler, "-std=c11", "-O2", str(source), "-lm", "-o", str(target)],
                capture_output=True, timeout=60, check=False,
            )
            if result.returncode:
                raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "C scene adapter compilation failed.")
            if _build_inputs(source, compiler) != inputs:
                raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "C scene adapter compilation inputs changed.")
            binary_hash = sha256(target.read_bytes()).hexdigest()
        except ModelError:
            raise
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            raise ModelError("UNSUPPORTED", "BASE_COMPILER", "I32", "Could not build C scene adapter.") from exc
        _BUILD_CACHE.clear()
        _BUILD_CACHE[inputs] = (str(target), binary_hash)
        return str(target)


def _execution_identity(program, *, wsl_distro=None):
    sources = source_closure.current_identity()
    if not sources["fresh"]:
        raise ModelError("UNSUPPORTED", "BASE_RUNTIME_CHANGED", "I32", "Model runtime sources changed after this process loaded.")
    return (sources["loaded"], sources["current"],
            source_closure.binary_identity(program, wsl_distro=wsl_distro))


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


def _load_base_or_candidate(scene_text: str, executable=None, *, builder=None,
                            command_builder=None, provider=None, neutral_sources=False):
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
    if provider is None:
        from .bootstrap import default_provider
        provider = default_provider()
    supported = provider.source_capabilities
    if source_capabilities - supported:
        raise ModelError("UNSUPPORTED", "CAPABILITY", "I32", "Unsupported required scene capability")
    program = executable or os.environ.get("GEOMETRY_MODEL_BASE") or (builder or _build_adapter)()
    wsl_distro = (os.environ.get("GEOMETRY_MODEL_BASE_WSL_DISTRO")
                  if sys.platform == "win32" and executable is None else None)
    try:
        identity = _execution_identity(program, wsl_distro=wsl_distro)
        with tempfile.TemporaryDirectory(prefix="geometry-model-scene-") as directory:
            source = Path(directory) / "input.scene"
            source.write_bytes(encoded)
            command = (command_builder or _adapter_command)(program, source, wsl_distro=wsl_distro)
            if neutral_sources:
                command = [*command[:-1], "--neutral-sources", command[-1]]
            result = subprocess.run(
                command, capture_output=True, timeout=20, check=False,
            )
    except subprocess.TimeoutExpired as exc:
        raise ModelError("UNSUPPORTED", "BASE_TIMEOUT", "I33", "C scene validation exceeded its execution budget.") from exc
    except ModelError:
        raise
    except (OSError, ValueError) as exc:
        raise ModelError("UNSUPPORTED", "BASE_EXECUTABLE", "I32", "Cannot execute the C scene adapter or create its input file.") from exc
    try:
        current = _execution_identity(program, wsl_distro=wsl_distro)
    except (OSError, ValueError, ModelError) as exc:
        raise ModelError("UNSUPPORTED", "BASE_RUNTIME_CHANGED", "I32", "Model runtime changed while validating the scene.") from exc
    if current != identity:
        raise ModelError("UNSUPPORTED", "BASE_RUNTIME_CHANGED", "I32", "Model runtime changed while validating the scene.")
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
    candidate = None
    if neutral_sources and not result.returncode:
        from .model_sources import decode_candidate
        candidate = decode_candidate(result.stdout, source_bytes=encoded,
                                     execution_identity=current)
        snapshot = candidate.legacy_snapshot
    if result.returncode or snapshot.get("schema") != "geometry-base-snapshot/1":
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter failed or returned an unsupported schema.")
    required = {"base_scene", "specs", "placements", "solids", "unplaced_timbers", "dependencies"}
    if not required.issubset(snapshot) or not isinstance(snapshot["base_scene"], str) or any(
        not isinstance(snapshot[name], list) for name in required - {"base_scene"}
    ):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned an incomplete snapshot.")
    capabilities = snapshot.get("required_capabilities", [])
    if (not isinstance(capabilities, list) or any(type(item) is not str for item in capabilities)
            or len(capabilities) != len(set(capabilities)) or set(capabilities) - supported):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I32", "C scene adapter returned unsupported source capabilities.")
    canonical_capabilities = scene_required_capabilities(snapshot["base_scene"])
    if source_capabilities != set(capabilities) or canonical_capabilities != set(capabilities):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I36", "C scene adapter did not preserve engineering source definitions and capability.")
    if SECTION_PROFILE_CAPABILITY in source_capabilities and not isinstance(snapshot.get("profile_runs"), list):
        raise ModelError("UNSUPPORTED", "BASE_PROTOCOL", "I51", "C scene adapter omitted section-profile definitions.")
    return candidate if neutral_sources else snapshot


def load_base(scene_text: str, executable=None, *, builder=None, command_builder=None, provider=None) -> dict:
    """Retain the existing snapshot API and its validation/error contract."""
    return _load_base_or_candidate(scene_text, executable, builder=builder,
        command_builder=command_builder, provider=provider)


def load_candidate(scene_text: str, executable=None, *, builder=None, command_builder=None, provider=None):
    """Read one complete typed candidate in one pinned native invocation.

    The product facade uses this transport and rejects an old adapter or an
    incomplete native graph instead of falling back to snapshot evaluation.
    """
    return _load_base_or_candidate(scene_text, executable, builder=builder,
        command_builder=command_builder, provider=provider, neutral_sources=True)
